"""add question position and assessment clone provenance

Revision ID: a9f4c2e71b06
Revises: c4a8b2d91e37
Create Date: 2026-10-01 00:00:00.000000

The concurrent index build commits the preceding DDL. Consequently, every
step must accept a compatible checkpoint left by an interrupted attempt,
while rejecting objects that reuse an expected name with another definition.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.engine import Connection, RowMapping

from alembic import op

revision: str = "a9f4c2e71b06"
down_revision: Union[str, Sequence[str], None] = "c4a8b2d91e37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEX_NAME = "ix_questions_assessment_position"
_UNIQUE_NAME = "uq_questions_assessment_position"


def _column(bind: Connection, table: str, column: str) -> RowMapping | None:
    return bind.execute(
        sa.text(
            "SELECT udt_name, is_nullable, column_default, character_maximum_length "
            "FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :table "
            "AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).mappings().one_or_none()


def _require_compatible_column(
    bind: Connection,
    table: str,
    column: str,
    expected_udt: str,
) -> RowMapping | None:
    existing = _column(bind, table, column)
    if existing is not None and existing["udt_name"] != expected_udt:
        raise RuntimeError(
            f"Incompatible checkpoint: {table}.{column} has PostgreSQL type "
            f"{existing['udt_name']!r}; expected {expected_udt!r}."
        )
    return existing


def _require_default(
    column: RowMapping,
    qualified_name: str,
    expected: str | None,
) -> None:
    actual = column["column_default"]
    normalized = None if actual is None else "".join(actual.lower().split())
    accepted = {expected} if expected is None else {"now()", "current_timestamp"}
    if normalized not in accepted:
        raise RuntimeError(
            f"Incompatible checkpoint: {qualified_name} has default {actual!r}; "
            f"expected {expected!r}."
        )


def _constraint(bind: Connection, table: str, name: str) -> RowMapping | None:
    return bind.execute(
        sa.text(
            "SELECT n.nspname AS table_schema, c.contype, c.convalidated, "
            "pg_get_constraintdef(c.oid) AS definition, "
            "pg_get_expr(c.conbin, c.conrelid) AS check_expression, "
            "ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) "
            " JOIN pg_attribute AS a ON a.attrelid = c.conrelid AND a.attnum = k.attnum "
            " ORDER BY k.ord) AS columns, rt.relname AS referenced_table, "
            "ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY AS k(attnum, ord) "
            " JOIN pg_attribute AS a ON a.attrelid = c.confrelid AND a.attnum = k.attnum "
            " ORDER BY k.ord) AS referenced_columns, rn.nspname AS referenced_schema, "
            "c.confdeltype, c.confupdtype, c.confmatchtype, "
            "c.condeferrable, c.condeferred, "
            "CASE WHEN c.conindid = 0 THEN NULL ELSE i.indisvalid END AS index_valid "
            "FROM pg_constraint AS c "
            "JOIN pg_class AS t ON t.oid = c.conrelid "
            "JOIN pg_namespace AS n ON n.oid = t.relnamespace "
            "LEFT JOIN pg_index AS i ON i.indexrelid = c.conindid "
            "LEFT JOIN pg_class AS rt ON rt.oid = c.confrelid "
            "LEFT JOIN pg_namespace AS rn ON rn.oid = rt.relnamespace "
            "WHERE n.nspname = current_schema() AND t.relname = :table "
            "AND c.conname = :name"
        ),
        {"table": table, "name": name},
    ).mappings().one_or_none()


def _ensure_not_null(
    bind: Connection,
    table: str,
    column: str,
    check_name: str,
) -> None:
    existing_column = _column(bind, table, column)
    if existing_column is None:
        raise RuntimeError(f"Missing required checkpoint column {table}.{column}.")

    check = _constraint(bind, table, check_name)
    if check is not None:
        expression = check["check_expression"] or ""
        normalized = "".join(
            character
            for character in expression.lower()
            if character not in '()" \t\r\n'
        )
        if (
            check["contype"] != "c"
            or list(check["columns"]) != [column]
            or normalized != f"{column.lower()}isnotnull"
        ):
            raise RuntimeError(
                f"Incompatible checkpoint: constraint {check_name!r} is "
                f"{check['definition']!r}."
            )

    if existing_column["is_nullable"] == "NO":
        if check is not None:
            op.drop_constraint(check_name, table, type_="check")
        return

    if check is None:
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {check_name} "
            f"CHECK ({column} IS NOT NULL) NOT VALID"
        )
        check = _constraint(bind, table, check_name)
    if check is None:
        raise RuntimeError(f"Failed to create checkpoint constraint {check_name!r}.")
    if not check["convalidated"]:
        op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {check_name}")
    op.alter_column(table, column, nullable=False)
    op.drop_constraint(check_name, table, type_="check")


def _index(bind: Connection, name: str) -> RowMapping | None:
    return bind.execute(
        sa.text(
            "SELECT c.relkind, t.relname AS indexed_table, i.indisunique, "
            "i.indisvalid, i.indisready, "
            "i.indpred IS NULL AS no_predicate, i.indexprs IS NULL AS no_expressions, "
            "am.amname, ARRAY("
            " SELECT a.attname FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)"
            " JOIN pg_attribute AS a ON a.attrelid = i.indrelid AND a.attnum = k.attnum"
            " ORDER BY k.ord"
            ") AS columns "
            "FROM pg_class AS c "
            "JOIN pg_namespace AS n ON n.oid = c.relnamespace "
            "LEFT JOIN pg_index AS i ON i.indexrelid = c.oid "
            "LEFT JOIN pg_class AS t ON t.oid = i.indrelid "
            "LEFT JOIN pg_am AS am ON am.oid = c.relam "
            "WHERE n.nspname = current_schema() AND c.relname = :name"
        ),
        {"name": name},
    ).mappings().one_or_none()


def _is_expected_index_shape(index: RowMapping) -> bool:
    return bool(
        index["relkind"] in {"i", "I"}
        and index["indexed_table"] == "questions"
        and index["indisunique"]
        and index["no_predicate"]
        and index["no_expressions"]
        and index["amname"] == "btree"
        and list(index["columns"]) == ["assessment_id", "position"]
    )


def _unique_constraint_complete(bind: Connection) -> bool:
    unique = _constraint(bind, "questions", _UNIQUE_NAME)
    if unique is None:
        return False
    if (
        unique["contype"] != "u"
        or list(unique["columns"]) != ["assessment_id", "position"]
        or not unique["index_valid"]
        or unique["condeferrable"]
        or unique["condeferred"]
    ):
        raise RuntimeError(
            f"Incompatible checkpoint: constraint {_UNIQUE_NAME!r} is "
            f"{unique['definition']!r} (index_valid={unique['index_valid']!r})."
        )
    return True


def _ensure_unique_constraint(bind: Connection) -> None:
    if _unique_constraint_complete(bind):
        return

    index = _index(bind, _INDEX_NAME)
    if index is not None and index["relkind"] not in {"i", "I"}:
        raise RuntimeError(
            f"Incompatible checkpoint: {_INDEX_NAME!r} exists but is not an index."
        )

    if index is not None and not _is_expected_index_shape(index):
        raise RuntimeError(
            f"Incompatible checkpoint: index {_INDEX_NAME!r} is not the expected "
            "unique btree index on questions (assessment_id, position)."
        )

    if index is not None and not index["indisvalid"]:
        with op.get_context().autocommit_block():
            op.execute(f"DROP INDEX CONCURRENTLY {_INDEX_NAME}")
        index = None

    if index is not None and not index["indisready"]:
        raise RuntimeError(
            f"Incompatible checkpoint: valid index {_INDEX_NAME!r} is not ready."
        )

    if index is None:
        with op.get_context().autocommit_block():
            op.execute(
                f"CREATE UNIQUE INDEX CONCURRENTLY {_INDEX_NAME} "
                "ON questions (assessment_id, position)"
            )

    op.execute(
        f"ALTER TABLE questions ADD CONSTRAINT {_UNIQUE_NAME} "
        f"UNIQUE USING INDEX {_INDEX_NAME}"
    )


def _ensure_clone_provenance(bind: Connection) -> None:
    cloned_from = _require_compatible_column(bind, "assessments", "cloned_from_id", "varchar")
    if cloned_from is None:
        op.add_column("assessments", sa.Column("cloned_from_id", sa.String(), nullable=True))
    else:
        if cloned_from["is_nullable"] != "YES":
            raise RuntimeError(
                "Incompatible checkpoint: assessments.cloned_from_id must be nullable."
            )
        if cloned_from["character_maximum_length"] is not None:
            raise RuntimeError(
                "Incompatible checkpoint: assessments.cloned_from_id must be unbounded varchar."
            )
        _require_default(cloned_from, "assessments.cloned_from_id", None)

    foreign_key = _constraint(bind, "assessments", "fk_assessments_cloned_from_id")
    if foreign_key is not None:
        if (
            foreign_key["contype"] != "f"
            or list(foreign_key["columns"]) != ["cloned_from_id"]
            or foreign_key["referenced_schema"] != foreign_key["table_schema"]
            or foreign_key["referenced_table"] != "assessments"
            or list(foreign_key["referenced_columns"]) != ["id"]
            or foreign_key["confdeltype"] != "a"
            or foreign_key["confupdtype"] != "a"
            or foreign_key["confmatchtype"] != "s"
            or foreign_key["condeferrable"]
            or foreign_key["condeferred"]
        ):
            raise RuntimeError(
                "Incompatible checkpoint: constraint 'fk_assessments_cloned_from_id' "
                f"is {foreign_key['definition']!r}."
            )
        if not foreign_key["convalidated"]:
            op.execute(
                "ALTER TABLE assessments VALIDATE CONSTRAINT "
                "fk_assessments_cloned_from_id"
            )
        return

    op.create_foreign_key(
        "fk_assessments_cloned_from_id",
        "assessments",
        "assessments",
        ["cloned_from_id"],
        ["id"],
    )


def upgrade() -> None:
    bind = op.get_bind()

    # Mandatory evidence query: do not infer legacy cardinality from the old API.
    multiple_assessments = bind.execute(
        sa.text(
            "SELECT assessment_id, COUNT(*) AS total "
            "FROM questions GROUP BY assessment_id HAVING COUNT(*) > 1"
        )
    ).fetchall()

    created_at = _require_compatible_column(bind, "questions", "created_at", "timestamp")
    if created_at is None:
        op.add_column(
            "questions",
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )
    else:
        _require_default(created_at, "questions.created_at", "now()")
    position = _require_compatible_column(bind, "questions", "position", "int4")
    if position is None:
        op.add_column("questions", sa.Column("position", sa.Integer(), nullable=True))
    else:
        _require_default(position, "questions.position", None)

    # Historical Question rows had no timestamp. The parent Assessment CREATE
    # audit event is the best available approximation; it is not asserted to be
    # the exact question creation time. The question id remains the final stable
    # tiebreaker when siblings share that approximation.
    bind.execute(
        sa.text(
            "UPDATE questions AS q SET created_at = COALESCE(("
            " SELECT MIN(ae.created_at) FROM audit_events AS ae"
            " WHERE ae.resource_type = 'Assessment' AND ae.action = 'CREATE'"
            " AND ae.resource_id = q.assessment_id"
            "), q.created_at)"
        )
    )

    if multiple_assessments:
        bind.execute(
            sa.text(
                "WITH ranked AS ("
                " SELECT id, ROW_NUMBER() OVER (PARTITION BY assessment_id "
                "ORDER BY created_at ASC, id ASC) AS position"
                " FROM questions"
                ") UPDATE questions AS q SET position = ranked.position"
                " FROM ranked WHERE ranked.id = q.id"
            )
        )
    else:
        bind.execute(sa.text("UPDATE questions SET position = 1"))

    _ensure_not_null(bind, "questions", "position", "questions_position_not_null")
    _ensure_not_null(bind, "questions", "created_at", "questions_created_at_not_null")
    _ensure_unique_constraint(bind)
    _ensure_clone_provenance(bind)


def downgrade() -> None:
    op.drop_constraint("fk_assessments_cloned_from_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "cloned_from_id")
    op.drop_constraint("uq_questions_assessment_position", "questions", type_="unique")
    op.drop_column("questions", "position")
    op.drop_column("questions", "created_at")
