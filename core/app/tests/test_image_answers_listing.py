"""AV-S06B (DEBT-AV-014) — retomada das respostas por imagem persistidas.

GET /v1/assessments/{id}/image-answers é leitura histórica: autorizada só por
propriedade (dono ou admin), sem exigir vínculo ativo de turma. Não cria, não
altera e não dispara nada.
"""
from __future__ import annotations

import io
from decimal import Decimal

import pytest
from PIL import Image

from app.config import get_settings
from app.models import (
    Answer,
    AnswerImage,
    AnswerSource,
    Assessment,
    AssessmentStatus,
    ClassGroup,
    CorrectionJob,
    Course,
    CourseDiscipline,
    Discipline,
    Organization,
    ProfessorClassLink,
    Question,
    Rubric,
    RubricCriterion,
    TranscriptionStatus,
    User,
)


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color=(30, 120, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


def _post_image_answer(client, token, question_id, *, student: str = "Aluno fictício"):
    return client.post(
        "/v1/answers/image",
        data={"question_id": question_id, "student_name_fake": student},
        files={"file": ("resposta.png", _image_bytes(), "image/png")},
        headers=_headers(token),
    )


def _list(client, token, assessment_id, question_id: str | None = None):
    params = {"question_id": question_id} if question_id is not None else None
    return client.get(f"/v1/assessments/{assessment_id}/image-answers", params=params, headers=_headers(token))


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


def _question(db_session, assessment_id: str, position: int) -> Question:
    question = Question(
        assessment_id=assessment_id,
        statement=f"Enunciado fictício {position}.",
        reference_answer="Resposta de referência.",
        max_score=Decimal("10.00"),
        position=position,
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
def assessment_with_questions(db_session, professor_token) -> tuple[str, str, str]:
    """Avaliação publicada (sem turma) com duas questões. Retorna (avaliação, q1, q2)."""
    assessment = Assessment(
        title="Avaliação com retomada por foto", owner_id=_owner(db_session).id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    first = _question(db_session, assessment.id, 1)
    second = _question(db_session, assessment.id, 2)
    db_session.commit()
    return assessment.id, first.id, second.id


@pytest.fixture()
def other_assessment_question(db_session, professor_token) -> str:
    assessment = Assessment(
        title="Outra avaliação", owner_id=_owner(db_session).id, status=AssessmentStatus.PUBLICADA
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id, 1)
    db_session.commit()
    return question.id


# ---------------- ACD-01: lista respostas IMAGE com estado e imagens ----------------
def test_lists_persisted_image_answers_with_state_and_images(
    client, db_session, professor_token, assessment_with_questions, storage_dir
):
    assessment_id, q1, q2 = assessment_with_questions
    first = _post_image_answer(client, professor_token, q1, student="Aluno A").json()
    second = _post_image_answer(client, professor_token, q2, student="Aluno B").json()
    text = client.post(
        "/v1/answers",
        json={"question_id": q1, "student_name_fake": "Aluno C", "text": "Resposta digitada."},
        headers=_headers(professor_token),
    )
    assert text.status_code == 201, text.text

    resp = _list(client, professor_token, assessment_id)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Uma nova requisição (como após F5 / nova sessão) devolve o que foi persistido.
    assert [item["id"] for item in body] == [first["id"], second["id"]]
    assert text.json()["id"] not in {item["id"] for item in body}
    for item in body:
        assert item["source"] == "IMAGE"
        assert item["transcription_status"] == "AGUARDANDO_TRANSCRICAO"
        assert item["text"] is None
        [image] = item["images"]
        assert image["answer_id"] == item["id"]
        assert image["content_type"] == "image/png"
    assert body[0]["images"][0]["id"] == first["images"][0]["id"]


def test_listing_is_read_only(client, db_session, professor_token, assessment_with_questions, storage_dir):
    assessment_id, q1, _ = assessment_with_questions
    _post_image_answer(client, professor_token, q1)
    db_session.rollback()
    before = (db_session.query(Answer).count(), db_session.query(AnswerImage).count())

    assert _list(client, professor_token, assessment_id).status_code == 200
    db_session.rollback()
    assert (db_session.query(Answer).count(), db_session.query(AnswerImage).count()) == before
    assert db_session.query(CorrectionJob).count() == 0


def test_empty_assessment_returns_empty_list(client, professor_token, assessment_with_questions):
    assessment_id, _, _ = assessment_with_questions
    resp = _list(client, professor_token, assessment_id)
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------- ACD-02: filtro por questão ----------------
def test_filter_by_question_restricts_results(
    client, professor_token, assessment_with_questions, storage_dir
):
    assessment_id, q1, q2 = assessment_with_questions
    _post_image_answer(client, professor_token, q1)
    on_second = _post_image_answer(client, professor_token, q2).json()

    resp = _list(client, professor_token, assessment_id, q2)
    assert resp.status_code == 200, resp.text
    assert [item["id"] for item in resp.json()] == [on_second["id"]]


def test_filter_by_question_of_other_assessment_returns_404(
    client, professor_token, assessment_with_questions, other_assessment_question, storage_dir
):
    assessment_id, _, _ = assessment_with_questions
    _post_image_answer(client, professor_token, other_assessment_question)
    resp = _list(client, professor_token, assessment_id, other_assessment_question)
    assert resp.status_code == 404


def test_filter_by_missing_question_returns_404(client, professor_token, assessment_with_questions):
    assessment_id, _, _ = assessment_with_questions
    assert _list(client, professor_token, assessment_id, "inexistente").status_code == 404


def test_missing_assessment_returns_404(client, professor_token):
    assert _list(client, professor_token, "inexistente").status_code == 404


# ---------------- ACD-03: autorização por propriedade ----------------
def test_listing_without_token_returns_401(client, assessment_with_questions):
    assessment_id, _, _ = assessment_with_questions
    assert _list(client, None, assessment_id).status_code == 401


def test_listing_by_other_professor_returns_403(
    client, professor_token, second_professor_token, assessment_with_questions, storage_dir
):
    assessment_id, q1, _ = assessment_with_questions
    _post_image_answer(client, professor_token, q1)
    assert _list(client, second_professor_token, assessment_id).status_code == 403
    assert _list(client, second_professor_token, assessment_id, q1).status_code == 403


def test_admin_can_list(client, professor_token, admin_token, assessment_with_questions, storage_dir):
    assessment_id, q1, _ = assessment_with_questions
    created = _post_image_answer(client, professor_token, q1).json()
    resp = _list(client, admin_token, assessment_id)
    assert resp.status_code == 200
    assert [item["id"] for item in resp.json()] == [created["id"]]


# ---------------- ACD-04: leitura histórica sem vínculo ativo ----------------
def test_owner_without_active_class_link_can_still_list(client, db_session, professor_token, storage_dir):
    owner = _owner(db_session)
    organization = Organization(name="Org retomada")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name="Curso", code="CUR-RET")
    discipline = Discipline(organization_id=organization.id, name="Disciplina", code="DISC-RET")
    db_session.add_all([course, discipline])
    db_session.flush()
    course_discipline = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(course_discipline)
    db_session.flush()
    class_group = ClassGroup(course_discipline_id=course_discipline.id, period="2026-2", code="T-RET")
    db_session.add(class_group)
    db_session.flush()
    assessment = Assessment(
        title="Avaliação de turma encerrada",
        owner_id=owner.id,
        class_group_id=class_group.id,
        status=AssessmentStatus.PUBLICADA,
    )
    db_session.add(assessment)
    db_session.flush()
    question = _question(db_session, assessment.id, 1)
    # Resposta persistida quando havia vínculo; o vínculo não existe mais.
    answer = Answer(
        question_id=question.id,
        student_name_fake="Aluno histórico",
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    db_session.add(answer)
    db_session.flush()
    db_session.add(
        AnswerImage(
            answer_id=answer.id,
            storage_filename="interno-nao-exposto.png",
            original_filename="historica.png",
            content_type="image/png",
            size_bytes=10,
            sha256_hash="0" * 64,
            uploaded_by_id=owner.id,
        )
    )
    db_session.commit()
    assert db_session.query(ProfessorClassLink).filter_by(professor_id=owner.id).count() == 0

    resp = _list(client, professor_token, assessment.id)
    assert resp.status_code == 200, resp.text
    [item] = resp.json()
    assert item["id"] == answer.id
    assert [image["original_filename"] for image in item["images"]] == ["historica.png"]
    # ACD-05: o nome interno do arquivo nunca aparece no corpo.
    assert "storage_filename" not in resp.text
    assert "interno-nao-exposto" not in resp.text

    filtered = _list(client, professor_token, assessment.id, question.id)
    assert filtered.status_code == 200
    assert [entry["id"] for entry in filtered.json()] == [answer.id]


# ---------------- ACD-05: storage_filename nunca exposto ----------------
def test_storage_filename_is_never_exposed(
    client, db_session, professor_token, assessment_with_questions, storage_dir
):
    assessment_id, q1, _ = assessment_with_questions
    created = _post_image_answer(client, professor_token, q1).json()
    db_session.rollback()
    stored = db_session.query(AnswerImage).filter_by(answer_id=created["id"]).one().storage_filename

    resp = _list(client, professor_token, assessment_id)
    assert resp.status_code == 200
    assert "storage_filename" not in resp.text
    assert stored not in resp.text
    for item in resp.json():
        for image in item["images"]:
            assert "storage_filename" not in image


# ---------------- ACD-09: bloqueio de correção permanece ----------------
def test_listed_image_answer_still_cannot_be_corrected(
    client, db_session, professor_token, assessment_with_questions, storage_dir
):
    assessment_id, q1, _ = assessment_with_questions
    _post_image_answer(client, professor_token, q1)
    [item] = _list(client, professor_token, assessment_id).json()

    resp = client.post(f"/v1/answers/{item['id']}/corrections", headers=_headers(professor_token))
    assert resp.status_code == 422
    assert resp.json()["code"] == "ANSWER_NOT_TRANSCRIBED"
    db_session.rollback()
    assert db_session.query(CorrectionJob).count() == 0
