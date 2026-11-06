import os
import sqlite3
from flask import g
from config import DATABASE_PATH, BASE_DIR


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Create tables from schema.sql and add a default demo profile."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.executescript(schema)
        has_profile = conn.execute("SELECT 1 FROM profiles LIMIT 1").fetchone()
        if not has_profile:
            conn.execute("INSERT INTO profiles (name, role) VALUES (?, ?)", ("Demo user", "self"))
        conn.commit()
    finally:
        conn.close()
