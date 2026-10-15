#!/usr/bin/env python3
"""Testes MOCKADOS das correções do runner v3 (SPEC_v3.md, C1-C5).

Rodar: `python3 -m pytest test_runner_v3_mock.py -v`.
Nenhum teste acessa rede ou Ollama real: `urllib.request.urlopen` é substituído
por um endpoint falso. Nenhuma imagem/foto é lida: os "PNGs" são bytes
sintéticos gravados em diretório temporário.
"""

from __future__ import annotations

import ast
import base64
import inspect
import io
import json
import os
import socket
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bench_runner_v3 as br  # noqa: E402

BYTES_SINTETICOS = b"nao-e-imagem-sintetico"
CORPO_CONTEXTO = {
    "error": {
        "code": 400,
        "message": "the request exceeds the available context size, try increasing it",
        "type": "exceed_context_size_error",
        "n_prompt_tokens": 4131,
        "n_ctx": 4096,
    }
}
B64_FALSO = base64.b64encode(bytes(range(256)) * 4).decode("ascii")  # 1368 chars


# --- Endpoint Ollama falso ---------------------------------------------------

class _Resposta:
    def __init__(self, dados):
        self._bruto = json.dumps(dados).encode("utf-8")

    def read(self, *a):
        return self._bruto

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(codigo, corpo):
    bruto = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode("utf-8")
    return urllib.error.HTTPError("http://127.0.0.1:11434/api/generate", codigo, "erro",
                                  {}, io.BytesIO(bruto))


class EndpointFalso:
    """Registra cada requisição; responde carga com 200 e inferência por roteiro."""

    def __init__(self, roteiro_inferencia, falha_carga=None):
        self.roteiro = list(roteiro_inferencia)
        self.falha_carga = falha_carga
        self.requisicoes = []

    def __call__(self, req, timeout=None):
        corpo = json.loads(req.data.decode("utf-8"))
        self.requisicoes.append(corpo)
        if "prompt" not in corpo:  # requisição de carga/descarga
            if self.falha_carga is not None:
                raise self.falha_carga
            return _Resposta({"model": corpo["model"], "done": True, "response": ""})
        item = self.roteiro.pop(0)
        if isinstance(item, BaseException):
            raise item
        return _Resposta(item)

    @property
    def inferencias(self):
        return [r for r in self.requisicoes if "prompt" in r]

    @property
    def cargas(self):
        return [r for r in self.requisicoes if "prompt" not in r and r.get("keep_alive") != 0]


@pytest.fixture
def imagem(tmp_path):
    caminho = tmp_path / "trabalho_png" / "S-01.png"
    caminho.parent.mkdir()
    caminho.write_bytes(BYTES_SINTETICOS)
    return str(caminho)


def _instalar(monkeypatch, endpoint):
    monkeypatch.setattr(br.urllib.request, "urlopen", endpoint)
    return endpoint


OK_200 = {"response": "Mesa de pau.", "done": True, "done_reason": "stop",
          "load_duration": 1, "prompt_eval_duration": 2, "eval_duration": 3,
          "total_duration": 6}


# --- C1: sanitizador ---------------------------------------------------------

def test_sanitizador_preserva_campos_de_diagnostico():
    s = br.sanitizar_corpo_erro(json.dumps(CORPO_CONTEXTO))
    obj = json.loads(s)
    assert obj == CORPO_CONTEXTO


def test_sanitizador_mascara_base64_e_images():
    corpo = {"error": "falhou", "images": [B64_FALSO],
             "detalhe": "payload " + B64_FALSO + " fim",
             "uri": "data:image/png;base64," + B64_FALSO[:40]}
    s = br.sanitizar_corpo_erro(json.dumps(corpo))
    assert B64_FALSO[:40] not in s and B64_FALSO[100:140] not in s
    obj = json.loads(s)
    assert obj["images"] == "[IMAGENS_OMITIDAS]"
    assert obj["detalhe"] == "payload [BASE64_OMITIDO] fim"
    assert obj["error"] == "falhou"


