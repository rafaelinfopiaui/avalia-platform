#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
CORE_DIR="$ROOT_DIR/core"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
CLUSTER_DIR="$(mktemp -d /private/tmp/av_s04_migration_pg16.XXXXXX)"
SOCKET_DIR="$CLUSTER_DIR/socket"
LOG_FILE="$CLUSTER_DIR/postgres.log"

FRESH_DB="av_s04_migration_fresh_agent"
RECOVERY_DB="av_s04_migration_recovery_agent"
VALID_INDEX_DB="av_s04_migration_valid_index_agent"

guard_database_name() {
    local database_name="$1"
    if [[ "$database_name" == "avalia_dev" || "$database_name" != av_s04_migration_* ]]; then
        echo "REFUSED unsafe database name: $database_name" >&2
        exit 64
    fi
}

cleanup() {
    "$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" -m fast stop >/dev/null 2>&1 || true
    if [[ "$CLUSTER_DIR" == /private/tmp/av_s04_migration_pg16.* ]]; then
        rm -rf "$CLUSTER_DIR"
    else
        echo "REFUSED unsafe cluster cleanup path: $CLUSTER_DIR" >&2
    fi
}
trap cleanup EXIT

for database_name in "$FRESH_DB" "$RECOVERY_DB" "$VALID_INDEX_DB"; do
    guard_database_name "$database_name"
done

mkdir "$SOCKET_DIR"
"$PG_BIN/initdb" -D "$CLUSTER_DIR/data" --auth=trust --no-locale --encoding=UTF8 \
    -c shared_memory_type=mmap -c dynamic_shared_memory_type=mmap >/dev/null
"$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" -l "$LOG_FILE" -o \
    "-k $SOCKET_DIR -c listen_addresses=''" start >/dev/null

psql_base=("$PG_BIN/psql" -h "$SOCKET_DIR" -v ON_ERROR_STOP=1 -X)

create_database() {
    local database_name="$1"
    guard_database_name "$database_name"
    "$PG_BIN/createdb" -h "$SOCKET_DIR" "$database_name"
}

database_url() {
    local database_name="$1"
    guard_database_name "$database_name"
    printf 'postgresql+psycopg2:///%s?host=%s' "$database_name" "$SOCKET_DIR"
}

alembic_upgrade() {
    local database_name="$1"
    local target="$2"
    guard_database_name "$database_name"
    (
        cd "$CORE_DIR"
        DATABASE_URL="$(database_url "$database_name")" \
            .venv/bin/python -m alembic upgrade "$target"
    )
}

seed_legacy_data() {
    local database_name="$1"
    guard_database_name "$database_name"
    "${psql_base[@]}" -d "$database_name" <<'SQL'
INSERT INTO users (id, email, password_hash, role, is_active, created_at)
VALUES ('u1', 'migration@example.test', 'x', 'PROFESSOR', true, '2026-01-01 00:00:00');

INSERT INTO assessments (id, title, owner_id, status, created_at, updated_at)
VALUES
    ('a1', 'three questions', 'u1', 'RASCUNHO', '2026-01-01', '2026-01-01'),
    ('a2', 'one question', 'u1', 'RASCUNHO', '2026-01-02', '2026-01-02');

INSERT INTO audit_events
    (id, actor_id, action, resource_type, resource_id, before_json, after_json, created_at)
VALUES
    ('ae1', 'u1', 'CREATE', 'Assessment', 'a1', NULL, NULL, '2026-01-01 10:00:00'),
    ('ae2', 'u1', 'CREATE', 'Assessment', 'a2', NULL, NULL, '2026-01-02 10:00:00');

INSERT INTO questions (id, assessment_id, statement, reference_answer, max_score)
VALUES
    ('q-a3', 'a1', 'third by id', 'r', 1),
    ('q-a1', 'a1', 'first by id', 'r', 1),
    ('q-a2', 'a1', 'second by id', 'r', 1),
    ('q-b1', 'a2', 'only', 'r', 1);
SQL
}

assert_common_green() {
    local database_name="$1"
    guard_database_name "$database_name"
    "${psql_base[@]}" -d "$database_name" <<'SQL'
DO $$
DECLARE
    actual_positions text;
    invalid_indexes integer;
BEGIN
    SELECT string_agg(id || ':' || position::text, ',' ORDER BY assessment_id, position)
      INTO actual_positions
      FROM questions;
    IF actual_positions <> 'q-a1:1,q-a2:2,q-a3:3,q-b1:1' THEN
        RAISE EXCEPTION 'unexpected deterministic positions: %', actual_positions;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'questions'
          AND column_name IN ('created_at', 'position') AND is_nullable <> 'NO'
    ) THEN
        RAISE EXCEPTION 'questions created_at/position are not both NOT NULL';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'questions'::regclass
          AND conname = 'uq_questions_assessment_position' AND contype = 'u'
    ) THEN
        RAISE EXCEPTION 'expected unique constraint is absent';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'assessments'::regclass
          AND conname = 'fk_assessments_cloned_from_id' AND contype = 'f'
    ) THEN
        RAISE EXCEPTION 'expected clone FK is absent';
    END IF;

    SELECT count(*) INTO invalid_indexes
    FROM pg_index WHERE indexrelid IN (
        SELECT indexrelid FROM pg_index WHERE indrelid = 'questions'::regclass
    ) AND NOT indisvalid;
    IF invalid_indexes <> 0 THEN
        RAISE EXCEPTION 'invalid question indexes remain: %', invalid_indexes;
    END IF;

    BEGIN
        INSERT INTO questions
            (id, assessment_id, statement, reference_answer, max_score, created_at, position)
        VALUES ('reject-unique', 'a1', 'x', 'x', 1, now(), 1);
        RAISE EXCEPTION 'duplicate position was accepted';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO questions
            (id, assessment_id, statement, reference_answer, max_score, created_at, position)
        VALUES ('reject-null', 'a1', 'x', 'x', 1, now(), NULL);
        RAISE EXCEPTION 'NULL position was accepted';
    EXCEPTION WHEN not_null_violation THEN NULL;
    END;

    BEGIN
        UPDATE assessments SET cloned_from_id = 'missing' WHERE id = 'a2';
        RAISE EXCEPTION 'invalid clone provenance was accepted';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
