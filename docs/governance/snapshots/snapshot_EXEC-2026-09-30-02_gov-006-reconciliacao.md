---
id: "EXEC-2026-09-30-02"
tipo: execucao
sprint: "GOV-006"
gerado_em: "2026-09-30T15:30:00-03:00"
executor: "Hermes"
status: concluida_aguardando_homologacao
commit_referencia: "a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8"
---

# Snapshot EXEC-2026-09-30-02 — GOV-006 (2ª rodada): reconciliação do numerador nominal e causa comprovada das divergências entre checkouts

> Registro histórico. Substitui/complementa EXEC-2026-09-30-01 (1ª rodada da
> mesma auditoria, que continha erro aritmético no numerador). Não
> promover automaticamente a baseline. Correções posteriores usam adendo
> datado ou novo snapshot.

## 1. Abertura

- objetivo desta rodada: corrigir o numerador nominal (14/70, não 15/70),
  comparar os dois checkouts por conteúdo (não só por lista de paths) e
  determinar a causa comprovada das divergências, precisar a linguagem
  sobre AV-S04/AV-S05/AV-S05B (coleta manuscrita), documentar
  explicitamente o checkout/base de cada alteração, remover a coleta
  manuscrita como dependência geral do projeto, e entregar pacote durável
  revisável separando auditoria de investigação OCR;
- escopo autorizado: mesma auditoria documental (GOV-006), sem reabrir
  auditoria geral; sem trocar branch nem podar worktree; sem
  stage/commit/push/merge; sem alteração em `avalia_dev`; sem nova
  implementação;
- checkout e base usados em todas as edições desta rodada: worktree
  `avalia-plataform-worktrees/av-s03-work`, branch `main`, HEAD `a5974b1`
  (idêntico à rodada anterior). O checkout principal
  (`avalia-plataform`, branch `docs/av-s02-encerramento-planos-operacionais`,
  HEAD `7f18ec3`) foi **apenas lido** nesta rodada, para comparação de
  conteúdo — nenhuma edição foi aplicada nele;
- working tree inicial: idêntico ao estado deixado por EXEC-2026-09-30-01
  (primeira rodada desta mesma auditoria).

## 2. Entregas

| Item | Estado | Entrega | Evidência |
|---|---|---|---|
| GOV-006-04 (revisado) | implementado/validado | numerador nominal corrigido de 15/70 para 14/70, com lista de 14 IDs, homologação e observação; `BL-AV-1-10` movido para indicador de itens parciais | `executive_technical_dashboard.md`, seção "Trilha proposta" |
| GOV-006-03 (revisado) | implementado/validado | causa comprovada da divergência "7→9→14/15" entre os dois checkouts, com evidência de `git log`, `git show`, `diff` de conteúdo e `stat` de mtime | `sprint_GOV-006_auditoria_governanca.md` §6 |
| — | implementado/validado | linguagem sobre AV-S04/AV-S05 corrigida para "nenhuma evidência de execução localizada nas fontes inspecionadas" | dashboard, banner de topo e seção de progresso |
| — | implementado/validado | linguagem sobre AV-S05B corrigida: "entrega experimental e documental local, ainda não publicada"; coleta manuscrita descrita sem presumir início, após busca no filesystem por `MAN-*` (sem resultado) | dashboard, banner de topo; `sprint_GOV-006...` §5 |
| — | implementado | pacote durável revisável com inventário, separando auditoria de investigação OCR | `docs/governance/evidence/GOV-006/pacote_revisao_gov-006.md` |

## 3. Não entregas e lacunas

- Conteúdo mais detalhado (676 linhas) de `proposta_saneamento_human_reviews_duplicadas.md`,
  encontrado apenas no checkout principal (não commitado), não foi
  promovido nem descartado — decisão de Rafael;
- checkout principal não foi trocado para `main`; worktree prunable do
  Codex não foi podado — decisões de Rafael, não pré-requisitos desta
  auditoria;
- publicação (stage/commit) de qualquer um dos dois pacotes propostos não
  foi executada — aguarda autorização explícita.

