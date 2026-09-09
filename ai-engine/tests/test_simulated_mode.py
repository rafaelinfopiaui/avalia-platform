import json
from unittest.mock import AsyncMock
from app.config import settings
from app.main import ollama_client


def test_explicit_simulated_mode_returns_simulated_payload(client, sample_payload, monkeypatch):
    """
    Quando AI_ENGINE_MODE=simulated:
    - Retorna engine_mode="simulated"
    - Retorna flag SIMULATED_MODE
    - model é string vazia conforme schema
    - Pontuação determinística = metade do max_score
    - Não chama Ollama
    """
    monkeypatch.setattr(settings, "ai_engine_mode", "simulated")
    mock_generate = AsyncMock()
    monkeypatch.setattr(ollama_client, "generate", mock_generate)

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    data = response.json()

    mock_generate.assert_not_called()
    assert data["engine_mode"] == "simulated"
    assert data["model"] == ""
    assert "SIMULATED_MODE" in data["flags"]
    assert data["review_recommendation"] == "REVIEW_REQUIRED"
    assert len(data["criterion_scores"]) == 2

    for item in data["criterion_scores"]:
        assert item["score"] == round(item["max_score"] / 2.0, 2)
        assert "simulado" in item["reason"].lower()


def test_real_mode_never_returns_simulated_flag_by_accident(client, sample_payload, monkeypatch):
    """
    Quando AI_ENGINE_MODE=real:
    - Retorna engine_mode="real"
    - NUNCA inclui flag SIMULATED_MODE
    """
    monkeypatch.setattr(settings, "ai_engine_mode", "real")

    mock_llm_output = json.dumps({
        "criterion_scores": [
            {
                "criterion_id": "crit_lifo",
                "score": 2.5,
                "max_score": 2.5,
                "reason": "Acertou perfeitamente o conceito LIFO.",
                "evidence": "pilha é LIFO",
            },
            {
                "criterion_id": "crit_fifo",
                "score": 2.5,
                "max_score": 2.5,
                "reason": "Acertou perfeitamente o conceito FIFO.",
                "evidence": "fila é FIFO",
            }
        ]
    })
    monkeypatch.setattr(ollama_client, "generate", AsyncMock(return_value=mock_llm_output))

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["engine_mode"] == "real"
    assert "SIMULATED_MODE" not in data["flags"]
    assert data["model"] == settings.ai_model_name
