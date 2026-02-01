"""
Unit tests for tools upset finder service.

Covers:
- Odds parsing (string +144 / unicode minus) -> correct implied prob
- Candidate selection: filters by min_edge + min_underdog_odds
- Sorting: edge desc -> confidence desc -> start_time asc
- Meta counts: games_scanned / games_with_odds / missing_odds

Model probability provider is mocked so tests do not need DB or external data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tools.upset_finder_service import (
    DEFAULT_MIN_EDGE,
    DEFAULT_MIN_UNDERDOG_ODDS,
    _has_usable_h2h,
    _implied_prob_from_american,
    _parse_american_odds,
    UpsetCandidateItem,
    UpsetFinderToolsService,
)
from app.services.tools.upset_candidate_quality import (
    UnderdogH2HPriceExtractor,
    UnderdogPriceStatsCalculator,
)


class TestParseAmericanOdds:
    """Odds parsing: string +144 / unicode minus -> correct integer."""

    def test_positive_string(self):
        assert _parse_american_odds("+140") == 140
        assert _parse_american_odds("+144") == 144
        assert _parse_american_odds("  +200  ") == 200

    def test_negative_string(self):
        assert _parse_american_odds("-110") == -110
        assert _parse_american_odds("-160") == -160

    def test_unicode_minus(self):
        assert _parse_american_odds("−120") == -120
        assert _parse_american_odds("–130") == -130

    def test_int_passthrough(self):
        assert _parse_american_odds(140) == 140
        assert _parse_american_odds(-110) == -110

    def test_invalid_returns_none(self):
        assert _parse_american_odds(None) is None
        assert _parse_american_odds("") is None
        assert _parse_american_odds("  ") is None
        assert _parse_american_odds("nope") is None


class TestImpliedProbFromAmerican:
    """American odds -> implied probability (0-1)."""

    def test_positive_odds(self):
        # +100 -> 50%
        assert _implied_prob_from_american(100) == pytest.approx(0.5, abs=0.001)
        # +200 -> 33.33%
        assert _implied_prob_from_american(200) == pytest.approx(100 / 300, abs=0.001)
        # +140 -> 100/240
        assert _implied_prob_from_american(140) == pytest.approx(100 / 240, abs=0.001)

    def test_negative_odds(self):
        # -100 -> 50%
        assert _implied_prob_from_american(-100) == pytest.approx(0.5, abs=0.001)
        # -200 -> 66.67%
        assert _implied_prob_from_american(-200) == pytest.approx(200 / 300, abs=0.001)


class TestHasUsableH2H:
    """Usable H2H: >=2 outcomes with price or implied_prob."""

    def test_has_two_prices(self):
        odd1 = MagicMock(price="+140", implied_prob=None)
        odd2 = MagicMock(price="-160", implied_prob=None)
        market = MagicMock(market_type="h2h", odds=[odd1, odd2])
        game = MagicMock(markets=[market])
        assert _has_usable_h2h(game) is True

    def test_has_implied_prob(self):
        odd1 = MagicMock(price=None, implied_prob=0.41)
        odd2 = MagicMock(price=None, implied_prob=0.59)
        market = MagicMock(market_type="h2h", odds=[odd1, odd2])
        game = MagicMock(markets=[market])
        assert _has_usable_h2h(game) is True

    def test_wrong_market_type(self):
        market = MagicMock(market_type="spreads", odds=[MagicMock(price="+100"), MagicMock(price="-100")])
        game = MagicMock(markets=[market])
        assert _has_usable_h2h(game) is False

    def test_only_one_outcome(self):
        odd1 = MagicMock(price="+140", implied_prob=None)
        market = MagicMock(market_type="h2h", odds=[odd1])
        game = MagicMock(markets=[market])
        assert _has_usable_h2h(game) is False

    def test_no_markets(self):
        game = MagicMock(markets=[])
        assert _has_usable_h2h(game) is False


class TestCandidateSelectionAndSorting:
    """Filters by min_edge + min_underdog_odds; sort edge desc -> confidence desc -> start_time asc; meta counts."""

    def _make_mock_game(
        self,
        id_: int = 1,
        start_time: datetime | None = None,
        sport: str = "NBA",
        home_team: str = "Home",
        away_team: str = "Away",
    ):
        g = MagicMock()
        g.id = id_
        g.start_time = start_time or datetime(2025, 2, 1, 19, 0, tzinfo=timezone.utc)
        g.sport = sport
        g.home_team = home_team
        g.away_team = away_team
        # Upset Finder now requires >=2 books for trust (to avoid clown edges).
        # Provide two H2H markets with distinct books by default.
        m1 = MagicMock(market_type="h2h", book="draftkings")
        m1.odds = [
            MagicMock(outcome="home", price="+140", implied_prob=None),
            MagicMock(outcome="away", price="-160", implied_prob=None),
        ]
        m2 = MagicMock(market_type="h2h", book="fanduel")
        m2.odds = [
            MagicMock(outcome="home", price="+140", implied_prob=None),
            MagicMock(outcome="away", price="-160", implied_prob=None),
        ]
        g.markets = [m1, m2]
        return g

    @pytest.mark.asyncio
    async def test_meta_counts_games_scanned_and_with_odds(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1, datetime(2025, 2, 1, 19, 0, tzinfo=timezone.utc))
        g2 = self._make_mock_game(2, datetime(2025, 2, 2, 20, 0, tzinfo=timezone.utc))
        g_no_h2h = MagicMock()
        g_no_h2h.id = 3
        g_no_h2h.start_time = datetime(2025, 2, 3, 21, 0, tzinfo=timezone.utc)
        g_no_h2h.sport = "NBA"
        g_no_h2h.home_team = "H"
        g_no_h2h.away_team = "A"
        g_no_h2h.markets = []  # no usable H2H

        async def fake_model_probs(*_args, **_kwargs):
            return (0.50, 0.50, 60.0)

        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1, g2, g_no_h2h]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.41 if side == "home" else 0.59
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=fake_model_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.41,
                        "away_implied_prob": 0.59,
                    }

                    result = await service.find_candidates(
                        sport="nba",
                        days=7,
                        min_edge=3.0,
                        max_results=10,
                        min_underdog_odds=110,
                    )

        assert result.meta["games_scanned"] == 3
        assert result.meta["games_with_odds"] == 2
        assert result.meta["missing_odds"] == 1
        assert len(result.candidates) == 2

    @pytest.mark.asyncio
    async def test_filtered_by_min_edge(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1)
        async def low_edge_probs(*_args, **_kwargs):
            return (0.42, 0.58, 50.0)
        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.41 if side == "home" else 0.59
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=low_edge_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.41,
                        "away_implied_prob": 0.59,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=5.0, max_results=10, min_underdog_odds=110
                    )
        assert result.meta["games_with_odds"] == 1
        assert len(result.candidates) == 0

    @pytest.mark.asyncio
    async def test_filtered_by_min_underdog_odds(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1)
        async def model_probs(*_args, **_kwargs):
            return (0.50, 0.50, 60.0)
        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.41 if side == "home" else 0.59
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=model_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+105",
                        "away_ml": "-115",
                        "home_implied_prob": 0.41,
                        "away_implied_prob": 0.59,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=3.0, max_results=10, min_underdog_odds=110
                    )
        assert result.meta["games_with_odds"] == 1
        assert len(result.candidates) == 0

    @pytest.mark.asyncio
    async def test_sort_order_edge_then_confidence_then_start_time(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1, datetime(2025, 2, 3, 19, 0, tzinfo=timezone.utc))
        g2 = self._make_mock_game(2, datetime(2025, 2, 1, 20, 0, tzinfo=timezone.utc))
        g3 = self._make_mock_game(3, datetime(2025, 2, 2, 21, 0, tzinfo=timezone.utc))
        probs_iter = iter([
            (0.50, 0.50, 60.0),
            (0.55, 0.45, 70.0),
            (0.48, 0.52, 50.0),
        ])
        async def model_probs_by_game(*_args, **_kwargs):
            return next(probs_iter, (0.50, 0.50, 50.0))
        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1, g2, g3]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.41 if side == "home" else 0.59
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=model_probs_by_game):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.41,
                        "away_implied_prob": 0.59,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=1.0, max_results=10, min_underdog_odds=110
                    )
        assert len(result.candidates) == 3
        edges = [c.edge for c in result.candidates]
        assert edges == sorted(edges, reverse=True)
        assert result.candidates[0].edge >= result.candidates[1].edge >= result.candidates[2].edge
        if result.candidates[0].edge == result.candidates[1].edge:
            assert result.candidates[0].confidence >= result.candidates[1].confidence
        assert result.candidates[0].start_time <= result.candidates[-1].start_time

    @pytest.mark.asyncio
    async def test_rejects_low_model_prob_floor(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1)

        async def low_model_probs(*_args, **_kwargs):
            # underdog is home; model_home below 0.43 should be rejected
            return (0.40, 0.60, 60.0)

        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.41 if side == "home" else 0.59
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=low_model_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.41,
                        "away_implied_prob": 0.59,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=1.0, max_results=10, min_underdog_odds=110
                    )
        assert len(result.candidates) == 0

    @pytest.mark.asyncio
    async def test_rejects_implied_prob_out_of_bounds(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1)

        async def model_probs(*_args, **_kwargs):
            return (0.60, 0.40, 60.0)

        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                # implied too low (<0.05) should reject
                mock_implied.side_effect = lambda self, sn, side: 0.01 if side == "home" else 0.99
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=model_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.01,
                        "away_implied_prob": 0.99,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=1.0, max_results=10, min_underdog_odds=110
                    )
        assert len(result.candidates) == 0

    @pytest.mark.asyncio
    async def test_rejects_edge_cap_above_25_points(self):
        db = AsyncMock()
        service = UpsetFinderToolsService(db)
        g1 = self._make_mock_game(1)

        async def model_probs(*_args, **_kwargs):
            # model_home 0.70 vs implied 0.30 => edge_abs 0.40 -> reject
            return (0.70, 0.30, 60.0)

        with patch.object(UpsetFinderToolsService, "_fetch_games", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [g1]
            with patch.object(UpsetFinderToolsService, "_get_implied_prob") as mock_implied:
                mock_implied.side_effect = lambda self, sn, side: 0.30 if side == "home" else 0.70
            with patch.object(UpsetFinderToolsService, "_get_model_probs", side_effect=model_probs):
                with patch.object(service._snapshot_builder, "build") as mock_build:
                    mock_build.return_value = {
                        "home_ml": "+140",
                        "away_ml": "-160",
                        "home_implied_prob": 0.30,
                        "away_implied_prob": 0.70,
                    }
                    result = await service.find_candidates(
                        sport="nba", days=7, min_edge=1.0, max_results=10, min_underdog_odds=110
                    )
        assert len(result.candidates) == 0


class TestUpsetCandidateItemToDict:
    """Response serialization."""

    def test_to_dict_rounds_and_includes_all_fields(self):
        item = UpsetCandidateItem(
            game_id="1",
            start_time="2025-02-01T19:00:00+00:00",
            league="NBA",
            home_team="Lakers",
            away_team="Celtics",
            underdog_side="away",
            underdog_team="Celtics",
            underdog_ml=140,
            implied_prob=0.41,
            model_prob=0.48,
            edge=7.0,
            confidence=0.6,
            market_disagreement=None,
            reasons=["Edge 7.0% (model 48% vs implied 41%)"],
        )
        d = item.to_dict()
        assert d["game_id"] == "1"
        assert d["underdog_team"] == "Celtics"
        assert d["underdog_ml"] == 140
        assert d["edge"] == 7.0
        assert d["confidence"] == 0.6
        assert "reasons" in d
        assert "books_count" in d
        assert "best_underdog_ml" in d
        assert "median_underdog_ml" in d
        assert "price_spread" in d
        assert "worst_underdog_ml" in d
        assert "flags" in d
        assert "odds_quality" in d


class TestBookMetricsHelpers:
    def test_extract_underdog_h2h_prices_multiple_books(self):
        extractor = UnderdogH2HPriceExtractor()

        # Book 1: home is underdog (+165 vs -190)
        m1 = MagicMock(market_type="h2h", book="draftkings")
        m1.odds = [
            MagicMock(outcome="home", price="+165", implied_prob=None),
            MagicMock(outcome="away", price="-190", implied_prob=None),
        ]

        # Book 2: home is underdog (+155 vs -175)
        m2 = MagicMock(market_type="h2h", book="fanduel")
        m2.odds = [
            MagicMock(outcome="home", price="+155", implied_prob=None),
            MagicMock(outcome="away", price="-175", implied_prob=None),
        ]

        prices = extractor.extract_prices(home_team="Home", away_team="Away", markets=[m1, m2])
        assert sorted(prices) == [155, 165]

    def test_extract_underdog_h2h_prices_ignores_invalid(self):
        extractor = UnderdogH2HPriceExtractor()

        m = MagicMock(market_type="h2h", book="draftkings")
        m.odds = [
            MagicMock(outcome="home", price="??", implied_prob=None),
            MagicMock(outcome="away", price="-190", implied_prob=None),
        ]
        prices = extractor.extract_prices(home_team="Home", away_team="Away", markets=[m])
        assert prices == []

    def test_compute_price_stats(self):
        calc = UnderdogPriceStatsCalculator()
        stats = calc.compute([140, 165, 155])
        assert stats.books_count == 3
        assert stats.best_underdog_ml == 165
        assert stats.median_underdog_ml == 155
        assert stats.worst_underdog_ml == 140
        assert stats.price_spread == 25
