"""Tests for placeholder team name detection."""

import pytest

from app.utils.placeholders import is_placeholder_team


def test_is_placeholder_team_afc_nfc_tbd_tba():
    assert is_placeholder_team("AFC") is True
    assert is_placeholder_team("NFC") is True
    assert is_placeholder_team("TBD") is True
    assert is_placeholder_team("TBA") is True
    assert is_placeholder_team("tbd") is True


def test_is_placeholder_team_winner_loser_of():
    assert is_placeholder_team("Winner of AFC Championship") is True
    assert is_placeholder_team("Loser of NFC Championship") is True
    assert is_placeholder_team("Winner of Wild Card") is True


def test_is_placeholder_team_real_names():
    assert is_placeholder_team("Kansas City Chiefs") is False
    assert is_placeholder_team("San Francisco 49ers") is False
    assert is_placeholder_team("") is False
    assert is_placeholder_team(None) is False
