"""AV-S08B — transcrição manual e confirmação humana (DEC-AV-040).

PATCH /v1/answers/{id}/manual-transcription/draft e
POST  /v1/answers/{id}/manual-transcription/confirm são mutações: exigem
propriedade + vínculo ativo de turma, usam lock otimista por
`transcription_version` e nunca criam CorrectionJob nem chamam
request_correction. A confirmação é definitiva nesta fatia (DP-2).

Os testes de concorrência real (ACD-15/16) rodam contra PostgreSQL isolado,
indicado por AVALIA_TEST_POSTGRES_URL; sem a variável, são pulados (SQLite
serializa escritas por arquivo e não prova o comportamento do lock).
"""
from __future__ import annotations

import ast
import inspect
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app import db as db_module
from app.config import get_settings
from app.db import Base
from app.models import (
    Answer,
    AnswerSource,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    ClassGroup,
    CorrectionJob,
    Course,
    CourseDiscipline,
    Discipline,
    HumanReview,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Question,
    ReviewDecision,
    Role,
    Rubric,
    RubricCriterion,
    TranscriptionStatus,
    User,
)
from app.security import hash_password

DRAFT_ACTION = "manual_transcription_draft_saved"
CONFIRM_ACTION = "manual_transcription_confirmed"


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _draft(client, token, answer_id, text, expected_version):
    return client.patch(
        f"/v1/answers/{answer_id}/manual-transcription/draft",
        json={"text": text, "expected_version": expected_version},
        headers=_headers(token),
    )


def _confirm(client, token, answer_id, text, expected_version):
    return client.post(
        f"/v1/answers/{answer_id}/manual-transcription/confirm",
        json={"text": text, "expected_version": expected_version},
        headers=_headers(token),
    )


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


def _question(db_session, assessment_id: str) -> Question:
    question = Question(
        assessment_id=assessment_id,
        statement="Enunciado fictício.",
        reference_answer="Resposta de referência.",
        max_score=Decimal("10.00"),
        position=1,
    )
    db_session.add(question)
    db_session.flush()
    rubric = Rubric(question_id=question.id, version=1, is_published=True)
    db_session.add(rubric)
    db_session.flush()
    db_session.add(RubricCriterion(rubric_id=rubric.id, name="Conteúdo", max_score=Decimal("10.00")))
    return question


def _image_answer(db_session, question_id: str, student: str = "Aluno fictício") -> Answer:
    answer = Answer(
        question_id=question_id,
        student_name_fake=student,
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.commit()
    return answer


def _current(db_session, answer_id: str) -> Answer:
    db_session.expire_all()
    return db_session.get(Answer, answer_id)


def _audit(db_session, answer_id: str, action: str) -> list[AuditEvent]:
    db_session.expire_all()
    return (
        db_session.query(AuditEvent)
        .filter_by(resource_type="Answer", resource_id=answer_id, action=action)
        .order_by(AuditEvent.created_at, AuditEvent.id)
        .all()
    )


@pytest.fixture()
def question_id(db_session, professor_token) -> str:
    assessment = Assessment(
        title="Avaliação com transcrição manual", owner_id=_owner(db_session).id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id)
    db_session.commit()
    return question.id


@pytest.fixture()
def answer_id(db_session, question_id) -> str:
    return _image_answer(db_session, question_id).id


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "answer_images"
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(path))
    return path


# ---------------- ACD-01: rascunho não confirma, versão incrementa ----------------
def test_draft_saves_without_touching_text_or_status(client, db_session, professor_token, answer_id):
    first = _draft(client, professor_token, answer_id, "Primeira leitura.", 0)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["manual_transcription_draft"] == "Primeira leitura."
    assert body["transcription_version"] == 1
    assert body["text"] is None
    assert body["transcription_status"] == "AGUARDANDO_TRANSCRICAO"
    assert body["transcription_confirmed_by_id"] is None
    assert body["transcription_confirmed_at"] is None
    assert "images" in body

    second = _draft(client, professor_token, answer_id, "Segunda leitura.", 1)
    assert second.status_code == 200, second.text
    assert second.json()["transcription_version"] == 2

    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft == "Segunda leitura."
    assert answer.text is None
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert answer.transcription_version == 2


