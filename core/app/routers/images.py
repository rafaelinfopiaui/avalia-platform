"""Recebimento, armazenamento e recuperação de imagens de resposta (AV-S06B).

Uma imagem é anexada a uma `Answer` já existente (uma foto por questão,
`DEC-AV-018`; avaliação/questão/aluno escolhidos manualmente pelo professor,
`DEC-AV-021`). Este módulo apenas guarda e devolve o arquivo original: não
extrai texto e não aciona correção.

NOTA (segurança):
- autorização reaplica o padrão de `create_answer` (`_get_owned_assessment` +
  `require_assessment_mutation`) em upload, listagem e download;
- o nome em disco é sempre `{uuid4}.{ext}`, com extensão derivada do formato
  detectado pelo Pillow; o nome enviado pelo cliente é só metadado;
- o conteúdo é gravado em arquivo temporário no próprio diretório de
  armazenamento e só é finalizado (`os.replace`) após validação; o registro no
  banco é commitado depois disso, e o arquivo é removido se o commit falhar;
- logs carregam apenas IDs, tamanho e tipo — nunca bytes, caminho ou nome original;
- não há rota estática: o binário só sai por `/v1/answer-images/{id}/download`.

Exclusão lógica reversível (BL-AV-4B-05, 1ª fatia, D1/D2/D3):
- `DELETE /v1/answer-images/{id}` marca `deleted_at`/`deleted_by_id`; o arquivo
  e o registro são mantidos (sem remoção física, sem expurgo);
- `POST /v1/answer-images/{id}/restore` reverte a marcação;
- ambas só operam com a resposta em AGUARDANDO_TRANSCRICAO (estágio A); depois
  da confirmação respondem 409, inclusive para admin (D2, R3);
- ambas travam a linha de `answers` (SELECT ... FOR UPDATE) antes de decidir,
  serializando com a confirmação da transcrição (R2);
- leituras padrão (listagem, download, transcrição) ignoram imagens excluídas;
  elas só aparecem na projeção mínima `/v1/answers/{id}/images/deleted` (R1/R4).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unicodedata
import uuid
import warnings
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import update
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.db import get_db
from app.deps import require_role
from app.logging_utils import log_event, new_correlation_id
from app.models import Answer, AnswerImage, AuditEvent, Question, TranscriptionStatus, User
from app.routers.academic import require_assessment_mutation
from app.schemas import AnswerImageOut, DeletedAnswerImageOut

router = APIRouter(prefix="/v1", tags=["answer-images"])

# Formato detectado pelo Pillow -> (MIME real, extensão gerada pelo servidor).
# MPO é como o Pillow identifica JPEGs de câmera com marcador multi-picture;
# o arquivo continua sendo um JPEG comum. MPO NÃO pode entrar na lista passada
# a Image.open(formats=...) — nessa posição o Pillow 12.x levanta KeyError('MPO'),
# pois MPO não é um plugin registrável por nome ali; ele é reconhecido via JPEG.
# Por isso o dicionário de MIME (resultado) inclui MPO, mas a lista de abertura não.
_ALLOWED_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "MPO": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
}
# Nomes de formato aceitos por Image.open(formats=...) — sem MPO (ver acima).
_OPEN_FORMATS = ["JPEG", "PNG"]
_DECLARED_TYPES = {"image/jpeg": "image/jpeg", "image/jpg": "image/jpeg", "image/png": "image/png"}
_CHUNK_SIZE = 64 * 1024
# Folga para boundary e cabeçalhos multipart na checagem prévia de Content-Length.
_MULTIPART_OVERHEAD = 64 * 1024
_MAX_ORIGINAL_FILENAME = 255
_STORAGE_ERROR = "Falha ao armazenar a imagem. Nenhum registro foi criado."
_INVALID_IMAGE = "O arquivo enviado não é uma imagem JPEG ou PNG válida."
_IMAGES_LOCKED = "ANSWER_IMAGES_LOCKED"
_IMAGES_LOCKED_MESSAGE = (
    "A transcrição desta resposta já foi confirmada: as imagens não podem mais ser "
    "excluídas nem restauradas."
)
_FILE_MISSING = "ANSWER_IMAGE_FILE_MISSING"
_FILE_MISSING_MESSAGE = (
    "O arquivo desta imagem não está disponível no armazenamento. A restauração não foi "
    "feita e a imagem continua excluída."
)

_UPLOAD_OPENAPI = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["file"],
                    "properties": {"file": {"type": "string", "format": "binary"}},
                }
            }
        },
    }
}


def _get_authorized_answer(db: Session, answer_id: str, user: User) -> Answer:
    # Import tardio: app.main importa este router, e a regra deve ser a mesma
    # de create_answer, sem cópia.
    from app.main import _get_owned_assessment

    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    return answer


def _lock_answer_row(db: Session, answer_id: str) -> Answer:
    """Trava a linha de `answers` (SELECT ... FOR UPDATE) até o fim da transação.

    Ponto único de serialização (R2) entre exclusão/restauração de imagem e
    confirmação da transcrição: quem obtém o lock relê o estado já commitado
    (`populate_existing`) e só então decide. No SQLite o FOR UPDATE é ignorado.
    """
    answer = (
        db.query(Answer)
        .filter(Answer.id == answer_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    return answer


def _storage_dir() -> Path:
    return Path(get_settings().answer_images_storage_dir).resolve()


def _stored_path(image: AnswerImage) -> Path | None:
    """Caminho do arquivo da imagem, ou None se ausente/fora do diretório."""
    storage_dir = _storage_dir()
    path = (storage_dir / image.storage_filename).resolve()
    if path.parent != storage_dir or not path.is_file():
        return None
    return path


def _too_large(max_bytes: int) -> HTTPException:
    return HTTPException(
        status_code=413,
        detail=f"Imagem excede o limite de {max_bytes // (1024 * 1024)} MB.",
    )


def _sanitize_original_filename(raw: str | None) -> str:
    # Remove caracteres de controle/formatação (categoria Unicode "C*").
    cleaned = "".join(ch for ch in raw or "" if not unicodedata.category(ch).startswith("C"))
    return cleaned.strip()[:_MAX_ORIGINAL_FILENAME] or "sem-nome"


def _normalize_declared_type(raw: str | None) -> str | None:
    return _DECLARED_TYPES.get((raw or "").split(";")[0].strip().lower())


def _inspect_image(path: Path) -> tuple[str, str]:
    """Abre o arquivo com Pillow e devolve (MIME real, extensão)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path, formats=_OPEN_FORMATS) as img:
                detected = img.format
                img.verify()
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise HTTPException(status_code=422, detail=_INVALID_IMAGE) from exc
    if detected not in _ALLOWED_FORMATS:
        raise HTTPException(status_code=422, detail=_INVALID_IMAGE)
    return _ALLOWED_FORMATS[detected]


