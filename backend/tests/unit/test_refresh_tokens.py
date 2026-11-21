from fastapi import Response

from app.auth.cookies import REFRESH_COOKIE, clear_refresh_cookie, set_refresh_cookie
from app.auth.tokens import hash_refresh_token, new_refresh_token
from tests.conftest import make_settings


def test_new_refresh_tokens_are_long_and_unique() -> None:
    tokens = {new_refresh_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(token) >= 43 for token in tokens)  # 32 random bytes, base64url


def test_refresh_token_hash_is_stable_sha256_hex() -> None:
    digest = hash_refresh_token("abc")

    assert digest == hash_refresh_token("abc")
    assert digest != hash_refresh_token("abd")
    assert digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def set_cookie_header(response: Response) -> str:
    return response.headers["set-cookie"].lower()


def test_refresh_cookie_attributes() -> None:
    response = Response()

    set_refresh_cookie(response, "token-value", make_settings())

    header = set_cookie_header(response)
    assert header.startswith(f"{REFRESH_COOKIE}=token-value")
    assert "httponly" in header
    assert "samesite=lax" in header
    assert "path=/auth" in header
    assert "max-age=604800" in header
    assert "secure" not in header


def test_refresh_cookie_is_secure_when_configured() -> None:
    response = Response()

    set_refresh_cookie(response, "token-value", make_settings(refresh_cookie_secure=True))

    assert "secure" in set_cookie_header(response)


def test_clearing_the_cookie_uses_the_same_path() -> None:
    response = Response()

    clear_refresh_cookie(response, make_settings())

    header = set_cookie_header(response)
    assert "max-age=0" in header
    assert "path=/auth" in header
