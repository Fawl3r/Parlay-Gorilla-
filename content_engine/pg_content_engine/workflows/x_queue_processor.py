from __future__ import annotations

from typing import Any

from ..models import ContentItemParseError, ContentStatus, XContentItem
from ..storage import JsonListStore
from ..validation import XValidator
from .item_validation_outcome import ItemValidationOutcome
from .queue_processing_summary import QueueProcessingSummary
from .queue_validation_report import QueueValidationReport
from .rejection_entry_builder import RejectionEntryBuilder
from .status_updater import StatusUpdater


class XQueueProcessor:
    def __init__(
        self,
        queue_store: JsonListStore,
        approved_store: JsonListStore,
        rejected_store: JsonListStore,
        validator: XValidator,
        status_updater: StatusUpdater,
        rejection_builder: RejectionEntryBuilder,
    ) -> None:
        self._queue_store = queue_store
        self._approved_store = approved_store
        self._rejected_store = rejected_store
        self._validator = validator
        self._status_updater = status_updater
        self._rejection_builder = rejection_builder

    def validate_queue(self) -> QueueValidationReport:
        raw_items = self._queue_store.load()
        outcomes: list[ItemValidationOutcome] = []
        valid_count = 0
        invalid_count = 0
        for raw_item in raw_items:
            outcome = self._validate_raw_item(raw_item)
            outcomes.append(outcome)
            if outcome.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        return QueueValidationReport(
            total=len(raw_items),
            valid_count=valid_count,
            invalid_count=invalid_count,
            outcomes=outcomes,
        )

    def approve_queue(self, keep: bool = False) -> QueueProcessingSummary:
        raw_items = self._queue_store.load()
        approved_entries: list[dict[str, Any]] = []
        rejected_entries: list[dict[str, Any]] = []
        error_count = 0
        for raw_item in raw_items:
            try:
                item = XContentItem.from_dict(raw_item)
            except ContentItemParseError as exc:
                rejected_entries.append(self._rejection_builder.from_raw(raw_item, [str(exc)]))
                error_count += 1
                continue
            result = self._validator.validate(item)
            if result.is_valid:
                approved_entries.append(
                    self._status_updater.with_status(item.to_dict(), ContentStatus.APPROVED)
                )
            else:
                rejected_entries.append(
                    self._rejection_builder.from_item_dict(item.to_dict(), result.reasons())
                )
        self._approved_store.append(approved_entries)
        self._rejected_store.append(rejected_entries)
        if not keep:
            self._queue_store.save([])
        return QueueProcessingSummary(
            total=len(raw_items),
            approved_count=len(approved_entries),
            rejected_count=len(rejected_entries),
            error_count=error_count,
        )

    def _validate_raw_item(self, raw_item: Any) -> ItemValidationOutcome:
        content_id = self._extract_id(raw_item)
        try:
            item = XContentItem.from_dict(raw_item)
        except ContentItemParseError as exc:
            return ItemValidationOutcome(content_id=content_id, is_valid=False, reasons=[str(exc)])
        result = self._validator.validate(item)
        return ItemValidationOutcome(
            content_id=content_id,
            is_valid=result.is_valid,
            reasons=result.reasons(),
        )

    @staticmethod
    def _extract_id(raw_item: Any) -> str:
        if isinstance(raw_item, dict) and isinstance(raw_item.get("id"), str):
            return raw_item.get("id") or "unknown"
        return "unknown"
