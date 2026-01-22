"""Add parlay_fingerprint idempotency key to verification_records.

Revision ID: 027_add_parlay_fingerprint_to_verification_records
Revises: 026_add_verification_records
Create Date: 2026-01-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "027_add_parlay_fingerprint_to_verification_records"
down_revision = "026_add_verification_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists (idempotent migration)
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns("verification_records")]
    
    # Add parlay_fingerprint column if it doesn't exist
    if "parlay_fingerprint" not in existing_columns:
        op.add_column("verification_records", sa.Column("parlay_fingerprint", sa.String(length=64), nullable=True))

    # Allow records that are not linked to a saved parlay (automatic custom parlay verification).
    # Check if saved_parlay_id is already nullable
    saved_parlay_col = next((col for col in inspector.get_columns("verification_records") if col["name"] == "saved_parlay_id"), None)
    if saved_parlay_col and not saved_parlay_col.get("nullable", False):
        op.alter_column(
            "verification_records",
            "saved_parlay_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=True,
        )

    # DB-level hard stop: one proof per fingerprint (NULLs allowed for legacy/saved-parlay records).
    # Check if constraint already exists
    existing_constraints = [con["name"] for con in inspector.get_unique_constraints("verification_records")]
    if "unique_verification_records_parlay_fingerprint" not in existing_constraints:
        op.create_unique_constraint(
            "unique_verification_records_parlay_fingerprint",
            "verification_records",
            ["parlay_fingerprint"],
        )


def downgrade() -> None:
    op.drop_constraint(
        "unique_verification_records_parlay_fingerprint",
        "verification_records",
        type_="unique",
    )

    op.alter_column(
        "verification_records",
        "saved_parlay_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_column("verification_records", "parlay_fingerprint")


