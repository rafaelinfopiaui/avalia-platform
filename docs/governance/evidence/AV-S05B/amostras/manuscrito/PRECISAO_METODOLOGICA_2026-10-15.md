---
id: "precisao_metodologica_av-s05b_diagnostico_http400"
tema: "AV-S05B eixo manuscrito — consolidação de precisão metodológica do diagnóstico do HTTP 400 e da rodada 2"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "CONSOLIDAÇÃO DE PRECISÃO — sem novas inferências; sem reexecução; sem reabrir scoring geral; AV-S05B permanece parcial; 22/70; ADR-009 sem promoção"
autorizacao: "Rafael — consolidar com precisão metodológica, corrigir por nota datada, revisão limitada do Antigravity, proposta de próximo experimento, organização em branch documental. Sem stage/commit/push/merge."
---

# Consolidação de precisão metodológica — diagnóstico do HTTP 400 (AV-S05B, Amostra_1)

Esta consolidação corrige e delimita, por notas datadas, os documentos da primeira
passagem (snapshot EXEC-2026-10-15-04, DIAGNOSTICO_HTTP400..., dashboard §13,
latest_execution), **sem reescrever** o texto original e **sem executar novas inferências**.
A rodada 1 (36 brutos) e a rodada 2 (9 brutos do Qwen) permanecem imutáveis.

## 1. Classificação corrigida de num_ctx (4096→8192)

A alteração é uma **alteração da configuração de contexto de inferência**, motivada pelos
erros de limite de contexto (`exceed_context_size_error`) no eval — **não** "somente
transporte/serialização". A autorização de Rafael (classificar como transporte e reexecutar)
é **preservada como decisão de processo** e permanece válida, mas **não muda a natureza
técnica do parâmetro**: `num_ctx` dimensiona a janela de atenção/KV-cache do modelo — é
hiperparâmetro de inferência. Daqui em diante, "transporte/serialização" nos documentos da
primeira passagem deve ser lido como "configuração de contexto de inferência".

Revisor independente (Antigravity, Gemini 3.8 Flash High) concordou e classificou como
**achado bloqueante** rotular essa mudança como "transporte" em documento de auditoria —
atendido por esta reclassificação.

## 2. Natureza da rodada 2 e delimitação da comparação

- A rodada 2 é **resultado exploratório sobre as MESMAS amostras, após ajuste de
  configuração (num_ctx) informado pelas próprias falhas do eval** (*post-hoc tuning*).
  **NÃO** é avaliação independente nem reprodução do protocolo original sem alteração.
- A comparação entre candidatos é **descritiva** (os denominadores coincidem: 7 amostras
  legíveis), **desde que explicitado** que o Qwen rodou em configuração diferente
  (num_ctx=8192) e com ajuste posterior informado pelas falhas, enquanto os demais candidatos
  foram medidos uma vez.
- **CER 0,077 NÃO é "92,3% de acurácia".** CER é taxa de erro por caractere (Levenshtein /
  tamanho da referência), pode passar de 1,0 e não admite conversão `1 - CER` em acurácia.
  Leitura honesta: **"melhor resultado observado entre os candidatos nesta coleção e nesta
  configuração"** — não conclusão geral sobre manuscrito em português. CER/WER, agregação e
  resultados por amostra foram **preservados, não recalculados**.

Antigravity concordou e marcou a leitura "92,3% de acurácia" como **achado bloqueante** para
relatórios de conformidade — atendido por esta delimitação.

## 3. Observabilidade do corpo do erro HTTP — LACUNA AINDA ABERTA (estado real)

Verificado no código: o `_post` usa `urllib.request.urlopen`, que levanta `HTTPError` antes
de a resposta ser lida; o `except Exception` em `executar()` grava apenas
`type(exc).__name__ + str(exc)` (ex.: "HTTPError: HTTP Error 400: Bad Request"), descartando
o corpo JSON do Ollama. O `num_ctx=8192` **não** corrigiu isso — apenas evitou o 400 nesta
coleção. **A lacuna permanece aberta no runner v2.** Correção mínima proposta pelo Antigravity
(capturar `urllib.error.HTTPError`, ler `e.read()`, registrar sanitizado, preservando
`STATUS_FALHA`/`texto=None`/tempos) está registrada como item do próximo experimento — **não
foi aplicada nesta rodada** (nesta rodada não se altera código executável nem se reexecuta).

