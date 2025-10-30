"""Add config tables only

Revision ID: e0f547d23bf2
Revises: 354afcc93d90
Create Date: 2025-10-29 22:33:25.818806

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0f547d23bf2"
down_revision: Union[str, None] = "354afcc93d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Création de la table genealogy_configs
    op.create_table(
        "genealogy_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("genealogy_id", sa.Integer(), nullable=False),
        sa.Column("body_prop", sa.String(length=255), nullable=True),
        sa.Column("default_lang", sa.String(length=10), nullable=True),
        sa.Column("trailer", sa.Text(), nullable=True),
        sa.Column("max_anc_level", sa.Integer(), nullable=True),
        sa.Column("max_desc_level", sa.Integer(), nullable=True),
        sa.Column("max_anc_tree", sa.Integer(), nullable=True),
        sa.Column("max_desc_tree", sa.Integer(), nullable=True),
        sa.Column("history", sa.Boolean(), nullable=True),
        sa.Column("hide_advanced_request", sa.Boolean(), nullable=True),
        sa.Column("images_path", sa.String(length=255), nullable=True),
        sa.Column("friend_passwd", sa.String(length=255), nullable=True),
        sa.Column("wizard_passwd", sa.String(length=255), nullable=True),
        sa.Column("wizard_just_friend", sa.Boolean(), nullable=True),
        sa.Column("hide_private_names", sa.Boolean(), nullable=True),
        sa.Column("can_send_image", sa.Boolean(), nullable=True),
        sa.Column("renamed", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["genealogy_id"],
            ["genealogies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_genealogy_configs_genealogy_id"),
        "genealogy_configs",
        ["genealogy_id"],
        unique=True,
    )

    # Création de la table server_configs
    op.create_table(
        "server_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("default_lang", sa.String(length=10), nullable=True),
        sa.Column("only", sa.String(length=255), nullable=True),
        sa.Column("log", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Suppression des tables
    op.drop_index(
        op.f("ix_genealogy_configs_genealogy_id"), table_name="genealogy_configs"
    )
    op.drop_table("genealogy_configs")
    op.drop_table("server_configs")
