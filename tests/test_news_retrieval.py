"""ニュース取得に関するテスト

- feeds.yml の各URLが正しい形式かどうかの検証
- fetch_new_articles による記事取得ロジックのテスト
"""

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from news_feeder.db import init_db
from news_feeder.feeds import fetch_new_articles, load_feeds

FEEDS_YML = Path(__file__).parent.parent / "feeds.yml"


# ---------------------------------------------------------------------------
# feeds.yml の URL 検証テスト
# ---------------------------------------------------------------------------


class TestFeedsYmlUrls:
    """feeds.yml に定義されたURLが正しい形式であることを確認する"""

    @pytest.fixture(autouse=True)
    def load(self):
        self.feeds = load_feeds(str(FEEDS_YML))

    def test_feeds_not_empty(self):
        """feeds.yml に1件以上のフィードが定義されていること"""
        assert len(self.feeds) >= 1

    def test_all_feeds_have_name(self):
        """すべてのフィードに name が存在すること"""
        for feed in self.feeds:
            assert "name" in feed, f"name がありません: {feed}"
            assert feed["name"], f"name が空です: {feed}"

    def test_all_feeds_have_url(self):
        """すべてのフィードに url が存在すること"""
        for feed in self.feeds:
            assert "url" in feed, f"url がありません: {feed}"
            assert feed["url"], f"url が空です: {feed}"

    def test_all_urls_are_http_or_https(self):
        """すべてのURLが http または https スキームであること"""
        for feed in self.feeds:
            parsed = urlparse(feed["url"])
            assert parsed.scheme in ("http", "https"), (
                f"{feed['name']} のURL スキームが不正です: {feed['url']}"
            )

    def test_all_urls_have_netloc(self):
        """すべてのURLにホスト名が含まれること"""
        for feed in self.feeds:
            parsed = urlparse(feed["url"])
            assert parsed.netloc, (
                f"{feed['name']} のURLにホスト名がありません: {feed['url']}"
            )

    def test_all_urls_have_no_whitespace(self):
        """URLに空白が含まれていないこと"""
        for feed in self.feeds:
            assert " " not in feed["url"], (
                f"{feed['name']} のURLに空白が含まれています: {feed['url']}"
            )


# ---------------------------------------------------------------------------
# fetch_new_articles の取得ロジックテスト
# ---------------------------------------------------------------------------


def _make_entry(guid: str, title: str = "Title", summary: str = "Summary") -> SimpleNamespace:
    """feedparser のエントリを模擬するオブジェクトを返す"""
    return SimpleNamespace(
        id=guid,
        link=f"https://example.com/{guid}",
        title=title,
        summary=summary,
        published="Sun, 01 Jan 2025 00:00:00 +0000",
        get=lambda key, default="": getattr(
            SimpleNamespace(id=guid, link=f"https://example.com/{guid}",
                            title=title, summary=summary,
                            published="Sun, 01 Jan 2025 00:00:00 +0000"),
            key, default,
        ),
    )


def _make_parsed(entries: list, bozo: bool = False) -> SimpleNamespace:
    """feedparser.parse の戻り値を模擬する"""
    return SimpleNamespace(entries=entries, bozo=bozo)


def _entry(guid: str, title: str = "Title", summary: str = "Summary") -> MagicMock:
    """feedparser エントリの MagicMock を返す"""
    e = MagicMock()
    e.get = lambda key, default="": {
        "id": guid,
        "link": f"https://example.com/{guid}",
        "title": title,
        "summary": summary,
        "published": "Sun, 01 Jan 2025 00:00:00 +0000",
    }.get(key, default)
    return e


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


@pytest.fixture
def feed():
    return {"name": "Test Feed", "url": "https://example.com/feed.xml"}


class TestFetchNewArticles:
    """fetch_new_articles の動作を検証する"""

    def test_returns_new_article(self, conn, feed):
        """未既読の記事が1件返されること"""
        entries = [_entry("guid-1", title="Hello World", summary="An article.")]
        parsed = SimpleNamespace(entries=entries, bozo=False)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            articles = fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert len(articles) == 1
        assert articles[0]["title"] == "Hello World"
        assert articles[0]["guid"] == "guid-1"
        assert articles[0]["feed_name"] == "Test Feed"

    def test_skips_already_seen_article(self, conn, feed):
        """既読の記事はスキップされること"""
        from news_feeder.db import mark_seen
        mark_seen(conn, "guid-seen")

        entries = [_entry("guid-seen", title="Old News")]
        parsed = SimpleNamespace(entries=entries, bozo=False)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            articles = fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert articles == []

    def test_marks_article_as_seen_after_fetch(self, conn, feed):
        """取得後に記事が既読としてマークされること"""
        from news_feeder.db import is_seen
        entries = [_entry("guid-new")]
        parsed = SimpleNamespace(entries=entries, bozo=False)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert is_seen(conn, "guid-new")

    def test_respects_max_articles_limit(self, conn, feed):
        """max_articles の上限が適用されること"""
        entries = [_entry(f"guid-{i}") for i in range(10)]
        parsed = SimpleNamespace(entries=entries, bozo=False)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            articles = fetch_new_articles(feed, conn, api_key="dummy", max_articles=3, max_chars=500)

        assert len(articles) == 3

    def test_returns_empty_on_no_entries(self, conn, feed):
        """エントリが0件のフィードは空リストを返すこと"""
        parsed = SimpleNamespace(entries=[], bozo=False)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            articles = fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert articles == []

    def test_strips_html_from_summary(self, conn, feed):
        """サマリーからHTMLタグが除去されること"""
        entries = [_entry("guid-html", summary="<p>Hello <b>World</b></p>")]
        parsed = SimpleNamespace(entries=entries, bozo=False)

        captured = {}

        def fake_translate(text, *args, **kwargs):
            captured["summary"] = text
            return text

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=fake_translate), \
             patch("news_feeder.feeds.time.sleep"):
            fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert "<p>" not in captured.get("summary", "")
        assert "<b>" not in captured.get("summary", "")

    def test_bozo_feed_still_processes_entries(self, conn, feed):
        """パースエラー (bozo=True) のフィードでも記事を処理すること"""
        entries = [_entry("guid-bozo", title="Bozo Entry")]
        parsed = SimpleNamespace(entries=entries, bozo=True)

        with patch("news_feeder.feeds.feedparser.parse", return_value=parsed), \
             patch("news_feeder.feeds.translate_deepl", side_effect=lambda text, *a, **kw: text), \
             patch("news_feeder.feeds.time.sleep"):
            articles = fetch_new_articles(feed, conn, api_key="dummy", max_articles=10, max_chars=500)

        assert len(articles) == 1
