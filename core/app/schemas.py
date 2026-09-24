from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    role: str


# ---- Rubric ----
class RubricCriterionInput(BaseModel):
    name: str
    description: str = ""
    max_score: Decimal = Field(gt=0)


class RubricInput(BaseModel):
    criteria: list[RubricCriterionInput]


class RubricCriterionOut(BaseModel):
    id: str
    name: str
    description: str
    max_score: Decimal

    class Config:
        from_attributes = True


class RubricOut(BaseModel):
    id: str
    question_id: str
    version: int
    is_published: bool
    criteria: list[RubricCriterionOut]

    class Config:
        from_attributes = True


# ---- Question / Assessment ----
class QuestionInput(BaseModel):
    statement: str
    reference_answer: str
    max_score: Decimal = Field(gt=0)


class QuestionOut(BaseModel):
    id: str
    statement: str
    reference_answer: str
    max_score: Decimal
    rubrics: list[RubricOut] = []

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    title: str
    question: Optional[QuestionInput] = None


class AssessmentOut(BaseModel):
    id: str
    title: str
    status: str
    owner_id: str
    created_at: datetime
    questions: list[QuestionOut] = []

    class Config:
        from_attributes = True


class AssessmentSummaryOut(BaseModel):
    id: str
    title: str

    class Config:
        from_attributes = True


# ---- Answer ----
class AnswerInput(BaseModel):
    question_id: str
    student_name_fake: str
    text: str


class AnswerOut(BaseModel):
    id: str
    question_id: str
    student_name_fake: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Correction / job ----
class CriterionScoreOut(BaseModel):
    criterion_id: str
    score: Decimal
    max_score: Decimal
    reason: str
    evidence: str
    confidence: Decimal
    was_clamped: bool

    class Config:
        from_attributes = True


class AIExecutionOut(BaseModel):
    id: str
    engine_mode: str
    model: str
    confidence_method_version: str
    overall_confidence: Decimal
    review_recommendation: str
    duration_ms: int
    flags: list[str]
    criterion_scores: list[CriterionScoreOut]

    class Config:
        from_attributes = True


class CorrectionJobOut(BaseModel):
    id: str
    answer_id: str
    status: str
    attempt: int
    error_message: Optional[str] = None
    latest_execution: Optional[AIExecutionOut] = None

    class Config:
        from_attributes = True


# ---- Human review ----
class CriterionScoreInput(BaseModel):
    criterion_id: str
    score: Decimal = Field(ge=0)


class HumanReviewInput(BaseModel):
    decision: str  # APPROVE | ALTER
    criteria_scores: list[CriterionScoreInput] = []
    justification: Optional[str] = None


class HumanReviewOut(BaseModel):
    id: str
    job_id: str
    reviewer_id: str
    decision: str
    final_total: Decimal
    justification: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HumanReviewSummaryOut(BaseModel):
    id: str
    reviewer_id: str
    reviewer_email: str
    decision: str
    final_total: Decimal
    final_scores: list[CriterionScoreInput]
    justification: Optional[str]
    created_at: datetime


class CorrectionJobContextOut(BaseModel):
    job: CorrectionJobOut
    answer: AnswerOut
    question: QuestionOut
    assessment: AssessmentSummaryOut
    human_review: Optional[HumanReviewSummaryOut] = None


# ---- Error envelope ----
class FieldError(BaseModel):
    field: str
    reason: str


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: dict = {}
    correlation_id: str
    field_errors: list[FieldError] = []
