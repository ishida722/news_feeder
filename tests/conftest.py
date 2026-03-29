import sqlite3

import pytest

from news_feeder.db import init_db


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    """インメモリSQLiteコネクションを返すフィクスチャ"""
    conn = init_db(":memory:")
    yield conn
    conn.close()
