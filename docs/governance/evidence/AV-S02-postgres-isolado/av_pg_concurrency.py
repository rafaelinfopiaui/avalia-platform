import os
import json
import threading
import httpx as requests
import time

BASE = "http://127.0.0.1:8010/v1"
prof_email = "revisor.pg@example.com"
prof_pw = os.environ["AV_TEST_PASSWORD"]  # senha fictícia de banco de teste isolado, nunca hardcoded


def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": prof_email, "password": prof_pw})
    return r.json()["access_token"]


def build_job(token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{BASE}/assessments",
        json={
            "title": "Avaliação PG isolado - concorrencia",
            "question": {
                "statement": "Explique pilha vs fila (concorrencia)",
                "reference_answer": "Resposta ref",
                "max_score": "2.00",
            },
        },
        headers=h,
    )
    body = r.json()
    question_id = body["questions"][0]["id"]

    r = requests.post(
        f"{BASE}/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "description": "Critério 1", "max_score": "2.00"}]},
        headers=h,
    )

    r = requests.post(f"{BASE}/assessments/{body['id']}/publish", headers=h)

    r = requests.post(
        f"{BASE}/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Concorrencia", "text": "Resposta ficticia"},
        headers=h,
    )
    answer_id = r.json()["id"]

    r = requests.post(f"{BASE}/answers/{answer_id}/corrections", headers=h)
    job_id = r.json()["id"]

    for _ in range(20):
        r = requests.get(f"{BASE}/correction-jobs/{job_id}", headers=h)
        status = r.json().get("status")
        if status in ("SUGERIDA", "FALHA"):
            break
        time.sleep(0.5)

    return job_id, h


def main():
    token = login()
    job_id, h = build_job(token)
    print("JOB_ID:", job_id)

    payload = {"decision": "APPROVE", "final_scores": [], "justification": None}
    results = []
    lock = threading.Lock()

    def worker():
        with requests.Client() as client:
            r = client.post(f"{BASE}/corrections/{job_id}/reviews", json=payload, headers=h)
            with lock:
                results.append((r.status_code, r.json().get("id")))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("RESULTS:")
    for status, rid in results:
        print(" ", status, rid)

    ids = set(rid for _, rid in results)
    print("DISTINCT_REVIEW_IDS:", ids)
    print("ALL_STATUS_200:", all(s == 200 for s, _ in results))


if __name__ == "__main__":
    main()
