# RSS翻訳メール配信スクリプト セットアップガイド

## 必要なもの

- Python 3.10+
- DeepL アカウント（無料）
- Gmail アカウント（Gmailアプリパスワード）

---

## 1. パッケージインストール

```bash
pip install feedparser requests
```

---

## 2. DeepL APIキーの取得

1. https://www.deepl.com/ja/pro-api にアクセス
2. 無料プランで登録（クレカ不要）
3. アカウント設定 → 「認証キー」をコピー

無料枠: **50万文字/月**（ニュース用途なら十分）

---

## 3. Gmail アプリパスワードの設定

1. Googleアカウント → セキュリティ → **2段階認証を有効化**
2. 「アプリパスワード」を検索 → 新規作成（名前は何でもOK）
3. 生成された16文字のパスワードをコピー

> 通常のGmailパスワードは使えません。アプリパスワードが必要です。

---

## 4. 環境変数の設定（推奨）

```bash
export DEEPL_API_KEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx"
export GMAIL_ADDRESS="your_address@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export TO_ADDRESS="recipient@example.com"
```

または `rss_mail.py` の `CONFIG` 内に直接書いてもOK（パスワード管理に注意）。

---

## 5. RSSフィードの追加・変更

`rss_mail.py` の `RSS_FEEDS` リストを編集：

```python
RSS_FEEDS = [
    {"name": "Jacobin",     "url": "https://jacobin.com/feed/"},
    {"name": "TechCrunch",  "url": "https://techcrunch.com/feed/"},
    # 追加したいフィードをここに...
]
```

---

## 6. 手動実行テスト

```bash
python rss_mail.py
```

初回はすべての記事が「新着」扱いになるので、`MAX_ARTICLES_PER_FEED` を小さくしておくと安全：

```python
"MAX_ARTICLES_PER_FEED": 3,  # テスト時は少なめに
```

---

## 7. cron で定期実行

```bash
crontab -e
```

毎朝7時に実行する例：

```cron
0 7 * * * cd /path/to/rss_translator && /usr/bin/python3 rss_mail.py >> /path/to/rss_translator/rss_mail.log 2>&1
```

6時間ごとに実行する例：

```cron
0 */6 * * * cd /path/to/rss_translator && /usr/bin/python3 rss_mail.py >> /path/to/rss_translator/rss_mail.log 2>&1
```

---

## ファイル構成

```
rss_translator/
├── rss_mail.py     # メインスクリプト
├── rss_seen.db     # 既読管理DB（自動生成）
└── rss_mail.log    # 実行ログ（自動生成）
```

---

## よくある問題

| 症状 | 原因 | 対処 |
|------|------|------|
| メール送信エラー | アプリパスワード未設定 | 2段階認証→アプリパスワード発行 |
| 翻訳されない | DeepL APIキー間違い | `:fx` サフィックスを確認 |
| 同じ記事が何度も届く | DB削除された | `rss_seen.db` を消さない |
| フィード取得失敗 | URL間違い・サービス側問題 | ログ確認 |
