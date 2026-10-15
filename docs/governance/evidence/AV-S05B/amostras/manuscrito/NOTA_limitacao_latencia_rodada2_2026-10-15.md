---
id: "nota_limitacao_latencia_rodada2"
tema: "AV-S05B manuscrito — limitação de latência da 1ª amostra da rodada 2 (qwen2.5vl:3b)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "NOTA DE LIMITAÇÃO — não corrige valores; não invalida CER/WER; brutos preservados intactos"
---

# Limitação de latência da 1ª amostra da rodada 2

Esta nota é um arquivo SEPARADO. Os JSON brutos da rodada 2, seus checksums e timestamps
NÃO são alterados por ela.

## Fato registrado (achado confirmado na revisão de precisão — Antigravity)

No runner v2, `AdaptadorOllamaVLM._carregar()` faz as requisições de carga **sem** o
dicionário `options` (portanto sem `num_ctx=8192`), enquanto `_inferir()` envia
`num_ctx=8192`. Na **primeira** inferência de cada modelo, o Ollama precisa reconfigurar o
contexto (de ~4096 para 8192), e esse custo de recarga é parcialmente contabilizado **dentro**
da janela medida como `t_inferencia_s` da primeira amostra, violando o isolamento pretendido
entre `t_carga_s` e `t_inferencia_s` (RUNNER_SPEC §7.3).

## Evidência observada nos brutos (sem alteração)

Primeira amostra processada do Qwen na rodada 2 (ordem do manifesto = MAN-01, conjunto dev):
- `t_carga_s` = 1,158 s; `t_inferencia_s` = 2,577 s; `ollama_meta.load_duration` ≈ 1,093 s.
- Amostras seguintes (MAN-02, MAN-03): `load_duration` ≈ 0,015–0,031 s, `t_inferencia_s`
  ≈ 8,7–9,1 s.

O `load_duration` elevado embutido na primeira inferência (≈1,1 s) é a assinatura da recarga
de contexto contabilizada na medição — exatamente o viés descrito. O efeito líquido no valor
final varia por amostra e não é separável com os dados já gravados.

## O que esta nota NÃO faz

- **Não corrige** `t_inferencia_s` por estimativa nem subtrai o `load_duration` — fazer isso
  seria introduzir número não medido. Os valores brutos ficam como estão.
- **Não invalida** CER/WER nem a agregação: o viés é de **latência**, não de transcrição;
  CER/WER dependem só do texto de saída vs referência, não do tempo.
- **Não altera** a classificação de status de nenhuma amostra.

## Encaminhamento

A correção estrutural (usar a mesma configuração de contexto na carga e na inferência,
separando claramente os tempos) é requisito do **runner v3** e da especificação candidata da
Amostra_2 — não se aplica retroativamente à rodada 2, que permanece válida com esta limitação
de latência explicitada.
