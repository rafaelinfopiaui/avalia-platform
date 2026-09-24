from decimal import Decimal


def _create_published_assessment(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/v1/assessments",
        json={
            "title": "Estruturas de Dados",
            "question": {
                "statement": "Explique pilha e fila.",
                "reference_answer": "Pilha é LIFO, fila é FIFO.",
                "max_score": 6.0,
            },
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assessment = resp.json()
    question_id = assessment["questions"][0]["id"]
    return assessment, question_id


def test_access_without_token_is_blocked(client):
    resp = client.get("/v1/assessments")
    assert resp.status_code == 401


def test_access_with_token_but_wrong_role_is_blocked(client, test_engine):
    # cria usuário aluno (role inexistente no enum -> simula acesso indevido criando token manualmente)
    from app.security import create_access_token
    fake_token = create_access_token("nao-existe", "professor")
    headers = {"Authorization": f"Bearer {fake_token}"}
    resp = client.get("/v1/me", headers=headers)
    assert resp.status_code == 401  # usuário não existe no banco


def test_publish_with_rubric_total_mismatch_is_rejected(client, professor_token):
    headers = {"Authorization": f"Bearer {professor_token}"}
    _, question_id = _create_published_assessment(client, professor_token)

    resp = client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "max_score": 2.0}, {"name": "C2", "max_score": 2.0}]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    assessment_id = client.get("/v1/assessments", headers=headers).json()[0]["id"]
    resp = client.post(f"/v1/assessments/{assessment_id}/publish", headers=headers)
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "RUBRIC_TOTAL_MISMATCH"


def test_publish_succeeds_when_rubric_matches(client, professor_token):
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)

    resp = client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [
            {"name": "C1", "max_score": 1.5}, {"name": "C2", "max_score": 1.5},
            {"name": "C3", "max_score": 1.5}, {"name": "C4", "max_score": 1.5},
        ]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)
    assert resp.status_code == 200, resp.text


def test_ai_engine_unavailable_does_not_fabricate_result(client, professor_token):
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)
    client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [
            {"name": "C1", "max_score": 1.5}, {"name": "C2", "max_score": 1.5},
            {"name": "C3", "max_score": 1.5}, {"name": "C4", "max_score": 1.5},
        ]},
        headers=headers,
    )
    client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)

    resp = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Ficticio", "text": "Resposta de teste."},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    answer_id = resp.json()["id"]

    resp = client.post(f"/v1/answers/{answer_id}/corrections", headers=headers)
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["job_id"]

    import time
    for _ in range(50):
        job = client.get(f"/v1/correction-jobs/{job_id}", headers=headers).json()
        if job["status"] in ("SUGERIDA", "FALHA"):
            break
        time.sleep(0.3)

    assert job["status"] == "FALHA", job
    assert job["error_message"] is not None
    assert (
        "manual" in job["error_message"].lower()
        or "indispon" in job["error_message"].lower()
        or "tente" in job["error_message"].lower()
    )


def test_human_review_persists_with_reviewer(client, professor_token, test_engine):
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)
    client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [
            {"name": "C1", "max_score": 3.0}, {"name": "C2", "max_score": 3.0},
        ]},
        headers=headers,
    )
    client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)

    resp = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno X", "text": "Texto."},
        headers=headers,
    )
    answer_id = resp.json()["id"]

    from sqlalchemy.orm import sessionmaker

    from app.models import AIExecution, CorrectionJob, CriterionScore, JobStatus, Rubric
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    rubric = session.query(Rubric).filter(Rubric.question_id == question_id).first()
    job = CorrectionJob(answer_id=answer_id, rubric_id=rubric.id, status=JobStatus.SUGERIDA, attempt=1)
    session.add(job)
    session.flush()
    ai_exec = AIExecution(
        job_id=job.id, engine_mode="real", model="qwen2.5:7b-instruct-q4_K_M",
        confidence_method_version="heuristic-v1", overall_confidence=Decimal("0.9"),
        review_recommendation="REVIEW_OPTIONAL",
    )
    session.add(ai_exec)
    session.flush()
    for c in rubric.criteria:
        session.add(CriterionScore(
            ai_execution_id=ai_exec.id, criterion_id=c.id, score=c.max_score,
            max_score=c.max_score, reason="sugestão inicial", evidence="", confidence=Decimal("0.9"),
        ))
    session.commit()
    job_id = job.id
    criteria_ids = [c.id for c in rubric.criteria]
    session.close()

    resp = client.post(
        f"/v1/corrections/{job_id}/reviews",
        json={
            "decision": "ALTER",
            "criteria_scores": [
                {"criterion_id": criteria_ids[0], "score": 2.0},
                {"criterion_id": criteria_ids[1], "score": 1.0},
            ],
            "justification": "Ajustei porque a resposta não cobriu todos os pontos.",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision"] == "ALTER"
    assert Decimal(str(body["final_total"])) == Decimal("3.00")
    assert body["reviewer_id"] is not None


def test_criterion_score_out_of_range_is_rejected(client, professor_token, test_engine):
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)
    client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "max_score": 2.0}]},
        headers=headers,
    )
    client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)
    resp = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Y", "text": "Texto."},
        headers=headers,
    )
    answer_id = resp.json()["id"]

    from sqlalchemy.orm import sessionmaker

    from app.models import CorrectionJob, JobStatus, Rubric
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    rubric = session.query(Rubric).filter(Rubric.question_id == question_id).first()
    job = CorrectionJob(answer_id=answer_id, rubric_id=rubric.id, status=JobStatus.SUGERIDA, attempt=1)
    session.add(job)
    session.commit()
    job_id = job.id
    criterion_id = rubric.criteria[0].id
    session.close()

    resp = client.post(
        f"/v1/corrections/{job_id}/reviews",
        json={
            "decision": "ALTER",
            "criteria_scores": [{"criterion_id": criterion_id, "score": 99.0}],
            "justification": "Tentativa fora do limite.",
        },
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "SCORE_OUT_OF_RANGE"


def test_reprocessing_preserves_previous_versions(client, professor_token, test_engine):
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)
    client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "max_score": 6.0}]},
        headers=headers,
    )
    client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)
    resp = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Z", "text": "Texto."},
        headers=headers,
    )
    answer_id = resp.json()["id"]

    # Solicita duas correções (duas tentativas) -- ambas falharão (AI Engine indisponível
    # no ambiente de teste), mas cada uma cria um CorrectionJob distinto e preserva o anterior.
    resp1 = client.post(f"/v1/answers/{answer_id}/corrections", headers=headers)
    resp2 = client.post(f"/v1/answers/{answer_id}/corrections", headers=headers)
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["job_id"] != resp2.json()["job_id"]