# ---------------- ACD-01B: rascunho e versão recuperáveis pela listagem ----------------
def test_listing_exposes_draft_and_version_for_resumption(client, professor_token, question_id, storage_dir):
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(buffer, format="PNG")
    created = client.post(
        "/v1/answers/image",
        data={"question_id": question_id, "student_name_fake": "Aluno A"},
        files={"file": ("resposta.png", buffer.getvalue(), "image/png")},
        headers=_headers(professor_token),
    )
    assert created.status_code == 201, created.text
    assert created.json()["transcription_version"] == 0
    assert created.json()["manual_transcription_draft"] is None
    answer_id = created.json()["id"]
    assessment_id = client.get("/v1/assessments", headers=_headers(professor_token)).json()[0]["id"]

    assert _draft(client, professor_token, answer_id, "Rascunho salvo antes do F5.", 0).status_code == 200

    # Nova leitura (equivale a reload/nova sessão): mesmo endpoint de DEBT-AV-014.
    [item] = client.get(
        f"/v1/assessments/{assessment_id}/image-answers", headers=_headers(professor_token)
    ).json()
    assert item["id"] == answer_id
    assert item["manual_transcription_draft"] == "Rascunho salvo antes do F5."
    assert item["transcription_version"] == 1
    assert len(item["images"]) == 1


# ---------------- ACD-02: resposta TEXT rejeitada ----------------
def test_text_answer_rejects_draft_and_confirm(client, db_session, professor_token, question_id):
    created = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno T", "text": "Resposta digitada."},
        headers=_headers(professor_token),
    )
    assert created.status_code == 201, created.text
    text_answer_id = created.json()["id"]

    draft = _draft(client, professor_token, text_answer_id, "Outro texto.", 0)
    confirm = _confirm(client, professor_token, text_answer_id, "Outro texto.", 0)
    for response in (draft, confirm):
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "ANSWER_NOT_IMAGE_SOURCE"

    answer = _current(db_session, text_answer_id)
    assert answer.text == "Resposta digitada."
    assert answer.manual_transcription_draft is None
    assert answer.transcription_version == 0
    assert _audit(db_session, text_answer_id, DRAFT_ACTION) == []
    assert _audit(db_session, text_answer_id, CONFIRM_ACTION) == []


# ---------------- ACD-03: confirmação preenche texto, estado, autoria e data ----------------
def test_confirm_sets_text_status_author_and_timestamp(client, db_session, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "Rascunho.", 0).status_code == 200

    response = _confirm(client, professor_token, answer_id, "Texto final conferido.", 1)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["text"] == "Texto final conferido."
    assert body["transcription_status"] == "TRANSCRICAO_CONFIRMADA"
    assert body["transcription_version"] == 2
    assert body["manual_transcription_draft"] is None
    assert body["transcription_confirmed_by_id"] == _owner(db_session).id
    assert body["transcription_confirmed_at"] is not None

    answer = _current(db_session, answer_id)
    assert answer.text == "Texto final conferido."
    assert answer.transcription_status == TranscriptionStatus.TRANSCRICAO_CONFIRMADA
    assert answer.transcription_confirmed_by_id == _owner(db_session).id
    assert answer.transcription_confirmed_at is not None
    assert answer.manual_transcription_draft is None


# ---------------- ACD-04: texto vazio na confirmação; rascunho vazio permitido ----------------
@pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
def test_confirm_with_blank_text_is_rejected_without_changes(client, db_session, professor_token, answer_id, blank):
    assert _draft(client, professor_token, answer_id, "Rascunho preservado.", 0).status_code == 200

    response = _confirm(client, professor_token, answer_id, blank, 1)
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "ANSWER_TEXT_REQUIRED"

    answer = _current(db_session, answer_id)
    assert answer.text is None
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert answer.manual_transcription_draft == "Rascunho preservado."
    assert answer.transcription_version == 1
    assert _audit(db_session, answer_id, CONFIRM_ACTION) == []


def test_blank_draft_is_allowed_and_clears_previous_draft(client, db_session, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "Algo a descartar.", 0).status_code == 200

    response = _draft(client, professor_token, answer_id, "", 1)
    assert response.status_code == 200, response.text
    assert response.json()["manual_transcription_draft"] is None
    assert response.json()["transcription_version"] == 2

    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft is None
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO


