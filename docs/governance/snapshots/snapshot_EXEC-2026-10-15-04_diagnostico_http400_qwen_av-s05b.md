---
id: "EXEC-2026-10-15-04"
tipo: execucao
sprint: "AV-S05B — eixo manuscrito: diagnóstico dirigido do HTTP 400 do qwen2.5vl:3b e correção de transporte (benchmark Amostra_1)"
gerado_em: "2026-10-15T15:30:00-03:00"
executor: "Hermes (orquestrador) — diagnóstico, reprodução sintética, runner v2 e reexecução; nenhum agente externo recebeu imagens/saídas da coleta"
status: "CONCLUÍDA — causa comprovada; correção de transporte validada; AV-S05B permanece PARCIAL; AC-05 NÃO concluído; nenhuma solução promovida"
base: "main 970eb8c212dfa50636699cbafede7a3644ff4ddb (não tocada)"
branch: "nenhuma — rodada LOCAL em área não-versionada; evidência documental em docs/governance (untracked)"
---

# Snapshot EXEC-2026-10-15-04 — AV-S05B manuscrito: diagnóstico do HTTP 400 do qwen2.5vl:3b

> **RECONCILIAÇÃO DATADA (2026-10-15T16:10-03:00) — precisão metodológica.** Correção
> sem reescrever o texto original abaixo: (1) `num_ctx` 4096→8192 é **alteração da
> configuração de contexto de inferência** (motivada pelos erros de limite de contexto),
> não "somente transporte/serialização" — a autorização de Rafael é preservada, mas não
> muda a natureza técnica do parâmetro; (2) a rodada 2 é **resultado exploratório sobre
> as mesmas amostras após ajuste informado pelas falhas do eval**, não avaliação
> independente nem reprodução do protocolo sem alteração; (3) denominadores coincidentes
> (7 legíveis) permitem **comparação descritiva**, explicitando a configuração diferente
> do Qwen e o ajuste posterior; **CER 0,077 não é "92,3% de acurácia"**; leitura correta =
> "melhor resultado observado entre os candidatos nesta coleção/configuração", não
> conclusão geral sobre manuscrito pt-BR; (4) a **lacuna de observabilidade do corpo do
> erro HTTP continua ABERTA** no runner v2 (num_ctx apenas evitou o 400 nesta coleção).
> Detalhe completo em `evidence/AV-S05B/amostras/manuscrito/DIAGNOSTICO_HTTP400_qwen2.5vl_2026-10-15.md`
> (nota de reconciliação no topo) e no documento de precisão metodológica desta rodada.

Consolidação da rodada do benchmark OCR local parcial (Amostra_1, eixo manuscrito) e
investigação dirigida das falhas HTTP 400 do `qwen2.5vl:3b`. Rafael autorizou diagnóstico
e correção **LOCAL** do caminho experimental, sem alterações no produto.

## 1. Preservação da rodada 1 (benchmark parcial Amostra_1)

A rodada original é mantida **imutável**: 36 JSON brutos (4 candidatos × 9 amostras),
agregado, ambiente, referências, `RESULTADOS_benchmark_parcial_Amostra_1.md`,
`RUNNER_SPEC_CONGELADA.md`, manifesto e checksums. O benchmark foi executado em
2026-10-15 ~15:18–15:19 (America/Sao_Paulo; carimbo UTC `20261015T181836Z` nos brutos).

**Correção estrutural do manifesto (rodada 1):** durante a rodada 1 houve uma correção de
um bug do próprio orquestrador no manifesto (chave `pares`→`amostras`, campos
`imagem_png`/`referencia_txt`), com re-execução; não era defeito do runner nem dos
critérios. O manifesto final (`manifesto_pares.json`, chave `amostras`) é o que produziu
os 36 resultados; nenhum resultado foi produzido sob o manifesto com o bug (a re-execução
regravou tudo).

## 2. Precisão dos resultados da rodada 1 (conferência, sem mudar o protocolo)

- **"7/7 ok"** (Tesseract, EasyOCR, moondream:v2) significa **execução bem-sucedida**, não
  transcrição útil. O agregador conta `status == ok`; **saída vazia conta como ok** (o prompt
  manda responder vazio quando ilegível). Ex.: Tesseract tem CER 1,0 em todas as 7 (saída
  vazia) e ainda assim "7/7 ok". A frase descreve execução, não qualidade.
- **"nenhuma abstenção"** está correta: nenhum registro tem `status = abstencao`. As saídas
  vazias são `status ok, produziu_texto=False` — por definição do protocolo (§6) e da
  heurística do runner, saída vazia NÃO é abstenção. A definição não foi alterada
  retroativamente.
