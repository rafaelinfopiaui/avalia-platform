"""add answer manual transcription fields (AV-S08B)

Revision ID: f2a9c4e6b1d3
Revises: e7c3f1a8b2d4
Create Date: 2026-10-14 00:00:00.000000

DEC-AV-040: o professor digita a transcrição de uma resposta por imagem, salva
rascunhos (um rascunho atual por resposta) e confirma explicitamente o texto
final. Mudança puramente aditiva: três colunas anuláveis e um contador de
versão (lock otimista) com default 0 no servidor, que cobre as linhas
existentes sem backfill. O downgrade recusa remover as colunas enquanto houver
rascunho, confirmação registrada ou versão avançada, para não descartar dado.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a9c4e6b1d3"
down_revision: Union[str, Sequence[str], None] = "e7c3f1a8b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_NAME = "fk_answers_transcription_confirmed_by_id_users"


def upgrade() -> None:
    op.add_column("answers", sa.Column("manual_transcription_draft", sa.Text(), nullable=True))
    op.add_column("answers", sa.Column("transcription_confirmed_by_id", sa.String(), nullable=True))
    op.add_column("answers", sa.Column("transcription_confirmed_at", sa.DateTime(), nullable=True))
    op.add_column(
        "answers",
        sa.Column("transcription_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(_FK_NAME, "answers", "users", ["transcription_confirmed_by_id"], ["id"])


def downgrade() -> None:
    connection = op.get_bind()
    if connection.exec_driver_sql(
        "SELECT EXISTS (SELECT 1 FROM answers WHERE manual_transcription_draft IS NOT NULL "
        "OR transcription_confirmed_by_id IS NOT NULL OR transcription_version <> 0)"
    ).scalar():
        raise RuntimeError(
            "Downgrade f2a9c4e6b1d3 bloqueado antes de qualquer DROP: existem respostas com "
            "rascunho de transcrição, confirmação registrada ou versão de transcrição avançada. "
            "Remover as colunas descartaria esse estado. Preserve/exporte esses dados por um "
            "procedimento separado e autorizado antes de tentar novamente."
        )

    op.drop_constraint(_FK_NAME, "answers", type_="foreignkey")
    op.drop_column("answers", "transcription_version")
    op.drop_column("answers", "transcription_confirmed_at")
    op.drop_column("answers", "transcription_confirmed_by_id")
    op.drop_column("answers", "manual_transcription_draft")
