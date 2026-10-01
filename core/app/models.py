from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    PROFESSOR = "professor"
    ADMIN = "admin"


class AssessmentStatus(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    PUBLICADA = "PUBLICADA"


class JobStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    SUGERIDA = "SUGERIDA"
    FALHA = "FALHA"


class ReviewDecision(str, enum.Enum):
    APPROVE = "APPROVE"
    ALTER = "ALTER"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    COMPLETED = "COMPLETED"


class ProfessorRole(str, enum.Enum):
    RESPONSIBLE = "responsible"
    COLLABORATOR = "collaborator"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.PROFESSOR, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    # Nullable preserves legacy assessments. Creation-time enforcement belongs to
    # BL-AV-2-03 and is activated through Settings.academic_module_enabled.
    class_group_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("class_groups.id"), nullable=True
    )
    cloned_from_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("assessments.id"), nullable=True
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus), default=AssessmentStatus.RASCUNHO, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="assessment", order_by="Question.position"
    )


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_courses_organization_code"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    organization_id: Mapped[str] = mapped_column(
        String, ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)


class Discipline(Base):
    __tablename__ = "disciplines"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_disciplines_organization_code"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    organization_id: Mapped[str] = mapped_column(
        String, ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)


class CourseDiscipline(Base):
    __tablename__ = "course_disciplines"
    __table_args__ = (
        UniqueConstraint("course_id", "discipline_id", name="uq_course_disciplines_pair"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    course_id: Mapped[str] = mapped_column(String, ForeignKey("courses.id"), nullable=False)
    discipline_id: Mapped[str] = mapped_column(
        String, ForeignKey("disciplines.id"), nullable=False
    )


class ClassGroup(Base):
    __tablename__ = "class_groups"
    __table_args__ = (
        UniqueConstraint(
            "course_discipline_id",
            "period",
            "code",
            name="uq_class_groups_curriculum_period_code",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    course_discipline_id: Mapped[str] = mapped_column(
        String, ForeignKey("course_disciplines.id"), nullable=False
    )
    period: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_students_organization_external"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    organization_id: Mapped[str] = mapped_column(
        String, ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str] = mapped_column(String, nullable=False)


class Enrollment(Base):
    __tablename__ = "enrollments"
    # Deliberately no unique constraint on (class_group_id, student_id):
    # historical reenrollment is valid. BL-AV-2-03 prevents simultaneous ACTIVE rows.
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    class_group_id: Mapped[str] = mapped_column(
        String, ForeignKey("class_groups.id"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(String, ForeignKey("students.id"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProfessorClassLink(Base):
    __tablename__ = "professor_class_links"
    __table_args__ = (
        UniqueConstraint(
            "professor_id", "class_group_id", "role", name="uq_professor_class_links_role"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    professor_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    class_group_id: Mapped[str] = mapped_column(
        String, ForeignKey("class_groups.id"), nullable=False
    )
    role: Mapped[ProfessorRole] = mapped_column(
        Enum(ProfessorRole, values_callable=lambda enum_type: [item.value for item in enum_type]),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("assessment_id", "position", name="uq_questions_assessment_position"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    assessment_id: Mapped[str] = mapped_column(String, ForeignKey("assessments.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str] = mapped_column(Text, nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="questions")
    rubrics: Mapped[list["Rubric"]] = relationship(
        back_populates="question",
        order_by="Rubric.version.desc()",
        cascade="all, delete-orphan",
    )


class Rubric(Base):
    __tablename__ = "rubrics"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    question_id: Mapped[str] = mapped_column(String, ForeignKey("questions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question: Mapped["Question"] = relationship(back_populates="rubrics")
    criteria: Mapped[list["RubricCriterion"]] = relationship(
        back_populates="rubric", cascade="all, delete-orphan"
    )


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    rubric_id: Mapped[str] = mapped_column(String, ForeignKey("rubrics.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    rubric: Mapped["Rubric"] = relationship(back_populates="criteria")


class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    question_id: Mapped[str] = mapped_column(String, ForeignKey("questions.id"), nullable=False)
    student_name_fake: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CorrectionJob(Base):
    __tablename__ = "correction_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    answer_id: Mapped[str] = mapped_column(String, ForeignKey("answers.id"), nullable=False)
    rubric_id: Mapped[str] = mapped_column(String, ForeignKey("rubrics.id"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDENTE, nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AIExecution(Base):
    __tablename__ = "ai_executions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("correction_jobs.id"), nullable=False)
    engine_mode: Mapped[str] = mapped_column(String, nullable=False)  # real | simulated
    model: Mapped[str] = mapped_column(String, default="")
    confidence_method_version: Mapped[str] = mapped_column(String, default="")
    overall_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    review_recommendation: Mapped[str] = mapped_column(String, default="REVIEW_REQUIRED")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    flags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list serializado
    raw_output_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criterion_scores: Mapped[list["CriterionScore"]] = relationship(back_populates="ai_execution")


class CriterionScore(Base):
    __tablename__ = "criterion_scores"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    ai_execution_id: Mapped[str] = mapped_column(String, ForeignKey("ai_executions.id"), nullable=False)
    criterion_id: Mapped[str] = mapped_column(String, ForeignKey("rubric_criteria.id"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    was_clamped: Mapped[bool] = mapped_column(Boolean, default=False)

    ai_execution: Mapped["AIExecution"] = relationship(back_populates="criterion_scores")


class HumanReview(Base):
    __tablename__ = "human_reviews"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_human_reviews_job_id"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("correction_jobs.id"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision), nullable=False)
    final_total: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    final_scores_json: Mapped[str] = mapped_column(Text, nullable=False)  # [{criterion_id, score}]
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    actor_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
