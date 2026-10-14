---
id: "EXEC-2026-10-14-08"
tipo: execucao
sprint: "AV-S08B (transcrição manual e confirmação humana)"
gerado_em: "2026-10-14T10:55:00-03:00"
executor: "Claude Code (implementação), Hermes (verificação independente + validação visual), Antigravity (revisão independente)"
status: "aprovação técnica local — rodada LOCAL, sem git nesta fatia"
base: "main e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d"
branch: "feat/av-s08b-transcricao-manual"
---

# Snapshot EXEC-2026-10-14-08 — Encerramento local: transcrição manual e confirmação humana (AV-S08B)

> Continuação do snapshot de abertura EXEC-2026-10-14-07. Rodada LOCAL: sem
> stage/commit/push nesta fatia (ordem de Rafael). Não promove baseline.

## 1. Resumo

Implementada e validada LOCALMENTE a transcrição manual e confirmação humana de
respostas por imagem (`AV-S08B`, parte manual de `BL-AV-4B-10/11/13/14/15`):
2 endpoints de mutação (`PATCH .../manual-transcription/draft`,
`POST .../manual-transcription/confirm`), controle de concorrência real por
versão (lock otimista via UPDATE condicional em transação), tela de conferência
com revisão em 2 passos e aviso de irreversibilidade, bloqueio de correção
automática preservado e liberado só após confirmação. Claude Code implementou;
Hermes verificou de forma independente (testes + navegador real); Antigravity
revisou de forma independente a implementação.

## 2. Entrega

| Item | Estado | Evidência |
|---|---|---|
| Backend: 2 endpoints de mutação com concorrência real (`transcription_version`) | implementado e validado | ACD-01..17 (relatório Claude Code + reexecução independente) |
| Migração Alembic aditiva, downgrade bloqueado com dados não-default | implementado e validado | §3 abaixo |
| Frontend: revisão em 2 passos, aviso de irreversibilidade, estado pós-confirmação somente leitura | implementado e validado | navegador real, §4 abaixo |
| Bloqueio de correção preservado; liberação só após confirmação | validado | HTTP real, §4 abaixo |
| Auditoria (AuditEvent) de rascunho e confirmação | validado | testes + inspeção de código |

## 3. Validações executadas

| Tipo | Resultado |
|---|---|
| Suíte automatizada (SQLite) | **201 passed, 5 skipped** (171 pré-existentes + 30 novos; zero regressão); 5 skipped = testes de concorrência real sem `AVALIA_TEST_POSTGRES_URL` |
| Testes de concorrência real (PostgreSQL descartável próprio do Hermes, `av_s08b_hermes_test`) | **5 passed** — reexecutados de forma independente, banco dropado ao final |
| Lint backend (`ruff`) | All checks passed |
| Build/tsc/lint frontend | limpos (Claude Code e, de forma independente, Antigravity) |
| Revisão independente do Antigravity | **APROVADO COM RESSALVAS DOCUMENTAIS** (sem achado bloqueante); reexecutou migração, concorrência real e suíte completa em ambiente próprio dele |
| Validação visual em navegador real (Hermes) | **PASS** — ver §4 |

## 4. Validação visual em navegador real (Hermes, ambiente isolado descartável)

Ambiente: banco PostgreSQL descartável `av_s08b_visual_hermes_test` (migrado a
head `f2a9c4e6b1d3`, dropado ao final); Core em `127.0.0.1:8311`
(`ACADEMIC_MODULE_ENABLED=false`, `AI_ENGINE_URL=http://127.0.0.1:9988` morto —
sem OCR, sem IA real nem simulada); Vite em `127.0.0.1:5311`; Chrome real via
CDP em `127.0.0.1:9337`. Seed: prof1 (dono) + prof2 (não-dono); Avaliação com
1 resposta por imagem já persistida.

| Cenário | Resultado |
|---|---|
| Rascunho: digitar e salvar | **PASS** — confirmação visual "Rascunho salvo" |
| Recuperação do rascunho após reload completo (ACD-01B) | **PASS** — texto digitado reaparece integralmente após F5 |
| Bloqueio para outro professor (403) | **PASS** — verificado via chamada autenticada direta com token de prof2 |
| Revisão em 2 passos antes de confirmar (DP-2) | **PASS** — painel "Revisão final antes de confirmar" com aviso explícito de irreversibilidade, imagem carregada automaticamente via download autenticado (blob, `naturalWidth` real) e texto lado a lado |
| Confirmação definitiva | **PASS** — estado muda para "TRANSCRIÇÃO CONFIRMADA", mostra quem confirmou e quando, textarea desaparece, texto em modo somente leitura |
| Persistência do estado confirmado após reload | **PASS** |
| Liberação de correção após confirmação (ACD-09) | **PASS** — `POST /v1/answers/{id}/corrections` retornou `202 Accepted` (job criado; falhou depois por `AI_ENGINE_URL` morto de propósito — **nenhum AI Engine real nem simulado foi exercitado nesta validação**, log do servidor confirma `correction_job_failed_engine_unavailable`) |