END
$$;
SQL
}

echo "PostgreSQL: $($PG_BIN/postgres --version)"

echo "=== A fresh ==="
create_database "$FRESH_DB"
alembic_upgrade "$FRESH_DB" c4a8b2d91e37
seed_legacy_data "$FRESH_DB"
alembic_upgrade "$FRESH_DB" head
assert_common_green "$FRESH_DB"
# Re-run from a fully persisted schema with the Alembic marker rewound. This
# covers columns/NOT NULL, attached unique constraint, clone column and FK.
"${psql_base[@]}" -d "$FRESH_DB" -c \
    "UPDATE alembic_version SET version_num = 'c4a8b2d91e37'"
alembic_upgrade "$FRESH_DB" head
assert_common_green "$FRESH_DB"
echo "A GREEN"

echo "=== B recovery-invalid-index ==="
create_database "$RECOVERY_DB"
alembic_upgrade "$RECOVERY_DB" c4a8b2d91e37
seed_legacy_data "$RECOVERY_DB"
"${psql_base[@]}" -d "$RECOVERY_DB" <<'SQL'
ALTER TABLE questions ADD COLUMN created_at timestamp DEFAULT now();
ALTER TABLE questions ADD COLUMN position integer;
UPDATE questions SET position = 1;
ALTER TABLE questions ADD CONSTRAINT questions_position_not_null
    CHECK (position IS NOT NULL) NOT VALID;
ALTER TABLE questions VALIDATE CONSTRAINT questions_position_not_null;
ALTER TABLE questions ADD CONSTRAINT questions_created_at_not_null
    CHECK (created_at IS NOT NULL) NOT VALID;
ALTER TABLE questions VALIDATE CONSTRAINT questions_created_at_not_null;
SQL
set +e
"${psql_base[@]}" -d "$RECOVERY_DB" -c \
    "CREATE UNIQUE INDEX CONCURRENTLY ix_questions_assessment_position ON questions (assessment_id, position)"
index_build_status=$?
set -e
if [[ "$index_build_status" -eq 0 ]]; then
    echo "Expected concurrent index build to fail" >&2
    exit 1
fi
"${psql_base[@]}" -d "$RECOVERY_DB" <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_index i ON i.indexrelid = c.oid
        WHERE c.relname = 'ix_questions_assessment_position' AND NOT i.indisvalid
    ) THEN
        RAISE EXCEPTION 'expected INVALID index was not produced';
    END IF;
END
$$;
WITH ranked AS (
    SELECT id, row_number() OVER (PARTITION BY assessment_id ORDER BY id) AS position
    FROM questions
)
UPDATE questions q SET position = ranked.position FROM ranked WHERE ranked.id = q.id;
SQL
alembic_upgrade "$RECOVERY_DB" head
assert_common_green "$RECOVERY_DB"
echo "B GREEN"

echo "=== C checkpoint-valid-index ==="
create_database "$VALID_INDEX_DB"
alembic_upgrade "$VALID_INDEX_DB" c4a8b2d91e37
seed_legacy_data "$VALID_INDEX_DB"
"${psql_base[@]}" -d "$VALID_INDEX_DB" <<'SQL'
ALTER TABLE questions ADD COLUMN created_at timestamp DEFAULT now();
ALTER TABLE questions ADD COLUMN position integer;
WITH ranked AS (
    SELECT id, row_number() OVER (PARTITION BY assessment_id ORDER BY id) AS position
    FROM questions
)
UPDATE questions q SET position = ranked.position FROM ranked WHERE ranked.id = q.id;
ALTER TABLE questions ADD CONSTRAINT questions_position_not_null
    CHECK (position IS NOT NULL) NOT VALID;
ALTER TABLE questions VALIDATE CONSTRAINT questions_position_not_null;
ALTER TABLE questions ADD CONSTRAINT questions_created_at_not_null
    CHECK (created_at IS NOT NULL) NOT VALID;
CREATE UNIQUE INDEX CONCURRENTLY ix_questions_assessment_position
    ON questions (assessment_id, position);
SQL
alembic_upgrade "$VALID_INDEX_DB" head
assert_common_green "$VALID_INDEX_DB"
echo "C GREEN"

echo "=== ruff ==="
(
    cd "$CORE_DIR"
    .venv/bin/python -m ruff check --config ../ruff.toml \
        alembic/versions/a9f4c2e71b06_add_question_position_and_clone.py
)
echo "ALL GREEN"