# ---------------- ACD-05: autorização de mutação ----------------
def test_without_token_returns_401(client, answer_id):
    assert _draft(client, None, answer_id, "x", 0).status_code == 401
    assert _confirm(client, None, answer_id, "x", 0).status_code == 401


def test_other_professor_is_forbidden(client, db_session, professor_token, second_professor_token, answer_id):
    assert _draft(client, second_professor_token, answer_id, "Invasão.", 0).status_code == 403
    assert _confirm(client, second_professor_token, answer_id, "Invasão.", 0).status_code == 403

    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft is None
    assert answer.text is None
    assert answer.transcription_version == 0


def test_admin_can_draft_and_confirm(client, db_session, professor_token, admin_token, answer_id):
    assert _draft(client, admin_token, answer_id, "Rascunho do admin.", 0).status_code == 200
    response = _confirm(client, admin_token, answer_id, "Confirmado pelo admin.", 1)
    assert response.status_code == 200, response.text
    admin = db_session.query(User).filter_by(email="admin@example.com").one()
    assert response.json()["transcription_confirmed_by_id"] == admin.id


def _class_assessment_answer(db_session, *, active_link: bool) -> str:
    owner = _owner(db_session)
    organization = Organization(name="Org transcrição")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name="Curso", code="CUR-TRN")
    discipline = Discipline(organization_id=organization.id, name="Disciplina", code="DISC-TRN")
    db_session.add_all([course, discipline])
    db_session.flush()
    course_discipline = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(course_discipline)
    db_session.flush()
    class_group = ClassGroup(course_discipline_id=course_discipline.id, period="2026-2", code="T-TRN")
    db_session.add(class_group)
    db_session.flush()
    if active_link:
        db_session.add(
            ProfessorClassLink(
                professor_id=owner.id, class_group_id=class_group.id, role=ProfessorRole.RESPONSIBLE, active=True
            )
        )
    assessment = Assessment(
        title="Avaliação de turma",
        owner_id=owner.id,
        class_group_id=class_group.id,
        status=AssessmentStatus.PUBLICADA,
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id)
    return _image_answer(db_session, question.id).id


def test_owner_without_active_class_link_is_forbidden(client, db_session, professor_token):
    answer_id = _class_assessment_answer(db_session, active_link=False)

    draft = _draft(client, professor_token, answer_id, "Sem vínculo.", 0)
    confirm = _confirm(client, professor_token, answer_id, "Sem vínculo.", 0)
    assert draft.status_code == 403, draft.text
    assert confirm.status_code == 403, confirm.text
    answer = _current(db_session, answer_id)
    assert answer.transcription_version == 0
    assert answer.text is None


def test_owner_with_active_class_link_can_confirm(client, db_session, professor_token):
    answer_id = _class_assessment_answer(db_session, active_link=True)

    assert _draft(client, professor_token, answer_id, "Com vínculo.", 0).status_code == 200
    assert _confirm(client, professor_token, answer_id, "Com vínculo.", 1).status_code == 200


# ---------------- ACD-06: confirmação repetida ----------------
def test_repeated_identical_confirm_is_idempotent_without_new_audit(client, db_session, professor_token, answer_id):
    first = _confirm(client, professor_token, answer_id, "Texto final.", 0)
    assert first.status_code == 200, first.text
    confirmed_at = first.json()["transcription_confirmed_at"]

    again = _confirm(client, professor_token, answer_id, "Texto final.", 1)
    assert again.status_code == 200, again.text
    assert again.json()["transcription_version"] == 1
    assert again.json()["transcription_confirmed_at"] == confirmed_at
    assert len(_audit(db_session, answer_id, CONFIRM_ACTION)) == 1


def test_repeated_identical_confirm_with_stale_version_is_version_conflict(
    client, db_session, professor_token, answer_id
):
    assert _confirm(client, professor_token, answer_id, "Texto final.", 0).status_code == 200

    stale = _confirm(client, professor_token, answer_id, "Texto final.", 0)
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "TRANSCRIPTION_VERSION_CONFLICT"
    assert stale.json()["details"]["current_answer"]["transcription_version"] == 1
    assert len(_audit(db_session, answer_id, CONFIRM_ACTION)) == 1


