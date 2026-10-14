"""AC-09 / BL-AV-S03B-03: guarda de nome de banco do seed da AV-S03B.

Nenhum destes testes abre conexão com banco algum: exercitam apenas a função
pura `require_isolated_database`, que decide se o alvo é aceitável ANTES de
qualquer `create_engine`. A lista de recusas inclui explicitamente `avalia_dev`
e `avalia_apresentacao_demo_20261002`, os dois bancos que `DEC-AV-032` proíbe
tocar.
"""
import importlib.util
from pathlib import Path

import pytest

SEED_PATH = Path(__file__).resolve().parents[3] / "core" / "scripts" / "seed_academic_capability_demo.py"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_academic_capability_demo", SEED_PATH)
    assert spec is not None and spec.loader is not None, SEED_PATH
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed = _load_seed_module()


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg2://localhost:5432/avalia_dev",
        "postgresql+psycopg2://user:pass@localhost:5432/avalia_dev",
        "postgresql+psycopg2://localhost:5432/avalia_apresentacao_demo_20261002",
        # Tentativas de burlar a guarda por substring/credencial/query-string.
        "postgresql+psycopg2://av_s03b_capacidades_x@localhost:5432/avalia_dev",
        "postgresql+psycopg2://localhost:5432/avalia_dev?options=av_s03b_capacidades_x",
        "postgresql+psycopg2://localhost:5432/av_s03b_capacidades_x_avalia_dev_extra/../avalia_dev",
        # Prefixo/sufixo próximos, mas fora do padrão ancorado.
        "postgresql+psycopg2://localhost:5432/av_s03b_capacidades",
        "postgresql+psycopg2://localhost:5432/xav_s03b_capacidades_local",
        "postgresql+psycopg2://localhost:5432/av_s02_saneamento_local",
        "",
    ],
)
def test_guard_refuses_non_isolated_targets(database_url):
    with pytest.raises(RuntimeError) as excinfo:
        seed.require_isolated_database(database_url)
    assert "Refusing to seed" in str(excinfo.value)


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg2://localhost:5432/av_s03b_capacidades_local",
        "postgresql+psycopg2://user:pass@127.0.0.1:5432/av_s03b_capacidades_ci-01",
        "postgresql+psycopg2://localhost:5432/av_s03b_capacidades_A1",
    ],
)
def test_guard_accepts_isolated_targets(database_url):
    seed.require_isolated_database(database_url)


def test_guard_pattern_is_disjoint_from_reference_seed():
    """O seed da AV-S03B e o de referência (AV-S04) nunca aceitam o mesmo banco."""
    reference_spec = importlib.util.spec_from_file_location(
        "seed_academic_multi_question_demo",
        SEED_PATH.with_name("seed_academic_multi_question_demo.py"),
    )
    assert reference_spec is not None and reference_spec.loader is not None
    reference = importlib.util.module_from_spec(reference_spec)
    reference_spec.loader.exec_module(reference)

    url = "postgresql+psycopg2://localhost:5432/av_s03b_capacidades_local"
    seed.require_isolated_database(url)
    with pytest.raises(RuntimeError):
        reference.require_isolated_database(url)


def test_demo_ids_are_prefixed_and_do_not_collide_with_reference_seed():
    assert all(value.startswith("demo-av-s03b") for value in seed.IDS.values())
    assert seed.PREFIX == "demo-av-s03b"
