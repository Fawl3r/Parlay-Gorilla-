"""Tests for Telegram alerting: payload sanitizer, stack trim, spike detection, message formatting."""

import asyncio
import pytest

from app.services.alerting.alerting_service import (
    AlertingService,
    sanitize_payload,
    trim_stack_trace,
    STACK_TRACE_LINE_LIMIT,
)


def test_sanitize_payload_empty():
    assert sanitize_payload({}) == {}
    assert sanitize_payload(None) == {}


def test_sanitize_payload_trim_large_string():
    long_msg = "x" * 600
    out = sanitize_payload({"message": long_msg})
    assert len(out["message"]) == 503
    assert out["message"].endswith("...")


def test_sanitize_payload_candidates_sample_max_3():
    candidates = [{"id": i} for i in range(5)]
    out = sanitize_payload({"candidates": candidates})
    assert len(out["candidates"]) == 3
    assert out["candidates"] == [{"id": 0}, {"id": 1}, {"id": 2}]


def test_sanitize_payload_list_generic_truncates():
    items = list(range(5))
    out = sanitize_payload({"items": items})
    assert len(out["items"]) == 4
    assert out["items"][-1] == "...+2 more"


def test_trim_stack_trace_empty():
    assert trim_stack_trace("") == ""
    assert trim_stack_trace("   \n  ") == "   \n  "


def test_trim_stack_trace_under_limit():
    lines = ["line1", "line2", "line3"]
    tb = "\n".join(lines)
    assert trim_stack_trace(tb, max_lines=5) == tb


def test_trim_stack_trace_trimmed():
    lines = [f"line{i}" for i in range(30)]
    tb = "\n".join(lines)
    result = trim_stack_trace(tb, max_lines=25)
    result_lines = result.split("\n")
    assert len(result_lines) == 26
    assert result_lines[-1] == "... (trimmed)"
    assert result_lines[0] == "line0"
    assert result_lines[24] == "line24"


@pytest.mark.asyncio
async def test_spike_suppresses_after_threshold():
    """Third emit for same (event, sport) in window is suppressed (spike)."""
    sent = []

    class MockNotifier:
        async def send_event(self, event, severity, payload):
            sent.append((event, payload))
            return True

    svc = AlertingService(notifier=MockNotifier())
    # First two should go through; third is spike-suppressed
    r1 = await svc.emit("test.event", "warning", {"a": 1}, sport="NFL")
    r2 = await svc.emit("test.event", "warning", {"a": 1}, sport="NFL")
    r3 = await svc.emit("test.event", "warning", {"a": 1}, sport="NFL")
    assert r1 is True
    assert r2 is True
    assert r3 is False
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_emit_sanitizes_payload():
    """Emit passes payload through sanitize_payload."""
    captured = []

    class MockNotifier:
        async def send_event(self, event, severity, payload):
            captured.append(payload)
            return True

    svc = AlertingService(notifier=MockNotifier())
    await svc.emit("test.event", "warning", {"candidates": [1, 2, 3, 4, 5]})
    assert len(captured) == 1
    assert len(captured[0]["candidates"]) == 3


@pytest.mark.asyncio
async def test_telegram_notifier_disabled_no_op():
    """When Telegram is disabled, send/send_event are no-op (return False)."""
    from app.services.alerting.telegram_notifier import TelegramNotifier

    notifier = TelegramNotifier(enabled=False, bot_token="", chat_id="")
    r = await notifier.send("hello")
    assert r is False
    r = await notifier.send_event("test", "warning", {"a": 1})
    assert r is False
