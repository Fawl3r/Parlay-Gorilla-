"""Tests for sport config: WNBA slug and Odds API key mapping."""

import pytest

from app.services.sports_config import SPORT_CONFIGS, get_sport_config


def test_wnba_sport_config_exists():
    """WNBA must be in SPORT_CONFIGS with slug wnba and odds_key basketball_wnba."""
    assert "wnba" in SPORT_CONFIGS
    cfg = SPORT_CONFIGS["wnba"]
    assert cfg.slug == "wnba"
    assert cfg.odds_key == "basketball_wnba"
    assert cfg.code == "WNBA"
    assert cfg.display_name == "WNBA"
    assert "h2h" in cfg.default_markets
    assert "spreads" in cfg.default_markets
    assert "totals" in cfg.default_markets


def test_get_sport_config_wnba_slug():
    """get_sport_config resolves wnba and basketball_wnba to same config."""
    by_slug = get_sport_config("wnba")
    by_odds_key = get_sport_config("basketball_wnba")
    assert by_slug.slug == "wnba"
    assert by_slug.odds_key == "basketball_wnba"
    assert by_slug.slug == by_odds_key.slug
    assert by_slug.odds_key == by_odds_key.odds_key


def test_wnba_not_hidden_not_coming_soon():
    """WNBA is visible and not in coming-soon (so it appears in /api/sports as normal)."""
    from app.services.sports_config import HIDDEN_SPORT_SLUGS, COMING_SOON_SPORT_SLUGS, is_sport_visible

    assert "wnba" not in HIDDEN_SPORT_SLUGS
    assert "wnba" not in COMING_SOON_SPORT_SLUGS
    cfg = get_sport_config("wnba")
    assert is_sport_visible(cfg) is True
