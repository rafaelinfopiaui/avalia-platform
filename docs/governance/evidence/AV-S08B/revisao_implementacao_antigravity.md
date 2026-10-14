# Parecer de Revisão Independente da Implementação — AV-S08B

- **Revisor:** Antigravity (revisor independente)
- **Implementador:** Claude Code (CLI `claude`, modelo Opus 5.5)
- **Data/Fuso:** 2026-10-14T10:42:00-03:00
- **Branch:** `feat/av-s08b-transcricao-manual` (base `main` `e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d`)
- **Documento analisado:** Implementação de código, testes, migração e relatório `local-nao-versionado/claude_report_av_s08b.md` frente a `docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md` (aprovado via `DEC-AV-040`) e `docs/governance/sprints/sprint_AV-S08B_transcricao_manual_confirmacao_humana.md`.

---

## 1. Veredito

**APROVADO COM RESSALVAS DOCUMENTAIS**

A implementação técnica cumpre integralmente todos os requisitos funcionais, contratuais, de segurança, autorização e concorrência estabelecidos no plano técnico aprovado por Rafael (`DEC-AV-040`).

Nenhum defeito bloqueante de código, dados ou concorrência foi encontrado. Todos os testes de concorrência real foram re-executados contra PostgreSQL descartável próprio e confirmados aprovados. As ressalvas registradas são puramente documentais/governativas (desvios aditivos D-1 e D-2 motivados por requisitos de UX e tratamento de erro, a registrar formalmente em Ajustes de Percurso).

---

## 2. Quadro Resumo de Verificação dos Requisitos Contratuais

| Item de Verificação | Situação | Evidência Direta Observada |
|---|---|---|
| **1. Migração Alembic** (`f2a9c4e6b1d3`) | **Conforme** | Executado upgrade, downgrade com dados (bloqueado com `RuntimeError`), downgrade limpo e re-upgrade em banco descartável próprio `av_s08b_antigravity_test`. `alembic check` limpo sem drift. |
| **2. Endpoints e Tratamento de Erros** | **Conforme** | Endpoints `PATCH .../draft` e `POST .../confirm` implementados com ordem fail-fast estrita, autorização por `require_assessment_mutation`, e todos os códigos de erro do plano (404, 403, 401, 422 `ANSWER_NOT_IMAGE_SOURCE`, 422 `ANSWER_TEXT_REQUIRED`, 409 `TRANSCRIPTION_ALREADY_CONFIRMED`, 409 `TRANSCRIPTION_VERSION_CONFLICT`). |
| **3. Mecanismo de Concorrência** | **Conforme** | `UPDATE answers SET ... WHERE id = :id AND transcription_version = :expected_version AND transcription_status = 'AGUARDANDO_TRANSCRICAO'` diretamente no banco em transação atômica. Sem locks em memória. |
| **4. Testes de Concorrência Real (Postgres)** | **Conforme** | 5 testes `pg_concurrent` re-executados contra Postgres descartável próprio com threads simultâneas e barreira sincronizada no cursor. **5 passed**. |
| **5. Bloqueio de Correção Automática (ACD-08)** | **Conforme** | Inspeção direta de código em `core/app/main.py:750-930` e teste AST comprovam zero invocações a `request_correction`, `CorrectionJob` ou `run_correction_job`. |
| **6. AuditEvent** | **Conforme** | Eventos `manual_transcription_draft_saved` e `manual_transcription_confirmed` (`resource_type="Answer"`) gravados na mesma transação atômica do UPDATE com before/after fiéis. |
| **7. Não-Regressão Backend** | **Conforme** | Suíte completa em SQLite: **201 passed, 5 skipped** (171 anteriores + 30 novos). Linter `ruff` 100% limpo. |
| **8. Frontend (UX, Revisão em 2 Passos)** | **Conforme** | JSX em `ImageAnswerPage.tsx:149-297` implementa conferência lado a lado, aviso explícito de irreversibilidade (`CONFIRMATION_WARNING`), confirmação em 2 passos, botão para recarregar versão em 409 e estado imutável pós-confirmação. `tsc -b`, `npm run build` e `npm run lint` 100% limpos. |
| **9. Desvios Reportados (D-1, D-2)** | **Ressalvas Documentais** | Avaliados como aditivos, coerentes e necessários (ver ACH-01 e ACH-02). |
| **10. Pendências Reportadas (P-1 a P-4)** | **Verificadas** | P-1 a P-4 são reais e de escopo procedimental/infraestrutura, sem impacto bloqueante no código. |

---

## 3. Achados de Revisão

