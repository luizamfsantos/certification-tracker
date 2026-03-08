from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    env: str
    data_dir: Path
    log_level: str


def load_config() -> AppConfig:
    load_dotenv(override=False)
    env = os.getenv("CERT_TRACKER_ENV", "dev")
    data_dir = Path(os.getenv("CERT_TRACKER_DATA_DIR", "data/curated"))
    log_level = os.getenv("CERT_TRACKER_LOG_LEVEL", "INFO")
    return AppConfig(env=env, data_dir=data_dir, log_level=log_level)
