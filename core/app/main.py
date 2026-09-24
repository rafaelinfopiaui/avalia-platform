from __future__ import annotations

import json
from decimal import Decimal

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db
from app.deps import get_current_user, require_role
from app.logging_utils import log_event, new_correlation_id
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
    ReviewDecision,
    Role,
    Rubric,
    RubricCriterion,
    User,
)
from app.schemas import (
    AIExecutionOut,
    AnswerInput,
    AnswerOut,
    AssessmentCreate,
    AssessmentOut,
    AssessmentSummaryOut,
    CorrectionJobContextOut,
    CorrectionJobOut,
    CriterionScoreOut,
    HumanReviewInput,
    HumanReviewOut,
    HumanReviewSummaryOut,
    LoginRequest,
    MeResponse,
    QuestionOut,
    RubricInput,
    RubricOut,
    TokenResponse,
)
from app.security import create_access_token, create_refresh_token, verify_password
from app.services.correction import round_score, run_correction_job

settings = get_settings()

app = FastAPI(title="AvalIA Core API", version="0.1.0-demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id", new_correlation_id())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


def error_response(
    status_code: int, code: str, message: str, correlation_id: str,
    details: dict | None = None, field_errors: list | None = None,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": details or {},
            "correlation_id": correlation_id,
            "field_errors": field_errors or [],
        },
    )


