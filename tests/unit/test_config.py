"""Unit tests for app.backend.core.config.Settings."""

import pytest

from app.backend.core.config import Settings


def test_settings_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """All defaults match the specification."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    s = Settings()
    assert s.anthropic_api_key == ""
    assert s.database_url == "postgresql+psycopg://garmentiq:garmentiq_dev@db:5432/garmentiq"
    assert s.upload_dir == "/app/uploads"
    assert s.max_upload_size_mb == 10
    assert s.claude_model == "claude-sonnet-4-20250514"
    assert s.claude_max_retries == 3


def test_settings_override_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env vars override default values."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

    s = Settings()
    assert s.database_url == "postgresql://test:test@localhost:5432/test"
    assert s.anthropic_api_key == "sk-ant-test-key"


def test_settings_upload_dir_default() -> None:
    """Upload dir defaults to /app/uploads."""
    s = Settings()
    assert s.upload_dir == "/app/uploads"
