"""
Aplicação principal FastAPI do AvalIA AI Engine.
Expõe os endpoints POST /v1/analyze e GET /v1/health.
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.cascade import DecisionCascade
from app.config import settings
from app.logging_config import (
    get_correlation_id,
    set_correlation_id,
    setup_logging,
)
from app.ollama_client import OllamaClient
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
)
from app.vision_client import VisionClient

# Configura logs estruturados
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

# Instâncias globais de clientes
ollama_client = OllamaClient()
cascade = DecisionCascade(ollama_client=ollama_client)
vision_client = VisionClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Inicializando AvalIA AI Engine",
        extra={
            "engine_mode": settings.ai_engine_mode,
            "model_name": settings.ai_model_name,
            "ollama_url": settings.ollama_url,
        },
    )
    yield
    logger.info("Encerrando AvalIA AI Engine")


app = FastAPI(
    title="AvalIA AI Engine",
    description="Motor de inferência e validação para correção assistida de respostas discursivas.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    """
    Middleware que gerencia correlation_id e registra logs estruturados
    sem vazar dados sensíveis ou texto integral do aluno (RNF-07).
    """
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(corr_id)

    start_time = time.perf_counter()
    logger.info(
        "Início da requisição HTTP",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    try:
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        response.headers["X-Correlation-ID"] = corr_id
        logger.info(
            "Fim da requisição HTTP",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.exception(
            "Erro não tratado na requisição HTTP",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "error": str(exc),
            },
        )
        raise exc


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para HTTPExceptions estruturadas com correlation_id."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "correlation_id": get_correlation_id(),
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


# Campos cujo valor NUNCA pode ser ecoado em erro de validação nem em log
# (AV-S07B, lacuna B): a imagem em base64 é dado do aluno e pode ser enorme.
_SENSITIVE_INPUT_FIELDS = frozenset({"image_base64"})
# Qualquer outra string de entrada acima deste tamanho vira placeholder
# (ex.: texto integral do aluno em /v1/analyze, RNF-07).
_MAX_ECHOED_INPUT_CHARS = 64


def _omitted(value: object) -> str:
    size = len(value) if isinstance(value, (str, bytes, bytearray)) else len(str(value))
    return f"<omitido:{size} chars>"


def _mask_input(value: object, key: object = None) -> object:
    """Mascara recursivamente valores sensíveis (por nome) ou longos."""
    if key in _SENSITIVE_INPUT_FIELDS:
        return _omitted(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, dict):
        return {k: _mask_input(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mask_input(item) for item in value]
    text = value if isinstance(value, str) else str(value)
    return text if len(text) <= _MAX_ECHOED_INPUT_CHARS else _omitted(text)


def _sanitize_validation_errors(errors: list) -> list:
    """
    Preserva loc/type/msg (úteis ao cliente) e mascara input/ctx: o `input`
    do Pydantic pode trazer o base64 da imagem ou o corpo inteiro da requisição.
    """
    sanitized = []
    for error in errors:
        loc = list(error.get("loc", ()))
        item = {"type": error.get("type"), "loc": loc, "msg": error.get("msg")}
        sensitive = any(part in _SENSITIVE_INPUT_FIELDS for part in loc)
        if "input" in error:
            item["input"] = _omitted(error["input"]) if sensitive else _mask_input(error["input"])
        ctx = error.get("ctx")
        if isinstance(ctx, dict) and ctx:
            if sensitive:
                # Só limites numéricos (ex.: max_length); nada textual do campo sensível.
                ctx = {k: v for k, v in ctx.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            else:
                ctx = {k: _mask_input(v) for k, v in ctx.items()}
            if ctx:
                item["ctx"] = ctx
        sanitized.append(item)
    return sanitized


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação de payload (input/ctx sempre sanitizados)."""
    details = _sanitize_validation_errors(exc.errors())
    # Log só com localização/tipo do erro: nunca o valor recebido.
    logger.warning(
        "Erro de validação nos dados de entrada",
        extra={
            "path": request.url.path,
            "error_count": len(details),
            "error_locs": [".".join(str(part) for part in item["loc"]) for item in details],
            "error_types": [item["type"] for item in details],
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Erro de validação nos dados de entrada",
            "details": details,
            "correlation_id": get_correlation_id(),
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.post(
    "/v1/analyze",
    response_model=AnalyzeResponse,
    summary="Analisar e avaliar resposta discursiva",
    description=(
        "Executa a cascata de decisão (Níveis 0, 1 e 3) sobre a resposta do aluno "
        "conforme a rubrica e o gabarito. Retorna saída estruturada estritamente validada."
    ),
)
async def analyze_answer(payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    Endpoint principal de análise.
    Recebe question_statement, reference_answer, rubric e answer_text.
    Atributos pessoais de estudantes são ignorados se fornecidos (RN-010).
    """
    return await cascade.execute(payload)


@app.post(
    "/v1/extract",
    response_model=ExtractResponse,
    summary="Extrair texto de imagem de resposta (experimental)",
    description=(
        "Transcreve literalmente o texto visível na imagem com o modelo de visão local. "
        "Não corrige nem avalia. Saída é texto puro; vazio/falha nunca trazem texto fabricado."
    ),
)
async def extract_text(payload: ExtractRequest) -> ExtractResponse:
    """
    Endpoint de extração OCR/visão (AV-S07B, DEC-AV-046).
    A imagem é dado não confiável: o motor não recebe ferramentas nem segredos
    e o texto devolvido nunca é interpretado como instrução.
    """
    if settings.ai_engine_mode == "simulated":
        # Nunca fabrica transcrição: o modo simulado não tem extração.
        return ExtractResponse(
            text="",
            model=settings.ai_vision_model_name,
            status="falha",
            duration_ms=0,
            error_detail="Extração indisponível em modo simulado.",
        )
    result = await vision_client.extract(payload.image_base64)
    return ExtractResponse(
        text=result.text if result.status == "ok" else "",
        model=result.model,
        status=result.status,
        duration_ms=result.duration_ms,
        error_detail=result.error_detail,
    )


@app.get(
    "/v1/health",
    response_model=HealthResponse,
    summary="Verificação de integridade do serviço",
    description="Retorna status do Ollama, modelo e engine_mode configurados sem vazar segredos.",
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check.
    Testa conectividade com o Ollama e expõe apenas informações operacionais seguras.
    """
    ollama_up = await ollama_client.check_health()
    overall_status = "healthy" if ollama_up else "degraded"

    return HealthResponse(
        status=overall_status,
        engine_mode=settings.ai_engine_mode,
        model=settings.ai_model_name,
        ollama_status="up" if ollama_up else "down",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_config=None,
    )
