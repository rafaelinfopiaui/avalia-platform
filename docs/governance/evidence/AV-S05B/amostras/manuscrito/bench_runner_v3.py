#!/usr/bin/env python3
"""Runner de benchmark OCR v3 — eixo manuscrito (AV-S05B).

v2 = v1 + OLLAMA_OPCOES["num_ctx"]=8192 (correção de transporte).
v3 = v2 + correções de SPEC_v3.md (NÃO congelado; revisão pendente):
  C1  corpo do erro HTTP do Ollama capturado, truncado e sanitizado
      (`sanitizar_corpo_erro`); URLError/timeout com mensagem sanitizada.
  C2  `_carregar` envia as mesmas options de contexto que `_inferir`: a
      reconfiguração de contexto cai em t_carga_s, não na 1ª t_inferencia_s.
  C3  options POR CANDIDATO (`OLLAMA_OPCOES_POR_MODELO`); num_ctx=8192 só
      para qwen2.5vl:3b; demais modelos usam o default do runtime.
  C4  seed fixa declarada (`OLLAMA_SEED`) e options efetivas registradas por
      candidato. Seed fixa + temperature=0 REDUZEM a variação, mas NÃO
      garantem determinismo absoluto (versão do runtime, backend, hardware,
      paralelismo).
  C5  falha de contexto permanece falha_execucao: sem aumento automático de
      num_ctx, sem resize/compressão de imagem, sem retry oculto.
Idêntico ao v2 em scoring, prompt e manejo de imagem.

Implementa o contrato em
docs/governance/evidence/AV-S05B/amostras/manuscrito/RUNNER_SPEC_CONGELADA.md.

Estrutura:
  1. Scoring (normalizar, levenshtein, cer, wer, avaliar_amostra): stdlib pura,
     independente de qualquer motor OCR, testável isolado.
  2. Detecção de abstenção (somente saídas de VLM) — heurística documentada em
     `detectar_abstencao`.
  3. Adaptadores de candidato (tesseract, easyocr, ollama_vlm). Cada um expõe
     `executar(imagem)` -> (texto_saida, t_carga_s, t_inferencia_s, status, erro).
     Nunca recebem a referência; nunca inventam saída em caso de erro.
  4. Orquestração: manifesto JSON -> inferência -> (só então) leitura da
     referência -> scoring -> um JSON por (candidato, amostra) em
     resultados_brutos/ -> agregação com denominadores explícitos.
  5. --dry-run: roda só scoring + agregação sobre casos sintéticos embutidos,
     sem chamar nenhum motor e sem ler nenhum arquivo de amostra.

Formato do manifesto (caminhos relativos ao diretório do manifesto):
  {
    "amostras": [
      {"amostra": "MAN-XX", "conjunto": "dev" | "eval",
       "imagem_png": "trabalho_png/MAN-XX.png",
       "referencia_txt": "referencias/MAN-XX_referencia.txt",
       "rotulo": "texto livre opcional (ex.: desvio do controle de ilegibilidade)"}
    ]
  }

Uso:
  python3 bench_runner.py --dry-run
  python3 bench_runner.py --manifesto manifesto.json \
      [--candidatos tesseract,easyocr,ollama:moondream:v2,ollama:qwen2.5vl:3b] \
      [--saida resultados_brutos] [--sobrescrever]
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import os
import platform
import re
import subprocess
import sys
import socket
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Parâmetros congelados
# ---------------------------------------------------------------------------

PROMPT_VLM = (
    "Transcreva literalmente todo o texto manuscrito desta imagem, exatamente como "
    "está escrito, preservando acentuação, pontuação e maiúsculas. Responda apenas "
    "com o texto transcrito, sem comentários. Se não houver texto legível, responda "
    "com uma linha vazia."
)

TESSERACT_LANG = "por"
# Spec §7: Reader(['pt']). O pedido de execução mencionava ['pt', 'en']; a spec
# congelada prevalece (divergência registrada no relatório de entrega).
EASYOCR_IDIOMAS = ["pt"]
OLLAMA_URL = "http://127.0.0.1:11434"
# RUNNER v3 (C4): seed fixa declarada. Seed fixa + temperature=0 REDUZEM a variação
# entre execuções, mas NÃO garantem determinismo absoluto (dependem de versão do
# runtime, backend, hardware e paralelismo). Não afirmar reprodutibilidade bit-a-bit.
OLLAMA_SEED = 42
NOTA_DETERMINISMO = (
    "seed fixa e temperature=0 reduzem a variação, mas não garantem determinismo "
    "absoluto (dependem de versão do runtime, backend, hardware, paralelismo)"
)
# Default conservador aplicado a todo candidato Ollama: sem num_ctx (vale o default
# do runtime Ollama).
OLLAMA_OPCOES_PADRAO: Dict[str, Any] = {"temperature": 0, "seed": OLLAMA_SEED}
# RUNNER v3 (C3): options POR CANDIDATO, sobrepostas ao default. Substitui o
# OLLAMA_OPCOES global do v2, que fazia todo modelo herdar num_ctx=8192.
# qwen2.5vl:3b — correção de TRANSPORTE do v2 (2026-10-15). Causa comprovada do
# HTTP 400 na rodada 1: num_ctx padrão do Ollama (4096) estourado pelos tokens de
# VISÃO da imagem (n_prompt_tokens 4107-4156 nas 5 falhas vs 4073-4084 nas 3 ok;
# corpo real do erro: exceed_context_size_error). NÃO altera imagem, prompt,
# modelo nem temperatura.
OLLAMA_OPCOES_POR_MODELO: Dict[str, Dict[str, Any]] = {
    "qwen2.5vl:3b": {"num_ctx": 8192},
}
OLLAMA_TIMEOUT_S = 600
# RUNNER v3 (C1): limites do corpo de erro HTTP. Lê-se no máximo
# LIMITE_LEITURA_ERRO bytes; o corpo sanitizado é truncado a LIMITE_CORPO_ERRO chars.
LIMITE_LEITURA_ERRO = 64 * 1024
LIMITE_CORPO_ERRO = 2048
TESSERACT_TIMEOUT_S = 300

CANDIDATOS_PADRAO = [
    "tesseract",
    "easyocr",
    "ollama:moondream:v2",
    "ollama:qwen2.5vl:3b",
]

STATUS_OK = "ok"
STATUS_FALHA = "falha_execucao"
STATUS_ABSTENCAO = "abstencao"

# Diretórios cujo conteúdo nunca pode ser entrada de candidato (spec §1).
_DIRS_PROIBIDOS_COMO_ENTRADA = ("referencias", "originais", "auditoria")


# ---------------------------------------------------------------------------
# 1. Scoring (stdlib pura)
# ---------------------------------------------------------------------------

def normalizar(texto: Optional[str]) -> str:
    """NFC + colapso de espaços + trim. Preserva caixa, pontuação e acentos.

    "Espaço" aqui é qualquer whitespace Unicode (espaço, tab, quebra de linha,
    NBSP...), via str.split() sem argumento: quebras de linha viram um único
    espaço, para que diferenças de layout de linha não contem como erro.
    """
    if texto is None:
        return ""
    return " ".join(unicodedata.normalize("NFC", texto).split())


def levenshtein(a: Sequence[Any], b: Sequence[Any]) -> int:
    """Distância de edição (substituição, inserção, remoção; custo 1)."""
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, x in enumerate(a, start=1):
        atual = [i]
        for j, y in enumerate(b, start=1):
            atual.append(min(
                anterior[j] + 1,              # remoção
                atual[j - 1] + 1,             # inserção
                anterior[j - 1] + (x != y),   # substituição
            ))
        anterior = atual
    return anterior[-1]


def _palavras(texto_normalizado: str) -> List[str]:
    return texto_normalizado.split(" ") if texto_normalizado else []


def cer(saida: Optional[str], ref: Optional[str]) -> Optional[float]:
    """CER sobre textos normalizados; None se a referência normalizada é vazia."""
    s, r = normalizar(saida), normalizar(ref)
    if not r:
        return None
    return levenshtein(s, r) / max(1, len(r))


def wer(saida: Optional[str], ref: Optional[str]) -> Optional[float]:
    """WER sobre palavras (split por espaço após normalizar); None se ref vazia."""
    s, r = _palavras(normalizar(saida)), _palavras(normalizar(ref))
    if not r:
        return None
    return levenshtein(s, r) / max(1, len(r))


def avaliar_amostra(saida_bruta: Optional[str], ref_bruta: Optional[str]) -> Dict[str, Any]:
    norm_saida = normalizar(saida_bruta)
    norm_ref = normalizar(ref_bruta)
    ref_vazia = not norm_ref
    produziu_texto = bool(norm_saida)
    return {
        "normalizado_saida": norm_saida,
        "normalizado_ref": norm_ref,
        "cer": None if ref_vazia else cer(saida_bruta, ref_bruta),
        "wer": None if ref_vazia else wer(saida_bruta, ref_bruta),
        "ref_vazia": ref_vazia,
        "produziu_texto": produziu_texto,
        "invencao_em_vazio": ref_vazia and produziu_texto,
    }


# ---------------------------------------------------------------------------
# 2. Detecção de abstenção (aplicada SOMENTE a saídas de VLM)
# ---------------------------------------------------------------------------
#
# Heurística exata:
#   a) A saída é "dobrada" APENAS para detecção (nunca para scoring): NFKD,
#      remoção de diacríticos, minúsculas, whitespace colapsado.
#   b) Se a saída dobrada tem mais de LIMITE_ABSTENCAO_CHARS caracteres, NÃO é
#      abstenção (uma transcrição longa que menciona "ilegível" é tratada como
#      transcrição; protocolo §6: abstenção não pode incluir texto junto).
#   c) É abstenção se:
#      c1) a saída inteira, sem pontuação/colchetes/aspas, é um marcador de
#          ilegibilidade (MARCADORES_ILEGIBILIDADE), ou o radical "ilegivel"
#          seguido de até 6 caracteres de ruído (cf. desvio de 2026-09-29 no
#          protocolo: "ilegivel.", "ilegivelive."); ou
#      c2) contém alguma das PADROES_RECUSA (frases de recusa/meta-comentário
#          que referem leitura/transcrição/texto/imagem — não basta "não
#          consigo" sozinho, para não capturar manuscrito como "não consigo ir").
#   d) Saída vazia NÃO é abstenção: é status ok com produziu_texto=False (o
#      prompt instrui a responder com linha vazia quando não há texto).
#   e) Marcadores parciais no meio de uma transcrição (ex.: "abc [ilegível] def")
#      NÃO são abstenção: status ok, o marcador é pontuado como texto.
# Limitação conhecida: uma transcrição curta cujo conteúdo real seja uma frase
# de recusa seria falso positivo. Cada registro guarda o texto verbatim e o
# padrão que casou (`abstencao_padrao`) para auditoria.

LIMITE_ABSTENCAO_CHARS = 300

MARCADORES_ILEGIBILIDADE = {
    "ilegivel", "texto ilegivel", "ilegiveis", "nao legivel", "illegible",
    "unreadable", "sem texto", "sem texto legivel", "nenhum texto",
    "nenhum texto legivel", "no text", "no legible text", "nao ha texto",
    "nao ha texto legivel",
}

PADROES_RECUSA = [
    r"\bnao (consigo|e possivel|foi possivel|posso|sou capaz de)\b.{0,40}?"
    r"\b(ler|transcrever|identificar|reconhecer|decifrar|distinguir|enxergar|extrair|interpretar)\b",
    r"\b(nao ha|nao existe|nao contem|nao possui|nao apresenta|sem|nenhum)\b.{0,20}?"
    r"\btexto\b.{0,30}?\b(legivel|visivel|identificavel|reconhecivel|na imagem|nesta imagem)\b",
    r"\b(nao ha|nao existe|nao contem|nao possui|nao apresenta|nenhum)\b.{0,10}?\btexto\b",
    r"\btexto\b.{0,15}?\b(ilegivel|nao (e |esta )?legivel|indecifravel)\b",
    r"\b(i can ?not|i can't|i cannot|i am unable|i'm unable|unable to)\b.{0,40}?"
    r"\b(read|transcribe|identify|see|make out|extract|recognize|decipher)\b",
    r"\bno (legible |readable |visible |discernible )?text\b",
    r"\b(illegible|unreadable)\b",
]
_PADROES_RECUSA_RE = [re.compile(p) for p in PADROES_RECUSA]
_RE_ILEGIVEL_RUIDO = re.compile(r"^ilegivel\w{0,6}$")


def _dobrar_para_deteccao(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.lower().split())


def detectar_abstencao(texto: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Retorna (é_abstenção, padrão_que_casou). Ver heurística acima."""
    dobrado = _dobrar_para_deteccao(texto or "")
    if not dobrado or len(dobrado) > LIMITE_ABSTENCAO_CHARS:
        return False, None
    nucleo = " ".join(re.sub(r"[^\w\s']", " ", dobrado).split())
    if nucleo in MARCADORES_ILEGIBILIDADE:
        return True, "marcador:" + nucleo
    if _RE_ILEGIVEL_RUIDO.match(nucleo):
        return True, "marcador_ruido:" + nucleo
    for padrao, regex in zip(PADROES_RECUSA, _PADROES_RECUSA_RE):
        if regex.search(dobrado):
            return True, "recusa:" + padrao
    return False, None


