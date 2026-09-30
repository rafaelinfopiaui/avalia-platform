"""Utilitarios de normalizacao e metricas CER/WER, conforme protocolo
congelado (secao 9): NFC, colapsa espacos multiplos, trim; preserva
maiuscula/minuscula, pontuacao e acentuacao (erro de acento conta)."""
import unicodedata
import re


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _levenshtein(a, b):
    """Distancia de edicao classica (insercao/delecao/substituicao custo 1)."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            custo = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + custo)
        prev = cur
    return prev[-1]


def cer(referencia: str, hipotese: str) -> float | None:
    """Character Error Rate. None se referencia vazia (usar tratamento
    especial do criterio eliminatorio, nao CER)."""
    ref = normalizar(referencia)
    hip = normalizar(hipotese)
    if len(ref) == 0:
        return None
    dist = _levenshtein(list(ref), list(hip))
    return dist / len(ref)


def wer(referencia: str, hipotese: str) -> float | None:
    """Word Error Rate. None se referencia vazia."""
    ref = normalizar(referencia).split(" ")
    hip = normalizar(hipotese).split(" ")
    ref = [w for w in ref if w]
    hip = [w for w in hip if w]
    if len(ref) == 0:
        return None
    dist = _levenshtein(ref, hip)
    return dist / len(ref)
