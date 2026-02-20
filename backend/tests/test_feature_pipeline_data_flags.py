from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.feature_pipeline import (
    FeaturePipeline,
    HOME_ADVANTAGE_BY_SPORT,
    MatchupFeatureVector,
)


@pytest.mark.asyncio
async def test_feature_pipeline_does_not_mark_missing_stats_or_injuries_as_present():
    pipeline = FeaturePipeline(db=None)
    pipeline._fetch_team_stats = AsyncMock(return_value=(None, None))
    pipeline._fetch_injuries = AsyncMock(return_value=(None, None))
    pipeline._fetch_recent_form = AsyncMock(return_value=([], []))
    pipeline._fetch_matchup_context = AsyncMock(return_value=None)

    features = await pipeline.build_matchup_features(
        home_team="Home Team",
        away_team="Away Team",
        sport="NBA",
        game_time=None,
    )

    assert features.has_stats_data is False
    assert features.has_injury_data is False


@pytest.mark.asyncio
async def test_feature_pipeline_marks_injuries_when_payload_exists():
    pipeline = FeaturePipeline(db=None)
    pipeline._fetch_team_stats = AsyncMock(return_value=(None, None))
    pipeline._fetch_injuries = AsyncMock(
        return_value=(
            {"injury_severity_score": 0.4, "key_players_out": ["Player A"]},
            None,
        )
    )
    pipeline._fetch_recent_form = AsyncMock(return_value=([], []))
    pipeline._fetch_matchup_context = AsyncMock(return_value=None)
    pipeline._fetch_weather = AsyncMock(return_value={"is_outdoor": True, "temperature": 65, "wind_speed": 5})

    features = await pipeline.build_matchup_features(
        home_team="Home Team",
        away_team="Away Team",
        sport="EPL",
        game_time=datetime.now(tz=timezone.utc),
    )

    assert features.has_injury_data is True
    assert features.key_players_out_home == ["Player A"]


def test_feature_pipeline_wnba_normalization_and_home_advantage():
    pipeline = FeaturePipeline(db=None)

    assert pipeline._normalize_sport_key("wnba") == "basketball_wnba"
    assert pipeline._normalize_sport_key("basketball_wnba") == "basketball_wnba"

    features = MatchupFeatureVector(
        home_team="A",
        away_team="B",
        sport="WNBA",
        home_advantage=HOME_ADVANTAGE_BY_SPORT.get("wnba", 0.025),
    )
    assert features.home_advantage == pytest.approx(0.033, abs=0.0001)