# ---------------------------------------------------------------------------
# 3. Adaptadores de candidato
# ---------------------------------------------------------------------------
#
# Contrato: executar(imagem) -> (texto_saida, t_carga_s, t_inferencia_s, status, erro)
#   - A carga (binário/pesos/modelo) é medida uma única vez, na 1ª chamada; o
#     t_carga_s vem preenchido só no resultado dessa 1ª chamada (None nas demais).
#   - t_inferencia_s mede apenas a inferência com o motor já carregado.
#   - Qualquer exceção -> status falha_execucao, texto_saida None, erro = mensagem.
#   - Se a carga falhou, todas as chamadas subsequentes retornam falha_execucao
#     com o mesmo erro (a amostra permanece no denominador).

Resultado = Tuple[Optional[str], Optional[float], Optional[float], str, Optional[str]]


class Adaptador:
    nome = "base"
    detecta_abstencao = False

    def __init__(self) -> None:
        self._carregado = False
        self._erro_carga: Optional[str] = None

    def _carregar(self) -> None:
        raise NotImplementedError

    def _inferir(self, imagem: str) -> str:
        raise NotImplementedError

    def parametros(self) -> Dict[str, Any]:
        return {}

    def executar(self, imagem: str) -> Resultado:
        t_carga: Optional[float] = None
        if not self._carregado:
            self._carregado = True
            inicio = time.perf_counter()
            try:
                self._carregar()
            except Exception as exc:  # noqa: BLE001 — registrar qualquer falha real
                self._erro_carga = "carga: %s: %s" % (type(exc).__name__, exc)
            t_carga = time.perf_counter() - inicio
        if self._erro_carga is not None:
            return None, t_carga, None, STATUS_FALHA, self._erro_carga

        inicio = time.perf_counter()
        try:
            texto = self._inferir(imagem)
        except Exception as exc:  # noqa: BLE001
            return (None, t_carga, time.perf_counter() - inicio, STATUS_FALHA,
                    "inferencia: %s: %s" % (type(exc).__name__, exc))
        t_inf = time.perf_counter() - inicio

        if texto is None:
            return None, t_carga, t_inf, STATUS_FALHA, "inferencia: motor retornou None"
        if self.detecta_abstencao and detectar_abstencao(texto)[0]:
            return texto, t_carga, t_inf, STATUS_ABSTENCAO, None
        return texto, t_carga, t_inf, STATUS_OK, None


