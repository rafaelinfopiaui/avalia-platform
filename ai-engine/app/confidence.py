"""
Cálculo de confiança do AvalIA AI Engine conforme ADR-008.

IMPORTANTE / RN-016:
Este cálculo é um indicador HEURÍSTICO operacional de necessidade de revisão humana.
NÃO é uma probabilidade estatística calibrada (pendência D-07, aguarda piloto com dados reais).
Versão do método: heuristic-v1.

Faixas operacionais (ADR-008):
- Alta: >= 0.85  -> REVIEW_OPTIONAL
- Média: 0.60 a 0.84 -> REVIEW_RECOMMENDED
- Baixa: < 0.60  -> REVIEW_REQUIRED
"""
from typing import Dict, List, Tuple
from app.schemas import CriterionScoreOutput, ReviewRecommendation

CONFIDENCE_METHOD_VERSION = "heuristic-v1"

# Pesos da heurística conforme ADR-008
WEIGHT_SCHEMA = 0.40    # Validade do schema JSON (peso alto)
WEIGHT_COVERAGE = 0.35  # Cobertura de critérios da rubrica
WEIGHT_RULES = 0.25     # Concordância com sinais de regras (Nível 1)


def calculate_confidence(
    criterion_scores_raw: List[Dict[str, any]],
    total_rubric_criteria_count: int,
    schema_repair_applied: bool,
    schema_valid: bool,
    rule_signals: Dict[str, Dict[str, any]],
    flags: List[str],
) -> Tuple[float, List[CriterionScoreOutput], ReviewRecommendation]:
    """
    Calcula a confiança por critério e a confiança geral de forma determinística.

    Retorna:
    - overall_confidence: float entre 0.0 e 1.0
    - criterion_scores: lista de CriterionScoreOutput com confidence individual calculada
    - review_recommendation: REVIEW_OPTIONAL | REVIEW_RECOMMENDED | REVIEW_REQUIRED
    """
    # 1. Componente de validade do schema
    if not schema_valid:
        c_schema = 0.20
    elif schema_repair_applied:
        c_schema = 0.60
    else:
        c_schema = 1.00

    # 2. Componente de cobertura de critérios
    returned_count = len(criterion_scores_raw)
    if total_rubric_criteria_count > 0:
        c_coverage = min(1.0, returned_count / total_rubric_criteria_count)
    else:
        c_coverage = 1.0

    if c_coverage < 1.0 and "LOW_COVERAGE" not in flags:
        flags.append("LOW_COVERAGE")

    # 3. Componente de regras e pontuação por critério
    criterion_outputs: List[CriterionScoreOutput] = []
    rule_agreements: List[float] = []

    for item in criterion_scores_raw:
        crit_id = item["criterion_id"]
        score = float(item["score"])
        max_score = float(item["max_score"])
        reason = str(item.get("reason", "")).strip()
        evidence = str(item.get("evidence", "")).strip()

        score_ratio = (score / max_score) if max_score > 0 else 0.0
        signal_info = rule_signals.get(crit_id, {"signal_present": True, "match_ratio": 1.0})
        signal_present = signal_info.get("signal_present", False)

        # Concordância entre sinal de regra e nota do LLM
        if score_ratio >= 0.5 and signal_present:
            # Termos presentes e nota positiva: concordância alta
            crit_agreement = 1.0
        elif score_ratio < 0.5 and not signal_present:
            # Termos ausentes e nota baixa: concordância alta
            crit_agreement = 0.95
        elif score_ratio >= 0.5 and not signal_present:
            # Aluno usou sinônimos válidos ou explicação conceitual sem termos exatos
            crit_agreement = 0.75
        else:
            # Termos citados mas com erro conceitual diagnosticado pelo LLM
            crit_agreement = 0.70

        rule_agreements.append(crit_agreement)

        # Confiança individual do critério (heurística)
        crit_conf = (
            (WEIGHT_SCHEMA * c_schema)
            + (WEIGHT_COVERAGE * c_coverage)
            + (WEIGHT_RULES * crit_agreement)
        )
        crit_conf_clamped = max(0.0, min(1.0, round(crit_conf, 2)))

        criterion_outputs.append(
            CriterionScoreOutput(
                criterion_id=crit_id,
                score=round(score, 2),
                max_score=round(max_score, 2),
                reason=reason if reason else "Critério avaliado pelo modelo.",
                evidence=evidence,
                confidence=crit_conf_clamped,
            )
        )

    avg_rules = (sum(rule_agreements) / len(rule_agreements)) if rule_agreements else 1.0

    # Confiança geral combinada (heurística, ADR-008)
    overall_conf = (
        (WEIGHT_SCHEMA * c_schema)
        + (WEIGHT_COVERAGE * c_coverage)
        + (WEIGHT_RULES * avg_rules)
    )
    overall_conf_clamped = max(0.0, min(1.0, round(overall_conf, 2)))

    # Determinação da recomendação de revisão
    # Casos mandatórios de revisão:
    if "EMPTY_ANSWER" in flags or "SIMULATED_MODE" in flags or not schema_valid:
        review_recommendation: ReviewRecommendation = "REVIEW_REQUIRED"
    elif "PROMPT_INJECTION_SUSPECTED" in flags:
        # Prompt injection detectado: não penaliza a nota acadêmica, mas exige revisão humana
        review_recommendation = "REVIEW_REQUIRED"
    elif overall_conf_clamped >= 0.85:
        review_recommendation = "REVIEW_OPTIONAL"
    elif overall_conf_clamped >= 0.60:
        review_recommendation = "REVIEW_RECOMMENDED"
    else:
        review_recommendation = "REVIEW_REQUIRED"

    return overall_conf_clamped, criterion_outputs, review_recommendation
