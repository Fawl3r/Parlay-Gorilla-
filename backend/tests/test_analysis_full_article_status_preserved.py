from app.services.analysis.analysis_contract import merge_preserving_full_article


def test_merge_preserves_full_article_status_when_article_is_preserved():
    existing = {
        "opening_summary": "Existing core summary",
        "full_article": "## Opening Summary\n\nExisting full article text.",
        "generation": {
            "core_status": "ready",
            "full_article_status": "ready",
            "updated_at": "t1",
        },
    }
    incoming = {
        "opening_summary": "New core summary",
        "full_article": "",
        "generation": {
            "core_status": "ready",
            "full_article_status": "queued",
            "updated_at": "t2",
        },
    }

    merged = merge_preserving_full_article(existing=existing, incoming=incoming, force_refresh_core=False)

    assert merged.get("full_article") == existing["full_article"]
    assert isinstance(merged.get("generation"), dict)
    assert merged["generation"].get("full_article_status") == "ready"


def test_force_refresh_preserves_full_article_status_when_article_is_preserved():
    existing = {
        "opening_summary": "Existing core summary",
        "full_article": "## Opening Summary\n\nExisting full article text.",
        "generation": {
            "core_status": "ready",
            "full_article_status": "ready",
            "updated_at": "t1",
        },
    }
    incoming = {
        "opening_summary": "New core summary",
        "full_article": "",
        "generation": {
            "core_status": "partial",
            "full_article_status": "queued",
            "updated_at": "t2",
        },
    }

    merged = merge_preserving_full_article(existing=existing, incoming=incoming, force_refresh_core=True)

    assert merged.get("full_article") == existing["full_article"]
    assert isinstance(merged.get("generation"), dict)
    assert merged["generation"].get("full_article_status") == "ready"


