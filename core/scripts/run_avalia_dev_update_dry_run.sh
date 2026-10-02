#!/usr/bin/env bash
set -euo pipefail

# Ensaio completo e destrutivo SOMENTE em cluster PostgreSQL 16 temporário.
# Nenhuma conexão com avalia_dev é feita por este script; ele apenas lê um
# arquivo .dump já criado previamente por pg_dump (read-only).
#
# Uso:
#   DUMP_PATH=/caminho/fora/do/git/avalia_dev_*.dump \
#     bash core/scripts/run_avalia_dev_update_dry_run.sh
#
# Saída: stdout com marcadores GREEN e durações; evidência completa pode ser
# capturada por tee fora do Git ou no pacote local versionável.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CORE_DIR="$ROOT_DIR/core"
SCRIPTS_DIR="$CORE_DIR/scripts"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
DUMP_PATH="${DUMP_PATH:-}"

if [[ -z "$DUMP_PATH" || ! -f "$DUMP_PATH" ]]; then
  echo "DUMP_PATH deve apontar para um dump existente" >&2
  exit 2
fi
case "$DUMP_PATH" in
  "$ROOT_DIR"/*)
    echo "Recusando dump dentro do repositório: $DUMP_PATH" >&2
    exit 2
    ;;
esac

for cmd in initdb pg_ctl createdb dropdb pg_restore psql postgres; do
  [[ -x "$PG_BIN/$cmd" ]] || { echo "PostgreSQL 16 não encontrado: $PG_BIN/$cmd" >&2; exit 2; }
done
[[ -x "$CORE_DIR/.venv/bin/python" ]] || { echo "venv Core ausente: $CORE_DIR/.venv/bin/python" >&2; exit 2; }

CLUSTER_DIR="$(mktemp -d /private/tmp/av_s02_saneamento_dryrun.XXXXXX)"
SOCKET_DIR="$CLUSTER_DIR/socket"
LOG_FILE="$CLUSTER_DIR/postgres.log"
PORT="${AV_S02_DRY_RUN_PORT:-55439}"
mkdir -p "$SOCKET_DIR"

cleanup() {
  "$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$CLUSTER_DIR"
}
trap cleanup EXIT

now_ns() { "$CORE_DIR/.venv/bin/python" -c 'import time; print(time.time_ns())'; }
duration_s() {
  "$CORE_DIR/.venv/bin/python" - "$1" "$2" <<'PY'
import sys
print(f"{(int(sys.argv[2]) - int(sys.argv[1])) / 1_000_000_000:.3f}")
PY
}

timed() {
  local label="$1"; shift
  local start end rc
  start="$(now_ns)"
  set +e
  "$@"
  rc=$?
  set -e
  end="$(now_ns)"
  echo "DURATION_${label}_SECONDS=$(duration_s "$start" "$end")"
  return "$rc"
}

psql_db() {
  local db="$1"; shift
  "$PG_BIN/psql" -h 127.0.0.1 -p "$PORT" -U postgres -d "$db" "$@"
}

create_empty_db() {
  local db="$1"
  case "$db" in
    av_s02_saneamento_*) ;;
    *) echo "Nome de banco inseguro: $db" >&2; exit 2 ;;
  esac
  "$PG_BIN/dropdb" -h 127.0.0.1 -p "$PORT" -U postgres --if-exists "$db" >/dev/null
  "$PG_BIN/createdb" -h 127.0.0.1 -p "$PORT" -U postgres "$db"
}

restore_dump() {
  local db="$1"
  create_empty_db "$db"
  timed "RESTORE_${db}" "$PG_BIN/pg_restore" --exit-on-error --no-owner \
    -h 127.0.0.1 -p "$PORT" -U postgres -d "$db" "$DUMP_PATH"
}

assert_scalar() {
  local db="$1" query="$2" expected="$3" label="$4" actual
  actual="$(psql_db "$db" -Atc "$query")"
  if [[ "$actual" != "$expected" ]]; then
    echo "ASSERTION FAILED [$label]: expected=$expected actual=$actual" >&2
    exit 1
  fi
  echo "ASSERTION_OK_${label}=$actual"
}

run_sanitation() {
  local db="$1"
  timed "SANITATION_${db}" psql_db "$db" -v ON_ERROR_STOP=1 \
    -f "$SCRIPTS_DIR/av_s02_saneamento_human_reviews.sql"
}

run_recovery() {
  local db="$1"
  timed "RECOVERY_${db}" psql_db "$db" -v ON_ERROR_STOP=1 \
    -f "$SCRIPTS_DIR/av_s02_recuperacao_saneamento.sql"
}

alembic_to() {
  local db="$1" target="$2" label="$3"
  (
    cd "$CORE_DIR"
    DATABASE_URL="postgresql+psycopg2://postgres@127.0.0.1:${PORT}/${db}" \
      timed "$label" .venv/bin/python -m alembic -c alembic.ini upgrade "$target"
  )
}

alembic_down_to() {
  local db="$1" target="$2" label="$3"
  (
    cd "$CORE_DIR"
    DATABASE_URL="postgresql+psycopg2://postgres@127.0.0.1:${PORT}/${db}" \
      timed "$label" .venv/bin/python -m alembic -c alembic.ini downgrade "$target"
  )
}

# ----------------------------------------------------------------------------
# Cluster temporário isolado PostgreSQL 16.
# ----------------------------------------------------------------------------
echo "POSTGRES_VERSION=$($PG_BIN/postgres --version)"
echo "DUMP_PATH=$DUMP_PATH"
echo "DUMP_SHA256=$(shasum -a 256 "$DUMP_PATH" | cut -d' ' -f1)"
echo "CLUSTER_DIR=$CLUSTER_DIR"

"$PG_BIN/initdb" -D "$CLUSTER_DIR/data" -U postgres --auth=trust >/dev/null
"$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" \
  -o "-p $PORT -k $SOCKET_DIR -c listen_addresses=127.0.0.1" \
  -l "$LOG_FILE" start >/dev/null

# ----------------------------------------------------------------------------
# A. Restore efetivo + validação do estado de origem.
# ----------------------------------------------------------------------------
echo "=== A RESTORE + SOURCE STATE VALIDATION ==="
DB_HAPPY="av_s02_saneamento_happy"
restore_dump "$DB_HAPPY"
assert_scalar "$DB_HAPPY" "SELECT version_num FROM alembic_version" "e1b02279b1a5" "RESTORED_ALEMBIC_VERSION"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "RESTORED_DUPLICATE_ROWS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM (SELECT job_id FROM human_reviews GROUP BY job_id HAVING COUNT(*)>1) t" "1" "RESTORED_DUPLICATE_GROUPS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM users" "4" "RESTORED_USERS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM assessments" "10" "RESTORED_ASSESSMENTS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM questions" "10" "RESTORED_QUESTIONS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM human_reviews" "18" "RESTORED_HUMAN_REVIEWS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM audit_events" "36" "RESTORED_AUDIT_EVENTS"
echo "RESTORE_EFFECTIVE_GREEN"

# Diagnóstico read-only do estado restaurado.
timed "DIAGNOSTIC" psql_db "$DB_HAPPY" -v ON_ERROR_STOP=1 \
  -f "$SCRIPTS_DIR/av_s02_diagnostico_human_reviews.sql"

# ----------------------------------------------------------------------------
# B. Happy path: e1 -> saneamento -> 7b1 -> c4a -> a9f -> validação.
# ----------------------------------------------------------------------------
echo "=== B HAPPY PATH FULL CHAIN ==="
run_sanitation "$DB_HAPPY"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM (SELECT job_id FROM human_reviews GROUP BY job_id HAVING COUNT(*)>1) t" "0" "POST_SANITATION_DUPLICATE_GROUPS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM human_reviews_superseded WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "2" "POST_SANITATION_ARCHIVED"
# Reexecução sobre estado pós exato deve ser no-op bem-sucedido, não erro.
run_sanitation "$DB_HAPPY"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "1" "SANITATION_IDEMPOTENT_ACTIVE"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM human_reviews_superseded WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "2" "SANITATION_IDEMPOTENT_ARCHIVE"

alembic_to "$DB_HAPPY" "7b1d6d853f20" "MIGRATION_7B1"
alembic_to "$DB_HAPPY" "c4a8b2d91e37" "MIGRATION_C4A"
alembic_to "$DB_HAPPY" "a9f4c2e71b06" "MIGRATION_A9F"

timed "POST_MIGRATION_VALIDATION" psql_db "$DB_HAPPY" -v ON_ERROR_STOP=1 \
  -f "$SCRIPTS_DIR/av_s02_validacao_pos_migracoes.sql"

# Flags acadêmicas coerentes (backend true + frontend true) e seed demo.
(
  cd "$ROOT_DIR"
  DATABASE_URL="postgresql+psycopg2://postgres@127.0.0.1:${PORT}/${DB_HAPPY}" \
  ACADEMIC_MODULE_ENABLED=true \
  VITE_ACADEMIC_MODULE_ENABLED=true \
  JWT_SECRET="isolated-dry-run-secret" \
  AI_ENGINE_URL="http://127.0.0.1:9999" \
  PYTHONPATH="$CORE_DIR" \
    timed "DEMO_SEED_FIRST" "$CORE_DIR/.venv/bin/python" \
      "$SCRIPTS_DIR/seed_academic_multi_question_demo.py"
  DATABASE_URL="postgresql+psycopg2://postgres@127.0.0.1:${PORT}/${DB_HAPPY}" \
  ACADEMIC_MODULE_ENABLED=true \
  VITE_ACADEMIC_MODULE_ENABLED=true \
  JWT_SECRET="isolated-dry-run-secret" \
  AI_ENGINE_URL="http://127.0.0.1:9999" \
  PYTHONPATH="$CORE_DIR" \
    timed "DEMO_SEED_SECOND_IDEMPOTENCY" "$CORE_DIR/.venv/bin/python" \
      "$SCRIPTS_DIR/seed_academic_multi_question_demo.py"
)
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM questions WHERE assessment_id='demo-av-s04-assessment-multiple-questions'" "2" "DEMO_TWO_QUESTIONS"
assert_scalar "$DB_HAPPY" "SELECT string_agg(position::text, ',' ORDER BY position) FROM questions WHERE assessment_id='demo-av-s04-assessment-multiple-questions'" "1,2" "DEMO_POSITIONS"
assert_scalar "$DB_HAPPY" "SELECT COUNT(*) FROM professor_class_links WHERE id='demo-av-s04-professor-link' AND active" "1" "DEMO_ACTIVE_PROFESSOR_LINK"
echo "HAPPY_PATH_FULL_CHAIN_GREEN"

# ----------------------------------------------------------------------------
# C. Falha: grupo deixa de ser equivalente. Deve abortar sem mover/apagar.
# ----------------------------------------------------------------------------
echo "=== C FAILURE NON-EQUIVALENT DUPLICATES ==="
DB_CONFLICT="av_s02_saneamento_conflict"
restore_dump "$DB_CONFLICT"
psql_db "$DB_CONFLICT" -v ON_ERROR_STOP=1 -c \
  "UPDATE human_reviews SET final_total = 3.00 WHERE id='9459489c-dd8e-4f33-936a-bc76cb7d5f0b';" >/dev/null
set +e
psql_db "$DB_CONFLICT" -v ON_ERROR_STOP=1 -f \
  "$SCRIPTS_DIR/av_s02_saneamento_human_reviews.sql" >"$CLUSTER_DIR/conflict.out" 2>&1
CONFLICT_RC=$?
set -e
if [[ "$CONFLICT_RC" -eq 0 ]]; then
  echo "Expected conflict sanitation to fail, but it succeeded" >&2
  exit 1
fi
assert_scalar "$DB_CONFLICT" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "CONFLICT_ACTIVE_ROWS_UNCHANGED"
assert_scalar "$DB_CONFLICT" "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename='human_reviews_superseded'" "0" "CONFLICT_ARCHIVE_DDL_ROLLED_BACK"
grep -q "Grupo conflitante" "$CLUSTER_DIR/conflict.out"
echo "FAILURE_NON_EQUIVALENT_ABORT_GREEN"

# ----------------------------------------------------------------------------
# D. Falha antes do COMMIT, depois da cópia: rollback automático completo.
# Usa um trigger BEFORE DELETE real em human_reviews para forçar a exceção
# dentro da própria execução de av_s02_saneamento_human_reviews.sql, no ponto
# exato entre o INSERT de arquivamento e o DELETE — não uma transação
# sintética à parte. Isso prova a atomicidade do script real, não apenas do
# PostgreSQL em geral.
# ----------------------------------------------------------------------------
echo "=== D FAILURE AFTER ARCHIVE COPY BEFORE DELETE/COMMIT ==="
DB_PRECOMMIT="av_s02_saneamento_precommit_failure"
restore_dump "$DB_PRECOMMIT"
psql_db "$DB_PRECOMMIT" -v ON_ERROR_STOP=1 -c "
CREATE OR REPLACE FUNCTION public.av_s02_force_precommit_failure() RETURNS trigger AS \$\$
BEGIN
  RAISE EXCEPTION 'FORCED_PRECOMMIT_FAILURE';
END;
\$\$ LANGUAGE plpgsql;
CREATE TRIGGER av_s02_force_precommit_failure
  BEFORE DELETE ON public.human_reviews
  FOR EACH ROW EXECUTE FUNCTION public.av_s02_force_precommit_failure();
" >/dev/null
set +e
psql_db "$DB_PRECOMMIT" -v ON_ERROR_STOP=1 -f \
  "$SCRIPTS_DIR/av_s02_saneamento_human_reviews.sql" >"$CLUSTER_DIR/precommit.out" 2>&1
set -e
assert_scalar "$DB_PRECOMMIT" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "PRECOMMIT_ACTIVE_ROWS_ROLLED_BACK"
assert_scalar "$DB_PRECOMMIT" "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename='human_reviews_superseded'" "0" "PRECOMMIT_ARCHIVE_TABLE_ROLLED_BACK"
grep -q "FORCED_PRECOMMIT_FAILURE" "$CLUSTER_DIR/precommit.out"
echo "FAILURE_PRECOMMIT_ROLLBACK_GREEN"
# Remove o trigger de injeção de falha antes de qualquer reexecução futura
# deste banco descartável (não se aplica a bancos de outros cenários).
psql_db "$DB_PRECOMMIT" -v ON_ERROR_STOP=1 -c \
  "DROP TRIGGER IF EXISTS av_s02_force_precommit_failure ON public.human_reviews;
   DROP FUNCTION IF EXISTS public.av_s02_force_precommit_failure();" >/dev/null

# ----------------------------------------------------------------------------
# E. Falha pós-COMMIT / pré-constraint: recuperação compensatória.
# ----------------------------------------------------------------------------
echo "=== E RECOVERY AFTER SANITATION BEFORE CONSTRAINT ==="
DB_RECOVERY_PRE="av_s02_saneamento_recovery_pre_constraint"
restore_dump "$DB_RECOVERY_PRE"
run_sanitation "$DB_RECOVERY_PRE"
run_recovery "$DB_RECOVERY_PRE"
assert_scalar "$DB_RECOVERY_PRE" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "RECOVERY_PRE_ACTIVE_ROWS"
assert_scalar "$DB_RECOVERY_PRE" "SELECT COUNT(*) FROM human_reviews_superseded" "0" "RECOVERY_PRE_ARCHIVE_EMPTY"
# Reexecução sobre estado já recuperado deve ser no-op bem-sucedido.
run_recovery "$DB_RECOVERY_PRE"
assert_scalar "$DB_RECOVERY_PRE" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "RECOVERY_IDEMPOTENT_ACTIVE"
echo "RECOVERY_AFTER_SANITATION_BEFORE_CONSTRAINT_GREEN"

# ----------------------------------------------------------------------------
# F. Recuperação depois da constraint: downgrade 7b1 -> e1 -> compensação.
# ----------------------------------------------------------------------------
echo "=== F RECOVERY AFTER 7B1 CONSTRAINT ==="
DB_RECOVERY_POST="av_s02_saneamento_recovery_post_constraint"
restore_dump "$DB_RECOVERY_POST"
run_sanitation "$DB_RECOVERY_POST"
alembic_to "$DB_RECOVERY_POST" "7b1d6d853f20" "RECOVERY_POST_APPLY_7B1"
alembic_down_to "$DB_RECOVERY_POST" "e1b02279b1a5" "RECOVERY_POST_DOWNGRADE_TO_E1"
run_recovery "$DB_RECOVERY_POST"
assert_scalar "$DB_RECOVERY_POST" "SELECT version_num FROM alembic_version" "e1b02279b1a5" "RECOVERY_POST_ALEMBIC_VERSION"
assert_scalar "$DB_RECOVERY_POST" "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'" "3" "RECOVERY_POST_ACTIVE_ROWS"
echo "RECOVERY_AFTER_CONSTRAINT_GREEN"

# ----------------------------------------------------------------------------
# G. Particularidade CREATE INDEX CONCURRENTLY / checkpoint interrompido.
# Reusa o validador dedicado AV-S04, que cria seu próprio cluster/bancos
# descartáveis e cobre fresh, índice INVALID residual e índice válido.
# ----------------------------------------------------------------------------
echo "=== G CONCURRENT INDEX FAILURE + RESUME ==="
timed "MIGRATION_CONCURRENT_INDEX_RECOVERY" \
  bash "$ROOT_DIR/docs/governance/evidence/AV-S04/pacote-execucao-local/validate_migration_recovery.sh"
echo "CONCURRENT_INDEX_RECOVERY_GREEN"

# ----------------------------------------------------------------------------
# H. Guard: nomes parecidos não podem passar por causa de '_' como wildcard.
# ----------------------------------------------------------------------------
echo "=== H DATABASE NAME GUARD ==="
BAD_DB="avXs02YsaneamentoZlookalike"
"$PG_BIN/createdb" -h 127.0.0.1 -p "$PORT" -U postgres "$BAD_DB"
set +e
psql_db "$BAD_DB" -v ON_ERROR_STOP=1 -f \
  "$SCRIPTS_DIR/av_s02_saneamento_human_reviews.sql" >"$CLUSTER_DIR/guard.out" 2>&1
GUARD_RC=$?
set -e
if [[ "$GUARD_RC" -eq 0 ]]; then
  echo "Guard aceitou nome lookalike indevidamente" >&2
  exit 1
fi
grep -q "Guard recusou banco" "$CLUSTER_DIR/guard.out"
echo "DATABASE_NAME_GUARD_GREEN"

echo "ALL_DRY_RUN_SCENARIOS_GREEN"