Nota de processo: a primeira tentativa de seed do Hermes usou o nome de
variável de ambiente errado (`ANSWER_IMAGE_STORAGE_DIR`, sem o `S` de
`IMAGES`), causando um 404 passageiro de "arquivo indisponível" no download —
**erro do ambiente de verificação do Hermes, não do código entregue**;
corrigido e revalidado com sucesso (download 200, imagem carregada). Registrado
aqui por transparência de processo.

## 5. Integridade

- Bancos protegidos **intactos** antes e depois de toda a rodada (implementação,
  revisão do Antigravity, validação visual do Hermes): `avalia_dev`
  (`a9f4c2e71b06`, 16 `human_reviews`) e `avalia_apresentacao_demo_20261002`
  (`a9f4c2e71b06`).
- Todos os bancos descartáveis desta rodada (`av_s08b_hermes_test`,
  `av_s08b_antigravity_test`, `av_s08b_visual_hermes_test`,
  `av_s08b_migration_test`, `av_s08b_concorrencia_test`) foram dropados.
  Nenhum resíduo (`psql -lqt` confirmado limpo).
- Ambiente de validação visual (Core, Vite, Chrome, storage temporário)
  encerrado e removido; portas 8311/5311/9337 livres.

## 6. Diff local (sem stage/commit/push)

7 arquivos alterados + 2 novos (fora dos arquivos de governança já presentes
desde a abertura):
- `core/app/main.py` (+179): 2 endpoints novos.
- `core/app/models.py` (+12): 4 colunas novas em `Answer`.
- `core/app/schemas.py` (+11): `AnswerOut` +4 campos (ver Ajustes de Percurso,
  D-1), `ManualTranscriptionInput`.
- `core/alembic/versions/f2a9c4e6b1d3_add_answer_manual_transcription.py`
  (novo): migração aditiva com downgrade bloqueado por dados não-default.
- `core/app/tests/test_manual_transcription.py` (novo): 30 testes SQLite + 5
  testes de concorrência real em PostgreSQL.
- `frontend/src/types.ts` (+11): campos novos + `ApiErrorBody.details`.
- `frontend/src/services/api.ts` (+16): 2 funções novas; `send()` repassa
  `details` do erro (ver Ajustes de Percurso, D-2).
- `frontend/src/pages/ImageAnswerPage.tsx` (+209): componente
  `ManualTranscription`, revisão em 2 passos.

## 7. Ajustes de percurso (ver também §14 da sprint)

- **D-1**: `AnswerOut` ganhou 2 campos além dos previstos no plano
  (`transcription_confirmed_by_id`, `transcription_confirmed_at`) — aditivo,
  necessário para exibir "quem confirmou e quando" na UI. Avaliado como
  aceitável pelo Antigravity (ACH-01 do parecer de implementação). Registrado
  formalmente, não requer nova decisão de produto (é exposição de dado já
  existente no modelo, não mudança de contrato/comportamento).
- **D-2**: `api.ts` `send()` passou a repassar `details` do corpo de erro —
  aditivo, necessário para o frontend ler `details.current_answer` do 409.
  Avaliado como aceitável pelo Antigravity (ACH-02).
- **ACD-13 e a parte "navegador real" de ACD-01B**: não validados pelo Claude
  Code nem pelo Antigravity (ambos limitaram-se a `tsc`/build/lint). **Validados
  nesta rodada pelo Hermes** em navegador real (§4 acima) — pendência P-1 do
  relatório do Claude Code está, portanto, resolvida.

## 8. Pendências remanescentes (fora desta rodada)

- Botão de disparo de IA na tela de resposta por imagem após confirmação:
  **resolvido na rodada seguinte** — ver
  `snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md` §2 (implementado
  dentro do escopo já autorizado, sem necessidade de nova decisão de
  produto).
- CI atual não roda os 5 testes de concorrência real (ficam `skipped` sem
  `AVALIA_TEST_POSTGRES_URL`); candidato a melhoria de infraestrutura de CI
  (service container PostgreSQL), não bloqueante para esta entrega.
- `AV-S08B` segue **não resolvido em `main`** — sem commit/push nesta fatia
  (ordem de Rafael); fechamento formal cabe a Rafael após
  publicação/homologação. (`DEBT-AV-014`, por sua vez, já está integrado em
  `main` desde antes desta sprint — ver reconciliação em
  `technical_debts.md` e em `snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md`
  §4.1.)

## 9. Estado final

- Rodada LOCAL: branch `feat/av-s08b-transcricao-manual` (base `e8b0864`);
  working tree não-staged; nenhuma ação remota.
- Progresso homologado permanece **19/70**; AV-S05B parcial; BL-AV-4B-05
  pendente; `BL-AV-4B-10`/`11` permanecem **parciais** (falta a parte de OCR).
- Bancos protegidos intactos.
- Pacote recuperável: todo o código e evidências estão no working tree da
  branch; relatórios em `docs/governance/evidence/AV-S08B/` e
  `local-nao-versionado/claude_report_av_s08b.md` (git-ignored).