def test_correction_creation_response_has_id_for_polling(client, professor_token):
    """Regressão do bug 'Análise na fila... Não foi possível concluir a operação':
    o frontend trata a resposta de POST /answers/{id}/corrections como um
    CorrectionJob (mesmo formato de GET /correction-jobs/{id}, que usa a chave
    "id") e navega para /correcoes/{job.id}. Quando este endpoint retornava
    apenas "job_id" (sem "id"), o frontend navegava para "/correcoes/undefined"
    e o polling seguinte recebia 404 mesmo com o job sendo processado com
    sucesso no backend. Este teste trava que "id" e "job_id" estejam sempre
    presentes e coincidam, e que GET /correction-jobs/{id} aceite exatamente
    esse valor.
    """
    headers = {"Authorization": f"Bearer {professor_token}"}
    assessment, question_id = _create_published_assessment(client, professor_token)
    client.post(
        f"/v1/questions/{question_id}/rubric",
        json={"criteria": [{"name": "C1", "max_score": 6.0}]},
        headers=headers,
    )
    client.post(f"/v1/assessments/{assessment['id']}/publish", headers=headers)
    resp = client.post(
        "/v1/answers",
        json={"question_id": question_id, "student_name_fake": "Aluno Regressao", "text": "Texto."},
        headers=headers,
    )
    answer_id = resp.json()["id"]

    resp = client.post(f"/v1/answers/{answer_id}/corrections", headers=headers)
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert "id" in body and body["id"], (
        "resposta de criação do job precisa expor 'id' (usado pelo frontend para navegar/pollar)"
    )
    assert body["id"] == body["job_id"]

    # A rota de polling usada pelo frontend precisa aceitar exatamente esse id.
    follow_up = client.get(f"/v1/correction-jobs/{body['id']}", headers=headers)
    assert follow_up.status_code == 200, follow_up.text
    assert follow_up.json()["id"] == body["id"]


def test_seed_professor_email_is_a_valid_email_syntax():
    """Regressão: SEED_PROFESSOR_EMAIL não pode usar domínio IANA "special-use"
    (local/test/invalid/onion/arpa/localhost). LoginRequest usa pydantic.EmailStr,
    que rejeita esses domínios com HTTP 422 antes de checar a senha -- travando o
    login de demonstração mesmo com credenciais corretas no banco. Ver
    core/app/config.py e docs/roteiro-demo.md.
    """
    from email_validator import validate_email

    from app.config import get_settings

    settings = get_settings()
    # Não deve levantar EmailSyntaxError.
    validate_email(settings.seed_professor_email, check_deliverability=False)


def test_login_with_special_use_domain_is_rejected_with_422_not_401():
    """Documenta o comportamento da causa raiz do bug de login: um e-mail com
    domínio "special-use" (.local) falha na validação de esquema (422), e não na
    autenticação (401). Serve de guarda para não reintroduzir domínios assim como
    padrão de configuração sem perceber a diferença de status code.
    """
    from fastapi.testclient import TestClient

    import app.main as main_module

    with TestClient(main_module.app) as c:
        resp = c.post(
            "/v1/auth/login",
            json={"email": "professor@avalia.local", "password": "qualquer"},
        )
    assert resp.status_code == 422
