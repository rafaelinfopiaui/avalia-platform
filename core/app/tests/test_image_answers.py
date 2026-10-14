"""AV-S06B (complemento, DEC-AV-037) — resposta por imagem.

A foto é a entrada inicial da resposta, sem texto. A resposta nasce
AGUARDANDO_TRANSCRICAO e não pode ser corrigida até ter transcrição confirmada.
"""
from __future__ import annotations

import asyncio
import io
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from PIL import Image
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

import app.main as main_module
from app.config import get_settings
from app.models import (
    Answer,
    AnswerImage,
    AnswerSource,
    Assessment,
    AssessmentStatus,
    CorrectionJob,
    JobStatus,
    Question,
    Rubric,
    RubricCriterion,
    TranscriptionStatus,
    User,
)
from app.routers import images as images_module
from app.services import correction as correction_module


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _image_bytes(fmt: str = "PNG", size: tuple[int, int] = (32, 32)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(30, 120, 200)).save(buffer, format=fmt)
    return buffer.getvalue()


def _post_image_answer(
    client,
    token,
    question_id,
    content: bytes,
    *,
    student: str = "Aluno fictício",
    filename: str = "resposta.png",
    content_type: str = "image/png",
):
    return client.post(
        "/v1/answers/image",
        data={"question_id": question_id, "student_name_fake": student},
        files={"file": (filename, content, content_type)},
        headers=_headers(token),
    )


def _stored_files(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []


def _count(db_session, model) -> int:
    db_session.rollback()  # garante leitura do estado gravado pela requisição
    return db_session.query(model).count()


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "answer_images"
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(path))
    return path


