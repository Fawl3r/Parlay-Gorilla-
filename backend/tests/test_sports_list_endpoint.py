import pytest


@pytest.mark.asyncio
async def test_list_sports_hides_ucl_and_marks_combat_sports_coming_soon(client):
    resp = await client.get("/api/sports")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)

    slugs = {item.get("slug") for item in data if isinstance(item, dict)}
    assert "ucl" not in slugs

    ufc = next((item for item in data if isinstance(item, dict) and item.get("slug") == "ufc"), None)
    boxing = next((item for item in data if isinstance(item, dict) and item.get("slug") == "boxing"), None)

    assert ufc is not None
    assert boxing is not None

    assert ufc.get("in_season") is False
    assert boxing.get("in_season") is False

    assert ufc.get("status_label") == "Coming Soon"
    assert boxing.get("status_label") == "Coming Soon"





