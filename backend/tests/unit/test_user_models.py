import pytest
from pydantic import ValidationError

from app.models.users import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, UserCreate

VALID = {"email": "Ana@Example.COM", "password": "long-enough", "display_name": "Ana"}


def test_email_is_lowercased() -> None:
    assert UserCreate(**VALID).email == "ana@example.com"


def test_display_name_is_trimmed() -> None:
    assert UserCreate(**{**VALID, "display_name": "  Ana Ivić  "}).display_name == "Ana Ivić"


@pytest.mark.parametrize("email", ["", "not-an-email", "ana@", "@example.com"])
def test_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError, match="email"):
        UserCreate(**{**VALID, "email": email})


def test_accepts_password_at_the_limits() -> None:
    UserCreate(**{**VALID, "password": "x" * PASSWORD_MIN_LENGTH})
    UserCreate(**{**VALID, "password": "x" * PASSWORD_MAX_LENGTH})


@pytest.mark.parametrize("length", [PASSWORD_MIN_LENGTH - 1, PASSWORD_MAX_LENGTH + 1])
def test_rejects_password_outside_the_limits(length: int) -> None:
    with pytest.raises(ValidationError, match="password"):
        UserCreate(**{**VALID, "password": "x" * length})


@pytest.mark.parametrize("name", ["", " ", "A", "x" * 51])
def test_rejects_display_name_outside_the_limits(name: str) -> None:
    with pytest.raises(ValidationError, match="display_name"):
        UserCreate(**{**VALID, "display_name": name})
