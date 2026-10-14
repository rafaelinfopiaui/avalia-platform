"""AC-01 / BL-AV-S03B-01: GET /v1/config/capabilities é a fonte única de verdade.

O endpoint deve refletir o valor real de settings.academic_module_enabled (sem
duplicar o parsing da env var) e não pode exigir autenticação — o frontend
precisa conhecer as capacidades antes de qualquer login para decidir o que
renderizar.
"""
import pytest

import app.main as main_module
from app.config import get_settings


@pytest.mark.parametrize("enabled", [False, True])
def test_capabilities_reflects_backend_setting(client, monkeypatch, enabled):
    # main_module.settings é o mesmo objeto retornado por get_settings()
    # (lru_cache), então o patch cobre as duas leituras.
    monkeypatch.setattr(main_module.settings, "academic_module_enabled", enabled)
    assert get_settings().academic_module_enabled is enabled

    response = client.get("/v1/config/capabilities")

    assert response.status_code == 200, response.text
    assert response.json() == {"academic_module_enabled": enabled}


def test_capabilities_does_not_require_authentication(client, monkeypatch):
    monkeypatch.setattr(main_module.settings, "academic_module_enabled", True)

    # Sem header Authorization: deve responder 200, não 401/403.
    response = client.get("/v1/config/capabilities")
    assert response.status_code == 200, response.text

    # Com token inválido também não deve falhar: o endpoint ignora credenciais.
    with_bad_token = client.get(
        "/v1/config/capabilities", headers={"Authorization": "Bearer token-invalido"}
    )
    assert with_bad_token.status_code == 200, with_bad_token.text
    assert with_bad_token.json() == {"academic_module_enabled": True}


def test_capabilities_exposes_only_capability_booleans(client):
    """Nenhum segredo/configuração sensível pode vazar por este endpoint público."""
    payload = client.get("/v1/config/capabilities").json()
    assert set(payload) == {"academic_module_enabled"}
    assert all(isinstance(value, bool) for value in payload.values())
