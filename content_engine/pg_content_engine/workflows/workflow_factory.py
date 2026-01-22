from __future__ import annotations

from ..storage import ContentEnginePathResolver, JsonFileGateway, JsonListStore
from ..validation import VideoValidatorFactory, XValidatorFactory
from .rejection_entry_builder import RejectionEntryBuilder
from .status_updater import StatusUpdater
from .video_queue_processor import VideoQueueProcessor
from .x_queue_processor import XQueueProcessor


class WorkflowFactory:
    def __init__(self, path_resolver: ContentEnginePathResolver, gateway: JsonFileGateway) -> None:
        self._path_resolver = path_resolver
        self._gateway = gateway

    def build_x_processor(self) -> XQueueProcessor:
        queue_store = JsonListStore(self._path_resolver.queue_path(), self._gateway)
        approved_store = JsonListStore(self._path_resolver.approved_path(), self._gateway)
        rejected_store = JsonListStore(self._path_resolver.rejected_path(), self._gateway)
        validator = XValidatorFactory().build()
        return XQueueProcessor(
            queue_store=queue_store,
            approved_store=approved_store,
            rejected_store=rejected_store,
            validator=validator,
            status_updater=StatusUpdater(),
            rejection_builder=RejectionEntryBuilder(),
        )

    def build_video_processor(self) -> VideoQueueProcessor:
        queue_store = JsonListStore(self._path_resolver.video_queue_path(), self._gateway)
        approved_store = JsonListStore(self._path_resolver.video_approved_path(), self._gateway)
        rejected_store = JsonListStore(self._path_resolver.video_rejected_path(), self._gateway)
        validator = VideoValidatorFactory().build()
        return VideoQueueProcessor(
            queue_store=queue_store,
            approved_store=approved_store,
            rejected_store=rejected_store,
            validator=validator,
            status_updater=StatusUpdater(),
            rejection_builder=RejectionEntryBuilder(),
        )