# ---------------- Auth ----------------
@app.post("/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    # Mensagem não revela se o e-mail existe (RF-01)
    generic_error = "Credenciais inválidas."
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        log_event("login_failed", correlation_id, email_hash=hash(payload.email))
        return error_response(401, "INVALID_CREDENTIALS", generic_error, correlation_id)
    access = create_access_token(user.id, user.role.value)
    refresh = create_refresh_token(user.id, user.role.value)
    log_event("login_success", correlation_id, user_id=user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@app.get("/v1/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(id=user.id, email=user.email, role=user.role.value)


# ---------------- Assessments ----------------
@app.get("/v1/assessments", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
    query = db.query(Assessment)
    if user.role == Role.PROFESSOR:
        query = query.filter(Assessment.owner_id == user.id)
    return query.order_by(Assessment.created_at.desc()).all()


@app.post("/v1/assessments", response_model=AssessmentOut, status_code=201)
def create_assessment(
    payload: AssessmentCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    assessment = Assessment(title=payload.title, owner_id=user.id, status=AssessmentStatus.RASCUNHO)
    db.add(assessment)
    db.flush()
    if payload.question:
        q = Question(
            assessment_id=assessment.id,
            statement=payload.question.statement,
            reference_answer=payload.question.reference_answer,
            max_score=payload.question.max_score,
        )
        db.add(q)
    db.commit()
    db.refresh(assessment)
    db.add(AuditEvent(
        actor_id=user.id, action="CREATE", resource_type="Assessment",
        resource_id=assessment.id, after_json=json.dumps({"title": assessment.title}),
    ))
    db.commit()
    log_event("assessment_created", correlation_id, assessment_id=assessment.id, user_id=user.id)
    return assessment


def _get_owned_assessment(db: Session, assessment_id: str, user: User) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if user.role == Role.PROFESSOR and assessment.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão sobre esta avaliação.")
    return assessment


@app.get("/v1/assessments/{assessment_id}", response_model=AssessmentOut)
def get_assessment(
    assessment_id: str, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    return _get_owned_assessment(db, assessment_id, user)


@app.post("/v1/assessments/{assessment_id}/publish")
def publish_assessment(
    assessment_id: str, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    assessment = _get_owned_assessment(db, assessment_id, user)

    if not assessment.questions:
        return error_response(422, "MISSING_QUESTION", "A avaliação precisa de ao menos uma questão.", correlation_id)

    for question in assessment.questions:
        published_rubric = next((r for r in question.rubrics if r.is_published), None)
        # pega rubrica mais recente se nenhuma publicada ainda (permitir publicar avaliação + rubrica junto)
        rubric = published_rubric or (question.rubrics[-1] if question.rubrics else None)
        if rubric is None or not rubric.criteria:
            return error_response(
                422, "MISSING_RUBRIC",
                f"A questão '{question.statement[:40]}...' precisa de uma rubrica com critérios.",
                correlation_id,
            )
        total = sum((c.max_score for c in rubric.criteria), Decimal("0"))
        if round_score(total) != round_score(question.max_score):
            return error_response(
                422, "RUBRIC_TOTAL_MISMATCH",
                f"A soma dos critérios deve ser {question.max_score}.",
                correlation_id,
                details={"expected": str(question.max_score), "actual": str(total)},
            )
        rubric.is_published = True

    assessment.status = AssessmentStatus.PUBLICADA
    db.commit()
    db.add(AuditEvent(actor_id=user.id, action="PUBLISH", resource_type="Assessment", resource_id=assessment.id))
    db.commit()
    log_event("assessment_published", correlation_id, assessment_id=assessment.id)
    return {"status": "PUBLICADA"}


# ---------------- Rubric ----------------
@app.post("/v1/questions/{question_id}/rubric", response_model=RubricOut, status_code=201)
def create_rubric(
    question_id: str, payload: RubricInput, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = db.get(Assessment, question.assessment_id)
    if user.role == Role.PROFESSOR and assessment.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sem permissão sobre esta questão.")

    existing_versions = db.query(Rubric).filter(Rubric.question_id == question_id).count()
    rubric = Rubric(question_id=question_id, version=existing_versions + 1, is_published=False)
    db.add(rubric)
    db.flush()
    for crit in payload.criteria:
        db.add(RubricCriterion(
            rubric_id=rubric.id, name=crit.name, description=crit.description, max_score=crit.max_score,
        ))
    db.commit()
    db.refresh(rubric)
    log_event("rubric_created", correlation_id, rubric_id=rubric.id, question_id=question_id, version=rubric.version)
    return rubric


# ---------------- Answers ----------------
@app.post("/v1/answers", response_model=AnswerOut, status_code=201)
def create_answer(
    payload: AnswerInput, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    _get_owned_assessment(db, question.assessment_id, user)
    answer = Answer(question_id=payload.question_id, student_name_fake=payload.student_name_fake, text=payload.text)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


# ---------------- Corrections ----------------
def _serialize_job(db: Session, job: CorrectionJob) -> CorrectionJobOut:
    latest_exec = (
        db.query(AIExecution)
        .filter(AIExecution.job_id == job.id)
        .order_by(AIExecution.created_at.desc())
        .first()
    )
    latest_out = None
    if latest_exec:
        scores = db.query(CriterionScore).filter(CriterionScore.ai_execution_id == latest_exec.id).all()
        latest_out = AIExecutionOut(
            id=latest_exec.id,
            engine_mode=latest_exec.engine_mode,
            model=latest_exec.model,
            confidence_method_version=latest_exec.confidence_method_version,
            overall_confidence=latest_exec.overall_confidence,
            review_recommendation=latest_exec.review_recommendation,
            duration_ms=latest_exec.duration_ms,
            flags=json.loads(latest_exec.flags or "[]"),
            criterion_scores=[CriterionScoreOut.model_validate(s) for s in scores],
        )
    return CorrectionJobOut(
        id=job.id, answer_id=job.answer_id, status=job.status.value,
        attempt=job.attempt, error_message=job.error_message, latest_execution=latest_out,
    )


def _get_job_context(
    db: Session, job_id: str, user: User
) -> tuple[CorrectionJob, Answer, Question, Assessment]:
    job = db.get(CorrectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    answer = db.get(Answer, job.answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    return job, answer, question, assessment


@app.post("/v1/answers/{answer_id}/corrections", status_code=202)
async def request_correction(
    answer_id: str, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    _get_owned_assessment(db, question.assessment_id, user)
    rubric = next((r for r in question.rubrics if r.is_published), None)
    if rubric is None:
        return error_response(422, "RUBRIC_NOT_PUBLISHED", "A questão não possui rubrica publicada.", correlation_id)

    prior_attempts = db.query(CorrectionJob).filter(CorrectionJob.answer_id == answer_id).count()
    job = CorrectionJob(answer_id=answer_id, rubric_id=rubric.id, status=JobStatus.PENDENTE, attempt=prior_attempts + 1)
    db.add(job)
    db.commit()
    db.refresh(job)

    log_event("correction_requested", correlation_id, job_id=job.id, answer_id=answer_id, attempt=job.attempt)

    background_tasks.add_task(run_correction_job, job.id, SessionLocal)

    # NOTA (bug corrigido): o frontend trata esta resposta como um CorrectionJob
    # (mesmo contrato de GET /correction-jobs/{id}, que usa a chave "id"), mas este
    # endpoint retornava apenas "job_id". Isso fazia o frontend navegar para
    # /correcoes/undefined e o polling subsequente falhar com 404, mesmo quando o
    # job era criado e processado com sucesso no backend (ver
    # core/app/tests/test_core_flow.py::test_correction_creation_response_has_id_for_polling).
    # Mantemos "job_id" por retrocompatibilidade com scripts/documentação existentes.
    return {"id": job.id, "job_id": job.id, "status": job.status.value}


@app.get("/v1/correction-jobs/{job_id}", response_model=CorrectionJobOut)
def get_correction_job(
    job_id: str, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    job, _, _, _ = _get_job_context(db, job_id, user)
    return _serialize_job(db, job)


@app.get("/v1/correction-jobs/{job_id}/context", response_model=CorrectionJobContextOut)
def get_correction_job_context(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    job, answer, question, assessment = _get_job_context(db, job_id, user)
    review = db.query(HumanReview).filter(HumanReview.job_id == job_id).first()
    review_summary = _serialize_review_summary(db, review) if review is not None else None
    return CorrectionJobContextOut(
        job=_serialize_job(db, job),
        answer=AnswerOut.model_validate(answer),
        question=QuestionOut.model_validate(question),
        assessment=AssessmentSummaryOut.model_validate(assessment),
        human_review=review_summary,
    )


def _serialize_review_summary(db: Session, review: HumanReview) -> HumanReviewSummaryOut:
    reviewer = db.get(User, review.reviewer_id)
    return HumanReviewSummaryOut(
        id=review.id,
        reviewer_id=review.reviewer_id,
        reviewer_email=reviewer.email if reviewer is not None else "",
        decision=review.decision.value,
        final_total=review.final_total,
        final_scores=json.loads(review.final_scores_json),
        justification=review.justification,
        created_at=review.created_at,
    )


def _review_is_equivalent(
    review: HumanReview,
    reviewer_id: str,
    decision: ReviewDecision,
    final_scores: list[dict[str, str]],
    justification: str | None,
) -> bool:
    existing_scores = {
        item["criterion_id"]: Decimal(str(item["score"]))
        for item in json.loads(review.final_scores_json)
    }
    attempted_scores = {
        item["criterion_id"]: Decimal(str(item["score"]))
        for item in final_scores
    }
    return (
        review.reviewer_id == reviewer_id
        and review.decision == decision
        and existing_scores == attempted_scores
        and (review.justification or "") == (justification or "")
    )


def _review_conflict_response(
    db: Session, review: HumanReview, correlation_id: str
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "code": "REVIEW_ALREADY_EXISTS",
            "message": "Este job já possui uma decisão humana registrada.",
            "existing_review": _serialize_review_summary(db, review).model_dump(mode="json"),
            "correlation_id": correlation_id,
        },
    )


@app.post("/v1/corrections/{job_id}/reviews", response_model=HumanReviewOut)
def review_correction(
    job_id: str, payload: HumanReviewInput, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    job, _, _, _ = _get_job_context(db, job_id, user)

    if payload.decision not in (ReviewDecision.APPROVE.value, ReviewDecision.ALTER.value):
        return error_response(422, "INVALID_DECISION", "Decisão inválida.", correlation_id)

    latest_exec = (
        db.query(AIExecution).filter(AIExecution.job_id == job_id)
        .order_by(AIExecution.created_at.desc()).first()
    )
    scores_by_criterion = {}
    if latest_exec:
        for s in db.query(CriterionScore).filter(CriterionScore.ai_execution_id == latest_exec.id).all():
            scores_by_criterion[s.criterion_id] = s

    if payload.decision == ReviewDecision.ALTER.value:
        if not payload.justification or not payload.justification.strip():
            return error_response(
                422, "JUSTIFICATION_REQUIRED", "Justificativa é obrigatória para alterar a nota.", correlation_id,
            )
        final_scores = []
        total = Decimal("0")
        for cs in payload.criteria_scores:
            ref = scores_by_criterion.get(cs.criterion_id)
            max_score = ref.max_score if ref else Decimal("0")
            score = cs.score
            if score < 0 or score > max_score:
                return error_response(
                    422, "SCORE_OUT_OF_RANGE",
                    f"Pontuação do critério {cs.criterion_id} deve estar entre 0 e {max_score}.",
                    correlation_id,
                )
            final_scores.append({"criterion_id": cs.criterion_id, "score": str(round_score(score))})
            total += score
        final_total = round_score(total)
    else:
        final_scores = [
            {"criterion_id": cid, "score": str(s.score)} for cid, s in scores_by_criterion.items()
        ]
        final_total = round_score(sum((s.score for s in scores_by_criterion.values()), Decimal("0")))

    decision = ReviewDecision(payload.decision)
    existing_review = db.query(HumanReview).filter(HumanReview.job_id == job_id).first()
    if existing_review is not None:
        if _review_is_equivalent(
            existing_review, user.id, decision, final_scores, payload.justification
        ):
            return existing_review
        return _review_conflict_response(db, existing_review, correlation_id)

    review = HumanReview(
        job_id=job_id, reviewer_id=user.id, decision=decision,
        final_total=final_total, final_scores_json=json.dumps(final_scores),
        justification=payload.justification,
    )
    db.add(review)
    db.add(AuditEvent(
        actor_id=user.id, action=f"REVIEW_{payload.decision}", resource_type="CorrectionJob",
        resource_id=job_id,
        before_json=json.dumps({cid: str(s.score) for cid, s in scores_by_criterion.items()}),
        after_json=json.dumps(final_scores),
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_review = db.query(HumanReview).filter(HumanReview.job_id == job_id).first()
        if existing_review is None:
            raise
        if _review_is_equivalent(
            existing_review, user.id, decision, final_scores, payload.justification
        ):
            return existing_review
        return _review_conflict_response(db, existing_review, correlation_id)
    db.refresh(review)
    log_event("human_review_registered", correlation_id, job_id=job_id, decision=payload.decision, reviewer_id=user.id)
    return review


# ---------------- Health ----------------
@app.get("/v1/health")
async def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False
    ai_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.ai_engine_url}/v1/health")
        ai_ok = r.status_code == 200
    except Exception:
        ai_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok, "ai_engine": ai_ok}
