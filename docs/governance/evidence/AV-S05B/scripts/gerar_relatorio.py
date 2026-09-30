"""Gera o relatorio final a partir de saida/resultados_brutos.json,
aplicando corretamente o criterio eliminatorio de invencao de texto
(corrigido apos o desvio de protocolo registrado em
protocolo/PROTOCOLO_CONGELADO.md secao 13).

NAO repete nenhuma chamada de inferencia -- opera sobre o texto bruto ja
gravado, imutavel desde a execucao do benchmark.
"""
import json
import os
import re
import unicodedata

BASE = os.path.join(os.path.dirname(__file__), "..")
SAIDA = os.path.join(BASE, "saida")


def eh_marcacao_ilegivel(texto: str) -> bool:
    """Reconhece variacoes razoaveis do marcador ILEGIVEL: case-insensitive,
    tolera pontuacao final e espacos. Nao tolera texto adicional alem do
    marcador (isso ainda seria invencao parcial)."""
    t = unicodedata.normalize("NFC", texto).strip()
    t = re.sub(r"[.\!\?]+$", "", t)  # remove pontuacao final
    return t.strip().upper() == "ILEGIVEL"


def eh_variacao_de_abstencao(texto: str) -> bool:
    """Deteccao mais tolerante que eh_marcacao_ilegivel, usada SOMENTE para
    a analise diagnostica de 'abstencao sistematica' (nunca para o criterio
    eliminatorio, que permanece estrito). Aceita o marcador exato OU um
    texto curto que comeca com o radical 'ilegivel' seguido apenas de
    ruido de poucos caracteres (ex.: 'ilegivelive.', tipico de decodificacao
    truncada/alucinada de VLM pequeno) -- reconhecida, achado real da
    revisao independente do Antigravity CLI, 2026-09-29. Isso NAO afeta o
    criterio eliminatorio (que so aceita o marcador exato): serve apenas
    para nao esconder abstencao sistematica atras de uma variacao textual
    espuria."""
    if eh_marcacao_ilegivel(texto):
        return True
    t = unicodedata.normalize("NFC", texto).strip().upper()
    t = re.sub(r"[.\!\?]+$", "", t)
    # radical "ILEGIVEL" no inicio, com no maximo 6 caracteres de ruido
    # adicional apos o radical (ex.: "ILEGIVELIVE" tem 3 a mais -- aceito;
    # um texto de resposta real teria dezenas de caracteres)
    if t.startswith("ILEGIVEL") and len(t) - len("ILEGIVEL") <= 6:
        return True
    return False


def avaliar_criterio_ilegivel(texto: str, erro: str | None) -> dict:
    """Avalia o criterio eliminatorio de nao-invencao de texto em IMP-08.
    Distingue explicitamente falha tecnica de execucao (erro != None) de
    saida vazia/marcador legitimos, conforme protocolo secao 6: falha
    tecnica NUNCA e excluida silenciosamente nem tratada como sucesso do
    criterio eliminatorio."""
    if erro is not None:
        return {
            "inventou_texto": None,
            "motivo": f"FALHA TECNICA DE EXECUCAO, nao avaliavel para este criterio: {erro}",
            "falha_tecnica": True,
        }
    texto_norm = unicodedata.normalize("NFC", texto).strip()
    if texto_norm == "":
        return {"inventou_texto": False, "motivo": "saida vazia — comportamento correto", "falha_tecnica": False}
    if eh_marcacao_ilegivel(texto):
        return {"inventou_texto": False, "motivo": "marcacao explicita de ilegibilidade — comportamento correto", "falha_tecnica": False}
    return {"inventou_texto": True, "motivo": f"produziu texto nao-vazio e nao-marcador sobre amostra vazia/ilegivel: {texto_norm!r}", "falha_tecnica": False}