class AdaptadorTesseract(Adaptador):
    """`tesseract <img> stdout -l por`.

    Carga = `tesseract --version` + `--list-langs` (binário carregado e `por`
    instalado). O tesseract CLI não mantém processo residente: cada inferência
    é um processo novo que recarrega os dados de idioma — limitação registrada.
    """

    nome = "tesseract"

    def _carregar(self) -> None:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True,
                       timeout=TESSERACT_TIMEOUT_S)
        langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True,
                               text=True, check=True, timeout=TESSERACT_TIMEOUT_S)
        if TESSERACT_LANG not in (langs.stdout + langs.stderr).split():
            raise RuntimeError("idioma '%s' não instalado no tesseract" % TESSERACT_LANG)

    def _inferir(self, imagem: str) -> str:
        proc = subprocess.run(["tesseract", imagem, "stdout", "-l", TESSERACT_LANG],
                              capture_output=True, timeout=TESSERACT_TIMEOUT_S)
        if proc.returncode != 0:
            raise RuntimeError("tesseract rc=%d: %s" % (
                proc.returncode, proc.stderr.decode("utf-8", "replace").strip()))
        return proc.stdout.decode("utf-8", "replace")

    def parametros(self) -> Dict[str, Any]:
        return {"comando": "tesseract <img> stdout -l %s" % TESSERACT_LANG}