def test_confirm_with_different_text_after_confirmation_conflicts(client, db_session, professor_token, answer_id):
    assert _confirm(client, professor_token, answer_id, "Texto final.", 0).status_code == 200

    for expected_version in (0, 1, 7):
        response = _confirm(client, professor_token, answer_id, "Texto alterado.", expected_version)
        assert response.status_code == 409, response.text
        body = response.json()
        assert body["code"] == "TRANSCRIPTION_ALREADY_CONFIRMED"
        assert body["details"]["current_answer"]["text"] == "Texto final."
        assert body["details"]["current_answer"]["transcription_status"] == "TRANSCRICAO_CONFIRMADA"

    answer = _current(db_session, answer_id)
    assert answer.text == "Texto final."
    assert answer.transcription_version == 1
    assert len(_audit(db_session, answer_id, CONFIRM_ACTION)) == 1


# ---------------- ACD-07: rascunho após confirmação sempre bloqueado ----------------
@pytest.mark.parametrize("expected_version", [0, 1, 2])
def test_draft_after_confirmation_is_always_blocked(client, db_session, professor_token, answer_id, expected_version):
    assert _confirm(client, professor_token, answer_id, "Texto final.", 0).status_code == 200

    response = _draft(client, professor_token, answer_id, "Rascunho tardio.", expected_version)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "TRANSCRIPTION_ALREADY_CONFIRMED"

    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft is None
    assert answer.text == "Texto final."
    assert answer.transcription_version == 1
    assert _audit(db_session, answer_id, DRAFT_ACTION) == []


# ---------------- ACD-08: confirmação não dispara correção ----------------
def test_confirm_does_not_create_correction_job(client, db_session, professor_token, answer_id, monkeypatch):
    calls = []
    monkeypatch.setattr(main_module, "run_correction_job", lambda *args, **kwargs: calls.append(args))

    assert _draft(client, professor_token, answer_id, "Rascunho.", 0).status_code == 200
    assert _confirm(client, professor_token, answer_id, "Texto final.", 1).status_code == 200

    db_session.expire_all()
    assert db_session.query(CorrectionJob).count() == 0
    assert calls == []


def test_manual_transcription_code_never_references_correction():
    """Inspeção: nenhum caminho novo chama request_correction ou cria CorrectionJob."""
    forbidden = {"request_correction", "CorrectionJob", "run_correction_job", "background_tasks", "BackgroundTasks"}
    functions = [
        main_module._save_manual_transcription,
        main_module._transcription_outcome,
        main_module._transcription_outcome_response,
        main_module._answer_with_images,
        main_module.save_manual_transcription_draft,
        main_module.confirm_manual_transcription,
    ]
    for function in functions:
        tree = ast.parse(inspect.getsource(function).lstrip())
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names |= {arg.arg for node in ast.walk(tree) if isinstance(node, ast.arguments) for arg in node.args}
        assert not names & forbidden, (function.__name__, names & forbidden)


# ---------------- ACD-09: guard de correção libera após confirmação ----------------
def test_correction_blocked_before_and_allowed_after_confirmation(client, db_session, professor_token, answer_id):
    blocked = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert blocked.status_code == 422
    assert blocked.json()["code"] == "ANSWER_NOT_TRANSCRIBED"

    # Rascunho sozinho não libera a correção.
    assert _draft(client, professor_token, answer_id, "Só rascunho.", 0).status_code == 200
    still_blocked = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert still_blocked.status_code == 422
    assert still_blocked.json()["code"] == "ANSWER_NOT_TRANSCRIBED"
    db_session.expire_all()
    assert db_session.query(CorrectionJob).count() == 0

    assert _confirm(client, professor_token, answer_id, "Texto confirmado.", 1).status_code == 200
    allowed = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert allowed.status_code == 202, allowed.text
    db_session.expire_all()
    assert db_session.query(CorrectionJob).filter_by(answer_id=answer_id).count() == 1


