"""
AV-S07B — extração OCR/visão experimental (POST /v1/extract).
Nenhuma chamada real ao Ollama: o transporte HTTP é substituído por
httpx.MockTransport e a imagem é um base64 sintético.
"""
import base64
import json

import httpx
import pytest

import app.vision_client as vision_module
from app.config import settings
from app.main import vision_client
from app.vision_client import VISION_TRANSCRIPTION_PROMPT, VisionClient, canonical_http_error

FAKE_IMAGE_B64 = base64.b64encode(b"\x89PNG-imagem-sintetica").decode()


def _install_transport(monkeypatch, handler):
    """Faz o VisionClient usar um transporte falso, registrando as requisições."""
    captured: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return handler(request)

    original = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(recording_handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(vision_module.httpx, "AsyncClient", fake_async_client)
    return captured


@pytest.fixture(autouse=True)
def _real_mode(monkeypatch):
    monkeypatch.setattr(settings, "ai_engine_mode", "real")


def _post(client):
    return client.post("/v1/extract", json={"image_base64": FAKE_IMAGE_B64, "mime_type": "image/png"})


def test_extract_ok_sends_literal_prompt_and_vision_options(client, monkeypatch):
    captured = _install_transport(
        monkeypatch, lambda req: httpx.Response(200, json={"response": "  A pilha é LIFU.\n"})
    )

    response = _post(client)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    # MÉDIA-7: o texto é devolvido BRUTO (sem strip); a limpeza de bordas é do
    # Core ao derivar o rascunho. Erro do aluno preservado, sem pós-correção.
    assert body["text"] == "  A pilha é LIFU.\n"
    assert body["model"] == "qwen2.5vl:3b"
    assert body["error_detail"] is None

    [request] = captured
    sent = json.loads(request.content)
    assert request.url.path == "/api/generate"
    assert sent["model"] == settings.ai_vision_model_name == "qwen2.5vl:3b"
    assert sent["model"] != settings.ai_model_name  # visão separada do modelo textual
    assert sent["images"] == [FAKE_IMAGE_B64]
    assert sent["stream"] is False
    assert "format" not in sent
    assert sent["options"] == {"num_ctx": 8192, "seed": 42, "temperature": 0.0}
    assert sent["prompt"] == VISION_TRANSCRIPTION_PROMPT
    assert "NÃO corrija" in sent["prompt"]


def test_extract_empty_response_is_vazio_without_text(client, monkeypatch):
    _install_transport(monkeypatch, lambda req: httpx.Response(200, json={"response": "  \n "}))

    body = _post(client).json()

    assert body["status"] == "vazio"
    assert body["text"] == ""


def test_extract_http_error_body_never_leaks_student_text(client, monkeypatch):
    # ALTA-6: o corpo do erro do Ollama (que pode conter texto reconhecido da
    # imagem) NUNCA aparece no error_detail devolvido. Só código + frase canônica.
    eco = "RESPOSTA_DO_ALUNO_" + "A" * 400  # simula o Ollama ecoando texto da imagem
    _install_transport(
        monkeypatch,
        lambda req: httpx.Response(500, json={"error": f"falha ao carregar modelo {eco}"}),
    )

    body = _post(client).json()

    assert body["status"] == "falha"
    assert body["text"] == ""
    assert "HTTP 500" in body["error_detail"]
    # O eco do corpo (e qualquer trecho dele) não pode vazar.
    assert eco not in body["error_detail"]
    assert "RESPOSTA_DO_ALUNO_" not in body["error_detail"]
    assert "falha ao carregar modelo" not in body["error_detail"]


def test_extract_connection_error_is_falha(client, monkeypatch):
    def refuse(request):
        raise httpx.ConnectError("conexão recusada", request=request)

    _install_transport(monkeypatch, refuse)

    body = _post(client).json()

    assert body["status"] == "falha"
    assert body["text"] == ""
    assert "conectar" in body["error_detail"]


def test_extract_timeout_is_falha(client, monkeypatch):
    def slow(request):
        raise httpx.ReadTimeout("timeout", request=request)

    _install_transport(monkeypatch, slow)

    body = _post(client).json()

    assert body["status"] == "falha"
    assert body["text"] == ""
    assert "Timeout" in body["error_detail"]


def test_extract_simulated_mode_never_fabricates(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_engine_mode", "simulated")
    captured = _install_transport(monkeypatch, lambda req: httpx.Response(200, json={"response": "x"}))

    body = _post(client).json()

    assert body["status"] == "falha"
    assert body["text"] == ""
    assert captured == []


def test_extract_rejects_invalid_base64_and_mime(client):
    bad_b64 = client.post("/v1/extract", json={"image_base64": "não é base64!", "mime_type": "image/png"})
    bad_mime = client.post("/v1/extract", json={"image_base64": FAKE_IMAGE_B64, "mime_type": "image/gif"})
    extra = client.post(
        "/v1/extract",
        json={"image_base64": FAKE_IMAGE_B64, "mime_type": "image/png", "reference_answer": "x"},
    )
    assert bad_b64.status_code == 422
    assert bad_mime.status_code == 422
    # Só a imagem entra: campos como resposta de referência são recusados.
    assert extra.status_code == 422


def test_health_does_not_depend_on_vision(client, monkeypatch):
    async def boom(*args, **kwargs):  # pragma: no cover - não deve ser chamado
        raise AssertionError("health não pode chamar a visão")

    monkeypatch.setattr(vision_client, "extract", boom)
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_canonical_http_error_nunca_propaga_corpo_do_ollama():
    # ALTA-6: a mensagem é FIXA por código HTTP; nunca inclui o corpo do erro
    # (que poderia conter texto reconhecido da imagem).
    sensivel = "RESPOSTA_DO_ALUNO_SECRETA_12345"
    for code in (400, 404, 429, 500, 503, 418):
        msg = canonical_http_error(code)
        assert str(code) in msg
        assert sensivel not in msg
        assert "aluno" not in msg.lower()


@pytest.mark.asyncio
async def test_vision_client_uses_explicit_timeout(monkeypatch):
    seen = {}
    original = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        kwargs["transport"] = httpx.MockTransport(lambda req: httpx.Response(200, json={"response": "ok"}))
        return original(*args, **kwargs)

    monkeypatch.setattr(vision_module.httpx, "AsyncClient", fake_async_client)
    result = await VisionClient().extract(FAKE_IMAGE_B64, timeout=7.5)
    assert seen["timeout"] == 7.5
    assert result.status == "ok"
