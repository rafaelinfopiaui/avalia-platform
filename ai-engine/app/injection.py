"""
Módulo de detecção básica de padrões de prompt injection em respostas de estudantes.
Conforme especificação: sinaliza com a flag PROMPT_INJECTION_SUSPECTED sem
penalizar automaticamente o conteúdo acadêmico.
"""
import re
import unicodedata

# Padrões conhecidos de tentativa de injeção de comandos ou evasão de rubrica
INJECTION_PATTERNS = [
    r"ignore\s+(as\s+|todas\s+as\s+|previous\s+|all\s+)?(instru[cç][oõ]es|instructions)",
    r"ignore\s+(a\s+)?(rubrica|rubric)",
    r"desconsidere\s+(as\s+)?(instru[cç][oõ]es|a\s+rubrica|regras)",
    r"esque[cç]a\s+(as\s+)?(instru[cç][oõ]es|regras)",
    r"you\s+are\s+now\b",
    r"voc[eê]\s+agora\s+[eé]\b",
    r"\bact\s+as\b",
    r"\baja\s+como\b",
    r"(atribua|atribuir|dar|d[eê]|give)\s+(a\s+)?(nota\s+m[aá]xima|full\s+marks|score\s+10|nota\s+10)",
    r"system\s+prompt\b",
    r"instru[cç][oõ]es\s+do\s+sistema\b",
    r"(revele|mostre|print)\s+(o\s+)?(prompt|system)",
    r"voc[eê]\s+[eé]\s+um\s+assistente\s+livre",
    r"jailbreak\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def _normalize_text(text: str) -> str:
    """Normaliza texto removendo acentos para comparação uniforme."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def detect_prompt_injection(text: str) -> bool:
    """
    Verifica se o texto contém padrões suspeitos de prompt injection.
    Retorna True se suspeito, False caso contrário.
    """
    if not text:
        return False

    # Checa no texto original
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True

    # Checa também no texto normalizado sem acentos
    normalized = _normalize_text(text)
    for pattern in COMPILED_PATTERNS:
        if pattern.search(normalized):
            return True

    return False
