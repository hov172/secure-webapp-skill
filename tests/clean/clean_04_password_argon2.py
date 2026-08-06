from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

_hasher = PasswordHasher()


def register(db, email: str, password: str) -> None:
    db.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, _hasher.hash(password)),
    )


def check_password(stored_hash: str, password: str) -> bool:
    try:
        _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
    return True


def needs_rehash(stored_hash: str) -> bool:
    return _hasher.check_needs_rehash(stored_hash)
