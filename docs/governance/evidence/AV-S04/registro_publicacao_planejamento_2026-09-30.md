# Registro de publicação — Planejamento AV-S04 — 2026-09-30

## Rodada 2 (2026-09-30, mesma data) — detalhamento das 7 decisões + revisão independente

- Checkout: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s04-planning`
  (mesmo worktree da rodada 1, reaproveitado).
- Branch: `docs/av-s04-planejamento` (mesma branch; PR #7 já aberto em
  rascunho pela rodada 1).
- Base no início desta rodada: `origin/docs/av-s04-planejamento` no
  commit `e98f43c7b02abdaaf69c04c9535bf18d9192df39` (rodada 1), que por
  sua vez está sobre `main@ba6f4074...`.
- Working tree no início desta rodada: limpo, sincronizado com o remoto.
- Gatilho: Rafael aprovou em princípio as 7 decisões da seção 3 e pediu
  detalhamento técnico de cada uma (cópia/rastreabilidade da clonagem,
  levantamento de consumidores do contrato singular, autorização e
  restrição a rascunho dos endpoints de coleção, backfill/transação de
  `position`, limites de associação resposta-questão, tratamento de
  avaliação incompleta na pontuação, valores concretos de limite
  máximo/tamanho), critérios de aceite atualizados, e revisão independente
  do plano por um agente que não o redigiu.
- Execução: detalhamento escrito diretamente no sprint document já
  publicado; revisão independente despachada via `delegate_task`
  (`deleg_cf841444`) com acesso de leitura ao código real; achados do
  revisor conferidos manualmente contra o código antes de aplicados;
  5 correções técnicas aplicadas ao sprint document (ver seção 7 do
  documento e `revisao_independente_2026-09-30.md`).

## Escopo desta publicação (rodada 2)

- Reescrita de `docs/governance/sprints/sprint_AV-S04_multiplas_questoes.md`:
  seções 3.1 a 3.7 detalhadas com evidência de código, critérios de
  aceite expandidos (AC-06 a AC-15), nova seção 7 com tabela de
  rastreabilidade da revisão independente, checklist de DoR atualizado.
- Criação de `docs/governance/evidence/AV-S04/revisao_independente_2026-09-30.md`
  com o parecer completo do revisor e o tratamento dado a cada achado.
- Este registro de publicação, atualizado para a rodada 2.

## O que esta publicação NÃO faz

- Não implementa nenhuma linha de código de AV-S04.
- Não altera `core/`, `ai-engine/` ou `frontend/`.
- Não executa nenhuma migração, nem isolada nem em `avalia_dev`.
- Não aprova a sprint; `status` do sprint document permanece em
  `planejamento_detalhado_com_revisao_independente_aguardando_aprovacao_final`.
- Não reabre nenhuma das 7 decisões de direção já aprovadas por Rafael —
  apenas detalha tecnicamente cada uma e corrige imprecisões identificadas
  pela revisão independente.
- Não depende da coleta manuscrita de AV-S05B; não altera o estado de
  AV-S05B como investigação parcial.
- Não faz merge nem promove baseline.
- Não reorganiza diretórios.

## Validação aplicada (rodada 2)

- Conferência manual de cada achado do revisor contra o código real
  (`models.py`, `schemas.py`, `main.py`, `routers/academic.py`) antes de
  aplicar qualquer correção ao sprint document.
- Varredura de padrões de credencial nos arquivos novos/alterados: nenhum
  encontrado.
- Nenhum teste de código aplicável (mudança exclusivamente documental).

---

## Rodada 1 (2026-09-30) — publicação inicial do planejamento

### Rito de execução (antes da publicação inicial)

- Checkout: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s04-planning`
- Branch criada: `docs/av-s04-planejamento`
- Base Git: `origin/main@ba6f4074f49f87461c515081964a2aff6202e6cb`
  (commit de merge do PR #6 — GOV-006 — momentos antes desta criação)
- Working tree no momento da criação do worktree: limpo, sincronizado com
  `origin/main` recém atualizado pelo merge do PR #6.
- Alterações locais relevantes ainda não incorporadas (fora deste
  worktree, sem relação com este pacote):
  - proposta de saneamento de 676 linhas em
    `avalia-plataform/docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`
    (checkout principal, branch `docs/av-s02-encerramento-planos-operacionais`);
  - worktree `av-s03-work` (base histórica `main@a5974b1`), preservado, não
    tocado nesta execução;
  - worktree órfão `/private/tmp/av-s03-work`, `prunable`, não removido.

### Escopo da publicação inicial

- Criação do sprint document canônico de planejamento:
  `docs/governance/sprints/sprint_AV-S04_multiplas_questoes.md`.
- Atualização de `docs/governance/backlog/backlog_tecnico_avalia.md`:
  `BL-AV-3-01` a `BL-AV-3-04` passam de `proposto` para
  `planejamento publicado (2026-09-30)`, com link ao sprint document.
- Atualização de `docs/governance/executive_technical_dashboard.md`:
  nova linha "Auditoria de governança encerrada" (GOV-006/PR #5/PR #6
  integrados) e nova linha "Planejamento publicado, sprint não iniciada"
  (AV-S04).
- Este próprio registro de publicação.

### O que a publicação inicial NÃO fez

- Não implementou nenhuma linha de código de AV-S04.
- Não alterou `core/`, `ai-engine/` ou `frontend/`.
- Não aprovou a sprint AV-S04.
- Não dependeu da coleta manuscrita de AV-S05B.
- Não fez merge nem promoveu baseline.

### Validação aplicada (rodada 1)

- Revisão de referências Markdown entre os três arquivos alterados/criados.
- Varredura de padrões de credencial nos arquivos novos/alterados: nenhum
  encontrado.
- Nenhum teste de código aplicável (mudança exclusivamente documental).

