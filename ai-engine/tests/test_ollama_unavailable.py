from unittest.mock import AsyncMock
from app.config import settings
from app.main import ollama_client
from app.ollama_client import OllamaConnectionError, OllamaTimeoutError


def test_ollama_connection_error_returns_503(client, sample_payload, monkeypatch):
    """
    RN-017: Se AI_ENGINE_MODE=real e o Ollama estiver fora do ar:
    - Retorna HTTP 503 Service Unavailable
    - NUNCA fabrica silenciosamente uma resposta simulada ou notas arbitrárias
    """
    monkeypatch.setattr(settings, "ai_engine_mode", "real")
    mock_generate = AsyncMock(
        side_effect=OllamaConnectionError("Conexão recusada em localhost:11434")
    )
    monkeypatch.setattr(ollama_client, "generate", mock_generate)

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 503
    data = response.json()
    assert "indisponível" in data["error"].lower() or "indisponivel" in data["error"].lower()
    assert data["status_code"] == 503
    assert "correlation_id" in data


def test_ollama_timeout_returns_503(client, sample_payload, monkeypatch):
    """Timeout na chamada ao Ollama também deve resultar em HTTP 503."""
    monkeypatch.setattr(settings, "ai_engine_mode", "real")
    mock_generate = AsyncMock(
        side_effect=OllamaTimeoutError("Timeout de 60s atingido")
    )
    monkeypatch.setattr(ollama_client, "generate", mock_generate)

    response = client.post("/v1/analyze", json=sample_payload)

    assert response.status_code == 503
    data = response.json()
    assert "correlation_id" in data
