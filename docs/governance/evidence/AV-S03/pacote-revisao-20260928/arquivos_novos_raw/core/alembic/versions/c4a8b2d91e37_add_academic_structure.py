"""add academic structure

Revision ID: c4a8b2d91e37
Revises: 7b1d6d853f20
Create Date: 2026-09-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4a8b2d91e37"
down_revision: Union[str, Sequence[str], None] = "7b1d6d853f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "courses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_courses_organization_code"),
    )
    op.create_table(
        "disciplines",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_disciplines_organization_code"),
    )
    op.create_table(
        "course_disciplines",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("course_id", sa.String(), nullable=False),
        sa.Column("discipline_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "discipline_id", name="uq_course_disciplines_pair"),
    )
    op.create_table(
        "class_groups",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("course_discipline_id", sa.String(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["course_discipline_id"], ["course_disciplines.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "course_discipline_id",
            "period",
            "code",
            name="uq_class_groups_curriculum_period_code",
        ),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "external_id", name="uq_students_organization_external"
        ),
    )
    op.create_table(
        "enrollments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("class_group_id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", "WITHDRAWN", "COMPLETED", name="enrollmentstatus"),
            nullable=False,
        ),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["class_group_id"], ["class_groups.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "professor_class_links",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("professor_id", sa.String(), nullable=False),
        sa.Column("class_group_id", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("responsible", "collaborator", name="professorrole"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["professor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["class_group_id"], ["class_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "professor_id", "class_group_id", "role", name="uq_professor_class_links_role"
        ),
    )
    op.add_column("assessments", sa.Column("class_group_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_assessments_class_group_id",
        "assessments",
        "class_groups",
        ["class_group_id"],
        ["id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    blockers = []
    checks = (
        ("organizations", "SELECT EXISTS (SELECT 1 FROM organizations)"),
        ("courses", "SELECT EXISTS (SELECT 1 FROM courses)"),
        ("disciplines", "SELECT EXISTS (SELECT 1 FROM disciplines)"),
        ("course_disciplines", "SELECT EXISTS (SELECT 1 FROM course_disciplines)"),
        ("class_groups", "SELECT EXISTS (SELECT 1 FROM class_groups)"),
        ("students", "SELECT EXISTS (SELECT 1 FROM students)"),
        ("enrollments", "SELECT EXISTS (SELECT 1 FROM enrollments)"),
        ("professor_class_links", "SELECT EXISTS (SELECT 1 FROM professor_class_links)"),
        (
            "assessments.class_group_id",
            "SELECT EXISTS (SELECT 1 FROM assessments WHERE class_group_id IS NOT NULL)",
        ),
    )
    for label, query in checks:
        if connection.exec_driver_sql(query).scalar():
            blockers.append(label)

    if blockers:
        raise RuntimeError(
            "Downgrade c4a8b2d91e37 bloqueado antes de qualquer DROP: existem dados "
            f"dependentes em {', '.join(blockers)}. Preserve/exporte esses dados por um "
            "procedimento separado e autorizado antes de tentar novamente."
        )

    op.drop_constraint("fk_assessments_class_group_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "class_group_id")
    op.drop_table("professor_class_links")
    op.drop_table("enrollments")
    op.drop_table("students")
    op.drop_table("class_groups")
    op.drop_table("course_disciplines")
    op.drop_table("disciplines")
    op.drop_table("courses")
    op.drop_table("organizations")

    sa.Enum(name="professorrole").drop(connection, checkfirst=True)
    sa.Enum(name="enrollmentstatus").drop(connection, checkfirst=True)
