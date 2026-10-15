"""add answer image logical deletion fields (BL-AV-4B-05, 1ª fatia)

Revision ID: b8d3e5f7a2c4
Revises: f2a9c4e6b1d3
Create Date: 2026-10-15 00:00:00.000000

D1: exclusão lógica reversível de imagens de resposta. Mudança puramente
aditiva: duas colunas anuláveis (`deleted_at`, `deleted_by_id` com FK para
users), sem backfill. Não há `storage_deleted_at` nem remoção física nesta
fatia (D1/D3). O downgrade recusa remover as colunas enquanto houver imagem
logicamente excluída, para não reativá-la silenciosamente nem descartar o
registro de quem a excluiu.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8d3e5f7a2c4"
down_revision: Union[str, Sequence[str], None] = "f2a9c4e6b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_NAME = "fk_answer_images_deleted_by_id_users"


def upgrade() -> None:
    op.add_column("answer_images", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("answer_images", sa.Column("deleted_by_id", sa.String(), nullable=True))
    op.create_foreign_key(_FK_NAME, "answer_images", "users", ["deleted_by_id"], ["id"])


def downgrade() -> None:
    connection = op.get_bind()
    if connection.exec_driver_sql(
        "SELECT EXISTS (SELECT 1 FROM answer_images WHERE deleted_at IS NOT NULL "
        "OR deleted_by_id IS NOT NULL)"
    ).scalar():
        raise RuntimeError(
            "Downgrade b8d3e5f7a2c4 bloqueado antes de qualquer DROP: existem imagens de resposta "
            "excluídas logicamente. Remover as colunas reativaria essas imagens e descartaria quem "
            "as excluiu. Restaure-as ou preserve/exporte esse estado por um procedimento separado "
            "e autorizado antes de tentar novamente."
        )

    op.drop_constraint(_FK_NAME, "answer_images", type_="foreignkey")
    op.drop_column("answer_images", "deleted_by_id")
    op.drop_column("answer_images", "deleted_at")