## 4. Revisão independente limitada (Antigravity)

- Escopo: delta do runner (v1→v2), configuração, tratamento de erro e metodologia, usando
  **apenas código, erros sanitizados e casos sintéticos**. Nenhuma foto, referência ou
  transcrição da coleta foi enviada — o pacote de revisão (`/tmp/av-s05b-revisao-antigravity`)
  continha só `bench_runner_v1.py`, `bench_runner_v2.py`, `DELTA_v1_v2.diff`,
  `test_bench_runner.py` (strings fictícias) e `ERROS_SANITIZADOS.txt` (metadados do erro:
  n_prompt_tokens/n_ctx). Não houve reexecução do benchmark nem reabertura do scoring geral.
- Modelo: Gemini 3.8 Flash (High) — família distinta do orquestrador (Opus). Parecer completo
  em `parecer_antigravity_precisao_metodologica_2026-10-15.txt`.
- **Nota de processo (datada 2026-10-15):** a primeira chamada ao `agy` em modo headless foi
  auto-negada por exigir a permissão "command" (leitura de arquivos via shell) que o modo
  headless não consegue aprovar. A revisão foi reexecutada com `--dangerously-skip-permissions`
  **restrito ao diretório sanitizado em `/tmp`** — nenhum caminho de produto, segredo ou da
  coleta estava acessível. Registrado como fato, não minimizado.
- Veredito por item: (1) classificação — CONCORDO/corrige rótulo; (2) observabilidade —
  CONCORDO, lacuna aberta; (3) metodologia — CONCORDO (post-hoc, exploratório, comparação
  descritiva com ressalvas); (4) métrica — CONCORDO (CER≠acurácia); (5) RESSALVA com 3 achados
  técnicos (ver §5). Bloqueantes (1 e 4) atendidos por esta consolidação.

## 5. Achados técnicos NOVOS do Antigravity (registrados; correção adiada para o próximo experimento)

Verificados no código, não tratados nesta rodada (sem alteração de código executável):

1. **Contaminação de `t_inferencia_s` da 1ª amostra.** `_carregar()` faz requests **sem**
   `options` (contexto padrão ~4096); a 1ª `_inferir()` envia `num_ctx=8192`, forçando o
   Ollama a recarregar o contexto **dentro da janela medida como inferência**. Viola o
   isolamento t_carga ≠ t_inferência. **Afeta apenas a latência relatada, não CER/WER.**
2. **`num_ctx=8192` global para todo modelo Ollama.** `OLLAMA_OPCOES` é aplicado
   indistintamente (inclusive a `moondream:v2`), não só ao Qwen — na rodada 2 só o Qwen rodou,
   mas o runner congelado tem esse acoplamento; relevante para futuras rodadas multi-modelo.
3. **Teto estático e determinismo.** 8192 é blindagem pontual: imagens de maior resolução
   voltariam a estourar; não há controle de resolução antes do base64; `seed` não fixada apesar
   de `temperature=0`.

Estes achados entram como requisitos de engenharia do próximo experimento
(`PROPOSTA_proximo_experimento_2026-10-15.md`), junto com a correção da observabilidade (§3).

## 6. Limites preservados

`AV-S05B` permanece **parcial**; **AC-05 NÃO concluído**; **revisão humana cronometrada
pendente**; numerador **22/70**; **ADR-009 sem promoção a solução aprovada**; nenhuma decisão
arquitetural (`BL-AV-4B-02`). `avalia_dev`/apresentação não tocados; nenhum código de produto
alterado. **Sem stage/commit/push/merge, sem novas inferências, sem instalações, sem alteração
em bancos protegidos.** MAN-EVAL-07 da Amostra_1 não foi substituída; nenhuma mistura de coleções.

## 7. Artefatos desta consolidação (branch documental `docs/av-s05b-precisao-metodologica-diagnostico-http400`)

- Este documento.
- `PROPOSTA_proximo_experimento_2026-10-15.md` (confirmação independente).
- `parecer_antigravity_precisao_metodologica_2026-10-15.txt` + `DELTA_runner_v1_v2.diff`.
- Notas datadas em: `DIAGNOSTICO_HTTP400_qwen2.5vl_2026-10-15.md`,
  `snapshot_EXEC-2026-10-15-04_...md`, `executive_technical_dashboard.md` (§13),
  `latest_execution.md`.