# ------- Delta AV-S08B: correção a partir da MESMA resposta por imagem -------
class _CapturingAIEngine:
    """Substitui httpx.AsyncClient no worker de correção e captura o payload."""

    payloads: list[dict] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kwargs):
        type(self).payloads.append(json)
        raise RuntimeError("AI Engine fictício: só captura o payload.")


@pytest.fixture()
def ai_engine(monkeypatch):
    import app.services.correction as correction_module

    _CapturingAIEngine.payloads = []
    monkeypatch.setattr(correction_module.httpx, "AsyncClient", _CapturingAIEngine)
    return _CapturingAIEngine


def test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text(
    client, db_session, professor_token, answer_id, ai_engine
):
    confirmed_text = "Texto confirmado\ncom quebra de linha e acentuação: ação."
    assert _draft(client, professor_token, answer_id, "Rascunho diferente.", 0).status_code == 200
    assert _confirm(client, professor_token, answer_id, confirmed_text, 1).status_code == 200

    requested = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert requested.status_code == 202, requested.text
    job_id = requested.json()["id"]

    db_session.expire_all()
    job = db_session.get(CorrectionJob, job_id)
    assert job.answer_id == answer_id
    assert job.attempt == 1
    # Nenhuma resposta nova foi criada para contornar o fluxo.
    assert db_session.query(Answer).count() == 1
    answer = db_session.get(Answer, answer_id)
    assert answer.source == AnswerSource.IMAGE
    assert answer.text == confirmed_text
    # O worker enviou ao AI Engine exatamente o texto confirmado (não o rascunho).
    assert [p["answer_text"] for p in ai_engine.payloads] == [confirmed_text]


def test_confirmed_image_answer_new_request_increments_attempt_on_same_answer(
    client, db_session, professor_token, answer_id, ai_engine
):
    assert _confirm(client, professor_token, answer_id, "Texto confirmado.", 0).status_code == 200
    first = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    second = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert first.status_code == second.status_code == 202

    db_session.expire_all()
    jobs = db_session.query(CorrectionJob).filter_by(answer_id=answer_id).order_by(CorrectionJob.attempt).all()
    assert [job.attempt for job in jobs] == [1, 2]
    assert {job.id for job in jobs} == {first.json()["id"], second.json()["id"]}
    assert [p["answer_text"] for p in ai_engine.payloads] == ["Texto confirmado.", "Texto confirmado."]


def test_unconfirmed_image_answer_correction_stays_blocked(client, db_session, professor_token, answer_id, ai_engine):
    assert _draft(client, professor_token, answer_id, "Só rascunho.", 0).status_code == 200
    blocked = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert blocked.status_code == 422
    assert blocked.json()["code"] == "ANSWER_NOT_TRANSCRIBED"
    db_session.expire_all()
    assert db_session.query(CorrectionJob).count() == 0
    assert ai_engine.payloads == []


# ---------------- ACD-10: histórico preservado em AuditEvent ----------------
def test_audit_history_preserves_every_draft_and_the_confirmation(client, db_session, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "Versão A.", 0).status_code == 200
    assert _draft(client, professor_token, answer_id, "Versão B.", 1).status_code == 200
    # Rejeitada: não pode gerar evento.
    assert _draft(client, professor_token, answer_id, "Versão perdida.", 0).status_code == 409
    assert _confirm(client, professor_token, answer_id, "Versão final.", 2).status_code == 200

    owner_id = _owner(db_session).id
    drafts = _audit(db_session, answer_id, DRAFT_ACTION)
    assert [json.loads(event.before_json) for event in drafts] == [
        {"manual_transcription_draft": None, "transcription_version": 0},
        {"manual_transcription_draft": "Versão A.", "transcription_version": 1},
    ]
    assert [json.loads(event.after_json) for event in drafts] == [
        {"manual_transcription_draft": "Versão A.", "transcription_version": 1},
        {"manual_transcription_draft": "Versão B.", "transcription_version": 2},
    ]
    assert all(event.actor_id == owner_id for event in drafts)

    [confirmation] = _audit(db_session, answer_id, CONFIRM_ACTION)
    assert confirmation.actor_id == owner_id
    assert json.loads(confirmation.before_json) == {
        "manual_transcription_draft": "Versão B.",
        "transcription_version": 2,
        "text": None,
        "transcription_status": "AGUARDANDO_TRANSCRICAO",
    }
    after = json.loads(confirmation.after_json)
    assert after["text"] == "Versão final."
    assert after["transcription_status"] == "TRANSCRICAO_CONFIRMADA"
    assert after["transcription_confirmed_by_id"] == owner_id
    assert after["manual_transcription_draft"] is None
    assert after["transcription_version"] == 3