def test_sanitizador_mascara_images_em_corpo_nao_json_truncado():
    s = br.sanitizar_corpo_erro('{"model":"m","images":["%s' % B64_FALSO[:500])
    assert B64_FALSO[:30] not in s
    assert "[IMAGENS_OMITIDAS]" in s


@pytest.mark.parametrize("trecho,segredo", [
    ("Authorization: Bearer sk-SEGREDO123", "SEGREDO123"),
    ("authorization=Basic dXNlcjpzZWdyZWRv", "dXNlcjpzZWdyZWRv"),
    ("X-Api-Key: CHAVE-SECRETA-9", "CHAVE-SECRETA-9"),
    ("api_key=CHAVE-SECRETA-9", "CHAVE-SECRETA-9"),
    ("token: tok_SEGREDO", "tok_SEGREDO"),
    ("access_token=tok_SEGREDO", "tok_SEGREDO"),
    ("Cookie: sessao=SEGREDO; outro=SEGREDO2", "SEGREDO"),
])
def test_sanitizador_mascara_credenciais_em_texto(trecho, segredo):
    s = br.sanitizar_corpo_erro("erro upstream; " + trecho + "\nfim")
    assert segredo not in s
    assert "[CREDENCIAL_OMITIDA]" in s


def test_sanitizador_mascara_credenciais_em_json():
    corpo = {"error": "x", "headers": {"Authorization": "Bearer SEGREDO",
                                       "api-key": "SEGREDO", "Cookie": "a=SEGREDO",
                                       "token": "SEGREDO"}}
    s = br.sanitizar_corpo_erro(json.dumps(corpo))
    assert "SEGREDO" not in s
    obj = json.loads(s)
    assert set(obj["headers"].values()) == {"[CREDENCIAL_OMITIDA]"}


def test_sanitizador_mascara_caminhos_e_nomes_de_imagem():
    corpo = ("open /Users/fulano/Projeto Estágio/coleta/trabalho_png/MAN-03.png: denied; "
             "C:\\dados\\coleta\\x.jpg; ~/coleta/fotos/y; arquivo MAN-07.heic")
    s = br.sanitizar_corpo_erro(corpo)
    for vazado in ("fulano", "Estágio", "coleta", "MAN-03", "MAN-07", "dados", "fotos"):
        assert vazado not in s, (vazado, s)
    assert "[CAMINHO_OMITIDO]" in s and "[ARQUIVO_OMITIDO]" in s


def test_sanitizador_nao_mascara_url_local_nem_n_prompt_tokens():
    s = br.sanitizar_corpo_erro("POST http://127.0.0.1:11434/api/generate n_prompt_tokens=4131")
    assert "127.0.0.1:11434/api/generate" in s
    assert "n_prompt_tokens=4131" in s


# Regressão (achado A): variantes com '_' ou prefixo colado escapavam do '\b'.
@pytest.mark.parametrize("trecho,chave,segredo", [
    ("proxy_authorization: secret123", "proxy_authorization", "secret123"),
    ("x_api_key=supersecret", "x_api_key", "supersecret"),
    ("Proxy_Authorization: Bearer abc", "Proxy_Authorization", "abc"),
    ("proxyauthorization=segredoXYZ", "proxyauthorization", "segredoXYZ"),
    ("xapikey: segredoXYZ", "xapikey", "segredoXYZ"),
    ("set_cookie: sessao=segredoXYZ", "set_cookie", "segredoXYZ"),
    ("upstream_api_key='segredoXYZ'", "api_key", "segredoXYZ"),
    ("Proxy-Authorization: Basic segredoXYZ", "Proxy-Authorization", "segredoXYZ"),
])
def test_sanitizador_mascara_credenciais_com_underscore_ou_colado(trecho, chave, segredo):
    s = br.sanitizar_corpo_erro("erro upstream; " + trecho + "\nfim")
    assert segredo not in s, s
    assert chave in s and "[CREDENCIAL_OMITIDA]" in s, s
    assert s.endswith("\nfim")