## 4. Arquivos impactados (todos no worktree de trabalho, `main` `a5974b1`)

| Caminho | Natureza | Item |
|---|---|---|
| `docs/governance/executive_technical_dashboard.md` | alterado (numerador nominal 14/70, linguagem AV-S04/AV-S05/AV-S05B) | GOV-006-04 |
| `docs/governance/sprints/sprint_GOV-006_auditoria_governanca.md` | reescrito integralmente (2ª rodada) | GOV-006-05 |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-30-02_gov-006-reconciliacao.md` | criado (este arquivo) | GOV-006-05 |
| `docs/governance/evidence/GOV-006/pacote_revisao_gov-006.md` | criado | GOV-006-06 |
| `docs/governance/evidence/GOV-006/inventario_checksums_gov-006.txt` | criado | GOV-006-06 |
| `docs/governance/snapshots/latest_execution.md` | alterado (ponteiro atualizado) | GOV-006-05 |

## 5. Validações realizadas

| Data/fuso | Comando/procedimento | Ambiente | Tipo | Resultado |
|---|---|---|---|---|
| 2026-09-30 -03:00 | `diff` de conteúdo linha a linha entre checkout principal e worktree para `dashboard`, `decisions.md`, `backlog`, `proposta_saneamento` | ambos os checkouts | inspeção de conteúdo | divergências reais identificadas, não apenas contagem de linhas |
| 2026-09-30 -03:00 | `git show <commit>:<path>` para dashboard em `7f18ec3`, `8e4b1fa`, `c391865`, `main` | checkout principal | inspeção Git | confirma que a correção "7→9" nunca foi commitada em nenhum branch |
| 2026-09-30 -03:00 | `git log --all -- snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` | checkout principal | inspeção Git | vazio — arquivo nunca commitado em nenhum branch |
| 2026-09-30 -03:00 | `git log --all -S"Desvio de processo registrado"` e `git merge-base --is-ancestor` para `DEC-AV-022` | checkout principal | inspeção Git | confirma histórico não-linear entre os dois checkouts (commits em branches divergentes) |
| 2026-09-30 -03:00 | `find` por `MAN-01*`/`MAN-EVAL*` em todo `Projeto Estágio/` | filesystem | inspeção | nenhum resultado — nenhuma evidência de foto/coleta manuscrita iniciada |
| 2026-09-30 -03:00 | `stat -f "%Sm"` (mtime) do dashboard nos dois checkouts | ambos | inspeção | checkout principal: 2026-09-28 13:43; worktree: 2026-09-30 (esta sessão) |

## 6. Estado Git final

`git status --short` no worktree de trabalho continua com a mesma lista de
paths de topo desde o início desta auditoria, mais os 2 novos arquivos do
pacote durável. Isso não comprova conteúdo inalterado. Nada staged, nada
commitado, em nenhum dos dois checkouts.

Execução imediatamente anterior: [EXEC-2026-09-30-01 — GOV-006: auditoria de
governança (1ª rodada, numerador com erro aritmético, corrigido nesta
rodada)](snapshot_EXEC-2026-09-30-01_gov-006-auditoria.md).

## Adendo de publicação — 2026-09-30

Rafael aceitou a reconciliação GOV-006, o numerador `14/70` e a apresentação
separada dos itens parciais. Autorizou a publicação dos pacotes A e B em
branches dedicadas e PRs em rascunho, sem merge.

Este adendo não altera o estado histórico descrito acima: na execução original
desta rodada nada foi staged ou publicado. A publicação posterior usa uma
pilha real:

1. Pacote B/AV-S05B: `docs/av-s05b-investigacao`, base `main@a5974b1`, HEAD
   publicado `44a09b0`, PR rascunho #5;
2. Pacote A/GOV-006: `docs/gov-006-reconciliacao`, baseado em `44a09b0` e
   aberto contra a branch B para consolidar `dashboard`, `backlog` e
   `latest_execution` sem sobrescrita.

A proposta local de saneamento de 676 linhas foi preservada no checkout
principal. Somente sua comparação e delta contra a versão integrada integram o
Pacote A; ela não foi promovida a plano aprovado.

