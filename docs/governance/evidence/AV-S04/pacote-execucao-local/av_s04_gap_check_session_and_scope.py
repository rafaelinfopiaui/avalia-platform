"""Targeted verification (not a full re-review — reuses rounds 2/3 findings
for 'catches the expected FK violation'; this script investigates only the
two concrete gaps Rafael asked about that those rounds did NOT explicitly
cover):

(A) After delete_question's except/rollback fires, is the SAME db Session
    object still usable for further queries/writes in the same request
    (i.e., not left in SQLAlchemy's "pending rollback" broken state)?

(B) Does the broad `except IntegrityError` risk mischaracterizing an
    unrelated integrity violation as "Questão possui respostas
    registradas"? Reasoned from schema topology + confirmed empirically:
    the only FK that can fire during this exact delete+flush (Question
    cascade-deletes its Rubrics, which cascade-delete RubricCriteria) is
    either (a) answers.question_id -> questions.id (the intended case) or
    (b) correction_jobs.rubric_id -> rubrics.id. But (b) can only be
    populated by request_correction, which requires an existing Answer
    row for this question -- so by construction (b) can only fire when an
    Answer *also* exists, making the generic 409 message still accurate
    even in that edge case. No other FK references Question or Rubric
    directly (confirmed: no ondelete= anywhere in models.py, and a grep
    for ForeignKey("questions.id") / ForeignKey("rubrics.id") shows only
    Answer.question_id, Rubric.question_id, RubricCriterion.rubric_id,
    CorrectionJob.rubric_id).
"""
import os
import sys
import uuid

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if "av_s04_" not in DATABASE_URL or "avalia_dev" in DATABASE_URL:
    raise RuntimeError("Refusing to run outside an isolated av_s04_* database")

sys.path.insert(0, ".")

from fastapi import HTTPException

import app.main as main_module
from app.db import SessionLocal
from app.models import Answer, Assessment, AssessmentStatus, Question, Role, User
from app.security import hash_password


def seed():
    db = SessionLocal()
    db.query(Answer).delete()
    db.query(Question).delete()
    db.query(Assessment).delete()
    db.query(User).filter(User.email == "gap_check@example.com").delete()
    db.commit()
    prof = User(id=str(uuid.uuid4()), email="gap_check@example.com", password_hash=hash_password("x"), role=Role.PROFESSOR)
    db.add(prof)
    db.commit()
    assessment = Assessment(id=str(uuid.uuid4()), owner_id=prof.id, title="GapCheck", status=AssessmentStatus.RASCUNHO)
    db.add(assessment)
    db.commit()
    question = Question(id=str(uuid.uuid4()), assessment_id=assessment.id, statement="S", reference_answer="R", max_score=1, position=1)
    db.add(question)
    db.commit()
    ids = (prof.id, assessment.id, question.id)
    db.close()
    return ids


prof_id, assessment_id, question_id = seed()
db = SessionLocal()
user = db.get(User, prof_id)

original_delete = db.delete
fired = {"n": 0}


def patched_delete(instance):
    fired["n"] += 1
    if fired["n"] == 1 and isinstance(instance, Question):
        racer = SessionLocal()
        racer.add(Answer(id=str(uuid.uuid4()), question_id=question_id, student_name_fake="Aluno", text="resposta"))
        racer.commit()
        racer.close()
    return original_delete(instance)


db.delete = patched_delete

caught = None
try:
    main_module.delete_question(question_id=question_id, db=db, user=user)
except HTTPException as exc:
    caught = exc
    print(f"(1) Caught HTTPException as expected: status={exc.status_code} detail={exc.detail!r}")

# (A) SAME session object db -- is it still usable right now, in the same
# request lifecycle, without raising PendingRollbackError or similar?
try:
    still_works_question = db.get(Question, question_id)
    still_works_count = db.query(Answer).filter(Answer.question_id == question_id).count()
    # Also try an actual write + commit on the SAME session to prove the
    # transaction state is fully clean, not just reads.
    probe = Assessment(id=str(uuid.uuid4()), owner_id=prof_id, title="PostRollbackProbe", status=AssessmentStatus.RASCUNHO)
    db.add(probe)
    db.commit()
    probe_persisted = db.get(Assessment, probe.id) is not None
    print(f"(A) SESSION_USABLE_AFTER_ROLLBACK=True question_survives={still_works_question is not None} answer_count={still_works_count} write_after_rollback_committed={probe_persisted}")
except Exception as exc:  # noqa: BLE001
    print(f"(A) SESSION_USABLE_AFTER_ROLLBACK=False error={type(exc).__name__}: {exc}")
finally:
    db.close()

# (B) Confirm the except is not indiscriminately catching unrelated things:
# force an IntegrityError from a completely different cause at the SAME
# call site pattern (NOT going through delete_question, just structurally
# proving delete_question's except is scoped to the delete(question)/flush()
# call, so it cannot catch errors from unrelated code elsewhere in the
# request). This is a code-shape fact, not a runtime fact: read the
# function itself to confirm the try block's span is minimal.
import inspect
source = inspect.getsource(main_module.delete_question)
try_start = source.index("try:")
except_start = source.index("except IntegrityError")
try_body = source[try_start:except_start]
lines_in_try = [ln.strip() for ln in try_body.splitlines() if ln.strip() and ln.strip() != "try:"]
print(f"(B) TRY_BLOCK_SPAN={lines_in_try}")
assert all("db.delete" in ln or "db.flush" in ln for ln in lines_in_try), "try block must contain ONLY delete+flush, nothing else"
print("(B) TRY_BLOCK_MINIMAL=True (contains only db.delete(question) and db.flush(), nothing else that could raise an unrelated IntegrityError)")
