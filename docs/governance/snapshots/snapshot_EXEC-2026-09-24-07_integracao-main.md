---
id: EXEC-2026-09-24-07
tipo: execucao
sprint: AV-S02
gerado_em: "2026-09-24T09:45:00-03:00"
executor: "Hermes"
status: integrada_a_main
commit_referencia: 7f2e0032ac7971ae43db5cc2386da0de321b778f
---

# Snapshot EXEC-2026-09-24-07 — integração do PR #1 a `main`

> Registro histórico. Não promove baseline, não autoriza tag/deploy/migração operacional.

## 1. Abertura

- objetivo: executar a integração autorizada por Rafael — retirar o PR #1 de rascunho, fazer
  merge por merge commit (preservando os 6 commits), acompanhar a CI disparada em `main` e
  registrar SHA/URL/resultados;
- escopo: `gh pr ready`, `gh pr merge --merge`, verificação do run em `main`, sincronização local;
- fora de escopo: tag, deploy, aplicação de migração em `avalia_dev`, saneamento de duplicatas,
  promoção de baseline, início de outra sprint;
- Git: `main`, antes em `0be691e12e9d5d6f3ffc989237739f6559d8dacd`, depois em
  `7f2e0032ac7971ae43db5cc2386da0de321b778f`;
- baseline: nenhum promovido.

## 2. Entregas

| Item | Estado | Entrega |
|---|---|---|
| PR retirado de rascunho | concluído | `gh pr ready 1` — `isDraft: false` confirmado |
| Merge | concluído | `gh pr merge 1 --merge` — merge commit, não squash |
| SHA do merge commit | `7f2e0032ac7971ae43db5cc2386da0de321b778f` | confirmado via `gh pr view --json mergeCommit` e `git log` |
| 6 commits preservados | confirmado | `dabd13a`, `5bfbac0`, `9b84c23`, `36de551`, `47d57f5`, `9e4b1d0` — todos presentes no histórico de `main` (`git log --graph`) |
| CI em `main` | executada, sucesso | run [36000432576](https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/36000432576), disparada por `push`, `headSha` idêntico ao merge commit |
| Resultado dos 3 jobs | 3/3 verdes | `Core API` ✅, `AI Engine` ✅, `Frontend` ✅ |
| `main` local sincronizado | concluído | `git pull` fast-forward, 114 arquivos, 28.526 inserções |
| Estado do `avalia_dev` reafirmado | confirmado | 8 linhas em `human_reviews`, sem `UniqueConstraint` — migração operacional NÃO aplicada |

## 3. Arquivos impactados nesta fatia

- `docs/governance/sprints/sprint_AV-S02_ci_visual_isolamento_testes.md` (§19.7 nova);
- `docs/governance/executive_technical_dashboard.md` (marco 8, referências, próxima sprint proposta);
- `docs/governance/snapshots/` (este snapshot).

Nenhum arquivo de código foi alterado nesta fatia — apenas a integração via merge dos commits já
validados e a documentação do resultado.

## 4. Validações reais

| Data/fuso | Comando/procedimento | Tipo | Resultado real |
|---|---|---|---|
| 2026-09-24 ~09:36 -03 | `gh pr ready 1` | automatizada/GitHub | `isDraft: false` |
| 2026-09-24 ~09:37 -03 | `gh pr merge 1 --merge --subject "..."` | automatizada/GitHub | `state: MERGED`, `mergeCommit.oid: 7f2e0032...` |
| 2026-09-24 ~09:38 -03 | `git fetch origin main` + `git log --oneline --graph origin/main -10` | verificação de integridade | merge commit no topo, 6 commits preservados como pais, sem squash |
| 2026-09-24 ~09:39 -03 | `gh run list --branch main --json databaseId,headSha,conclusion,status,event` | verificação de CI | run `36000432576`, evento `push`, `headSha` = SHA do merge commit |
| 2026-09-24 ~09:41 -03 | `gh run watch 36000432576 --exit-status` | integração real remota | `conclusion: success`, 3/3 jobs verdes |
| 2026-09-24 ~09:43 -03 | `git checkout main && git pull origin main` | sincronização local | fast-forward `0be691e..7f2e003`, sem conflito |
| 2026-09-24 ~09:44 -03 | `SELECT COUNT(*) FROM human_reviews` + `\d human_reviews` em `avalia_dev` | verificação de integridade | 8 linhas; nenhuma `UniqueConstraint` — confirma que a migração operacional continua não aplicada, mesmo após a integração do código a `main` |

## 5. Limites e estado final

- integração: concluída, PR #1 `MERGED`, `main` em `7f2e0032ac7971ae43db5cc2386da0de321b778f`;
- CI remota em `main`: 3/3 jobs verdes, sem necessidade de correção;
- `avalia_dev`: **não migrado** — o código integrado exige a migração `7b1d6d853f20` para garantir
  unicidade real no banco, mas o ambiente operacional continua com as 3 duplicatas fictícias
  preservadas e sem `UniqueConstraint`;
- saneamento de duplicatas: continua não autorizado, não executado;
- tag, deploy, promoção de baseline: nenhum executado;
- próxima ação: Rafael decidir sobre a próxima sprint elegível (proposta apresentada separadamente,
  não iniciada) e/ou sobre a aplicação da migração operacional e saneamento de duplicatas, quando
  desejar priorizá-los;
- status: `AV-S02` homologada e integrada a `main`; nenhuma outra sprint iniciada.
