from __future__ import annotations
import json
from decimal import Decimal, ROUND_HALF_EVEN

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging_utils import log_event
from app.models import (
    Answer, CorrectionJob, JobStatus, Rubric, RubricCriterion,
    AIExecution, CriterionScore, AuditEvent,
)

settings = get_settings()

DECIMAL_QUANT = Decimal("0.01")


def round_score(value: Decimal) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_EVEN)


async def run_correction_job(job_id: str, session_factory) -> None:
    """Executa um CorrectionJob de forma assíncrona in-process (ADR-006).

    Chama o AI Engine local via HTTP. Nunca fabrica resultado quando o AI
    Engine está indisponível — o job vai para FALHA (RN-017).
    """
    db: Session = session_factory()
    correlation_id = f"job-{job_id}"
    try:
        job = db.get(CorrectionJob, job_id)
        if job is None:
            return
        job.status = JobStatus.PROCESSANDO
        db.commit()

        answer = db.get(Answer, job.answer_id)
        rubric = db.get(Rubric, job.rubric_id)
        question = rubric.question
        criteria: list[RubricCriterion] = rubric.criteria

        payload = {
            "question_statement": question.statement,
            "reference_answer": question.reference_answer,
            "rubric": [
                {
                    "criterion_id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "max_score": float(c.max_score),
                }
                for c in criteria
            ],
            "answer_text": answer.text,
        }

        log_event(
            "correction_job_started", correlation_id, job_id=job_id,
            answer_text_len=len(answer.text or ""),
        )

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(f"{settings.ai_engine_url}/v1/analyze", json=payload)
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:  # noqa: BLE001 - queremos capturar qualquer falha de rede/timeout
            job.status = JobStatus.FALHA
            job.error_message = (
                "Não foi possível analisar esta resposta. AI Engine indisponível. "
                "Encaminhe para correção manual ou tente novamente."
            )
            db.add(AuditEvent(
                actor_id=None, action="AI_ENGINE_UNAVAILABLE", resource_type="CorrectionJob",
                resource_id=job_id, before_json=None,
                after_json=json.dumps({"error": str(exc)}),
            ))
            db.commit()
            log_event("correction_job_failed_engine_unavailable", correlation_id, job_id=job_id, error=str(exc))
            return

        # Core NUNCA confia cegamente no total vindo da IA (RN-009): recalcula
        # a partir dos criterion_scores, e valida/clampa limites (0..max_score).
        ai_execution = AIExecution(
            job_id=job_id,
            engine_mode=result.get("engine_mode", "real"),
            model=result.get("model", ""),
            confidence_method_version=result.get("confidence_method_version", ""),
            overall_confidence=Decimal(str(result.get("overall_confidence", 0))),
            review_recommendation=result.get("review_recommendation", "REVIEW_REQUIRED"),
            duration_ms=int(result.get("duration_ms", 0)),
            flags=json.dumps(result.get("flags", [])),
            raw_output_json=json.dumps(result, ensure_ascii=False),
        )
        db.add(ai_execution)
        db.flush()

        criteria_by_id = {c.id: c for c in criteria}
        for cs in result.get("criterion_scores", []):
            criterion = criteria_by_id.get(cs.get("criterion_id"))
            max_score = criterion.max_score if criterion else Decimal(str(cs.get("max_score", 0)))
            raw_score = Decimal(str(cs.get("score", 0)))
            clamped = False
            if raw_score < 0:
                raw_score = Decimal("0")
                clamped = True
            if raw_score > max_score:
                raw_score = max_score
                clamped = True
            score = round_score(raw_score)
            db.add(CriterionScore(
                ai_execution_id=ai_execution.id,
                criterion_id=cs.get("criterion_id", ""),
                score=score,
                max_score=max_score,
                reason=cs.get("reason", ""),
                evidence=cs.get("evidence", ""),
                confidence=Decimal(str(cs.get("confidence", 0))),
                was_clamped=clamped,
            ))
            if clamped:
                log_event(
                    "criterion_score_clamped", correlation_id, job_id=job_id,
                    criterion_id=cs.get("criterion_id"), raw_score=str(cs.get("score")),
                    max_score=str(max_score),
                )

        job.status = JobStatus.SUGERIDA
        db.commit()
        log_event(
            "correction_job_completed", correlation_id, job_id=job_id,
            engine_mode=ai_execution.engine_mode, overall_confidence=str(ai_execution.overall_confidence),
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.get(CorrectionJob, job_id)
        if job:
            job.status = JobStatus.FALHA
            job.error_message = f"Erro inesperado no processamento: {exc}"
            db.commit()
        log_event("correction_job_unexpected_error", correlation_id, job_id=job_id, error=str(exc))
    finally:
        db.close()