### ACH-01: Desvio D-1 — Adição de campos de autoria e data da confirmação ao schema `AnswerOut`
- **Severidade:** Baixa (Ressalva documental)
- **Bloqueante:** Não
- **Localização:** [`core/app/schemas.py:164-165`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L164-L165)
- **Descrição:** O plano técnico §3.1 previa a inclusão em `AnswerOut` apenas de `manual_transcription_draft: Optional[str] = None` e `transcription_version: int = 0`. O implementador incluiu adicionalmente `transcription_confirmed_by_id: Optional[str] = None` e `transcription_confirmed_at: Optional[datetime] = None`.
- **Avaliação:** O desvio é estritamente aditivo, retrocompatível e necessário para cumprir o requisito de UX de exibir "quem confirmou e quando" na tela de conferência após a confirmação. O campo expõe o ID do usuário (não dados sensíveis como e-mail) e está restrito àqueles autorizados a consultar a avaliação.
- **Ação necessária:** O consolidador (Hermes) deve registrar a alteração formalmente na seção 14 ("Ajustes de Percurso") da sprint `sprint_AV-S08B_transcricao_manual_confirmacao_humana.md`.

---

### ACH-02: Desvio D-2 — Repasse do campo `details` do corpo de erro em `api.ts`
- **Severidade:** Baixa (Ressalva documental)
- **Bloqueante:** Não
- **Localização:** [`frontend/src/services/api.ts:90-92`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/services/api.ts#L90-L92)
- **Descrição:** A função utilitária `send()` do cliente HTTP do frontend passou a extrair `details` do corpo JSON de erro da API e repassá-lo ao `ApiError`.
- **Avaliação:** O contrato de 409 estipulado no plano §3.3 e §6 determina que o backend devolva o estado atual do recurso (`details.current_answer`) para permitir ao cliente decidir e oferecer recuperação de versão. Sem essa alteração no utilitário de transporte, o frontend não receberia o estado atualizado. A alteração é aditiva e não altera o comportamento de nenhum consumidor pré-existente.
- **Ação necessária:** Registrar formalmente na seção 14 da sprint.

---

### ACH-03: Não inclusão de botão de disparo de IA na tela `ImageAnswerPage.tsx`
- **Severidade:** Informativa (Alinhamento de escopo)
- **Bloqueante:** Não
- **Localização:** [`frontend/src/pages/ImageAnswerPage.tsx:163-174`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L163-L174)
- **Descrição:** O plano técnico §9 mencionava a possibilidade de reaproveitar o botão "Solicitar análise da IA" na tela da resposta por imagem após a confirmação. O implementador optou por não incluí-lo, mantendo a tela estritamente restrita à transcrição manual e confirmação.
- **Avaliação:** Decisão tecnicamente correta e prudente. O prompt fornecido a Claude Code não solicitou ação de correção na interface desta tela, e a fatia homologada anterior (DEBT-AV-014) foi expressamente aprovada "sem ação de correção na tela". O backend comprova via teste automatizado (`test_correction_blocked_before_and_allowed_after_confirmation`) que a confirmação libera o guard `ANSWER_NOT_TRANSCRIBED` para chamadas subsequentes à API de correção. O disparo de IA via UI para respostas de imagem pode ser introduzido em fatia futura dedicada se Rafael assim desejar.

---

### ACH-04: Testes de concorrência real `pg_concurrent` dependem de banco PostgreSQL
- **Severidade:** Informativa (Infraestrutura)
- **Bloqueante:** Não
- **Localização:** [`core/app/tests/test_manual_transcription.py:618-620`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L618-L620)
- **Descrição:** Os 5 testes de concorrência real utilizam a fixture `@requires_postgres`, condicionada à variável de ambiente `AVALIA_TEST_POSTGRES_URL`. Na execução padrão de CI com SQLite, esses 5 testes são ignorados (`skipped`).
- **Avaliação:** O revisor independente re-executou os 5 testes contra uma base PostgreSQL descartável dedicada e confirmou aprovação integral (`5 passed in 2.32s`). Como SQLite serializa escritas por arquivo em nível de processo, a exigência de PostgreSQL para testar row locks concorrentes reais é tecnicamente fundamentada.
- **Recomendação:** Avaliar em rodada de infraestrutura a configuração de um service container de PostgreSQL no GitHub Actions para que a suíte em CI execute também esses 5 testes automaticamente.

---

## 4. Evidências de Execução Realizadas pelo Revisor Independente

### 4.1 Migração Alembic em PostgreSQL descartável
Comando de criação da base de teste:
```bash
createdb av_s08b_antigravity_test
```

Execução de upgrade até a revisão imediatamente anterior (`e7c3f1a8b2d4`):
```text
INFO  [alembic.runtime.migration] Running upgrade e1b02279b1a5 -> 7b1d6d853f20, add unique human review job id
INFO  [alembic.runtime.migration] Running upgrade 7b1d6d853f20 -> c4a8b2d91e37, add academic structure
INFO  [alembic.runtime.migration] Running upgrade c4a8b2d91e37 -> a9f4c2e71b06, add question position and assessment clone provenance
INFO  [alembic.runtime.migration] Running upgrade a9f4c2e71b06 -> d5e3a7c19f42, add answer images (AV-S06B)
INFO  [alembic.runtime.migration] Running upgrade d5e3a7c19f42 -> e7c3f1a8b2d4, add answer source and transcription status
```

Seed de dados de teste (respostas TEXT e IMAGE pré-existentes):
```sql
INSERT INTO answers (id, question_id, student_name_fake, text, source, transcription_status, created_at)
VALUES ('ans1', 'q1', 'Aluno 1', 'Texto digitado', 'TEXT', 'TRANSCRICAO_CONFIRMADA', now());
INSERT INTO answers (id, question_id, student_name_fake, text, source, transcription_status, created_at)
VALUES ('ans2', 'q1', 'Aluno 2', NULL, 'IMAGE', 'AGUARDANDO_TRANSCRICAO', now());
```

Upgrade para a nova revisão:
```bash
DATABASE_URL=postgresql+psycopg2://localhost:5432/av_s08b_antigravity_test core/.venv/bin/alembic -c core/alembic.ini upgrade head
```
Saída:
```text
INFO  [alembic.runtime.migration] Running upgrade e7c3f1a8b2d4 -> f2a9c4e6b1d3, add answer manual transcription fields (AV-S08B)
```

Verificação de proteção de downgrade com dados:
```sql
UPDATE answers SET manual_transcription_draft = 'Rascunho de teste' WHERE id = 'ans2';
```
Tentativa de downgrade:
```bash
DATABASE_URL=postgresql+psycopg2://localhost:5432/av_s08b_antigravity_test core/.venv/bin/alembic -c core/alembic.ini downgrade e7c3f1a8b2d4
```
Saída:
```text
RuntimeError: Downgrade f2a9c4e6b1d3 bloqueado antes de qualquer DROP: existem respostas com rascunho de transcrição, confirmação registrada ou versão de transcrição avançada. Remover as colunas descartaria esse estado. Preserve/exporte esses dados por um procedimento separado e autorizado antes de tentar novamente.
```
Estado do banco após a recusa:
```text
f2a9c4e6b1d3 (head) - colunas e FK perfeitamente preservadas.
```

Downgrade limpo após remoção de dados não-default e re-upgrade:
```bash
UPDATE answers SET manual_transcription_draft = NULL WHERE id = 'ans2';
alembic downgrade e7c3f1a8b2d4  # OK, colunas removidas
alembic upgrade head            # OK, colunas recriadas
alembic check                   # "No new upgrade operations detected."
```

---

### 4.2 Testes de Concorrência Real no PostgreSQL
Executado contra a base `av_s08b_antigravity_test`:
```bash
AVALIA_TEST_POSTGRES_URL=postgresql+psycopg2://localhost:5432/av_s08b_antigravity_test \
  core/.venv/bin/pytest core/app/tests/test_manual_transcription.py -k pg -v
```
Saída:
```text
core/app/tests/test_manual_transcription.py::test_pg_concurrent_drafts_only_one_commits[2] PASSED [ 20%]
core/app/tests/test_manual_transcription.py::test_pg_concurrent_drafts_only_one_commits[8] PASSED [ 40%]
core/app/tests/test_manual_transcription.py::test_pg_concurrent_confirms_exactly_one_wins[2] PASSED [ 60%]
core/app/tests/test_manual_transcription.py::test_pg_concurrent_confirms_exactly_one_wins[8] PASSED [ 80%]
core/app/tests/test_manual_transcription.py::test_pg_concurrent_confirm_and_draft_never_reopen PASSED [100%]

================ 5 passed, 30 deselected, 14 warnings in 2.32s =================
```
Limpeza imediata do banco descartável:
```bash
dropdb av_s08b_antigravity_test
```
Conferência via `psql -l`: base descartável removida; bases protegidas (`avalia_dev`, `avalia_apresentacao_demo_20261002`, `postgres`) intocadas.

---

### 4.3 Suíte Completa de Testes Automatizados (SQLite)
```bash
env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET core/.venv/bin/pytest core/app/tests -q
```
Saída:
```text
201 passed, 5 skipped, 14 warnings in 81.56s (0:01:21)
```
- 171 testes pré-existentes: **100% preservados** (regressão zero).
- 30 novos testes de transcrição manual e confirmação: **100% aprovados**.
- 5 testes `pg_concurrent` pulados por falta de env var (comportamento esperado em modo SQLite).

---

### 4.4 Verificação de Qualidade e Linters

**Backend (`ruff`):**
```bash
core/.venv/bin/ruff check core/app core/alembic/versions/f2a9c4e6b1d3_add_answer_manual_transcription.py
```
Saída: `All checks passed!`

**Frontend (`tsc`, `build`, `eslint`):**
```bash
cd frontend && npx tsc -b && npm run build && npm run lint
```
Saída:
```text
vite v8.2.2 building client environment for production...
✓ 35 modules transformed.
dist/index.html                   0.54 kB │ gzip:  0.34 kB
dist/assets/index-DhxhAQRq.css    8.82 kB │ gzip:  2.89 kB
dist/assets/index-ZQu5NAot.js   282.29 kB │ gzip: 85.13 kB
✓ built in 46ms
> eslint src  # limpo, zero erros
```

---

## 5. Conclusão

A entrega de AV-S08B por Claude Code é tecnicamente sólida, robusta em concorrência, respeita estritamente o isolamento de transações, segue a convenção arquitetural do repositório e cumpre os critérios canônicos de segurança e não-regressão.

O revisor recomenda a homologação da implementação por Rafael, observando-se o registro formal dos desvios aditivos ACH-01 e ACH-02 em governança antes do encerramento final da sprint.
