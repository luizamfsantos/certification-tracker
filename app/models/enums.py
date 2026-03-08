from __future__ import annotations

from enum import Enum


class ModuleStatus(str, Enum):
    NOT_SEEN = "not_seen"
    SEEN = "seen"
    MASTERED = "mastered"
