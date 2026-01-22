from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from pg_content_engine.storage import JsonFileGateway, JsonListStore
from pg_content_engine.validation import VideoValidatorFactory
from pg_content_engine.workflows.rejection_entry_builder import RejectionEntryBuilder
from pg_content_engine.workflows.status_updater import StatusUpdater
from pg_content_engine.workflows.video_queue_processor import VideoQueueProcessor


class VideoQueueFixture:
    def __init__(self, root: Path) -> None:
        gateway = JsonFileGateway()
        self.queue = JsonListStore(root / "video_queue.json", gateway)
        self.approved = JsonListStore(root / "video_approved.json", gateway)
        self.rejected = JsonListStore(root / "video_rejected.json", gateway)
        self.processor = VideoQueueProcessor(
            queue_store=self.queue,
            approved_store=self.approved,
            rejected_store=self.rejected,
            validator=VideoValidatorFactory().build(),
            status_updater=StatusUpdater(),
            rejection_builder=RejectionEntryBuilder(),
        )


class VideoItemFactory:
    def __init__(self) -> None:
        self._base = {
            "id": "pg_v_001",
            "type": "video_script",
            "topic": "discipline",
            "script": (
                "Parlay Gorilla reminder: discipline starts with one clear angle. "
                "If you cannot explain why each leg wins, you cut it. "
                "That is how risk stays controlled and variance stops writing your results over time "
                "for disciplined decision making under pressure."
            ),
            "format_tag": "discipline_reminder",
            "compliance": {"no_guarantees": True, "no_hype": True, "no_emojis": True},
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


def test_video_queue_approve_moves_items(tmp_path: Path) -> None:
    fixture = VideoQueueFixture(tmp_path)
    factory = VideoItemFactory()
    valid_item = factory.build({"id": "pg_v_valid"})
    invalid_item = factory.build({"id": "pg_v_invalid", "script": "Free money."})
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