def test_sanitizador_omite_credencial_sem_separador():
    s = br.sanitizar_corpo_erro("rejeitado: x_api_key sk-segredo123 invalida")
    assert "segredo123" not in s
    assert "x_api_key [TRECHO_OMITIDO_NAO_SANITIZAVEL] invalida" in s
    # palavra comum após o nome não é tratada como segredo
    assert br.sanitizar_corpo_erro("authorization required") == "authorization required"


# Regressão (achado B): caminho relativo sem extensão de imagem passava sem máscara.
@pytest.mark.parametrize("caminho", [
    "coleta/referencias/ref.txt", "amostras/MAN-04/nota.txt",
    "amostras/MAN-04/anotacao.txt", "coleta\\referencias\\ref.txt",
    "coleta/fotos", "referencias/ref.txt",
])
def test_sanitizador_mascara_caminho_relativo(caminho):
    s = br.sanitizar_corpo_erro("open " + caminho + ": no such file")
    assert s == "open [CAMINHO_OMITIDO]: no such file", s


def test_sanitizador_caminho_relativo_preserva_diagnostico():
    texto = ("exceed_context_size_error n_prompt_tokens=4131 n_ctx=4096 razao 4131/4096 "
             "Content-Type: application/json POST http://127.0.0.1:11434/api/generate")
    assert br.sanitizar_corpo_erro(texto) == texto
    corpo = {"error": dict(CORPO_CONTEXTO["error"],
                           message="erro ao abrir amostras/MAN-04/nota.txt")}
    obj = json.loads(br.sanitizar_corpo_erro(json.dumps(corpo)))
    erro = obj["error"]
    assert erro["message"] == "erro ao abrir [CAMINHO_OMITIDO]"
    assert {k: erro[k] for k in ("code", "type", "n_prompt_tokens", "n_ctx")} == {
        "code": 400, "type": "exceed_context_size_error",
        "n_prompt_tokens": 4131, "n_ctx": 4096}


# Regressão (revisão Antigravity): com any(), pasta com UM segmento numérico
# (coleta/01) escapava como "razão numérica" e vazava estrutura da coleta.
@pytest.mark.parametrize("caminho", ["coleta/01", "amostras/42", "lote/2024"])
def test_sanitizador_mascara_caminho_com_um_segmento_numerico(caminho):
    s = br.sanitizar_corpo_erro("open " + caminho + ": no such file")
    assert s == "open [CAMINHO_OMITIDO]: no such file", s


@pytest.mark.parametrize("trecho", ["4131/4096", "application/json"])
def test_sanitizador_preserva_razao_numerica_e_mime(trecho):
    texto = "diagnostico " + trecho + " fim"
    assert br.sanitizar_corpo_erro(texto) == texto


def test_sanitizador_mascara_transcricao_ecoada():
    s = br.sanitizar_corpo_erro(json.dumps({"error": "x", "response": "Texto manuscrito"}))
    assert "manuscrito" not in s


def test_sanitizador_trunca_a_2048():
    s = br.sanitizar_corpo_erro("erro " * 5000)
    assert len(s) <= 2048 and br.LIMITE_CORPO_ERRO == 2048
    assert s.endswith("[truncado]")
    assert br.sanitizar_corpo_erro(b"curto") == "curto"


# --- C1: _post com HTTPError / URLError / timeout ---------------------------

def test_http_400_contexto_gera_erro_diagnostico(monkeypatch):
    _instalar(monkeypatch, EndpointFalso([_http_error(400, CORPO_CONTEXTO)]))
    a = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    with pytest.raises(RuntimeError) as info:
        a._post("/api/generate", {"model": "m", "prompt": "p"})
    msg = str(info.value)
    assert msg.startswith(
        "ollama HTTP 400: exceed_context_size_error n_prompt_tokens=4131 n_ctx=4096")
    assert "the request exceeds the available context size" in msg


