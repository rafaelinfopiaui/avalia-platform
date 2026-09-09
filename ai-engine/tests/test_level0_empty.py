from unittest.mock import AsyncMock
import pytest
from app.main import ollama_client


def test_empty_answer_returns_empty_answer_flag(client, sample_payload, monkeypatch):
    """
    Nível 0 - Resposta vazia deve:
    - Retornar direto com flag EMPTY_ANSWER
    - Ter review_recommendation=REVIEW_REQUIRED
    - Ter overall_confidence baixa (0.10)
    - NUNCA chamar o runtime do LLM (mock/monkeypatch verifica que generate não é chamado)
    """
    mock_generate = AsyncMock()
    monkeypatch.setattr(ollama_client, "generate", mock_generate)

    # Teste com string vazia
    sample_payload["answer_text"] = ""
    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    data = response.json()

    # Verifica ausência de chamada ao LLM
    mock_generate.assert_not_called()

    assert data["schema_version"] == "1.0"
    assert "EMPTY_ANSWER" in data["flags"]
    assert data["review_recommendation"] == "REVIEW_REQUIRED"
    assert data["overall_confidence"] < 0.60
    assert len(data["criterion_scores"]) == 2

    for item in data["criterion_scores"]:
        assert item["score"] == 0.0
        assert item["confidence"] < 0.60


@pytest.mark.parametrize("short_text", [
    "   ",
    "ola",
    "não sei",
    "...",
    "12345",
    "curto!",
])
def test_short_answer_below_10_useful_chars_activates_level_0(client, sample_payload, monkeypatch, short_text):
    """Respostas com menos de 10 caracteres úteis não devem acionar o LLM."""
    mock_generate = AsyncMock()
    monkeypatch.setattr(ollama_client, "generate", mock_generate)

    sample_payload["answer_text"] = short_text
    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    data = response.json()

    mock_generate.assert_not_called()
    assert "EMPTY_ANSWER" in data["flags"]
    assert data["review_recommendation"] == "REVIEW_REQUIRED"
