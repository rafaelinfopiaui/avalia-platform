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
from app.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse

# Configura logs estruturados
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

# Instâncias globais de clientes
ollama_client = OllamaClient()
cascade = DecisionCascade(ollama_client=ollama_client)


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação de payload."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Erro de validação nos dados de entrada",
            "details": exc.errors(),
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