- **IDs das 2 amostras eval bem-sucedidas do Qwen na rodada 1: MAN-02 e MAN-03.**
- **MAN-01 é `dev`** e NÃO entra no agregado eval (fica em `dev_sanidade`).
- **CER/WER do Qwen na rodada 1 (0,318/0,350)** são condicionados a apenas MAN-02 e MAN-03 e
  **não comparáveis** ao conjunto completo dos outros candidatos — registrado como tal.

## 3. Diagnóstico do HTTP 400 — causa COMPROVADA (não é payload)

Causa comprovada: **num_ctx padrão do Ollama (4096) estourado pelos tokens de VISÃO** da
imagem decodificada — não limite de payload. Detalhe completo, tabelas e reproduções em
`evidence/AV-S05B/amostras/manuscrito/DIAGNOSTICO_HTTP400_qwen2.5vl_2026-10-15.md`. Resumo:

- A hipótese "limite de payload" do relatório da rodada 1 está **refutada**: o tamanho do
  arquivo PNG não prediz a falha (MAN-03 7,2 MB passou; MAN-04 5,7 MB falhou; MAN-EVAL-06
  8,9 MB passou).
- O corpo real do erro — que o runner v1 descartava (só guardava `str(exc)`) — é
  `exceed_context_size_error`: "request (N tokens) exceeds the available context size (4096)".
- `n_prompt_tokens` separa os casos exatamente na fronteira 4096, sem exceção: passaram
  4073–4084 (MAN-02/03/EVAL-06); falharam 4107–4156 (EVAL-07/05/07/04/06).
- A rodada 1 já continha a assinatura: `ollama_meta.prompt_eval_duration` ≈ 8,5 s nas falhas
  (o modelo processou a imagem antes de rejeitar — incompatível com rejeição de transporte).
- Ambiente: Ollama 0.33.3; `qwen2.5vl:3b` (ID `fb90415cde1e`); `127.0.0.1:11434/api/generate`.
- Nenhuma imagem/conteúdo foi exposto; diagnóstico 100% local.

Registrado também um **gap de observabilidade** do runner v1 (não lia o corpo do erro HTTP).

## 4. Correção e nova medição (condições do item 4 atendidas)

Rafael classificou `num_ctx` como **transporte/serialização** e autorizou reexecutar o Qwen.
A correção é elevar `options.num_ctx` 4096→8192, preservando imagem (mesmo base64), prompt,
modelo e temperatura (=0). Validação: as 5 amostras que davam 400 passaram a HTTP 200.

- **Runner v2 congelado**: `local-nao-versionado/ocr/Amostra_1/rodada2_qwen_num_ctx/bench_runner_v2.py`
  (+ `.sha256`); única diferença funcional é `num_ctx=8192`; 19/19 testes sintéticos passam.
- **Rodada 2 (Qwen, 9 amostras)** gravada em rodada NOVA
  (`rodada2_qwen_num_ctx/resultados_brutos/`), sem substituir a rodada 1. Resultado eval:
  **7/7 ok** (antes 2/7 + 5 falha); **CER médio 0,077**, **WER médio 0,168** (primeira medida
  comparável do Qwen no eval completo); controle vazio MAN-EVAL-06 sem invenção.

Resultado **parcial e exploratório** — nenhuma solução promovida a produção.

## 5. Limites preservados (não alterados)

- **AC-05 NÃO concluído** (MAN-EVAL-07 é legível; sem estímulo ilegível comprovado).
- **Revisão humana cronometrada** pendente; não estimada por IA.
- `AV-S05B` permanece **PARCIAL**; nenhuma decisão arquitetural (`BL-AV-4B-02`/ADR-009).
- Numerador homologado **22/70** inalterado; nenhum baseline promovido.
- `avalia_dev`/apresentação não tocados; nenhum código de produto alterado.
- **AC-05 e revisão humana cronometrada continuam pendentes; AV-S05B NÃO concluído; 22/70 inalterado.**

## 6. Ação Git/remota desta execução

**Nenhuma.** Não houve stage/commit/push/merge. O working tree de `main` tem apenas o
diretório untracked `docs/governance/evidence/AV-S05B/amostras/manuscrito/` (artefatos do
benchmark, nunca commitados) — preservado como estava, agora acrescido do documento de
diagnóstico e deste snapshot. Os brutos/runner/rodada 2 ficam em `local-nao-versionado/`
(não entra em Git por construção). Arquivos de governança destinados a versionamento futuro
≠ arquivos efetivamente commitados: nesta rodada **não houve publicação Git**.
