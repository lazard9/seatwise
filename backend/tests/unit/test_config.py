import pytest
from pydantic import ValidationError

from app.config import Settings
from tests.conftest import TEST_SECRET


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("JWT_SECRET", "CORS_ORIGINS", "MONGODB_URL", "DATABASE_NAME"):
        monkeypatch.delenv(name, raising=False)


def test_accepts_strong_secret() -> None:
    settings = Settings(_env_file=None, jwt_secret=TEST_SECRET)
    assert settings.jwt_secret == TEST_SECRET


def test_rejects_missing_secret() -> None:
    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_rejects_short_secret() -> None:
    with pytest.raises(ValidationError, match="at least 32 bytes"):
        Settings(_env_file=None, jwt_secret="too-short")


def test_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError, match="placeholder"):
        Settings(_env_file=None, jwt_secret="change-me-" + "x" * 40)


def test_reads_secret_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    assert Settings(_env_file=None).jwt_secret == TEST_SECRET  # type: ignore[call-arg]


def test_splits_comma_separated_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://seatwise.example ,")
    settings = Settings(_env_file=None, jwt_secret=TEST_SECRET)
    assert settings.cors_origins == ["http://localhost:5173", "https://seatwise.example"]
