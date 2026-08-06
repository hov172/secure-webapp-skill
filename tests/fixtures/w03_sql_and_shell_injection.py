import os
import sqlite3


def find_user(conn: sqlite3.Connection, email: str):
    cur = conn.cursor()
    cur.execute("SELECT id, email, role FROM users WHERE email = '" + email + "'")
    return cur.fetchone()


def make_thumbnail(filename: str) -> None:
    os.system(f"convert {filename} -resize 200x200 /var/www/thumbs/{filename}")
