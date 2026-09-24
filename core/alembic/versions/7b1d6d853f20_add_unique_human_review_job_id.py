"""add unique human review job id

Revision ID: 7b1d6d853f20
Revises: e1b02279b1a5
Create Date: 2026-09-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "7b1d6d853f20"
down_revision: Union[str, Sequence[str], None] = "e1b02279b1a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow exactly one human review per correction job.

    Política aprovada por Rafael (2026-09-24): esta migração NÃO apaga,
    altera nem escolhe entre registros duplicados existentes. Ela apenas
    verifica se algum job_id já possui mais de uma HumanReview e, se
    houver, INTERROMPE a migração com um diagnóstico claro (job_id,
    quantidade de linhas, ids envolvidos), sem tocar em nenhum dado.

    Saneamento de duplicatas pré-existentes é um procedimento SEPARADO,
    manual, com backup e validação, dependente de aprovação explícita de
    Rafael antes de qualquer execução — não faz parte desta migração.
    """
    connection = op.get_bind()
    duplicates = connection.exec_driver_sql(
        """
        SELECT job_id, COUNT(*) AS review_count,
               GROUP_CONCAT(id) AS review_ids
        FROM human_reviews
        GROUP BY job_id
        HAVING COUNT(*) > 1
        """
    ).fetchall() if connection.dialect.name == "sqlite" else connection.exec_driver_sql(
        """
        SELECT job_id, COUNT(*) AS review_count,
               STRING_AGG(id::text, ',') AS review_ids
        FROM human_reviews
        GROUP BY job_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    if duplicates:
        detail_lines = "\n".join(
            f"  - job_id={row[0]} review_count={row[1]} review_ids=[{row[2]}]"
            for row in duplicates
        )
        raise RuntimeError(
            "Migração 7b1d6d853f20 interrompida: existem HumanReview "
            "duplicadas para o(s) seguinte(s) job_id (nenhum dado foi "
            "apagado, alterado ou escolhido por esta migração):\n"
            f"{detail_lines}\n"
            "Saneie essas duplicatas por um procedimento separado, "
            "explícito e aprovado por Rafael (com backup e validação) "
            "antes de reexecutar esta migração."
        )

    with op.batch_alter_table("human_reviews") as batch_op:
        batch_op.create_unique_constraint(
            "uq_human_reviews_job_id", ["job_id"]
        )


def downgrade() -> None:
    """Remove the one-review-per-job constraint."""
    with op.batch_alter_table("human_reviews") as batch_op:
        batch_op.drop_constraint(
            "uq_human_reviews_job_id", type_="unique"
        )
