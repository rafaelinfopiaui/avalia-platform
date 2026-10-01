"""Deterministic reproduction (RED) and verification (GREEN) of the
delete_question x create_answer TOCTOU race, against real PostgreSQL.

Technique: call delete_question's own logic directly, but monkeypatch the
Answer-existence check query to return None (simulating the window where the
check ran and found nothing), then -- before the function proceeds to
db.delete/flush/commit -- commit a real competing Answer through a second,
independent SQLAlchemy session. This deterministically opens the exact race
window instead of relying on wall-clock thread timing, while still exercising
the real ORM/DB behavior (FK enforcement is only real in Postgres).

Usage:
    DATABASE_URL=postgresql+psycopg2://localhost:5432/<isolated_db> \
    .venv/bin/python av_s04_delete_answer_race.py
"""
from __future__ import annotations

import os
import sys
import uuid

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if "av_s04_" not in DATABASE_URL or "avalia_dev" in DATABASE_URL:
    raise RuntimeError("Refusing to run outside an isolated av_s04_* database")

sys.path.insert(0, ".")

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.main as main_module
from app.db import SessionLocal
from app.models import Answer, Assessment, AssessmentStatus, Question, Role, User
from app.security import hash_password


def seed():
    db = SessionLocal()
    db.query(Answer).delete()
    db.query(Question).delete()
    db.query(Assessment).delete()
    db.query(User).filter(User.email == "race_fn@example.com").delete()
    db.commit()
    prof = User(id=str(uuid.uuid4()), email="race_fn@example.com", password_hash=hash_password("x"), role=Role.PROFESSOR)
    db.add(prof)
    db.commit()
    assessment = Assessment(id=str(uuid.uuid4()), owner_id=prof.id, title="Race", status=AssessmentStatus.RASCUNHO)
    db.add(assessment)
    db.commit()
    question = Question(id=str(uuid.uuid4()), assessment_id=assessment.id, statement="S", reference_answer="R", max_score=1, position=1)
    db.add(question)
    db.commit()
    ids = (prof.id, question.id)
    db.close()
    return ids


def run_once():
    prof_id, question_id = seed()
    db: Session = SessionLocal()
    user = db.get(User, prof_id)

    original_delete = db.delete
    call_count = {"n": 0}

    def patched_delete(instance):
        # This is called by delete_question right after its own Answer
        # existence check already returned "no rows" -- i.e. exactly the
        # TOCTOU window between that check and the physical DELETE. Inject
        # the competing commit from an independent session here, then let
        # the real delete proceed into that now-inconsistent state.
        call_count["n"] += 1
        if call_count["n"] == 1 and isinstance(instance, Question):
            racer = SessionLocal()
            racer.add(Answer(id=str(uuid.uuid4()), question_id=question_id, student_name_fake="Aluno", text="resposta"))
            racer.commit()
            racer.close()
        return original_delete(instance)

    db.delete = patched_delete  # type: ignore[assignment]

    try:
        main_module.delete_question(question_id=question_id, db=db, user=user)
        print("RESULT: delete_question returned normally (204) despite race -> BUG")
        return "no_exception"
    except HTTPException as exc:
        print(f"RESULT: HTTPException status={exc.status_code} detail={exc.detail!r}")
        return f"http_{exc.status_code}"
    except Exception as exc:  # noqa: BLE001
        print(f"RESULT: unhandled {type(exc).__name__}: {exc}")
        return f"unhandled_{type(exc).__name__}"
    finally:
        db.close()
        verify = SessionLocal()
        q_exists = verify.get(Question, question_id) is not None
        a_count = verify.query(Answer).filter(Answer.question_id == question_id).count()
        print(f"POST-STATE: question_exists={q_exists} answer_count={a_count}")
        verify.close()


if __name__ == "__main__":
    outcome = run_once()
    print(f"OUTCOME={outcome}")