class AdaptadorEasyOCR(Adaptador):
    """import easyocr + Reader (carga); readtext(detail=0) (inferência).

    download_enabled=False: se os pesos não estiverem presentes, a carga FALHA
    em vez de baixar (download é preparação, fora do benchmark). As linhas
    detectadas são unidas por espaço, na ordem retornada pelo readtext.
    """

    nome = "easyocr"

    def __init__(self) -> None:
        super().__init__()
        self._reader = None

    def _carregar(self) -> None:
        import easyocr  # noqa: WPS433 — import faz parte da carga medida
        self._reader = easyocr.Reader(EASYOCR_IDIOMAS, download_enabled=False, verbose=False)

    def _inferir(self, imagem: str) -> str:
        linhas = self._reader.readtext(imagem, detail=0)
        return " ".join(str(linha) for linha in linhas)

    def parametros(self) -> Dict[str, Any]:
        return {"Reader": {"lang_list": EASYOCR_IDIOMAS, "download_enabled": False},
                "readtext": {"detail": 0}, "juncao_linhas": "espaco"}


# --- Sanitização de erros do Ollama (RUNNER v3, C1) --------------------------
#
# O corpo de um erro HTTP do Ollama é diagnóstico (ex.: exceed_context_size_error
# com n_prompt_tokens/n_ctx), mas pode ecoar a requisição. `sanitizar_corpo_erro`
# mascara: imagens/base64 (campo `images`, data URIs, sequências base64-like
# longas), conteúdo gerado (`response`/`context`), caminhos de arquivo e nomes de
# arquivo de imagem, e credenciais (authorization, api-key, token, cookie, bearer).
# Preserva os campos de diagnóstico (code, type, message, n_prompt_tokens, n_ctx,
# error) — seus valores passam pelo mesmo mascaramento textual. O resultado é
# truncado a LIMITE_CORPO_ERRO caracteres (marcador incluído no limite).
# Trecho de credencial que não pode ser delimitado com segurança é omitido como
# [TRECHO_OMITIDO_NAO_SANITIZAVEL] em vez de passar.

_MASCARA_BASE64 = "[BASE64_OMITIDO]"
_MASCARA_IMAGENS = "[IMAGENS_OMITIDAS]"
_MASCARA_CONTEUDO = "[CONTEUDO_OMITIDO]"
_MASCARA_CREDENCIAL = "[CREDENCIAL_OMITIDA]"
_MASCARA_CAMINHO = "[CAMINHO_OMITIDO]"
_MASCARA_ARQUIVO = "[ARQUIVO_OMITIDO]"
_MARCA_TRUNCADO = "...[truncado]"

CAMPOS_DIAGNOSTICO_OLLAMA = ("code", "type", "message", "n_prompt_tokens", "n_ctx", "error")
_CHAVES_IMAGEM = {"images", "image"}
_CHAVES_CONTEUDO = {"response", "context", "thinking"}
_MASCARA_NAO_SANITIZAVEL = "[TRECHO_OMITIDO_NAO_SANITIZAVEL]"
_RE_CHAVE_CREDENCIAL = re.compile(
    r"(?i)^(?:(?:proxy[-_]?)?authorization|(?:x[-_]?)?api[-_]?key|"
    r"(?:access[-_]?|refresh[-_]?|auth[-_]?)?token|(?:set[-_]?)?cookie)$")

_SEG_CAMINHO = r"[^\s\"'<>|,;:\\/]+"
# Caminho relativo: segmentos sem espaço/pontuação; não começa no meio de outro
# token, de URL (após '/' ou ':') nem de caminho já tratado.
_SEG_RELATIVO = r"[\w.~@+%-]+"
_RE_EXTENSAO = re.compile(r"\.[A-Za-z0-9]{1,5}$")
_RE_MIME = re.compile(r"(?i)^(?:application|image|text|audio|video|multipart|font)/[\w.+-]+$")
_RE_NUMERICO = re.compile(r"^[\d.]+$")


def _mascarar_caminho_relativo(m: "re.Match[str]") -> str:
    """Mascara caminho relativo com >= 2 segmentos. Preserva só os pares de 2
    segmentos sem extensão que são diagnóstico legítimo: tipo MIME
    (application/json) ou razão numérica (4131/4096)."""
    trecho = m.group(0)
    segmentos = re.split(r"[/\\]", trecho)
    if len(segmentos) == 2 and not _RE_EXTENSAO.search(segmentos[-1]):
        if _RE_MIME.match(trecho) or all(_RE_NUMERICO.match(s) for s in segmentos):
            return trecho
    return _MASCARA_CAMINHO


# Nomes de credencial em texto livre: prefixos proxy/x/set/access/... com '-', '_'
# ou colados. Lookbehind no lugar de '\b' para casar após '_' (proxy_authorization).
_CHAVES_CREDENCIAL_TEXTO = (r"(?<![A-Za-z0-9])(?:(?:proxy[-_]?)?authorization|"
                            r"(?:x[-_]?)?api[-_]?key|"
                            r"(?:access[-_]?|refresh[-_]?|auth[-_]?)?token|"
                            r"(?:set[-_]?)?cookie)\b")
