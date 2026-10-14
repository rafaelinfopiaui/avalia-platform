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
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import unicodedata
import uuid
import warnings
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.db import get_db
from app.deps import require_role
from app.logging_utils import log_event, new_correlation_id
from app.models import Answer, AnswerImage, Question, User
from app.routers.academic import require_assessment_mutation
from app.schemas import AnswerImageOut

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


def _storage_dir() -> Path:
    return Path(get_settings().answer_images_storage_dir).resolve()


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
    return (
        db.query(AnswerImage)
        .filter(AnswerImage.answer_id == answer_id)
        .order_by(AnswerImage.created_at.desc(), AnswerImage.id.desc())
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
    storage_dir = _storage_dir()
    path = (storage_dir / image.storage_filename).resolve()
    if path.parent != storage_dir or not path.is_file():
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
