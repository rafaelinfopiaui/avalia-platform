# Registro de publicação — Planejamento AV-S04 — 2026-09-30

## Rodada 3 (2026-09-30, mesma data) — compatibilidade, migração e limites definidos; bloqueado por organização local

- Checkout: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s04-planning`
  (mesmo worktree das rodadas 1-2, reaproveitado).
- Branch: `docs/av-s04-planejamento` (mesma branch; PR #7 já aberto em
  rascunho pela rodada 1).
- Base no início desta rodada: `origin/docs/av-s04-planejamento` no
  commit `303a0b9daf604d44b42d08ac1bdec1dc1195013d` (rodada 2), que por
  sua vez está sobre `main@ba6f4074...`.
- Working tree no início desta rodada: limpo, sincronizado com o remoto.
- Gatilho: Rafael definiu os pontos restantes da rodada 2 — aprovou os
  limites de 50 questões/10.000 caracteres com escopo precisado (não
  indiscriminado a título/identificadores), não confirmou implantação
  conjunta de backend/frontend (adotando compatibilidade `questions`
  canônico + `question` legado, sem prazo de remoção inventado), e pediu
  precisão técnica da estratégia de migração (`NOT VALID` aplicado apenas
  a constraints corretas; backfill considerando todos os dados permitidos
  pelo schema, não apenas o contrato de API atual).
- Execução: seções 3.2, 3.4 e 3.7 reescritas conforme as definições de
  Rafael; critérios de aceite ajustados (AC-03 recontextualizado, AC-09/
  AC-12/AC-13 revisados, AC-16/AC-17/AC-18 adicionados); revisão
  independente limitada às mudanças desta rodada despachada via
  `delegate_task` (`deleg_6a39b7c2`), com 8 achados verificados contra o
  código real e corrigidos antes da publicação.

## Escopo desta publicação (rodada 3)

- Reescrita de `docs/governance/sprints/sprint_AV-S04_multiplas_questoes.md`:
  - seção 3.2: `questions` canônico com `question` como entrada legada
    temporária (normalização de entrada, saída computada `question` só
    para 0/1 questão, instrumentação de uso via `log_event`, depreciação
    documentada sem prazo inventado, sem consumidor externo presumido);
  - seção 3.4: migração reespecificada com precisão por constraint
    (`NOT VALID`/`VALIDATE CONSTRAINT` só para `CHECK`/`FOREIGN KEY`;
    `CREATE UNIQUE INDEX CONCURRENTLY` + `ADD CONSTRAINT ... USING INDEX`
    para a `UniqueConstraint`), consulta de verificação real de dados
    antes de presumir backfill trivial, nota de limpeza de índice
    `INVALID` remanescente;
  - seção 3.7: tabela de escopo precisa por campo (limite de 10.000
    caracteres aplicado somente a `statement`/`reference_answer`, não a
    `title`/identificadores/`max_score`), testes de limite exigidos
    incluindo teste negativo e teste de não-interferência em `max_score`;
  - seção 7b: tabela de rastreabilidade da revisão independente desta
    rodada;
  - checklist de DoR atualizado.
- Criação de `docs/governance/evidence/AV-S04/revisao_independente_rodada3_2026-09-30.md`
  com o parecer completo da revisão desta rodada.
- Este registro de publicação, atualizado para a rodada 3.

## Decisão explícita de não autorização de execução

Conforme instrução de Rafael, esta rodada **não marca a sprint como
autorizada para execução**. O planejamento está registrado como
aguardando:
1. conclusão da organização local do diretório `avalia-plataform`
   (consolidação de worktrees/checkouts, pendência já conhecida desde
   GOV-006);
2. autorização de implementação separada, a ser decidida depois da
   organização local, não nesta rodada.

## O que esta publicação NÃO faz

- Não implementa nenhuma linha de código de AV-S04.
- Não altera `core/`, `ai-engine/` ou `frontend/`.
- Não executa nenhuma migração, nem a consulta de verificação de dados
  nem qualquer DDL, nem isolada nem em `avalia_dev`.
- Não faz merge.
- Não faz deploy.
- Não aprova a sprint; `status` do sprint document permanece em
  `planejamento_detalhado_rodada3_aguardando_revisao_independente_e_organizacao_local`.
- Não reabre nenhuma decisão já aprovada nas rodadas 1-2 (clonagem,
  helper de autorização, concorrência, ordenação de rubrica) — apenas as
  três decisões explicitamente trazidas por Rafael nesta rodada (limites,
  compatibilidade, precisão de migração) foram tratadas.
- Não depende da coleta manuscrita de AV-S05B; não altera o estado de
  AV-S05B como investigação parcial.
- Não reorganiza diretórios — a consolidação de `avalia-plataform` é
  reconhecida como próximo passo, mas não iniciada aqui.

## Validação aplicada (rodada 3)

- Conferência manual de cada achado da revisão independente contra o
  código real (`schemas.py`, `models.py`, `seed.py`, fixtures de teste)
  antes de aplicar qualquer correção ao sprint document.
- Verificação de duplicação acidental de conteúdo após edições
  sucessivas via `patch` (encontrada e corrigida uma duplicação de bloco
  na seção 3.4 antes da publicação).
- Varredura de padrões de credencial nos arquivos novos/alterados: nenhum
  encontrado.
- Nenhum teste de código aplicável (mudança exclusivamente documental).
- Nenhuma consulta SQL de verificação, migração ou DDL foi executada —
  apenas especificada em texto.

---

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

