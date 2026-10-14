---
id: "EXEC-2026-10-14-10"
tipo: execucao
sprint: "AV-S08B (transcrição manual e confirmação humana) — publicação"
gerado_em: "2026-10-14T11:35:00-03:00"
executor: "Hermes (stage seletivo, organização de commits, push, PR, acompanhamento de CI)"
status: "publicado em PR rascunho, sem merge"
base: "main e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d"
branch: "feat/av-s08b-transcricao-manual"
---

# Snapshot EXEC-2026-10-14-10 — Publicação da fatia MANUAL de AV-S08B (PR rascunho, sem merge)

> Continuação dos snapshots EXEC-2026-10-14-07/08/09. Rafael autorizou
> preparar e publicar a fatia manual em PR rascunho, sem merge, condicionado
> a: correção de uma imprecisão de evidência (identidade de texto por
> comprimento), conferência final do diff, stage seletivo com exclusão de
> conteúdo sensível, organização de commits, push, acompanhamento de CI, e
> descrição do PR restrita ao escopo MANUAL.

## 1. Correção de evidência (antes da publicação)

A seção 3.3 do snapshot `EXEC-2026-10-14-09` afirmava que a igualdade entre
`answer_text_len` (log) e `char_length(text)` (banco) comprovava identidade
de conteúdo — isso está incorreto: dois textos diferentes podem ter o mesmo
comprimento. Corrigido em ambos os documentos
(`snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md` §3.3 e
`latest_execution.md`): a prova de identidade de **conteúdo integral** é o
teste automatizado
`test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`
(`core/app/tests/test_manual_transcription.py:501-522`), que intercepta o
`httpx.AsyncClient` do worker e compara o payload inteiro
(`assert [p["answer_text"] for p in ai_engine.payloads] == [confirmed_text]`)
contra um texto propositalmente diferente do rascunho anterior. Reexecutado
isoladamente nesta rodada: **1 passed**. A coincidência de comprimento da
validação manual em navegador real permanece registrada como observação
consistente, não como prova.

## 2. Conferência final (antes do stage)

- `git diff --stat` e leitura completa de cada arquivo modificado
  (`core/app/main.py`, `models.py`, `schemas.py`, migração,
  `ImageAnswerPage.tsx`, `api.ts`, `types.ts`) confirmando: nenhuma chamada a
  `request_correction`/criação de `CorrectionJob` nos endpoints de
  rascunho/confirmação; `AuditEvent` com autoria (`actor_id`) e before/after
  em cada mutação; lock otimista por `UPDATE ... WHERE transcription_version
  = :expected_version` dentro de transação (não lock em memória); migração
  puramente aditiva com downgrade bloqueado por dados não-default;
  `AnswerPage.tsx` (fluxo textual) não tocado; `AIExecutionResult.engine_mode`
  distingue `'real' | 'simulated'` desde o tipo TypeScript.
- Suíte completa reexecutada uma última vez antes do stage: **204 passed, 5
  skipped** (os 5 skipped são os testes de concorrência real, que exigem
  `AVALIA_TEST_POSTGRES_URL` — comportamento inalterado e esperado,
  reafirmado aqui a pedido de Rafael: executados localmente pelo autor desta
  rodada e pelos 2 revisores independentes anteriores; **a CI atual deste
  repositório não define essa variável e os pula**; nenhuma infraestrutura
  de CI foi alterada nesta rodada). `ruff check`, `npx tsc -b`, `npm run
  build`, `npm run lint`: todos limpos.
- Nenhum item de DoD da sprint reivindica publicação/homologação/integração
  da própria `AV-S08B` como concluída — confirmado por leitura de
  `sprint_AV-S08B_transcricao_manual_confirmacao_humana.md` §9; nenhuma
  edição necessária ali.
- Verificação de conteúdo sensível antes do stage: busca por padrões de
  credenciais/segredos nos arquivos candidatos — único resultado foi a senha
  fictícia de fixture de teste (`"Senha123!"`, mesmo padrão já usado em todo
  o repositório para dados de teste, não uma credencial real). `.env`,
  `core/var/` (storage de imagens) e `local-nao-versionado/` (relatórios dos
  executores) já cobertos por `.gitignore` — confirmado que nenhum desses
  apareceu em `git status --short`.

## 3. Stage seletivo e organização de commits

4 commits, cada um com escopo único, criados nesta branch:

| Commit | SHA | Escopo |
|---|---|---|
| `feat(core)` | `b1ce7bd` | Migração `f2a9c4e6b1d3` + modelo + schema + 2 endpoints de mutação |
| `test(core)` | `62cb6c2` | `test_manual_transcription.py` (33 testes, ACD-01..17 + delta de correção) |
| `feat(frontend)` | `3deef2b` | `ImageAnswerPage.tsx` + `api.ts` + `types.ts` (UI de transcrição + botão de correção) |
| `docs(governance)` | `92edce4` | Sprint, plano técnico, decisões, pareceres de revisão, snapshots EXEC-07/08/09 |

Cada stage foi conferido por `git diff --cached --stat` antes do commit
correspondente. Nenhum arquivo fora do escopo pretendido entrou em nenhum
commit (confirmado por `git status --short` após cada stage).

## 4. Publicação

- Push: `git push -u origin feat/av-s08b-transcricao-manual` — confirmado de
  forma **independente** por `git fetch origin feat/av-s08b-transcricao-manual`
  seguido de `git rev-parse origin/feat/av-s08b-transcricao-manual`: SHA
  remoto `92edce4013ba5688be4e4ff99fdf249a677636f3`, idêntico ao SHA local
  (não confiando apenas na saída do próprio comando de push).
- PR rascunho aberto contra `main`:
  **https://github.com/rafaelinfopiaui/avalia-platform/pull/18**
  (`gh pr create --draft`). Confirmado via `gh pr view --json` (consulta
  independente à API, não apenas a saída da criação): `isDraft: true`,
  `state: OPEN`, `baseRefName: main`, `headRefOid:
  92edce4013ba5688be4e4ff99fdf249a677636f3`, `mergeable: MERGEABLE`,
  `mergeStateStatus: CLEAN`.
- Checks de CI no SHA publicado, confirmados via
  `gh api repos/.../commits/{sha}/check-runs` (consulta direta à API, não
  apenas `gh pr checks`):

  | Check | Status | Conclusão |
  |---|---|---|
  | Core API (FastAPI + Postgres) | completed | success |
  | AI Engine (FastAPI) | completed | success |
  | Frontend (Vite + React + TS) | completed | success |

  **3/3 checks pass**, run `38581948805`. Nenhuma falha a corrigir —
  nenhuma revalidação adicional foi necessária.
- Nenhum merge realizado. Nenhum worktree novo criado. Nenhuma alteração em
  `avalia_dev`/apresentação. Nenhuma migração operacional, P5, seed
  operacional, OCR, deploy ou baseline.

## 5. Estado final do checkout

- Branch: `feat/av-s08b-transcricao-manual`.
- `git status --short`: limpo (working tree sem alterações pendentes após
  os 4 commits).
- HEAD local e remoto idênticos: `92edce4013ba5688be4e4ff99fdf249a677636f3`.
- `avalia_dev` e `avalia_apresentacao_demo_20261002`: não tocados nesta
  rodada de publicação (nenhuma conexão feita); seguem no mesmo estado
  confirmado em `EXEC-2026-10-14-09` (`a9f4c2e71b06`, 16 `human_reviews`).

## 6. Escopo descrito no PR (apenas MANUAL)

A descrição do PR #18 declara explicitamente: fatia **MANUAL** da AV-S08B,
sem OCR; cobre integralmente `BL-AV-4B-13`/`14`, cobre **parcialmente**
`BL-AV-4B-10`/`11`/`15` (a parte de OCR não está incluída); distingue testes
com AI Engine simulado de inferência real; registra que os 5 testes de
concorrência real em PostgreSQL são executados localmente, não pela CI
atual; declara estado "rascunho, sem merge", e reafirma: progresso
homologado permanece **19/70**; `AV-S05B` parcial; `BL-AV-4B-05` pendente.
Homologação e decisão de merge permanecem com Rafael — não antecipadas por
este snapshot nem pela descrição do PR.

## 7. Ressalvas reais (sem omissão)

- Os 5 testes de concorrência real seguem fora da CI (infraestrutura não
  alterada nesta rodada, por instrução explícita).
- O rótulo "Solicitar nova análise da IA" no frontend é estado local de
  sessão (não persiste a um reload) — já documentado e aceito pelo
  Antigravity como limitação informativa, não bloqueante (ACH-01 do parecer
  do delta).
- `BL-AV-4B-10`/`11`/`15` permanecem parciais no backlog — esta publicação
  não os encerra.
- Nenhuma homologação, integração ou ativação operacional ocorreu nesta
  rodada — PR permanece rascunho, decisão de Rafael.
