from __future__ import annotations

import os
import threading
import time

from fastapi.testclient import TestClient

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if "av_s04_migration_" not in DATABASE_URL or "avalia_dev" in DATABASE_URL:
    raise RuntimeError("Refusing to run outside an isolated av_s04_migration_* database")

from app import main as main_module  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import hash_password  # noqa: E402


def require_status(response, expected: int) -> None:
    if response.status_code != expected:
        raise AssertionError(f"expected {expected}, got {response.status_code}: {response.text}")


def main() -> None:
    with SessionLocal() as session:
        session.add(
            User(
                email="av-s04-lock@example.com",
                password_hash=hash_password("Senha123!"),
                role=Role.PROFESSOR,
            )
        )
        session.commit()

    with TestClient(main_module.app) as client:
        login = client.post(
            "/v1/auth/login",
            json={"email": "av-s04-lock@example.com", "password": "Senha123!"},
        )
        require_status(login, 200)
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        created = client.post(
            "/v1/assessments",
            headers=headers,
            json={
                "title": "AV-S04 PostgreSQL row-lock proof",
                "questions": [
                    {
                        "statement": f"Question {number}",
                        "reference_answer": f"Reference {number}",
                        "max_score": 1,
                    }
                    for number in range(1, 6)
                ],
            },
        )
        require_status(created, 201)
        assessment_id = created.json()["id"]
        question_ids = [question["id"] for question in created.json()["questions"]]

        original_lock = main_module._lock_assessment
        counter_guard = threading.Lock()
        first_locked = threading.Event()
        second_entered = threading.Event()
        release_first = threading.Event()
        calls = 0

        def instrumented_lock(db, locked_assessment_id):
            nonlocal calls
            with counter_guard:
                calls += 1
                call_number = calls
            if call_number == 1:
                assessment = original_lock(db, locked_assessment_id)
                first_locked.set()
                if not release_first.wait(timeout=10):
                    raise RuntimeError("timed out waiting to release the first transaction")
                return assessment
            second_entered.set()
            return original_lock(db, locked_assessment_id)

        main_module._lock_assessment = instrumented_lock
        results: dict[str, tuple[int, str]] = {}
        failures: list[BaseException] = []

        def reorder(name: str, order: list[str]) -> None:
            try:
                response = client.put(
                    f"/v1/assessments/{assessment_id}/questions/order",
                    headers=headers,
                    json={"question_ids": order},
                )
                results[name] = (response.status_code, response.text)
            except BaseException as exc:  # retain worker failures for the main thread
                failures.append(exc)

        first = threading.Thread(target=reorder, args=("first", list(reversed(question_ids))))
        second = threading.Thread(target=reorder, args=("second", question_ids[1:] + question_ids[:1]))
        try:
            first.start()
            if not first_locked.wait(timeout=10):
                raise AssertionError("first request never acquired the PostgreSQL row lock")
            second.start()
            if not second_entered.wait(timeout=10):
                raise AssertionError("second request never reached the row-lock acquisition")
            time.sleep(0.75)
            if not second.is_alive():
                raise AssertionError("second reorder completed while first transaction still held FOR UPDATE")
            print("SECOND_REQUEST_BLOCKED_WHILE_FIRST_HELD_LOCK=True")
            release_first.set()
            first.join(timeout=10)
            second.join(timeout=10)
        finally:
            release_first.set()
            main_module._lock_assessment = original_lock

        if first.is_alive() or second.is_alive():
            raise AssertionError("concurrent request thread did not terminate")
        if failures:
            raise AssertionError(f"worker failures: {failures!r}")
        for name in ("first", "second"):
            status, body = results[name]
            if status != 200:
                raise AssertionError(f"{name} reorder failed with {status}: {body}")

        final = client.get(f"/v1/assessments/{assessment_id}", headers=headers)
        require_status(final, 200)
        positions = [question["position"] for question in final.json()["questions"]]
        if positions != [1, 2, 3, 4, 5] or len(set(positions)) != 5:
            raise AssertionError(f"non-contiguous/duplicate final positions: {positions}")
        print(f"REQUEST_STATUSES={[results['first'][0], results['second'][0]]}")
        print(f"FINAL_POSITIONS={positions}")
        print("POSTGRES_FOR_UPDATE_CONCURRENCY_GREEN")


if __name__ == "__main__":
    main()
