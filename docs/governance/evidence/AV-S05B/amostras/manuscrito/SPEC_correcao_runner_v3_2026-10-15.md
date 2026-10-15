---
id: "spec_correcao_runner_v3"
tema: "AV-S05B manuscrito — especificação da correção do runner (v3), ANTES da implementação"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "ESPECIFICAÇÃO — detalhada antes de implementar; NÃO congelada (há implementação e revisão pendentes); sem inferência sobre coleções nesta rodada"
executor_previsto: "Claude Code (executor principal); Antigravity revisa o delta pelo fluxo permitido"
---

# Especificação da correção do runner — v3 (detalhada antes de implementar)

v3 = v2 + correções pontuais abaixo. **Mantém imutáveis** v1, v2, resultados, checksums e
timestamps. **Não altera** o scoring (normalizar/levenshtein/CER/WER/agregação) nem o prompt,
nem a semântica de medição. Objetivo: tornar o runner correto e observável para o PRÓXIMO
experimento (Amostra_2) — nesta rodada **não há inferência sobre nenhuma coleção**; validação
somente por testes sintéticos/mockados.

## Princípio inviolável

Falha de contexto (e qualquer erro de inferência) **permanece `falha_execucao`**. É
**proibido**: aumento automático de `num_ctx`, resize/compressão/recorte de imagem, e retry
com parâmetros diferentes de forma oculta. A amostra que falha continua no denominador como
falha, com o erro diagnóstico registrado. Nenhuma "recuperação silenciosa".

## Correção 1 — Corpo do erro HTTP: capturar, limitar e sanitizar

- Em `_post`, capturar `urllib.error.HTTPError`, ler `exc.read()` (corpo), e levantar
  `RuntimeError` com: código HTTP + corpo **truncado a um limite** (ex.: 2048 chars) +
  passagem por um **sanitizador**.
- Sanitizador (função dedicada, testável): remove/!mascara qualquer ocorrência de
  `images`/base64 (strings longas base64-like), caminhos de arquivo da coleta, e cabeçalhos
  de credencial (`authorization`, `api-key`, `token`, `cookie`). Preserva campos úteis de
  diagnóstico do Ollama: `code`, `type`, `message`, `n_prompt_tokens`, `n_ctx`,
  `error`. Nunca inclui a imagem, o base64 nem a transcrição.
- O status resultante continua `falha_execucao`; `texto=None`; o `t_inferencia_s` segue sendo
  o tempo de parede da tentativa (sem mudança de semântica). O erro agora é **diagnóstico**
  (ex.: `ollama HTTP 400: exceed_context_size_error n_prompt_tokens=4131 n_ctx=4096`), não
  opaco.
- Também aplicar a captura/sanitização em `URLError`/timeout (mensagem sanitizada, sem corpo).

## Correção 2 — Mesma configuração de contexto na carga e na inferência; tempos separados

- `_carregar()` passa a enviar as **mesmas** `options` de contexto que `_inferir()` usará
  (no mínimo `num_ctx`), de modo que a reconfiguração de contexto ocorra DENTRO da janela de
  `t_carga_s`, não da primeira `t_inferencia_s`.
- `t_carga_s` (primeira vez) e `t_inferencia_s` permanecem campos distintos; a spec §7.3 de
  isolamento passa a ser respeitada de fato. Nenhuma estimativa/subtração: a separação é
  estrutural (a carga já paga o custo do contexto).

## Correção 3 — Opções por candidato (num_ctx do Qwen não afeta outros modelos)

- Substituir o `OLLAMA_OPCOES` global por **opções por candidato**: um mapa
  `{modelo -> options}` (ou options passadas ao construir cada `AdaptadorOllamaVLM`), com um
  default conservador. `num_ctx=8192` fica associado **somente** ao `qwen2.5vl:3b`; modelos
  como `moondream:v2` não herdam 8192 silenciosamente.
- O adaptador registra, em `parametros()` e no ambiente, as options efetivas de cada candidato
  (auditável).

## Correção 4 — Registrar seed e parâmetros suportados, sem prometer determinismo absoluto

- Incluir `seed` explícito nas options (valor fixo declarado) e registrar no ambiente todos
  os parâmetros de inferência efetivos por candidato (`temperature`, `seed`, `num_ctx`, etc.).
- A documentação/relatório deve dizer: "seed fixa e temperature=0 **reduzem** a variação, mas
  **não garantem determinismo absoluto** (dependem de versão do runtime, backend, hardware,
  paralelismo)". Não afirmar reprodutibilidade bit-a-bit.

## Correção 5 — Falha de contexto como falha de execução (reafirmação no código)

- Garantir, por teste, que um erro `exceed_context_size_error` (HTTP 400) resulta em
  `status=falha_execucao`, `texto=None`, `cer=None`, `wer=None`, amostra **no denominador**,
  e que **nenhum** caminho do runner tenta reenviar com `num_ctx` maior, redimensionar ou
  recomprimir. Teste negativo explícito contra "recuperação silenciosa".

## Validação exigida (sem fotos nem saídas da coleta)

- Testes sintéticos/mockados: um **mock do endpoint Ollama** (sem rede real, sem imagem) que
  simula (a) 200 com `response`/meta; (b) HTTP 400 com corpo `exceed_context_size_error`;
  (c) corpo com campos sensíveis (base64/authorization) para provar a sanitização; (d)
  timeout/URLError.
- Reaproveitar e manter passando os 19 testes sintéticos existentes do scoring.
- Nenhuma chamada a Ollama real, nenhuma leitura de imagem da coleta nesta rodada.

## Não-metas desta rodada

- Não reexecutar benchmark; não medir Amostra_1 nem Amostra_2; não congelar v3 (há
  implementação + revisão independente pendentes); não promover solução; `AV-S05B` parcial;
  `22/70`; `ADR-009` sem promoção.