# ---------------- ACD-11: correção/revisão existentes nunca são tocadas ----------------
def test_existing_correction_and_review_are_untouched(client, db_session, professor_token, answer_id):
    assert _confirm(client, professor_token, answer_id, "Texto usado na correção.", 0).status_code == 200
    requested = client.post(f"/v1/answers/{answer_id}/corrections", headers=_headers(professor_token))
    assert requested.status_code == 202, requested.text
    job_id = requested.json()["id"]
    db_session.expire_all()
    job = db_session.get(CorrectionJob, job_id)
    job_snapshot = (job.status, job.attempt, job.rubric_id, job.updated_at)
    db_session.add(
        HumanReview(
            job_id=job_id,
            reviewer_id=_owner(db_session).id,
            decision=ReviewDecision.APPROVE,
            final_total=Decimal("7.00"),
            final_scores_json="[]",
        )
    )
    db_session.commit()

    assert _draft(client, professor_token, answer_id, "Tentativa.", 1).status_code == 409
    assert _confirm(client, professor_token, answer_id, "Texto diferente.", 1).status_code == 409
    assert _confirm(client, professor_token, answer_id, "Texto usado na correção.", 1).status_code == 200

    db_session.expire_all()
    assert db_session.query(CorrectionJob).filter_by(answer_id=answer_id).count() == 1
    job = db_session.get(CorrectionJob, job_id)
    assert (job.status, job.attempt, job.rubric_id, job.updated_at) == job_snapshot
    [review] = db_session.query(HumanReview).filter_by(job_id=job_id).all()
    assert review.final_total == Decimal("7.00")
    assert db_session.get(Answer, answer_id).text == "Texto usado na correção."


# ---------------- ACD-12: fluxo textual preservado ----------------
def test_text_answer_flow_unchanged(client, db_session, professor_token, question_id):
    created = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno T", "text": "Resposta digitada."},
        headers=_headers(professor_token),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["transcription_status"] == "TRANSCRICAO_CONFIRMADA"
    assert body["transcription_version"] == 0
    assert body["manual_transcription_draft"] is None
    correction = client.post(f"/v1/answers/{body['id']}/corrections", headers=_headers(professor_token))
    assert correction.status_code == 202, correction.text


# ---------------- ACD-14: resposta inexistente ----------------
def test_missing_answer_returns_404(client, professor_token):
    assert _draft(client, professor_token, "nao-existe", "x", 0).status_code == 404
    assert _confirm(client, professor_token, "nao-existe", "x", 0).status_code == 404


def test_negative_expected_version_is_rejected(client, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "x", -1).status_code == 422


# ---------------- ACD-15 (sequencial): versão desatualizada no rascunho ----------------
def test_stale_draft_is_rejected_with_current_state(client, db_session, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "Aba A.", 0).status_code == 200

    stale = _draft(client, professor_token, answer_id, "Aba B.", 0)
    assert stale.status_code == 409, stale.text
    body = stale.json()
    assert body["code"] == "TRANSCRIPTION_VERSION_CONFLICT"
    assert body["details"]["current_answer"]["manual_transcription_draft"] == "Aba A."
    assert body["details"]["current_answer"]["transcription_version"] == 1
    assert _current(db_session, answer_id).manual_transcription_draft == "Aba A."


def test_stale_confirm_is_rejected(client, db_session, professor_token, answer_id):
    assert _draft(client, professor_token, answer_id, "Aba A.", 0).status_code == 200

    stale = _confirm(client, professor_token, answer_id, "Aba B confirma.", 0)
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "TRANSCRIPTION_VERSION_CONFLICT"
    answer = _current(db_session, answer_id)
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert answer.text is None


