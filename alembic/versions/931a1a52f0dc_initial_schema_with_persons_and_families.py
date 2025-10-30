"""Initial schema with persons and families

Revision ID: 931a1a52f0dc
Revises:
Create Date: 2025-10-29 02:02:29.025190

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "931a1a52f0dc"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create persons table
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("surname", sa.String(length=100), nullable=False),
        sa.Column("sex", sa.String(length=1), nullable=True),
        sa.Column("birth_date", sa.String(length=50), nullable=True),
        sa.Column("birth_place", sa.String(length=200), nullable=True),
        sa.Column("death_date", sa.String(length=50), nullable=True),
        sa.Column("death_place", sa.String(length=200), nullable=True),
        sa.Column("occupation", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("public_name", sa.String(length=100), nullable=True),
        sa.Column("qualifier", sa.String(length=50), nullable=True),
        sa.Column("alias", sa.String(length=100), nullable=True),
        sa.Column("image", sa.String(length=200), nullable=True),
        sa.Column("baptism_date", sa.String(length=50), nullable=True),
        sa.Column("baptism_place", sa.String(length=200), nullable=True),
        sa.Column("burial_date", sa.String(length=50), nullable=True),
        sa.Column("burial_place", sa.String(length=200), nullable=True),
        sa.Column("access", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_persons_first_name"), "persons", ["first_name"], unique=False
    )
    op.create_index(op.f("ix_persons_surname"), "persons", ["surname"], unique=False)

    # Create families table
    op.create_table(
        "families",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("father_id", sa.Integer(), nullable=True),
        sa.Column("mother_id", sa.Integer(), nullable=True),
        sa.Column("marriage_date", sa.String(length=50), nullable=True),
        sa.Column("marriage_place", sa.String(length=200), nullable=True),
        sa.Column("divorce_date", sa.String(length=50), nullable=True),
        sa.Column("marriage_note", sa.Text(), nullable=True),
        sa.Column("marriage_src", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["father_id"],
            ["persons.id"],
        ),
        sa.ForeignKeyConstraint(
            ["mother_id"],
            ["persons.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_families_father_id"), "families", ["father_id"], unique=False
    )
    op.create_index(
        op.f("ix_families_mother_id"), "families", ["mother_id"], unique=False
    )

    # Create children association table
    op.create_table(
        "family_children",
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["families.id"],
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
        ),
        sa.PrimaryKeyConstraint("family_id", "person_id"),
    )

    # Create places table
    op.create_table(
        "places",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_places_name"), "places", ["name"], unique=False)

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("family_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("date", sa.String(length=50), nullable=True),
        sa.Column("place", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["families.id"],
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_events_event_type"), "events", ["event_type"], unique=False
    )
    op.create_index(op.f("ix_events_person_id"), "events", ["person_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_events_person_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_places_name"), table_name="places")
    op.drop_table("places")
    op.drop_table("family_children")
    op.drop_index(op.f("ix_families_mother_id"), table_name="families")
    op.drop_index(op.f("ix_families_father_id"), table_name="families")
    op.drop_table("families")
    op.drop_index(op.f("ix_persons_surname"), table_name="persons")
    op.drop_index(op.f("ix_persons_first_name"), table_name="persons")
    op.drop_table("persons")
