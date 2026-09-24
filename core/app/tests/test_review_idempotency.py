from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy.orm import Session

from app.models import (
    AIExecution,
    Answer,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    CorrectionJob,
    CriterionScore,
    HumanReview,
    JobStatus,
    Question,
    Rubric,
    RubricCriterion,
    User,
)


@pytest.fixture()
def review_job(db_session, professor_token):
    owner = db_session.query(User).filter(User.email == "professor@example.com").one()
    assessment = Assessment(
        title="Avaliação de idempotência",
        owner_id=owner.id,
        status=AssessmentStatus.PUBLICADA,
    )
    db_session.add(assessment)
    db_session.flush()
    question = Question(
        assessment_id=assessment.id,
        statement="Explique idempotência.",
        reference_answer="Uma repetição equivalente não muda o estado.",
        max_score=Decimal("10.00"),
    )
    db_session.add(question)
    db_session.flush()
    rubric = Rubric(question_id=question.id, version=1, is_published=True)
    db_session.add(rubric)
    db_session.flush()
    criterion = RubricCriterion(
        rubric_id=rubric.id,
        name="Precisão",
        description="",
        max_score=Decimal("10.00"),
    )
    db_session.add(criterion)
    answer = Answer(
        question_id=question.id,
        student_name_fake="Aluno fictício",
        text="Repetir com segurança.",
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
    db_session.flush()
    execution = AIExecution(
        job_id=job.id,
        engine_mode="simulated",
        model="test",
        confidence_method_version="test-v1",
        overall_confidence=Decimal("0.9000"),
        review_recommendation="REVIEW_OPTIONAL",
    )
    db_session.add(execution)
    db_session.flush()
    db_session.add(
        CriterionScore(
            ai_execution_id=execution.id,
            criterion_id=criterion.id,
            score=Decimal("8.00"),
            max_score=criterion.max_score,
            reason="Teste",
            evidence="",
            confidence=Decimal("0.9000"),
        )
    )
    db_session.commit()
    return {
        "job_id": job.id,
        "criterion_id": criterion.id,
        "owner_id": owner.id,
        "owner_email": owner.email,
    }


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _approve(client, token, job_id):
    return client.post(
        f"/v1/corrections/{job_id}/reviews",
        json={"decision": "APPROVE", "criteria_scores": [], "justification": None},
        headers=_headers(token),
    )


def _alter(client, token, job_id, criterion_id, score):
    return client.post(
        f"/v1/corrections/{job_id}/reviews",
        json={
            "decision": "ALTER",
            "criteria_scores": [{"criterion_id": criterion_id, "score": score}],
            "justification": "Ajuste fundamentado.",
        },
        headers=_headers(token),
    )


def test_equivalent_retry_returns_existing_review_without_duplicate_or_audit(
    client, professor_token, db_session, review_job
):
    first = _alter(
        client, professor_token, review_job["job_id"], review_job["criterion_id"], "7.0"
    )
    second = _alter(
        client, professor_token, review_job["job_id"], review_job["criterion_id"], "7.00"
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    db_session.expire_all()
    assert db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).count() == 1
    assert db_session.query(AuditEvent).filter_by(resource_id=review_job["job_id"]).count() == 1


def test_different_decision_returns_conflict_and_preserves_original(
    client, professor_token, db_session, review_job
):
    original = _approve(client, professor_token, review_job["job_id"])
    conflict = client.post(
        f"/v1/corrections/{review_job['job_id']}/reviews",
        json={
            "decision": "ALTER",
            "criteria_scores": [
                {"criterion_id": review_job["criterion_id"], "score": "7.00"}
            ],
            "justification": "Ajuste fundamentado.",
        },
        headers=_headers(professor_token),
    )

    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["code"] == "REVIEW_ALREADY_EXISTS"
    existing_review = conflict.json()["existing_review"]
    assert existing_review["id"] == original.json()["id"]
    assert existing_review["reviewer_email"] == review_job["owner_email"]
    assert existing_review["final_scores"] == [
        {"criterion_id": review_job["criterion_id"], "score": "8.00"}
    ]
    assert "job_id" not in existing_review
    db_session.expire_all()
    persisted = db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).one()
    assert persisted.id == original.json()["id"]
    assert persisted.decision.value == "APPROVE"
    assert persisted.final_total == Decimal("8.00")


def test_approve_retry_compares_justification_symmetrically(
    client, professor_token, db_session, review_job
):
    first = client.post(
        f"/v1/corrections/{review_job['job_id']}/reviews",
        json={
            "decision": "APPROVE",
            "criteria_scores": [],
            "justification": "Aprovação fundamentada.",
        },
        headers=_headers(professor_token),
    )
    conflict = _approve(client, professor_token, review_job["job_id"])

    assert first.status_code == 200, first.text
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["existing_review"]["justification"] == "Aprovação fundamentada."
    db_session.expire_all()
    assert db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).count() == 1


def test_approve_retry_treats_null_and_empty_justification_as_equivalent(
    client, professor_token, db_session, review_job
):
    first = _approve(client, professor_token, review_job["job_id"])
    second = client.post(
        f"/v1/corrections/{review_job['job_id']}/reviews",
        json={"decision": "APPROVE", "criteria_scores": [], "justification": ""},
        headers=_headers(professor_token),
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    db_session.expire_all()
    assert db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).count() == 1


def test_concurrent_equivalent_requests_persist_exactly_one_review(
    client, professor_token, db_session, review_job, monkeypatch
):
    barrier = Barrier(2)
    original_commit = Session.commit

    def synchronized_commit(session):
        if any(isinstance(item, HumanReview) for item in session.new):
            barrier.wait(timeout=5)
        return original_commit(session)

    monkeypatch.setattr(Session, "commit", synchronized_commit)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: _approve(client, professor_token, review_job["job_id"]),
                range(2),
            )
        )

    assert [response.status_code for response in responses] == [200, 200]
    assert len({response.json()["id"] for response in responses}) == 1
    db_session.expire_all()
    assert db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).count() == 1
    assert db_session.query(AuditEvent).filter_by(resource_id=review_job["job_id"]).count() == 1


def test_unrelated_professor_remains_forbidden(
    client, second_professor_token, db_session, review_job
):
    response = _approve(client, second_professor_token, review_job["job_id"])

    assert response.status_code == 403, response.text
    db_session.expire_all()
    assert db_session.query(HumanReview).filter_by(job_id=review_job["job_id"]).count() == 0


def test_context_exposes_null_then_persisted_human_review(
    client, professor_token, review_job
):
    before = client.get(
        f"/v1/correction-jobs/{review_job['job_id']}/context",
        headers=_headers(professor_token),
    )
    assert before.status_code == 200, before.text
    assert before.json()["human_review"] is None

    created = _approve(client, professor_token, review_job["job_id"])
    after = client.get(
        f"/v1/correction-jobs/{review_job['job_id']}/context",
        headers=_headers(professor_token),
    )

    assert after.status_code == 200, after.text
    review = after.json()["human_review"]
    assert review["id"] == created.json()["id"]
    assert review["reviewer_id"] == review_job["owner_id"]
    assert review["reviewer_email"] == review_job["owner_email"]
    assert review["decision"] == "APPROVE"
    assert Decimal(str(review["final_total"])) == Decimal("8.00")
    assert review["final_scores"] == [
        {"criterion_id": review_job["criterion_id"], "score": "8.00"}
    ]
    assert review["justification"] is None
    assert review["created_at"]
