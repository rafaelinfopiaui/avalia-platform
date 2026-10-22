from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime
from decimal import Decimal

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db
from app.deps import get_current_user, require_role
from app.logging_utils import log_event, new_correlation_id
from app.models import (
    AIExecution,
    Answer,
    AnswerImage,
    AnswerSource,
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
    TranscriptionExtraction,
    TranscriptionStatus,
    User,
    gen_uuid,
)
from app.routers.academic import (
    require_active_class_link,
    require_assessment_mutation,
)
from app.routers.academic import (
    router as academic_router,
)
from app.routers.config import (
    router as config_router,
)
from app.routers.images import (
    _MULTIPART_OVERHEAD,
    _STORAGE_ERROR,
    _lock_answer_row,
    _normalize_declared_type,
    _sanitize_original_filename,
    _storage_dir,
    _stored_path,
    _too_large,
    _write_validated_file,
)
from app.routers.images import (
    router as images_router,
)
from app.schemas import (
    AIExecutionOut,
    AnswerImageOut,
    AnswerInput,
    AnswerOut,
    AnswerWithImagesOut,
    AssessmentCreate,
    AssessmentOut,
    AssessmentSummaryOut,
    AssessmentUpdate,
    CorrectionJobContextOut,
    CorrectionJobOut,
    CriterionScoreOut,
    HumanReviewInput,
    HumanReviewOut,
    HumanReviewSummaryOut,
    LatestTranscriptionExtractionOut,
    LoginRequest,
    ManualTranscriptionInput,
    MeResponse,
    QuestionInput,
    QuestionOrderInput,
    QuestionOut,
    RubricInput,
    RubricOut,
    TokenResponse,
    TranscriptionExtractionOut,
    TranscriptionExtractionStateOut,
)
from app.security import create_access_token, create_refresh_token, verify_password
from app.services import inference_gate as inference_gate_module
from app.services.correction import round_score, run_correction_job
from app.services.inference_gate import INFERENCE_BUSY, InferenceBusyError

settings = get_settings()

app = FastAPI(title="AvalIA Core API", version="0.1.0-demo")
app.include_router(academic_router)
app.include_router(config_router)
app.include_router(images_router)

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
    status_code: int,
    code: str,
    message: str,
    correlation_id: str,
    details: dict | None = None,
    field_errors: list | None = None,
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
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    if settings.academic_module_enabled and payload.class_group_id is None:
        raise HTTPException(status_code=422, detail="Turma é obrigatória para novas avaliações.")
    if payload.class_group_id is not None:
        require_active_class_link(db, user, payload.class_group_id)
    assessment = Assessment(
        title=payload.title,
        owner_id=user.id,
        class_group_id=payload.class_group_id,
        status=AssessmentStatus.RASCUNHO,
    )
    db.add(assessment)
    db.flush()
    for position, item in enumerate(payload.questions or [], start=1):
        q = Question(
            assessment_id=assessment.id,
            statement=item.statement,
            reference_answer=item.reference_answer,
            max_score=item.max_score,
            position=position,
        )
        db.add(q)
    db.commit()
    db.refresh(assessment)
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="CREATE",
            resource_type="Assessment",
            resource_id=assessment.id,
            after_json=json.dumps({"title": assessment.title}),
        )
    )
    db.commit()
    log_event("assessment_created", correlation_id, assessment_id=assessment.id, user_id=user.id)
    if payload.question is not None:
        log_event(
            "assessment_created_legacy_singular_payload",
            correlation_id,
            assessment_id=assessment.id,
            assessment_created_legacy_singular_payload=True,
        )
    return assessment


def _get_owned_assessment(db: Session, assessment_id: str, user: User) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if user.role == Role.PROFESSOR and assessment.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão sobre esta avaliação.")
    return assessment


def _get_assessment_for_question(
    db: Session, question_id: str, user: User
) -> tuple[Question, Assessment]:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == question.assessment_id)
        .with_for_update()
        .one_or_none()
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    require_assessment_mutation(db, user, assessment)
    return question, assessment


def _lock_assessment(db: Session, assessment_id: str) -> Assessment:
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id)
        .with_for_update()
        .one_or_none()
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    return assessment


def _require_draft(assessment: Assessment) -> None:
    if assessment.status == AssessmentStatus.PUBLICADA:
        raise HTTPException(
            status_code=409,
            detail="Avaliação publicada não pode ser alterada; crie um clone.",
        )


@app.get("/v1/assessments/{assessment_id}", response_model=AssessmentOut)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    return _get_owned_assessment(db, assessment_id, user)


