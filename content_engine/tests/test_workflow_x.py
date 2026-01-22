from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from pg_content_engine.storage import JsonFileGateway, JsonListStore
from pg_content_engine.validation import XValidatorFactory
from pg_content_engine.workflows.rejection_entry_builder import RejectionEntryBuilder
from pg_content_engine.workflows.status_updater import StatusUpdater
from pg_content_engine.workflows.x_queue_processor import XQueueProcessor


class XQueueFixture:
    def __init__(self, root: Path) -> None:
        gateway = JsonFileGateway()
        self.queue = JsonListStore(root / "queue.json", gateway)
        self.approved = JsonListStore(root / "approved.json", gateway)
        self.rejected = JsonListStore(root / "rejected.json", gateway)
        self.processor = XQueueProcessor(
            queue_store=self.queue,
            approved_store=self.approved,
            rejected_store=self.rejected,
            validator=XValidatorFactory().build(),
            status_updater=StatusUpdater(),
            rejection_builder=RejectionEntryBuilder(),
        )


class XItemFactory:
    def __init__(self) -> None:
        self._base = {
            "id": "pg_x_001",
            "type": "post",
            "topic": "discipline",
            "text": "Calm, direct guidance.",
            "style_tag": "discipline",
            "compliance": {"no_guarantees": True, "no_hype": True, "no_emojis": True},
            "hashtags": [],
            "schedule": {
                "priority": "normal",
                "window": "evening",
                "cadence": "daily",
                "evergreen": True,
                "expiration_hours": None,
            },
            "status": "pending",
        }

    def build(self, overrides: dict) -> dict:
        data = deepcopy(self._base)
        data.update(overrides)
        return data


def test_x_queue_approve_moves_items(tmp_path: Path) -> None:
    fixture = XQueueFixture(tmp_path)
    factory = XItemFactory()
    valid_item = factory.build({"id": "pg_x_valid"})
    invalid_item = factory.build({"id": "pg_x_invalid", "text": "Free money."})
    fixture.queue.save([valid_item, invalid_item])

    summary = fixture.processor.approve_queue()

    approved = fixture.approved.load()
    rejected = fixture.rejected.load()
    assert summary.approved_count == 1
    assert summary.rejected_count == 1
    assert approved[0]["status"] == "approved"
    assert rejected[0]["status"] == "rejected"
    assert rejected[0]["rejection_reasons"]
    assert fixture.queue.load() == []
