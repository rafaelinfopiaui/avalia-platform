---
id: "EXEC-2026-09-29-03"
tipo: execucao
sprint: "AV-S03 (fechamento de AC-05) / governanca geral (reconciliacao PR #2)"
gerado_em: "2026-09-29T09:45:00-03:00"
executor: "Hermes"
consolidador: "Hermes"
---

# EXEC-2026-09-29-03 — Fechamento de AC-05 e reconciliação do PR #2

## 1. Objetivo desta fatia

Antes do encerramento documental completo da `AV-S03`, atender três pontos
levantados por Rafael: (1) fechar a lacuna de validação visual de `AC-05`
com evidência real produzida nesta rodada, não reaproveitada; (2) comparar
o conteúdo do PR #2 contra `main` e preservar o que ainda é necessário em
versão atualizada; (3) atualizar o PR #4 refletindo isso, sem declarar
fechamento integral enquanto houver decisão pendente.

## 2. AC-05 — requisito, lacuna, execução, resultado

**Requisito exato** (seção 9 do documento da sprint): "usuário não
autenticado recebe 401 e retorna ao destino após login quando aplicável".

**Já comprovado antes desta rodada**: a parte automatizada — 401 sem token
em `/v1/class-groups` e `/v1/enrollments`
(`test_academic_routes_require_authentication`), parte da suíte 68/68
reconfirmada em múltiplas rodadas, inclusive pós-integração do PR #3.

**Lacuna identificada**: a segunda metade do critério — retorno ao destino
após login — nunca havia sido verificada visualmente na reconstrução; o
registro anterior dizia explicitamente "retorno pós-login não reverificado
visualmente nesta rodada".

**Execução**: dentro do escopo local já autorizado para a AV-S03 (execução
local, PostgreSQL isolado, validação visual). Ambiente isolado e
descartável: PostgreSQL dedicado (porta 55440), backend e frontend reais no
código da branch já integrada a `main`, Chromium via Playwright em venv
descartável dedicado a esta validação (não reaproveitado). Roteiro: acesso
não autenticado a `/academico` → confirma redirect a `/login` com
`history.state.from = "/academico"` → login real → confirma retorno
automático a `/academico` (`page.wait_for_url` + evidência visual).

**Achado transparente, não defeito de produto**: a primeira tentativa
reportou falso alarme (permaneceu em `/login`); causa raiz identificada no
log do backend (`OPTIONS /v1/auth/login → 400`) — erro de configuração de
`CORS_ORIGINS` no próprio ambiente de teste isolado (`localhost` vs.
`127.0.0.1`), não no código do produto. Corrigido o ambiente e reexecutado
com espera determinística até confirmação real.

**Resultado**: `AC-05` atendido, evidência completa (screenshots, JSON
estruturado, script reexecutável) em
`docs/governance/evidence/AV-S03/AC-05-visual/` e
`AC-05_validacao_retorno_pos_login.md`. Documento da sprint atualizado:
`AC-05` e `BL-AV-2-05` de "parcial"/"401 automatizado apenas" para
"executado e confirmado" — **12 de 12 critérios de aceite da AV-S03 agora
com evidência real completa**.

## 3. Reconciliação do PR #2 contra `main`

Comparação completa (`git diff origin/main...7f18ec3`, por arquivo) em
`docs/governance/snapshots/snapshot_RECONCILIACAO-2026-09-29-02_desvio-processo-2026-09-24.md`.
Resumo:

- **já incorporado**: `DEC-AV-022` (`registers/decisions.md`) — idêntico
  em `main`, não reaplicado;
- **ainda necessário e ausente, reincorporado nesta branch**:
  `execution_policy.md` (regra formal de branch+PR obrigatório, nunca
  antes aplicada à política em si); detalhamento completo do desvio de
  processo de 24/09 (3 estados distintos, evidência SQL), com
  reconfirmação **read-only** desta data de que `avalia_dev` segue no
  mesmo estado (1 grupo duplicado, job `4f56a10b-...`, 3 linhas, sem
  `UniqueConstraint` — nenhuma escrita realizada); plano completo de
  saneamento de duplicatas (`backlog/proposta_saneamento_human_reviews_duplicadas.md`,
  352 linhas), reincorporado sem alteração de conteúdo técnico, ainda
  **PROPOSTA NÃO EXECUTADA**;
- **superado** (aplicar reverteria informação mais recente já em `main`):
  `executive_technical_dashboard.md`, `snapshots/latest_execution.md`, o
  documento de sprint `AV-S03` do PR #2 (versão de planejamento de 24/09,
  pré-implementação — a versão real e homologada já está em `main`), e o
  snapshot intermediário `EXEC-2026-09-24-08`.

**Recomendação registrada, não executada**: fechar o PR #2 sem merge, após
esta preservação. Nenhuma ação sobre o PR #2 foi tomada — decisão final
cabe a Rafael.

## 4. Estado do PR #4 após esta fatia

PR #4 segue em **rascunho**, HEAD atualizado com os 2 commits desta fatia
(`2aeec59` — AC-05; `3ca0b53` — reconciliação PR #2). CI a confirmar no HEAD
final. Nenhuma alteração no PR #3 (já mesclado) nem no PR #2 (permanece
aberto, sem decisão).

## 5. Estado final desta fatia

- `avalia_dev`: acessado apenas em leitura (1 `SELECT` read-only, sem
  nenhuma escrita), confirmado por comando executado e seu resultado
  registrado;
- nenhum deploy, nenhuma migração operacional aplicada, nenhuma promoção de
  baseline, nenhuma nova sprint;
- `AC-05`: fechado com evidência real desta rodada;
- reconciliação do PR #2: classificação completa apresentada, conteúdo
  necessário preservado em versão atualizada, nenhuma decisão de fechamento
  tomada;
- PR #4: atualizado, ainda em rascunho, aguardando decisão de merge;
- PR #2: sem alteração de estado, aguardando decisão de fechamento.

## 6. Próxima ação

Apresentar a Rafael: (1) resultado de AC-05; (2) classificação e
preservação do conteúdo do PR #2; (3) HEAD/checks do PR #4; (4) pedido de
decisão sobre merge do PR #4 e fechamento do PR #2.