_RES_TEXTO = [
    # data URI de imagem
    (re.compile(r"(?i)data:[\w/+.-]+;base64,[A-Za-z0-9+/=]*"), _MASCARA_BASE64),
    # fragmento `"images": [...]` em corpo não-JSON ou truncado (lista possivelmente aberta)
    (re.compile(r"(?i)(\"?\bimages?\"?\s*[:=]\s*)\[[^\]]*\]?"), r"\1" + _MASCARA_IMAGENS),
    # esquema de autenticação com credencial
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+"), r"\1 " + _MASCARA_CREDENCIAL),
    # cabeçalho/par chave-valor de credencial (authorization, api-key, token, cookie)
    (re.compile(r"(?i)(" + _CHAVES_CREDENCIAL_TEXTO + r")"
                r"(\"?'?\s*[:=]\s*)(\"[^\"]*\"?|'[^']*'?|[^\r\n,}&]*)"),
     r"\1\2" + _MASCARA_CREDENCIAL),
    # nome de cabeçalho de credencial seguido de valor SEM separador ':'/'=' (ex.:
    # "x_api_key sk-abc123"): estrutura ambígua, não dá para delimitar o valor com
    # segurança -> o trecho é omitido e a omissão fica registrada. Só para valores
    # com cara de segredo (>= 8 chars com dígito/símbolo); "token" fica de fora por
    # ser palavra comum em mensagens de erro.
    (re.compile(r"(?i)((?<![A-Za-z0-9])(?:(?:proxy[-_]?)?authorization|"
                r"(?:x[-_]?)?api[-_]?key|(?:set[-_]?)?cookie)\b)"
                r"[ \t]+(?!\[)(?=[^\s]*[\d_.+/=-])[^\s,;}]{8,}"),
     r"\1 " + _MASCARA_NAO_SANITIZAVEL),
    # sequência base64-like longa (antes dos caminhos: base64 contém '/')
    (re.compile(r"[A-Za-z0-9+/]{64,}={0,2}"), _MASCARA_BASE64),
    # caminho absoluto/home com >= 2 segmentos; segmentos internos podem ter espaços
    # (ex.: "Projeto Estágio"). Não casa caminho de URL (precedido de host/porta).
    (re.compile(r"(?<![\w:/.])(?:~|[A-Za-z]:)?(?:[/\\]%s(?: %s)*(?=[/\\]))+[/\\]%s"
                % (_SEG_CAMINHO, _SEG_CAMINHO, _SEG_CAMINHO)), _MASCARA_CAMINHO),
    # caminho relativo com >= 2 segmentos (coleta/referencias/ref.txt); 1 segmento,
    # URL e MIME/razão numérica de 2 segmentos não são mascarados
    (re.compile(r"(?<![\w:/\\.~@+%%-])%s(?:[/\\]%s)+" % (_SEG_RELATIVO, _SEG_RELATIVO)),
     _mascarar_caminho_relativo),
    # nome de arquivo de imagem solto
    (re.compile(r"(?i)\b[\w.-]+\.(?:png|jpe?g|heic|heif|tiff?|webp|bmp|gif)\b"), _MASCARA_ARQUIVO),
]


def _sanitizar_texto(texto: str) -> str:
    for regex, substituto in _RES_TEXTO:
        texto = regex.sub(substituto, texto)
    return texto


def _sanitizar_json(valor: Any) -> Any:
    if isinstance(valor, dict):
        saida = {}
        for chave, v in valor.items():
            nome = str(chave)
            if nome.lower() in _CHAVES_IMAGEM:
                saida[chave] = _MASCARA_IMAGENS
            elif nome.lower() in _CHAVES_CONTEUDO:
                saida[chave] = _MASCARA_CONTEUDO
            elif nome not in CAMPOS_DIAGNOSTICO_OLLAMA and _RE_CHAVE_CREDENCIAL.match(nome):
                saida[chave] = _MASCARA_CREDENCIAL
            else:
                saida[chave] = _sanitizar_json(v)
        return saida
    if isinstance(valor, list):
        return [_sanitizar_json(v) for v in valor]
    if isinstance(valor, str):
        return _sanitizar_texto(valor)
    return valor


def _sanitizar_estrutura(corpo: Any) -> Tuple[Any, str]:
    """(objeto JSON sanitizado ou None, texto sanitizado SEM truncar)."""
    if isinstance(corpo, bytes):
        corpo = corpo.decode("utf-8", "replace")
    texto = "" if corpo is None else str(corpo)
    try:
        obj = json.loads(texto)
    except ValueError:
        return None, _sanitizar_texto(texto)
    obj = _sanitizar_json(obj)
    return obj, json.dumps(obj, ensure_ascii=False)