async def _write_validated_file(
    upload: UploadFile,
    declared_type: str,
    max_bytes: int,
    correlation_id: str,
    answer_id: str,
) -> tuple[str, str, int, str]:
    """Grava, valida e finaliza o arquivo. Devolve (nome em disco, MIME, tamanho, sha256)."""
    try:
        storage_dir = _storage_dir()
        storage_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=storage_dir, prefix=".upload-", suffix=".part")
    except OSError as exc:
        log_event("answer_image_storage_failed", correlation_id, answer_id=answer_id, stage="prepare")
        raise HTTPException(status_code=500, detail=_STORAGE_ERROR) from exc

    tmp_path = Path(tmp_name)
    try:
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(fd, "wb") as out:
            while chunk := await upload.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise _too_large(max_bytes)
                digest.update(chunk)
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        if size == 0:
            raise HTTPException(status_code=422, detail="Arquivo vazio.")
        content_type, extension = _inspect_image(tmp_path)
        if content_type != declared_type:
            raise HTTPException(
                status_code=422,
                detail="Tipo declarado do arquivo diverge do conteúdo real.",
            )
        storage_filename = f"{uuid.uuid4()}.{extension}"
        os.replace(tmp_path, storage_dir / storage_filename)
    except OSError as exc:
        log_event("answer_image_storage_failed", correlation_id, answer_id=answer_id, stage="write")
        raise HTTPException(status_code=500, detail=_STORAGE_ERROR) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return storage_filename, content_type, size, digest.hexdigest()


