import json
import logging
from pathlib import Path
from typing import Any, Dict, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configurações da aplicação AvalIA AI Engine."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ai_engine_mode: Literal["real", "simulated"] = "real"
    ai_model_name: str = "qwen2.5:7b-instruct-q4_K_M"
    ollama_url: str = "http://localhost:11434"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"
    schema_path: str = "../docs/contracts/ai-engine-output.schema.json"
    ollama_timeout_seconds: float = 60.0


settings = Settings()

# Cache para o schema JSON oficial
_cached_schema: Dict[str, Any] | None = None


def get_output_schema() -> Dict[str, Any]:
    """
    Carrega o schema JSON oficial em docs/contracts/ai-engine-output.schema.json.
    Não altera o schema, servindo como fonte única da verdade.
    """
    global _cached_schema
    if _cached_schema is not None:
        return _cached_schema

    # Tentativa 1: caminho configurado
    configured_path = Path(settings.schema_path)
    if not configured_path.is_absolute():
        # Tenta a partir do diretório de trabalho atual e a partir da raiz do repositório
        base_dir = Path(__file__).resolve().parent.parent.parent
        possible_paths = [
            Path.cwd() / configured_path,
            base_dir / "docs" / "contracts" / "ai-engine-output.schema.json",
            Path(__file__).resolve().parent.parent / configured_path,
        ]
        schema_file = None
        for p in possible_paths:
            if p.exists():
                schema_file = p
                break
    else:
        schema_file = configured_path if configured_path.exists() else None

    if not schema_file or not schema_file.exists():
        raise FileNotFoundError(
            f"Schema de saída do AI Engine não encontrado no caminho {settings.schema_path} nem nos caminhos de fallback."
        )

    with open(schema_file, "r", encoding="utf-8") as f:
        _cached_schema = json.load(f)

    return _cached_schema
