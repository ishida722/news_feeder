"""ネットワークテスト: feeds.yml の各URLへの実際のアクセスと記事取得を検証する

通常の pytest 実行ではスキップされます。
実行するには -m network オプションを指定してください:

    uv run pytest -m network -v
"""

import feedparser
import pytest

from news_feeder.feeds import load_feeds
from pathlib import Path

FEEDS_YML = Path(__file__).parent.parent / "feeds.yml"

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def feeds():
    return load_feeds(str(FEEDS_YML))


@pytest.fixture(scope="module")
def parsed_feeds(feeds):
    """全フィードを実際にフェッチしてキャッシュする"""
    return {feed["name"]: feedparser.parse(feed["url"]) for feed in feeds}


class TestFeedUrlsAccessible:
    """各フィードURLが実際にアクセス可能かを検証する"""

    def test_all_feeds_return_no_http_error(self, feeds, parsed_feeds):
        """全フィードでHTTPエラー(4xx/5xx)が発生しないこと"""
        for feed in feeds:
            result = parsed_feeds[feed["name"]]
            status = getattr(result, "status", None)
            assert status is None or status < 400, (
                f"{feed['name']} が HTTP {status} を返しました: {feed['url']}"
            )

    def test_all_feeds_return_entries(self, feeds, parsed_feeds):
        """全フィードに1件以上の記事エントリが含まれること"""
        for feed in feeds:
            result = parsed_feeds[feed["name"]]
            assert len(result.entries) > 0, (
                f"{feed['name']} のエントリが0件です: {feed['url']}"
            )

    def test_all_entries_have_title(self, feeds, parsed_feeds):
        """各フィードの先頭エントリにタイトルが存在すること"""
        for feed in feeds:
            result = parsed_feeds[feed["name"]]
            if not result.entries:
                continue
            entry = result.entries[0]
            title = entry.get("title", "")
            assert title, (
                f"{feed['name']} の先頭エントリにタイトルがありません: {feed['url']}"
            )

    def test_all_entries_have_link(self, feeds, parsed_feeds):
        """各フィードの先頭エントリにリンクが存在すること"""
        for feed in feeds:
            result = parsed_feeds[feed["name"]]
            if not result.entries:
                continue
            entry = result.entries[0]
            link = entry.get("link", "")
            assert link, (
                f"{feed['name']} の先頭エントリにリンクがありません: {feed['url']}"
            )
