import subprocess
import sqlite3

ALLOWED_SORT = {"created_at", "name", "email"}


def find_user(conn: sqlite3.Connection, email: str):
    cur = conn.cursor()
    cur.execute("SELECT id, email, role FROM users WHERE email = ?", (email,))
    return cur.fetchone()


def list_users(conn: sqlite3.Connection, sort: str, limit: int):
    # Identifiers cannot be parameterized, so they are allowlisted instead.
    column = sort if sort in ALLOWED_SORT else "created_at"
    bounded = max(1, min(int(limit), 100))
    return conn.execute(
        f"SELECT id, email FROM users ORDER BY {column} LIMIT ?", (bounded,)
    ).fetchall()


def make_thumbnail(source_path: str, dest_path: str) -> None:
    # argv form: no shell, so filenames cannot inject commands.
    subprocess.run(
        ["convert", source_path, "-resize", "200x200", dest_path],
        shell=False,
        check=True,
        timeout=30,
    )
