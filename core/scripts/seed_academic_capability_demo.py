"""Seed demonstrativo idempotente da AV-S03B (BL-AV-S03B-03).

Cobre, com dados 100% fictícios, o cenário que a sprint precisa demonstrar:

1. estrutura acadêmica completa: organização → curso → disciplina →
   associação curso-disciplina → turma → vínculo professor↔turma (responsável);
2. avaliação ACADÊMICA vinculada à turma, PUBLICADA, com DUAS questões, cada
   uma com rubrica publicada e critério, e uma resposta fictícia por questão —
   ponto de partida pronto para correção e revisão humana via API;
3. avaliação LEGADA do MESMO professor, sem `class_group_id` (nullable),
   também com questão e resposta — prova de que o fluxo legado continua
   acessível mesmo com o módulo acadêmico ligado (AC-06 / `DEC-AV-023`).

USO (somente banco isolado NOVO desta sprint; recusa avalia_dev e
avalia_apresentacao_demo_20261002):

    DATABASE_URL=postgresql+psycopg2://localhost:5432/av_s03b_capacidades_local \
    ACADEMIC_MODULE_ENABLED=true \
    JWT_SECRET=isolated-demo-secret \
    PYTHONPATH=core core/.venv/bin/python core/scripts/seed_academic_capability_demo.py

Pré-requisito: `alembic upgrade head` aplicado ao banco isolado.

Este script é um ARQUIVO NOVO e não reaproveita nem altera
`seed_academic_multi_question_demo.py` (que permanece intocado, servindo a
AV-S04 com o prefixo "demo-av-s04" e a guarda "av_s02_saneamento_*"). Os dois
prefixos e as duas guardas de banco são disjuntos de propósito, para que os
seeds nunca colidam no mesmo banco.

Idempotência:
- usa IDs determinísticos exclusivos desta demo, prefixados com "demo-av-s03b";
- se todos os registros esperados já existem, valida conteúdo/links e imprime
  DEMO_SEED_ALREADY_VALID sem criar duplicatas;
- se encontra estado parcial ou conteúdo divergente em algum ID reservado,
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
    Answer,
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

PREFIX = "demo-av-s03b"

# Guarda de nome de banco desta sprint. Deliberadamente distinta da usada em
# seed_academic_multi_question_demo.py ("av_s02_saneamento_*"): bancos isolados
# já existentes de outras sprintes não devem ser alvo deste seed.
DATABASE_NAME_PATTERN = r"av_s03b_capacidades_[A-Za-z0-9_-]+"

DEMO_PROFESSOR_EMAIL = "demo.avs03b@avalia-platform.example"
DEMO_PROFESSOR_PASSWORD = "DemoAVS03B-Only-Isolated!"

IDS = {
    "user": f"{PREFIX}-user-professor",
    "organization": f"{PREFIX}-organization",
    "course": f"{PREFIX}-course",
    "discipline": f"{PREFIX}-discipline",
    "course_discipline": f"{PREFIX}-course-discipline",
    "class_group": f"{PREFIX}-class-group",
    "professor_link": f"{PREFIX}-professor-link",
    # Avaliação acadêmica (vinculada à turma), com múltiplas questões.
    "assessment": f"{PREFIX}-assessment-academic",
    "question_1": f"{PREFIX}-question-1",
    "question_2": f"{PREFIX}-question-2",
    "rubric_1": f"{PREFIX}-rubric-1",
    "rubric_2": f"{PREFIX}-rubric-2",
    "criterion_1": f"{PREFIX}-criterion-1",
    "criterion_2": f"{PREFIX}-criterion-2",
    "answer_1": f"{PREFIX}-answer-1",
    "answer_2": f"{PREFIX}-answer-2",
    # Avaliação legada (class_group_id nulo) do MESMO professor — AC-06.
    "legacy_assessment": f"{PREFIX}-assessment-legacy",
    "legacy_question": f"{PREFIX}-legacy-question-1",
    "legacy_rubric": f"{PREFIX}-legacy-rubric-1",
    "legacy_criterion": f"{PREFIX}-legacy-criterion-1",
    "legacy_answer": f"{PREFIX}-legacy-answer-1",
}

MODELS_BY_KEY = {
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
    "answer_1": Answer,
    "answer_2": Answer,
    "legacy_assessment": Assessment,
    "legacy_question": Question,
    "legacy_rubric": Rubric,
    "legacy_criterion": RubricCriterion,
    "legacy_answer": Answer,
}


def require_isolated_database(database_url: str) -> None:
    """Extract the actual database name from the URL and validate it with an
    anchored regex — never substring-match the raw URL, since credentials,
    host, or query-string fragments could spoof a substring check.

    Recusa explicitamente, por construção, qualquer nome que não case com o
    padrão desta sprint: em particular `avalia_dev` e
    `avalia_apresentacao_demo_20261002` nunca são aceitos.

    NOTA (bug corrigido em revisão, AV-S03B): a primeira versão desta guarda
    usava `urllib.parse.urlsplit()` e cortava o nome do banco no primeiro "/"
    (`path.lstrip("/").split("/", 1)[0]`). Isso DIVERGIA do parser que o
    SQLAlchemy realmente usa: em
    `postgresql+psycopg2://host:5432/av_s03b_capacidades_x/../avalia_dev` o
    recorte manual produzia `av_s03b_capacidades_x`, que casa com o padrão e
    passava na guarda, enquanto `create_engine()` recebia o restante do path
    como parte do nome do banco. A guarda precisa validar EXATAMENTE a string
    que o driver vai usar, por isso agora a extração é feita com
    `sqlalchemy.engine.make_url()` — o mesmo parser de `create_engine()` — e o
    valor extraído passa por uma rejeição explícita de separadores de caminho
    e de travessia antes do `fullmatch`.
    """
    import re

    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import ArgumentError

    try:
        url = make_url(database_url)
    except (ArgumentError, ValueError, AttributeError) as exc:
        raise RuntimeError(
            f"Refusing to seed: DATABASE_URL is not a parseable URL ({database_url!r})."
        ) from exc

    dbname = url.database or ""

    # Defesa em profundidade: mesmo que uma versão futura do parser passe a
    # devolver o nome com separadores, nada que contenha "/", "\\" ou ".."
    # pode ser aceito — o alvo real deixaria de ser o banco validado.
    if any(token in dbname for token in ("/", "\\", "..")):
        raise RuntimeError(
            "Refusing to seed: DATABASE_URL database name contains a path "
            f"separator or traversal segment ({dbname!r})."
        )

    if not re.fullmatch(DATABASE_NAME_PATTERN, dbname):
        raise RuntimeError(
            "Refusing to seed: DATABASE_URL database name must match "
            f"^{DATABASE_NAME_PATTERN}$ exactly (got {dbname!r}). This script "
            "never targets avalia_dev nor avalia_apresentacao_demo_20261002."
        )


def require_academic_flags() -> None:
    settings = get_settings()
    if not settings.academic_module_enabled:
        raise RuntimeError(
            "ACADEMIC_MODULE_ENABLED must be true for this demonstration. "
            "A partir da AV-S03B o frontend NÃO precisa mais de "
            "VITE_ACADEMIC_MODULE_ENABLED: ele lê a capacidade do backend em "
            "GET /v1/config/capabilities."
        )


def validate_existing(session: Session) -> bool:
    """Return True iff all reserved demo rows exist and match expected links."""
    rows = {key: session.get(model, IDS[key]) for key, model in MODELS_BY_KEY.items()}
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
        complete["user"].email == DEMO_PROFESSOR_EMAIL,
        complete["user"].role == Role.PROFESSOR,
        complete["user"].is_active is True,
        complete["organization"].name == "DEMO-AV-S03B Organização Fictícia",
        complete["course"].organization_id == IDS["organization"],
        complete["course"].name == "DEMO-AV-S03B Curso Fictício",
        complete["course"].code == "DEMO-AV-S03B-CURSO",
        complete["discipline"].organization_id == IDS["organization"],
        complete["discipline"].name == "DEMO-AV-S03B Disciplina Fictícia",
        complete["discipline"].code == "DEMO-AV-S03B-DISC",
        complete["course_discipline"].course_id == IDS["course"],
        complete["course_discipline"].discipline_id == IDS["discipline"],
        complete["class_group"].course_discipline_id == IDS["course_discipline"],
        complete["class_group"].period == "2026-DEMO",
        complete["class_group"].code == "DEMO-AV-S03B-TURMA",
        complete["professor_link"].professor_id == IDS["user"],
        complete["professor_link"].class_group_id == IDS["class_group"],
        complete["professor_link"].role == ProfessorRole.RESPONSIBLE,
        complete["professor_link"].active is True,
        # --- avaliação acadêmica (com turma) ---
        complete["assessment"].owner_id == IDS["user"],
        complete["assessment"].class_group_id == IDS["class_group"],
        complete["assessment"].title == "DEMO-AV-S03B Avaliação acadêmica (turma vinculada)",
        complete["assessment"].status == AssessmentStatus.PUBLICADA,
        complete["question_1"].assessment_id == IDS["assessment"],
        complete["question_1"].position == 1,
        complete["question_1"].statement
        == "DEMO-AV-S03B Questão 1: explique o conceito fictício A.",
        complete["question_1"].reference_answer == "DEMO-AV-S03B Referência fictícia A.",
        complete["question_1"].max_score == Decimal("4.00"),
        complete["question_2"].assessment_id == IDS["assessment"],
        complete["question_2"].position == 2,
        complete["question_2"].statement
        == "DEMO-AV-S03B Questão 2: compare os conceitos fictícios A e B.",
        complete["question_2"].reference_answer
        == "DEMO-AV-S03B Referência fictícia comparativa A/B.",
        complete["question_2"].max_score == Decimal("6.00"),
        complete["rubric_1"].question_id == IDS["question_1"],
        complete["rubric_1"].version == 1,
        complete["rubric_1"].is_published is True,
        complete["rubric_2"].question_id == IDS["question_2"],
        complete["rubric_2"].version == 1,
        complete["rubric_2"].is_published is True,
        complete["criterion_1"].rubric_id == IDS["rubric_1"],
        complete["criterion_1"].name == "DEMO-AV-S03B Critério fictício Q1",
        complete["criterion_1"].description == "Critério fictício, somente ambiente isolado.",
        complete["criterion_1"].max_score == Decimal("4.00"),
        complete["criterion_2"].rubric_id == IDS["rubric_2"],
        complete["criterion_2"].name == "DEMO-AV-S03B Critério fictício Q2",
        complete["criterion_2"].description == "Critério fictício, somente ambiente isolado.",
        complete["criterion_2"].max_score == Decimal("6.00"),
        complete["answer_1"].question_id == IDS["question_1"],
        complete["answer_1"].student_name_fake == "DEMO-AV-S03B Aluno Fictício 1",
        complete["answer_1"].text == "DEMO-AV-S03B Resposta fictícia para a questão 1.",
        complete["answer_2"].question_id == IDS["question_2"],
        complete["answer_2"].student_name_fake == "DEMO-AV-S03B Aluno Fictício 2",
        complete["answer_2"].text == "DEMO-AV-S03B Resposta fictícia para a questão 2.",
        # --- avaliação legada (sem turma), mesmo professor — AC-06 ---
        complete["legacy_assessment"].owner_id == IDS["user"],
        complete["legacy_assessment"].class_group_id is None,
        complete["legacy_assessment"].title == "DEMO-AV-S03B Avaliação legada (sem turma)",
        complete["legacy_assessment"].status == AssessmentStatus.RASCUNHO,
        complete["legacy_question"].assessment_id == IDS["legacy_assessment"],
        complete["legacy_question"].position == 1,
        complete["legacy_question"].statement
        == "DEMO-AV-S03B Questão legada 1: descreva o procedimento fictício L.",
        complete["legacy_question"].reference_answer
        == "DEMO-AV-S03B Referência fictícia legada L.",
        complete["legacy_question"].max_score == Decimal("5.00"),
        complete["legacy_rubric"].question_id == IDS["legacy_question"],
        complete["legacy_rubric"].version == 1,
        complete["legacy_rubric"].is_published is True,
        complete["legacy_criterion"].rubric_id == IDS["legacy_rubric"],
        complete["legacy_criterion"].name == "DEMO-AV-S03B Critério fictício legado",
        complete["legacy_criterion"].description == "Critério fictício, somente ambiente isolado.",
        complete["legacy_criterion"].max_score == Decimal("5.00"),
        complete["legacy_answer"].question_id == IDS["legacy_question"],
        complete["legacy_answer"].student_name_fake == "DEMO-AV-S03B Aluno Fictício Legado",
        complete["legacy_answer"].text == "DEMO-AV-S03B Resposta fictícia para a questão legada.",
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
            print(f"DEMO_ASSESSMENT_ID={IDS['assessment']}")
            print(f"DEMO_LEGACY_ASSESSMENT_ID={IDS['legacy_assessment']}")
            return

        user = User(
            id=IDS["user"],
            email=DEMO_PROFESSOR_EMAIL,
            password_hash=hash_password(DEMO_PROFESSOR_PASSWORD),
            role=Role.PROFESSOR,
            is_active=True,
        )
        organization = Organization(
            id=IDS["organization"], name="DEMO-AV-S03B Organização Fictícia"
        )
        course = Course(
            id=IDS["course"],
            organization_id=IDS["organization"],
            name="DEMO-AV-S03B Curso Fictício",
            code="DEMO-AV-S03B-CURSO",
        )
        discipline = Discipline(
            id=IDS["discipline"],
            organization_id=IDS["organization"],
            name="DEMO-AV-S03B Disciplina Fictícia",
            code="DEMO-AV-S03B-DISC",
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
            code="DEMO-AV-S03B-TURMA",
        )
        professor_link = ProfessorClassLink(
            id=IDS["professor_link"],
            professor_id=IDS["user"],
            class_group_id=IDS["class_group"],
            role=ProfessorRole.RESPONSIBLE,
            active=True,
        )

        # Avaliação acadêmica: publicada com rubricas publicadas, de modo que o
        # próximo passo do fluxo (POST /v1/answers/{id}/corrections) já seja
        # alcançável por HTTP sem nenhuma edição manual prévia.
        assessment = Assessment(
            id=IDS["assessment"],
            owner_id=IDS["user"],
            class_group_id=IDS["class_group"],
            title="DEMO-AV-S03B Avaliação acadêmica (turma vinculada)",
            status=AssessmentStatus.PUBLICADA,
        )
        question_1 = Question(
            id=IDS["question_1"],
            assessment_id=IDS["assessment"],
            statement="DEMO-AV-S03B Questão 1: explique o conceito fictício A.",
            reference_answer="DEMO-AV-S03B Referência fictícia A.",
            max_score=Decimal("4.00"),
            position=1,
        )
        question_2 = Question(
            id=IDS["question_2"],
            assessment_id=IDS["assessment"],
            statement="DEMO-AV-S03B Questão 2: compare os conceitos fictícios A e B.",
            reference_answer="DEMO-AV-S03B Referência fictícia comparativa A/B.",
            max_score=Decimal("6.00"),
            position=2,
        )
        rubric_1 = Rubric(
            id=IDS["rubric_1"], question_id=IDS["question_1"], version=1, is_published=True
        )
        rubric_2 = Rubric(
            id=IDS["rubric_2"], question_id=IDS["question_2"], version=1, is_published=True
        )
        criterion_1 = RubricCriterion(
            id=IDS["criterion_1"],
            rubric_id=IDS["rubric_1"],
            name="DEMO-AV-S03B Critério fictício Q1",
            description="Critério fictício, somente ambiente isolado.",
            max_score=Decimal("4.00"),
        )
        criterion_2 = RubricCriterion(
            id=IDS["criterion_2"],
            rubric_id=IDS["rubric_2"],
            name="DEMO-AV-S03B Critério fictício Q2",
            description="Critério fictício, somente ambiente isolado.",
            max_score=Decimal("6.00"),
        )
        answer_1 = Answer(
            id=IDS["answer_1"],
            question_id=IDS["question_1"],
            student_name_fake="DEMO-AV-S03B Aluno Fictício 1",
            text="DEMO-AV-S03B Resposta fictícia para a questão 1.",
        )
        answer_2 = Answer(
            id=IDS["answer_2"],
            question_id=IDS["question_2"],
            student_name_fake="DEMO-AV-S03B Aluno Fictício 2",
            text="DEMO-AV-S03B Resposta fictícia para a questão 2.",
        )

        # Avaliação LEGADA do mesmo professor: class_group_id nulo (AC-06).
        # Mantida em RASCUNHO justamente para provar que o proprietário continua
        # podendo EDITAR uma avaliação sem turma com o módulo acadêmico ligado —
        # a exigência de turma vale apenas para a CRIAÇÃO de novas avaliações
        # (DEC-AV-023), não para o histórico.
        legacy_assessment = Assessment(
            id=IDS["legacy_assessment"],
            owner_id=IDS["user"],
            class_group_id=None,
            title="DEMO-AV-S03B Avaliação legada (sem turma)",
            status=AssessmentStatus.RASCUNHO,
        )
        legacy_question = Question(
            id=IDS["legacy_question"],
            assessment_id=IDS["legacy_assessment"],
            statement="DEMO-AV-S03B Questão legada 1: descreva o procedimento fictício L.",
            reference_answer="DEMO-AV-S03B Referência fictícia legada L.",
            max_score=Decimal("5.00"),
            position=1,
        )
        legacy_rubric = Rubric(
            id=IDS["legacy_rubric"],
            question_id=IDS["legacy_question"],
            version=1,
            is_published=True,
        )
        legacy_criterion = RubricCriterion(
            id=IDS["legacy_criterion"],
            rubric_id=IDS["legacy_rubric"],
            name="DEMO-AV-S03B Critério fictício legado",
            description="Critério fictício, somente ambiente isolado.",
            max_score=Decimal("5.00"),
        )
        legacy_answer = Answer(
            id=IDS["legacy_answer"],
            question_id=IDS["legacy_question"],
            student_name_fake="DEMO-AV-S03B Aluno Fictício Legado",
            text="DEMO-AV-S03B Resposta fictícia para a questão legada.",
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
        session.add_all([professor_link, assessment, legacy_assessment])
        session.flush()
        session.add_all([question_1, question_2, legacy_question])
        session.flush()
        session.add_all([rubric_1, rubric_2, legacy_rubric])
        session.flush()
        session.add_all([criterion_1, criterion_2, legacy_criterion])
        session.add_all([answer_1, answer_2, legacy_answer])
        session.commit()

        # Final read-back assertions from the committed state.
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

        answers = session.scalars(
            select(Answer).where(
                Answer.question_id.in_(
                    [IDS["question_1"], IDS["question_2"], IDS["legacy_question"]]
                )
            )
        ).all()
        if len(answers) != 3:
            raise RuntimeError("Committed demo seed must have exactly one answer per question")

        legacy = session.get(Assessment, IDS["legacy_assessment"])
        if legacy is None or legacy.class_group_id is not None:
            raise RuntimeError("Legacy demo assessment must persist with class_group_id = NULL")

        print("DEMO_SEED_CREATED_AND_VALID")
        print(f"DEMO_PROFESSOR_EMAIL={DEMO_PROFESSOR_EMAIL}")
        print(f"DEMO_ASSESSMENT_ID={IDS['assessment']}")
        print(f"DEMO_LEGACY_ASSESSMENT_ID={IDS['legacy_assessment']}")
        print(f"DEMO_CLASS_GROUP_ID={IDS['class_group']}")
        print("DEMO_ACADEMIC_FLAGS_REQUIRED=ACADEMIC_MODULE_ENABLED=true")


if __name__ == "__main__":
    run()
