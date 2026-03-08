from __future__ import annotations

from app.config import load_config


def test_load_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CERT_TRACKER_ENV", raising=False)
    monkeypatch.delenv("CERT_TRACKER_DATA_DIR", raising=False)
    monkeypatch.delenv("CERT_TRACKER_LOG_LEVEL", raising=False)

    config = load_config()

    assert config.env == "dev"
    assert str(config.data_dir).replace("\\", "/") == "data/curated"
    assert config.log_level == "INFO"
