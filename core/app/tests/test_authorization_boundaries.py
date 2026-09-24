from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.models import (
    Answer,
    Assessment,
    AssessmentStatus,
    CorrectionJob,
    HumanReview,
    JobStatus,
    Question,
    Rubric,
    RubricCriterion,
)


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


@pytest.fixture()
def owned_resources(db_session, professor_token):
    # professor_token ensures that the owner exists in this test's isolated DB.
    owner = db_session.query(Assessment).first()
    if owner is None:
        from app.models import User

        owner_user = db_session.query(User).filter(User.email == "professor@example.com").one()
        assessment = Assessment(
            title="Avaliação protegida",
            owner_id=owner_user.id,
            status=AssessmentStatus.PUBLICADA,
        )
        db_session.add(assessment)
        db_session.flush()
        question = Question(
            assessment_id=assessment.id,
            statement="Explique autorização por vínculo.",
            reference_answer="O recurso pertence ao proprietário.",
            max_score=Decimal("10.00"),
        )
        db_session.add(question)
        db_session.flush()
        rubric = Rubric(question_id=question.id, version=1, is_published=True)
        db_session.add(rubric)
        db_session.flush()
        db_session.add(
            RubricCriterion(
                rubric_id=rubric.id,
                name="Correção",
                description="",
                max_score=Decimal("10.00"),
            )
        )
        answer = Answer(
            question_id=question.id,
            student_name_fake="Aluno fictício",
            text="Resposta protegida.",
        )
        db_session.add(answer)
        db_session.flush()
        job = CorrectionJob(
            answer_id=answer.id,
            rubric_id=rubric.id,
            status=JobStatus.SUGERIDA,
            attempt=1,
        )
        db_session.add(job)
        db_session.commit()
        return {
            "assessment_id": assessment.id,
            "question_id": question.id,
            "answer_id": answer.id,
            "job_id": job.id,
        }
    raise AssertionError("fixture de recursos recebeu estado inesperado")


@pytest.fixture(params=["owner", "other_professor", "admin", "anonymous"])
def actor(request, professor_token, second_professor_token, admin_token):
    tokens = {
        "owner": professor_token,
        "other_professor": second_professor_token,
        "admin": admin_token,
        "anonymous": None,
    }
    return request.param, tokens[request.param]


def _expected_status(profile: str, allowed_status: int) -> int:
    return {
        "owner": allowed_status,
        "other_professor": 403,
        "admin": allowed_status,
        "anonymous": 401,
    }[profile]


def test_create_answer_authorization_matrix(client, db_session, owned_resources, actor):
    profile, token = actor
    before = db_session.query(Answer).count()

    response = client.post(
        "/v1/answers",
        json={
            "question_id": owned_resources["question_id"],
            "student_name_fake": "Novo aluno fictício",
            "text": "Nova resposta.",
        },
        headers=_headers(token),
    )

    assert response.status_code == _expected_status(profile, 201), response.text
    db_session.expire_all()
    expected_delta = 1 if profile in {"owner", "admin"} else 0
    assert db_session.query(Answer).count() == before + expected_delta


def test_request_correction_authorization_matrix(client, db_session, owned_resources, actor, monkeypatch):
    profile, token = actor
    monkeypatch.setattr("app.main.run_correction_job", lambda *args, **kwargs: None)
    before = db_session.query(CorrectionJob).count()

    response = client.post(
        f"/v1/answers/{owned_resources['answer_id']}/corrections",
        headers=_headers(token),
    )

    assert response.status_code == _expected_status(profile, 202), response.text
    db_session.expire_all()
    expected_delta = 1 if profile in {"owner", "admin"} else 0
    assert db_session.query(CorrectionJob).count() == before + expected_delta


def test_get_correction_job_authorization_matrix(client, owned_resources, actor):
    profile, token = actor
    response = client.get(
        f"/v1/correction-jobs/{owned_resources['job_id']}",
        headers=_headers(token),
    )
    assert response.status_code == _expected_status(profile, 200), response.text


def test_review_correction_authorization_matrix(client, db_session, owned_resources, actor):
    profile, token = actor
    before = db_session.query(HumanReview).count()

    response = client.post(
        f"/v1/corrections/{owned_resources['job_id']}/reviews",
        json={"decision": "APPROVE", "criteria_scores": [], "justification": None},
        headers=_headers(token),
    )

    assert response.status_code == _expected_status(profile, 200), response.text
    db_session.expire_all()
    expected_delta = 1 if profile in {"owner", "admin"} else 0
    assert db_session.query(HumanReview).count() == before + expected_delta


def test_correction_job_context_authorization_matrix(client, owned_resources, actor):
    profile, token = actor
    response = client.get(
        f"/v1/correction-jobs/{owned_resources['job_id']}/context",
        headers=_headers(token),
    )
    assert response.status_code == _expected_status(profile, 200), response.text

    if response.status_code == 200:
        body = response.json()
        assert body["job"]["id"] == owned_resources["job_id"]
        assert body["answer"]["id"] == owned_resources["answer_id"]
        assert body["question"]["id"] == owned_resources["question_id"]
        assert body["assessment"] == {
            "id": owned_resources["assessment_id"],
            "title": "Avaliação protegida",
        }


@pytest.mark.parametrize("missing_resource", ["job", "answer", "question", "assessment"])
def test_correction_job_context_returns_404_for_broken_chain(
    client, db_session, professor_token, owned_resources, missing_resource
):
    resource_models = {
        "job": (CorrectionJob, owned_resources["job_id"]),
        "answer": (Answer, owned_resources["answer_id"]),
        "question": (Question, owned_resources["question_id"]),
        "assessment": (Assessment, owned_resources["assessment_id"]),
    }
    model, resource_id = resource_models[missing_resource]
    db_session.execute(delete(model).where(model.id == resource_id))
    db_session.commit()

    response = client.get(
        f"/v1/correction-jobs/{owned_resources['job_id']}/context",
        headers=_headers(professor_token),
    )

    assert response.status_code == 404, response.text
