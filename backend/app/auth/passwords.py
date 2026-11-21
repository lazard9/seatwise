from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Library defaults follow the current OWASP recommendation for Argon2id.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError, InvalidHashError:
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the hash was made with older parameters and should be replaced on login."""
    return _hasher.check_needs_rehash(password_hash)
