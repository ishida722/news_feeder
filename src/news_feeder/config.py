import os

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
