import hashlib


def register(db, email: str, password: str) -> None:
    digest = hashlib.md5(password.encode()).hexdigest()
    db.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, digest))


def check_password(stored_hash: str, password: str) -> bool:
    return stored_hash == hashlib.md5(password.encode()).hexdigest()
