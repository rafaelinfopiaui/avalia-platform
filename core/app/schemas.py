from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, computed_field, model_validator


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
    statement: str = Field(max_length=10000)
    reference_answer: str = Field(max_length=10000)
    max_score: Decimal = Field(gt=0)


class QuestionOut(BaseModel):
    id: str
    statement: str
    reference_answer: str
    max_score: Decimal
    position: int
    rubrics: list[RubricOut] = []

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    title: str
    class_group_id: Optional[str] = None
    questions: Optional[list[QuestionInput]] = None
    question: Optional[QuestionInput] = None

    @model_validator(mode="after")
    def normalize_questions(self):
        has_questions = bool(self.questions)
        has_question = self.question is not None
        if has_questions and has_question:
            raise ValueError(
                "Forneça `questions` ou `question`, não ambos. "
                "`question` está depreciado; prefira `questions`."
            )
        if not has_questions and not has_question:
            raise ValueError("Pelo menos uma questão é obrigatória.")
        if has_question:
            self.questions = [self.question]
        if len(self.questions or []) > 50:
            raise ValueError("Uma avaliação pode ter no máximo 50 questões.")
        return self


class QuestionOrderInput(BaseModel):
    question_ids: list[str]


class AssessmentUpdate(BaseModel):
    title: str


class AssessmentOut(BaseModel):
    id: str
    title: str
    status: str
    owner_id: str
    class_group_id: Optional[str] = None
    cloned_from_id: Optional[str] = None
    created_at: datetime
    questions: list[QuestionOut] = []

    @computed_field(return_type=Optional[QuestionOut])
    @property
    def question(self):
        return self.questions[0] if len(self.questions) == 1 else None

    @computed_field(return_type=Decimal)
    @property
    def assessment_max_score(self):
        return sum((question.max_score for question in self.questions), Decimal("0"))

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