def test_http_erro_com_campos_sensiveis_sai_sanitizado(monkeypatch, imagem):
    corpo = {"error": {"type": "bad_request", "message": "falha em " + imagem},
             "images": [B64_FALSO], "authorization": "Bearer SEGREDO"}
    _instalar(monkeypatch, EndpointFalso([_http_error(500, corpo)]))
    a = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    texto, _, _, status, erro = a.executar(imagem)
    assert status == br.STATUS_FALHA and texto is None
    assert "ollama HTTP 500: bad_request" in erro
    for vazado in (B64_FALSO[:40], "SEGREDO", imagem, "S-01.png"):
        assert vazado not in erro


def test_http_erro_com_corpo_gigante_eh_limitado(monkeypatch, imagem):
    corpo = b'{"error":"' + b"x" * 500000 + b'"}'
    _instalar(monkeypatch, EndpointFalso([_http_error(400, corpo)]))
    a = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    erro = a.executar(imagem)[4]
    assert len(erro) < 2048 + 200


def test_url_error_sanitizado(monkeypatch, imagem):
    falha = urllib.error.URLError("conexão recusada lendo /Users/fulano/coleta/x/MAN-01.png")
    _instalar(monkeypatch, EndpointFalso([falha]))
    texto, _, t_inf, status, erro = br.AdaptadorOllamaVLM("qwen2.5vl:3b").executar(imagem)
    assert status == br.STATUS_FALHA and texto is None and t_inf is not None
    assert "ollama URLError" in erro and "fulano" not in erro and "MAN-01" not in erro


@pytest.mark.parametrize("falha", [socket.timeout("timed out"),
                                   urllib.error.URLError(socket.timeout("timed out")),
                                   TimeoutError("timed out")])
def test_timeout_vira_falha_sanitizada(monkeypatch, imagem, falha):
    _instalar(monkeypatch, EndpointFalso([falha]))
    texto, _, _, status, erro = br.AdaptadorOllamaVLM("qwen2.5vl:3b").executar(imagem)
    assert status == br.STATUS_FALHA and texto is None
    assert "ollama timeout" in erro


def test_falha_na_carga_tambem_sanitizada(monkeypatch, imagem):
    endpoint = _instalar(monkeypatch, EndpointFalso(
        [], falha_carga=_http_error(400, {"error": "modelo x", "images": [B64_FALSO]})))
    texto, t_carga, _, status, erro = br.AdaptadorOllamaVLM("qwen2.5vl:3b").executar(imagem)
    assert status == br.STATUS_FALHA and texto is None and t_carga is not None
    assert erro.startswith("carga: RuntimeError: ollama HTTP 400")
    assert B64_FALSO[:40] not in erro
    assert endpoint.inferencias == []


def test_200_ok_com_meta(monkeypatch, imagem):
    _instalar(monkeypatch, EndpointFalso([OK_200]))
    a = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    texto, t_carga, t_inf, status, erro = a.executar(imagem)
    assert (texto, status, erro) == ("Mesa de pau.", br.STATUS_OK, None)
    assert t_carga is not None and t_inf is not None
    assert a.ultima_resposta_meta["done_reason"] == "stop"


def test_200_com_campo_error_sanitizado(monkeypatch, imagem):
    _instalar(monkeypatch, EndpointFalso([{"error": "falhou com Bearer SEGREDO"}]))
    erro = br.AdaptadorOllamaVLM("qwen2.5vl:3b").executar(imagem)[4]
    assert "ollama:" in erro and "SEGREDO" not in erro


# --- C2: mesmas options na carga e na inferência -----------------------------

