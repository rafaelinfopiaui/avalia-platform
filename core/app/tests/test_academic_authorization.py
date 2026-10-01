from datetime import datetime, timedelta

import pytest

import app.main as main_module
from app.models import (
    Answer,
    Assessment,
    ClassGroup,
    CorrectionJob,
    Course,
    CourseDiscipline,
    Discipline,
    Enrollment,
    JobStatus,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Question,
    Rubric,
    Student,
    User,
)


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _user(db_session, email):
    return db_session.query(User).filter_by(email=email).one()


def _academic_context(db_session, suffix="one"):
    organization = Organization(name=f"Organization {suffix}")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name=f"Course {suffix}", code=f"COURSE-{suffix}")
    discipline = Discipline(
        organization_id=organization.id,
        name=f"Discipline {suffix}",
        code=f"DISC-{suffix}",
    )
    db_session.add_all([course, discipline])
    db_session.flush()
    course_discipline = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(course_discipline)
    db_session.flush()
    class_group = ClassGroup(
        course_discipline_id=course_discipline.id,
        period="2026-2",
        code=f"GROUP-{suffix}",
    )
    student = Student(
        organization_id=organization.id,
        name=f"Student {suffix}",
        external_id=f"STUDENT-{suffix}",
    )
    db_session.add_all([class_group, student])
    db_session.commit()
    return organization, course_discipline, class_group, student