def _truncar(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto
    return texto[:max(0, limite - len(_MARCA_TRUNCADO))] + _MARCA_TRUNCADO


def sanitizar_corpo_erro(corpo: Any, limite: int = LIMITE_CORPO_ERRO) -> str:
    """Corpo de erro (str/bytes) -> texto sanitizado com no máximo `limite` chars."""
    return _truncar(_sanitizar_estrutura(corpo)[1], limite)


def _resumo_diagnostico(obj: Any) -> Optional[str]:
    """Ex.: 'exceed_context_size_error n_prompt_tokens=4131 n_ctx=4096'.

    Lê `type`, `n_prompt_tokens` e `n_ctx` do objeto (já sanitizado) ou de seu
    campo `error`; se `error` for string simples, usa-a. None se nada útil.
    """
    if not isinstance(obj, dict):
        return None
    fontes = [obj] + ([obj["error"]] if isinstance(obj.get("error"), dict) else [])
    partes: List[str] = []
    for fonte in fontes:
        if isinstance(fonte.get("type"), str):
            partes.append(fonte["type"])
        for campo in ("n_prompt_tokens", "n_ctx"):
            if isinstance(fonte.get(campo), (int, float, str)):
                partes.append("%s=%s" % (campo, fonte[campo]))
    if not partes and isinstance(obj.get("error"), str):
        partes.append(obj["error"])
    return _truncar(" ".join(partes), 256) if partes else None


def _mensagem_erro_http(exc: urllib.error.HTTPError) -> str:
    try:
        bruto = exc.read(LIMITE_LEITURA_ERRO) or b""
        falha_leitura = None
    except Exception as erro_leitura:  # noqa: BLE001 — corpo ilegível não mascara o código
        bruto, falha_leitura = b"", type(erro_leitura).__name__
    obj, sanitizado = _sanitizar_estrutura(bruto)
    mensagem = "ollama HTTP %s" % exc.code
    resumo = _resumo_diagnostico(obj)
    if resumo:
        mensagem += ": " + resumo
    if falha_leitura:
        return mensagem + " | corpo=<ilegível: %s>" % falha_leitura
    return mensagem + " | corpo=" + (_truncar(sanitizado, LIMITE_CORPO_ERRO) or "<vazio>")


def opcoes_ollama(modelo: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Options efetivas do candidato: padrão <- mapa por modelo <- `options` explícitas."""
    efetivas = dict(OLLAMA_OPCOES_PADRAO)
    efetivas.update(OLLAMA_OPCOES_POR_MODELO.get(modelo, {}))
    if options:
        efetivas.update(options)
    return efetivas


class AdaptadorOllamaVLM(Adaptador):
    """POST /api/generate no Ollama local (somente 127.0.0.1).

    Carga: descarrega o modelo (keep_alive=0, não remove o modelo do disco) e o
    carrega de novo com uma requisição sem prompt, com as MESMAS options da
    inferência (num_ctx incluso), para que a (re)configuração de contexto ocorra
    dentro de t_carga_s. Inferência: requisição com images=[b64], prompt fixo,
    stream=False, options do candidato (`opcoes_ollama`); tempo de parede.

    Uma única tentativa por amostra: erro (inclusive exceed_context_size_error)
    vira falha_execucao com o erro sanitizado. Nunca reenvia com num_ctx maior,
    nunca redimensiona/recomprime a imagem, nunca faz retry.
    """

    detecta_abstencao = True

    def __init__(self, modelo: str, url: str = OLLAMA_URL,
                 options: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        host = urllib.parse.urlparse(url).hostname
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("Ollama precisa ser local (127.0.0.1); recebido: %s" % url)
        self.modelo = modelo
        self.url = url.rstrip("/")
        self.nome = "ollama:" + modelo
        self.options = opcoes_ollama(modelo, options)
        self.ultima_resposta_meta: Dict[str, Any] = {}

    def _post(self, caminho: str, corpo: Dict[str, Any]) -> Dict[str, Any]:
        req = urllib.request.Request(
            self.url + caminho, data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_S) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(_mensagem_erro_http(exc)) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise RuntimeError("ollama timeout após %ss" % OLLAMA_TIMEOUT_S) from None
            raise RuntimeError("ollama URLError: %s"
                               % sanitizar_corpo_erro(str(exc.reason))) from None
        except (socket.timeout, TimeoutError):
            raise RuntimeError("ollama timeout após %ss" % OLLAMA_TIMEOUT_S) from None
        if isinstance(dados, dict) and dados.get("error"):
            erro = dados["error"]
            raise RuntimeError("ollama: %s" % sanitizar_corpo_erro(
                erro if isinstance(erro, str) else json.dumps(erro, ensure_ascii=False)))
        return dados

    def _carregar(self) -> None:
        self._post("/api/generate", {"model": self.modelo, "keep_alive": 0, "stream": False})
        self._post("/api/generate", {"model": self.modelo, "keep_alive": "30m", "stream": False,
                                     "options": dict(self.options)})

    def _inferir(self, imagem: str) -> str:
        with open(imagem, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        dados = self._post("/api/generate", {
            "model": self.modelo, "prompt": PROMPT_VLM, "images": [b64],
            "stream": False, "options": dict(self.options), "keep_alive": "30m",
        })
        self.ultima_resposta_meta = {
            k: dados.get(k) for k in
            ("load_duration", "prompt_eval_duration", "eval_duration", "total_duration", "done_reason")
        }
        if "response" not in dados:
            raise RuntimeError("resposta do ollama sem campo 'response'")
        return dados["response"]

    def parametros(self) -> Dict[str, Any]:
        return {"endpoint": self.url + "/api/generate", "modelo": self.modelo,
                "prompt": PROMPT_VLM, "stream": False, "options": dict(self.options),
                "options_na_carga": dict(self.options),
                "num_ctx_origem": ("candidato" if "num_ctx" in self.options
                                   else "default do runtime Ollama (não enviado)"),
                "nota_determinismo": NOTA_DETERMINISMO}


def criar_adaptador(nome: str) -> Adaptador:
    if nome == "tesseract":
        return AdaptadorTesseract()
    if nome == "easyocr":
        return AdaptadorEasyOCR()
    if nome.startswith("ollama:"):
        return AdaptadorOllamaVLM(nome[len("ollama:"):])
    raise ValueError("candidato desconhecido: %s" % nome)


# ---------------------------------------------------------------------------
# 4. Orquestração
# ---------------------------------------------------------------------------

def carregar_manifesto(caminho: str) -> List[Dict[str, Any]]:
    base = os.path.dirname(os.path.abspath(caminho))
    with open(caminho, encoding="utf-8") as fh:
        dados = json.load(fh)
    amostras = []
    vistos = set()
    for item in dados["amostras"]:
        conjunto = item["conjunto"]
        if conjunto not in ("dev", "eval"):
            raise ValueError("conjunto inválido em %s: %s" % (item["amostra"], conjunto))
        if item["amostra"] in vistos:
            raise ValueError("amostra duplicada no manifesto: %s" % item["amostra"])
        vistos.add(item["amostra"])
        imagem = os.path.normpath(os.path.join(base, item["imagem_png"]))
        referencia = os.path.normpath(os.path.join(base, item["referencia_txt"]))
        partes = os.path.relpath(imagem, base).split(os.sep)
        if any(d in partes for d in _DIRS_PROIBIDOS_COMO_ENTRADA) or imagem == referencia:
            raise ValueError("imagem de %s aponta para área proibida como entrada: %s"
                             % (item["amostra"], imagem))
        amostras.append({"amostra": item["amostra"], "conjunto": conjunto,
                         "imagem_png": imagem, "referencia_txt": referencia,
                         "rotulo": item.get("rotulo")})
    return amostras


def _ler_referencia(caminho: str) -> str:
    with open(caminho, encoding="utf-8-sig") as fh:
        return fh.read()


def montar_registro(candidato: str, amostra: Dict[str, Any], resultado: Resultado,
                    ref_bruta: str) -> Dict[str, Any]:
    """Combina saída do adaptador com o scoring. Regras por status:

    - ok: scoring completo (avaliar_amostra).
    - abstencao: cer/wer None (fora da média); produziu_texto=False e
      invencao_em_vazio=False (protocolo §6: abstenção não é invenção).
    - falha_execucao: cer/wer None; produziu_texto=False;
      invencao_em_vazio=None (não avaliável) se a ref é vazia.
    """
    texto, t_carga, t_inf, status, erro = resultado
    aval = avaliar_amostra(texto or "", ref_bruta)
    if status != STATUS_OK:
        aval["cer"] = None
        aval["wer"] = None
        aval["produziu_texto"] = False
        if status == STATUS_ABSTENCAO:
            aval["invencao_em_vazio"] = False if aval["ref_vazia"] else None
        else:
            aval["invencao_em_vazio"] = None
    elif not aval["ref_vazia"]:
        aval["invencao_em_vazio"] = None  # critério só se aplica a ref vazia
    registro = {
        "candidato": candidato,
        "amostra": amostra["amostra"],
        "conjunto": amostra["conjunto"],
        "rotulo": amostra.get("rotulo"),
        "texto_saida_original": texto,
        "status": status,
        "erro": erro,
        "t_carga_s": t_carga,
        "t_inferencia_s": t_inf,
    }
    registro.update(aval)
    if status == STATUS_ABSTENCAO:
        registro["abstencao_padrao"] = detectar_abstencao(texto)[1]
    return registro


def _nome_arquivo(candidato: str, amostra: str) -> str:
    seguro = re.sub(r"[^A-Za-z0-9._-]", "_", candidato)
    return "%s__%s.json" % (seguro, amostra)


def executar_benchmark(amostras: List[Dict[str, Any]], adaptadores: List[Adaptador],
                       dir_saida: str, sobrescrever: bool = False) -> List[Dict[str, Any]]:
    os.makedirs(dir_saida, exist_ok=True)
    if not sobrescrever:
        existentes = [
            _nome_arquivo(a.nome, s["amostra"]) for a in adaptadores for s in amostras
            if os.path.exists(os.path.join(dir_saida, _nome_arquivo(a.nome, s["amostra"])))
        ]
        if existentes:
            raise FileExistsError("resultados brutos já existem (use --sobrescrever): %s"
                                  % ", ".join(existentes))
    registros = []
    for adaptador in adaptadores:
        for amostra in amostras:
            destino = os.path.join(dir_saida, _nome_arquivo(adaptador.nome, amostra["amostra"]))
            # Inferência primeiro, apenas com a imagem; a referência só é lida depois.
            resultado = adaptador.executar(amostra["imagem_png"])
            ref_bruta = _ler_referencia(amostra["referencia_txt"])
            registro = montar_registro(adaptador.nome, amostra, resultado, ref_bruta)
            registro["registrado_em"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
            if isinstance(adaptador, AdaptadorOllamaVLM):
                registro["ollama_meta"] = adaptador.ultima_resposta_meta
            with open(destino, "w", encoding="utf-8") as fh:
                json.dump(registro, fh, ensure_ascii=False, indent=2)
            registros.append(registro)
            print("[%s] %s: %s cer=%s wer=%s" % (adaptador.nome, amostra["amostra"],
                  registro["status"], registro["cer"], registro["wer"]), flush=True)
    return registros


def _media(valores: List[float]) -> Optional[float]:
    return sum(valores) / len(valores) if valores else None


def agregar(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Agrega por candidato conforme spec §6.

    - Média CER/WER: só eval, ref não-vazia, status ok; denominador explícito
      sobre TODAS as amostras eval de ref não-vazia (falhas/abstenções ficam
      visíveis no denominador, não somem).
    - dev: listado à parte, fora da média.
    - eval com ref vazia: critério de invenção à parte.
    - Desclassificação: invenção em amostra vazia. Critério não avaliável
      (falha de execução na amostra vazia) é reportado como inconclusivo.
    - Não elege vencedor.
    """
    por_candidato: Dict[str, List[Dict[str, Any]]] = {}
    for r in registros:
        por_candidato.setdefault(r["candidato"], []).append(r)

    resumo: Dict[str, Any] = {}
    for candidato, regs in por_candidato.items():
        eval_texto = [r for r in regs if r["conjunto"] == "eval" and not r["ref_vazia"]]
        eval_vazia = [r for r in regs if r["conjunto"] == "eval" and r["ref_vazia"]]
        dev = [r for r in regs if r["conjunto"] == "dev"]
        ok = [r for r in eval_texto if r["status"] == STATUS_OK]
        n_falha = sum(r["status"] == STATUS_FALHA for r in eval_texto)
        n_abst = sum(r["status"] == STATUS_ABSTENCAO for r in eval_texto)

        denominador = "%d/%d ok" % (len(ok), len(eval_texto))
        if n_falha:
            denominador += ", %d falha_execucao" % n_falha
        if n_abst:
            denominador += ", %d abstencao" % n_abst

        invencoes = [r["amostra"] for r in eval_vazia if r["invencao_em_vazio"] is True]
        nao_avaliaveis = [r["amostra"] for r in eval_vazia if r["invencao_em_vazio"] is None]
        if invencoes:
            situacao = "desclassificado"
            motivo = "invenção de texto em amostra de referência vazia: %s" % ", ".join(invencoes)
        elif nao_avaliaveis:
            situacao = "inconclusivo"
            motivo = ("critério de invenção não avaliável (falha de execução): %s"
                      % ", ".join(nao_avaliaveis))
        elif not eval_vazia:
            situacao = "inconclusivo"
            motivo = "nenhuma amostra eval de referência vazia no manifesto"
        else:
            situacao = "nao_desclassificado"
            motivo = None

        cargas = [r["t_carga_s"] for r in regs if r["t_carga_s"] is not None]
        resumo[candidato] = {
            "eval_media_cer": _media([r["cer"] for r in ok]),
            "eval_media_wer": _media([r["wer"] for r in ok]),
            "eval_denominador": denominador,
            "eval_por_amostra": [
                {k: r[k] for k in ("amostra", "rotulo", "status", "cer", "wer", "erro")}
                for r in eval_texto
            ],
            "criterio_invencao": [
                {k: r[k] for k in ("amostra", "status", "produziu_texto", "invencao_em_vazio",
                                   "texto_saida_original", "erro")}
                for r in eval_vazia
            ],
            "dev_sanidade": [
                {k: r[k] for k in ("amostra", "status", "cer", "wer", "erro")} for r in dev
            ],
            "situacao": situacao,
            "motivo": motivo,
            "t_carga_s": cargas[0] if cargas else None,
            "t_inferencia_eval_media_s": _media(
                [r["t_inferencia_s"] for r in ok if r["t_inferencia_s"] is not None]),
            "rotulo_latencia": "hardware local; não representativo de produção",
        }
    return {"candidatos": resumo, "vencedor": None,
            "nota": "nenhum vencedor é atribuído automaticamente (spec §6)"}


def _versao_cmd(cmd: List[str]) -> Optional[str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (p.stdout or p.stderr).strip() or None
    except Exception as exc:  # noqa: BLE001
        return "indisponível: %s" % exc


def registrar_ambiente(adaptadores: List[Adaptador]) -> Dict[str, Any]:
    """Versões, parâmetros e hardware (spec §8). Não baixa nada."""
    amb: Dict[str, Any] = {
        "registrado_em": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "python": sys.version,
        "plataforma": platform.platform(),
        "cpu": _versao_cmd(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "memoria_bytes": _versao_cmd(["sysctl", "-n", "hw.memsize"]),
        "prompt_vlm": PROMPT_VLM,
        "parametros": {a.nome: a.parametros() for a in adaptadores},
        "nota_rede": "inferência offline não é verificada por este runner; "
                     "Ollama restrito a 127.0.0.1 por construção",
    }
    nomes = [a.nome for a in adaptadores]
    if "tesseract" in nomes:
        amb["tesseract_version"] = _versao_cmd(["tesseract", "--version"])
    if "easyocr" in nomes:
        try:
            from importlib.metadata import version
            amb["easyocr_version"] = version("easyocr")
        except Exception as exc:  # noqa: BLE001
            amb["easyocr_version"] = "indisponível: %s" % exc
    if any(n.startswith("ollama:") for n in nomes):
        amb["ollama_opcoes_por_candidato"] = {
            a.nome: dict(a.options) for a in adaptadores if isinstance(a, AdaptadorOllamaVLM)}
        amb["ollama_nota_determinismo"] = NOTA_DETERMINISMO
        amb["ollama_list"] = _versao_cmd(["ollama", "list"])
        amb["ollama_version"] = _versao_cmd(["ollama", "--version"])
    return amb


# ---------------------------------------------------------------------------
# 5. Dry-run: casos sintéticos embutidos (strings fictícias)
# ---------------------------------------------------------------------------

CASOS_SINTETICOS = [
    # (amostra, conjunto, referência, {candidato: (texto, status)})
    ("SINT-DEV", "dev", "Gato azul pula.",
     {"cand_a": ("Gato azul pula.", STATUS_OK), "cand_b": ("Gato azul pula.", STATUS_OK)}),
    ("SINT-01", "eval", "Óculos de sol.",
     {"cand_a": ("Óculos de sol.", STATUS_OK), "cand_b": ("Oculos de sol", STATUS_OK)}),
    ("SINT-02", "eval", "Três  maçãs\nverdes!",
     {"cand_a": ("Três maçãs verdes!", STATUS_OK), "cand_b": (None, STATUS_FALHA)}),
    ("SINT-VAZIA", "eval", "",
     {"cand_a": ("", STATUS_OK), "cand_b": ("Lorem ipsum", STATUS_OK)}),
]


def dry_run() -> Dict[str, Any]:
    registros = []
    for amostra, conjunto, ref, saidas in CASOS_SINTETICOS:
        for cand, (texto, status) in saidas.items():
            erro = "falha simulada" if status == STATUS_FALHA else None
            registros.append(montar_registro(
                cand, {"amostra": amostra, "conjunto": conjunto, "rotulo": "sintetico"},
                (texto, None, None, status, erro), ref))
    return {"registros": registros, "agregado": agregar(registros)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="roda só scoring/agregação sobre casos sintéticos; não chama motores")
    ap.add_argument("--manifesto")
    ap.add_argument("--candidatos", default=",".join(CANDIDATOS_PADRAO))
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "resultados_brutos"))
    ap.add_argument("--sobrescrever", action="store_true")
    args = ap.parse_args(argv)

    if args.dry_run:
        print(json.dumps(dry_run(), ensure_ascii=False, indent=2))
        return 0
    if not args.manifesto:
        ap.error("--manifesto é obrigatório fora do --dry-run")

    amostras = carregar_manifesto(args.manifesto)
    adaptadores = [criar_adaptador(n.strip()) for n in args.candidatos.split(",") if n.strip()]
    os.makedirs(args.saida, exist_ok=True)
    carimbo = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with open(os.path.join(args.saida, "ambiente_%s.json" % carimbo), "w", encoding="utf-8") as fh:
        json.dump(registrar_ambiente(adaptadores), fh, ensure_ascii=False, indent=2)
    registros = executar_benchmark(amostras, adaptadores, args.saida, args.sobrescrever)
    agregado = agregar(registros)
    with open(os.path.join(args.saida, "agregado_%s.json" % carimbo), "w", encoding="utf-8") as fh:
        json.dump(agregado, fh, ensure_ascii=False, indent=2)
    print(json.dumps(agregado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
