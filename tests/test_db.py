from news_feeder.db import is_seen, mark_seen


def test_is_seen_returns_false_for_new_guid(db_conn):
    assert is_seen(db_conn, "https://example.com/article/1") is False


def test_mark_seen_then_is_seen(db_conn):
    guid = "https://example.com/article/2"
    mark_seen(db_conn, guid)
    assert is_seen(db_conn, guid) is True


def test_mark_seen_idempotent(db_conn):
    guid = "https://example.com/article/3"
    mark_seen(db_conn, guid)
    mark_seen(db_conn, guid)  # 2回目は INSERT OR IGNORE で無視される
    assert is_seen(db_conn, guid) is True
