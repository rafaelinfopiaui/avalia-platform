---
id: "execucao_claude_code_1a_fatia_bl-av-4b-05"
tema: "BL-AV-4B-05 — 1ª fatia (exclusão lógica reversível de imagens) — registro de execução"
data: "2026-10-15 (America/Sao_Paulo)"
executor: "Claude Code (CLI claude 2.1.299, invocado com --model opus)"
branch: "feat/bl-av-4b-05-exclusao-logica-imagens (renomeada de docs/...; working tree na execução do executor, sem git)"
status: "IMPLEMENTADO pelo executor — NÃO VALIDADO por ele (execução de testes bloqueada por permissão na sessão); validação feita depois pelo orquestrador (ver parecer_antigravity_implementacao.md e evidencia_validacao_navegador.md)"
---

# Registro de execução — 1ª fatia de BL-AV-4B-05

Especificação seguida: `desenho_bl-av-4b-05_retencao_exclusao_imagens.md`
§6 (D1/D2/D3), §7, §8 (ACD-01..15), §9 e §12 (R1/R2/R3/R4). Sem git, sem
acesso a `avalia_dev`/`avalia_apresentacao_demo_20261002`, sem remoção física,
sem `storage_deleted_at`, sem scheduler, sem OCR/deploy/P5.

## Estado real

| Etapa | Estado |
|---|---|
| Implementação backend, migração, script, frontend, testes | **implementado** (arquivos no working tree) |
| `pytest` (SQLite) | **NÃO executado** — sessão sem permissão para rodar `core/.venv/bin/python`/`alembic` |
| Concorrência PostgreSQL (ACD-07/10/14) | **NÃO executado** — `createdb`/`pg_isready` também bloqueados; nenhum banco foi criado |
| Migração upgrade/downgrade em banco descartável | **NÃO executado** |
| `npm run build` / `npm run lint` | **NÃO executado** — `npm` bloqueado |
| Revisão independente (Antigravity) | pendente |
| Homologação (Rafael) | pendente |

Nada aqui deve ser lido como validado. O código foi revisado por leitura pelo
próprio executor, o que não substitui execução nem revisão independente.

## Arquivos

Criados:
- `core/alembic/versions/b8d3e5f7a2c4_add_answer_image_logical_deletion.py`
  (down_revision `f2a9c4e6b1d3`, conferido por leitura da cadeia de `down_revision`)
- `core/scripts/blav4b05_diagnostico_imagens.py` (ACD-13, somente leitura)
- `core/app/tests/test_answer_image_deletion.py`

Alterados:
- `core/app/models.py` — `AnswerImage.deleted_at`, `AnswerImage.deleted_by_id`
- `core/app/schemas.py` — `DeletedAnswerImageOut` (id, deleted_at, deleted_by_id)
- `core/app/routers/images.py` — `_lock_answer_row` (SELECT … FOR UPDATE),
  `DELETE /v1/answer-images/{id}`, `POST /v1/answer-images/{id}/restore`,
  `GET /v1/answers/{id}/images/deleted`; listagem/download filtram excluídas
  (download de excluída → 410)
- `core/app/main.py` — `_answer_with_images`/`list_image_answers` só com ativas;
  confirmação trava a linha de `answers`, reavalia estado e exige imagem ativa
  (409 `ANSWER_HAS_NO_ACTIVE_IMAGE`); lock otimista de `transcription_version` mantido
- `core/app/tests/test_manual_transcription.py` — helper `_image_answer` passa a
  criar um registro de imagem (exigido por ACD-09); barreira de concorrência
  adaptada ao lock pessimista da confirmação (sincroniza a primeira escrita de
  cada transação: UPDATE ou SELECT … FOR UPDATE)
- `frontend/src/types.ts`, `frontend/src/services/api.ts`,
  `frontend/src/pages/ImageAnswerPage.tsx`

## Procedimento de validação pendente (para quem tiver permissão de execução)

```sh
cd core
.venv/bin/python -m pytest -q                       # suíte padrão (SQLite)

DB=avalia_test_blav4b05_$$                           # banco descartável
createdb "$DB"
DATABASE_URL="postgresql+psycopg2://localhost:5432/$DB" .venv/bin/alembic upgrade head
# downgrade bloqueado com deleted_at preenchido: inserir uma imagem excluída
# fictícia e conferir RuntimeError em `alembic downgrade f2a9c4e6b1d3`
AVALIA_TEST_POSTGRES_URL="postgresql+psycopg2://localhost:5432/$DB" \
  .venv/bin/python -m pytest -q app/tests/test_answer_image_deletion.py -k pg -s
AVALIA_TEST_POSTGRES_URL="postgresql+psycopg2://localhost:5432/$DB" \
  .venv/bin/python -m pytest -q                      # inclui PG de AV-S08B
dropdb "$DB"

cd ../frontend && npm run build && npm run lint
```

Atenção: `DATABASE_URL` sem valor cai no default `avalia_dev`
(`core/app/config.py`). Sempre definir explicitamente ao rodar `alembic`.
Os testes PG de `test_answer_image_deletion.py` exigem o schema da migração
(conferem `alembic_version = b8d3e5f7a2c4`) e devem rodar antes dos de
`test_manual_transcription.py`, que fazem `drop_all` ao final (é a ordem
padrão do pytest, por nome de arquivo).

## Decisões técnicas tomadas na implementação (dentro do desenho)

- 409 `ANSWER_IMAGES_LOCKED` para excluir/restaurar fora do estágio A, inclusive admin.
- 409 `ANSWER_IMAGE_FILE_MISSING` na restauração sem arquivo (estado preservado).
- 410 no download de imagem excluída (ACD-08 admite 404/410).
- Guard de estágio avaliado antes da idempotência: repetir exclusão em B → 409.
- `AuditEvent` `before_json`/`after_json`: id, answer_id, uploaded_by_id,
  content_type, size_bytes, created_at, deleted_at, deleted_by_id — nunca
  original_filename, storage_filename, sha256_hash ou conteúdo.
- O script de diagnóstico não tem banco/diretório padrão (ambos obrigatórios)
  para não apontar para `avalia_dev` por acidente; abre a conexão em modo
  somente leitura no próprio banco.

Snapshot de sessão e atualização do dashboard ficam com o Hermes, que conduz
o rito; este registro é a evidência de execução do executor.