def _link_professor(
    db_session,
    professor,
    class_group,
    *,
    role=ProfessorRole.RESPONSIBLE,
    starts_at=None,
    ends_at=None,
):
    link = ProfessorClassLink(
        professor_id=professor.id,
        class_group_id=class_group.id,
        role=role,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db_session.add(link)
    db_session.commit()
    return link


def test_active_professor_can_list_and_create_resources_in_own_class(
    client, db_session, professor_token
):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, student = _academic_context(db_session)
    _link_professor(db_session, professor, class_group)
    headers = _headers(professor_token)

    response = client.get("/v1/class-groups", headers=headers)
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [class_group.id]

    response = client.post(
        "/v1/enrollments",
        headers=headers,
        json={"class_group_id": class_group.id, "student_id": student.id},
    )
    assert response.status_code == 201, response.text
    assert response.json()["class_group_id"] == class_group.id

    response = client.post(
        "/v1/assessments",
        headers=headers,
        json={
            "title": "Authorized assessment",
            "class_group_id": class_group.id,
            "question": {
                "statement": "Questão de autorização",
                "reference_answer": "Resposta esperada",
                "max_score": 10,
            },
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["class_group_id"] == class_group.id


def test_professor_without_link_cannot_discover_or_use_another_class(client, db_session, professor_token):
    _, _, class_group, student = _academic_context(db_session)
    headers = _headers(professor_token)

    response = client.get(f"/v1/class-groups/{class_group.id}", headers=headers)
    assert response.status_code == 404, response.text

    response = client.post(
        "/v1/enrollments",
        headers=headers,
        json={"class_group_id": class_group.id, "student_id": student.id},
    )
    assert response.status_code == 404, response.text


def test_collaborator_cannot_create_enrollment(client, db_session, professor_token):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, student = _academic_context(db_session)
    _link_professor(db_session, professor, class_group, role=ProfessorRole.COLLABORATOR)

    headers = _headers(professor_token)
    existing_student = client.post(
        "/v1/enrollments",
        headers=headers,
        json={"class_group_id": class_group.id, "student_id": student.id},
    )
    missing_student = client.post(
        "/v1/enrollments",
        headers=headers,
        json={"class_group_id": class_group.id, "student_id": "missing-student"},
    )

    assert existing_student.status_code == missing_student.status_code == 403
    assert existing_student.json() == missing_student.json()


def test_professor_link_scope_hides_other_professor_link_and_admin_keeps_global_access(
    client, db_session, professor_token, second_professor_token, admin_token
):
    second_professor = _user(db_session, "second.professor@example.com")
    _, _, class_group, _ = _academic_context(db_session)
    other_link = _link_professor(db_session, second_professor, class_group)

    out_of_scope = client.get(
        f"/v1/professor-class-links/{other_link.id}", headers=_headers(professor_token)
    )
    missing = client.get(
        "/v1/professor-class-links/missing-link", headers=_headers(professor_token)
    )
    own = client.get(
        f"/v1/professor-class-links/{other_link.id}", headers=_headers(second_professor_token)
    )
    admin = client.get(
        f"/v1/professor-class-links/{other_link.id}", headers=_headers(admin_token)
    )

    assert out_of_scope.status_code == missing.status_code == 404
    assert out_of_scope.json() == missing.json()
    assert own.status_code == 200, own.text
    assert admin.status_code == 200, admin.text


@pytest.mark.parametrize(
    ("academic_module_enabled", "expected_status"),
    [(False, 201), (True, 422)],
)
def test_academic_module_flag_controls_creation_of_legacy_assessment_without_class(
    client, professor_token, monkeypatch, academic_module_enabled, expected_status
):
    monkeypatch.setattr(main_module.settings, "academic_module_enabled", academic_module_enabled)

    response = client.post(
        "/v1/assessments",
        headers=_headers(professor_token),
        json={
            "title": f"Legacy flag {academic_module_enabled}",
            "question": {
                "statement": "Questão legada",
                "reference_answer": "Resposta esperada",
                "max_score": 10,
            },
        },
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.parametrize("academic_module_enabled", [False, True])
def test_linked_assessment_creation_is_allowed_with_flag_on_or_off(
    client, db_session, professor_token, monkeypatch, academic_module_enabled
):
    monkeypatch.setattr(main_module.settings, "academic_module_enabled", academic_module_enabled)
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session, f"flag-{academic_module_enabled}")
    _link_professor(db_session, professor, class_group)

    response = client.post(
        "/v1/assessments",
        headers=_headers(professor_token),
        json={
            "title": "Linked assessment",
            "class_group_id": class_group.id,
            "question": {
                "statement": "Questão vinculada",
                "reference_answer": "Resposta esperada",
                "max_score": 10,
            },
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["class_group_id"] == class_group.id


@pytest.mark.parametrize("academic_module_enabled", [False, True])
def test_linked_assessment_mutation_requires_active_link_regardless_of_flag(
    client, db_session, professor_token, monkeypatch, academic_module_enabled
):
    monkeypatch.setattr(main_module.settings, "academic_module_enabled", academic_module_enabled)
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session, f"mutation-{academic_module_enabled}")
    assessment = Assessment(
        title="Already linked",
        owner_id=professor.id,
        class_group_id=class_group.id,
    )
    db_session.add(assessment)
    db_session.commit()

    response = client.patch(
        f"/v1/assessments/{assessment.id}",
        headers=_headers(professor_token),
        json={"title": "Forbidden without active link"},
    )

    assert response.status_code == 403, response.text


def test_academic_routes_require_authentication(client):
    assert client.get("/v1/class-groups").status_code == 401
    assert client.post("/v1/enrollments", json={}).status_code == 401


def test_out_of_scope_and_missing_resources_have_identical_status(
    client, db_session, professor_token
):
    _, _, class_group, student = _academic_context(db_session)
    enrollment = Enrollment(class_group_id=class_group.id, student_id=student.id)
    db_session.add(enrollment)
    db_session.commit()
    headers = _headers(professor_token)

    class_out_of_scope = client.get(f"/v1/class-groups/{class_group.id}", headers=headers)
    class_missing = client.get("/v1/class-groups/missing-class", headers=headers)
    enrollment_out_of_scope = client.get(f"/v1/enrollments/{enrollment.id}", headers=headers)
    enrollment_missing = client.get("/v1/enrollments/missing-enrollment", headers=headers)

    assert class_out_of_scope.status_code == class_missing.status_code == 404
    assert enrollment_out_of_scope.status_code == enrollment_missing.status_code == 404


def test_expired_link_does_not_authorize_new_operations(client, db_session, professor_token):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session)
    _link_professor(
        db_session,
        professor,
        class_group,
        ends_at=datetime.utcnow() - timedelta(minutes=1),
    )

    response = client.post(
        "/v1/assessments",
        headers=_headers(professor_token),
        json={
            "title": "Too late",
            "class_group_id": class_group.id,
            "question": {
                "statement": "Questão fora da vigência",
                "reference_answer": "Resposta esperada",
                "max_score": 10,
            },
        },
    )
    assert response.status_code == 403, response.text


def test_future_link_does_not_authorize_access_yet(client, db_session, professor_token):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session)
    _link_professor(
        db_session,
        professor,
        class_group,
        starts_at=datetime.utcnow() + timedelta(days=1),
    )

    response = client.get(f"/v1/class-groups/{class_group.id}", headers=_headers(professor_token))
    assert response.status_code == 404, response.text


def test_admin_has_global_access_across_organizations_and_classes(client, db_session, admin_token):
    first_organization, _, first_class, _ = _academic_context(db_session, "first")
    second_organization, _, second_class, _ = _academic_context(db_session, "second")
    headers = _headers(admin_token)

    organizations = client.get("/v1/organizations", headers=headers)
    assert organizations.status_code == 200, organizations.text
    assert {item["id"] for item in organizations.json()} == {
        first_organization.id,
        second_organization.id,
    }

    classes = client.get("/v1/class-groups", headers=headers)
    assert classes.status_code == 200, classes.text
    assert {item["id"] for item in classes.json()} == {first_class.id, second_class.id}

    for class_group in (first_class, second_class):
        response = client.get(f"/v1/class-groups/{class_group.id}", headers=headers)
        assert response.status_code == 200, response.text


def test_legacy_assessment_remains_accessible_to_owner_and_admin(
    client, db_session, professor_token, admin_token
):
    professor = _user(db_session, "professor@example.com")
    assessment = Assessment(title="Legacy assessment", owner_id=professor.id)
    db_session.add(assessment)
    db_session.commit()

    owner_response = client.get(
        f"/v1/assessments/{assessment.id}", headers=_headers(professor_token)
    )
    assert owner_response.status_code == 200, owner_response.text
    assert owner_response.json()["class_group_id"] is None

    admin_response = client.get(f"/v1/assessments/{assessment.id}", headers=_headers(admin_token))
    assert admin_response.status_code == 200, admin_response.text
    assert admin_response.json()["id"] == assessment.id


def test_expired_professor_can_read_but_not_edit_or_republish_linked_assessment(
    client, db_session, professor_token
):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session)
    _link_professor(
        db_session,
        professor,
        class_group,
        ends_at=datetime.utcnow() - timedelta(minutes=1),
    )
    assessment = Assessment(
        title="Previously linked assessment",
        owner_id=professor.id,
        class_group_id=class_group.id,
    )
    db_session.add(assessment)
    db_session.commit()
    headers = _headers(professor_token)

    read_response = client.get(f"/v1/assessments/{assessment.id}", headers=headers)
    assert read_response.status_code == 200, read_response.text

    edit_response = client.patch(
        f"/v1/assessments/{assessment.id}",
        headers=headers,
        json={"title": "Forbidden edit"},
    )
    assert edit_response.status_code == 403, edit_response.text

    publish_response = client.post(f"/v1/assessments/{assessment.id}/publish", headers=headers)
    assert publish_response.status_code == 403, publish_response.text


def test_expired_professor_cannot_write_operational_class_flow(
    client, db_session, professor_token
):
    professor = _user(db_session, "professor@example.com")
    _, _, class_group, _ = _academic_context(db_session)
    _link_professor(
        db_session,
        professor,
        class_group,
        ends_at=datetime.utcnow() - timedelta(minutes=1),
    )
    assessment = Assessment(
        title="Expired operational flow",
        owner_id=professor.id,
        class_group_id=class_group.id,
    )
    db_session.add(assessment)
    db_session.flush()
    question = Question(
        assessment_id=assessment.id,
        statement="Question",
        reference_answer="Reference",
        max_score=1,
    )
    db_session.add(question)
    db_session.flush()
    answer = Answer(question_id=question.id, student_name_fake="Student", text="Answer")
    rubric = Rubric(question_id=question.id, version=1, is_published=True)
    db_session.add_all([answer, rubric])
    db_session.flush()
    job = CorrectionJob(
        answer_id=answer.id,
        rubric_id=rubric.id,
        status=JobStatus.SUGERIDA,
        attempt=1,
    )
    db_session.add(job)
    db_session.commit()
    headers = _headers(professor_token)

    create_answer = client.post(
        "/v1/answers",
        headers=headers,
        json={"question_id": question.id, "student_name_fake": "Other", "text": "Text"},
    )
    request_correction = client.post(f"/v1/answers/{answer.id}/corrections", headers=headers)
    review = client.post(
        f"/v1/corrections/{job.id}/reviews",
        headers=headers,
        json={"decision": "APPROVE", "criteria_scores": []},
    )

    assert create_answer.status_code == 403, create_answer.text
    assert request_correction.status_code == 403, request_correction.text
    assert review.status_code == 403, review.text


def test_expired_current_class_link_blocks_assessment_reassignment(
    client, db_session, professor_token
):
    professor = _user(db_session, "professor@example.com")
    _, _, current_class, _ = _academic_context(db_session, "current")
    _, _, new_class, _ = _academic_context(db_session, "new")
    _link_professor(
        db_session,
        professor,
        current_class,
        ends_at=datetime.utcnow() - timedelta(minutes=1),
    )
    _link_professor(db_session, professor, new_class)
    assessment = Assessment(
        title="Cannot reassign",
        owner_id=professor.id,
        class_group_id=current_class.id,
    )
    db_session.add(assessment)
    db_session.commit()

    response = client.post(
        f"/v1/assessments/{assessment.id}/class-group",
        headers=_headers(professor_token),
        json={"class_group_id": new_class.id},
    )

    assert response.status_code == 403, response.text


def test_duplicate_class_group_returns_integrity_conflict(client, db_session, admin_token):
    _, course_discipline, class_group, _ = _academic_context(db_session)
    payload = {
        "course_discipline_id": course_discipline.id,
        "period": class_group.period,
        "code": class_group.code,
    }

    response = client.post("/v1/class-groups", headers=_headers(admin_token), json=payload)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Conflito de integridade."
