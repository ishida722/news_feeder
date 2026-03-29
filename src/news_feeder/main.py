#!/usr/bin/env python3
"""
RSS翻訳メール配信スクリプト
- RSSフィードを取得して日本語に翻訳し、メールで配信する
- SQLiteで既読管理（重複送信防止）
- DeepL無料APIで翻訳
- Gmail SMTPでメール送信
"""

import logging
import os

from .config import CONFIG
from .db import init_db
from .email import build_email_html, send_email
from .feeds import fetch_new_articles, load_feeds

# ── ログ設定 ──────────────────────────────────────────────
_handlers: list = [logging.StreamHandler()]
# GitHub Actions環境ではファイルログをスキップ（CI=true が自動でセットされる）
if not os.environ.get("CI"):
    _handlers.append(logging.FileHandler("rss_mail.log", encoding="utf-8"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=== RSS翻訳メール配信 開始 ===")
    conn = init_db(CONFIG["DB_PATH"])
    rss_feeds = load_feeds()

    all_articles = []
    for feed in rss_feeds:
        try:
            articles = fetch_new_articles(
                feed,
                conn,
                CONFIG["DEEPL_API_KEY"],
                CONFIG["MAX_ARTICLES_PER_FEED"],
                CONFIG["MAX_TRANSLATE_CHARS"],
            )
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"フィード処理エラー ({feed['name']}): {e}")

    if not all_articles:
        logger.info("新着記事なし。メール送信をスキップします。")
        return

    html = build_email_html(all_articles)
    send_email(html, len(all_articles), CONFIG)
    logger.info(f"=== 完了: {len(all_articles)} 件配信 ===")


if __name__ == "__main__":
    main()
