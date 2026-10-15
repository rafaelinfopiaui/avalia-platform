---
id: "escopo_ci_cobertura_postgres_concorrencia"
tema: "Melhoria de CI — cobertura real dos testes de concorrência PostgreSQL"
data: "2026-10-15 (America/Sao_Paulo)"
origem: "lacuna registrada em DEC-AV-041 e DEC-AV-043 (a CI roda SQLite; testes test_pg_* ficam SKIPPED)"
base: "main cde87cc74f37dfca6136a1c8eeeb5489318045e2"
branch: "ci/cobertura-postgres-concorrencia (checkout principal, sem worktree)"
status: "PLANEJAMENTO + IMPLEMENTAÇÃO LOCAL — sem publicação nesta rodada"
---

# Escopo — cobertura dos testes de concorrência PostgreSQL na CI

## 1. Problema

A CI atual (`.github/workflows/ci.yml`, job `core`) roda a suíte em
**SQLite**: o step "Run core tests" faz
`env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET pytest app/tests -q`
(remove `DATABASE_URL` → cai no default SQLite do `conftest.py`) e **não
define `AVALIA_TEST_POSTGRES_URL`**. Os testes `test_pg_*`
(`@requires_postgres`, `skipif(not AVALIA_TEST_POSTGRES_URL)`) ficam
**SKIPPED** (log da run `38704909538`: `232 passed, 10 skipped`). O
serviço `postgres:16` existe mas não é exercitado.

## 2. Objetivo (mínimo, sem ampliação)

Acrescentar execução **explícita** dos testes PostgreSQL já implementados,
contra um **banco descartável exclusivo** no serviço postgres da CI, SEM:
- alterar regras de produto;
- migrar toda a suíte para PostgreSQL (a suíte SQLite existente é
  preservada integralmente, como está);
- tocar `avalia_dev` / `avalia_apresentacao_demo_20261002` (não existem na
  CI; a guarda de banco protegido nos testes permanece);
- ampliar para deploy/baseline/migração operacional.

## 3. Inventário dos testes PostgreSQL (coletado, não presumido)

Casos guardados por `AVALIA_TEST_POSTGRES_URL` — **10 casos** no total
(= os "10 skipped" da CI SQLite):

`app/tests/test_answer_image_deletion.py` (5 casos; 4 funções, uma
parametrizada [2,8]):
1. `test_pg_delete_last_image_vs_confirm_exactly_one_wins`
2. `test_pg_concurrent_deletes_produce_one_effect_and_one_audit[2]`
3. `test_pg_concurrent_deletes_produce_one_effect_and_one_audit[8]`
4. `test_pg_restore_after_confirmation_with_other_image_is_409_even_for_admin`
5. `test_pg_restore_vs_confirm_never_changes_confirmed_image_set`

`app/tests/test_manual_transcription.py` (5 casos; 3 funções, duas
parametrizadas [2,8]):
6. `test_pg_concurrent_drafts_only_one_commits[2]`
7. `test_pg_concurrent_drafts_only_one_commits[8]`
8. `test_pg_concurrent_confirms_exactly_one_wins[2]`
9. `test_pg_concurrent_confirms_exactly_one_wins[8]`
10. `test_pg_concurrent_confirm_and_draft_never_reopen`

### Preparação de schema (difere por arquivo — relevante para o step)
- `test_answer_image_deletion.py`: a fixture `pg_engine` **exige o schema
  criado por `alembic upgrade head`** e faz assert
  `alembic_version == b8d3e5f7a2c4`. Logo, o step DEVE rodar
  `alembic upgrade head` no banco descartável ANTES.
- `test_manual_transcription.py`: a fixture `pg_engine` usa
  `Base.metadata.create_all` (não depende de alembic); compatível com o
  mesmo banco já migrado.

## 4. Desenho da mudança (um step novo, isolado)

No job `core`, **após** o step SQLite existente (preservado intacto),
adicionar um step novo "Run PostgreSQL concurrency tests" que:
1. cria um banco descartável **exclusivo** no serviço postgres da CI
   (ex.: `avalia_ci_pg_concurrency`), distinto de `avalia_dev`;
2. roda `alembic upgrade head` nesse banco (satisfaz o assert de head);
3. exporta `AVALIA_TEST_POSTGRES_URL` apontando a esse banco;
4. roda SÓ os arquivos com testes PG, selecionando os `test_pg_*`
   (`-k "test_pg_"`), com relatório verificável (`-v -rsa`, resumo de
   coletados/passados/skipped);
5. **falha explicitamente** se nenhum teste PG for selecionado/executado,
   ou se algum dos 10 esperados for skippado (guard anti-skip-silencioso):
   usa `--deselect`-free seleção + verificação do número de passed; e
   `-p no:cacheprovider`. A falha é um `exit 1` com mensagem clara.

Credenciais do serviço postgres da CI são as já definidas no job
(`avalia_user`/`avalia_password` em `localhost:5432`) — **não são segredo
de produção** e já constam no workflow; não se adiciona segredo novo nem
se expõe credencial fora do que o workflow já declara.

## 5. Critérios de aceite (ACD-CI)

| ID | Critério |
|---|---|
| ACD-CI-01 | A suíte SQLite existente (step "Run core tests") permanece inalterada e verde. |
| ACD-CI-02 | Um step novo e distinto roda os testes PostgreSQL contra um banco descartável exclusivo (nunca `avalia_dev`/apresentação). |
| ACD-CI-03 | O banco de teste é criado, migrado (`alembic upgrade head`) e os 10 casos `test_pg_*` são coletados e **executados** (não skipped). |
| ACD-CI-04 | O step FALHA explicitamente (exit≠0, mensagem clara) se `AVALIA_TEST_POSTGRES_URL` estiver ausente OU se os testes PG esperados forem todos ignorados/não coletados. |
| ACD-CI-05 | A saída do step permite verificar coletados/executados/passados/skipped (ex.: `-v -rsa` e contagem explícita). |
| ACD-CI-06 | Não há dependência de banco local do desenvolvedor; o step usa só o serviço postgres da CI. Limpeza: o banco descartável não precisa sobreviver ao job (runner é efêmero); opcionalmente dropado ao fim. |
| ACD-CI-07 | O workflow distingue claramente, por nome de step e saída, a suíte SQLite dos testes PostgreSQL reais. |
| ACD-CI-08 | Nenhuma regra de produto alterada; nenhum arquivo de teste de produto reescrito além do estritamente necessário (idealmente zero). |

## 6. Limite de verificação (explícito)

A **execução remota real** no GitHub Actions só pode ser comprovada por
uma run real — que depende de publicação, **não autorizada nesta rodada**.
Portanto esta entrega é **implementada e validada LOCALMENTE**; a lacuna
remota **não é declarada resolvida** até uma run real do Actions
comprovar os 10 casos executados. Critérios para conferir a 1ª run remota
(após futura autorização) ficam na entrega.

## 7. Papéis

- **Claude Code**: implementa a mudança no workflow (e, se necessário,
  um comando/script auxiliar), validando localmente a lógica do step.
- **Antigravity**: revisa o delta (só esta mudança), não reaudita a fatia
  já homologada.
- **Codex**: só diante de risco concreto.

## 8. Não autorizado nesta rodada

stage/commit/push/merge, publicação, alteração em bancos protegidos,
migração operacional, P5, OCR, remoção física, deploy, baseline. Numerador
preservado 22/70; BL-AV-4B-05 permanece parcial.
