# news_feeder — Claude 作業コンテキスト

## プロジェクト概要
RSSフィードを取得して日本語に翻訳し、Gmail でメール配信する Python スクリプト。
GitHub Actions で毎朝 7:00 JST (22:00 UTC) に自動実行する。

## ファイル構成

```
news_feeder/
├── CLAUDE.md                      # このファイル（作業コンテキスト）
├── pyproject.toml                 # プロジェクト設定・依存パッケージ（uv 管理）
├── feeds.yml                      # 購読フィード一覧（外部定義）
├── src/
│   └── news_feeder/
│       ├── __init__.py
│       ├── config.py              # CONFIG 設定辞書
│       ├── db.py                  # SQLite 既読管理
│       ├── translate.py           # DeepL 翻訳
│       ├── feeds.py               # フィード取得・翻訳
│       ├── email.py               # メール生成・送信
│       └── main.py                # エントリポイント
├── tests/
│   ├── conftest.py                # pytest フィクスチャ
│   ├── test_db.py
│   ├── test_translate.py
│   └── test_feeds.py
├── .github/
│   └── workflows/
│       └── rss_mail.yml           # GitHub Actions ワークフロー
├── README.md                      # セットアップガイド（日本語）
└── GITHUB_ACTIONS_SETUP.md        # GitHub Actions 設定ガイド（日本語）
```

## 主要な設計決定

- **フィード設定**: `feeds.yml` で管理（Python コードを触らずに追加・削除可能）
- **既読管理**: SQLite (`rss_seen.db`) でGUID管理。GitHub Actions では Artifact で永続化
- **翻訳**: DeepL Free API（月50万字まで無料）。失敗時は原文を返す
- **メール送信**: Gmail SMTP SSL（ポート465）。アプリパスワード必須
- **重複防止**: 記事のGUIDをDBに記録。新着のみ翻訳・送信

## 設定（環境変数）

| 変数名 | 用途 |
|--------|------|
| `DEEPL_API_KEY` | DeepL Free API キー |
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（16文字） |
| `TO_ADDRESS` | 配信先メールアドレス |

## ローカル実行

```bash
# 依存パッケージのインストール（uv）
uv sync

# 実行
export DEEPL_API_KEY=xxx GMAIL_ADDRESS=xxx GMAIL_APP_PASSWORD=xxx TO_ADDRESS=xxx
uv run news-feeder

# テスト実行
uv run pytest
```

## feeds.yml の形式

```yaml
feeds:
  - name: "フィード名"
    url: "https://example.com/feed.xml"
  - name: "Another Feed"
    url: "https://another.com/rss"
```

## GitHub Actions

- ワークフロー: `.github/workflows/rss_mail.yml`
- トリガー: 毎日 22:00 UTC (7:00 JST)、または手動実行
- Secrets 登録が必要: `DEEPL_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `TO_ADDRESS`
- DB は Artifact `rss-seen-db` として90日間保持

## 今後の改善候補

- `feeds.yml` にカテゴリ（タグ）フィールドを追加してメール内で分類表示
- DeepL 以外の翻訳 API への切り替えオプション
- 記事フィルタリング（キーワードで除外など）
