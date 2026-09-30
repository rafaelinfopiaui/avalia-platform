"""Executor do candidato Tesseract OCR sobre uma imagem.
Retorna dict com texto extraido e tempos de carregamento/inferencia.
Conforme protocolo: 100% local, sem chamada de rede."""
import subprocess
import time


def rodar_tesseract(caminho_imagem: str, lang: str = "por") -> dict:
    # "carregamento" para o Tesseract via CLI e o tempo de start do processo
    # + carregamento do modelo de idioma; medimos o processo completo como
    # inferencia, ja que o CLI nao separa as duas fases de forma exposta.
    t0 = time.perf_counter()
    try:
        resultado = subprocess.run(
            ["tesseract", caminho_imagem, "stdout", "-l", lang],
            capture_output=True,
            text=True,
            timeout=60,
        )
        texto = resultado.stdout.strip()
        erro = resultado.stderr.strip() if resultado.returncode != 0 else None
    except subprocess.TimeoutExpired:
        texto = ""
        erro = "timeout"
    except Exception as e:
        texto = ""
        erro = str(e)
    t1 = time.perf_counter()
    return {
        "candidato": "tesseract",
        "texto": texto,
        "erro": erro,
        "tempo_carregamento_s": None,  # nao separavel via CLI
        "tempo_inferencia_s": round(t1 - t0, 4),
    }


if __name__ == "__main__":
    import sys
    print(rodar_tesseract(sys.argv[1]))