# ---------------- ACD-17: versão monotônica, sem saltos por rejeição ----------------
def test_version_never_regresses_nor_skips_on_rejected_calls(client, db_session, professor_token, answer_id):
    steps = [
        (_draft, "Rascunho 1.", 0, 200),
        (_draft, "Atrasado.", 0, 409),  # versão desatualizada
        (_confirm, "   ", 1, 422),  # texto vazio
        (_confirm, "Confirma.", 5, 409),  # versão futura
        (_draft, "Rascunho 2.", 1, 200),
        (_confirm, "Final.", 2, 200),
        (_draft, "Pós-confirmação.", 3, 409),
        (_confirm, "Outro final.", 3, 409),
        (_confirm, "Final.", 3, 200),  # idempotente: não incrementa
    ]
    versions = [_current(db_session, answer_id).transcription_version]
    for call, text, expected_version, status in steps:
        response = call(client, professor_token, answer_id, text, expected_version)
        assert response.status_code == status, (text, response.text)
        versions.append(_current(db_session, answer_id).transcription_version)

    assert versions == [0, 1, 1, 1, 1, 2, 3, 3, 3, 3]
    assert all(later >= earlier for earlier, later in zip(versions, versions[1:]))


# ======================= Concorrência real em PostgreSQL =======================
_PROTECTED_DATABASES = {"avalia_dev", "avalia_apresentacao_demo_20261002", "postgres"}
_PG_URL = os.environ.get("AVALIA_TEST_POSTGRES_URL")

requires_postgres = pytest.mark.skipif(
    not _PG_URL, reason="AVALIA_TEST_POSTGRES_URL não definido (concorrência real exige PostgreSQL isolado)"
)


@pytest.fixture()
def pg_engine():
    url = make_url(_PG_URL)
    assert url.get_backend_name() == "postgresql"
    # Só banco descartável de teste; nunca os bancos protegidos.
    assert url.database not in _PROTECTED_DATABASES and "test" in (url.database or ""), url.database
    engine = create_engine(url, future=True, pool_size=20, max_overflow=0)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def pg_client(pg_engine):
    PgSessionLocal = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = PgSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[db_module.get_db] = override_get_db
    with TestClient(main_module.app) as c:
        yield c, PgSessionLocal
    main_module.app.dependency_overrides.clear()


@pytest.fixture()
def pg_setup(pg_client):
    client, PgSessionLocal = pg_client
    session = PgSessionLocal()
    owner = User(email="pg.professor@example.com", password_hash=hash_password("Senha123!"), role=Role.PROFESSOR)
    session.add(owner)
    session.flush()
    assessment = Assessment(title="Concorrência", owner_id=owner.id, status=AssessmentStatus.PUBLICADA)
    session.add(assessment)
    session.flush()
    question = _question(session, assessment.id)
    answer = _image_answer(session, question.id)
    answer_id = answer.id
    session.close()
    login = client.post("/v1/auth/login", json={"email": "pg.professor@example.com", "password": "Senha123!"})
    assert login.status_code == 200, login.text
    return client, PgSessionLocal, login.json()["access_token"], answer_id


