import os
import threading
import httpx as requests
import time

BASE = "http://127.0.0.1:8010/v1"
prof_email = "revisor.pg@example.com"
prof_pw = os.environ["AV_TEST_PASSWORD"]  # senha fictícia de banco de teste isolado, nunca hardcoded


def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": prof_email, "password": prof_pw})
    return r.json()["access_token"]


def build_job(token, tag):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{BASE}/assessments",
        json={
            "title": f"Avaliação PG isolado - conflito {tag}",
            "question": {
                "statement": "Explique pilha vs fila (conflito)",
                "reference_answer": "Resposta ref",
                "max_score": "2.00",
            },
        },
        headers=h,
    )
    body = r.json()
    question_id = body["questions"][0]["id"]
    requests.post(
        f"{BASE}/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "description": "Critério 1", "max_score": "2.00"}]},
        headers=h,
    )
    requests.post(f"{BASE}/assessments/{body['id']}/publish", headers=h)
    r = requests.post(
        f"{BASE}/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Conflito", "text": "Resposta ficticia"},
        headers=h,
    )
    answer_id = r.json()["id"]
    r = requests.post(f"{BASE}/answers/{answer_id}/corrections", headers=h)
    job_id = r.json()["id"]
    for _ in range(20):
        r = requests.get(f"{BASE}/correction-jobs/{job_id}", headers=h)
        if r.json().get("status") in ("SUGERIDA", "FALHA"):
            break
        time.sleep(0.5)
    return job_id, h


def main():
    token = login()
    job_id, h = build_job(token, "mix")
    print("JOB_ID:", job_id)

    results = []
    lock = threading.Lock()

    def worker(payload):
        with requests.Client() as client:
            r = client.post(f"{BASE}/corrections/{job_id}/reviews", json=payload, headers=h)
            with lock:
                results.append((r.status_code, r.json()))

    payloads = []
    for i in range(6):
        if i % 2 == 0:
            payloads.append({"decision": "APPROVE", "final_scores": [], "justification": None})
        else:
            payloads.append({"decision": "ALTER", "final_scores": [{"criterion_id": "x", "score": "0.50"}], "justification": "Divergente"})

    threads = [threading.Thread(target=worker, args=(p,)) for p in payloads]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("RESULTS:")
    for status, body in results:
        print(" ", status, body.get("decision") if status == 200 else body.get("code"))

    statuses = sorted(s for s, _ in results)
    print("STATUS_COUNTS:", {s: statuses.count(s) for s in set(statuses)})


if __name__ == "__main__":
    main()
