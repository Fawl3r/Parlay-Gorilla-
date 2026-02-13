"""Add scheduler_job_runs table for /ops/jobs.

Revision ID: 049_add_scheduler_job_runs
Revises: 048_add_verification_processing_status
Create Date: 2026-02-13

Stores last run per job: job_name, last_run_at, duration_ms, status, error_snippet.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "049_add_scheduler_job_runs"
down_revision = "048_add_verification_processing_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_job_runs",
        sa.Column("job_name", sa.String(128), primary_key=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_snippet", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("scheduler_job_runs")
