"""BL-AV-4B-05 (1ª fatia) — exclusão lógica reversível de imagens de resposta.

DELETE /v1/answer-images/{id} e POST /v1/answer-images/{id}/restore só operam
com a resposta aguardando transcrição (estágio A); depois da confirmação (B, C,
D) respondem 409, inclusive para admin (D2, R3). Nada é removido fisicamente
(D1/D3). Ambos, e a confirmação da transcrição, travam a linha de `answers`
(SELECT ... FOR UPDATE) antes de decidir (R2).

Os testes de concorrência real (ACD-07/10/14) rodam contra PostgreSQL isolado
indicado por AVALIA_TEST_POSTGRES_URL, com o schema criado por
`alembic upgrade head`; sem a variável, são pulados.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from threading import Barrier, Lock
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app import db as db_module
from app.config import get_settings
from app.db import Base
from app.models import (
    AIExecution,
    Answer,
    AnswerImage,
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
    JobStatus,
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

DELETE_ACTION = "DELETE_LOGICAL"
RESTORE_ACTION = "RESTORE_LOGICAL"
CONFIRM_ACTION = "manual_transcription_confirmed"
# Nome original propositalmente "sensível" (aluno/turma) para provar que não vaza.
SENSITIVE_FILENAME = "Maria_Ficticia_Turma_3B.png"
_AUDIT_KEYS = {
    "id",
    "answer_id",
    "uploaded_by_id",
    "content_type",
    "size_bytes",
    "created_at",
    "deleted_at",
    "deleted_by_id",
}


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _png(color=(10, 20, 30), size=(16, 16)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def _create_image_answer(client, token, question_id, *, filename=SENSITIVE_FILENAME, content=None) -> dict:
    response = client.post(
        "/v1/answers/image",
        data={"question_id": question_id, "student_name_fake": "Aluno fictício"},
        files={"file": (filename, content or _png(), "image/png")},
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _add_image(client, token, answer_id, *, content=None) -> str:
    response = client.post(
        f"/v1/answers/{answer_id}/images",
        files={"file": ("segunda.png", content or _png((90, 80, 70)), "image/png")},
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _delete(client, token, image_id):
    return client.delete(f"/v1/answer-images/{image_id}", headers=_headers(token))


def _restore(client, token, image_id):
    return client.post(f"/v1/answer-images/{image_id}/restore", headers=_headers(token))


def _deleted_list(client, token, answer_id):
    return client.get(f"/v1/answers/{answer_id}/images/deleted", headers=_headers(token))


def _download(client, token, image_id):
    return client.get(f"/v1/answer-images/{image_id}/download", headers=_headers(token))


def _confirm(client, token, answer_id, text_value="Texto confirmado.", expected_version=0):
    return client.post(
        f"/v1/answers/{answer_id}/manual-transcription/confirm",
        json={"text": text_value, "expected_version": expected_version},
        headers=_headers(token),
    )


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


def _image(db_session, image_id) -> AnswerImage:
    db_session.expire_all()
    return db_session.get(AnswerImage, image_id)


def _answer(db_session, answer_id) -> Answer:
    db_session.expire_all()
    return db_session.get(Answer, answer_id)


def _image_audit(db_session, image_id, action=None) -> list[AuditEvent]:
    db_session.expire_all()
    query = db_session.query(AuditEvent).filter_by(resource_type="AnswerImage", resource_id=image_id)
    if action is not None:
        query = query.filter_by(action=action)
    return query.order_by(AuditEvent.created_at, AuditEvent.id).all()


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


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "answer_images"
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(path))
    return path


@pytest.fixture()
def question_id(db_session, professor_token) -> str:
    assessment = Assessment(
        title="Avaliação com exclusão de imagem", owner_id=_owner(db_session).id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id)
    db_session.commit()
    return question.id


@pytest.fixture()
def image_answer(client, professor_token, question_id, storage_dir) -> dict:
    return _create_image_answer(client, professor_token, question_id)


def _advance_to_stage(db_session, client, token, answer_id, stage: str) -> None:
    """B: transcrição confirmada; C: + CorrectionJob/AIExecution; D: + HumanReview."""
    assert _confirm(client, token, answer_id).status_code == 200
    if stage == "B":
        return
    db_session.expire_all()
    answer = db_session.get(Answer, answer_id)
    rubric = db_session.query(Rubric).filter_by(question_id=answer.question_id).one()
    job = CorrectionJob(answer_id=answer_id, rubric_id=rubric.id, status=JobStatus.SUGERIDA)
    db_session.add(job)
    db_session.flush()
    db_session.add(AIExecution(job_id=job.id, engine_mode="simulated"))
    if stage == "D":
        db_session.add(
            HumanReview(
                job_id=job.id,
                reviewer_id=_owner(db_session).id,
                decision=ReviewDecision.APPROVE,
                final_total=Decimal("7.00"),
                final_scores_json="[]",
            )
        )
    db_session.commit()


def _dependents(db_session, answer_id) -> tuple[int, int, int]:
    db_session.expire_all()
    jobs = db_session.query(CorrectionJob).filter_by(answer_id=answer_id).all()
    job_ids = [job.id for job in jobs]
    executions = db_session.query(AIExecution).filter(AIExecution.job_id.in_(job_ids)).count() if job_ids else 0
    reviews = db_session.query(HumanReview).filter(HumanReview.job_id.in_(job_ids)).count() if job_ids else 0
    return len(jobs), executions, reviews


# ---------------- ACD-01: exclusão lógica pelo dono no estágio A ----------------
def test_owner_deletes_image_logically_in_stage_a(client, db_session, professor_token, image_answer):
    image_id = image_answer["images"][0]["id"]

    response = _delete(client, professor_token, image_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"id", "deleted_at", "deleted_by_id"}
    assert body["id"] == image_id
    assert body["deleted_by_id"] == _owner(db_session).id
    assert body["deleted_at"] is not None

    image = _image(db_session, image_id)
    assert image.deleted_at is not None
    assert image.deleted_by_id == _owner(db_session).id


def test_admin_deletes_image_logically_in_stage_a(client, db_session, admin_token, image_answer):
    image_id = image_answer["images"][0]["id"]
    response = _delete(client, admin_token, image_id)
    assert response.status_code == 200, response.text
    admin = db_session.query(User).filter_by(email="admin@example.com").one()
    assert _image(db_session, image_id).deleted_by_id == admin.id


def test_delete_and_restore_missing_image_return_404(client, professor_token, storage_dir):
    assert _delete(client, professor_token, "nao-existe").status_code == 404
    assert _restore(client, professor_token, "nao-existe").status_code == 404


def test_delete_restore_and_deleted_list_require_token(client, image_answer):
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, None, image_id).status_code == 401
    assert _restore(client, None, image_id).status_code == 401
    assert _deleted_list(client, None, image_answer["id"]).status_code == 401


# ---------------- ACD-02: bloqueio em B/C/D, inclusive para admin ----------------
@pytest.mark.parametrize("stage", ["B", "C", "D"])
@pytest.mark.parametrize("actor", ["owner", "admin"])
def test_delete_is_blocked_after_confirmation_even_for_admin(
    client, db_session, professor_token, admin_token, image_answer, stage, actor
):
    answer_id = image_answer["id"]
    image_id = image_answer["images"][0]["id"]
    _advance_to_stage(db_session, client, professor_token, answer_id, stage)
    dependents = _dependents(db_session, answer_id)

    token = professor_token if actor == "owner" else admin_token
    response = _delete(client, token, image_id)
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["code"] == "ANSWER_IMAGES_LOCKED"
    assert body["details"]["transcription_status"] == "TRANSCRICAO_CONFIRMADA"

    image = _image(db_session, image_id)
    assert image.deleted_at is None and image.deleted_by_id is None
    assert _image_audit(db_session, image_id) == []
    assert _dependents(db_session, answer_id) == dependents
    assert _download(client, professor_token, image_id).status_code == 200


# ---------------- ACD-03: nada é removido fisicamente nem em cascata ----------------
def test_logical_deletion_keeps_file_record_and_answer(client, db_session, professor_token, image_answer, storage_dir):
    answer_id = image_answer["id"]
    image_id = image_answer["images"][0]["id"]
    image = _image(db_session, image_id)
    path = storage_dir / image.storage_filename
    original_bytes = path.read_bytes()

    assert _delete(client, professor_token, image_id).status_code == 200

    assert path.is_file()
    assert path.read_bytes() == original_bytes
    assert hashlib.sha256(path.read_bytes()).hexdigest() == image.sha256_hash
    image = _image(db_session, image_id)
    assert image is not None
    assert image.storage_filename == path.name
    assert image.original_filename == SENSITIVE_FILENAME
    answer = _answer(db_session, answer_id)
    assert answer is not None
    assert answer.source == AnswerSource.IMAGE
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert _dependents(db_session, answer_id) == (0, 0, 0)


# ---------------- ACD-04: restauração no estágio A ----------------
def test_restore_in_stage_a_reactivates_image_and_download(client, db_session, professor_token, image_answer):
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, professor_token, image_id).status_code == 200
    assert _download(client, professor_token, image_id).status_code == 410

    response = _restore(client, professor_token, image_id)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == image_id
    assert set(response.json()) == set(image_answer["images"][0])  # contrato de imagem ativa intacto

    image = _image(db_session, image_id)
    assert image.deleted_at is None and image.deleted_by_id is None
    assert _download(client, professor_token, image_id).status_code == 200
    assert len(_image_audit(db_session, image_id, RESTORE_ACTION)) == 1


# ---------------- ACD-05: auditoria com metadados mínimos ----------------
def test_audit_events_carry_only_minimal_metadata(client, db_session, professor_token, image_answer):
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, professor_token, image_id).status_code == 200
    assert _restore(client, professor_token, image_id).status_code == 200

    image = _image(db_session, image_id)
    owner_id = _owner(db_session).id
    [deletion] = _image_audit(db_session, image_id, DELETE_ACTION)
    [restoration] = _image_audit(db_session, image_id, RESTORE_ACTION)
    for event_ in (deletion, restoration):
        assert event_.actor_id == owner_id
        assert event_.resource_type == "AnswerImage"
        assert event_.resource_id == image_id
        serialized = (event_.before_json or "") + (event_.after_json or "")
        for secret in (image.original_filename, image.storage_filename, image.sha256_hash, "Maria", "Turma"):
            assert secret not in serialized
        for forbidden_key in ("original_filename", "storage_filename", "sha256_hash"):
            assert forbidden_key not in serialized
        assert set(json.loads(event_.before_json)) <= _AUDIT_KEYS
        assert set(json.loads(event_.after_json)) <= _AUDIT_KEYS

    before = json.loads(deletion.before_json)
    assert before["id"] == image_id
    assert before["answer_id"] == image_answer["id"]
    assert before["size_bytes"] == image.size_bytes
    assert before["content_type"] == "image/png"
    assert before["deleted_at"] is None
    after = json.loads(deletion.after_json)
    assert after["deleted_by_id"] == owner_id and after["deleted_at"] is not None
    assert json.loads(restoration.before_json)["deleted_by_id"] == owner_id
    assert json.loads(restoration.after_json) == {"deleted_at": None, "deleted_by_id": None}


# ---------------- ACD-06: idempotência ----------------
def test_repeated_delete_is_idempotent(client, db_session, professor_token, admin_token, image_answer):
    image_id = image_answer["images"][0]["id"]
    first = _delete(client, professor_token, image_id)
    assert first.status_code == 200
    original = _image(db_session, image_id)
    deleted_at, deleted_by = original.deleted_at, original.deleted_by_id

    # Nem o mesmo usuário nem outro (admin) sobrescrevem a marcação original.
    for token in (professor_token, admin_token):
        again = _delete(client, token, image_id)
        assert again.status_code == 200, again.text
        assert again.json() == first.json()

    image = _image(db_session, image_id)
    assert (image.deleted_at, image.deleted_by_id) == (deleted_at, deleted_by)
    assert len(_image_audit(db_session, image_id, DELETE_ACTION)) == 1


def test_restore_of_active_image_is_idempotent(client, db_session, professor_token, image_answer):
    image_id = image_answer["images"][0]["id"]
    never_deleted = _restore(client, professor_token, image_id)
    assert never_deleted.status_code == 200, never_deleted.text
    assert _image_audit(db_session, image_id) == []

    assert _delete(client, professor_token, image_id).status_code == 200
    assert _restore(client, professor_token, image_id).status_code == 200
    again = _restore(client, professor_token, image_id)
    assert again.status_code == 200
    assert again.json()["id"] == image_id
    assert len(_image_audit(db_session, image_id, RESTORE_ACTION)) == 1
    assert len(_image_audit(db_session, image_id, DELETE_ACTION)) == 1


# ---------------- ACD-07 (sequencial; concorrente no PostgreSQL abaixo) ----------------
def test_deletion_uses_conditional_update_on_deleted_at():
    """Inspeção: o UPDATE da exclusão é condicionado a deleted_at IS NULL."""
    from app.routers import images as images_module

    source = Path(images_module.__file__).read_text(encoding="utf-8")
    assert "AnswerImage.deleted_at.is_(None)" in source
    assert "_lock_answer_row(db, image.answer_id)" in source


# ---------------- ACD-08: download de imagem excluída ----------------
def test_download_of_deleted_image_is_refused(
    client, db_session, professor_token, admin_token, image_answer, storage_dir
):
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, professor_token, image_id).status_code == 200
    for token in (professor_token, admin_token):
        response = _download(client, token, image_id)
        assert response.status_code == 410, response.text
        assert response.content != (storage_dir / _image(db_session, image_id).storage_filename).read_bytes()


# ---------------- ACD-09: confirmar exige imagem ativa ----------------
def test_confirm_is_blocked_without_active_image(client, db_session, professor_token, image_answer):
    answer_id = image_answer["id"]
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, professor_token, image_id).status_code == 200

    blocked = _confirm(client, professor_token, answer_id)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["code"] == "ANSWER_HAS_NO_ACTIVE_IMAGE"
    answer = _answer(db_session, answer_id)
    assert answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
    assert answer.text is None
    assert answer.transcription_version == 0
    db_session.expire_all()
    assert db_session.query(AuditEvent).filter_by(resource_id=answer_id, action=CONFIRM_ACTION).count() == 0

    # Rascunho continua permitido; restaurar libera a confirmação.
    draft = client.patch(
        f"/v1/answers/{answer_id}/manual-transcription/draft",
        json={"text": "Rascunho.", "expected_version": 0},
        headers=_headers(professor_token),
    )
    assert draft.status_code == 200, draft.text
    assert _restore(client, professor_token, image_id).status_code == 200
    confirmed = _confirm(client, professor_token, answer_id, expected_version=1)
    assert confirmed.status_code == 200, confirmed.text
    assert [image["id"] for image in confirmed.json()["images"]] == [image_id]


def test_confirm_with_one_of_two_images_deleted_is_allowed(client, db_session, professor_token, image_answer):
    answer_id = image_answer["id"]
    first_id = image_answer["images"][0]["id"]
    second_id = _add_image(client, professor_token, answer_id)
    assert _delete(client, professor_token, first_id).status_code == 200

    confirmed = _confirm(client, professor_token, answer_id)
    assert confirmed.status_code == 200, confirmed.text
    assert [image["id"] for image in confirmed.json()["images"]] == [second_id]


# ---------------- ACD-11: autorização por propriedade/vínculo ----------------
def test_other_professor_cannot_delete_restore_or_list_deleted(
    client, db_session, professor_token, second_professor_token, image_answer
):
    answer_id = image_answer["id"]
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, second_professor_token, image_id).status_code == 403
    assert _image(db_session, image_id).deleted_at is None

    assert _delete(client, professor_token, image_id).status_code == 200
    assert _restore(client, second_professor_token, image_id).status_code == 403
    assert _deleted_list(client, second_professor_token, answer_id).status_code == 403
    assert _image(db_session, image_id).deleted_at is not None
    assert len(_image_audit(db_session, image_id)) == 1


def _class_answer_with_image(db_session, *, active_link: bool) -> tuple[str, str]:
    owner = _owner(db_session)
    organization = Organization(name="Org exclusão")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name="Curso", code="CUR-EXC")
    discipline = Discipline(organization_id=organization.id, name="Disciplina", code="DISC-EXC")
    db_session.add_all([course, discipline])
    db_session.flush()
    course_discipline = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(course_discipline)
    db_session.flush()
    class_group = ClassGroup(course_discipline_id=course_discipline.id, period="2026-2", code="T-EXC")
    db_session.add(class_group)
    db_session.flush()
    if active_link:
        db_session.add(
            ProfessorClassLink(
                professor_id=owner.id, class_group_id=class_group.id, role=ProfessorRole.RESPONSIBLE, active=True
            )
        )
    assessment = Assessment(
        title="Avaliação de turma", owner_id=owner.id, class_group_id=class_group.id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id)
    answer = Answer(
        question_id=question.id,
        student_name_fake="Aluno fictício",
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.flush()
    image = AnswerImage(
        answer_id=answer.id,
        storage_filename="ficticio.png",
        original_filename="ficticio.png",
        content_type="image/png",
        size_bytes=1,
        sha256_hash="0" * 64,
        uploaded_by_id=owner.id,
    )
    db_session.add(image)
    db_session.commit()
    return answer.id, image.id


def test_owner_without_active_class_link_is_forbidden(client, db_session, professor_token, storage_dir):
    _, image_id = _class_answer_with_image(db_session, active_link=False)
    assert _delete(client, professor_token, image_id).status_code == 403
    assert _restore(client, professor_token, image_id).status_code == 403
    assert _image(db_session, image_id).deleted_at is None


def test_owner_with_active_class_link_can_delete(client, db_session, professor_token, storage_dir):
    _, image_id = _class_answer_with_image(db_session, active_link=True)
    assert _delete(client, professor_token, image_id).status_code == 200


# ---------------- ACD-12: restauração sem arquivo não é prometida ----------------
def test_restore_with_missing_file_fails_and_preserves_state(
    client, db_session, professor_token, image_answer, storage_dir
):
    image_id = image_answer["images"][0]["id"]
    assert _delete(client, professor_token, image_id).status_code == 200
    deleted = _image(db_session, image_id)
    marking = (deleted.deleted_at, deleted.deleted_by_id)
    # Divergência induzida no storage do teste (simula perda do arquivo).
    (storage_dir / deleted.storage_filename).unlink()

    response = _restore(client, professor_token, image_id)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "ANSWER_IMAGE_FILE_MISSING"

    image = _image(db_session, image_id)
    assert (image.deleted_at, image.deleted_by_id) == marking
    assert _image_audit(db_session, image_id, RESTORE_ACTION) == []
    assert [item["id"] for item in _deleted_list(client, professor_token, image_answer["id"]).json()] == [image_id]


# ---------------- ACD-14 (sequencial; repetido no PostgreSQL abaixo) ----------------
def test_restore_after_confirmation_with_other_image_is_blocked_even_for_admin(
    client, db_session, professor_token, admin_token, image_answer
):
    answer_id = image_answer["id"]
    deleted_id = image_answer["images"][0]["id"]
    active_id = _add_image(client, professor_token, answer_id)
    assert _delete(client, professor_token, deleted_id).status_code == 200
    assert _confirm(client, professor_token, answer_id).status_code == 200

    for token in (professor_token, admin_token):
        response = _restore(client, token, deleted_id)
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "ANSWER_IMAGES_LOCKED"
        assert _delete(client, token, active_id).status_code == 409

    assert _image(db_session, deleted_id).deleted_at is not None
    assert _image(db_session, active_id).deleted_at is None
    assert _image_audit(db_session, deleted_id, RESTORE_ACTION) == []
    assert _image_audit(db_session, active_id) == []


# ---------------- ACD-15: projeções de leitura ----------------
def test_default_reads_hide_deleted_images_and_deleted_projection_is_minimal(
    client, db_session, professor_token, image_answer
):
    answer_id = image_answer["id"]
    deleted_id = image_answer["images"][0]["id"]
    active_contract = set(image_answer["images"][0])
    active_id = _add_image(client, professor_token, answer_id)
    assert _delete(client, professor_token, deleted_id).status_code == 200

    listed = client.get(f"/v1/answers/{answer_id}/images", headers=_headers(professor_token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [active_id]
    assert set(listed.json()[0]) == active_contract  # contrato existente intacto
    assert "sha256_hash" in active_contract and "original_filename" in active_contract

    assessment_id = client.get("/v1/assessments", headers=_headers(professor_token)).json()[0]["id"]
    [item] = client.get(
        f"/v1/assessments/{assessment_id}/image-answers", headers=_headers(professor_token)
    ).json()
    assert [image["id"] for image in item["images"]] == [active_id]

    draft = client.patch(
        f"/v1/answers/{answer_id}/manual-transcription/draft",
        json={"text": "Rascunho.", "expected_version": 0},
        headers=_headers(professor_token),
    )
    assert [image["id"] for image in draft.json()["images"]] == [active_id]

    deleted = _deleted_list(client, professor_token, answer_id)
    assert deleted.status_code == 200, deleted.text
    [entry] = deleted.json()
    assert set(entry) == {"id", "deleted_at", "deleted_by_id"}
    assert entry["id"] == deleted_id
    assert entry["deleted_by_id"] == _owner(db_session).id
    raw = deleted.text
    image = _image(db_session, deleted_id)
    for secret in (image.sha256_hash, image.original_filename, image.storage_filename):
        assert secret not in raw

    # Restaurada, sai da projeção de excluídas e volta à listagem padrão.
    assert _restore(client, professor_token, deleted_id).status_code == 200
    assert _deleted_list(client, professor_token, answer_id).json() == []
    listed = client.get(f"/v1/answers/{answer_id}/images", headers=_headers(professor_token)).json()
    assert {item["id"] for item in listed} == {active_id, deleted_id}


# ---------------- ACD-13: diagnóstico somente leitura ----------------
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "blav4b05_diagnostico_imagens.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("blav4b05_diagnostico_imagens", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot(db_path: Path, storage: Path) -> tuple[str, dict[str, str]]:
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in storage.iterdir() if p.is_file()}
    return hashlib.sha256(db_path.read_bytes()).hexdigest(), files


def test_divergence_script_reports_without_changing_data(test_engine, db_session, tmp_path, capsys):
    storage = tmp_path / "diag_storage"
    storage.mkdir()
    owner = User(email="diag@example.com", password_hash=hash_password("Senha123!"), role=Role.PROFESSOR)
    db_session.add(owner)
    db_session.flush()
    assessment = Assessment(title="Diagnóstico", owner_id=owner.id, status=AssessmentStatus.PUBLICADA)
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id)
    answer = Answer(
        question_id=question.id,
        student_name_fake="Aluno fictício",
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.flush()

    def image(name: str, *, with_file: bool, deleted: bool) -> str:
        record = AnswerImage(
            answer_id=answer.id,
            storage_filename=name,
            original_filename=SENSITIVE_FILENAME,
            content_type="image/png",
            size_bytes=3,
            sha256_hash="f" * 64,
            uploaded_by_id=owner.id,
            deleted_at=datetime.utcnow() if deleted else None,
            deleted_by_id=owner.id if deleted else None,
        )
        db_session.add(record)
        db_session.flush()
        if with_file:
            (storage / name).write_bytes(b"png")
        return record.id

    ok_id = image("ok.png", with_file=True, deleted=False)
    active_missing_id = image("sumiu.png", with_file=False, deleted=False)
    retained_id = image("excluida.png", with_file=True, deleted=True)
    deleted_missing_id = image("excluida-sumiu.png", with_file=False, deleted=True)
    escaping_id = image("../fora.png", with_file=False, deleted=False)
    db_session.commit()
    (storage / "orfao.png").write_bytes(b"png")

    db_path = Path(test_engine.url.database)
    before = _snapshot(db_path, storage)
    rows_before = [
        (row.id, row.deleted_at, row.deleted_by_id)
        for row in db_session.query(AnswerImage).order_by(AnswerImage.id).all()
    ]
    script = _load_script()

    report = script.diagnose(str(test_engine.url), storage)
    assert report["active_missing_file"] == sorted([active_missing_id, escaping_id])
    assert report["orphan_files"] == ["orfao.png"]
    assert report["retained_deleted_files"] == [retained_id]
    assert report["deleted_missing_file"] == [deleted_missing_id]
    assert report["divergences"] == 3
    assert ok_id not in json.dumps(report)
    assert SENSITIVE_FILENAME not in json.dumps(report)
    assert "f" * 64 not in json.dumps(report)

    assert script.main(["--database-url", str(test_engine.url), "--storage-dir", str(storage)]) == 1
    assert json.loads(capsys.readouterr().out) == report

    # Nenhuma alteração: banco (bytes do arquivo SQLite e linhas) e storage intactos.
    assert _snapshot(db_path, storage) == before
    db_session.expire_all()
    assert [
        (row.id, row.deleted_at, row.deleted_by_id)
        for row in db_session.query(AnswerImage).order_by(AnswerImage.id).all()
    ] == rows_before


def test_divergence_script_reports_clean_storage_with_exit_zero(test_engine, tmp_path, capsys):
    storage = tmp_path / "vazio"
    storage.mkdir()
    script = _load_script()
    assert script.main(["--database-url", str(test_engine.url), "--storage-dir", str(storage)]) == 0
    assert json.loads(capsys.readouterr().out)["divergences"] == 0


def test_divergence_script_has_no_write_operations():
    tree = ast.parse(_SCRIPT.read_text(encoding="utf-8"))
    forbidden_calls = {
        "unlink", "remove", "rmdir", "rmtree", "rename", "replace",
        "write_text", "write_bytes", "commit",
    }
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not attributes & forbidden_calls, attributes & forbidden_calls
    strings = " ".join(
        node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER)\b", strings)


# ======================= Concorrência real em PostgreSQL =======================
_PROTECTED_DATABASES = {"avalia_dev", "avalia_apresentacao_demo_20261002", "postgres"}
_PG_URL = os.environ.get("AVALIA_TEST_POSTGRES_URL")
_ALEMBIC_HEAD = "b8d3e5f7a2c4"

requires_postgres = pytest.mark.skipif(
    not _PG_URL, reason="AVALIA_TEST_POSTGRES_URL não definido (concorrência real exige PostgreSQL isolado)"
)


def _truncate_all(engine) -> None:
    names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} CASCADE"))


@pytest.fixture()
def pg_engine():
    url = make_url(_PG_URL)
    assert url.get_backend_name() == "postgresql"
    # Só banco descartável de teste; nunca os bancos protegidos.
    assert url.database not in _PROTECTED_DATABASES and "test" in (url.database or ""), url.database
    engine = create_engine(url, future=True, pool_size=20, max_overflow=0)
    # O schema vem da migração (alembic upgrade head), não de create_all.
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == _ALEMBIC_HEAD
    _truncate_all(engine)
    yield engine
    _truncate_all(engine)
    engine.dispose()


@pytest.fixture()
def pg_ctx(pg_engine, storage_dir):
    PgSessionLocal = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = PgSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[db_module.get_db] = override_get_db
    session = PgSessionLocal()
    owner = User(email="pg.dono@example.com", password_hash=hash_password("Senha123!"), role=Role.PROFESSOR)
    admin = User(email="pg.admin@example.com", password_hash=hash_password("Senha123!"), role=Role.ADMIN)
    session.add_all([owner, admin])
    session.flush()
    assessment = Assessment(title="Concorrência de imagens", owner_id=owner.id, status=AssessmentStatus.PUBLICADA)
    session.add(assessment)
    session.flush()
    question_id = _question(session, assessment.id).id
    session.commit()
    session.close()
    with TestClient(main_module.app) as client:
        tokens = {}
        for key, email in (("owner", "pg.dono@example.com"), ("admin", "pg.admin@example.com")):
            login = client.post("/v1/auth/login", json={"email": email, "password": "Senha123!"})
            assert login.status_code == 200, login.text
            tokens[key] = login.json()["access_token"]
        yield SimpleNamespace(
            client=client, Session=PgSessionLocal, question_id=question_id, engine=pg_engine, **tokens
        )
    main_module.app.dependency_overrides.clear()


class _AnswerLockGate:
    """Segura os `parties` primeiros SELECT ... FROM answers ... FOR UPDATE até todos chegarem.

    Todas as requisições já passaram nas checagens prévias (autorização,
    estágio, versão) com o mesmo estado; a disputa é decidida só pelo lock da
    linha de answers no PostgreSQL. As seguintes não esperam (já serializadas).
    """

    def __init__(self, engine):
        self._guard = Lock()
        self._remaining = 0
        self._barrier: Barrier | None = None
        event.listen(engine, "before_cursor_execute", self._wait)

    def arm(self, parties: int) -> None:
        with self._guard:
            self._barrier = Barrier(parties)
            self._remaining = parties

    def _wait(self, conn, cursor, statement, parameters, context, executemany):
        sql = statement.strip().upper()
        if not (sql.startswith("SELECT") and "FROM ANSWERS" in sql and sql.endswith("FOR UPDATE")):
            return
        with self._guard:
            if self._remaining == 0:
                return
            self._remaining -= 1
            barrier = self._barrier
        barrier.wait(timeout=15)


def _pg_state(ctx, answer_id: str) -> dict:
    session = ctx.Session()
    try:
        answer = session.get(Answer, answer_id)
        images = session.query(AnswerImage).filter_by(answer_id=answer_id).order_by(AnswerImage.id).all()
        image_ids = [image.id for image in images]
        events = (
            session.query(AuditEvent)
            .filter(AuditEvent.resource_id.in_([answer_id, *image_ids]))
            .order_by(AuditEvent.created_at)
            .all()
        )
        return {
            "status": answer.transcription_status,
            "text": answer.text,
            "version": answer.transcription_version,
            "active": [image.id for image in images if image.deleted_at is None],
            "deleted": {image.id: (image.deleted_at, image.deleted_by_id) for image in images if image.deleted_at},
            "actions": [event_.action for event_ in events],
        }
    finally:
        session.close()


# ---------------- ACD-10: excluir a última imagem ativa x confirmar ----------------
@requires_postgres
def test_pg_delete_last_image_vs_confirm_exactly_one_wins(pg_ctx):
    gate = _AnswerLockGate(pg_ctx.engine)
    winners = []
    for round_ in range(10):
        answer = _create_image_answer(pg_ctx.client, pg_ctx.owner, pg_ctx.question_id)
        image_id = answer["images"][0]["id"]
        gate.arm(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            delete_future = pool.submit(_delete, pg_ctx.client, pg_ctx.owner, image_id)
            confirm_future = pool.submit(_confirm, pg_ctx.client, pg_ctx.owner, answer["id"], f"Texto {round_}.", 0)
            delete, confirm = delete_future.result(), confirm_future.result()

        assert sorted([delete.status_code, confirm.status_code]) == [200, 409], (delete.text, confirm.text)
        state = _pg_state(pg_ctx, answer["id"])
        # Invariante: nunca confirmada sem imagem ativa.
        assert not (state["status"] == TranscriptionStatus.TRANSCRICAO_CONFIRMADA and not state["active"])
        if delete.status_code == 200:
            winners.append("delete")
            assert confirm.json()["code"] == "ANSWER_HAS_NO_ACTIVE_IMAGE"
            assert state["status"] == TranscriptionStatus.AGUARDANDO_TRANSCRICAO
            assert state["text"] is None and state["version"] == 0
            assert state["active"] == [] and list(state["deleted"]) == [image_id]
            assert state["actions"] == [DELETE_ACTION]
        else:
            winners.append("confirm")
            assert delete.json()["code"] == "ANSWER_IMAGES_LOCKED"
            assert state["status"] == TranscriptionStatus.TRANSCRICAO_CONFIRMADA
            assert state["text"] == f"Texto {round_}." and state["version"] == 1
            assert state["active"] == [image_id] and state["deleted"] == {}
            assert state["actions"] == [CONFIRM_ACTION]
    print(f"ACD-10 vencedores por rodada: {winners}")


# ---------------- ACD-07: exclusões concorrentes da mesma imagem ----------------
@requires_postgres
@pytest.mark.parametrize("parties", [2, 8])
def test_pg_concurrent_deletes_produce_one_effect_and_one_audit(pg_ctx, parties):
    gate = _AnswerLockGate(pg_ctx.engine)
    answer = _create_image_answer(pg_ctx.client, pg_ctx.owner, pg_ctx.question_id)
    image_id = answer["images"][0]["id"]
    gate.arm(parties)
    with ThreadPoolExecutor(max_workers=parties) as pool:
        responses = list(pool.map(lambda _: _delete(pg_ctx.client, pg_ctx.owner, image_id), range(parties)))

    assert [response.status_code for response in responses] == [200] * parties, [r.text for r in responses]
    assert len({response.json()["deleted_at"] for response in responses}) == 1
    state = _pg_state(pg_ctx, answer["id"])
    assert list(state["deleted"]) == [image_id]
    assert state["actions"] == [DELETE_ACTION]


# ---------------- ACD-14: restaurar após confirmação com a outra imagem ----------------
@requires_postgres
def test_pg_restore_after_confirmation_with_other_image_is_409_even_for_admin(pg_ctx):
    client = pg_ctx.client
    answer = _create_image_answer(client, pg_ctx.owner, pg_ctx.question_id)
    deleted_id = answer["images"][0]["id"]
    active_id = _add_image(client, pg_ctx.owner, answer["id"])

    assert _delete(client, pg_ctx.owner, deleted_id).status_code == 200
    confirmed = _confirm(client, pg_ctx.owner, answer["id"], "Texto pela outra imagem.", 0)
    assert confirmed.status_code == 200, confirmed.text
    assert [image["id"] for image in confirmed.json()["images"]] == [active_id]

    for token in (pg_ctx.owner, pg_ctx.admin):
        response = _restore(client, token, deleted_id)
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "ANSWER_IMAGES_LOCKED"

    state = _pg_state(pg_ctx, answer["id"])
    assert state["status"] == TranscriptionStatus.TRANSCRICAO_CONFIRMADA
    assert state["active"] == [active_id]
    assert list(state["deleted"]) == [deleted_id]
    assert RESTORE_ACTION not in state["actions"]


@requires_postgres
def test_pg_restore_vs_confirm_never_changes_confirmed_image_set(pg_ctx):
    """Corrida restaurar x confirmar (R3): o conjunto confirmado nunca muda depois."""
    gate = _AnswerLockGate(pg_ctx.engine)
    client = pg_ctx.client
    for round_ in range(5):
        answer = _create_image_answer(client, pg_ctx.owner, pg_ctx.question_id)
        deleted_id = answer["images"][0]["id"]
        active_id = _add_image(client, pg_ctx.owner, answer["id"])
        assert _delete(client, pg_ctx.owner, deleted_id).status_code == 200
        gate.arm(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            restore_future = pool.submit(_restore, client, pg_ctx.admin, deleted_id)
            confirm_future = pool.submit(_confirm, client, pg_ctx.owner, answer["id"], f"Texto {round_}.", 0)
            restore, confirm = restore_future.result(), confirm_future.result()

        assert confirm.status_code == 200, confirm.text
        state = _pg_state(pg_ctx, answer["id"])
        confirmed_ids = sorted(image["id"] for image in confirm.json()["images"])
        # O que a confirmação devolveu é exatamente o conjunto ativo final.
        assert sorted(state["active"]) == confirmed_ids
        if restore.status_code == 200:
            assert confirmed_ids == sorted([deleted_id, active_id])
        else:
            assert restore.status_code == 409 and restore.json()["code"] == "ANSWER_IMAGES_LOCKED"
            assert confirmed_ids == [active_id]
