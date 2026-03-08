from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models.enums import ModuleStatus


@dataclass(frozen=True)
class TimeEntryInput:
    user_id: str
    track_id: str
    module_id: str | None
    minutes_spent: int
    entry_date: date

    def validate(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.track_id:
            raise ValueError("track_id is required")
        if self.minutes_spent <= 0:
            raise ValueError("minutes_spent must be greater than 0")


@dataclass(frozen=True)
class ModuleProgressInput:
    user_id: str
    module_id: str
    status: ModuleStatus

    def validate(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.module_id:
            raise ValueError("module_id is required")
