"""AV-S07B — extração OCR/visão experimental (DEC-AV-046).

POST /v1/answers/{id}/transcription/extract: autoriza por propriedade/vínculo,
usa só a imagem ativa (a mais recente, de forma explícita), grava
TranscriptionExtraction, preenche o rascunho apenas se vazio e NUNCA confirma
nem dispara correção. O AI Engine é sempre substituído por stub (sem Ollama
real); as imagens são sintéticas, geradas pelo Pillow.
"""
from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image

import app.main as main_module
from app.config import get_settings
from app.models import (
    Answer,
    AnswerImage,
    AnswerSource,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    CorrectionJob,
    Question,
    Rubric,
    RubricCriterion,
    TranscriptionExtraction,
    TranscriptionStatus,
    User,
)

EXTRACTED = "A pilha é LIFU e a fila é FIFO."  # erro do aluno preservado


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _extract(client, token, answer_id, answer_image_id=None):
    json_body = {"answer_image_id": answer_image_id} if answer_image_id is not None else None
    return client.post(
        f"/v1/answers/{answer_id}/transcription/extract", headers=_headers(token), json=json_body
    )


def _png_bytes(color=(10, 20, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


class _EngineStub:
    """Substitui _call_ai_engine_extract e registra o que foi enviado."""

    def __init__(self, response: dict):
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def __call__(self, image_base64: str, mime_type: str) -> dict:
        self.calls.append((image_base64, mime_type))
        return self.response


def _ok(text=EXTRACTED):
    return {"status": "ok", "text": text, "model": "qwen2.5vl:3b", "duration_ms": 1234, "error_detail": None}


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "answer_images"
    path.mkdir()
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(path))
    return path


@pytest.fixture()
def engine(monkeypatch):
    def install(response: dict) -> _EngineStub:
        stub = _EngineStub(response)
        monkeypatch.setattr(main_module, "_call_ai_engine_extract", stub)
        return stub

    return install


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


@pytest.fixture()
def question_id(db_session, professor_token) -> str:
    assessment = Assessment(
        title="Avaliação com extração", owner_id=_owner(db_session).id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = Question(
        assessment_id=assessment.id,
        statement="ENUNCIADO-SECRETO-NAO-ENVIAR",
        reference_answer="REFERENCIA-SECRETA-NAO-ENVIAR",
        max_score=Decimal("10.00"),
        position=1,
    )
    db_session.add(question)
    db_session.flush()
    rubric = Rubric(question_id=question.id, version=1, is_published=True)
    db_session.add(rubric)
    db_session.flush()
    db_session.add(RubricCriterion(rubric_id=rubric.id, name="Conteúdo", max_score=Decimal("10.00")))
    db_session.commit()
    return question.id


def _add_image(
    db_session, storage_dir, answer_id, *, created_at=None, color=(10, 20, 30), deleted=False
) -> AnswerImage:
    content = _png_bytes(color)
    image = AnswerImage(
        answer_id=answer_id,
        storage_filename=f"{answer_id}-{color[0]}.png",
        original_filename="sintetica.png",
        content_type="image/png",
        size_bytes=len(content),
        sha256_hash="0" * 64,
        uploaded_by_id=_owner(db_session).id,
        created_at=created_at or datetime.utcnow(),
        deleted_at=datetime.utcnow() if deleted else None,
    )
    (storage_dir / image.storage_filename).write_bytes(content)
    db_session.add(image)
    db_session.commit()
    return image


@pytest.fixture()
def answer_id(db_session, question_id, storage_dir) -> str:
    answer = Answer(
        question_id=question_id,
        student_name_fake="Aluno fictício",
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.commit()
    _add_image(db_session, storage_dir, answer.id)
    return answer.id


def _current(db_session, answer_id) -> Answer:
    db_session.expire_all()
    return db_session.get(Answer, answer_id)


def _extractions(db_session, answer_id) -> list[TranscriptionExtraction]:
    db_session.expire_all()
    return db_session.query(TranscriptionExtraction).filter_by(answer_id=answer_id).all()


def test_image_deleted_during_inference_result_not_applied_to_draft(
    client, db_session, professor_token, answer_id, monkeypatch
):
    # ALTA-2 (fecho do TOCTOU): se a imagem for excluída DURANTE a inferência
    # (entre a revalidação e a gravação), o resultado NÃO é aplicado ao rascunho.
    image = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()

    class DeleteDuringCall:
        calls: list = []

        async def __call__(self, image_base64, mime_type):
            self.calls.append((image_base64, mime_type))
            # Simula exclusão concorrente durante a chamada ao motor.
            img = db_session.query(AnswerImage).filter_by(id=image.id).one()
            img.deleted_at = datetime.utcnow()
            db_session.commit()
            return _ok()

    stub = DeleteDuringCall()
    monkeypatch.setattr(main_module, "_call_ai_engine_extract", stub)

    response = _extract(client, professor_token, answer_id)
    assert response.status_code == 200, response.text
    body = response.json()
    # O motor até foi chamado, mas o resultado não contamina o rascunho.
    assert len(stub.calls) == 1
    assert body["status"] == "falha"
    assert body["draft_updated"] is False
    assert body["extracted_text"] == ""  # contrato: fora de 'ok' não há texto
    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft is None  # rascunho intacto
    [record] = _extractions(db_session, answer_id)
    assert record.status == "falha"
    assert record.raw_output == ""  # não persiste conteúdo sob falha
    assert record.error_detail == "IMAGE_NO_LONGER_ACTIVE"


# ---------------- Sucesso: rascunho vazio é preenchido, sem confirmar ----------------
def test_ok_fills_empty_draft_without_confirming_or_correcting(
    client, db_session, professor_token, answer_id, engine
):
    stub = engine(_ok())

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["extracted_text"] == EXTRACTED
    assert body["draft_updated"] is True
    assert body["draft_origin"] == "OCR"
    assert body["transcription_version"] == 1
    assert "NÃO foi confirmada" in body["message"]

    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft == EXTRACTED
    assert answer.transcription_version == 1
    assert answer.text is None
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert answer.transcription_confirmed_by_id is None
    assert db_session.query(CorrectionJob).count() == 0

    [record] = _extractions(db_session, answer_id)
    assert record.id == body["extraction_id"]
    assert record.status == "ok"
    assert record.raw_output == EXTRACTED
    assert record.engine == "ollama-vision"
    assert record.model == "qwen2.5vl:3b"
    assert record.duration_ms == 1234
    assert record.answer_image_id == body["answer_image_id"]

    # Só a imagem entra no motor: base64 do arquivo real, nada de enunciado/referência.
    [(sent_b64, sent_mime)] = stub.calls
    image = db_session.get(AnswerImage, record.answer_image_id)
    stored = Path(get_settings().answer_images_storage_dir) / image.storage_filename
    assert base64.b64decode(sent_b64) == stored.read_bytes()
    assert sent_mime == "image/png"

    origin = (
        db_session.query(AuditEvent)
        .filter_by(resource_id=answer_id, action="transcription_draft_filled_by_extraction")
        .one()
    )
    assert json.loads(origin.after_json)["draft_origin"] == "OCR"
    # Auditoria não guarda o texto extraído.
    for event in db_session.query(AuditEvent).all():
        assert EXTRACTED not in (event.after_json or "")


def test_engine_payload_never_contains_question_text(client, professor_token, answer_id, monkeypatch):
    sent: list[dict] = []

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return _ok()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            sent.append({"timeout": kwargs.get("timeout")})

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json):
            sent.append({"url": url, "json": json})
            return FakeResponse()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", FakeClient)

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    assert sent[0]["timeout"] == main_module._EXTRACTION_TIMEOUT_SECONDS
    call = sent[1]
    assert call["url"].endswith("/v1/extract")
    assert set(call["json"]) == {"image_base64", "mime_type"}
    serialized = json.dumps(call["json"])
    assert "ENUNCIADO-SECRETO" not in serialized
    assert "REFERENCIA-SECRETA" not in serialized


# ---------------- Rascunho manual preenchido não é sobrescrito ----------------
def test_existing_manual_draft_is_not_overwritten(client, db_session, professor_token, answer_id, engine):
    engine(_ok())
    saved = client.patch(
        f"/v1/answers/{answer_id}/manual-transcription/draft",
        json={"text": "Rascunho digitado pelo professor.", "expected_version": 0},
        headers=_headers(professor_token),
    )
    assert saved.status_code == 200, saved.text

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["draft_updated"] is False
    assert body["draft_origin"] is None
    assert body["extracted_text"] == EXTRACTED  # devolvido para o usuário decidir
    assert body["transcription_version"] == 1
    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft == "Rascunho digitado pelo professor."
    assert answer.transcription_version == 1
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO


# ---------------- 'vazio' e 'falha' não fabricam texto nem confirmam ----------------
@pytest.mark.parametrize(
    "engine_response, expected_status",
    [
        ({"status": "vazio", "text": "", "model": "qwen2.5vl:3b", "duration_ms": 50, "error_detail": None}, "vazio"),
        # 'ok' com texto só de espaços é rebaixado para 'vazio'.
        ({"status": "ok", "text": "   \n", "model": "qwen2.5vl:3b", "duration_ms": 50, "error_detail": None}, "vazio"),
        ({"status": "falha", "text": "", "model": "x", "duration_ms": 0, "error_detail": "Timeout"}, "falha"),
        # Texto vindo junto de 'falha' é descartado (nunca vira rascunho).
        ({"status": "falha", "text": "lixo", "model": "x", "duration_ms": 0, "error_detail": "HTTP 500"}, "falha"),
        # Resposta fora do contrato vira 'falha'.
        ({"resultado": "qualquer"}, "falha"),
    ],
)
def test_empty_and_failure_never_fabricate_text(
    client, db_session, professor_token, answer_id, engine, engine_response, expected_status
):
    engine(engine_response)

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == expected_status
    assert body["extracted_text"] == ""
    assert body["draft_updated"] is False
    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft is None
    assert answer.text is None
    assert answer.transcription_version == 0
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert db_session.query(CorrectionJob).count() == 0
    [record] = _extractions(db_session, answer_id)
    assert record.status == expected_status
    assert record.raw_output == ""


def test_ai_engine_unreachable_is_recorded_as_failure(client, db_session, professor_token, answer_id):
    # Sem stub: conftest aponta AI_ENGINE_URL para porta inexistente.
    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "falha"
    assert body["extracted_text"] == ""
    [record] = _extractions(db_session, answer_id)
    assert record.status == "falha"
    assert record.error_detail and "AI Engine" in record.error_detail
    assert _current(db_session, answer_id).manual_transcription_draft is None


# ---------------- Autorização ----------------
def test_non_owner_professor_gets_403_without_calling_engine(
    client, db_session, second_professor_token, answer_id, engine
):
    stub = engine(_ok())

    response = _extract(client, second_professor_token, answer_id)

    assert response.status_code == 403
    assert stub.calls == []
    assert _extractions(db_session, answer_id) == []


def test_admin_can_extract(client, admin_token, answer_id, engine):
    engine(_ok())
    response = _extract(client, admin_token, answer_id)
    assert response.status_code == 200, response.text


def test_unauthenticated_is_rejected(client, answer_id, engine):
    stub = engine(_ok())
    response = client.post(f"/v1/answers/{answer_id}/transcription/extract")
    assert response.status_code == 401
    assert stub.calls == []


def test_unknown_answer_is_404(client, professor_token, engine):
    engine(_ok())
    assert _extract(client, professor_token, "inexistente").status_code == 404


# ---------------- Pré-condições ----------------
def test_answer_without_active_image_returns_clear_error(
    client, db_session, professor_token, question_id, storage_dir, engine
):
    stub = engine(_ok())
    answer = Answer(
        question_id=question_id,
        student_name_fake="Aluno sem imagem ativa",
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.commit()
    _add_image(db_session, storage_dir, answer.id, deleted=True)

    response = _extract(client, professor_token, answer.id)

    assert response.status_code == 409
    assert response.json()["code"] == "ANSWER_HAS_NO_ACTIVE_IMAGE"
    assert "imagem ativa" in response.json()["message"]
    assert stub.calls == []
    assert _extractions(db_session, answer.id) == []


def test_missing_file_returns_clear_error(client, db_session, professor_token, answer_id, storage_dir, engine):
    stub = engine(_ok())
    for path in storage_dir.iterdir():
        path.unlink()

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 409
    assert response.json()["code"] == "ANSWER_IMAGE_FILE_MISSING"
    assert stub.calls == []


def test_text_answer_is_rejected(client, professor_token, question_id, engine):
    stub = engine(_ok())
    created = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno T", "text": "Digitada."},
        headers=_headers(professor_token),
    )
    assert created.status_code == 201, created.text

    response = _extract(client, professor_token, created.json()["id"])

    assert response.status_code == 422
    assert response.json()["code"] == "ANSWER_NOT_IMAGE_SOURCE"
    assert stub.calls == []


def test_confirmed_transcription_is_not_reextracted(client, db_session, professor_token, answer_id, engine):
    stub = engine(_ok())
    confirmed = client.post(
        f"/v1/answers/{answer_id}/manual-transcription/confirm",
        json={"text": "Texto confirmado.", "expected_version": 0},
        headers=_headers(professor_token),
    )
    assert confirmed.status_code == 200, confirmed.text

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 409
    assert response.json()["code"] == "TRANSCRIPTION_ALREADY_CONFIRMED"
    assert stub.calls == []
    assert _current(db_session, answer_id).text == "Texto confirmado."


# ---------------- Múltiplas imagens ativas: escolha explícita ----------------
def test_multiple_active_images_requires_explicit_selection(
    client, db_session, professor_token, answer_id, storage_dir, engine
):
    # BLOQUEANTE-1: com >1 imagem ativa e sem seleção explícita, a extração é
    # RECUSADA (nunca escolhe silenciosamente). Nada é enviado ao motor.
    stub = engine(_ok())
    older = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()
    newer = _add_image(
        db_session, storage_dir, answer_id, created_at=older.created_at + timedelta(minutes=5), color=(99, 0, 0)
    )

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 409, response.text
    body = response.json()
    assert body["code"] == "MULTIPLE_ACTIVE_IMAGES_REQUIRE_EXPLICIT_SELECTION"
    assert set(body["details"]["active_image_ids"]) == {older.id, newer.id}
    assert stub.calls == []  # motor não chamado
    assert _extractions(db_session, answer_id) == []  # nada persistido
    assert _current(db_session, answer_id).manual_transcription_draft is None


def test_multiple_active_images_with_explicit_selection_uses_chosen(
    client, db_session, professor_token, answer_id, storage_dir, engine
):
    # Com answer_image_id EXPLÍCITO, extrai a imagem indicada (mesmo não sendo a
    # mais recente) e registra a escolha explícita.
    engine(_ok())
    older = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()
    _newer = _add_image(
        db_session, storage_dir, answer_id, created_at=older.created_at + timedelta(minutes=5), color=(99, 0, 0)
    )

    response = _extract(client, professor_token, answer_id, answer_image_id=older.id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answer_image_id"] == older.id
    [record] = _extractions(db_session, answer_id)
    selection = json.loads(record.config_json)["image_selection"]
    assert selection["chosen_image_id"] == older.id
    assert selection["explicit_selection"] is True
    assert "explicit" in selection["criterion"] or "explícita" in selection["criterion"]


def test_explicit_selection_of_unknown_image_is_rejected(
    client, db_session, professor_token, answer_id, engine
):
    stub = engine(_ok())
    response = _extract(client, professor_token, answer_id, answer_image_id="nao-existe-123")
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "ANSWER_IMAGE_NOT_ACTIVE"
    assert stub.calls == []
    assert _extractions(db_session, answer_id) == []


# ---------------- Idempotência / anti-duplo-clique ----------------
def test_concurrent_extraction_is_blocked_while_processing(
    client, db_session, professor_token, answer_id, engine
):
    stub = engine(_ok())
    image = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()
    in_flight = TranscriptionExtraction(
        answer_id=answer_id,
        answer_image_id=image.id,
        engine="ollama-vision",
        model="",
        config_json="{}",
        status="processando",
        raw_output="",
        duration_ms=0,
    )
    db_session.add(in_flight)
    db_session.commit()

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 409
    assert response.json()["code"] == "EXTRACTION_IN_PROGRESS"
    assert response.json()["details"]["extraction_id"] == in_flight.id
    assert stub.calls == []
    assert len(_extractions(db_session, answer_id)) == 1
    assert _current(db_session, answer_id).manual_transcription_draft is None


def test_stale_processing_record_does_not_block_forever(
    client, db_session, professor_token, answer_id, engine
):
    engine(_ok())
    image = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()
    stale = TranscriptionExtraction(
        answer_id=answer_id,
        answer_image_id=image.id,
        engine="ollama-vision",
        model="",
        config_json="{}",
        status="processando",
        raw_output="",
        duration_ms=0,
        created_at=datetime.utcnow() - timedelta(seconds=main_module._EXTRACTION_STALE_SECONDS + 1),
    )
    db_session.add(stale)
    db_session.commit()
    stale_id = stale.id

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.get(TranscriptionExtraction, stale_id).status == "falha"


def test_repeated_click_creates_new_record_but_never_overwrites_ocr_draft(
    client, db_session, professor_token, answer_id, engine
):
    engine(_ok())
    first = _extract(client, professor_token, answer_id)
    assert first.json()["draft_updated"] is True

    engine(_ok("Outra leitura diferente."))
    second = _extract(client, professor_token, answer_id)

    assert second.status_code == 200, second.text
    assert second.json()["draft_updated"] is False
    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft == EXTRACTED
    assert answer.transcription_version == 1
    assert len(_extractions(db_session, answer_id)) == 2
    assert db_session.query(CorrectionJob).count() == 0


def test_extraction_flow_does_not_reference_correction():
    """A extração nunca chama request_correction/run_correction_job nem cria CorrectionJob."""
    import ast
    import inspect

    for function in (
        main_module.extract_transcription, main_module._run_extraction, main_module._call_ai_engine_extract
    ):
        tree = ast.parse(inspect.getsource(function).lstrip())
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert not names & {"request_correction", "run_correction_job", "CorrectionJob", "BackgroundTasks"}
