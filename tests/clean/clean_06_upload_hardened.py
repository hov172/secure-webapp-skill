import secrets
from pathlib import Path

# Outside the web root: nothing here is ever served directly.
UPLOAD_DIR = Path("/var/lib/app/uploads")
MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {"image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
           "image/jpeg": (b"\xff\xd8\xff", ".jpg")}


def store_upload(file_storage, declared_type: str) -> dict:
    if declared_type not in ALLOWED:
        raise ValueError("unsupported content type")

    magic, extension = ALLOWED[declared_type]
    head = file_storage.stream.read(len(magic))
    file_storage.stream.seek(0)
    if head != magic:
        raise ValueError("file content does not match its declared type")

    data = file_storage.stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("file too large")

    # Generated name: the client filename never reaches the filesystem.
    stored_name = f"{secrets.token_hex(16)}{extension}"
    destination = UPLOAD_DIR / stored_name
    destination.write_bytes(data)
    return {"id": stored_name}
