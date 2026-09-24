"""
Orquestrador da cascata de decisão reduzida do AvalIA AI Engine.
Implementa os níveis 0, 1 e 3 da arquitetura (ADR-005, ADR-008, RN-010, RN-017).
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from fastapi import HTTPException

from app.confidence import CONFIDENCE_METHOD_VERSION, calculate_confidence
from app.config import get_output_schema, settings
from app.injection import detect_prompt_injection
from app.logging_config import hash_text
from app.ollama_client import OllamaClient, OllamaConnectionError, OllamaTimeoutError
from app.prompts.prompt_v1 import (
    build_system_prompt,
    build_user_prompt,
)
from app.rules import analyze_rule_signals
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CriterionScoreOutput,
    FlagEnum,
    RubricCriterionInput,
)

logger = logging.getLogger(__name__)


def count_useful_chars(text: str) -> int:
    """Conta caracteres úteis (alfanuméricos), excluindo pontuação e espaços em branco."""
    return len(re.findall(r"\w", text))


def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Tenta extrair um objeto JSON a partir de um texto que possa conter
    blocos markdown (```json ... ```) ou texto ao redor.
    """
    cleaned = raw_text.strip()
    # Remove cercas markdown
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Tenta parsing direto
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Tenta localizar o primeiro '{' e o último '}'
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace : last_brace + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    return None


