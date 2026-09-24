"""
Cliente assíncrono para comunicação com o runtime Ollama local.
Lida com chamadas de inferência, verificação de saúde e retentativa de reparo JSON.
"""
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.prompts.prompt_v1 import build_repair_prompt

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Erro base para operações com o Ollama."""
    pass


class OllamaConnectionError(OllamaError):
    """Lançado quando o Ollama está inacessível ou fora do ar."""
    pass


class OllamaTimeoutError(OllamaConnectionError):
    """Lançado quando a chamada ao Ollama atinge timeout."""
    pass


class OllamaResponseError(OllamaError):
    """Lançado quando o Ollama retorna um status de erro HTTP 5xx ou inesperado."""
    pass


class OllamaClient:
    """Cliente HTTP para a API do Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.ollama_url).rstrip("/")
        self.model_name = model_name or settings.ai_model_name
        self.timeout = timeout or settings.ollama_timeout_seconds

    async def check_health(self) -> bool:
        """
        Verifica se o Ollama está ativo e respondendo.
        Retorna True se operacional, False se inacessível.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception as exc:
            logger.warning(
                "Health check do Ollama falhou",
                extra={"error": str(exc), "url": self.base_url},
            )
            return False

    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float = 0.2,
        format_json: bool = True,
    ) -> str:
        """
        Executa uma chamada de inferência no endpoint /api/generate do Ollama.
        """
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if format_json:
            payload["format"] = "json"

        url = f"{self.base_url}/api/generate"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
        except httpx.ConnectError as exc:
            logger.error(
                "Falha de conexão com o Ollama",
                extra={"url": url, "error": str(exc)},
            )
            raise OllamaConnectionError(
                f"Não foi possível conectar ao Ollama em {self.base_url}."
            ) from exc
        except (httpx.TimeoutException, httpx.ReadTimeout) as exc:
            logger.error(
                "Timeout aguardando resposta do Ollama",
                extra={"url": url, "timeout": self.timeout, "error": str(exc)},
            )
            raise OllamaTimeoutError(
                f"Timeout de {self.timeout}s aguardando resposta do Ollama."
            ) from exc
        except Exception as exc:
            logger.error(
                "Erro inesperado de rede com o Ollama",
                extra={"url": url, "error": str(exc)},
            )
            raise OllamaConnectionError(f"Erro de comunicação com o Ollama: {exc}") from exc

        if res.status_code != 200:
            logger.error(
                "Ollama retornou erro HTTP",
                extra={"status_code": res.status_code, "body": res.text[:200]},
            )
            raise OllamaResponseError(
                f"Ollama retornou status HTTP {res.status_code}: {res.text[:200]}"
            )

        data = res.json()
        response_text = data.get("response", "")
        return response_text

    async def repair_json(self, bad_output: str, error_details: str) -> str:
        """
        Executa UMA tentativa de reparo pedindo para o modelo corrigir o JSON.
        """
        system = "Você é um formatador estrito de JSON. Responda apenas com o JSON corrigido."
        repair_prompt = build_repair_prompt(bad_output, error_details)
        return await self.generate(
            prompt=repair_prompt,
            system=system,
            temperature=0.1,
            format_json=True,
        )