@app.patch("/v1/assessments/{assessment_id}", response_model=AssessmentOut)
def update_assessment(
    assessment_id: str,
    payload: AssessmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    assessment = _get_owned_assessment(db, assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    _require_draft(assessment)
    assessment.title = payload.title
    db.commit()
    db.refresh(assessment)
    return assessment


@app.post("/v1/assessments/{assessment_id}/publish")
def publish_assessment(
    assessment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    assessment = _get_owned_assessment(db, assessment_id, user)
    require_assessment_mutation(db, user, assessment)

    if not assessment.questions:
        return error_response(422, "MISSING_QUESTION", "A avaliação precisa de ao menos uma questão.", correlation_id)

    rubrics_to_publish = []
    for question in assessment.questions:
        published_rubric = next((r for r in question.rubrics if r.is_published), None)
        # pega rubrica mais recente se nenhuma publicada ainda (permitir publicar avaliação + rubrica junto)
        rubric = published_rubric or (question.rubrics[0] if question.rubrics else None)
        if rubric is None or not rubric.criteria:
            return error_response(
                422,
                "MISSING_RUBRIC",
                f"A questão '{question.statement[:40]}...' precisa de uma rubrica com critérios.",
                correlation_id,
            )
        total = sum((c.max_score for c in rubric.criteria), Decimal("0"))
        if round_score(total) != round_score(question.max_score):
            return error_response(
                422,
                "RUBRIC_TOTAL_MISMATCH",
                f"A soma dos critérios deve ser {question.max_score}.",
                correlation_id,
                details={"expected": str(question.max_score), "actual": str(total)},
            )
        rubrics_to_publish.append(rubric)

    for rubric in rubrics_to_publish:
        rubric.is_published = True
    assessment.status = AssessmentStatus.PUBLICADA
    db.commit()
    db.add(AuditEvent(actor_id=user.id, action="PUBLISH", resource_type="Assessment", resource_id=assessment.id))
    db.commit()
    log_event("assessment_published", correlation_id, assessment_id=assessment.id)
    return {"status": "PUBLICADA"}


@app.post("/v1/assessments/{assessment_id}/clone", response_model=AssessmentOut, status_code=201)
def clone_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    source = _get_owned_assessment(db, assessment_id, user)
    if source.status != AssessmentStatus.PUBLICADA:
        raise HTTPException(status_code=409, detail="Apenas avaliações publicadas podem ser clonadas.")
    clone = Assessment(
        title=source.title,
        owner_id=user.id,
        class_group_id=source.class_group_id,
        cloned_from_id=source.id,
        status=AssessmentStatus.RASCUNHO,
    )
    db.add(clone)
    db.flush()
    for source_question in source.questions:
        cloned_question = Question(
            assessment_id=clone.id,
            statement=source_question.statement,
            reference_answer=source_question.reference_answer,
            max_score=source_question.max_score,
            position=source_question.position,
        )
        db.add(cloned_question)
        db.flush()
        source_rubric = source_question.rubrics[0] if source_question.rubrics else None
        if source_rubric is not None:
            cloned_rubric = Rubric(
                question_id=cloned_question.id, version=1, is_published=False
            )
            db.add(cloned_rubric)
            db.flush()
            for criterion in source_rubric.criteria:
                db.add(
                    RubricCriterion(
                        rubric_id=cloned_rubric.id,
                        name=criterion.name,
                        description=criterion.description,
                        max_score=criterion.max_score,
                    )
                )
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="CLONE",
            resource_type="Assessment",
            resource_id=clone.id,
            before_json=json.dumps({"source_assessment_id": source.id}),
        )
    )
    db.commit()
    db.refresh(clone)
    return clone


@app.post("/v1/assessments/{assessment_id}/questions", response_model=QuestionOut, status_code=201)
def create_question(
    assessment_id: str,
    payload: QuestionInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    assessment = _lock_assessment(db, assessment_id)
    require_assessment_mutation(db, user, assessment)
    _require_draft(assessment)
    current_count = db.query(Question).filter(Question.assessment_id == assessment.id).count()
    if current_count >= 50:
        raise HTTPException(status_code=422, detail="Uma avaliação pode ter no máximo 50 questões.")
    question = Question(
        assessment_id=assessment.id,
        statement=payload.statement,
        reference_answer=payload.reference_answer,
        max_score=payload.max_score,
        position=current_count + 1,
    )
    db.add(question)
    db.flush()
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="CREATE",
            resource_type="Question",
            resource_id=question.id,
            after_json=json.dumps({"assessment_id": assessment.id, "position": question.position}),
        )
    )
    db.commit()
    db.refresh(question)
    return question


@app.patch("/v1/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: str,
    payload: QuestionInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    question, assessment = _get_assessment_for_question(db, question_id, user)
    _require_draft(assessment)
    before = {"max_score": str(question.max_score), "position": question.position}
    question.statement = payload.statement
    question.reference_answer = payload.reference_answer
    question.max_score = payload.max_score
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="UPDATE",
            resource_type="Question",
            resource_id=question.id,
            before_json=json.dumps(before),
            after_json=json.dumps(
                {"max_score": str(question.max_score), "position": question.position}
            ),
        )
    )
    db.commit()
    db.refresh(question)
    return question


@app.delete("/v1/questions/{question_id}", status_code=204)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    question, assessment = _get_assessment_for_question(db, question_id, user)
    _require_draft(assessment)
    if db.query(Answer.id).filter(Answer.question_id == question.id).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Questão possui respostas registradas; não pode ser excluída.",
        )
    remaining = (
        db.query(Question)
        .filter(Question.assessment_id == assessment.id, Question.id != question.id)
        .order_by(Question.position)
        .all()
    )
    deleted_position = question.position
    try:
        db.delete(question)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Questão possui respostas registradas; não pode ser excluída.",
        ) from None
    if remaining:
        offset = max(item.position for item in remaining) + len(remaining) + 1
        db.execute(
            update(Question)
            .where(Question.assessment_id == assessment.id)
            .values(position=Question.position + offset)
        )
        db.flush()
        for position, item in enumerate(remaining, start=1):
            item.position = position
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="DELETE",
            resource_type="Question",
            resource_id=question.id,
            before_json=json.dumps(
                {"assessment_id": assessment.id, "position": deleted_position}
            ),
        )
    )
    db.commit()
    return Response(status_code=204)


@app.put("/v1/assessments/{assessment_id}/questions/order", response_model=AssessmentOut)
def reorder_questions(
    assessment_id: str,
    payload: QuestionOrderInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    assessment = _lock_assessment(db, assessment_id)
    require_assessment_mutation(db, user, assessment)
    _require_draft(assessment)
    questions = db.query(Question).filter(Question.assessment_id == assessment.id).all()
    previous_order = [question.id for question in sorted(questions, key=lambda item: item.position)]
    current_ids = {question.id for question in questions}
    if len(payload.question_ids) != len(set(payload.question_ids)) or set(payload.question_ids) != current_ids:
        raise HTTPException(
            status_code=422,
            detail="A ordem deve conter exatamente todos os IDs atuais, sem repetições.",
        )
    if questions:
        offset = max(question.position for question in questions) + len(questions) + 1
        db.execute(
            update(Question)
            .where(Question.assessment_id == assessment.id)
            .values(position=Question.position + offset)
        )
        db.flush()
        by_id = {question.id: question for question in questions}
        for position, question_id in enumerate(payload.question_ids, start=1):
            by_id[question_id].position = position
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="REORDER",
            resource_type="Assessment",
            resource_id=assessment.id,
            before_json=json.dumps({"question_ids": previous_order}),
            after_json=json.dumps({"question_ids": payload.question_ids}),
        )
    )
    db.commit()
    db.refresh(assessment)
    return assessment


