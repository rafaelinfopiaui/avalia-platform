from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Modos de execução suportados (RN-017)
EngineMode = Literal["real", "simulated"]

# Recomendações de revisão humana (RF-09, ADR-008)
ReviewRecommendation = Literal["REVIEW_OPTIONAL", "REVIEW_RECOMMENDED", "REVIEW_REQUIRED"]

# Flags padronizadas pelo schema de contrato (docs/contracts/ai-engine-output.schema.json)
FlagEnum = Literal[
    "EMPTY_ANSWER",
    "OUT_OF_DOMAIN",
    "PROMPT_INJECTION_SUSPECTED",
    "LOW_COVERAGE",
    "SCHEMA_REPAIR_APPLIED",
    "SIMULATED_MODE",
]


class RubricCriterionInput(BaseModel):
    """Critério individual da rubrica recebido para avaliação."""
    model_config = ConfigDict(extra="ignore")

    criterion_id: str = Field(..., description="Identificador único do critério")
    name: str = Field(..., description="Nome do critério")
    description: str = Field(default="", description="Descrição detalhada do critério")
    max_score: float = Field(..., gt=0, description="Pontuação máxima do critério")


class AnalyzeRequest(BaseModel):
    """
    Payload de requisição para POST /v1/analyze.
    Em conformidade com RN-010 e RNF-02: atributos pessoais (nome, matrícula)
    NUNCA são esperados nem exigidos; campos extras são ignorados.
    """
    model_config = ConfigDict(extra="ignore")

    question_statement: str = Field(..., description="Enunciado da questão")
    reference_answer: str = Field(..., description="Resposta esperada/referência")
    rubric: List[RubricCriterionInput] = Field(..., min_length=1, description="Lista de critérios da rubrica")
    answer_text: str = Field(..., description="Texto da resposta do aluno a ser analisada")


class CriterionScoreOutput(BaseModel):
    """Pontuação e justificativa de um critério específico conforme schema oficial."""
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., description="ID do critério avaliado")
    score: float = Field(..., ge=0, description="Nota atribuída no intervalo [0, max_score]")
    max_score: float = Field(..., gt=0, description="Pontuação máxima do critério")
    reason: str = Field(..., min_length=1, description="Justificativa curta em português")
    evidence: str = Field(..., description="Trecho literal da resposta do aluno que sustenta a pontuação")
    confidence: float = Field(..., ge=0, le=1, description="Grau de confiança heurístico [0, 1]")


class AnalyzeResponse(BaseModel):
    """
    Saída estruturada do AI Engine em conformidade estrita com
    docs/contracts/ai-engine-output.schema.json.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(default="1.0", description="Versão do schema do contrato")
    engine_mode: EngineMode = Field(..., description="Modo real ou simulated (RN-017)")
    model: str = Field(default="", description="Tag do modelo usado (vazio se simulated)")
    criterion_scores: List[CriterionScoreOutput] = Field(..., min_length=1, description="Scores por critério")
    overall_confidence: float = Field(..., ge=0, le=1, description="Confiança geral heurística")
    confidence_method_version: str = Field(default="heuristic-v1", description="Versão do método de confiança")
    review_recommendation: ReviewRecommendation = Field(..., description="Ação de revisão recomendada")
    flags: List[FlagEnum] = Field(default_factory=list, description="Lista de flags detectadas")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Duração do processamento em milissegundos")


class HealthResponse(BaseModel):
    """Resposta do health check /v1/health sem vazar detalhes sensíveis."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy", "degraded", "unhealthy"]
    engine_mode: EngineMode
    model: str
    ollama_status: Literal["up", "down"]
