---
id: "proposta_proximo_experimento_av-s05b_manuscrito"
tema: "AV-S05B eixo manuscrito — proposta curta de próximo experimento (confirmação independente)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "PROPOSTA — não autoriza execução; aguarda decisão de Rafael. Nenhuma nova inferência nesta rodada."
---

# Proposta curta — próximo experimento (confirmação independente) do eixo manuscrito

Objetivo: confirmar de forma independente o indício exploratório da rodada 2 (qwen2.5vl:3b
como melhor resultado observado nesta coleção/configuração), sem herdar o viés do ajuste
de configuração informado pelas próprias falhas do eval. **Esta é uma proposta; não autoriza
execução, não reexecuta nada e não mistura coleções.**

## Condições de validade (pré-registradas ANTES de qualquer nova amostra)

1. **Configuração congelada antes das novas amostras.** Fixar e versionar, antes de ver
   qualquer imagem nova: modelo e tag (`qwen2.5vl:3b`, ID), `num_ctx`, temperatura, prompt,
   e demais `options`. A configuração passa a ser parâmetro fixo do experimento; nenhum ajuste
   pode ser informado pelos resultados da nova coleção (sob pena de deixar de ser confirmação
   independente). O `num_ctx` deixa de ser "correção ad hoc" e passa a ser configuração
   declarada do protocolo.

2. **Segunda coleção produzida pelo parceiro, ainda não usada para ajustes.** As novas
   amostras (Amostra_2) devem vir do parceiro e **nunca** ter sido usadas para calibrar
   configuração, prompt ou scoring. Confirmação só é independente se as imagens forem inéditas
   para o pipeline.

3. **Controle genuinamente ilegível, com avaliação humana cega.** Incluir pelo menos um
   estímulo comprovadamente ilegível (não apenas vazio), com a ilegibilidade atestada por
   avaliação humana **sem conhecimento do original** — é o que fecha o AC-05, hoje em aberto
   (MAN-EVAL-07 da Amostra_1 é legível e NÃO serve como controle de ilegibilidade).

4. **Revisão humana cronometrada conforme o protocolo existente.** Medir o esforço de revisão
   humana com cronômetro, pelo procedimento já previsto no protocolo (§12), por revisor humano
   real — não estimado por IA. Pendência registrada desde a rodada 1.

## Item de engenharia a corrigir antes (observabilidade)

5. **Preservar o corpo do erro HTTP de forma sanitizada.** A lacuna continua aberta no runner
   v2: o `_post` usa `urllib.request.urlopen`, que levanta `HTTPError` antes de ler o corpo,
   e o `except` grava só `str(exc)`. Antes do próximo experimento, o runner deve capturar
   `urllib.error.HTTPError`, ler `e.read()` e registrar o corpo **sanitizado** (sem imagem,
   sem conteúdo da coleta — apenas código, tipo de erro e campos como `n_prompt_tokens`/`n_ctx`),
   para que qualquer falha futura seja diagnosticável sem reprodução manual.

## Restrições explícitas (invioláveis nesta linha)

- **Não substituir MAN-EVAL-07 da Amostra_1** nem qualquer amostra da primeira coleção.
- **Não misturar resultados das duas coleções** em um mesmo agregado; a Amostra_2 é medida e
  reportada separadamente, e só então comparada descritivamente, com as diferenças de coleção
  e configuração explicitadas.
- A rodada 2 da Amostra_1 permanece como **resultado exploratório** (mesmas amostras, após
  ajuste informado pelas falhas), não como avaliação independente.
- Nada é promovido a produção; `AV-S05B` permanece **parcial**; numerador **22/70**; nenhuma
  decisão arquitetural (`BL-AV-4B-02`/ADR-009).

## Entregáveis do próximo experimento (quando autorizado)

- Protocolo/configuração congelados e versionados (com checksum) antes da coleta.
- Runner com observabilidade do erro HTTP corrigida (item 5), revisado no delta.
- Resultados da Amostra_2 em rodada própria, separada da Amostra_1.
- AC-05 fechado por controle ilegível com avaliação cega; revisão humana cronometrada medida.
- Só então: comparação descritiva entre coleções/configurações e eventual insumo para
  `BL-AV-4B-02`/ADR-009 — ainda sem promover solução.
