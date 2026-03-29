import textwrap

import pytest

from news_feeder.feeds import load_feeds


def test_load_feeds_returns_list(tmp_path):
    feeds_file = tmp_path / "feeds.yml"
    feeds_file.write_text(
        textwrap.dedent("""\
        feeds:
          - name: "Test Feed"
            url: "https://example.com/feed.xml"
          - name: "Another Feed"
            url: "https://another.com/rss"
        """),
        encoding="utf-8",
    )
    feeds = load_feeds(str(feeds_file))
    assert len(feeds) == 2
    assert feeds[0]["name"] == "Test Feed"
    assert feeds[1]["url"] == "https://another.com/rss"


def test_load_feeds_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_feeds(str(tmp_path / "nonexistent.yml"))


def test_load_feeds_empty_feeds_key(tmp_path):
    feeds_file = tmp_path / "feeds.yml"
    feeds_file.write_text("feeds: []\n", encoding="utf-8")
    feeds = load_feeds(str(feeds_file))
    assert feeds == []