# ---------------- Rubric ----------------
@app.post("/v1/questions/{question_id}/rubric", response_model=RubricOut, status_code=201)
def create_rubric(
    question_id: str,
    payload: RubricInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    question, assessment = _get_assessment_for_question(db, question_id, user)
    _require_draft(assessment)

    existing_versions = db.query(Rubric).filter(Rubric.question_id == question_id).count()
    rubric = Rubric(question_id=question_id, version=existing_versions + 1, is_published=False)
    db.add(rubric)
    db.flush()
    for crit in payload.criteria:
        db.add(
            RubricCriterion(
                rubric_id=rubric.id,
                name=crit.name,
                description=crit.description,
                max_score=crit.max_score,
            )
        )
    db.commit()
    db.refresh(rubric)
    log_event("rubric_created", correlation_id, rubric_id=rubric.id, question_id=question_id, version=rubric.version)
    return rubric


# ---------------- Answers ----------------
@app.post("/v1/answers", response_model=AnswerOut, status_code=201)
def create_answer(
    payload: AnswerInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    # Invariante 1 (DEC-AV-037): resposta textual exige texto não-vazio.
    if not payload.text.strip():
        return error_response(
            422, "ANSWER_TEXT_REQUIRED", "O texto da resposta não pode ser vazio.", correlation_id
        )
    answer = Answer(
        question_id=payload.question_id,
        student_name_fake=payload.student_name_fake,
        text=payload.text,
        source=AnswerSource.TEXT,
        transcription_status=TranscriptionStatus.TRANSCRICAO_CONFIRMADA,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


# Resposta por imagem (DEC-AV-037): a foto é a entrada inicial, sem texto. Fica
# aqui, e não em routers/images.py, porque aquele módulo não pode referenciar
# correção (teste AST de isolamento); dele só reutilizamos validação e gravação.
@app.post("/v1/answers/image", response_model=AnswerWithImagesOut, status_code=201)
async def create_image_answer(
    request: Request,
    file: UploadFile = File(...),
    question_id: str = Form(...),
    student_name_fake: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    # Fail-fast: autorização e campos antes de gravar qualquer byte no storage.
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    student_name = student_name_fake.strip()
    if not student_name:
        return error_response(
            422, "STUDENT_NAME_REQUIRED", "A identificação do aluno é obrigatória.", correlation_id
        )

    max_bytes = get_settings().answer_image_max_bytes
    declared_length = request.headers.get("content-length")
    if declared_length is not None and declared_length.isdigit():
        if int(declared_length) > max_bytes + _MULTIPART_OVERHEAD:
            log_event("image_answer_rejected", correlation_id, question_id=question_id, reason="too_large")
            raise _too_large(max_bytes)
    declared_type = _normalize_declared_type(file.content_type)
    if declared_type is None:
        raise HTTPException(status_code=422, detail="Apenas imagens JPEG ou PNG são aceitas.")
    original_filename = _sanitize_original_filename(file.filename)

    answer_id = gen_uuid()
    storage_filename, content_type, size, sha256_hash = await _write_validated_file(
        file, declared_type, max_bytes, correlation_id, answer_id
    )

    answer = Answer(
        id=answer_id,
        question_id=question.id,
        student_name_fake=student_name,
        text=None,
        source=AnswerSource.IMAGE,
        transcription_status=TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
    )
    image = AnswerImage(
        answer_id=answer_id,
        storage_filename=storage_filename,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size,
        sha256_hash=sha256_hash,
        uploaded_by_id=user.id,
    )
    # Answer e AnswerImage são commitados juntos, por último; se falhar, nada
    # fica no banco e o arquivo já finalizado é removido (sem órfãos).
    try:
        db.add(answer)
        db.flush()
        db.add(image)
        db.commit()
    except Exception as exc:
        db.rollback()
        (_storage_dir() / storage_filename).unlink(missing_ok=True)
        log_event("image_answer_storage_failed", correlation_id, answer_id=answer_id, stage="commit")
        raise HTTPException(status_code=500, detail=_STORAGE_ERROR) from exc
    db.refresh(answer)
    db.refresh(image)
    log_event(
        "image_answer_created",
        correlation_id,
        answer_id=answer_id,
        image_id=image.id,
        user_id=user.id,
        content_type=content_type,
        size_bytes=size,
    )
    return AnswerWithImagesOut(
        **AnswerOut.model_validate(answer).model_dump(),
        images=[AnswerImageOut.model_validate(image)],
    )


# Retomada das respostas por imagem (DEBT-AV-014): leitura histórica, autorizada
# só por propriedade (como get_assessment) — não exige vínculo ativo de turma.
@app.get("/v1/assessments/{assessment_id}/image-answers", response_model=list[AnswerWithImagesOut])
def list_image_answers(
    assessment_id: str,
    question_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    assessment = _get_owned_assessment(db, assessment_id, user)
    query = (
        db.query(Answer)
        .join(Question, Answer.question_id == Question.id)
        .filter(Question.assessment_id == assessment.id, Answer.source == AnswerSource.IMAGE)
    )
    if question_id is not None:
        question = db.get(Question, question_id)
        if question is None or question.assessment_id != assessment.id:
            raise HTTPException(status_code=404, detail="Questão não encontrada nesta avaliação.")
        query = query.filter(Answer.question_id == question.id)
    answers = query.order_by(Answer.created_at, Answer.id).all()
    images_by_answer: dict[str, list[AnswerImage]] = {answer.id: [] for answer in answers}
    if answers:
        # Só imagens ativas (BL-AV-4B-05, R1); excluídas têm rota própria.
        images = (
            db.query(AnswerImage)
            .filter(AnswerImage.answer_id.in_(list(images_by_answer)), AnswerImage.deleted_at.is_(None))
            .order_by(AnswerImage.created_at, AnswerImage.id)
            .all()
        )
        for image in images:
            images_by_answer[image.answer_id].append(image)
    return [
        AnswerWithImagesOut(
            **AnswerOut.model_validate(answer).model_dump(),
            images=[AnswerImageOut.model_validate(image) for image in images_by_answer[answer.id]],
        )
        for answer in answers
    ]


# ---------------- Manual transcription (AV-S08B, DEC-AV-040) ----------------
# Rascunho e confirmação da transcrição de uma resposta por imagem. São mutações
# (exigem vínculo ativo, como request_correction) e NUNCA criam CorrectionJob nem
# chamam request_correction: a confirmação só libera o guard ANSWER_NOT_TRANSCRIBED.
_TRANSCRIPTION_IDEMPOTENT = "IDEMPOTENT"
_TRANSCRIPTION_CONFLICT_MESSAGES = {
    "TRANSCRIPTION_ALREADY_CONFIRMED": (
        "A transcrição desta resposta já foi confirmada e não pode mais ser alterada."
    ),
    "TRANSCRIPTION_VERSION_CONFLICT": (
        "A transcrição foi alterada em outra sessão; recarregue para ver a versão mais recente."
    ),
}
_NO_ACTIVE_IMAGE = "ANSWER_HAS_NO_ACTIVE_IMAGE"
_NO_ACTIVE_IMAGE_MESSAGE = (
    "Esta resposta não tem nenhuma imagem ativa. Restaure ou envie uma imagem antes de "
    "confirmar a transcrição."
)


def _active_images_query(db: Session, answer_id: str):
    # Imagens excluídas logicamente (BL-AV-4B-05) ficam fora da transcrição (R1).
    return db.query(AnswerImage).filter(
        AnswerImage.answer_id == answer_id, AnswerImage.deleted_at.is_(None)
    )


def _answer_with_images(db: Session, answer: Answer) -> AnswerWithImagesOut:
    images = _active_images_query(db, answer.id).order_by(AnswerImage.created_at, AnswerImage.id).all()
    return AnswerWithImagesOut(
        **AnswerOut.model_validate(answer).model_dump(),
        images=[AnswerImageOut.model_validate(image) for image in images],
    )


def _transcription_outcome(answer: Answer, payload: ManualTranscriptionInput, confirm: bool) -> str | None:
    """None quando a mutação pode prosseguir; senão o desfecho sem mutação."""
    if answer.transcription_status == TranscriptionStatus.TRANSCRICAO_CONFIRMADA:
        # DP-2/DP-3: confirmação é definitiva; só o reenvio idêntico, com a
        # versão já confirmada, é aceito (sem novo AuditEvent).
        if confirm and payload.text == answer.text:
            if payload.expected_version == answer.transcription_version:
                return _TRANSCRIPTION_IDEMPOTENT
            return "TRANSCRIPTION_VERSION_CONFLICT"
        return "TRANSCRIPTION_ALREADY_CONFIRMED"
    if payload.expected_version != answer.transcription_version:
        return "TRANSCRIPTION_VERSION_CONFLICT"
    return None


def _transcription_outcome_response(db: Session, answer: Answer, outcome: str, correlation_id: str):
    if outcome == _TRANSCRIPTION_IDEMPOTENT:
        return _answer_with_images(db, answer)
    # Devolve o estado atual para o cliente decidir (padrão de REVIEW_ALREADY_EXISTS).
    return error_response(
        409,
        outcome,
        _TRANSCRIPTION_CONFLICT_MESSAGES[outcome],
        correlation_id,
        details={"current_answer": _answer_with_images(db, answer).model_dump(mode="json")},
    )


def _save_manual_transcription(
    answer_id: str,
    payload: ManualTranscriptionInput,
    request: Request,
    db: Session,
    user: User,
    *,
    confirm: bool,
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    if answer.source != AnswerSource.IMAGE:
        return error_response(
            422,
            "ANSWER_NOT_IMAGE_SOURCE",
            "A transcrição manual só se aplica a respostas enviadas por imagem.",
            correlation_id,
        )
    if confirm and not payload.text.strip():
        return error_response(
            422, "ANSWER_TEXT_REQUIRED", "O texto da transcrição não pode ser vazio.", correlation_id
        )
    outcome = _transcription_outcome(answer, payload, confirm)
    if outcome is not None:
        return _transcription_outcome_response(db, answer, outcome, correlation_id)
    if confirm:
        # BL-AV-4B-05 (R2): trava a linha de answers — o mesmo lock da
        # exclusão/restauração de imagem — e só então reavalia estado e imagem
        # ativa, para que nenhuma checagem fique inválida antes do commit.
        answer = _lock_answer_row(db, answer.id)
        outcome = _transcription_outcome(answer, payload, confirm)
        if outcome is not None:
            return _transcription_outcome_response(db, answer, outcome, correlation_id)
        if _active_images_query(db, answer.id).first() is None:
            log_event("manual_transcription_without_active_image", correlation_id, answer_id=answer.id)
            return error_response(
                409, _NO_ACTIVE_IMAGE, _NO_ACTIVE_IMAGE_MESSAGE, correlation_id, details={"answer_id": answer.id}
            )

    # A versão lida acima é a esperada; o UPDATE condicional abaixo garante, na
    # transação do banco, que ninguém a avançou desde então (lock otimista).
    before = {
        "manual_transcription_draft": answer.manual_transcription_draft,
        "transcription_version": answer.transcription_version,
    }
    if confirm:
        before.update(text=answer.text, transcription_status=answer.transcription_status.value)
        action = "manual_transcription_confirmed"
        values = {
            "text": payload.text,
            "transcription_status": TranscriptionStatus.TRANSCRICAO_CONFIRMADA,
            "transcription_confirmed_by_id": user.id,
            "transcription_confirmed_at": datetime.utcnow(),
            "manual_transcription_draft": None,
        }
    else:
        # Rascunho vazio é permitido: limpa o rascunho anterior.
        action = "manual_transcription_draft_saved"
        values = {"manual_transcription_draft": payload.text if payload.text.strip() else None}
    result = db.execute(
        update(Answer)
        .where(
            Answer.id == answer.id,
            Answer.transcription_version == payload.expected_version,
            Answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
        )
        .values(**values, transcription_version=Answer.transcription_version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        # Outra sessão mutou a resposta entre a leitura e o UPDATE.
        db.rollback()
        db.refresh(answer)
        outcome = _transcription_outcome(answer, payload, confirm) or "TRANSCRIPTION_VERSION_CONFLICT"
        log_event("manual_transcription_conflict", correlation_id, answer_id=answer.id, outcome=outcome)
        return _transcription_outcome_response(db, answer, outcome, correlation_id)

    after = {
        key: value.value if isinstance(value, TranscriptionStatus) else value
        for key, value in values.items()
        if key != "transcription_confirmed_at"
    }
    after["transcription_version"] = payload.expected_version + 1
    db.add(
        AuditEvent(
            actor_id=user.id,
            action=action,
            resource_type="Answer",
            resource_id=answer.id,
            before_json=json.dumps(before),
            after_json=json.dumps(after),
        )
    )
    db.commit()
    db.refresh(answer)
    log_event(
        action,
        correlation_id,
        answer_id=answer.id,
        user_id=user.id,
        transcription_version=answer.transcription_version,
    )
    return _answer_with_images(db, answer)


@app.patch("/v1/answers/{answer_id}/manual-transcription/draft", response_model=AnswerWithImagesOut)
def save_manual_transcription_draft(
    answer_id: str,
    payload: ManualTranscriptionInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    return _save_manual_transcription(answer_id, payload, request, db, user, confirm=False)


@app.post("/v1/answers/{answer_id}/manual-transcription/confirm", response_model=AnswerWithImagesOut)
def confirm_manual_transcription(
    answer_id: str,
    payload: ManualTranscriptionInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    return _save_manual_transcription(answer_id, payload, request, db, user, confirm=True)


# ---------------- Extração OCR/visão experimental (AV-S07B, DEC-AV-046) ----------------
# Só a imagem ativa entra no motor — nunca enunciado, referência ou transcrição
# esperada. A extração NUNCA confirma a transcrição nem cria CorrectionJob: no
# máximo preenche o rascunho VAZIO, que segue para conferência humana (/confirm).
_EXTRACTION_ENGINE = "ollama-vision"
_EXTRACTION_PROCESSING = "processando"
_EXTRACTION_FINAL_STATUSES = {"ok", "vazio", "falha"}
# Timeout explícito da chamada ao AI Engine (acima do timeout do motor de visão).
_EXTRACTION_TIMEOUT_SECONDS = 150.0
# Registro "processando" mais antigo que isto é tratado como abandonado (ex.:
# queda do processo) e deixa de bloquear um novo pedido EXPLÍCITO do usuário.
_EXTRACTION_STALE_SECONDS = _EXTRACTION_TIMEOUT_SECONDS + 60
_EXTRACTION_DRAFT_ORIGIN = "OCR"
_EXTRACTION_MESSAGES = {
    "draft_updated": (
        "Texto extraído e colocado no rascunho (origem: OCR, experimental). Confira com a imagem "
        "e corrija antes de confirmar; a transcrição NÃO foi confirmada."
    ),
    "draft_kept": (
        "Texto extraído, mas o rascunho já tem conteúdo e não foi alterado. Compare o texto "
        "extraído com o rascunho e decida o que manter."
    ),
    "answer_changed": (
        "Texto extraído, mas a resposta foi alterada durante a extração; o rascunho não foi "
        "modificado. Compare o texto extraído e decida o que manter."
    ),
    "vazio": "Nenhum texto foi identificado na imagem. Digite a transcrição manualmente.",
    "falha": (
        "Não foi possível extrair o texto da imagem. Digite a transcrição manualmente ou "
        "solicite uma nova extração."
    ),
}


def _extraction_failure(detail: str) -> dict:
    return {"status": "falha", "text": "", "model": "", "duration_ms": 0, "error_detail": detail}


async def _call_ai_engine_extract(image_base64: str, mime_type: str) -> dict:
    """Uma única chamada ao AI Engine (sem retry oculto); falhas viram 'falha'."""
    try:
        async with httpx.AsyncClient(timeout=_EXTRACTION_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{settings.ai_engine_url}/v1/extract",
                json={"image_base64": image_base64, "mime_type": mime_type},
            )
    except httpx.TimeoutException:
        return _extraction_failure(f"Timeout de {_EXTRACTION_TIMEOUT_SECONDS:.0f}s aguardando o AI Engine.")
    except httpx.HTTPError as exc:
        return _extraction_failure(f"AI Engine indisponível ({type(exc).__name__}).")
    if resp.status_code != 200:
        return _extraction_failure(f"AI Engine retornou HTTP {resp.status_code}.")
    try:
        return resp.json()
    except ValueError:
        return _extraction_failure("Resposta do AI Engine em formato inesperado (não JSON).")


def _normalize_extraction(data) -> tuple[str, str, str, int, str | None]:
    """(status, texto, modelo, duração, erro). Nunca fabrica texto fora de 'ok'."""
    if not isinstance(data, dict) or data.get("status") not in _EXTRACTION_FINAL_STATUSES:
        return "falha", "", "", 0, "Resposta do AI Engine fora do contrato de extração."
    status = data["status"]
    raw_text = data.get("text")
    text = raw_text if isinstance(raw_text, str) else ""
    # MÉDIA-7: preserva o texto do motor SEM strip quando há CONTEÚDO. Fora de
    # 'ok' nunca há texto. 'ok' só com espaços/quebras (sem conteúdo útil) é
    # reclassificado como 'vazio' com text="" — não é transcrição a preservar,
    # e nada é fabricado. Texto com conteúdo real é mantido fiel (sem strip).
    if status != "ok":
        text = ""
    elif not text.strip():
        status = "vazio"
        text = ""
    raw_model = data.get("model")
    model = raw_model if isinstance(raw_model, str) else ""
    try:
        duration_ms = max(int(data.get("duration_ms") or 0), 0)
    except (TypeError, ValueError):
        duration_ms = 0
    error_detail = data.get("error_detail") if isinstance(data.get("error_detail"), str) else None
    return status, text, model, duration_ms, error_detail


@app.post("/v1/answers/{answer_id}/transcription/extract", response_model=TranscriptionExtractionOut)
async def extract_transcription(
    answer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    if answer.source != AnswerSource.IMAGE:
        return error_response(
            422,
            "ANSWER_NOT_IMAGE_SOURCE",
            "A extração de texto só se aplica a respostas enviadas por imagem.",
            correlation_id,
        )

    # Seleção de imagem (BLOQUEANTE-1): nunca escolher silenciosamente entre
    # várias. O cliente pode passar answer_image_id EXPLÍCITO no corpo; se não
    # passar e houver >1 imagem ativa, a extração é recusada (ver _run_extraction).
    requested_image_id: str | None = None
    try:
        body = await request.json()
        if isinstance(body, dict):
            raw = body.get("answer_image_id")
            if isinstance(raw, str) and raw.strip():
                requested_image_id = raw.strip()
    except Exception:
        requested_image_id = None

    # Gate global de inferência (lacuna C): visão e análise textual não rodam
    # juntas no mesmo Ollama. Adquirido ANTES de criar o registro "processando",
    # para que a rejeição (409 INFERENCE_BUSY) não deixe nada pendente; liberado
    # sempre ao sair do bloco. Espera curta: ver app/services/inference_gate.py.
    try:
        gate = inference_gate_module.inference_gate
        async with gate.hold("extração de texto (visão)", inference_gate_module.EXTRACTION_WAIT_SECONDS):
            return await _run_extraction(
                answer_id, answer, user, db, correlation_id, requested_image_id
            )
    except InferenceBusyError as busy:
        db.rollback()
        log_event(
            "transcription_extraction_inference_busy",
            correlation_id,
            answer_id=answer_id,
            busy_with=busy.busy_with,
            waited_seconds=busy.waited_seconds,
        )
        return error_response(
            409,
            INFERENCE_BUSY,
            "O motor de IA local está ocupado com outra inferência (extração ou análise). Nenhuma "
            "extração foi iniciada; tente novamente em instantes.",
            correlation_id,
            details={"busy_with": busy.busy_with, "waited_seconds": busy.waited_seconds},
        )


async def _run_extraction(
    answer_id: str,
    answer: Answer,
    user: User,
    db: Session,
    correlation_id: str,
    requested_image_id: str | None = None,
) -> TranscriptionExtractionOut | JSONResponse:
    # Anti-duplo-clique: sob o lock da linha de answers (o mesmo da confirmação
    # e da exclusão de imagem), um registro "processando" recente bloqueia novo pedido.
    answer = _lock_answer_row(db, answer.id)
    if answer.transcription_status == TranscriptionStatus.TRANSCRICAO_CONFIRMADA:
        db.rollback()
        return error_response(
            409,
            "TRANSCRIPTION_ALREADY_CONFIRMED",
            _TRANSCRIPTION_CONFLICT_MESSAGES["TRANSCRIPTION_ALREADY_CONFIRMED"],
            correlation_id,
        )
    now = datetime.utcnow()
    pending = (
        db.query(TranscriptionExtraction)
        .filter(
            TranscriptionExtraction.answer_id == answer.id,
            TranscriptionExtraction.status == _EXTRACTION_PROCESSING,
        )
        .all()
    )
    for item in pending:
        if item.created_at is None or (now - item.created_at).total_seconds() < _EXTRACTION_STALE_SECONDS:
            db.rollback()
            log_event("transcription_extraction_in_progress", correlation_id, answer_id=answer.id)
            return error_response(
                409,
                "EXTRACTION_IN_PROGRESS",
                "Já existe uma extração em andamento para esta resposta. Aguarde a conclusão.",
                correlation_id,
                details={"extraction_id": item.id},
            )
    for item in pending:
        item.status = "falha"
        item.error_detail = "Extração abandonada (sem conclusão dentro do prazo); encerrada como falha."

    # Seleção EXPLÍCITA da imagem (BLOQUEANTE-1): nunca escolher silenciosamente
    # entre várias. Com answer_image_id explícito, valida posse/atividade e usa-o.
    # Sem explícito: só 1 imagem ativa => usa-a; >1 => recusa (seleção explícita
    # ainda não suportada nesta entrega) e orienta o fallback manual.
    active_images = (
        _active_images_query(db, answer.id).order_by(AnswerImage.created_at.desc(), AnswerImage.id.desc()).all()
    )
    if not active_images:
        db.rollback()
        return error_response(
            409,
            _NO_ACTIVE_IMAGE,
            "Esta resposta não tem nenhuma imagem ativa para extrair texto. Restaure ou envie uma imagem.",
            correlation_id,
            details={"answer_id": answer.id},
        )
    if requested_image_id is not None:
        image = next((img for img in active_images if img.id == requested_image_id), None)
        if image is None:
            db.rollback()
            return error_response(
                409,
                "ANSWER_IMAGE_NOT_ACTIVE",
                "A imagem indicada não pertence a esta resposta ou não está ativa; nenhuma extração foi feita.",
                correlation_id,
                details={"answer_image_id": requested_image_id},
            )
    elif len(active_images) > 1:
        db.rollback()
        return error_response(
            409,
            "MULTIPLE_ACTIVE_IMAGES_REQUIRE_EXPLICIT_SELECTION",
            "Há mais de uma imagem ativa nesta resposta; a seleção explícita de imagem ainda não é "
            "suportada nesta entrega. Indique a imagem (answer_image_id) ou use a transcrição manual.",
            correlation_id,
            details={
                "answer_id": answer.id,
                "active_image_ids": [img.id for img in active_images],
            },
        )
    else:
        image = active_images[0]
    image_path = _stored_path(image)
    if image_path is None:
        db.rollback()
        log_event("answer_image_file_missing", correlation_id, image_id=image.id, operation="extract")
        return error_response(
            409,
            "ANSWER_IMAGE_FILE_MISSING",
            "O arquivo da imagem ativa não está disponível no armazenamento; nenhuma extração foi feita.",
            correlation_id,
            details={"answer_image_id": image.id},
        )
    selection = {
        "chosen_image_id": image.id,
        "criterion": (
            "imagem indicada explicitamente pelo usuário"
            if requested_image_id is not None
            else "única imagem ativa"
        ),
        "active_image_count": len(active_images),
        "explicit_selection": requested_image_id is not None,
    }
    config = {
        "engine": _EXTRACTION_ENGINE,
        "ai_engine_endpoint": "/v1/extract",
        "timeout_seconds": _EXTRACTION_TIMEOUT_SECONDS,
        "input": "somente a imagem (sem enunciado, referência ou transcrição esperada)",
        "image_selection": selection,
    }
    extraction = TranscriptionExtraction(
        answer_id=answer.id,
        answer_image_id=image.id,
        engine=_EXTRACTION_ENGINE,
        model="",
        config_json=json.dumps(config, ensure_ascii=False),
        status=_EXTRACTION_PROCESSING,
        raw_output="",
        duration_ms=0,
    )
    db.add(extraction)
    # Commit antes da chamada lenta: libera o lock da resposta e deixa o
    # registro "processando" visível para bloquear cliques repetidos.
    db.commit()
    extraction_id = extraction.id
    log_event(
        "transcription_extraction_started",
        correlation_id,
        answer_id=answer_id,
        extraction_id=extraction_id,
        image_id=image.id,
        active_image_count=len(active_images),
    )

    # Revalidação (ALTA-2): entre a seleção e o uso, outra sessão pode ter
    # excluído a imagem. Reconfirma que ela ainda está ativa IMEDIATAMENTE antes
    # de ler o arquivo e chamar o motor; se não, encerra como falha sem enviar
    # nada ao motor.
    still_active = (
        _active_images_query(db, answer.id)
        .filter(AnswerImage.id == image.id)
        .first()
    )
    if still_active is None:
        data = _extraction_failure("A imagem deixou de estar ativa antes da extração; nada foi enviado ao motor.")
        error_code_no_longer_active = True
    else:
        error_code_no_longer_active = False
        try:
            image_base64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        except OSError:
            data = _extraction_failure("Falha ao ler o arquivo da imagem no armazenamento.")
        else:
            try:
                data = await _call_ai_engine_extract(image_base64, image.content_type)
            except asyncio.CancelledError:
                # ALTA-8: cancelamento durante a chamada externa não pode deixar
                # o registro 'processando' órfão. Finaliza como 'falha' e re-levanta.
                stale = db.get(TranscriptionExtraction, extraction_id)
                if stale is not None and stale.status == _EXTRACTION_PROCESSING:
                    stale.status = "falha"
                    stale.error_detail = "CANCELADO"
                    db.commit()
                raise
    status, text, model, duration_ms, error_detail = _normalize_extraction(data)
    if error_code_no_longer_active:
        error_detail = "IMAGE_NO_LONGER_ACTIVE"

    extraction = db.get(TranscriptionExtraction, extraction_id)
    assert extraction is not None  # recém-criado nesta mesma função
    extraction.status = status
    # raw_output fiel (MÉDIA-7): preserva a saída do motor SEM strip. O strip
    # é aplicado só ao derivar o rascunho, mais abaixo.
    extraction.raw_output = text
    extraction.model = model
    extraction.duration_ms = duration_ms
    extraction.error_detail = error_detail

    # Rascunho só é preenchido se estiver VAZIO, com o mesmo lock otimista do
    # rascunho manual (+1 em transcription_version); nunca confirma.
    answer = _lock_answer_row(db, answer_id)
    draft_updated = False
    message_key = status
    # ALTA-2 (fecho do TOCTOU residual): sob o lock do answer, revalida que a
    # imagem usada ainda está ativa ANTES de aplicar o resultado. Se foi excluída
    # durante a inferência, o texto NÃO é aplicado ao rascunho (resultado órfão de
    # imagem inativa não contamina a transcrição). A limitação de não manter lock
    # DURANTE a inferência (chamada longa) é intencional; o resultado só é aceito
    # se a imagem seguir ativa neste ponto.
    image_still_active_now = (
        _active_images_query(db, answer.id).filter(AnswerImage.id == image.id).first() is not None
    )
    if status == "ok" and not image_still_active_now:
        status = "falha"
        message_key = "falha"
        # Contrato: fora de 'ok' não há texto. Zera também text/raw_output para
        # não devolver nem persistir conteúdo sob status 'falha'.
        text = ""
        extraction.status = "falha"
        extraction.raw_output = ""
        extraction.error_detail = "IMAGE_NO_LONGER_ACTIVE"
    elif status == "ok":
        message_key = "draft_kept"
        if answer.transcription_status != TranscriptionStatus.AGUARDANDO_TRANSCRICAO:
            message_key = "answer_changed"
        elif not (answer.manual_transcription_draft or "").strip():
            version = answer.transcription_version
            # O rascunho recebe o texto COM strip (limpo para edição humana); o
            # raw_output da extração permanece fiel (MÉDIA-7).
            draft_text = text.strip()
            result = db.execute(
                update(Answer)
                .where(
                    Answer.id == answer.id,
                    Answer.transcription_version == version,
                    Answer.transcription_status == TranscriptionStatus.AGUARDANDO_TRANSCRICAO,
                    or_(Answer.manual_transcription_draft.is_(None), Answer.manual_transcription_draft == ""),
                )
                .values(manual_transcription_draft=draft_text, transcription_version=Answer.transcription_version + 1)
                .execution_options(synchronize_session=False)
            )
            draft_updated = result.rowcount == 1
            message_key = "draft_updated" if draft_updated else "answer_changed"
            if draft_updated:
                # Proveniência REAL (ALTA-4/5): registra a versão RESULTANTE que
                # esta extração produziu. A origem do rascunho passa a ser
                # derivada por VERSÃO, não por coincidência de texto.
                extraction.resulting_transcription_version = version + 1
                # Origem OCR do rascunho também fica na trilha de auditoria.
                db.add(
                    AuditEvent(
                        actor_id=user.id,
                        action="transcription_draft_filled_by_extraction",
                        resource_type="Answer",
                        resource_id=answer.id,
                        before_json=json.dumps(
                            {"manual_transcription_draft": None, "transcription_version": version}
                        ),
                        after_json=json.dumps(
                            {
                                "draft_origin": _EXTRACTION_DRAFT_ORIGIN,
                                "extraction_id": extraction_id,
                                "transcription_version": version + 1,
                            }
                        ),
                    )
                )
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="transcription_extraction_finished",
            resource_type="TranscriptionExtraction",
            resource_id=extraction_id,
            after_json=json.dumps(
                {
                    "answer_id": answer_id,
                    "answer_image_id": image.id,
                    "status": status,
                    "model": model,
                    "duration_ms": duration_ms,
                    "text_length": len(text),
                    "draft_updated": draft_updated,
                }
            ),
        )
    )
    db.commit()
    db.refresh(answer)
    log_event(
        "transcription_extraction_finished",
        correlation_id,
        answer_id=answer_id,
        extraction_id=extraction_id,
        status=status,
        duration_ms=duration_ms,
        text_length=len(text),
        draft_updated=draft_updated,
    )
    message = _EXTRACTION_MESSAGES[message_key]
    if requested_image_id is not None and len(active_images) > 1:
        message += " Foi usada a imagem que você indicou explicitamente."
    return TranscriptionExtractionOut(
        extraction_id=extraction_id,
        status=status,
        extracted_text=text,
        draft_updated=draft_updated,
        draft_origin=_EXTRACTION_DRAFT_ORIGIN if draft_updated else None,
        answer_image_id=image.id,
        transcription_version=answer.transcription_version,
        message=message,
    )


# Retomada da extração após reload (AV-S07B, lacuna A). SOMENTE LEITURA:
# autorizada por propriedade (como list_image_answers), sem exigir vínculo
# ativo, e nunca altera rascunho, versão nem transcrição confirmada.
_EXTRACTION_RAW_TEXT_LIMIT = 20_000


@app.get(
    "/v1/answers/{answer_id}/transcription/extractions", response_model=TranscriptionExtractionStateOut
)
def get_transcription_extraction_state(
    answer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    _get_owned_assessment(db, question.assessment_id, user)

    extractions = db.query(TranscriptionExtraction).filter(TranscriptionExtraction.answer_id == answer.id)
    latest = extractions.order_by(
        TranscriptionExtraction.created_at.desc(), TranscriptionExtraction.id.desc()
    ).first()

    draft = answer.manual_transcription_draft or ""
    if answer.transcription_status == TranscriptionStatus.TRANSCRICAO_CONFIRMADA:
        text_state = "CONFIRMADA"
    elif draft.strip():
        text_state = "RASCUNHO"
    else:
        text_state = "VAZIO"

    draft_origin = None
    source = None
    if text_state == "RASCUNHO":
        # Proveniência por VERSÃO (ALTA-4/5), nunca por coincidência de texto.
        # Procura a extração que preencheu o rascunho em alguma versão.
        current_version = answer.transcription_version
        ocr_exact = (
            extractions.filter(
                TranscriptionExtraction.resulting_transcription_version == current_version
            )
            .order_by(TranscriptionExtraction.created_at.desc(), TranscriptionExtraction.id.desc())
            .first()
        )
        last_filled = (
            extractions.filter(TranscriptionExtraction.resulting_transcription_version.isnot(None))
            .order_by(
                TranscriptionExtraction.resulting_transcription_version.desc(),
                TranscriptionExtraction.created_at.desc(),
                TranscriptionExtraction.id.desc(),
            )
            .first()
        )
        if ocr_exact is not None:
            # A versão atual do rascunho é EXATAMENTE a que a extração produziu e
            # não foi editada desde então: origem OCR.
            draft_origin = _EXTRACTION_DRAFT_ORIGIN
            source = ocr_exact
        elif (
            last_filled is not None
            and last_filled.resulting_transcription_version is not None
            and current_version > last_filled.resulting_transcription_version
        ):
            # Uma extração preencheu o rascunho e o humano editou depois
            # (a versão avançou além da preenchida por OCR): OCR_EDITADO.
            draft_origin = f"{_EXTRACTION_DRAFT_ORIGIN}_EDITADO"
            source = last_filled
        else:
            # Nenhuma extração preencheu a versão atual nem uma anterior
            # relacionada: rascunho digitado manualmente. Coincidência de texto
            # com um raw_output histórico NÃO conta como OCR.
            draft_origin = "MANUAL"

    latest_out = None
    if latest is not None:
        raw = latest.raw_output or ""
        latest_out = LatestTranscriptionExtractionOut(
            extraction_id=latest.id,
            status=latest.status,
            created_at=latest.created_at,
            model=latest.model,
            image_id=latest.answer_image_id,
            has_raw_output=bool(raw),
            raw_text=raw[:_EXTRACTION_RAW_TEXT_LIMIT],
            raw_text_truncated=len(raw) > _EXTRACTION_RAW_TEXT_LIMIT,
            error_detail=latest.error_detail,
        )
    return TranscriptionExtractionStateOut(
        answer_id=answer.id,
        transcription_status=answer.transcription_status.value,
        transcription_version=answer.transcription_version,
        text_state=text_state,
        draft_origin=draft_origin,
        draft_source_extraction_id=source.id if source is not None else None,
        draft_source_raw_text=(source.raw_output or "")[:_EXTRACTION_RAW_TEXT_LIMIT] if source is not None else None,
        latest_extraction=latest_out,
    )


# ---------------- Corrections ----------------
def _serialize_job(db: Session, job: CorrectionJob) -> CorrectionJobOut:
    latest_exec = (
        db.query(AIExecution).filter(AIExecution.job_id == job.id).order_by(AIExecution.created_at.desc()).first()
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
        id=job.id,
        answer_id=job.answer_id,
        status=job.status.value,
        attempt=job.attempt,
        error_message=job.error_message,
        latest_execution=latest_out,
    )


def _get_job_context(db: Session, job_id: str, user: User) -> tuple[CorrectionJob, Answer, Question, Assessment]:
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
    answer_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    question = db.get(Question, answer.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    assessment = _get_owned_assessment(db, question.assessment_id, user)
    require_assessment_mutation(db, user, assessment)
    # Guard após a autorização, para não revelar o estado da resposta a quem
    # não tem acesso; antes de qualquer CorrectionJob (DEC-AV-037).
    if (
        answer.transcription_status != TranscriptionStatus.TRANSCRICAO_CONFIRMADA
        or not (answer.text or "").strip()
    ):
        return error_response(
            422,
            "ANSWER_NOT_TRANSCRIBED",
            "A resposta por imagem ainda não tem transcrição confirmada; não pode ser corrigida.",
            correlation_id,
        )
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
    job_id: str,
    db: Session = Depends(get_db),
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
        item["criterion_id"]: Decimal(str(item["score"])) for item in json.loads(review.final_scores_json)
    }
    attempted_scores = {item["criterion_id"]: Decimal(str(item["score"])) for item in final_scores}
    return (
        review.reviewer_id == reviewer_id
        and review.decision == decision
        and existing_scores == attempted_scores
        and (review.justification or "") == (justification or "")
    )


def _review_conflict_response(db: Session, review: HumanReview, correlation_id: str) -> JSONResponse:
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
    job_id: str,
    payload: HumanReviewInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    correlation_id = getattr(request.state, "correlation_id", new_correlation_id())
    job, _, _, assessment = _get_job_context(db, job_id, user)
    require_assessment_mutation(db, user, assessment)

    if payload.decision not in (ReviewDecision.APPROVE.value, ReviewDecision.ALTER.value):
        return error_response(422, "INVALID_DECISION", "Decisão inválida.", correlation_id)

    latest_exec = (
        db.query(AIExecution).filter(AIExecution.job_id == job_id).order_by(AIExecution.created_at.desc()).first()
    )
    scores_by_criterion = {}
    if latest_exec:
        for s in db.query(CriterionScore).filter(CriterionScore.ai_execution_id == latest_exec.id).all():
            scores_by_criterion[s.criterion_id] = s

    if payload.decision == ReviewDecision.ALTER.value:
        if not payload.justification or not payload.justification.strip():
            return error_response(
                422,
                "JUSTIFICATION_REQUIRED",
                "Justificativa é obrigatória para alterar a nota.",
                correlation_id,
            )
        final_scores = []
        total = Decimal("0")
        for cs in payload.criteria_scores:
            ref = scores_by_criterion.get(cs.criterion_id)
            max_score = ref.max_score if ref else Decimal("0")
            score = cs.score
            if score < 0 or score > max_score:
                return error_response(
                    422,
                    "SCORE_OUT_OF_RANGE",
                    f"Pontuação do critério {cs.criterion_id} deve estar entre 0 e {max_score}.",
                    correlation_id,
                )
            final_scores.append({"criterion_id": cs.criterion_id, "score": str(round_score(score))})
            total += score
        final_total = round_score(total)
    else:
        final_scores = [{"criterion_id": cid, "score": str(s.score)} for cid, s in scores_by_criterion.items()]
        final_total = round_score(sum((s.score for s in scores_by_criterion.values()), Decimal("0")))

    decision = ReviewDecision(payload.decision)
    existing_review = db.query(HumanReview).filter(HumanReview.job_id == job_id).first()
    if existing_review is not None:
        if _review_is_equivalent(existing_review, user.id, decision, final_scores, payload.justification):
            return existing_review
        return _review_conflict_response(db, existing_review, correlation_id)

    review = HumanReview(
        job_id=job_id,
        reviewer_id=user.id,
        decision=decision,
        final_total=final_total,
        final_scores_json=json.dumps(final_scores),
        justification=payload.justification,
    )
    db.add(review)
    db.add(
        AuditEvent(
            actor_id=user.id,
            action=f"REVIEW_{payload.decision}",
            resource_type="CorrectionJob",
            resource_id=job_id,
            before_json=json.dumps({cid: str(s.score) for cid, s in scores_by_criterion.items()}),
            after_json=json.dumps(final_scores),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_review = db.query(HumanReview).filter(HumanReview.job_id == job_id).first()
        if existing_review is None:
            raise
        if _review_is_equivalent(existing_review, user.id, decision, final_scores, payload.justification):
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
