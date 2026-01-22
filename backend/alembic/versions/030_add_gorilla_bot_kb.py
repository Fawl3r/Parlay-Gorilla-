"""Add Gorilla Bot knowledgebase + chat tables.

Revision ID: 030_add_gorilla_bot_kb
Revises: 029_merge_arcade_points_and_weekly_free_limits
Create Date: 2026-01-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = "030_add_gorilla_bot_kb"
down_revision = "299b00a5cc58"  # References production head - will be merged with 029 in migration 036
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "gorilla_bot_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_gorilla_bot_conversations_user_id", "gorilla_bot_conversations", ["user_id"])
    op.create_index(
        "idx_gorilla_bot_conversation_user_updated",
        "gorilla_bot_conversations",
        ["user_id", "updated_at"],
    )
    op.create_index(
        "idx_gorilla_bot_conversation_user_last_msg",
        "gorilla_bot_conversations",
        ["user_id", "last_message_at"],
    )

    op.create_table(
        "gorilla_bot_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gorilla_bot_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_gorilla_bot_message_conversation_role",
        "gorilla_bot_messages",
        ["conversation_id", "role"],
    )
    op.create_index(
        "idx_gorilla_bot_message_conversation_created",
        "gorilla_bot_messages",
        ["conversation_id", "created_at"],
    )

    op.create_table(
        "gorilla_bot_kb_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_path", sa.String(length=255), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_gorilla_bot_kb_doc_active", "gorilla_bot_kb_documents", ["is_active"])
    op.create_index("idx_gorilla_bot_kb_doc_checksum", "gorilla_bot_kb_documents", ["checksum"])
    op.create_index("ix_gorilla_bot_kb_documents_source_path", "gorilla_bot_kb_documents", ["source_path"])

    op.create_table(
        "gorilla_bot_kb_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gorilla_bot_kb_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("embedding_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_gorilla_bot_kb_chunk_doc_index",
        "gorilla_bot_kb_chunks",
        ["document_id", "chunk_index"],
    )

    if _is_postgres():
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_gorilla_bot_kb_chunks_embedding "
            "ON gorilla_bot_kb_chunks USING ivfflat (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP INDEX IF EXISTS idx_gorilla_bot_kb_chunks_embedding")

    op.drop_index("idx_gorilla_bot_kb_chunk_doc_index", table_name="gorilla_bot_kb_chunks")
    op.drop_table("gorilla_bot_kb_chunks")

    op.drop_index("idx_gorilla_bot_kb_doc_checksum", table_name="gorilla_bot_kb_documents")
    op.drop_index("idx_gorilla_bot_kb_doc_active", table_name="gorilla_bot_kb_documents")
    op.drop_index("ix_gorilla_bot_kb_documents_source_path", table_name="gorilla_bot_kb_documents")
    op.drop_table("gorilla_bot_kb_documents")

    op.drop_index("idx_gorilla_bot_message_conversation_created", table_name="gorilla_bot_messages")
    op.drop_index("idx_gorilla_bot_message_conversation_role", table_name="gorilla_bot_messages")
    op.drop_table("gorilla_bot_messages")

    op.drop_index("idx_gorilla_bot_conversation_user_last_msg", table_name="gorilla_bot_conversations")
    op.drop_index("idx_gorilla_bot_conversation_user_updated", table_name="gorilla_bot_conversations")
    op.drop_index("ix_gorilla_bot_conversations_user_id", table_name="gorilla_bot_conversations")
    op.drop_table("gorilla_bot_conversations")
