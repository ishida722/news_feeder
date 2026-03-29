import sqlite3

import pytest

from news_feeder.db import init_db


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    """インメモリSQLiteコネクションを返すフィクスチャ"""
    conn = init_db(":memory:")
    yield conn
    conn.close()


def pytest_collection_modifyitems(config, items):
    """`-m network` が指定されていない場合、networkマーク付きテストをスキップする"""
    marker_expr = config.getoption("-m", default="")
    if "network" not in marker_expr:
        skip = pytest.mark.skip(reason="ネットワークテストは '-m network' を付けて実行してください")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip)