@pytest.mark.parametrize("modelo", ["qwen2.5vl:3b", "moondream:v2"])
def test_carga_envia_mesmas_options_que_inferencia(monkeypatch, imagem, modelo):
    endpoint = _instalar(monkeypatch, EndpointFalso([OK_200, OK_200]))
    a = br.AdaptadorOllamaVLM(modelo)
    r1 = a.executar(imagem)
    r2 = a.executar(imagem)
    assert len(endpoint.cargas) == 1
    opcoes_carga = endpoint.cargas[0]["options"]
    assert all(r["options"] == opcoes_carga for r in endpoint.inferencias)
    assert opcoes_carga == a.options
    # descarga (keep_alive=0) precede a carga; tempos continuam campos distintos
    assert endpoint.requisicoes[0]["keep_alive"] == 0
    assert r1[1] is not None and r1[2] is not None
    assert r2[1] is None and r2[2] is not None


# --- C3: options por candidato -----------------------------------------------

def test_options_por_candidato():
    qwen = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    moon = br.AdaptadorOllamaVLM("moondream:v2")
    assert qwen.options["num_ctx"] == 8192
    assert "num_ctx" not in moon.options
    assert not hasattr(br, "OLLAMA_OPCOES")
    assert qwen.parametros()["options"] == qwen.options
    assert moon.parametros()["options"] == moon.options
    assert moon.parametros()["num_ctx_origem"].startswith("default do runtime")
    assert qwen.parametros()["num_ctx_origem"] == "candidato"


def test_options_explicitas_no_construtor_e_isolamento():
    a = br.AdaptadorOllamaVLM("moondream:v2", options={"num_ctx": 2048})
    assert a.options == {"temperature": 0, "seed": br.OLLAMA_SEED, "num_ctx": 2048}
    a.options["num_ctx"] = 1  # mutação local não vaza para o mapa/default
    assert "num_ctx" not in br.AdaptadorOllamaVLM("moondream:v2").options
    assert br.AdaptadorOllamaVLM("qwen2.5vl:3b").options["num_ctx"] == 8192
    assert "num_ctx" not in br.OLLAMA_OPCOES_PADRAO


@pytest.mark.parametrize("modelo,num_ctx", [("qwen2.5vl:3b", 8192), ("moondream:v2", None)])
def test_moondream_nao_herda_num_ctx_na_requisicao(monkeypatch, imagem, modelo, num_ctx):
    endpoint = _instalar(monkeypatch, EndpointFalso([OK_200]))
    br.AdaptadorOllamaVLM(modelo).executar(imagem)
    for r in endpoint.cargas + endpoint.inferencias:
        assert r["options"].get("num_ctx") == num_ctx


# --- C4: seed e parâmetros registrados ---------------------------------------

def test_seed_fixa_e_parametros_registrados(monkeypatch):
    monkeypatch.setattr(br, "_versao_cmd", lambda cmd: "mock")
    adaptadores = [br.AdaptadorOllamaVLM("qwen2.5vl:3b"), br.AdaptadorOllamaVLM("moondream:v2")]
    amb = br.registrar_ambiente(adaptadores)
    for a in adaptadores:
        p = amb["parametros"][a.nome]
        assert p["options"]["seed"] == br.OLLAMA_SEED
        assert p["options"]["temperature"] == 0
        assert p["options_na_carga"] == p["options"]
        assert amb["ollama_opcoes_por_candidato"][a.nome] == a.options
    assert amb["ollama_opcoes_por_candidato"]["ollama:qwen2.5vl:3b"]["num_ctx"] == 8192
    assert "num_ctx" not in amb["ollama_opcoes_por_candidato"]["ollama:moondream:v2"]
    nota = amb["ollama_nota_determinismo"]
    assert "não garantem determinismo absoluto" in nota


# --- C5: falha de contexto permanece falha_execucao, sem recuperação ---------

