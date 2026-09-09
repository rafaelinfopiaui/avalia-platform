from unittest.mock import AsyncMock
from app.main import ollama_client


def test_health_check_healthy_when_ollama_up(client, monkeypatch):
    """GET /v1/health retorna status=healthy e ollama_status=up."""
    monkeypatch.setattr(ollama_client, "check_health", AsyncMock(return_value=True))

    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["ollama_status"] == "up"
    assert "engine_mode" in data
    assert "model" in data
    # Garante ausência de campos confidenciais
    assert "password" not in data
    assert "token" not in data
    assert "secret" not in data


def test_health_check_degraded_when_ollama_down(client, monkeypatch):
    """GET /v1/health retorna status=degraded e ollama_status=down quando Ollama não responde."""
    monkeypatch.setattr(ollama_client, "check_health", AsyncMock(return_value=False))

    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "degraded"
    assert data["ollama_status"] == "down"
