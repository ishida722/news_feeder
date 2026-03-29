import sqlite3
from datetime import datetime


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_articles (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            guid    TEXT UNIQUE NOT NULL,
            seen_at TEXT NOT NULL
        )
    """
    )
    conn.commit()
    return conn


def is_seen(conn: sqlite3.Connection, guid: str) -> bool:
    cur = conn.execute("SELECT 1 FROM seen_articles WHERE guid = ?", (guid,))
    return cur.fetchone() is not None


def mark_seen(conn: sqlite3.Connection, guid: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO seen_articles (guid, seen_at) VALUES (?, ?)",
        (guid, datetime.now().isoformat()),
    )
    conn.commit()
