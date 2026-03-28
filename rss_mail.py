#!/usr/bin/env python3
"""
RSS翻訳メール配信スクリプト
- RSSフィードを取得して日本語に翻訳し、メールで配信する
- SQLiteで既読管理（重複送信防止）
- DeepL無料APIで翻訳
- Gmail SMTPでメール送信
"""

import feedparser
import sqlite3
import smtplib
import os
import time
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import requests

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

# ── 設定（環境変数 or 直接書き換えてOK） ────────────────────
CONFIG = {
    # DeepL
    "DEEPL_API_KEY": os.environ.get("DEEPL_API_KEY", "YOUR_DEEPL_API_KEY"),
    # Gmail SMTP
    "GMAIL_ADDRESS": os.environ.get("GMAIL_ADDRESS", "your_address@gmail.com"),
    "GMAIL_APP_PASSWORD": os.environ.get("GMAIL_APP_PASSWORD", "YOUR_APP_PASSWORD"),
    "TO_ADDRESS": os.environ.get("TO_ADDRESS", "recipient@example.com"),
    # DB
    "DB_PATH": "rss_seen.db",
    # 1リクエストあたりの翻訳文字数上限（DeepL無料枠節約のため）
    "MAX_TRANSLATE_CHARS": 1500,
    # フィード1件あたりの最大取得記事数
    "MAX_ARTICLES_PER_FEED": 10,
}

# ── 購読RSSフィード一覧 ──────────────────────────────────
RSS_FEEDS = [
    # テック・AI
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    # 政治・国際
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews"},
    # ビジネス・経済
    {"name": "FT", "url": "https://www.ft.com/?format=rss"},
    # 左派・論考
    {"name": "Jacobin", "url": "https://jacobin.com/feed/"},
    # ↑ ここにフィードを追加してね！
]


# ── DB初期化 ────────────────────────────────────────────
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


# ── DeepL翻訳 ───────────────────────────────────────────
def translate_deepl(text: str, api_key: str, max_chars: int = 1500) -> str:
    """DeepL Free APIで翻訳（文字数制限あり）"""
    if not text or not text.strip():
        return ""
    text = text[:max_chars]
    try:
        resp = requests.post(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": api_key,
                "text": text,
                "target_lang": "JA",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]
    except Exception as e:
        logger.warning(f"翻訳失敗: {e}")
        return text  # 失敗時は原文を返す


# ── RSS取得＆翻訳 ────────────────────────────────────────
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
        import re
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


# ── メール生成 ───────────────────────────────────────────
def build_email_html(all_articles: list[dict]) -> str:
    """記事リストをHTML形式のメール本文に整形"""
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    total = len(all_articles)

    # フィード別にグループ化
    from collections import defaultdict
    grouped: dict[str, list] = defaultdict(list)
    for a in all_articles:
        grouped[a["feed_name"]].append(a)

    sections = ""
    for feed_name, articles in grouped.items():
        items = ""
        for a in articles:
            items += f"""
            <div style="margin-bottom:20px; padding:16px; background:#fff;
                        border-radius:8px; border-left:4px solid #4f46e5;">
              <a href="{a['link']}" style="font-size:16px; font-weight:bold;
                 color:#1e1b4b; text-decoration:none;">
                {a['title']}
              </a>
              <div style="font-size:11px; color:#9ca3af; margin:4px 0 8px;">
                {a['title_orig']} ／ {a['published']}
              </div>
              <p style="font-size:14px; color:#374151; margin:0; line-height:1.7;">
                {a['summary'] or '（要約なし）'}
              </p>
              <a href="{a['link']}" style="font-size:12px; color:#4f46e5;">
                続きを読む →
              </a>
            </div>"""

        sections += f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:18px; color:#4f46e5; border-bottom:2px solid #e0e7ff;
                     padding-bottom:8px; margin-bottom:16px;">
            📰 {feed_name}
          </h2>
          {items}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif; background:#f3f4f6;
             margin:0; padding:0;">
  <div style="max-width:680px; margin:0 auto; padding:24px;">
    <div style="background:#4f46e5; color:white; padding:20px 24px;
                border-radius:12px 12px 0 0;">
      <h1 style="margin:0; font-size:22px;">🌐 海外ニュース翻訳ダイジェスト</h1>
      <p style="margin:4px 0 0; font-size:13px; opacity:.8;">
        {now} ／ 新着 {total} 件
      </p>
    </div>
    <div style="background:#f9fafb; padding:24px; border-radius:0 0 12px 12px;">
      {sections if sections else '<p style="color:#6b7280;">新着記事はありませんでした。</p>'}
    </div>
    <p style="text-align:center; font-size:11px; color:#9ca3af; margin-top:16px;">
      このメールはRSS翻訳スクリプトにより自動送信されています
    </p>
  </div>
</body>
</html>"""
    return html


# ── メール送信 ───────────────────────────────────────────
def send_email(html_body: str, article_count: int, cfg: dict) -> None:
    subject = (
        f"[RSS翻訳] 新着{article_count}件 "
        f"- {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["GMAIL_ADDRESS"]
    msg["To"] = cfg["TO_ADDRESS"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(cfg["GMAIL_ADDRESS"], cfg["GMAIL_APP_PASSWORD"])
        server.sendmail(cfg["GMAIL_ADDRESS"], cfg["TO_ADDRESS"], msg.as_string())
    logger.info(f"メール送信完了 → {cfg['TO_ADDRESS']}")


# ── メイン ───────────────────────────────────────────────
def main():
    logger.info("=== RSS翻訳メール配信 開始 ===")
    conn = init_db(CONFIG["DB_PATH"])

    all_articles = []
    for feed in RSS_FEEDS:
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
