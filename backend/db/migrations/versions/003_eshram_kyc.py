"""add eshram fields to riders

Revision ID: 003_eshram_kyc
Revises: 002  (update this to your actual previous revision ID)
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa

revision = "003_eshram_kyc"
down_revision = "002"   # UPDATE to your actual previous migration revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "riders",
        sa.Column("eshram_id", sa.String(), nullable=True, unique=True),
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
    # Unique index on eshram_id for deduplication enforcement
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
