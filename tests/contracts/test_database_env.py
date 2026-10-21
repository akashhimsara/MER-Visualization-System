"""
Tests for Automatic .env Loading, Environment Precedence, and Database Fallback.
"""

from pathlib import Path
import pytest

from components.personalization.persistence.database import (
    get_database_url,
    load_project_env,
    PROJECT_ROOT,
)
from components.personalization.runtime import PersonalizationRuntimeService


def test_env_provides_database_url_when_no_shell_variable(tmp_path, monkeypatch):
    """Verify .env provides DATABASE_URL when no shell environment variable exists."""
    mock_env = tmp_path / ".env"
    mock_env.write_text(
        "DATABASE_URL=postgresql+psycopg://mock_dotenv_user:mock_dotenv_pass@localhost:5432/mock_dotenv_db\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)

    loaded = load_project_env(env_path=mock_env, override=False)
    assert loaded is True
    assert get_database_url() == "postgresql+psycopg://mock_dotenv_user:mock_dotenv_pass@localhost:5432/mock_dotenv_db"


def test_shell_database_url_overrides_env(tmp_path, monkeypatch):
    """Verify explicit shell DATABASE_URL takes priority over .env (override=False)."""
    mock_env = tmp_path / ".env"
    mock_env.write_text(
        "DATABASE_URL=postgresql+psycopg://dotenv_user:dotenv_pass@localhost:5432/dotenv_db\n",
        encoding="utf-8",
    )
    shell_url = "postgresql+psycopg://shell_user:shell_pass@localhost:5432/shell_db"
    monkeypatch.setenv("DATABASE_URL", shell_url)

    loaded = load_project_env(env_path=mock_env, override=False)
    # Shell URL must not be overridden
    assert get_database_url() == shell_url


def test_missing_database_url_permits_in_memory_mode(monkeypatch):
    """Verify missing DATABASE_URL still permits in-memory mode."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() is None

    svc = PersonalizationRuntimeService()
    assert svc.repository is None


def test_explicit_none_repository_forces_in_memory_mode(monkeypatch):
    """Verify explicit repository=None enforces in-memory mode even if DATABASE_URL is set."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db",
    )
    svc = PersonalizationRuntimeService(repository=None)
    assert svc.repository is None


def test_no_real_credentials_in_tracked_example_or_gitignore():
    """Verify .env.example contains only safe placeholders and .gitignore properly ignores .env."""
    example_path = PROJECT_ROOT / ".env.example"
    assert example_path.is_file()
    content = example_path.read_text(encoding="utf-8")
    assert "DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/emotion_visualization" in content

    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.is_file()
    gi_content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in gi_content
    assert ".env.*" in gi_content
    assert "!.env.example" in gi_content
