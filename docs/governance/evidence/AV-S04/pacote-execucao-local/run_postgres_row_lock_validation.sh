#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
CORE_DIR="$ROOT_DIR/core"
PY_SCRIPT="$ROOT_DIR/docs/governance/evidence/AV-S04/pacote-execucao-local/validate_postgres_row_lock.py"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
CLUSTER_DIR="$(mktemp -d /private/tmp/av_s04_migration_lock_pg16.XXXXXX)"
SOCKET_DIR="$CLUSTER_DIR/socket"
LOG_FILE="$CLUSTER_DIR/postgres.log"
DATABASE_NAME="av_s04_migration_row_lock"

if [[ "$DATABASE_NAME" == "avalia_dev" || "$DATABASE_NAME" != av_s04_migration_* ]]; then
    echo "REFUSED unsafe database name: $DATABASE_NAME" >&2
    exit 64
fi

cleanup() {
    "$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" -m fast stop >/dev/null 2>&1 || true
    if [[ "$CLUSTER_DIR" == /private/tmp/av_s04_migration_lock_pg16.* ]]; then
        rm -rf "$CLUSTER_DIR"
    else
        echo "REFUSED unsafe cluster cleanup path: $CLUSTER_DIR" >&2
    fi
}
trap cleanup EXIT

mkdir "$SOCKET_DIR"
"$PG_BIN/initdb" -D "$CLUSTER_DIR/data" --auth=trust --no-locale --encoding=UTF8 \
    -c shared_memory_type=mmap -c dynamic_shared_memory_type=mmap >/dev/null
"$PG_BIN/pg_ctl" -D "$CLUSTER_DIR/data" -l "$LOG_FILE" -o \
    "-k $SOCKET_DIR -c listen_addresses=''" start >/dev/null
"$PG_BIN/createdb" -h "$SOCKET_DIR" "$DATABASE_NAME"
DATABASE_URL="postgresql+psycopg2:///$DATABASE_NAME?host=$SOCKET_DIR"

(
    cd "$CORE_DIR"
    DATABASE_URL="$DATABASE_URL" .venv/bin/python -m alembic upgrade head
    DATABASE_URL="$DATABASE_URL" JWT_SECRET="av-s04-isolated-test-secret" \
        PYTHONPATH="$CORE_DIR" .venv/bin/python "$PY_SCRIPT"
)
