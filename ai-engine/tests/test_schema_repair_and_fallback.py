import json
from unittest.mock import AsyncMock
import pytest
from app.config import settings
from app.main import ollama_client


def test_invalid_llm_json_triggers_repair_and_succeeds(client, sample_payload, monkeypatch):
    """
    Quando o modelo retorna um JSON malformado na primeira tentativa, o AI Engine:
    - Executa UMA tentativa de reparo
    - Se a tentativa de reparo devolver JSON válido, o payload final inclui SCHEMA_REPAIR_APPLIED
    - O schema é validado e status 200 é retornado
    """
    broken_output = "Aqui está a resposta: {criterion_scores: [incompleto..."
    valid_repaired_output = json.dumps({
        "criterion_scores": [
            {
                "criterion_id": "crit_lifo",
                "score": 2.5,
                "max_score": 2.5,
                "reason": "Explicou corretamente o conceito LIFO.",
                "evidence": "A pilha é LIFO",
            },
            {
                "criterion_id": "crit_fifo",
                "score": 2.5,
                "max_score": 2.5,
                "reason": "Explicou corretamente o conceito FIFO.",
                "evidence": "a fila é FIFO",
            }
        ]
    })

    mock_generate = AsyncMock(return_value=broken_output)
    mock_repair = AsyncMock(return_value=valid_repaired_output)

    monkeypatch.setattr(settings, "ai_engine_mode", "real")
    monkeypatch.setattr(ollama_client, "generate", mock_generate)
    monkeypatch.setattr(ollama_client, "repair_json", mock_repair)

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    data = response.json()

    # Verifica que o reparo foi invocado exatamente uma vez
    mock_repair.assert_called_once()
    assert "SCHEMA_REPAIR_APPLIED" in data["flags"]
    assert len(data["criterion_scores"]) == 2


def test_invalid_llm_json_fails_after_repair_returns_502(client, sample_payload, monkeypatch):
    """
    Quando o modelo retorna JSON quebrado e a tentativa de reparo também falha:
    - Retorna erro HTTP 502 (Bad Gateway) com mensagem clara
    - NUNCA inventa notas ou números fictícios
    """
    broken_output = "Resposta inválida completamente sem formato."
    still_broken_output = "Ainda inválido: erro persistente."

    mock_generate = AsyncMock(return_value=broken_output)
    mock_repair = AsyncMock(return_value=still_broken_output)

    monkeypatch.setattr(settings, "ai_engine_mode", "real")
    monkeypatch.setattr(ollama_client, "generate", mock_generate)
    monkeypatch.setattr(ollama_client, "repair_json", mock_repair)

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 502
    data = response.json()
    assert "error" in data
    assert "reparo" in data["error"].lower()
    mock_repair.assert_called_once()