def main():
    with open(os.path.join(SAIDA, "resultados_brutos.json")) as f:
        dados = json.load(f)

    relatorio = {"protocolo_congelado_sha256": dados["protocolo_congelado_sha256"], "candidatos": {}}

    for cand, fases in dados["fases"].items():
        info = {"eliminatorio_100_local": True, "eliminatorio_zero_invencao": None, "eval": []}

        # criterio eliminatorio 1: 100% local -- todos os 3 candidatos
        # testados (tesseract, easyocr, moondream:v2 via ollama local) sao
        # locais por design; nenhuma chamada de rede foi feita durante a
        # fase de inferencia (apenas na preparacao, registrada a parte)
        info["eliminatorio_100_local"] = True

        # criterio eliminatorio 2: reavaliado corretamente sobre IMP-08 (eval)
        for it in fases["eval"]:
            if "IMP-08" in it["amostra"]:
                aval = avaliar_criterio_ilegivel(it["texto"], it.get("erro"))
                # falha tecnica: criterio eliminatorio fica indeterminado,
                # nao aprovado nem reprovado -- candidato nao pode ser
                # declarado elegivel sem uma medicao valida deste criterio
                info["eliminatorio_zero_invencao"] = (
                    (not aval["inventou_texto"]) if not aval["falha_tecnica"] else None
                )
                info["detalhe_IMP-08_eval"] = {
                    "texto_bruto": it["texto"],
                    "erro_execucao": it.get("erro"),
                    "avaliacao": aval,
                }

        # falhas tecnicas em qualquer amostra da fase eval (nao apenas
        # IMP-08) sao contadas e reportadas, nunca excluidas silenciosamente
        falhas_eval = [it for it in fases["eval"] if it.get("erro") is not None]
        info["amostras_com_falha_tecnica_eval"] = [
            {"amostra": it["amostra"], "erro": it["erro"]} for it in falhas_eval
        ]

        if info["eliminatorio_zero_invencao"] is None:
            elegivel = None  # indeterminado -- nao pode ser declarado elegivel nem desclassificado
        else:
            elegivel = info["eliminatorio_100_local"] and info["eliminatorio_zero_invencao"] and len(falhas_eval) == 0
        info["elegivel"] = elegivel

        # observacao critica: abstencao sistematica (responde "ilegivel"
        # para TODAS as amostras SEM FALHA TECNICA, inclusive as legiveis)
        # indica falha de reconhecimento, nao sucesso do criterio
        # eliminatorio -- sinalizada explicitamente, nao escondida atras
        # do rotulo "elegivel". Amostras com falha tecnica sao excluidas
        # desta analise (nao podemos saber se o candidato teria abstido
        # ou reconhecido, dado que a chamada nem completou)
        eval_sem_falha = [it for it in fases["eval"] if it.get("erro") is None]
        dev_sem_falha = [it for it in fases["dev"] if it.get("erro") is None]
        if eval_sem_falha and dev_sem_falha:
            todas_abstiveram = all(
                eh_variacao_de_abstencao(it["texto"]) for it in eval_sem_falha
            ) and all(
                eh_variacao_de_abstencao(it["texto"]) for it in dev_sem_falha
            )
        else:
            todas_abstiveram = None  # indeterminado -- sem amostras validas para avaliar
        info["abstencao_sistematica_todas_amostras"] = todas_abstiveram
        if todas_abstiveram:
            info["observacao_critica"] = (
                "Candidato respondeu o marcador ILEGIVEL ou uma variacao curta "
                "desse marcador (ex.: 'ilegivelive.') para TODAS as amostras "
                "testadas, incluindo IMP-01 (nitida, dev), que e a amostra "
                "mais facil do conjunto. Isso indica falha sistematica de "
                "extracao de texto nesta configuracao (prompt/modelo), NAO "
                "sucesso robusto do criterio eliminatorio de nao-invencao. "
                "CER/WER de ~100% refletem essa abstencao total, nao um erro "
                "de reconhecimento parcial. Elegibilidade tecnica pelo "
                "criterio eliminatorio nao implica candidato funcionalmente "
                "util nesta configuracao. Achado inicialmente omitido pela "
                "deteccao estrita demais; corrigido apos revisao independente "
                "do Antigravity CLI."
            )

        # metricas comparativas (apenas para elegiveis, mas reportadas para todos)
        # amostras com falha tecnica sao EXCLUIDAS do CER/WER agregado (uma
        # falha de rede/execucao nao e um erro de reconhecimento e nao deve
        # inflar CER/WER como se o candidato tivesse "errado tudo")
        cers, wers, tempos_inf = [], [], []
        for it in fases["eval"]:
            if "IMP-08" in it["amostra"]:
                continue  # excluida do CER/WER agregado (referencia vazia)
            tem_falha = it.get("erro") is not None
            info["eval"].append({
                "amostra": it["amostra"],
                "cer": it["cer"] if not tem_falha else None,
                "wer": it["wer"] if not tem_falha else None,
                "tempo_inferencia_s": it["tempo_inferencia_s"],
                "erro": it["erro"],
                "excluida_do_agregado_por_falha_tecnica": tem_falha,
            })
            if tem_falha:
                continue
            if it["cer"] is not None:
                cers.append(it["cer"])
            if it["wer"] is not None:
                wers.append(it["wer"])
            if it["tempo_inferencia_s"] is not None:
                tempos_inf.append(it["tempo_inferencia_s"])

        info["cer_medio_agregado"] = round(sum(cers) / len(cers), 4) if cers else None
        info["wer_medio_agregado"] = round(sum(wers) / len(wers), 4) if wers else None
        info["tempo_inferencia_medio_s"] = round(sum(tempos_inf) / len(tempos_inf), 4) if tempos_inf else None

        # tempo de carregamento (fase dev, primeira amostra que reportou)
        for it in fases["dev"]:
            if it.get("tempo_carregamento_s") is not None:
                info["tempo_carregamento_s"] = it["tempo_carregamento_s"]
                break
        else:
            info["tempo_carregamento_s"] = None

        relatorio["candidatos"][cand] = info

    out_path = os.path.join(SAIDA, "relatorio_final.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    print("\nRelatorio salvo em", out_path)


if __name__ == "__main__":
    main()
