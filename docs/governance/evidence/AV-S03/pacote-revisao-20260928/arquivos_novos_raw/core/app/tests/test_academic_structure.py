from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Assessment,
    ClassGroup,
    Course,
    CourseDiscipline,
    Discipline,
    Enrollment,
    EnrollmentStatus,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Role,
    Student,
    User,
)


def _base_hierarchy(db_session):
    organization = Organization(name="Instituição Fictícia")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name="Engenharia", code="ENG")
    discipline = Discipline(organization_id=organization.id, name="Cálculo", code="CALC")
    db_session.add_all([course, discipline])
    db_session.flush()
    association = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(association)
    db_session.flush()
    class_group = ClassGroup(
        course_discipline_id=association.id, period="2026-2", code="T01"
    )
    student = Student(
        organization_id=organization.id, name="Aluno Fictício", external_id="STU-001"
    )
    professor = User(
        email="academic.professor@example.com",
        password_hash="not-a-real-password",
        role=Role.PROFESSOR,
    )
    db_session.add_all([class_group, student, professor])
    db_session.flush()
    return organization, course, discipline, association, class_group, student, professor


def test_complete_academic_hierarchy(db_session):
    *_, class_group, student, professor = _base_hierarchy(db_session)
    enrollment = Enrollment(class_group_id=class_group.id, student_id=student.id)
    link = ProfessorClassLink(
        professor_id=professor.id,
        class_group_id=class_group.id,
        role=ProfessorRole.RESPONSIBLE,
    )
    db_session.add_all([enrollment, link])
    db_session.commit()

    assert enrollment.status is EnrollmentStatus.ACTIVE
    assert enrollment.enrolled_at is not None
    assert link.active is True
    assert db_session.get(ProfessorClassLink, link.id) is link


def test_duplicate_class_group_identity_is_rejected(db_session):
    *_, association, class_group, _, _ = _base_hierarchy(db_session)
    db_session.add(
        ClassGroup(
            course_discipline_id=association.id,
            period=class_group.period,
            code=class_group.code,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_student_can_be_active_in_more_than_one_class_group(db_session):
    *_, association, first_group, student, _ = _base_hierarchy(db_session)
    second_group = ClassGroup(
        course_discipline_id=association.id, period="2026-2", code="T02"
    )
    db_session.add(second_group)
    db_session.flush()
    db_session.add_all(
        [
            Enrollment(class_group_id=first_group.id, student_id=student.id),
            Enrollment(class_group_id=second_group.id, student_id=student.id),
        ]
    )
    db_session.commit()

    enrollments = db_session.query(Enrollment).filter_by(student_id=student.id).all()
    assert len(enrollments) == 2
    assert {item.class_group_id for item in enrollments} == {first_group.id, second_group.id}


def test_discipline_can_belong_to_more_than_one_course(db_session):
    organization, _, discipline, _, _, _, _ = _base_hierarchy(db_session)
    second_course = Course(organization_id=organization.id, name="Computação", code="COMP")
    db_session.add(second_course)
    db_session.flush()
    db_session.add(CourseDiscipline(course_id=second_course.id, discipline_id=discipline.id))
    db_session.commit()

    associations = db_session.query(CourseDiscipline).filter_by(discipline_id=discipline.id).all()
    assert len(associations) == 2


def test_expired_professor_link_is_persisted(db_session):
    *_, class_group, _, professor = _base_hierarchy(db_session)
    expired_at = datetime.utcnow() - timedelta(days=1)
    link = ProfessorClassLink(
        professor_id=professor.id,
        class_group_id=class_group.id,
        role=ProfessorRole.COLLABORATOR,
        ends_at=expired_at,
    )
    db_session.add(link)
    db_session.commit()
    db_session.expire_all()

    persisted = db_session.get(ProfessorClassLink, link.id)
    assert persisted is not None
    assert persisted.ends_at == expired_at


def test_legacy_assessment_without_class_group_remains_valid(db_session):
    professor = User(
        email="legacy.owner@example.com",
        password_hash="not-a-real-password",
        role=Role.PROFESSOR,
    )
    db_session.add(professor)
    db_session.flush()
    assessment = Assessment(title="Avaliação legada", owner_id=professor.id)
    db_session.add(assessment)
    db_session.commit()

    assert assessment.class_group_id is None
