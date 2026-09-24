import os
import json
import threading
import httpx as requests

BASE = "http://127.0.0.1:8010/v1"
prof_email = "revisor.pg@example.com"
prof_pw = os.environ["AV_TEST_PASSWORD"]  # senha fictícia de banco de teste isolado, nunca hardcoded

def register_and_login():
    r = requests.post(f"{BASE}/auth/login", json={"email": prof_email, "password": prof_pw})
    print("login:", r.status_code)
    return r.json()["access_token"]

def build_job(token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{BASE}/assessments",
        json={
            "title": "Avaliação PG isolado",
            "question": {
                "statement": "Explique pilha vs fila",
                "reference_answer": "Resposta ref",
                "max_score": "2.00",
            },
        },
        headers=h,
    )
    print("create assessment+question:", r.status_code, r.text[:300])
    body = r.json()
    assessment_id = body["id"]
    question_id = body["questions"][0]["id"]

    r = requests.post(
        f"{BASE}/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "description": "Critério 1", "max_score": "2.00"}]},
        headers=h,
    )
    print("create rubric:", r.status_code, r.text[:200])

    r = requests.post(f"{BASE}/assessments/{assessment_id}/publish", headers=h)
    print("publish:", r.status_code, r.text[:200])

    r = requests.post(
        f"{BASE}/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno PG Isolado", "text": "Resposta ficticia do aluno"},
        headers=h,
    )
    print("create answer:", r.status_code, r.text[:200])
    answer_id = r.json()["id"]

    r = requests.post(f"{BASE}/answers/{answer_id}/corrections", headers=h)
    print("request correction:", r.status_code, r.text[:200])
    job_id = r.json()["id"]

    import time
    for _ in range(20):
        r = requests.get(f"{BASE}/correction-jobs/{job_id}", headers=h)
        status = r.json().get("status")
        print("poll job status:", status)
        if status in ("SUGERIDA", "FALHA"):
            break
        time.sleep(0.5)

    return job_id, h

def main():
    token = register_and_login()
    job_id, h = build_job(token)

    print("\n=== TESTE: reenvio equivalente (mesma decisao 2x) ===")
    payload = {"decision": "APPROVE", "final_scores": [], "justification": None}
    r1 = requests.post(f"{BASE}/corrections/{job_id}/reviews", json=payload, headers=h)
    print("1a submissao:", r1.status_code, r1.text[:300])
    r2 = requests.post(f"{BASE}/corrections/{job_id}/reviews", json=payload, headers=h)
    print("2a submissao (equivalente):", r2.status_code, r2.text[:300])

    print("\n=== TESTE: decisao conflitante ===")
    conflicting = {"decision": "ALTER", "final_scores": [], "justification": "Mudei de ideia"}
    r3 = requests.post(f"{BASE}/corrections/{job_id}/reviews", json=conflicting, headers=h)
    print("submissao conflitante:", r3.status_code, r3.text[:400])

    print("\n=== TESTE: contexto mostra decisao persistida ===")
    r4 = requests.get(f"{BASE}/correction-jobs/{job_id}/context", headers=h)
    print("context:", r4.status_code)
    ctx = r4.json()
    print("human_review:", json.dumps(ctx.get("human_review"), indent=2, ensure_ascii=False))

    print(f"\nJOB_ID_FOR_CONCURRENCY={job_id}")

if __name__ == "__main__":
    main()
