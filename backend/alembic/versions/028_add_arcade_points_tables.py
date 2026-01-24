"""Add arcade_points_events and arcade_points_totals tables.

Revision ID: 028_add_arcade_points_tables
Revises: 027_add_parlay_fingerprint_to_verification_records
Create Date: 2025-01-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "028_add_arcade_points_tables"
down_revision = "027_add_parlay_fingerprint_to_verification_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    from sqlalchemy.exc import ProgrammingError
    
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())
    existing_indexes = {}
    for table_name in existing_tables:
        try:
            existing_indexes[table_name] = [idx["name"] for idx in inspector.get_indexes(table_name)]
        except Exception:
            existing_indexes[table_name] = []
    
    # Arcade points events (one row per awarded win)
    # Use try-except for extra safety in case inspector check fails
    if "arcade_points_events" not in existing_tables:
        try:
            op.create_table(
                "arcade_points_events",
                sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("saved_parlay_result_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("num_legs", sa.Integer(), nullable=False),
                sa.Column("points_awarded", sa.Integer(), nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
                sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"], ondelete="CASCADE"),
                sa.ForeignKeyConstraint(["saved_parlay_result_id"], ["saved_parlay_results.id"], ondelete="CASCADE"),
                sa.PrimaryKeyConstraint("id"),
                sa.UniqueConstraint("saved_parlay_result_id", name="unique_arcade_points_event_result"),
            )
        except ProgrammingError as e:
            # Table might exist even if inspector didn't catch it
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                raise
            # Table exists, continue with index creation
            pass

    # Ensure indexes exist (safe to run multiple times)
    if "arcade_points_events" in existing_tables or "arcade_points_events" in inspector.get_table_names():
        try:
            if "idx_arcade_points_events_user_created" not in existing_indexes.get("arcade_points_events", []):
                op.create_index(
                    "idx_arcade_points_events_user_created", "arcade_points_events", ["user_id", "created_at"], unique=False
                )
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise
        
        try:
            if "idx_arcade_points_events_created" not in existing_indexes.get("arcade_points_events", []):
                op.create_index("idx_arcade_points_events_created", "arcade_points_events", ["created_at"], unique=False)
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise

    # Arcade points totals (per-user aggregate)
    if "arcade_points_totals" not in existing_tables:
        try:
            op.create_table(
                "arcade_points_totals",
                sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("total_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
                sa.Column("total_qualifying_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
                sa.Column("last_win_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
                sa.PrimaryKeyConstraint("id"),
                sa.UniqueConstraint("user_id", name="unique_arcade_points_totals_user"),
            )
        except ProgrammingError as e:
            # Table might exist even if inspector didn't catch it
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                raise
            # Table exists, continue with index creation
            pass

    # Ensure indexes exist (safe to run multiple times)
    if "arcade_points_totals" in existing_tables or "arcade_points_totals" in inspector.get_table_names():
        try:
            if "idx_arcade_points_totals_points" not in existing_indexes.get("arcade_points_totals", []):
                op.create_index("idx_arcade_points_totals_points", "arcade_points_totals", ["total_points"], unique=False)
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise
        
        try:
            if "idx_arcade_points_totals_last_win" not in existing_indexes.get("arcade_points_totals", []):
                op.create_index("idx_arcade_points_totals_last_win", "arcade_points_totals", ["last_win_at"], unique=False)
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise


def downgrade() -> None:
    op.drop_index("idx_arcade_points_totals_last_win", table_name="arcade_points_totals")
    op.drop_index("idx_arcade_points_totals_points", table_name="arcade_points_totals")
    op.drop_table("arcade_points_totals")

    op.drop_index("idx_arcade_points_events_created", table_name="arcade_points_events")
    op.drop_index("idx_arcade_points_events_user_created", table_name="arcade_points_events")
    op.drop_table("arcade_points_events")

