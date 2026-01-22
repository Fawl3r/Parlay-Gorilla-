"""Add verification_records table.

Revision ID: 026_add_verification_records
Revises: 299b00a5cc58
Create Date: 2026-01-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "026_add_verification_records"
down_revision = "299b00a5cc58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists (idempotent migration)
    # This handles the case where the table was created manually or migration was partially applied
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if "verification_records" in inspector.get_table_names():
        # Table already exists, skip creation but ensure indexes exist
        # Check and create indexes if they don't exist
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("verification_records")]
        
        if "idx_verification_records_user_id" not in existing_indexes:
            op.create_index("idx_verification_records_user_id", "verification_records", ["user_id"], unique=False)
        if "idx_verification_records_saved_parlay_id" not in existing_indexes:
            op.create_index("idx_verification_records_saved_parlay_id", "verification_records", ["saved_parlay_id"], unique=False)
        if "idx_verification_records_data_hash" not in existing_indexes:
            op.create_index("idx_verification_records_data_hash", "verification_records", ["data_hash"], unique=False)
        if "idx_verification_records_status" not in existing_indexes:
            op.create_index("idx_verification_records_status", "verification_records", ["status"], unique=False)
        if "idx_verification_records_user_created" not in existing_indexes:
            op.create_index(
                "idx_verification_records_user_created",
                "verification_records",
                ["user_id", "created_at"],
                unique=False,
            )
        if "idx_verification_records_saved_created" not in existing_indexes:
            op.create_index(
                "idx_verification_records_saved_created",
                "verification_records",
                ["saved_parlay_id", "created_at"],
                unique=False,
            )
        if "idx_verification_records_status_created" not in existing_indexes:
            op.create_index(
                "idx_verification_records_status_created",
                "verification_records",
                ["status", "created_at"],
                unique=False,
            )
        return
    
    op.create_table(
        "verification_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'queued'"), nullable=False),
        sa.Column("tx_digest", sa.String(length=128), nullable=True),
        sa.Column("object_id", sa.String(length=128), nullable=True),
        sa.Column("network", sa.String(length=20), server_default=sa.text("'mainnet'"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quota_consumed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("credits_consumed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_verification_records_user_id", "verification_records", ["user_id"], unique=False)
    op.create_index("idx_verification_records_saved_parlay_id", "verification_records", ["saved_parlay_id"], unique=False)
    op.create_index("idx_verification_records_data_hash", "verification_records", ["data_hash"], unique=False)
    op.create_index("idx_verification_records_status", "verification_records", ["status"], unique=False)
    op.create_index(
        "idx_verification_records_user_created",
        "verification_records",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_verification_records_saved_created",
        "verification_records",
        ["saved_parlay_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_verification_records_status_created",
        "verification_records",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_verification_records_status_created", table_name="verification_records")
    op.drop_index("idx_verification_records_saved_created", table_name="verification_records")
    op.drop_index("idx_verification_records_user_created", table_name="verification_records")
    op.drop_index("idx_verification_records_status", table_name="verification_records")
    op.drop_index("idx_verification_records_data_hash", table_name="verification_records")
    op.drop_index("idx_verification_records_saved_parlay_id", table_name="verification_records")
    op.drop_index("idx_verification_records_user_id", table_name="verification_records")
    op.drop_table("verification_records")


