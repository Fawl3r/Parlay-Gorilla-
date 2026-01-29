"""APISports quota per sport: add sport column and (date, sport) PK.

Revision ID: 044_apisports_quota_per_sport
Revises: 043_add_sport_season_state
Create Date: 2026-01-29

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "044_apisports_quota_per_sport"
down_revision = "043_add_sport_season_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # api_quota_usage was not created on SQLite (042 skipped); skip this migration.
        return
    inspector = inspect(conn)
    if "api_quota_usage" not in inspector.get_table_names():
        return
    op.add_column("api_quota_usage", sa.Column("sport", sa.String(16), nullable=True))
    op.execute("UPDATE api_quota_usage SET sport = 'default' WHERE sport IS NULL")
    op.alter_column(
        "api_quota_usage",
        "sport",
        existing_type=sa.String(16),
        nullable=False,
    )
    op.drop_constraint("api_quota_usage_pkey", "api_quota_usage", type_="primary")
    op.create_primary_key("api_quota_usage_pkey", "api_quota_usage", ["date", "sport"])


def downgrade() -> None:
    op.drop_constraint("api_quota_usage_pkey", "api_quota_usage", type_="primary")
    op.create_primary_key("api_quota_usage_pkey", "api_quota_usage", ["date"])
    op.drop_column("api_quota_usage", "sport")