@pytest.fixture()
def published_question(db_session, professor_token) -> str:
    """Questão de avaliação publicada, com rubrica publicada (correção possível)."""
    owner = _owner(db_session)
    assessment = Assessment(
        title="Avaliação com resposta por foto", owner_id=owner.id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = Question(
        assessment_id=assessment.id,
        statement="Descreva o ciclo da água.",
        reference_answer="Evaporação, condensação e precipitação.",
        max_score=Decimal("10.00"),
    )
    db_session.add(question)
    db_session.flush()
    rubric = Rubric(question_id=question.id, version=1, is_published=True)
    db_session.add(rubric)
    db_session.flush()
    db_session.add(RubricCriterion(rubric_id=rubric.id, name="Conteúdo", max_score=Decimal("10.00")))
    db_session.commit()
    return question.id


@pytest.fixture()
def no_background_correction(monkeypatch):
    """Evita rede no fluxo textual: só nos interessa o 202 e o job criado."""

    async def noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(main_module, "run_correction_job", noop)


# ---------------- ACI-01: criar resposta por imagem sem texto ----------------
def test_image_answer_is_created_without_text_awaiting_transcription(
    client, db_session, professor_token, published_question, storage_dir
):
    content = _image_bytes("PNG")
    resp = _post_image_answer(client, professor_token, published_question, content)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source"] == "IMAGE"
    assert body["transcription_status"] == "AGUARDANDO_TRANSCRICAO"
    assert body["text"] is None
    assert body["question_id"] == published_question
    assert body["student_name_fake"] == "Aluno fictício"
    [image] = body["images"]
    assert image["answer_id"] == body["id"]
    assert image["content_type"] == "image/png"
    assert image["size_bytes"] == len(content)
    assert "storage_filename" not in image

    db_session.rollback()
    answer = db_session.get(Answer, body["id"])
    assert answer.text is None  # nunca "" nem placeholder
    assert answer.source == AnswerSource.IMAGE
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert db_session.query(AnswerImage).filter_by(answer_id=answer.id).count() == 1
    [stored] = _stored_files(storage_dir)
    assert stored.read_bytes() == content
    assert _count(db_session, CorrectionJob) == 0


def test_image_answer_accepts_jpeg_and_lists_and_downloads(
    client, professor_token, published_question, storage_dir
):
    content = _image_bytes("JPEG")
    resp = _post_image_answer(
        client, professor_token, published_question, content, filename="foto.jpg", content_type="image/jpeg"
    )
    assert resp.status_code == 201, resp.text
    answer_id = resp.json()["id"]
    image_id = resp.json()["images"][0]["id"]

    listed = client.get(f"/v1/answers/{answer_id}/images", headers=_headers(professor_token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [image_id]
    download = client.get(f"/v1/answer-images/{image_id}/download", headers=_headers(professor_token))
    assert download.status_code == 200
    assert download.content == content


def test_image_answer_rejects_blank_student_name_before_writing(
    client, db_session, professor_token, published_question, storage_dir
):
    resp = _post_image_answer(client, professor_token, published_question, _image_bytes(), student="   ")
    assert resp.status_code == 422
    assert resp.json()["code"] == "STUDENT_NAME_REQUIRED"
    assert _count(db_session, Answer) == 0
    assert _stored_files(storage_dir) == []


def test_image_answer_rejects_invalid_image_without_records(
    client, db_session, professor_token, published_question, storage_dir
):
    resp = _post_image_answer(
        client, professor_token, published_question, b"%PDF-1.4 nao e imagem", content_type="image/png"
    )
    assert resp.status_code == 422
    assert _count(db_session, Answer) == 0
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_image_answer_rejects_oversized_file(
    client, db_session, professor_token, published_question, storage_dir, monkeypatch
):
    monkeypatch.setattr(get_settings(), "answer_image_max_bytes", 1024)
    resp = _post_image_answer(client, professor_token, published_question, b"\x89PNG" + b"\x00" * 2000)
    assert resp.status_code == 413
    assert _count(db_session, Answer) == 0
    assert _stored_files(storage_dir) == []


def test_image_answer_missing_question_returns_404(client, db_session, professor_token, storage_dir):
    resp = _post_image_answer(client, professor_token, "inexistente", _image_bytes())
    assert resp.status_code == 404
    assert _stored_files(storage_dir) == []


def test_repeated_image_answer_request_creates_another_answer(
    client, db_session, professor_token, published_question, storage_dir
):
    # Sem idempotência/deduplicação: política de reenvio não aprovada (desenho §8).
    content = _image_bytes()
    first = _post_image_answer(client, professor_token, published_question, content)
    second = _post_image_answer(client, professor_token, published_question, content)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert _count(db_session, Answer) == 2


# ---------------- ACI-02: correção bloqueada sem transcrição ----------------
def test_correction_of_untranscribed_image_answer_is_blocked(
    client, db_session, professor_token, published_question, storage_dir
):
    answer_id = _post_image_answer(client, professor_token, published_question, _image_bytes()).json()["id"]
    resp = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "ANSWER_NOT_TRANSCRIBED"
    assert "transcrição confirmada" in body["message"]
    assert _count(db_session, CorrectionJob) == 0


def test_correction_guard_does_not_leak_state_to_other_professor(
    client, db_session, professor_token, second_professor_token, published_question, storage_dir
):
    answer_id = _post_image_answer(client, professor_token, published_question, _image_bytes()).json()["id"]
    resp = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(second_professor_token))
    assert resp.status_code == 403
    assert _count(db_session, CorrectionJob) == 0


# ---------------- ACI-03: fluxo textual inalterado ----------------
def test_text_answer_flow_is_unchanged(
    client, db_session, professor_token, published_question, no_background_correction
):
    resp = client.post(
        "/v1/answers",
        json={"question_id": published_question, "student_name_fake": "Aluno", "text": "Evaporação e chuva."},
        headers=_headers(professor_token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source"] == "TEXT"
    assert body["transcription_status"] == "TRANSCRICAO_CONFIRMADA"
    assert body["text"] == "Evaporação e chuva."

    resp = client.post(f"/v1/answers/{body['id']}/corrections", headers=_headers(professor_token))
    assert resp.status_code == 202, resp.text
    assert resp.json()["status"] == "PENDENTE"
    assert _count(db_session, CorrectionJob) == 1


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_text_answer_with_blank_text_is_rejected(client, db_session, professor_token, published_question, text):
    resp = client.post(
        "/v1/answers",
        json={"question_id": published_question, "student_name_fake": "Aluno", "text": text},
        headers=_headers(professor_token),
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "ANSWER_TEXT_REQUIRED"
    assert _count(db_session, Answer) == 0


def test_check_constraint_rejects_text_answer_without_text(db_session, published_question):
    db_session.add(
        Answer(question_id=published_question, student_name_fake="Aluno", text=None, source=AnswerSource.TEXT)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------- ACI-04: autorização no novo endpoint ----------------
def test_image_answer_without_token_returns_401(client, db_session, published_question, storage_dir):
    resp = _post_image_answer(client, None, published_question, _image_bytes())
    assert resp.status_code == 401
    assert _count(db_session, Answer) == 0
    assert _stored_files(storage_dir) == []


def test_image_answer_by_unrelated_professor_returns_403(
    client, db_session, second_professor_token, published_question, storage_dir
):
    resp = _post_image_answer(client, second_professor_token, published_question, _image_bytes())
    assert resp.status_code == 403
    assert _count(db_session, Answer) == 0
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_admin_can_create_image_answer(client, admin_token, published_question, storage_dir):
    resp = _post_image_answer(client, admin_token, published_question, _image_bytes())
    assert resp.status_code == 201, resp.text


# ---------------- ACI-05: falha de commit sem órfãos ----------------
def test_commit_failure_leaves_no_answer_image_or_file(
    client, db_session, professor_token, published_question, storage_dir, monkeypatch
):
    def fail_commit(_self):
        raise OperationalError("COMMIT", {}, Exception("banco indisponível simulado"))

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        resp = _post_image_answer(client, professor_token, published_question, _image_bytes())
    assert resp.status_code == 500
    assert _count(db_session, Answer) == 0
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_file_finalize_failure_leaves_no_records(
    client, db_session, professor_token, published_question, storage_dir, monkeypatch
):
    def fail_replace(*_args, **_kwargs):
        raise OSError("disco cheio simulado")

    monkeypatch.setattr(images_module.os, "replace", fail_replace)
    resp = _post_image_answer(client, professor_token, published_question, _image_bytes())
    assert resp.status_code == 500
    assert _count(db_session, Answer) == 0
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


# ---------------- ACI-06: reenvio preserva anteriores (DEC-AV-018) ----------------
def test_resend_on_existing_image_answer_preserves_previous(
    client, professor_token, published_question, storage_dir
):
    created = _post_image_answer(client, professor_token, published_question, _image_bytes()).json()
    answer_id, first_id = created["id"], created["images"][0]["id"]
    resend = client.post(
        f"/v1/answers/{answer_id}/images",
        files={"file": ("nova.png", _image_bytes("PNG", (16, 16)), "image/png")},
        headers=_headers(professor_token),
    )
    assert resend.status_code == 201, resend.text
    listed = client.get(f"/v1/answers/{answer_id}/images", headers=_headers(professor_token)).json()
    assert [item["id"] for item in listed] == [resend.json()["id"], first_id]
    assert len(_stored_files(storage_dir)) == 2


# ---------------- ACI-09: defesa em profundidade no job ----------------
@pytest.mark.parametrize(
    ("text", "source", "status"),
    [
        (None, AnswerSource.IMAGE, TranscriptionStatus.AGUARDANDO_TRANSCRICAO),
        ("   ", AnswerSource.TEXT, TranscriptionStatus.TRANSCRICAO_CONFIRMADA),
    ],
    ids=["image-without-text", "blank-text"],
)
def test_run_correction_job_fails_fast_without_calling_ai_engine(
    test_engine, db_session, published_question, monkeypatch, text, source, status
):
    calls: list[tuple] = []

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("AI Engine não pode ser chamado")

    monkeypatch.setattr(httpx, "AsyncClient", ForbiddenClient)

    rubric = db_session.query(Rubric).filter_by(question_id=published_question).one()
    answer = Answer(
        question_id=published_question,
        student_name_fake="Aluno",
        text=text,
        source=source,
        transcription_status=status,
    )
    db_session.add(answer)
    db_session.flush()
    job = CorrectionJob(answer_id=answer.id, rubric_id=rubric.id, status=JobStatus.PENDENTE)
    db_session.add(job)
    db_session.commit()
    job_id = job.id

    factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    asyncio.run(correction_module.run_correction_job(job_id, factory))

    assert calls == []
    db_session.expire_all()
    job = db_session.get(CorrectionJob, job_id)
    assert job.status == JobStatus.FALHA
    assert "transcrição confirmada" in job.error_message