@router.post(
    "/answers/{answer_id}/images",
    response_model=AnswerImageOut,
    status_code=201,
    openapi_extra=_UPLOAD_OPENAPI,
)
async def upload_answer_image(
    answer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    _get_authorized_answer(db, answer_id, user)
    max_bytes = get_settings().answer_image_max_bytes

    # Primeira defesa: recusa pelo Content-Length antes de ler o corpo.
    # Segunda defesa: o limite é reaplicado sobre os bytes efetivamente lidos.
    declared_length = request.headers.get("content-length")
    if declared_length is not None:
        try:
            length = int(declared_length)
        except ValueError:
            raise HTTPException(status_code=400, detail="Content-Length inválido.") from None
        if length > max_bytes + _MULTIPART_OVERHEAD:
            log_event("answer_image_rejected", correlation_id, answer_id=answer_id, reason="too_large")
            raise _too_large(max_bytes)

    async with request.form(max_files=1, max_fields=1) as form:
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise HTTPException(status_code=422, detail="Campo 'file' com a imagem é obrigatório.")
        declared_type = _normalize_declared_type(upload.content_type)
        if declared_type is None:
            raise HTTPException(status_code=422, detail="Apenas imagens JPEG ou PNG são aceitas.")
        original_filename = _sanitize_original_filename(upload.filename)
        storage_filename, content_type, size, sha256_hash = await _write_validated_file(
            upload, declared_type, max_bytes, correlation_id, answer_id
        )

    image = AnswerImage(
        answer_id=answer_id,
        storage_filename=storage_filename,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size,
        sha256_hash=sha256_hash,
        uploaded_by_id=user.id,
    )
    db.add(image)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        (_storage_dir() / storage_filename).unlink(missing_ok=True)
        log_event("answer_image_storage_failed", correlation_id, answer_id=answer_id, stage="commit")
        raise HTTPException(status_code=500, detail=_STORAGE_ERROR) from exc
    db.refresh(image)
    log_event(
        "answer_image_uploaded",
        correlation_id,
        answer_id=answer_id,
        image_id=image.id,
        user_id=user.id,
        content_type=content_type,
        size_bytes=size,
    )
    return image


@router.get("/answers/{answer_id}/images", response_model=list[AnswerImageOut])
def list_answer_images(
    answer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    _get_authorized_answer(db, answer_id, user)
    # Mais recente primeiro: a primeira da lista é a imagem vigente da resposta.
    # Só imagens ativas (R1); as excluídas logicamente têm rota própria.
    return (
        db.query(AnswerImage)
        .filter(AnswerImage.answer_id == answer_id, AnswerImage.deleted_at.is_(None))
        .order_by(AnswerImage.created_at.desc(), AnswerImage.id.desc())
        .all()
    )


@router.get("/answers/{answer_id}/images/deleted", response_model=list[DeletedAnswerImageOut])
def list_deleted_answer_images(
    answer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    # Projeção mínima (ACD-15/R4): mantém a restauração alcançável pela
    # interface sem reexpor nome original, hash ou download.
    _get_authorized_answer(db, answer_id, user)
    return (
        db.query(AnswerImage)
        .filter(AnswerImage.answer_id == answer_id, AnswerImage.deleted_at.is_not(None))
        .order_by(AnswerImage.deleted_at.desc(), AnswerImage.id.desc())
        .all()
    )


@router.get("/answer-images/{image_id}/download")
def download_answer_image(
    image_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    image = db.get(AnswerImage, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    _get_authorized_answer(db, image.answer_id, user)
    # O estado lógico é autoritativo: imagem excluída nunca é servida, mesmo
    # com o arquivo ainda em disco (ACD-08).
    if image.deleted_at is not None:
        raise HTTPException(status_code=410, detail="Imagem excluída. Restaure-a para visualizar.")
    path = _stored_path(image)
    if path is None:
        correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
        log_event("answer_image_file_missing", correlation_id, image_id=image.id)
        raise HTTPException(status_code=404, detail="Arquivo da imagem indisponível.")
    return FileResponse(
        path,
        media_type=image.content_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


# ---------------- Exclusão lógica e restauração (BL-AV-4B-05) ----------------
def _error_response(status_code: int, code: str, message: str, correlation_id: str, details: dict):
    # Import tardio pelo mesmo motivo de _get_authorized_answer.
    from app.main import error_response

    return error_response(status_code, code, message, correlation_id, details=details)


def _audit_metadata(image: AnswerImage) -> dict:
    # Conjunto MÍNIMO (ACD-05): nunca original_filename, storage_filename,
    # sha256_hash nem conteúdo — esses ficam só na própria tabela.
    return {
        "id": image.id,
        "answer_id": image.answer_id,
        "uploaded_by_id": image.uploaded_by_id,
        "content_type": image.content_type,
        "size_bytes": image.size_bytes,
        "created_at": image.created_at.isoformat() if image.created_at else None,
    }


def _deletion_state(deleted_at: datetime | None, deleted_by_id: str | None) -> dict:
    return {
        "deleted_at": deleted_at.isoformat() if deleted_at else None,
        "deleted_by_id": deleted_by_id,
    }


def _image_for_mutation(
    db: Session, image_id: str, user: User, operation: str, correlation_id: str
) -> tuple[AnswerImage, JSONResponse | None]:
    """Autoriza, trava a resposta e aplica o guard de estágio A (D2/R3).

    Devolve a imagem relida sob o lock e, se o estágio não permitir, a resposta
    409 já pronta (inclusive para admin).
    """
    image = db.get(AnswerImage, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    _get_authorized_answer(db, image.answer_id, user)
    # O estágio é avaliado só DEPOIS do lock, para não ficar inválido antes do
    # commit (R2/ACD-10).
    answer = _lock_answer_row(db, image.answer_id)
    db.refresh(image)
    if answer.transcription_status != TranscriptionStatus.AGUARDANDO_TRANSCRICAO:
        log_event(
            "answer_image_mutation_blocked",
            correlation_id,
            image_id=image.id,
            answer_id=answer.id,
            operation=operation,
        )
        return image, _error_response(
            409,
            _IMAGES_LOCKED,
            _IMAGES_LOCKED_MESSAGE,
            correlation_id,
            {"answer_id": answer.id, "transcription_status": answer.transcription_status.value},
        )
    return image, None


@router.delete("/answer-images/{image_id}", response_model=DeletedAnswerImageOut)
def delete_answer_image(
    image_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    image, blocked = _image_for_mutation(db, image_id, user, "delete", correlation_id)
    if blocked is not None:
        return blocked

    before = {**_audit_metadata(image), **_deletion_state(image.deleted_at, image.deleted_by_id)}
    deleted_at = datetime.utcnow()
    # Condicional: só a primeira exclusão marca; repetir não sobrescreve
    # deleted_at nem gera novo AuditEvent (ACD-06/ACD-07).
    result = db.execute(
        update(AnswerImage)
        .where(AnswerImage.id == image.id, AnswerImage.deleted_at.is_(None))
        .values(deleted_at=deleted_at, deleted_by_id=user.id)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        db.rollback()
        db.refresh(image)
        return image

    db.add(
        AuditEvent(
            actor_id=user.id,
            action="DELETE_LOGICAL",
            resource_type="AnswerImage",
            resource_id=image.id,
            before_json=json.dumps(before),
            after_json=json.dumps(_deletion_state(deleted_at, user.id)),
        )
    )
    db.commit()
    db.refresh(image)
    log_event(
        "answer_image_deleted_logically",
        correlation_id,
        image_id=image.id,
        answer_id=image.answer_id,
        user_id=user.id,
    )
    return image


@router.post("/answer-images/{image_id}/restore", response_model=AnswerImageOut)
def restore_answer_image(
    image_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    image, blocked = _image_for_mutation(db, image_id, user, "restore", correlation_id)
    if blocked is not None:
        return blocked
    if image.deleted_at is None:
        return image  # já ativa: no-op (ACD-06)
    # Não promete restauração sem o arquivo: preserva a marcação para
    # diagnóstico, sem reconstruir bytes (ACD-12).
    if _stored_path(image) is None:
        log_event("answer_image_file_missing", correlation_id, image_id=image.id, operation="restore")
        return _error_response(409, _FILE_MISSING, _FILE_MISSING_MESSAGE, correlation_id, {"image_id": image.id})

    before = {**_audit_metadata(image), **_deletion_state(image.deleted_at, image.deleted_by_id)}
    result = db.execute(
        update(AnswerImage)
        .where(AnswerImage.id == image.id, AnswerImage.deleted_at.is_not(None))
        .values(deleted_at=None, deleted_by_id=None)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        db.rollback()
        db.refresh(image)
        return image

    db.add(
        AuditEvent(
            actor_id=user.id,
            action="RESTORE_LOGICAL",
            resource_type="AnswerImage",
            resource_id=image.id,
            before_json=json.dumps(before),
            after_json=json.dumps(_deletion_state(None, None)),
        )
    )
    db.commit()
    db.refresh(image)
    log_event(
        "answer_image_restored",
        correlation_id,
        image_id=image.id,
        answer_id=image.answer_id,
        user_id=user.id,
    )
    return image
