import contextvars
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# ContextVar para propagação assíncrona do correlation_id
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="no-correlation-id"
)


def get_correlation_id() -> str:
    """Retorna o correlation_id atual do contexto."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Define o correlation_id no contexto assíncrono."""
    correlation_id_ctx.set(correlation_id)


def hash_text(text: str) -> str:
    """
    Retorna o hash SHA-256 truncado do texto para auditoria sem vazar
    o conteúdo completo da resposta do aluno (RNF-07).
    """
    if not text:
        return "empty"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


class JSONFormatter(logging.Formatter):
    """
    Formatador de log estruturado em JSON com correlation_id.
    Garante conformidade com RNF-07: nunca inclui textos integrais de alunos.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", get_correlation_id()),
            "message": record.getMessage(),
        }

        # Inclui atributos extras passados no extra={}
        # Proteção RNF-07: bloqueia chaves que possam conter texto integral de aluno
        forbidden_keys = {"answer_text", "student_answer", "raw_text", "untrusted_content"}
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName", "correlation_id"
            ):
                if key in forbidden_keys:
                    log_entry[f"{key}_hash"] = hash_text(str(value))
                    log_entry[f"{key}_length"] = len(str(value))
                else:
                    log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> None:
    """Configura o root logger para usar o formatador JSON estruturado."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Limpa handlers existentes
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)

    # Reduz ruído de logs de bibliotecas de baixo nível
    logging.getLogger("uvicorn.access").handlers = [stream_handler]
    logging.getLogger("uvicorn.error").handlers = [stream_handler]
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
