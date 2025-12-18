from datetime import datetime, timezone

from app.services.saved_parlays.payloads import SavedParlayHashInputs, payload_builder


def test_saved_parlay_hash_payload_contains_account_number_and_no_pii_keys():
    payload = payload_builder.build_payload(
        SavedParlayHashInputs(
            saved_parlay_id="11111111-1111-1111-1111-111111111111",
            account_number="0001234567",
            created_at_utc=datetime(2025, 1, 1, tzinfo=timezone.utc),
            parlay_type="custom",
            legs=[
                {"game_id": "g1", "market_type": "h2h", "pick": "home", "odds": "-110"},
                {"game_id": "g2", "market_type": "totals", "pick": "over", "point": 44.5},
            ],
            app_version="pg_backend_v1",
        )
    )

    assert payload["account_number"] == "0001234567"
    assert "email" not in payload
    assert "user_id" not in payload


