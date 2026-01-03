from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from src.publisher import XPublisher


def test_publisher_dry_run_does_not_call_network() -> None:
    pub = XPublisher(
        api_base_url="https://api.x.com/2",
        bearer_token="",
        dry_run=True,
        max_retries=0,
        backoff_initial_seconds=0.0,
        backoff_max_seconds=0.0,
        timeout_seconds=0.1,
    )
    res = pub.publish_single(text="hello")
    assert res.success is True
    assert res.tweet_ids and res.tweet_ids[0].startswith("dryrun-")


def test_publisher_retries_network_error_then_succeeds(monkeypatch) -> None:
    calls = {"n": 0}

    class FakeClient:
        def __init__(self, timeout):
            self._timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers=None, json=None):
            calls["n"] += 1
            req = httpx.Request("POST", url)
            if calls["n"] == 1:
                raise httpx.ConnectError("boom", request=req)
            return httpx.Response(201, json={"data": {"id": "123"}}, request=req)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    pub = XPublisher(
        api_base_url="https://api.x.com/2",
        bearer_token="token",
        dry_run=False,
        max_retries=2,
        backoff_initial_seconds=0.0,
        backoff_max_seconds=0.0,
        timeout_seconds=0.1,
    )
    res = pub.publish_single(text="hello")
    assert res.success is True
    assert res.tweet_ids == ["123"]
    assert calls["n"] == 2


def test_publisher_429_sets_pause_until(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    reset = int((now + timedelta(seconds=60)).timestamp())

    class FakeClient:
        def __init__(self, timeout):
            self._timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers=None, json=None):
            req = httpx.Request("POST", url)
            return httpx.Response(429, headers={"x-rate-limit-reset": str(reset)}, request=req)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    pub = XPublisher(
        api_base_url="https://api.x.com/2",
        bearer_token="token",
        dry_run=False,
        max_retries=0,
        backoff_initial_seconds=0.0,
        backoff_max_seconds=0.0,
        timeout_seconds=0.1,
    )
    res = pub.publish_single(text="hello")
    assert res.success is False
    assert res.pause_until is not None


