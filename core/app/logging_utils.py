from __future__ import annotations
import json
import logging
import sys
import time
import uuid

logger = logging.getLogger("avalia.core")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(_handler)


def log_event(event: str, correlation_id: str, **fields) -> None:
    """Log estruturado em JSON. NUNCA passar texto completo de resposta de aluno
    ou segredos em `fields` — apenas identificadores, tamanhos, status."""
    record = {
        "ts": time.time(),
        "event": event,
        "correlation_id": correlation_id,
        **fields,
    }
    logger.info(json.dumps(record, ensure_ascii=False, default=str))


def new_correlation_id() -> str:
    return str(uuid.uuid4())
