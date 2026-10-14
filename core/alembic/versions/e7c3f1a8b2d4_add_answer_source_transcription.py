"""add answer source and transcription status (AV-S06B, resposta por imagem)

Revision ID: e7c3f1a8b2d4
Revises: d5e3a7c19f42
Create Date: 2026-10-14 00:00:00.000000

DEC-AV-037: a foto pode ser a entrada inicial da resposta, sem texto. Por isso
`answers.text` passa a aceitar NULL, governado por um invariante de origem
(`source`) e por um estado de transcrição. Todas as linhas existentes são
respostas digitadas: o backfill as marca, de forma determinística, como
`TEXT`/`TRANSCRICAO_CONFIRMADA`. O downgrade recusa voltar `text` a NOT NULL
enquanto houver resposta sem texto, para não descartar dado.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7c3f1a8b2d4"
down_revision: Union[str, Sequence[str], None] = "d5e3a7c19f42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ANSWER_SOURCE = sa.Enum("TEXT", "IMAGE", name="answersource")
_TRANSCRIPTION_STATUS = sa.Enum(
    "AGUARDANDO_TRANSCRICAO", "TRANSCRICAO_CONFIRMADA", name="transcriptionstatus"
)
_CHECK_NAME = "ck_answers_source_text"


def upgrade() -> None:
    connection = op.get_bind()
    _ANSWER_SOURCE.create(connection, checkfirst=True)
    _TRANSCRIPTION_STATUS.create(connection, checkfirst=True)

    # Colunas nascem anuláveis só para permitir o backfill; logo depois viram NOT NULL.
    op.add_column(
        "answers",
        sa.Column(
            "source",
            sa.Enum("TEXT", "IMAGE", name="answersource", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "answers",
        sa.Column(
            "transcription_status",
            sa.Enum(
                "AGUARDANDO_TRANSCRICAO",
                "TRANSCRICAO_CONFIRMADA",
                name="transcriptionstatus",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE answers SET source = 'TEXT', transcription_status = 'TRANSCRICAO_CONFIRMADA'"
    )
    op.alter_column("answers", "source", nullable=False)
    op.alter_column("answers", "transcription_status", nullable=False)
    op.alter_column("answers", "text", existing_type=sa.Text(), nullable=True)
    op.create_check_constraint(
        _CHECK_NAME,
        "answers",
        "(source = 'TEXT' AND text IS NOT NULL) OR (source = 'IMAGE')",
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.exec_driver_sql("SELECT EXISTS (SELECT 1 FROM answers WHERE text IS NULL)").scalar():
        raise RuntimeError(
            "Downgrade e7c3f1a8b2d4 bloqueado antes de qualquer DROP: existem respostas "
            "sem texto (respostas por imagem aguardando transcrição). Voltar answers.text "
            "para NOT NULL descartaria esse estado. Preserve/exporte esses dados por um "
            "procedimento separado e autorizado antes de tentar novamente."
        )

    op.drop_constraint(_CHECK_NAME, "answers", type_="check")
    op.alter_column("answers", "text", existing_type=sa.Text(), nullable=False)
    op.drop_column("answers", "transcription_status")
    op.drop_column("answers", "source")

    _TRANSCRIPTION_STATUS.drop(connection, checkfirst=True)
    _ANSWER_SOURCE.drop(connection, checkfirst=True)
