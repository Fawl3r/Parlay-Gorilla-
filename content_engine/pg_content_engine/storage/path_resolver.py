from __future__ import annotations

from pathlib import Path


class ContentEnginePathResolver:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(__file__).resolve().parents[2]

    @property
    def root(self) -> Path:
        return self._root

    @property
    def outputs_dir(self) -> Path:
        return self._root / "outputs"

    def queue_path(self) -> Path:
        return self.outputs_dir / "queue.json"

    def approved_path(self) -> Path:
        return self.outputs_dir / "approved.json"

    def rejected_path(self) -> Path:
        return self.outputs_dir / "rejected.json"

    def post_log_path(self) -> Path:
        return self.outputs_dir / "post_log.json"

    def video_queue_path(self) -> Path:
        return self.outputs_dir / "video_queue.json"

    def video_approved_path(self) -> Path:
        return self.outputs_dir / "video_approved.json"

    def video_rejected_path(self) -> Path:
        return self.outputs_dir / "video_rejected.json"
