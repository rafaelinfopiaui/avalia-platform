"""
Nível 1 da cascata de decisão: extração de sinais básicos de regras.
Identifica presença de conceitos ou palavras-chave esperadas por critério da rubrica.
Usado exclusivamente como insumo determinístico para o cálculo de confiança (ADR-008),
NUNCA decide a nota final por si só.
"""
import re
import unicodedata
from typing import Dict, List, Set
from app.schemas import RubricCriterionInput

# Stopwords básicas em português para não poluir palavras-chave de regras
STOPWORDS: Set[str] = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "pelo", "pela", "pelos", "pelas", "para", "pra",
    "com", "sem", "sob", "sobre", "entre", "que", "e", "ou", "mas", "se", "como", "quando",
    "onde", "porque", "por que", "pois", "este", "esta", "estes", "estas", "esse", "essa",
    "esses", "essas", "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo",
    "ele", "ela", "eles", "elas", "meu", "minha", "seu", "sua", "seus", "suas", "nosso",
    "nossa", "ser", "estar", "ter", "haver", "fazer", "são", "foi", "era", "será", "tem",
    "têm", "tinha", "havia", "qual", "quais", "muito", "mais", "menos", "bem", "mal",
    "criterio", "critério", "avaliação", "avaliacao", "pontuação", "pontuacao", "aluno"
}


def _normalize(text: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text)
    clean = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    return re.sub(r"[^\w\s]", " ", clean)


def extract_criterion_keywords(criterion: RubricCriterionInput) -> Set[str]:
    """
    Extrai palavras-chave candidatas a partir do nome e descrição do critério.
    Tokens significativos (>= 3 letras ou siglas).
    """
    source_text = f"{criterion.name} {criterion.description}"
    normalized = _normalize(source_text)
    tokens = re.findall(r"\b[a-z0-9_]+\b", normalized)

    keywords = set()
    for token in tokens:
        if len(token) >= 3 and token not in STOPWORDS:
            keywords.add(token)
    return keywords


def analyze_rule_signals(
    rubric: List[RubricCriterionInput],
    answer_text: str,
) -> Dict[str, Dict[str, any]]:
    """
    Avalia sinais de regras simples para cada critério da rubrica.
    Retorna um dicionário indexado por criterion_id com:
    - keywords: palavras-chave extraídas do critério
    - matched_keywords: palavras encontradas na resposta do aluno
    - match_ratio: proporção de palavras-chave encontradas [0.0, 1.0]
    - signal_present: booleano indicando se ao menos um termo relevante foi detectado
    """
    normalized_answer = _normalize(answer_text)
    answer_tokens = set(re.findall(r"\b[a-z0-9_]+\b", normalized_answer))

    results: Dict[str, Dict[str, any]] = {}
    for crit in rubric:
        keywords = extract_criterion_keywords(crit)
        if not keywords:
            # Critério sem termos específicos extraíveis
            results[crit.criterion_id] = {
                "keywords": [],
                "matched_keywords": [],
                "match_ratio": 1.0,
                "signal_present": True,
            }
            continue

        matched = keywords.intersection(answer_tokens)
        ratio = len(matched) / len(keywords)
        results[crit.criterion_id] = {
            "keywords": sorted(list(keywords)),
            "matched_keywords": sorted(list(matched)),
            "match_ratio": round(ratio, 2),
            "signal_present": len(matched) > 0,
        }

    return results
