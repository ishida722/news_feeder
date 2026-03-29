# news_feeder — RSS翻訳メール配信

RSSフィードを取得して日本語に翻訳し、Gmail でメール配信する Python スクリプト。
GitHub Actions で毎朝 7:00 JST に自動実行します。

## 機能

- 複数の RSS フィードを `feeds.yml` で管理
- DeepL API で記事タイトル・概要を日本語翻訳
- Gmail SMTP でメール配信
- SQLite で既読管理（重複配信を防止）
- GitHub Actions で完全自動運行（完全無料）

---

## ファイル構成

```
news_feeder/
├── pyproject.toml                 # プロジェクト設定・依存パッケージ（uv 管理）
├── feeds.yml                      # 購読フィード一覧
├── src/
│   └── news_feeder/
│       ├── config.py              # 設定値
│       ├── db.py                  # SQLite 既読管理
│       ├── translate.py           # DeepL 翻訳
│       ├── feeds.py               # フィード取得・翻訳
│       ├── email.py               # メール生成・送信
│       └── main.py                # エントリポイント
├── tests/                         # pytest テスト
└── .github/
    └── workflows/
        └── rss_mail.yml           # GitHub Actions ワークフロー
```

---

## セットアップ（ローカル実行）

### 1. 事前準備

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) のインストール

```bash
# uv のインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 依存パッケージのインストール

```bash
uv sync
```

### 3. DeepL API キーの取得

1. https://www.deepl.com/ja/pro-api にアクセス
2. 無料プランで登録（クレカ不要）
3. アカウント設定 → 「認証キー」をコピー

無料枠: **50万文字/月**（ニュース用途なら十分）

### 4. Gmail アプリパスワードの設定

1. Google アカウント → セキュリティ → **2段階認証を有効化**
2. 「アプリパスワード」を検索 → 新規作成（名前は何でもOK）
3. 生成された 16 文字のパスワードをコピー

> 通常の Gmail パスワードは使えません。アプリパスワードが必要です。

### 5. 環境変数の設定

```bash
export DEEPL_API_KEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx"
export GMAIL_ADDRESS="your_address@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export TO_ADDRESS="recipient@example.com"
```

### 6. RSS フィードの設定

`feeds.yml` を編集してフィードを追加・削除します（Python コードの変更不要）：

```yaml
feeds:
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
  - name: "Reuters World"
    url: "https://feeds.reuters.com/reuters/worldNews"
  # 追加したいフィードをここに...
  # - name: "フィード名"
  #   url: "https://example.com/feed.xml"
```

### 7. 実行

```bash
uv run news-feeder
```

初回はすべての記事が「新着」扱いになります。テスト時は `feeds.yml` のフィード数を減らすと安全です。

### 8. テスト実行

```bash
uv run pytest
```

---

## GitHub Actions で自動実行

毎朝 7:00 JST (22:00 UTC) に自動でメール配信されます。詳細な設定手順は **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** を参照してください。

**概要:**
1. このリポジトリを GitHub に push（private 推奨）
2. リポジトリの Settings → Secrets に 4 つの環境変数を登録
3. Actions タブでワークフローを有効化

---

## 設定（環境変数一覧）

| 変数名 | 用途 |
|--------|------|
| `DEEPL_API_KEY` | DeepL Free API キー（末尾に `:fx`） |
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（16文字） |
| `TO_ADDRESS` | 配信先メールアドレス |

---

## よくある問題

| 症状 | 原因 | 対処 |
|------|------|------|
| メール送信エラー | アプリパスワード未設定 | 2段階認証 → アプリパスワード発行 |
| 翻訳されない | DeepL APIキー間違い | `:fx` サフィックスを確認 |
| 同じ記事が何度も届く | DB が削除された | `rss_seen.db` を消さない |
| フィード取得失敗 | URL 間違い・サービス側問題 | ログ確認 |
| `uv: command not found` | uv 未インストール | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
