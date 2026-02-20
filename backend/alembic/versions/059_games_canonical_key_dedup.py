"""Add canonical_match_key to games, dedupe by key, enforce uniqueness.

Revision ID: 059_canonical_key_dedup
Revises: 058_idempotency_key
Create Date: 2026-02-20

- Add games.canonical_match_key (sport|team_low|team_high|start_iso_5min).
- Backfill key using SQL (lower trim teams, 5-min bucket UTC).
- For each duplicate group: pick survivor (prefer non-ESPN, then by market count);
  re-point markets, parlay_legs, watched_games, game_analyses, analysis_page_views,
  model_predictions, game_results, market_efficiency to survivor; delete losers.
- Add unique constraint on games.canonical_match_key.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "059_canonical_key_dedup"
down_revision = "058_idempotency_key"
branch_labels = None
depends_on = None

# Tables with game_id FK that must be re-pointed before deleting duplicate games.
GAME_CHILD_TABLES = [
    "markets",
    "parlay_legs",
    "watched_games",
    "game_analyses",
    "analysis_page_views",
    "model_predictions",
    "game_results",
    "market_efficiency",
]


def _is_postgres(conn) -> bool:
    return conn.dialect.name == "postgresql"


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).scalar()
    return r is not None


def _index_exists(conn, index_name: str) -> bool:
    r = conn.execute(
        text(
            "SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = :n"
        ),
        {"n": index_name},
    ).scalar()
    return r is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        # SQLite or other: only add column; skip dedupe and unique (not supported the same way).
        if not _column_exists(conn, "games", "canonical_match_key"):
            op.add_column(
                "games",
                sa.Column("canonical_match_key", sa.String(256), nullable=True),
            )
        return

    # 1) Add column (idempotent)
    if not _column_exists(conn, "games", "canonical_match_key"):
        op.add_column(
            "games",
            sa.Column("canonical_match_key", sa.String(256), nullable=True),
        )

    # 2) Backfill canonical_match_key: sport|team_low|team_high|start_iso_5min
    # 5-min bucket (UTC): floor minute to 5, then ISO string
    conn.execute(
        text("""
        UPDATE games
        SET canonical_match_key = (
            sport
            || '|'
            || LEAST(LOWER(TRIM(home_team)), LOWER(TRIM(away_team)))
            || '|'
            || GREATEST(LOWER(TRIM(home_team)), LOWER(TRIM(away_team)))
            || '|'
            || to_char(
                date_trunc('hour', start_time AT TIME ZONE 'UTC')
                + (FLOOR(EXTRACT(MINUTE FROM start_time AT TIME ZONE 'UTC')::int / 5) * 5) * interval '1 minute',
                'YYYY-MM-DD"T"HH24:MI:00'
            ) || '+00:00'
        )
        WHERE canonical_match_key IS NULL
        """
        )
    )

    # 3) Find duplicate groups and process each
    dup_rows = conn.execute(
        text("""
        SELECT canonical_match_key, array_agg(id ORDER BY
            (external_game_id NOT LIKE 'espn:%') DESC,
            (SELECT count(*) FROM markets m WHERE m.game_id = games.id) DESC,
            id
        ) AS game_ids
        FROM games
        WHERE canonical_match_key IS NOT NULL
        GROUP BY canonical_match_key
        HAVING count(*) > 1
        """)
    ).fetchall()

    for (canonical_key, game_ids) in dup_rows:
        ids_list = list(game_ids) if game_ids is not None else []
        if len(ids_list) < 2:
            continue
        survivor_id = ids_list[0]
        loser_ids = ids_list[1:]
        for loser_id in loser_ids:
            for table in GAME_CHILD_TABLES:
                try:
                    conn.execute(
                        text(
                            f"UPDATE {table} SET game_id = :survivor WHERE game_id = :loser"
                        ),
                        {"survivor": survivor_id, "loser": loser_id},
                    )
                except Exception as e:
                    # Table might not exist or have no game_id column
                    if "does not exist" in str(e) or "column" in str(e).lower():
                        continue
                    raise RuntimeError(
                        f"Cannot re-point {table} from game {loser_id} to {survivor_id}: {e}"
                    ) from e
            conn.execute(
                text("DELETE FROM games WHERE id = :loser"),
                {"loser": loser_id},
            )

    # 4) Set NOT NULL and add unique constraint (idempotent)
    conn.execute(text("UPDATE games SET canonical_match_key = id::text WHERE canonical_match_key IS NULL"))
    op.alter_column(
        "games",
        "canonical_match_key",
        existing_type=sa.String(256),
        nullable=False,
    )
    if not _index_exists(conn, "uq_games_canonical_match_key"):
        op.create_index(
            "uq_games_canonical_match_key",
            "games",
            ["canonical_match_key"],
            unique=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _is_postgres(conn) and _index_exists(conn, "uq_games_canonical_match_key"):
        op.drop_index("uq_games_canonical_match_key", table_name="games")
    if _column_exists(conn, "games", "canonical_match_key"):
        op.drop_column("games", "canonical_match_key")
