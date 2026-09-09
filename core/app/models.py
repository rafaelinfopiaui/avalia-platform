from __future__ import annotations
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Text, ForeignKey, DateTime, Enum, Numeric, Boolean, Integer, JSON
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
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus), default=AssessmentStatus.RASCUNHO, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    questions: Mapped[list["Question"]] = relationship(back_populates="assessment")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    assessment_id: Mapped[str] = mapped_column(String, ForeignKey("assessments.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str] = mapped_column(Text, nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="questions")
    rubrics: Mapped[list["Rubric"]] = relationship(back_populates="question")


class Rubric(Base):
    __tablename__ = "rubrics"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    question_id: Mapped[str] = mapped_column(String, ForeignKey("questions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question: Mapped["Question"] = relationship(back_populates="rubrics")
    criteria: Mapped[list["RubricCriterion"]] = relationship(back_populates="rubric")


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