def test_contexto_excedido_e_falha_sem_recuperacao_silenciosa(monkeypatch, tmp_path):
    (tmp_path / "trabalho_png").mkdir()
    (tmp_path / "referencias").mkdir()
    casos = [("S-01", "Mesa de pau."), ("S-02", "Copo cheio.")]
    for nome, ref in casos:
        (tmp_path / "trabalho_png" / (nome + ".png")).write_bytes(BYTES_SINTETICOS + nome.encode())
        (tmp_path / "referencias" / (nome + "_referencia.txt")).write_text(ref, encoding="utf-8")
    manifesto = tmp_path / "manifesto.json"
    manifesto.write_text(json.dumps({"amostras": [
        {"amostra": n, "conjunto": "eval", "imagem_png": "trabalho_png/%s.png" % n,
         "referencia_txt": "referencias/%s_referencia.txt" % n} for n, _ in casos]}))
    amostras = br.carregar_manifesto(str(manifesto))

    # S-01 estoura o contexto; S-02 responde 200. Roteiro com UM item por amostra:
    # qualquer reenvio esgotaria o roteiro (IndexError) e seria detectado abaixo.
    endpoint = _instalar(monkeypatch, EndpointFalso(
        [_http_error(400, CORPO_CONTEXTO), dict(OK_200, response="Copo cheio.")]))
    adaptador = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    regs = br.executar_benchmark(amostras, [adaptador], str(tmp_path / "saida"))

    falha = next(r for r in regs if r["amostra"] == "S-01")
    assert falha["status"] == br.STATUS_FALHA
    assert falha["texto_saida_original"] is None
    assert falha["cer"] is None and falha["wer"] is None
    assert falha["t_inferencia_s"] is not None  # tempo de parede da tentativa
    assert "exceed_context_size_error n_prompt_tokens=4131 n_ctx=4096" in falha["erro"]
    assert "IndexError" not in falha["erro"]

    ag = br.agregar(regs)["candidatos"]["ollama:qwen2.5vl:3b"]
    assert ag["eval_denominador"] == "1/2 ok, 1 falha_execucao"  # amostra no denominador
    assert ag["eval_media_cer"] == 0

    # Exatamente uma tentativa de inferência por amostra; nenhum reenvio.
    assert len(endpoint.inferencias) == 2
    assert len(endpoint.cargas) == 1
    # Nenhum aumento de num_ctx: todas as requisições usam o num_ctx declarado.
    assert {r["options"]["num_ctx"] for r in endpoint.cargas + endpoint.inferencias} == {8192}
    # Nenhum resize/recompressão: a imagem enviada é o base64 exato dos bytes originais.
    for req, (nome, _) in zip(endpoint.inferencias, casos):
        assert req["images"] == [base64.b64encode(BYTES_SINTETICOS + nome.encode()).decode()]
        assert req["prompt"] == br.PROMPT_VLM


def test_contexto_excedido_repetido_nao_escala_num_ctx(monkeypatch, imagem):
    endpoint = _instalar(monkeypatch, EndpointFalso([_http_error(400, CORPO_CONTEXTO) for _ in range(3)]))
    a = br.AdaptadorOllamaVLM("qwen2.5vl:3b")
    for _ in range(3):
        texto, _, _, status, erro = a.executar(imagem)
        assert status == br.STATUS_FALHA and texto is None and "exceed_context_size" in erro
    assert len(endpoint.inferencias) == 3
    assert [r["options"] for r in endpoint.inferencias] == [a.options] * 3
    assert a.options["num_ctx"] == 8192


def test_codigo_ollama_sem_caminho_de_recuperacao():
    """Teste negativo estático: uma única chamada de rede, sem manipulação de imagem."""
    fonte_modulo = inspect.getsource(br)
    # código sem a docstring (que descreve, em prosa, o que é proibido)
    classe = ast.parse(inspect.getsource(br.AdaptadorOllamaVLM)).body[0]
    classe.body = classe.body[1:]
    fonte = ast.unparse(classe)
    assert fonte.count("urlopen(") == 1
    for proibido in ("PIL", "Image.open", "resize", "thumbnail", "cv2", "retry",
                     "num_ctx'] *", "num_ctx'] +", "for tentativa", "while "):
        assert proibido not in fonte, proibido
    for proibido in ("import PIL", "from PIL", "import cv2"):
        assert proibido not in fonte_modulo, proibido