def _synchronize_answer_updates(engine, parties: int) -> Barrier:
    """Segura cada UPDATE de answers até todas as transações chegarem nele.

    Todas já leram a mesma versão e passaram na checagem prévia; a disputa é
    decidida só pelo UPDATE condicional na transação do PostgreSQL.
    """
    barrier = Barrier(parties)

    @event.listens_for(engine, "before_cursor_execute")
    def _wait(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("UPDATE ANSWERS"):
            barrier.wait(timeout=15)

    return barrier


def _pg_answer_and_audit(PgSessionLocal, answer_id):
    session = PgSessionLocal()
    try:
        answer = session.get(Answer, answer_id)
        events = (
            session.query(AuditEvent)
            .filter_by(resource_type="Answer", resource_id=answer_id)
            .order_by(AuditEvent.created_at)
            .all()
        )
        return (
            {
                "text": answer.text,
                "draft": answer.manual_transcription_draft,
                "status": answer.transcription_status,
                "version": answer.transcription_version,
            },
            [(event.action, json.loads(event.after_json)) for event in events],
        )
    finally:
        session.close()


# ---------------- ACD-15: rascunhos concorrentes ----------------
@requires_postgres
@pytest.mark.parametrize("parties", [2, 8])
def test_pg_concurrent_drafts_only_one_commits(pg_engine, pg_setup, parties):
    client, PgSessionLocal, token, answer_id = pg_setup
    _synchronize_answer_updates(pg_engine, parties)
    texts = [f"Aba {index}." for index in range(parties)]

    with ThreadPoolExecutor(max_workers=parties) as pool:
        responses = list(pool.map(lambda text: _draft(client, token, answer_id, text, 0), texts))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [200] + [409] * (parties - 1), [r.text for r in responses]
    [winner] = [response for response in responses if response.status_code == 200]
    winning_text = winner.json()["manual_transcription_draft"]
    for loser in (response for response in responses if response.status_code == 409):
        body = loser.json()
        assert body["code"] == "TRANSCRIPTION_VERSION_CONFLICT"
        assert body["details"]["current_answer"]["manual_transcription_draft"] == winning_text
        assert body["details"]["current_answer"]["transcription_version"] == 1

    state, events = _pg_answer_and_audit(PgSessionLocal, answer_id)
    assert state["draft"] == winning_text
    assert state["version"] == 1
    assert [action for action, _ in events] == [DRAFT_ACTION]
    assert events[0][1]["manual_transcription_draft"] == winning_text


# ---------------- ACD-16: confirmações concorrentes ----------------
@requires_postgres
@pytest.mark.parametrize("parties", [2, 8])
def test_pg_concurrent_confirms_exactly_one_wins(pg_engine, pg_setup, parties):
    client, PgSessionLocal, token, answer_id = pg_setup
    _synchronize_answer_updates(pg_engine, parties)
    texts = [f"Texto final {index}." for index in range(parties)]

    with ThreadPoolExecutor(max_workers=parties) as pool:
        responses = list(pool.map(lambda text: _confirm(client, token, answer_id, text, 0), texts))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [200] + [409] * (parties - 1), [r.text for r in responses]
    [winner] = [response for response in responses if response.status_code == 200]
    final_text = winner.json()["text"]
    for loser in (response for response in responses if response.status_code == 409):
        body = loser.json()
        assert body["code"] in {"TRANSCRIPTION_ALREADY_CONFIRMED", "TRANSCRIPTION_VERSION_CONFLICT"}
        assert body["details"]["current_answer"]["text"] == final_text

    state, events = _pg_answer_and_audit(PgSessionLocal, answer_id)
    assert state["text"] == final_text
    assert state["status"] == TranscriptionStatus.TRANSCRICAO_CONFIRMADA
    assert state["version"] == 1
    confirmations = [after for action, after in events if action == CONFIRM_ACTION]
    assert len(confirmations) == 1
    assert confirmations[0]["text"] == final_text


@requires_postgres
def test_pg_concurrent_confirm_and_draft_never_reopen(pg_engine, pg_setup):
    """Corrida mista (recomendação do parecer v2): rascunho tardio não reverte a confirmação."""
    client, PgSessionLocal, token, answer_id = pg_setup
    _synchronize_answer_updates(pg_engine, 2)

    with ThreadPoolExecutor(max_workers=2) as pool:
        confirm_future = pool.submit(_confirm, client, token, answer_id, "Confirmado.", 0)
        draft_future = pool.submit(_draft, client, token, answer_id, "Rascunho concorrente.", 0)
        confirm, draft = confirm_future.result(), draft_future.result()

    assert sorted([confirm.status_code, draft.status_code]) == [200, 409], (confirm.text, draft.text)
    state, events = _pg_answer_and_audit(PgSessionLocal, answer_id)
    assert state["version"] == 1
    if confirm.status_code == 200:
        assert state["status"] == TranscriptionStatus.TRANSCRICAO_CONFIRMADA
        assert state["text"] == "Confirmado."
        assert state["draft"] is None
        assert [action for action, _ in events] == [CONFIRM_ACTION]
    else:
        assert state["status"] == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
        assert state["draft"] == "Rascunho concorrente."
        assert [action for action, _ in events] == [DRAFT_ACTION]
