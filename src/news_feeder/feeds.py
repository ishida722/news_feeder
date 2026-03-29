import logging
import re
import sqlite3
import time

import feedparser
import yaml

from .db import is_seen, mark_seen
from .translate import translate_deepl

logger = logging.getLogger(__name__)


def load_feeds(feeds_path: str = "feeds.yml") -> list[dict]:
    """feeds.yml からフィード一覧を読み込む"""
    try:
        with open(feeds_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        feeds = data.get("feeds", [])
        logger.info(f"feeds.yml から {len(feeds)} 件のフィードを読み込みました")
        return feeds
    except FileNotFoundError:
        logger.error(f"{feeds_path} が見つかりません。feeds.yml を作成してください。")
        raise


def fetch_new_articles(
    feed: dict,
    conn: sqlite3.Connection,
    api_key: str,
    max_articles: int,
    max_chars: int,
) -> list[dict]:
    """新着記事を取得して翻訳済みリストを返す"""
    logger.info(f"フィード取得: {feed['name']} ({feed['url']})")
    parsed = feedparser.parse(feed["url"])
    if parsed.bozo:
        logger.warning(f"フィード解析エラー: {feed['name']}")

    articles = []
    for entry in parsed.entries[:max_articles]:
        guid = entry.get("id") or entry.get("link", "")
        if not guid or is_seen(conn, guid):
            continue

        title_orig = entry.get("title", "(タイトルなし)")
        summary_orig = entry.get("summary", entry.get("description", ""))

        # HTMLタグを簡易除去
        summary_orig = re.sub(r"<[^>]+>", "", summary_orig).strip()

        title_ja = translate_deepl(title_orig, api_key, max_chars)
        time.sleep(0.3)  # API rate limit対策
        summary_ja = translate_deepl(summary_orig, api_key, max_chars)
        time.sleep(0.3)

        articles.append(
            {
                "feed_name": feed["name"],
                "title": title_ja,
                "title_orig": title_orig,
                "summary": summary_ja,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "guid": guid,
            }
        )
        mark_seen(conn, guid)

    logger.info(f"  → 新着 {len(articles)} 件")
    return articles
