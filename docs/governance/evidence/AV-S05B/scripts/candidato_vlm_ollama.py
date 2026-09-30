"""Executor de candidatos VLM locais via Ollama (moondream:v2, qwen2.5vl:3b).
100% local (chamada ao daemon Ollama local, nao servico externo).
Separa tempo de carregamento (primeira chamada, carrega modelo em memoria)
de tempo de inferencia (chamadas subsequentes com modelo ja carregado),
conforme protocolo secao 7.

PROMPT CONGELADO (nao alterar apos inicio da avaliacao final):
"""
import base64
import time
import json
import urllib.request

PROMPT_CONGELADO = (
    "Transcreva EXATAMENTE o texto visivel nesta imagem, em portugues, "
    "sem adicionar nem inventar nenhuma palavra. Se a imagem nao contiver "
    "nenhum texto legivel, responda apenas com a palavra: ILEGIVEL"
)

_MODELOS_JA_CARREGADOS = set()


def _chamar_ollama(modelo: str, imagem_b64: str, prompt: str, timeout=120) -> dict:
    payload = {
        "model": modelo,
        "prompt": prompt,
        "images": [imagem_b64],
        "stream": False,
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def rodar_vlm_ollama(caminho_imagem: str, modelo: str) -> dict:
    with open(caminho_imagem, "rb") as f:
        imagem_b64 = base64.b64encode(f.read()).decode("ascii")

    tempo_carregamento = None
    if modelo not in _MODELOS_JA_CARREGADOS:
        # primeira chamada: carrega o modelo em memoria, medido a parte
        t0 = time.perf_counter()
        try:
            _chamar_ollama(modelo, imagem_b64, "diga apenas: ok")
        except Exception:
            pass
        t1 = time.perf_counter()
        tempo_carregamento = round(t1 - t0, 4)
        _MODELOS_JA_CARREGADOS.add(modelo)

    t0 = time.perf_counter()
    try:
        resposta = _chamar_ollama(modelo, imagem_b64, PROMPT_CONGELADO)
        texto = resposta.get("response", "").strip()
        erro = None
    except Exception as e:
        texto = ""
        erro = str(e)
    t1 = time.perf_counter()
    return {
        "candidato": modelo,
        "texto": texto,
        "erro": erro,
        "tempo_carregamento_s": tempo_carregamento,
        "tempo_inferencia_s": round(t1 - t0, 4),
        "prompt": PROMPT_CONGELADO,
    }


if __name__ == "__main__":
    import sys
    print(rodar_vlm_ollama(sys.argv[1], sys.argv[2]))
