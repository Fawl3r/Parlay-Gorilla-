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
    dialect_name = conn.dialect.name

    def table_exists(table_name: str) -> bool:
        if dialect_name == "postgresql":
            result = conn.execute(sa.text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :name)"
            ), {"name": table_name})
        else:
            result = conn.execute(sa.text(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name = :name"
            ), {"name": table_name})
            return result.scalar() > 0
        return result.scalar()

    def index_exists(index_name: str, table_name: str) -> bool:
        if dialect_name == "postgresql":
            result = conn.execute(sa.text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE schemaname = 'public' AND indexname = :idx_name AND tablename = :tbl_name)"
            ), {"idx_name": index_name, "tbl_name": table_name})
            return result.scalar()
        idx_list = [idx["name"] for idx in inspector.get_indexes(table_name)]
        return index_name in idx_list
    
    # Arcade points events (one row per awarded win)
    # Use try-except for extra safety in case table exists but check fails
    if not table_exists("arcade_points_events"):
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
            # Table might exist even if check didn't catch it
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                raise
            # Table exists, continue with index creation
            pass

    # Ensure indexes exist (safe to run multiple times)
    if table_exists("arcade_points_events"):
        if not index_exists("idx_arcade_points_events_user_created", "arcade_points_events"):
            try:
                op.create_index(
                    "idx_arcade_points_events_user_created", "arcade_points_events", ["user_id", "created_at"], unique=False
                )
            except ProgrammingError as e:
                if "already exists" not in str(e).lower():
                    raise
        
        if not index_exists("idx_arcade_points_events_created", "arcade_points_events"):
            try:
                op.create_index("idx_arcade_points_events_created", "arcade_points_events", ["created_at"], unique=False)
            except ProgrammingError as e:
                if "already exists" not in str(e).lower():
                    raise

    # Arcade points totals (per-user aggregate)
    if not table_exists("arcade_points_totals"):
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
            # Table might exist even if check didn't catch it
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                raise
            # Table exists, continue with index creation
            pass

    # Ensure indexes exist (safe to run multiple times)
    if table_exists("arcade_points_totals"):
        if not index_exists("idx_arcade_points_totals_points", "arcade_points_totals"):
            try:
                op.create_index("idx_arcade_points_totals_points", "arcade_points_totals", ["total_points"], unique=False)
            except ProgrammingError as e:
                if "already exists" not in str(e).lower():
                    raise
        
        if not index_exists("idx_arcade_points_totals_last_win", "arcade_points_totals"):
            try:
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

