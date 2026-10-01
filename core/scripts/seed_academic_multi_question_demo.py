"""Seed demonstrativo idempotente: estrutura acadêmica + múltiplas questões.

USO (somente banco isolado restaurado/teste; recusa avalia_dev):

    DATABASE_URL=postgresql+psycopg2://localhost:5432/av_s02_saneamento_<nome> \
    ACADEMIC_MODULE_ENABLED=true \
    JWT_SECRET=isolated-demo-secret \
    PYTHONPATH=core core/.venv/bin/python core/scripts/seed_academic_multi_question_demo.py

Pré-requisito: alembic upgrade head aplicado ao banco isolado.
Não copia dados reais para evidências públicas: todos os IDs, códigos, nomes,
enunciados e emails criados por este script são explicitamente fictícios e
prefixados com "DEMO-AV-S04" / "demo.avs04".

Idempotência:
- usa IDs determinísticos exclusivos da demo;
- se todos os registros esperados já existem, valida conteúdo/links e imprime
  DEMO_SEED_ALREADY_VALID sem criar duplicatas;
- se encontra estado parcial ou conteúdo divergente com algum ID reservado,
  aborta sem tentar "consertar" automaticamente (não mascara drift).
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    Assessment,
    AssessmentStatus,
    ClassGroup,
    Course,
    CourseDiscipline,
    Discipline,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Question,
    Role,
    Rubric,
    RubricCriterion,
    User,
)
from app.security import hash_password

PREFIX = "demo-av-s04"
IDS = {
    "user": f"{PREFIX}-user-professor",
    "organization": f"{PREFIX}-organization",
    "course": f"{PREFIX}-course",
    "discipline": f"{PREFIX}-discipline",
    "course_discipline": f"{PREFIX}-course-discipline",
    "class_group": f"{PREFIX}-class-group",
    "professor_link": f"{PREFIX}-professor-link",
    "assessment": f"{PREFIX}-assessment-multiple-questions",
    "question_1": f"{PREFIX}-question-1",
    "question_2": f"{PREFIX}-question-2",
    "rubric_1": f"{PREFIX}-rubric-1",
    "rubric_2": f"{PREFIX}-rubric-2",
    "criterion_1": f"{PREFIX}-criterion-1",
    "criterion_2": f"{PREFIX}-criterion-2",
}


def require_isolated_database(database_url: str) -> None:
    """Extract the actual database name from the URL and validate it with an
    anchored regex — never substring-match the raw URL, since credentials,
    host, or query-string fragments could spoof a substring check."""
    import re
    from urllib.parse import urlsplit

    parsed = urlsplit(database_url)
    dbname = (parsed.path or "").lstrip("/")
    if "/" in dbname:
        dbname = dbname.split("/", 1)[0]
    if not re.fullmatch(r"av_s02_saneamento_[A-Za-z0-9_-]+", dbname):
        raise RuntimeError(
            "Refusing to seed: DATABASE_URL database name must match "
            "^av_s02_saneamento_[A-Za-z0-9_-]+$ exactly (got "
            f"{dbname!r}). This script never targets avalia_dev."
        )


def require_academic_flags() -> None:
    settings = get_settings()
    if not settings.academic_module_enabled:
        raise RuntimeError(
            "ACADEMIC_MODULE_ENABLED must be true for this demonstration. "
            "Frontend must also be started/built with "
            "VITE_ACADEMIC_MODULE_ENABLED=true."
        )


def validate_existing(session: Session) -> bool:
    """Return True iff all reserved demo rows exist and match expected links."""
    rows = {
        key: session.get(model, IDS[key])
        for key, model in {
            "user": User,
            "organization": Organization,
            "course": Course,
            "discipline": Discipline,
            "course_discipline": CourseDiscipline,
            "class_group": ClassGroup,
            "professor_link": ProfessorClassLink,
            "assessment": Assessment,
            "question_1": Question,
            "question_2": Question,
            "rubric_1": Rubric,
            "rubric_2": Rubric,
            "criterion_1": RubricCriterion,
            "criterion_2": RubricCriterion,
        }.items()
    }
    present = [key for key, value in rows.items() if value is not None]
    if not present:
        return False
    if len(present) != len(rows):
        missing = sorted(set(rows) - set(present))
        raise RuntimeError(
            f"Partial demo seed detected; present={sorted(present)}, missing={missing}. "
            "Abort without automatic repair."
        )

    # All values are proven non-None by the completeness check above. Cast
    # once so static analyzers do not lose that invariant across dict keys.
    complete = cast(dict[str, Any], rows)

    expected = [
        complete["user"].email == "demo.avs04@avalia-platform.example",
        complete["user"].role == Role.PROFESSOR,
        complete["user"].is_active is True,
        complete["organization"].name == "DEMO-AV-S04 Organização Fictícia",
        complete["course"].organization_id == IDS["organization"],
        complete["course"].name == "DEMO-AV-S04 Curso Fictício",
        complete["course"].code == "DEMO-AV-S04-CURSO",
        complete["discipline"].organization_id == IDS["organization"],
        complete["discipline"].name == "DEMO-AV-S04 Disciplina Fictícia",
        complete["discipline"].code == "DEMO-AV-S04-DISC",
        complete["course_discipline"].course_id == IDS["course"],
        complete["course_discipline"].discipline_id == IDS["discipline"],
        complete["class_group"].course_discipline_id == IDS["course_discipline"],
        complete["class_group"].period == "2026-DEMO",
        complete["class_group"].code == "DEMO-AV-S04-TURMA",
        complete["professor_link"].professor_id == IDS["user"],
        complete["professor_link"].class_group_id == IDS["class_group"],
        complete["professor_link"].role == ProfessorRole.RESPONSIBLE,
        complete["professor_link"].active is True,
        complete["assessment"].owner_id == IDS["user"],
        complete["assessment"].class_group_id == IDS["class_group"],
        complete["assessment"].title == "DEMO-AV-S04 Avaliação com múltiplas questões",
        complete["assessment"].status == AssessmentStatus.RASCUNHO,
        complete["question_1"].assessment_id == IDS["assessment"],
        complete["question_1"].position == 1,
        complete["question_1"].statement
        == "DEMO-AV-S04 Questão 1: explique o conceito fictício A.",
        complete["question_1"].reference_answer == "DEMO-AV-S04 Referência fictícia A.",
        complete["question_1"].max_score == Decimal("4.00"),
        complete["question_2"].assessment_id == IDS["assessment"],
        complete["question_2"].position == 2,
        complete["question_2"].statement
        == "DEMO-AV-S04 Questão 2: compare os conceitos fictícios A e B.",
        complete["question_2"].reference_answer
        == "DEMO-AV-S04 Referência fictícia comparativa A/B.",
        complete["question_2"].max_score == Decimal("6.00"),
        complete["rubric_1"].question_id == IDS["question_1"],
        complete["rubric_1"].version == 1,
        complete["rubric_1"].is_published is False,
        complete["rubric_2"].question_id == IDS["question_2"],
        complete["rubric_2"].version == 1,
        complete["rubric_2"].is_published is False,
        complete["criterion_1"].rubric_id == IDS["rubric_1"],
        complete["criterion_1"].name == "DEMO-AV-S04 Critério fictício Q1",
        complete["criterion_1"].description == "Critério fictício, somente ambiente isolado.",
        complete["criterion_1"].max_score == Decimal("4.00"),
        complete["criterion_2"].rubric_id == IDS["rubric_2"],
        complete["criterion_2"].name == "DEMO-AV-S04 Critério fictício Q2",
        complete["criterion_2"].description == "Critério fictício, somente ambiente isolado.",
        complete["criterion_2"].max_score == Decimal("6.00"),
    ]
    if not all(expected):
        raise RuntimeError("Existing demo seed uses reserved IDs with divergent content; aborting")
    return True


def run() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    require_isolated_database(database_url)
    require_academic_flags()

    engine = create_engine(database_url, future=True)
    with Session(engine, future=True) as session:
        if validate_existing(session):
            print("DEMO_SEED_ALREADY_VALID")
            return

        user = User(
            id=IDS["user"],
            email="demo.avs04@avalia-platform.example",
            password_hash=hash_password("DemoAVS04-Only-Isolated!"),
            role=Role.PROFESSOR,
            is_active=True,
        )
        organization = Organization(id=IDS["organization"], name="DEMO-AV-S04 Organização Fictícia")
        course = Course(
            id=IDS["course"],
            organization_id=IDS["organization"],
            name="DEMO-AV-S04 Curso Fictício",
            code="DEMO-AV-S04-CURSO",
        )
        discipline = Discipline(
            id=IDS["discipline"],
            organization_id=IDS["organization"],
            name="DEMO-AV-S04 Disciplina Fictícia",
            code="DEMO-AV-S04-DISC",
        )
        course_discipline = CourseDiscipline(
            id=IDS["course_discipline"],
            course_id=IDS["course"],
            discipline_id=IDS["discipline"],
        )
        class_group = ClassGroup(
            id=IDS["class_group"],
            course_discipline_id=IDS["course_discipline"],
            period="2026-DEMO",
            code="DEMO-AV-S04-TURMA",
        )
        professor_link = ProfessorClassLink(
            id=IDS["professor_link"],
            professor_id=IDS["user"],
            class_group_id=IDS["class_group"],
            role=ProfessorRole.RESPONSIBLE,
            active=True,
        )
        assessment = Assessment(
            id=IDS["assessment"],
            owner_id=IDS["user"],
            class_group_id=IDS["class_group"],
            title="DEMO-AV-S04 Avaliação com múltiplas questões",
            status=AssessmentStatus.RASCUNHO,
        )
        question_1 = Question(
            id=IDS["question_1"],
            assessment_id=IDS["assessment"],
            statement="DEMO-AV-S04 Questão 1: explique o conceito fictício A.",
            reference_answer="DEMO-AV-S04 Referência fictícia A.",
            max_score=Decimal("4.00"),
            position=1,
        )
        question_2 = Question(
            id=IDS["question_2"],
            assessment_id=IDS["assessment"],
            statement="DEMO-AV-S04 Questão 2: compare os conceitos fictícios A e B.",
            reference_answer="DEMO-AV-S04 Referência fictícia comparativa A/B.",
            max_score=Decimal("6.00"),
            position=2,
        )
        rubric_1 = Rubric(
            id=IDS["rubric_1"], question_id=IDS["question_1"], version=1, is_published=False
        )
        rubric_2 = Rubric(
            id=IDS["rubric_2"], question_id=IDS["question_2"], version=1, is_published=False
        )
        criterion_1 = RubricCriterion(
            id=IDS["criterion_1"],
            rubric_id=IDS["rubric_1"],
            name="DEMO-AV-S04 Critério fictício Q1",
            description="Critério fictício, somente ambiente isolado.",
            max_score=Decimal("4.00"),
        )
        criterion_2 = RubricCriterion(
            id=IDS["criterion_2"],
            rubric_id=IDS["rubric_2"],
            name="DEMO-AV-S04 Critério fictício Q2",
            description="Critério fictício, somente ambiente isolado.",
            max_score=Decimal("6.00"),
        )

        # Persist in explicit FK dependency layers. Most academic models do
        # not declare ORM relationships, so SQLAlchemy's unit-of-work cannot
        # infer ordering from Python object references when only raw *_id
        # values are assigned. Explicit flushes make the seed deterministic.
        session.add_all([user, organization])
        session.flush()
        session.add_all([course, discipline])
        session.flush()
        session.add(course_discipline)
        session.flush()
        session.add(class_group)
        session.flush()
        session.add_all([professor_link, assessment])
        session.flush()
        session.add_all([question_1, question_2])
        session.flush()
        session.add_all([rubric_1, rubric_2])
        session.flush()
        session.add_all([criterion_1, criterion_2])
        session.commit()

        # Final read-back assertion from the committed state.
        questions = session.scalars(
            select(Question)
            .where(Question.assessment_id == IDS["assessment"])
            .order_by(Question.position)
        ).all()
        if [(item.id, item.position) for item in questions] != [
            (IDS["question_1"], 1),
            (IDS["question_2"], 2),
        ]:
            raise RuntimeError("Committed demo assessment questions are not exactly ordered 1,2")
        print("DEMO_SEED_CREATED_AND_VALID")
        print(f"DEMO_ASSESSMENT_ID={IDS['assessment']}")
        print("DEMO_ACADEMIC_FLAGS_REQUIRED=ACADEMIC_MODULE_ENABLED=true,VITE_ACADEMIC_MODULE_ENABLED=true")


if __name__ == "__main__":
    run()
