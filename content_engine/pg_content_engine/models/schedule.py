from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .string_enum import StringEnum


class SchedulePriority(StringEnum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ScheduleWindow(StringEnum):
    MORNING = "morning"
    MIDDAY = "midday"
    EVENING = "evening"
    LATE = "late"


class ScheduleCadence(StringEnum):
    DAILY = "daily"
    THREAD_DAY = "thread_day"
    REPLY_ONLY = "reply_only"


@dataclass(frozen=True)
class Schedule:
    priority: SchedulePriority
    window: ScheduleWindow
    cadence: ScheduleCadence
    evergreen: bool
    expiration_hours: Optional[int]

    @classmethod
    def from_dict(cls, data: Any) -> "Schedule":
        if not isinstance(data, dict):
            raise ValueError("Schedule must be an object.")
        priority = SchedulePriority.from_value(str(data.get("priority", "")))
        window = ScheduleWindow.from_value(str(data.get("window", "")))
        cadence = ScheduleCadence.from_value(str(data.get("cadence", "")))
        evergreen = data.get("evergreen")
        if not isinstance(evergreen, bool):
            raise ValueError("Schedule evergreen must be a boolean.")
        expiration_hours = data.get("expiration_hours")
        if expiration_hours is not None and not isinstance(expiration_hours, int):
            raise ValueError("Schedule expiration_hours must be an integer or null.")
        return cls(
            priority=priority,
            window=window,
            cadence=cadence,
            evergreen=evergreen,
            expiration_hours=expiration_hours,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority.value,
            "window": self.window.value,
            "cadence": self.cadence.value,
            "evergreen": self.evergreen,
            "expiration_hours": self.expiration_hours,
        }
