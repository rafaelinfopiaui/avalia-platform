---
id: EXEC-2026-09-24-02
tipo: execucao
sprint: AV-S02
gerado_em: "2026-09-24T06:29:09-03:00"
executor: "Codex"
status: implementada_validada_localmente
commit_referencia: 0be691e12e9d5d6f3ffc989237739f6559d8dacd
---

# Snapshot EXEC-2026-09-24-02 — correções da revisão independente de BL-AV-1-10

> Registro histórico. Não promove baseline nem homologa o resultado.

## 1. Abertura

- objetivo: corrigir os três achados da revisão independente de Claude Code sobre idempotência de revisão humana;
- escopo: migração `7b1d6d853f20`, equivalência de justificativa, contrato do conflito 409, testes do Core e registros obrigatórios;
- fora de escopo: frontend, AI Engine, workflow CI, banco operacional `avalia_dev`, commit, push, tag e deploy;
- Git: `main`, HEAD/upstream `0be691e12e9d5d6f3ffc989237739f6559d8dacd`; working tree inicialmente suja com mudanças preexistentes de AV-S01/AV-S02, preservadas;
- baseline: nenhum promovido.

## 2. Entregas

| Item | Estado | Entrega |
|---|---|---|
| BL-AV-1-10 / achado 1 | validado localmente | deduplicação no `upgrade()` preserva a linha de menor `created_at`, com desempate por `id`, antes da constraint |
| BL-AV-1-10 / achado 2 | validado localmente | justificativa comparada para `APPROVE` e `ALTER`; `None` e string vazia equivalentes |
| BL-AV-1-10 / achado 3 | validado localmente | conflito 409 serializa `existing_review` como `HumanReviewSummaryOut`, com e-mail e notas finais |

## 3. Arquivos impactados nesta fatia

- `core/alembic/versions/7b1d6d853f20_add_unique_human_review_job_id.py`;
- `core/app/main.py`;
- `core/app/tests/test_review_idempotency.py`;
- sprint, registro de débitos, dashboard e snapshots de governança.

README, requisitos/PRD e roadmap foram revisados; nenhuma alteração adicional foi necessária. Frontend, AI Engine e workflow CI não foram tocados nesta fatia.

## 4. Validações reais

Ambiente: macOS local, Core `.venv`, SQLite descartável sob `/tmp`, America/Sao_Paulo.

| Data/fuso | Comando/procedimento | Tipo | Resultado real |
|---|---|---|---|
| 2026-09-24 06:2x -03 | teste dirigido de `app/tests/test_review_idempotency.py` | automatizada | exit 0; 7 passed, 13 warnings |
| 2026-09-24 06:2x -03 | primeira montagem do SQLite isolado | preparação | falhou antes da inserção por erro de quoting no auxiliar Python; nenhuma migração operacional ocorreu |
| 2026-09-24 06:2x -03 | `alembic upgrade e1b02279b1a5`, inserção de 3 duplicatas e `alembic upgrade head` com SQLite descartável | automatizada/migração isolada | exit 0; 3→1; manteve `review-oldest-a` de `2026-09-22 12:00:00`; nova duplicata rejeitada com exit 19 / `UNIQUE constraint failed` |
| 2026-09-24 06:2x -03 | `env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET .venv/bin/pytest app/tests -q` | automatizada | exit 0; 42 passed, 13 warnings, 28.58s |
| 2026-09-24 06:2x -03 | `.venv/bin/ruff check --config ../ruff.toml app` | automatizada/lint | exit 0; `All checks passed!` |
| 2026-09-24 06:2x -03 | `git diff --check` | automatizada/estática | exit 0, sem saída |

## 5. Limites e estado final

- `avalia_dev`: não acessado e não migrado; nenhuma contagem foi consultada para evitar tocar o alvo proibido;
- migração: validada apenas no SQLite isolado e descartável;
- revisão independente: realizada por Claude Code antes desta correção; este snapshot não a reapresenta como revisão posterior;
- homologação: pendente de Rafael;
- Git/remoto: nenhum commit, push, tag, deploy ou ação remota;
- status: implementada e validada localmente; CI remota e homologação geral de AV-S02 continuam pendentes.
