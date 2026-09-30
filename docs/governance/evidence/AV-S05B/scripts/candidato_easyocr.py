"""Executor do candidato EasyOCR sobre uma imagem.
Separa tempo de carregamento (inicializacao do Reader/modelo) de tempo
de inferencia (processamento da imagem), conforme protocolo secao 7."""
import time

_READER_CACHE = {}


def _get_reader(lang_list):
    key = tuple(lang_list)
    if key not in _READER_CACHE:
        import easyocr

        t0 = time.perf_counter()
        _READER_CACHE[key] = easyocr.Reader(lang_list, gpu=False, verbose=False)
        t1 = time.perf_counter()
        _READER_CACHE["_ultimo_tempo_carregamento"] = round(t1 - t0, 4)
    return _READER_CACHE[key]


def rodar_easyocr(caminho_imagem: str, lang_list=("pt",)) -> dict:
    tempo_carregamento = None
    try:
        reader = _get_reader(lang_list)
        tempo_carregamento = _READER_CACHE.pop("_ultimo_tempo_carregamento", None)
        t0 = time.perf_counter()
        resultados = reader.readtext(caminho_imagem, detail=0, paragraph=True)
        texto = " ".join(resultados).strip()
        erro = None
        t1 = time.perf_counter()
        tempo_inferencia = round(t1 - t0, 4)
    except Exception as e:
        texto = ""
        erro = str(e)
        tempo_inferencia = None
    return {
        "candidato": "easyocr",
        "texto": texto,
        "erro": erro,
        "tempo_carregamento_s": tempo_carregamento,
        "tempo_inferencia_s": tempo_inferencia,
    }


if __name__ == "__main__":
    import sys
    print(rodar_easyocr(sys.argv[1]))
