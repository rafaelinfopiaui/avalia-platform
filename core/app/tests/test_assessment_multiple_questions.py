import json
import threading
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

import app.main as main_module
from app.models import (
    Answer,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    CorrectionJob,
    HumanReview,
    JobStatus,
    Question,
    ReviewDecision,
    User,
)
from app.schemas import AssessmentCreate


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def question(name: str, score: int = 10, reference: str | None = None) -> dict:
    return {
        "statement": name,
        "reference_answer": reference or f"Reference {name}",
        "max_score": score,
    }


def create_assessment(client, token, title, questions):
    response = client.post(
        "/v1/assessments",
        json={"title": title, "questions": questions},
        headers=headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_rubric(client, token, question_id, name, score=10):
    response = client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [{"name": name, "max_score": score}]},
        headers=headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def get_assessment(client, token, assessment_id):
    response = client.get(
        f"/v1/assessments/{assessment_id}", headers=headers(token)
    )
    assert response.status_code == 200, response.text
    return response.json()


def order(data):
    return [(item["id"], item["position"]) for item in data["questions"]]


def test_ac01_ac02_create_and_read_ordered_questions(client, professor_token):
    """AC-01/02: GET returns every created question once in position order."""
    created = create_assessment(
        client,
        professor_token,
        "Ordered",
        [question("Q1", 10), question("Q2", 20), question("Q3", 30)],
    )
    fetched = get_assessment(client, professor_token, created["id"])
    assert order(fetched) == [
        (created["questions"][0]["id"], 1),
        (created["questions"][1]["id"], 2),
        (created["questions"][2]["id"], 3),
    ]
    assert len({item["id"] for item in fetched["questions"]}) == 3


def test_ac03_other_professor_cannot_mutate_draft(
    client, professor_token, second_professor_token
):
    """AC-03: another professor gets 403 and leaves the draft unchanged."""
    created = create_assessment(
        client, professor_token, "Owned", [question("Protected")]
    )
    question_id = created["questions"][0]["id"]
    response = client.patch(
        f"/v1/questions/{question_id}",
        json=question("Changed"),
        headers=headers(second_professor_token),
    )
    assert response.status_code == 403, response.text
    assert get_assessment(client, professor_token, created["id"])[
        "questions"
    ] == created["questions"]


