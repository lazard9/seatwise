from app.auth.passwords import hash_password, needs_rehash, verify_password


def test_hash_is_argon2id_and_not_the_password() -> None:
    password_hash = hash_password("correct horse battery")

    assert password_hash.startswith("$argon2id$")
    assert "correct horse battery" not in password_hash


def test_same_password_hashes_differently_each_time() -> None:
    assert hash_password("same password") != hash_password("same password")


def test_verify_accepts_the_right_password() -> None:
    assert verify_password(hash_password("s3cret-pass"), "s3cret-pass") is True


def test_verify_rejects_a_wrong_password() -> None:
    assert verify_password(hash_password("s3cret-pass"), "S3cret-pass") is False


def test_verify_rejects_a_malformed_hash() -> None:
    assert verify_password("not-a-hash", "anything") is False


def test_fresh_hash_does_not_need_rehash() -> None:
    assert needs_rehash(hash_password("s3cret-pass")) is False
