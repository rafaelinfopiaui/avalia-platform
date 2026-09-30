"""Orquestrador do benchmark AV-S05B, conforme protocolo congelado.
Roda a fase dev (verificacao funcional, sem medir qualidade) e depois a
fase eval (avaliacao final, congelada), para cada candidato configurado.
Nao ajusta parametros apos ver resultado da fase eval (protocolo secao 4).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from metricas import cer, wer, normalizar  # noqa: E402
from candidato_tesseract import rodar_tesseract  # noqa: E402
from candidato_easyocr import rodar_easyocr  # noqa: E402
from candidato_vlm_ollama import rodar_vlm_ollama  # noqa: E402

BASE = os.path.join(os.path.dirname(__file__), "..")
AMOSTRAS_DEV = os.path.join(BASE, "amostras", "dev")
AMOSTRAS_EVAL = os.path.join(BASE, "amostras", "eval")
REFERENCIAS = os.path.join(BASE, "amostras", "referencias")
SAIDA = os.path.join(BASE, "saida")
os.makedirs(SAIDA, exist_ok=True)

CANDIDATOS = [
    {"id": "tesseract", "fn": lambda p: rodar_tesseract(p, lang="por")},
    {"id": "easyocr", "fn": lambda p: rodar_easyocr(p, lang_list=("pt",))},
    {"id": "moondream:v2", "fn": lambda p: rodar_vlm_ollama(p, "moondream:v2")},
]


def carregar_referencia(nome_imagem: str) -> str:
    base = os.path.splitext(nome_imagem)[0]
    caminho = os.path.join(REFERENCIAS, base + ".txt")
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def rodar_fase(candidato, diretorio_amostras, fase: str):
    resultados = []
    amostras = sorted(os.listdir(diretorio_amostras))
    for nome in amostras:
        caminho = os.path.join(diretorio_amostras, nome)
        ref = carregar_referencia(nome)
        print(f"  [{fase}] {candidato['id']} x {nome} ...", flush=True)
        t_ini = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            r = candidato["fn"](caminho)
        except Exception as e:
            r = {
                "candidato": candidato["id"],
                "texto": "",
                "erro": f"excecao nao tratada: {e}",
                "tempo_carregamento_s": None,
                "tempo_inferencia_s": None,
            }
        r["amostra"] = nome
        r["fase"] = fase
        r["timestamp_inicio"] = t_ini
        r["referencia"] = ref

        # metricas (apenas informativas na fase dev; nao usadas para
        # ajustar parametros, conforme protocolo)
        if ref.strip() == "":
            r["cer"] = None
            r["wer"] = None
            r["inventou_texto_em_amostra_vazia"] = normalizar(r["texto"]) != "" and normalizar(r["texto"]).upper() != "ILEGIVEL"
        else:
            r["cer"] = cer(ref, r["texto"])
            r["wer"] = wer(ref, r["texto"])
            r["inventou_texto_em_amostra_vazia"] = None
        resultados.append(r)
    return resultados


def main():
    protocolo_hash_path = os.path.join(BASE, "protocolo", "PROTOCOLO_CONGELADO_ORIGINAL.sha256")
    with open(protocolo_hash_path) as f:
        protocolo_hash = f.read().strip()

    relatorio = {
        "protocolo_congelado_sha256": protocolo_hash,
        "gerado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fases": {},
    }

    for candidato in CANDIDATOS:
        print(f"=== Candidato: {candidato['id']} ===")
        print(" Fase DEV (verificacao funcional, nao usada para medir qualidade)")
        dev = rodar_fase(candidato, AMOSTRAS_DEV, "dev")
        print(" Fase EVAL (avaliacao final, congelada)")
        evl = rodar_fase(candidato, AMOSTRAS_EVAL, "eval")
        relatorio["fases"].setdefault(candidato["id"], {})["dev"] = dev
        relatorio["fases"][candidato["id"]]["eval"] = evl

        # salva incrementalmente para nao perder progresso
        out_path = os.path.join(SAIDA, "resultados_brutos.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        print(f" (salvo incrementalmente em {out_path})")

    print("Benchmark concluido. Resultado bruto em", os.path.join(SAIDA, "resultados_brutos.json"))


if __name__ == "__main__":
    main()
