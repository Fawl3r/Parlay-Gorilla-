"""Unit tests for score scraper start_time backfill behavior."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.game import Game
from app.services.scores.normalizer import GameUpdate
from app.services.scores.score_scraper_service import backfill_start_time_if_missing


def test_backfill_start_time_when_existing_null_sets_start_time():
    """When existing_game.start_time is None and update has start_time, backfill sets it."""
    now = datetime.now(timezone.utc)
    existing = Game(
        id=uuid.uuid4(),
        external_game_id="ext-1",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=None,
        status="LIVE",
    )
    update = GameUpdate(
        external_game_key="key-1",
        home_team="Seahawks",
        away_team="Raiders",
        home_score=21,
        away_score=17,
        status="LIVE",
        period="Q3",
        clock="04:12",
        start_time=now,
        data_source="espn",
    )
    backfill_start_time_if_missing(existing, update)
    assert existing.start_time is not None
    assert existing.start_time == now


def test_backfill_start_time_when_existing_set_does_not_overwrite():
    """When existing_game.start_time is set, backfill does not overwrite it."""
    original = datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc)
    new_time = datetime(2025, 1, 16, 19, 0, 0, tzinfo=timezone.utc)
    existing = Game(
        id=uuid.uuid4(),
        external_game_id="ext-2",
        sport="NFL",
        home_team="Chiefs",
        away_team="Bills",
        start_time=original,
        status="FINAL",
    )
    update = GameUpdate(
        external_game_key="key-2",
        home_team="Chiefs",
        away_team="Bills",
        home_score=27,
        away_score=24,
        status="FINAL",
        period=None,
        clock=None,
        start_time=new_time,
        data_source="yahoo",
    )
    backfill_start_time_if_missing(existing, update)
    assert existing.start_time == original
    assert existing.start_time != new_time
