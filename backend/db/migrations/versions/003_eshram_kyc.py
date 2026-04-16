"""add eshram fields to riders

Revision ID: 003_eshram_kyc
Revises: (initial migration — no prior revision)
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa

revision = "003_eshram_kyc"
down_revision = None   # This is the ONLY migration in this project.
                       # Setting this to "002" would reference a file that
                       # does not exist and break alembic upgrade head on
                       # a fresh database.
branch_labels = None
depends_on = None


def upgrade() -> None:
    # eshram_id: nullable because most riders won't have it immediately.
    # We intentionally omit unique=True here — the partial unique index
    # below is the sole uniqueness mechanism.  A full unique constraint
    # would treat multiple NULLs as duplicates on some databases, which
    # would incorrectly prevent multiple un-verified riders.
    op.add_column(
        "riders",
        sa.Column("eshram_id", sa.String(), nullable=True),
    )
    op.add_column(
        "riders",
        sa.Column("eshram_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "riders",
        sa.Column("eshram_income_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "riders",
        sa.Column(
            "eshram_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # Partial unique index: only enforce uniqueness for non-NULL values.
    # This lets many riders have eshram_id = NULL (not yet linked) while
    # preventing the same UAN being tied to two different rider accounts.
    op.create_index(
        "ix_riders_eshram_id",
        "riders",
        ["eshram_id"],
        unique=True,
        postgresql_where=sa.text("eshram_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_riders_eshram_id", table_name="riders")
    op.drop_column("riders", "eshram_verified_at")
    op.drop_column("riders", "eshram_income_verified")
    op.drop_column("riders", "eshram_verified")
    op.drop_column("riders", "eshram_id")
