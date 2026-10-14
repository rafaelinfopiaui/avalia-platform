"""add answer images (AV-S06B)

Revision ID: d5e3a7c19f42
Revises: a9f4c2e71b06
Create Date: 2026-10-14 00:00:00.000000

Only metadata lives in the database; the image bytes are stored on local disk
under Settings.answer_images_storage_dir. Downgrade refuses to drop the table
while rows exist, so metadata is never silently detached from stored files.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5e3a7c19f42"
down_revision: Union[str, Sequence[str], None] = "a9f4c2e71b06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "answer_images",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("answer_id", sa.String(), nullable=False),
        sa.Column("storage_filename", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(), nullable=False),
        sa.Column("uploaded_by_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_answer_images_answer_id"), "answer_images", ["answer_id"])


def downgrade() -> None:
    has_rows = op.get_bind().execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM answer_images)")
    ).scalar()
    if has_rows:
        raise RuntimeError(
            "answer_images contém registros; downgrade recusado para não "
            "desvincular metadados de arquivos armazenados."
        )
    op.drop_index(op.f("ix_answer_images_answer_id"), table_name="answer_images")
    op.drop_table("answer_images")
