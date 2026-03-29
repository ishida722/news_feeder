# GitHub Actions セットアップガイド

毎朝 7:00 JST に RSS フィードを取得・翻訳してメール配信するワークフローを設定します。

---

## リポジトリ構成

```
news_feeder/
├── pyproject.toml
├── feeds.yml
├── src/news_feeder/
└── .github/
    └── workflows/
        └── rss_mail.yml   ← GitHub Actions ワークフロー定義
```

---

## 手順

### 1. GitHub にリポジトリを作成して push

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/<ユーザー名>/news-feeder.git
git push -u origin main
```

> **private リポジトリ推奨**（フィード URL や設定を公開したくない場合）

---

### 2. Secrets を登録（APIキーの安全な保管）

GitHubリポジトリ → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 名 | 値 |
|-----------|---|
| `DEEPL_API_KEY` | DeepL の API キー（末尾に `:fx` がつく） |
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（16文字） |
| `TO_ADDRESS` | 受信先メールアドレス |

---

### 3. Actions を有効化

1. リポジトリの **Actions タブ** を開く
2. 「I understand my workflows, go ahead and enable them」をクリック

---

### 4. 手動で動作確認

**Actions タブ → RSS翻訳メール配信 → Run workflow → Run workflow**

ログを見てエラーがないか確認します。

よくあるエラー:
- `Error: Resource not accessible by integration` → Secrets が未設定
- `SMTPAuthenticationError` → Gmail アプリパスワードを確認
- `DeepLException` → DeepL API キー（末尾の `:fx`）を確認

---

### 5. スケジュールの変更（任意）

`.github/workflows/rss_mail.yml` の cron 行を編集します：

```yaml
on:
  schedule:
    # 毎朝7時 JST（= UTC 22時）
    - cron: '0 22 * * *'

    # 毎朝6時 JST の場合
    # - cron: '0 21 * * *'

    # 6時間ごとの場合
    # - cron: '0 */6 * * *'
```

> GitHub Actions の cron は **UTC 基準**。JST は UTC+9 なので 7:00 JST = 22:00 UTC（前日）

---

## ワークフローの仕組み

```
実行開始
  ├─ 1. リポジトリをチェックアウト
  ├─ 2. uv をセットアップ・依存パッケージをインストール
  ├─ 3. Artifact から既読 DB（rss_seen.db）をダウンロード
  │      └─ 初回は Artifact なし → スキップ（全記事を新着扱い）
  ├─ 4. news-feeder を実行
  │      ├─ feeds.yml からフィード一覧を読み込み
  │      ├─ 各フィードから新着記事を取得
  │      ├─ DeepL API でタイトル・概要を日本語翻訳
  │      └─ Gmail SMTP でメール送信
  └─ 5. 既読 DB を Artifact として保存（90日間保持）
```

### Artifact による既読 DB の永続化

```
実行①（初回）
  DBなし → 全記事を新着扱い → メール送信 → DB を Artifact に保存

実行②（2回目以降）
  Artifact から DB をダウンロード → 既読チェック → 新着のみ送信 → DB を上書き保存
```

- Artifact は **90日間保持**（`retention-days: 90` で変更可能）
- 90日経過後は DB がリセットされますが、メール自体は引き続き届きます

---

## 無料枠の目安

| リソース | 消費量（目安） | 無料枠 |
|---------|--------------|--------|
| GitHub Actions | 約3分/回 × 30回 = 90分/月 | 2,000分/月（private リポジトリ） |
| DeepL | 約5,000文字/回 × 30回 = 15万文字/月 | 50万文字/月 |

**完全無料で運用できます。**

---

## フィードの追加・変更

コードを変更せず `feeds.yml` を編集するだけです：

```yaml
feeds:
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
  - name: "追加したいフィード名"
    url: "https://example.com/feed.xml"
```

変更後は git commit して push すれば、次回実行から反映されます。