def test_ac04_zero_questions_is_atomic(client, professor_token, db_session):
    """AC-04: zero questions returns 422 and preserves the empty draft."""
    owner = db_session.query(User).filter_by(email="professor@example.com").one()
    assessment = Assessment(
        title="Empty", owner_id=owner.id, status=AssessmentStatus.RASCUNHO
    )
    db_session.add(assessment)
    db_session.commit()
    before = get_assessment(client, professor_token, assessment.id)
    response = client.post(
        f"/v1/assessments/{assessment.id}/publish",
        headers=headers(professor_token),
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "MISSING_QUESTION"
    assert get_assessment(client, professor_token, assessment.id) == before
    assert before["status"] == "RASCUNHO" and before["questions"] == []


def test_ac04_rubric_mismatch_is_atomic(client, professor_token):
    """AC-04: mismatch returns 422 without publishing any state."""
    created = create_assessment(
        client,
        professor_token,
        "Mismatch",
        [question("Q1", 10), question("Q2", 20)],
    )
    q1, q2 = [item["id"] for item in created["questions"]]
    create_rubric(client, professor_token, q1, "Valid", 10)
    create_rubric(client, professor_token, q2, "Mismatch", 10)
    before = get_assessment(client, professor_token, created["id"])
    response = client.post(
        f"/v1/assessments/{created['id']}/publish",
        headers=headers(professor_token),
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "RUBRIC_TOTAL_MISMATCH"
    after = get_assessment(client, professor_token, created["id"])
    assert after == before and after["status"] == "RASCUNHO"
    assert not any(
        rubric["is_published"]
        for item in after["questions"]
        for rubric in item["rubrics"]
    )


def test_ac05_published_mutations_return_409(client, professor_token):
    """AC-05: all public mutation routes reject a published assessment."""
    created = create_assessment(
        client, professor_token, "Published", [question("Q1")]
    )
    assessment_id = created["id"]
    question_id = created["questions"][0]["id"]
    create_rubric(client, professor_token, question_id, "C1")
    published = client.post(
        f"/v1/assessments/{assessment_id}/publish",
        headers=headers(professor_token),
    )
    assert published.status_code == 200, published.text
    responses = [
        client.patch(
            f"/v1/assessments/{assessment_id}",
            json={"title": "Changed"},
            headers=headers(professor_token),
        ),
        client.patch(
            f"/v1/questions/{question_id}",
            json=question("Changed"),
            headers=headers(professor_token),
        ),
        client.delete(f"/v1/questions/{question_id}", headers=headers(professor_token)),
        client.put(
            f"/v1/assessments/{assessment_id}/questions/order",
            json={"question_ids": [question_id]},
            headers=headers(professor_token),
        ),
        client.post(
            f"/v1/assessments/{assessment_id}/questions",
            json=question("New"),
            headers=headers(professor_token),
        ),
        client.post(
            f"/v1/questions/{question_id}/rubric",
            json={"criteria": [{"name": "New", "max_score": 10}]},
            headers=headers(professor_token),
        ),
    ]
    assert [response.status_code for response in responses] == [409] * 6


def test_ac06_clone_excludes_operational_history(
    client, professor_token, db_session: Session
):
    """AC-06: clone gets new content IDs and no original operational rows."""
    original = create_assessment(
        client, professor_token, "Original", [question("Original Q")]
    )
    original_q = original["questions"][0]["id"]
    original_rubric = create_rubric(
        client, professor_token, original_q, "Original criterion"
    )
    published = client.post(
        f"/v1/assessments/{original['id']}/publish",
        headers=headers(professor_token),
    )
    assert published.status_code == 200, published.text
    owner = db_session.query(User).filter_by(email="professor@example.com").one()
    answer = Answer(question_id=original_q, student_name_fake="Student", text="Answer")
    db_session.add(answer)
    db_session.flush()
    job = CorrectionJob(
        answer_id=answer.id,
        rubric_id=original_rubric["id"],
        status=JobStatus.SUGERIDA,
        attempt=1,
    )
    db_session.add(job)
    db_session.flush()
    review = HumanReview(
        job_id=job.id,
        reviewer_id=owner.id,
        decision=ReviewDecision.APPROVE,
        final_total=Decimal("10"),
        final_scores_json="[]",
    )
    event = AuditEvent(
        actor_id=owner.id,
        action="HISTORY",
        resource_type="Assessment",
        resource_id=original["id"],
    )
    db_session.add_all([review, event])
    db_session.commit()
    ids = answer.id, job.id, review.id, event.id
    original_before = get_assessment(client, professor_token, original["id"])

    response = client.post(
        f"/v1/assessments/{original['id']}/clone",
        headers=headers(professor_token),
    )
    assert response.status_code == 201, response.text
    clone = response.json()
    clone_q = clone["questions"][0]["id"]
    clone_rubric = clone["questions"][0]["rubrics"][0]["id"]
    assert clone["status"] == "RASCUNHO"
    assert clone["cloned_from_id"] == original["id"]
    assert clone_q != original_q and clone_rubric != original_rubric["id"]

    db_session.expire_all()
    assert db_session.get(Answer, ids[0]).question_id == original_q
    assert db_session.get(CorrectionJob, ids[1]).answer_id == ids[0]
    assert db_session.get(CorrectionJob, ids[1]).rubric_id == original_rubric["id"]
    assert db_session.get(HumanReview, ids[2]).job_id == ids[1]
    assert db_session.get(AuditEvent, ids[3]).resource_id == original["id"]
    clone_answers = (
        db_session.query(Answer)
        .join(Question, Answer.question_id == Question.id)
        .filter(Question.assessment_id == clone["id"])
        .all()
    )
    clone_jobs = (
        db_session.query(CorrectionJob)
        .join(Answer, CorrectionJob.answer_id == Answer.id)
        .join(Question, Answer.question_id == Question.id)
        .filter(Question.assessment_id == clone["id"])
        .all()
    )
    clone_reviews = (
        db_session.query(HumanReview)
        .join(CorrectionJob, HumanReview.job_id == CorrectionJob.id)
        .join(Answer, CorrectionJob.answer_id == Answer.id)
        .join(Question, Answer.question_id == Question.id)
        .filter(Question.assessment_id == clone["id"])
        .all()
    )
    assert clone_answers == [] and clone_jobs == [] and clone_reviews == []
    clone_events = db_session.query(AuditEvent).filter_by(resource_id=clone["id"]).all()
    assert [(item.action, item.resource_type) for item in clone_events] == [
        ("CLONE", "Assessment")
    ]
    assert json.loads(clone_events[0].before_json) == {
        "source_assessment_id": original["id"]
    }
    assert ids[3] not in {item.id for item in clone_events}
    assert get_assessment(client, professor_token, original["id"]) == original_before


def test_ac07_original_context_survives_clone_republication(
    client, professor_token, db_session: Session
):
    """AC-07: an original job stays pinned after clone editing/publication."""
    original = create_assessment(
        client,
        professor_token,
        "Original context",
        [question("Original statement", reference="Original reference")],
    )
    original_q = original["questions"][0]["id"]
    original_rubric = create_rubric(
        client, professor_token, original_q, "Original criterion"
    )
    published = client.post(
        f"/v1/assessments/{original['id']}/publish",
        headers=headers(professor_token),
    )
    assert published.status_code == 200, published.text
    answer = Answer(question_id=original_q, student_name_fake="Student", text="Answer")
    db_session.add(answer)
    db_session.flush()
    job = CorrectionJob(
        answer_id=answer.id,
        rubric_id=original_rubric["id"],
        status=JobStatus.PENDENTE,
        attempt=1,
    )
    db_session.add(job)
    db_session.commit()
    job_id = job.id
    cloned = client.post(
        f"/v1/assessments/{original['id']}/clone",
        headers=headers(professor_token),
    )
    assert cloned.status_code == 201, cloned.text
    clone = cloned.json()
    clone_q = clone["questions"][0]["id"]
    changed = client.patch(
        f"/v1/questions/{clone_q}",
        json=question("Clone statement", reference="Clone reference"),
        headers=headers(professor_token),
    )
    assert changed.status_code == 200, changed.text
    clone_rubric = create_rubric(
        client, professor_token, clone_q, "Clone criterion"
    )
    assert clone_rubric["version"] == 2
    republished = client.post(
        f"/v1/assessments/{clone['id']}/publish",
        headers=headers(professor_token),
    )
    assert republished.status_code == 200, republished.text
    response = client.get(
        f"/v1/correction-jobs/{job_id}/context",
        headers=headers(professor_token),
    )
    assert response.status_code == 200, response.text
    context = response.json()
    assert context["assessment"] == {
        "id": original["id"],
        "title": "Original context",
    }
    assert context["question"]["id"] == original_q
    assert context["question"]["statement"] == "Original statement"
    assert context["question"]["reference_answer"] == "Original reference"
    assert [item["id"] for item in context["question"]["rubrics"]] == [
        original_rubric["id"]
    ]
    rubric = context["question"]["rubrics"][0]
    assert rubric["version"] == 1
    assert rubric["criteria"][0]["name"] == "Original criterion"
    db_session.expire_all()
    assert db_session.get(CorrectionJob, job_id).rubric_id == original_rubric["id"]


def test_ac08_second_question_context_and_highest_rubric_version(
    client, professor_token, db_session: Session
):
    """AC-08: context uses question two; publish chooses highest version."""
    created = create_assessment(
        client,
        professor_token,
        "Two questions",
        [
            question("First statement", reference="First reference"),
            question("Second statement", reference="Second reference"),
        ],
    )
    first, second = [item["id"] for item in created["questions"]]
    create_rubric(client, professor_token, first, "First old")
    first_latest = create_rubric(client, professor_token, first, "First latest")
    create_rubric(client, professor_token, second, "Second old")
    second_latest = create_rubric(client, professor_token, second, "Second latest")
    assert first_latest["version"] == second_latest["version"] == 2
    published = client.post(
        f"/v1/assessments/{created['id']}/publish",
        headers=headers(professor_token),
    )
    assert published.status_code == 200, published.text
    fetched = get_assessment(client, professor_token, created["id"])
    for item, latest in zip(
        fetched["questions"], [first_latest, second_latest], strict=True
    ):
        selected = [rubric for rubric in item["rubrics"] if rubric["is_published"]]
        assert [(rubric["id"], rubric["version"]) for rubric in selected] == [
            (latest["id"], 2)
        ]
    answer = Answer(question_id=second, student_name_fake="Student", text="A2")
    db_session.add(answer)
    db_session.flush()
    job = CorrectionJob(
        answer_id=answer.id,
        rubric_id=second_latest["id"],
        status=JobStatus.PENDENTE,
        attempt=1,
    )
    db_session.add(job)
    db_session.commit()
    response = client.get(
        f"/v1/correction-jobs/{job.id}/context",
        headers=headers(professor_token),
    )
    assert response.status_code == 200, response.text
    context = response.json()
    assert context["question"]["id"] == second
    assert context["question"]["id"] != first
    assert context["question"]["statement"] == "Second statement"
    assert context["question"]["statement"] != "First statement"
    assert context["question"]["reference_answer"] == "Second reference"
    assert any(
        item["id"] == second_latest["id"]
        and item["version"] == 2
        and item["is_published"]
        for item in context["question"]["rubrics"]
    )


def test_ac09_ac16_payload_truth_table_and_output_cardinality(
    client, professor_token, db_session: Session
):
    """AC-09/16: complete singular/plural truth table and output behavior."""
    auth = headers(professor_token)
    plural = client.post(
        "/v1/assessments",
        json={"title": "Plural", "questions": [question("P1"), question("P2")]},
        headers=auth,
    )
    assert plural.status_code == 201, plural.text
    assert len(plural.json()["questions"]) == 2
    assert plural.json()["question"] is None
    singular = client.post(
        "/v1/assessments",
        json={"title": "Singular", "question": question("S1")},
        headers=auth,
    )
    assert singular.status_code == 201, singular.text
    assert singular.json()["question"] == singular.json()["questions"][0]
    both = client.post(
        "/v1/assessments",
        json={
            "title": "Both",
            "question": question("S1"),
            "questions": [question("P1")],
        },
        headers=auth,
    )
    assert both.status_code == 422, both.text
    assert both.json()["detail"][0]["msg"] == (
        "Value error, Forneça `questions` ou `question`, não ambos. "
        "`question` está depreciado; prefira `questions`."
    )
    for payload in [{"title": "None"}, {"title": "Empty", "questions": []}]:
        response = client.post("/v1/assessments", json=payload, headers=auth)
        assert response.status_code == 422, response.text
        assert response.json()["detail"][0]["msg"] == (
            "Value error, Pelo menos uma questão é obrigatória."
        )
    singular_empty = client.post(
        "/v1/assessments",
        json={"title": "Singular empty", "question": question("S"), "questions": []},
        headers=auth,
    )
    assert singular_empty.status_code == 201, singular_empty.text
    assert singular_empty.json()["question"] == singular_empty.json()["questions"][0]
    owner = db_session.query(User).filter_by(email="professor@example.com").one()
    empty = Assessment(
        title="Output empty", owner_id=owner.id, status=AssessmentStatus.RASCUNHO
    )
    db_session.add(empty)
    db_session.commit()
    output = get_assessment(client, professor_token, empty.id)
    assert output["questions"] == [] and output["question"] is None


def test_ac11_reorder_rollback_and_delete_recompaction(client, professor_token):
    """AC-11: all invalid orders roll back; intermediate deletion recompacts."""
    primary = create_assessment(
        client,
        professor_token,
        "Ordering",
        [question("Q1"), question("Q2"), question("Q3")],
    )
    other = create_assessment(client, professor_token, "Other", [question("Other")])
    q1, q2, q3 = [item["id"] for item in primary["questions"]]
    other_q = other["questions"][0]["id"]
    response = client.put(
        f"/v1/assessments/{primary['id']}/questions/order",
        json={"question_ids": [q3, q1, q2]},
        headers=headers(professor_token),
    )
    assert response.status_code == 200, response.text
    expected = [(q3, 1), (q1, 2), (q2, 3)]
    assert order(response.json()) == expected
    for invalid in [[q3, q3, q2], [q3, q1], [q3, q1, other_q]]:
        response = client.put(
            f"/v1/assessments/{primary['id']}/questions/order",
            json={"question_ids": invalid},
            headers=headers(professor_token),
        )
        assert response.status_code == 422, response.text
        assert order(get_assessment(client, professor_token, primary["id"])) == expected
    deleted = client.delete(f"/v1/questions/{q1}", headers=headers(professor_token))
    assert deleted.status_code == 204, deleted.text
    assert order(get_assessment(client, professor_token, primary["id"])) == [
        (q3, 1),
        (q2, 2),
    ]


def test_ac11_answered_draft_delete_conflict(client, professor_token, db_session):
    """AC-11 regression: DELETE 409 preserves an answered draft question."""
    created = create_assessment(client, professor_token, "Answered", [question("Q")])
    question_id = created["questions"][0]["id"]
    answer = Answer(question_id=question_id, student_name_fake="Student", text="A")
    db_session.add(answer)
    db_session.commit()
    answer_id = answer.id
    response = client.delete(
        f"/v1/questions/{question_id}", headers=headers(professor_token)
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "detail": "Questão possui respostas registradas; não pode ser excluída."
    }
    db_session.expire_all()
    assert db_session.get(Question, question_id) is not None
    assert db_session.get(Answer, answer_id).question_id == question_id


def test_ac11_delete_create_answer_race_returns_409(client, professor_token, test_engine, db_session):
    """AC-11 regression: a TOCTOU race between delete_question's own
    Answer-existence check and its physical DELETE must not surface as an
    unhandled IntegrityError. A concurrent create_answer that commits an
    Answer *after* the check passed but *before* the DELETE executes must
    cause delete_question to roll back and return the same domain 409,
    never a bare 500, and must preserve both the Question and the Answer.

    SQLite does not enforce foreign keys unless PRAGMA foreign_keys=ON is
    issued per-connection; this test enables it explicitly on test_engine so
    the FK violation that only happens for real in PostgreSQL is reproduced
    here too, deterministically (no thread timing / wall clock).
    """
    from sqlalchemy import event
    from sqlalchemy.orm import sessionmaker

    @event.listens_for(test_engine, "connect")
    def _enable_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    created = create_assessment(client, professor_token, "Race", [question("Q")])
    question_id = created["questions"][0]["id"]

    professor = db_session.query(User).filter_by(email="professor@example.com").one()

    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    race_db = TestingSessionLocal()
    race_user = race_db.get(User, professor.id)

    original_delete = race_db.delete
    injected = {"done": False}

    def patched_delete(instance):
        # Fires exactly inside delete_question, right after its own Answer
        # existence check already returned "no rows" -- the TOCTOU window.
        if not injected["done"] and isinstance(instance, Question):
            injected["done"] = True
            racer = TestingSessionLocal()
            racer.add(Answer(question_id=question_id, student_name_fake="Aluno", text="resposta concorrente"))
            racer.commit()
            racer.close()
        return original_delete(instance)

    race_db.delete = patched_delete

    try:
        with pytest.raises(main_module.HTTPException) as excinfo:
            main_module.delete_question(question_id=question_id, db=race_db, user=race_user)
        assert excinfo.value.status_code == 409
        assert excinfo.value.detail == "Questão possui respostas registradas; não pode ser excluída."
    finally:
        race_db.close()

    db_session.expire_all()
    assert db_session.get(Question, question_id) is not None, "Question must survive the raced delete"
    surviving_answers = db_session.query(Answer).filter(Answer.question_id == question_id).all()
    assert len(surviving_answers) == 1, "The concurrently created Answer must survive"


def test_ac12_question_count_boundaries(client, professor_token):
    """AC-12: 50 questions pass and 51 fail."""
    for count, status in [(50, 201), (51, 422)]:
        response = client.post(
            "/v1/assessments",
            json={
                "title": str(count),
                "questions": [question(f"Q{index}") for index in range(count)],
            },
            headers=headers(professor_token),
        )
        assert response.status_code == status, response.text
        if status == 201:
            assert len(response.json()["questions"]) == 50


def test_ac12_statement_boundaries(client, professor_token):
    """AC-12: statement accepts 10,000 and rejects 10,001 characters."""
    for length, status in [(10_000, 201), (10_001, 422)]:
        response = client.post(
            "/v1/assessments",
            json={
                "title": f"Statement {length}",
                "questions": [question("s" * length, reference="Reference")],
            },
            headers=headers(professor_token),
        )
        assert response.status_code == status, response.text


def test_ac12_reference_answer_boundaries(client, professor_token):
    """AC-12: reference accepts 10,000 and rejects 10,001 characters."""
    for length, status in [(10_000, 201), (10_001, 422)]:
        response = client.post(
            "/v1/assessments",
            json={
                "title": f"Reference {length}",
                "questions": [question("Q", reference="r" * length)],
            },
            headers=headers(professor_token),
        )
        assert response.status_code == status, response.text


def test_ac12_title_has_no_max_length(client, professor_token):
    """AC-12: title metadata has no max_length and accepts a long value."""
    field = AssessmentCreate.model_fields["title"]
    assert all(getattr(item, "max_length", None) is None for item in field.metadata)
    title = "t" * 20_000
    response = client.post(
        "/v1/assessments",
        json={"title": title, "questions": [question("Q")]},
        headers=headers(professor_token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["title"] == title


def test_ac12_max_score_and_numeric_metadata(client, professor_token):
    """AC-12: nonpositive scores fail and the ORM type remains Numeric(6,2)."""
    numeric_type = Question.__table__.c.max_score.type
    assert numeric_type.precision == 6 and numeric_type.scale == 2
    for score in [0, -1]:
        response = client.post(
            "/v1/assessments",
            json={"title": str(score), "questions": [question("Q", score)]},
            headers=headers(professor_token),
        )
        assert response.status_code == 422, response.text


def test_ac13_legacy_single_question_read(client, professor_token, db_session):
    """AC-13: a legacy single question reads unchanged at position one."""
    owner = db_session.query(User).filter_by(email="professor@example.com").one()
    assessment = Assessment(
        title="Legacy", owner_id=owner.id, status=AssessmentStatus.RASCUNHO
    )
    legacy = Question(
        statement="Legacy statement",
        reference_answer="Legacy reference",
        max_score=Decimal("10"),
        position=1,
    )
    assessment.questions.append(legacy)
    db_session.add(assessment)
    db_session.commit()
    response = client.get(
        f"/v1/assessments/{assessment.id}", headers=headers(professor_token)
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["questions"][0]["id"] == legacy.id
    assert data["questions"][0]["statement"] == "Legacy statement"
    assert data["questions"][0]["reference_answer"] == "Legacy reference"
    assert data["questions"][0]["position"] == 1
    assert data["question"] == data["questions"][0]


def test_ac14_mutations_use_shared_authorization_helpers(
    client, professor_token, monkeypatch
):
    """AC-14: root-question and collection routes call the shared guards."""
    created = create_assessment(
        client,
        professor_token,
        "Helpers",
        [question("Update"), question("Rubric"), question("Delete")],
    )
    assessment_id = created["id"]
    update_id, rubric_id, delete_id = [item["id"] for item in created["questions"]]
    helper_calls = []
    mutation_calls = []
    original_helper = main_module._get_assessment_for_question
    original_mutation = main_module.require_assessment_mutation

    def spy_helper(db, question_id, user):
        helper_calls.append(question_id)
        return original_helper(db, question_id, user)

    def spy_mutation(db, user, assessment):
        mutation_calls.append(assessment.id)
        return original_mutation(db, user, assessment)

    monkeypatch.setattr(main_module, "_get_assessment_for_question", spy_helper)
    monkeypatch.setattr(main_module, "require_assessment_mutation", spy_mutation)
    updated = client.patch(
        f"/v1/questions/{update_id}",
        json=question("Updated"),
        headers=headers(professor_token),
    )
    assert updated.status_code == 200, updated.text
    rubric = client.post(
        f"/v1/questions/{rubric_id}/rubric",
        json={"criteria": [{"name": "C", "max_score": 10}]},
        headers=headers(professor_token),
    )
    assert rubric.status_code == 201, rubric.text
    deleted = client.delete(
        f"/v1/questions/{delete_id}", headers=headers(professor_token)
    )
    assert deleted.status_code == 204, deleted.text
    assert helper_calls == [update_id, rubric_id, delete_id]
    assert mutation_calls == [assessment_id] * 3
    previous = len(mutation_calls)
    added = client.post(
        f"/v1/assessments/{assessment_id}/questions",
        json=question("Added"),
        headers=headers(professor_token),
    )
    assert added.status_code == 201, added.text
    assert mutation_calls[previous:] == [assessment_id]
    assert helper_calls == [update_id, rubric_id, delete_id]
    current = get_assessment(client, professor_token, assessment_id)
    ids = [item["id"] for item in reversed(current["questions"])]
    previous = len(mutation_calls)
    reordered = client.put(
        f"/v1/assessments/{assessment_id}/questions/order",
        json={"question_ids": ids},
        headers=headers(professor_token),
    )
    assert reordered.status_code == 200, reordered.text
    assert mutation_calls[previous:] == [assessment_id]
    assert helper_calls == [update_id, rubric_id, delete_id]


def test_ac15_sqlite_concurrency_smoke(client, professor_token):
    """AC-15 smoke: SQLite threads preserve 1..N; this does not prove locks."""
    created = create_assessment(
        client,
        professor_token,
        "Concurrency",
        [question(f"Q{index}") for index in range(10)],
    )
    assessment_id = created["id"]
    ids = [item["id"] for item in created["questions"]]
    results = []
    result_lock = threading.Lock()

    def reorder(new_order):
        try:
            response = client.put(
                f"/v1/assessments/{assessment_id}/questions/order",
                json={"question_ids": new_order},
                headers=headers(professor_token),
            )
            result = response.status_code, response.text
        except Exception as exc:  # pragma: no cover - reported by assertion
            result = None, repr(exc)
        with result_lock:
            results.append(result)

    threads = [
        threading.Thread(target=reorder, args=(ids[::-1],)),
        threading.Thread(target=reorder, args=(ids[1:] + ids[:1],)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(results) == 2
    assert all(status == 200 for status, _ in results), results
    final = get_assessment(client, professor_token, assessment_id)
    assert len(final["questions"]) == 10
    assert sorted(item["position"] for item in final["questions"]) == list(range(1, 11))


def test_ac17_legacy_log_payload_is_distinguishable(
    client, professor_token, monkeypatch
):
    """AC-17: legacy input logs the exact event and complete identifying fields."""
    calls = []

    def fake_log_event(event, correlation_id, **fields):
        calls.append((event, correlation_id, fields))

    monkeypatch.setattr(main_module, "log_event", fake_log_event)
    canonical = client.post(
        "/v1/assessments",
        json={"title": "Canonical", "questions": [question("P")]},
        headers=headers(professor_token),
    )
    assert canonical.status_code == 201, canonical.text
    assert not any(
        event == "assessment_created_legacy_singular_payload"
        for event, _, _ in calls
    )
    calls.clear()
    legacy = client.post(
        "/v1/assessments",
        json={"title": "Legacy", "question": question("S")},
        headers=headers(professor_token),
    )
    assert legacy.status_code == 201, legacy.text
    legacy_calls = [
        call
        for call in calls
        if call[0] == "assessment_created_legacy_singular_payload"
    ]
    assert len(legacy_calls) == 1
    event, correlation_id, fields = legacy_calls[0]
    assert event == "assessment_created_legacy_singular_payload"
    assert correlation_id
    assert fields == {
        "assessment_id": legacy.json()["id"],
        "assessment_created_legacy_singular_payload": True,
    }
