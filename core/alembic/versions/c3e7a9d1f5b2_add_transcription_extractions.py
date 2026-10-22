"""add transcription_extractions (AV-S07B, extração OCR/visão experimental)

Revision ID: c3e7a9d1f5b2
Revises: b8d3e5f7a2c4
Create Date: 2026-10-22 00:00:00.000000

DEC-AV-046: registra cada extração automática de texto de uma imagem de
resposta (motor, modelo, configuração, estado, saída bruta, duração e erro),
vinculada à resposta e à imagem usada. Mudança puramente aditiva: cria só a
tabela nova, sem backfill e sem tocar tabelas existentes. O downgrade remove
apenas essa tabela.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3e7a9d1f5b2"
down_revision: Union[str, Sequence[str], None] = "b8d3e5f7a2c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transcription_extractions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("answer_id", sa.String(), nullable=False),
        sa.Column("answer_image_id", sa.String(), nullable=False),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("raw_output", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error_detail", sa.Text(), nullable=True),
        # Proveniência REAL do rascunho: quando esta extração preenche o
        # rascunho, grava a versão RESULTANTE de transcription_version do
        # answer. Permite derivar a origem (OCR / OCR_EDITADO / MANUAL) por
        # VERSÃO, nunca por coincidência de texto. NULL = extração não preencheu
        # o rascunho (vazio, falha, rascunho já ocupado, ou resposta alterada).
        sa.Column("resulting_transcription_version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"]),
        sa.ForeignKeyConstraint(["answer_image_id"], ["answer_images.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transcription_extractions_answer_id"),
        "transcription_extractions",
        ["answer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transcription_extractions_answer_id"), table_name="transcription_extractions")
    op.drop_table("transcription_extractions")
