from datetime import timedelta

import jwt
import pytest

from app.auth.tokens import ALGORITHM, create_access_token, decode_access_token
from app.errors import Unauthorized
from app.utils.time import utcnow
from tests.conftest import make_settings

SETTINGS = make_settings()
USER_ID = "6740a1b2c3d4e5f6a7b8c9d0"


def sign(claims: dict[str, object], secret: str = SETTINGS.jwt_secret) -> str:
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def valid_claims(**overrides: object) -> dict[str, object]:
    now = utcnow()
    claims: dict[str, object] = {
        "sub": USER_ID,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(overrides)
    return claims


def test_round_trip_returns_the_user_id() -> None:
    token, expires_in = create_access_token(USER_ID, SETTINGS)

    assert decode_access_token(token, SETTINGS) == USER_ID
    assert expires_in == SETTINGS.access_token_expire_minutes * 60


def test_token_carries_no_role() -> None:
    token, _ = create_access_token(USER_ID, SETTINGS)

    claims = jwt.decode(token, SETTINGS.jwt_secret, algorithms=[ALGORITHM])

    assert "role" not in claims


def test_expired_token_is_rejected_with_its_own_code() -> None:
    token = sign(valid_claims(exp=utcnow() - timedelta(seconds=1)))

    with pytest.raises(Unauthorized) as info:
        decode_access_token(token, SETTINGS)

    assert info.value.code == "TOKEN_EXPIRED"


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        sign(valid_claims(), secret="another-secret-that-is-long-enough-to-sign"),
        sign(valid_claims(type="refresh")),
        sign({k: v for k, v in valid_claims().items() if k != "sub"}),
        sign({k: v for k, v in valid_claims().items() if k != "exp"}),
        jwt.encode(valid_claims(), key="", algorithm="none"),
    ],
    ids=["garbage", "wrong-secret", "wrong-type", "no-sub", "no-exp", "alg-none"],
)
def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(Unauthorized) as info:
        decode_access_token(token, SETTINGS)

    assert info.value.code == "INVALID_TOKEN"