class DecisionCascade:
    """Motor de execução da cascata de decisão."""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama_client = ollama_client or OllamaClient()

    async def execute(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start_time = time.perf_counter()
        flags: List[FlagEnum] = []

        logger.info(
            "Iniciando análise de resposta",
            extra={
                "question_length": len(request.question_statement),
                "answer_length": len(request.answer_text),
                "answer_hash": hash_text(request.answer_text),
                "criteria_count": len(request.rubric),
                "configured_engine_mode": settings.ai_engine_mode,
            },
        )

        # -------------------------------------------------------------------
        # NÍVEL 0: Validação de resposta vazia ou insignificante (< 10 chars úteis)
        # Não chama o LLM; retorna imediatamente com flags e REVIEW_REQUIRED
        # -------------------------------------------------------------------
        useful_chars = count_useful_chars(request.answer_text)
        if useful_chars < 10:
            logger.info(
                "Nível 0 ativado: resposta vazia ou insuficiente",
                extra={"useful_chars": useful_chars},
            )
            flags.append("EMPTY_ANSWER")

            # Verifica também se houve tentativa de injeção mesmo no texto curto
            if detect_prompt_injection(request.answer_text):
                flags.append("PROMPT_INJECTION_SUSPECTED")

            duration_ms = int((time.perf_counter() - start_time) * 1000)
            scores = [
                CriterionScoreOutput(
                    criterion_id=crit.criterion_id,
                    score=0.0,
                    max_score=round(crit.max_score, 2),
                    reason="Resposta em branco ou com conteúdo insuficiente para avaliação.",
                    evidence="",
                    confidence=0.10,
                )
                for crit in request.rubric
            ]

            mode = settings.ai_engine_mode
            model_tag = settings.ai_model_name if mode == "real" else ""

            response_data = {
                "schema_version": "1.0",
                "engine_mode": mode,
                "model": model_tag,
                "criterion_scores": [s.model_dump() for s in scores],
                "overall_confidence": 0.10,
                "confidence_method_version": CONFIDENCE_METHOD_VERSION,
                "review_recommendation": "REVIEW_REQUIRED",
                "flags": flags,
                "duration_ms": duration_ms,
            }

            self._validate_contract_schema(response_data)
            return AnalyzeResponse(**response_data)

        # -------------------------------------------------------------------
        # NÍVEL 1: Sinais de regras e verificação de Prompt Injection
        # -------------------------------------------------------------------
        if detect_prompt_injection(request.answer_text):
            logger.warning("Prompt injection suspeito detectado na resposta do aluno")
            flags.append("PROMPT_INJECTION_SUSPECTED")

        rule_signals = analyze_rule_signals(request.rubric, request.answer_text)

        # -------------------------------------------------------------------
        # MODO SIMULADO EXPLÍCITO (RN-017)
        # Acionado SOMENTE quando AI_ENGINE_MODE=simulated estiver configurado
        # -------------------------------------------------------------------
        if settings.ai_engine_mode == "simulated":
            logger.info("Executando em modo simulado explícito (RN-017)")
            if "SIMULATED_MODE" not in flags:
                flags.append("SIMULATED_MODE")

            duration_ms = int((time.perf_counter() - start_time) * 1000)
            scores = [
                CriterionScoreOutput(
                    criterion_id=crit.criterion_id,
                    score=round(crit.max_score / 2.0, 2),
                    max_score=round(crit.max_score, 2),
                    reason="Resultado gerado em modo simulado para teste/contingência, sem inferência real.",
                    evidence="",
                    confidence=0.50,
                )
                for crit in request.rubric
            ]

            response_data = {
                "schema_version": "1.0",
                "engine_mode": "simulated",
                "model": "",  # Vazio se engine_mode=simulated
                "criterion_scores": [s.model_dump() for s in scores],
                "overall_confidence": 0.50,
                "confidence_method_version": CONFIDENCE_METHOD_VERSION,
                "review_recommendation": "REVIEW_REQUIRED",
                "flags": flags,
                "duration_ms": duration_ms,
            }

            self._validate_contract_schema(response_data)
            return AnalyzeResponse(**response_data)

        # -------------------------------------------------------------------
        # NÍVEL 3: LLM Local (Ollama)
        # -------------------------------------------------------------------
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            question_statement=request.question_statement,
            reference_answer=request.reference_answer,
            rubric=request.rubric,
            answer_text=request.answer_text,
        )

        try:
            llm_response_text = await self.ollama_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.2,
                format_json=True,
            )
        except (OllamaConnectionError, OllamaTimeoutError) as exc:
            logger.error("Falha ao comunicar com o runtime Ollama: %s", exc)
            # RN-017: NUNCA fabricar resposta simulada em modo real quando o Ollama cai
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI Engine indisponível — runtime Ollama local inacessível ou fora do ar. "
                    "Correção assistida temporariamente indisponível (RN-017)."
                ),
            )

        # Parsing tolerante e validação de saída
        parsed_data, repair_applied = await self._parse_with_repair(
            llm_response_text, request.rubric
        )

        if repair_applied:
            flags.append("SCHEMA_REPAIR_APPLIED")

        # Processamento dos critérios e limites de pontuação
        raw_criterion_scores = self._normalize_criterion_scores(
            parsed_data.get("criterion_scores", []), request.rubric, flags
        )

        # Cálculo de confiança heurística conforme ADR-008
        overall_conf, criterion_outputs, review_rec = calculate_confidence(
            criterion_scores_raw=raw_criterion_scores,
            total_rubric_criteria_count=len(request.rubric),
            schema_repair_applied=repair_applied,
            schema_valid=True,
            rule_signals=rule_signals,
            flags=flags,
        )

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        response_data = {
            "schema_version": "1.0",
            "engine_mode": "real",
            "model": settings.ai_model_name,
            "criterion_scores": [c.model_dump() for c in criterion_outputs],
            "overall_confidence": overall_conf,
            "confidence_method_version": CONFIDENCE_METHOD_VERSION,
            "review_recommendation": review_rec,
            "flags": flags,
            "duration_ms": duration_ms,
        }

        # Validação final estrita contra o schema oficial de contrato
        self._validate_contract_schema(response_data)

        logger.info(
            "Análise concluída com sucesso",
            extra={
                "overall_confidence": overall_conf,
                "review_recommendation": review_rec,
                "flags": flags,
                "duration_ms": duration_ms,
            },
        )

        return AnalyzeResponse(**response_data)

    async def _parse_with_repair(
        self,
        raw_text: str,
        rubric: List[RubricCriterionInput],
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Tenta parsear o JSON retornado pelo LLM. Se inválido ou ausente de criterion_scores,
        executa UMA tentativa de reparo pedindo a correção ao modelo.
        """
        parsed = extract_json_from_text(raw_text)
        if parsed and "criterion_scores" in parsed and isinstance(parsed["criterion_scores"], list):
            return parsed, False

        # Dispara UMA tentativa de reparo
        logger.warning("Saída do modelo inválida. Iniciando UMA tentativa de reparo JSON")
        error_details = (
            "JSON não pôde ser decodificado ou chave 'criterion_scores' não foi encontrada."
        )

        try:
            repaired_text = await self.ollama_client.repair_json(raw_text, error_details)
            repaired_parsed = extract_json_from_text(repaired_text)
            if (
                repaired_parsed
                and "criterion_scores" in repaired_parsed
                and isinstance(repaired_parsed["criterion_scores"], list)
            ):
                logger.info("Tentativa de reparo JSON bem-sucedida")
                return repaired_parsed, True
        except Exception as exc:
            logger.error("Erro durante a tentativa de reparo: %s", exc)

        # Se após a tentativa de reparo continuar inválido, retorna erro 502 claro sem inventar notas
        logger.error("Reparo falhou. Rejeitando saída com erro 502.")
        raise HTTPException(
            status_code=502,
            detail="Não foi possível obter uma saída estruturada válida do modelo de IA após tentativa de reparo.",
        )

    def _normalize_criterion_scores(
        self,
        scores_list: List[Dict[str, Any]],
        rubric: List[RubricCriterionInput],
        flags: List[FlagEnum],
    ) -> List[Dict[str, Any]]:
        """
        Valida que cada critério da rubrica tenha sua nota no intervalo [0, max_score]
        e garante tipos consistentes.
        """
        rubric_map = {c.criterion_id: c for c in rubric}
        normalized: List[Dict[str, Any]] = []
        found_crit_ids = set()

        for item in scores_list:
            cid = str(item.get("criterion_id", "")).strip()
            if cid not in rubric_map:
                continue

            found_crit_ids.add(cid)
            rubric_crit = rubric_map[cid]
            max_score = float(rubric_crit.max_score)

            try:
                score = float(item.get("score", 0.0))
            except (ValueError, TypeError):
                score = 0.0

            # Garante limites [0, max_score]
            if score < 0:
                score = 0.0
            elif score > max_score:
                score = max_score

            reason = str(item.get("reason", "")).strip()
            if not reason:
                reason = "Critério avaliado pelo modelo."

            evidence = str(item.get("evidence", "")).strip()

            normalized.append(
                {
                    "criterion_id": cid,
                    "score": round(score, 2),
                    "max_score": round(max_score, 2),
                    "reason": reason,
                    "evidence": evidence,
                }
            )

        # Se algum critério da rubrica foi omitido pelo LLM, completa com nota 0 e flag LOW_COVERAGE
        for cid, rubric_crit in rubric_map.items():
            if cid not in found_crit_ids:
                if "LOW_COVERAGE" not in flags:
                    flags.append("LOW_COVERAGE")
                normalized.append(
                    {
                        "criterion_id": cid,
                        "score": 0.0,
                        "max_score": round(rubric_crit.max_score, 2),
                        "reason": "Critério não abordado na avaliação gerada pelo modelo.",
                        "evidence": "",
                    }
                )

        return normalized

    def _validate_contract_schema(self, data: Dict[str, Any]) -> None:
        """
        Valida a estrutura do dicionário contra o schema oficial em docs/contracts/ai-engine-output.schema.json.
        """
        schema = get_output_schema()
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            logger.error(
                "Falha na validação contra docs/contracts/ai-engine-output.schema.json: %s",
                exc.message,
                extra={"validation_error": exc.message, "path": list(exc.path)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Saída gerada não atende ao schema oficial do contrato: {exc.message}",
            )
