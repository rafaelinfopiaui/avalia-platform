"""
AV-S07B, lacuna B — a resposta 422 (e o log) nunca ecoam o base64 da imagem.
Entradas sintéticas com marcador único; nenhuma chamada ao Ollama (a validação
falha antes do endpoint).
"""
import logging

import pytest

MARKER = "MARCADOR_SECRETO_12345"
# Charset válido de base64 (sem "_"), para exercitar erros que não sejam de padrão.
VALID_CHARSET_MARKER = "MARCADORSECRETO12345"


def _all_log_text(caplog) -> str:
    return "\n".join(f"{record.getMessage()} {record.__dict__}" for record in caplog.records)


@pytest.mark.parametrize(
    "image_base64",
    [
        # Curto e inválido (underscore e "!" fora do padrão base64).
        f"{MARKER}!!!",
        # Longo e inválido: acima do limite de truncamento.
        f"{MARKER}!" + "A" * 500,
    ],
    ids=["curto", "longo"],
)
def test_invalid_base64_marker_never_echoed_in_422_nor_log(client, caplog, image_base64):
    caplog.set_level(logging.DEBUG)

    response = client.post("/v1/extract", json={"image_base64": image_base64, "mime_type": "image/png"})

    assert response.status_code == 422
    assert MARKER not in response.text
    assert "AAAAAAAAAA" not in response.text
    body = response.json()
    [error] = body["details"]
    # Informação útil preservada: onde e qual foi o erro.
    assert error["loc"] == ["body", "image_base64"]
    assert error["type"] == "string_pattern_mismatch"
    assert error["msg"]
    assert error["input"] == f"<omitido:{len(image_base64)} chars>"
    assert "pattern" not in error.get("ctx", {})
    # O log da validação existe (a asserção abaixo não é vazia) e não traz o valor.
    assert any(record.getMessage() == "Erro de validação nos dados de entrada" for record in caplog.records)
    assert MARKER not in _all_log_text(caplog)


def test_valid_base64_in_body_is_masked_when_other_field_fails(client, caplog):
    """Erro em outro campo traz o corpo inteiro como input: a imagem é omitida por nome."""
    caplog.set_level(logging.DEBUG)
    image = VALID_CHARSET_MARKER * 10

    response = client.post("/v1/extract", json={"image_base64": image})  # falta mime_type

    assert response.status_code == 422
    assert VALID_CHARSET_MARKER not in response.text
    [error] = response.json()["details"]
    assert error["loc"] == ["body", "mime_type"]
    assert error["type"] == "missing"
    assert error["input"] == {"image_base64": f"<omitido:{len(image)} chars>"}
    assert VALID_CHARSET_MARKER not in _all_log_text(caplog)


def test_too_long_base64_reports_limit_without_value(client):
    from app.schemas import _MAX_IMAGE_BASE64_CHARS

    image = VALID_CHARSET_MARKER * (_MAX_IMAGE_BASE64_CHARS // len(VALID_CHARSET_MARKER) + 1)

    response = client.post("/v1/extract", json={"image_base64": image, "mime_type": "image/png"})

    assert response.status_code == 422
    assert VALID_CHARSET_MARKER not in response.text
    [error] = response.json()["details"]
    assert error["type"] == "string_too_long"
    assert error["ctx"] == {"max_length": _MAX_IMAGE_BASE64_CHARS}


def test_analyze_validation_error_stays_useful(client, sample_payload):
    payload = dict(sample_payload)
    del payload["rubric"]
    payload["answer_text"] = "Texto do aluno " * 20  # longo: mascarado (RNF-07)

    response = client.post("/v1/analyze", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Erro de validação nos dados de entrada"
    assert body["correlation_id"]
    [error] = body["details"]
    assert error["loc"] == ["body", "rubric"]
    assert error["type"] == "missing"
    assert error["msg"] == "Field required"
    # Campos curtos seguem legíveis; o texto longo do aluno não é ecoado.
    assert error["input"]["question_statement"].startswith("<omitido:")
    assert error["input"]["answer_text"] == f"<omitido:{len(payload['answer_text'])} chars>"
    assert "Texto do aluno" not in response.text


def test_analyze_short_invalid_value_is_still_echoed(client, sample_payload):
    payload = dict(sample_payload)
    payload["rubric"] = [dict(payload["rubric"][0], max_score="abc")]

    response = client.post("/v1/analyze", json=payload)

    assert response.status_code == 422
    [error] = response.json()["details"]
    assert error["loc"] == ["body", "rubric", 0, "max_score"]
    assert error["input"] == "abc"
