# GitHub Actions セットアップガイド

## リポジトリ構成

```
your-repo/
├── rss_mail.py
├── README.md
└── .github/
    └── workflows/
        └── rss_mail.yml   ← これがcron定義
```

---

## 手順

### 1. GitHubにprivateリポジトリを作成

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/あなたのユーザー名/rss-mail.git
git push -u origin main
```

> ⚠️ **privateリポジトリ推奨**（RSSフィードURLを公開したくない場合）

---

### 2. Secretsを登録（APIキーの安全な保管）

GitHubリポジトリ → **Settings → Secrets and variables → Actions → New repository secret**

| Secret名 | 値 |
|---------|---|
| `DEEPL_API_KEY` | DeepLのAPIキー（末尾に`:fx`がつく） |
| `GMAIL_ADDRESS` | 送信元Gmailアドレス |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード（16文字） |
| `TO_ADDRESS` | 受信先メールアドレス |

---

### 3. Actionsを有効化

- リポジトリの **Actions タブ** を開く
- 「I understand my workflows, go ahead and enable them」をクリック

---

### 4. 手動で動作確認

**Actions タブ → RSS翻訳メール配信 → Run workflow**

ログを見てエラーがないか確認 ✅

---

### 5. cronのスケジュール変更（任意）

`.github/workflows/rss_mail.yml` の cron 行を編集：

```yaml
# 毎朝7時 JST
- cron: '0 22 * * *'

# 毎朝6時 JST
- cron: '0 21 * * *'

# 6時間ごと
- cron: '0 */6 * * *'
```

> ⚠️ GitHub ActionsのcronはUTC基準。JSTはUTC+9なので、7時JST = 22時UTC（前日）

---

## Artifactによる既読DB管理の仕組み

```
実行①
  └─ DBなし → 全記事を新着扱い → メール送信 → DBをArtifactに保存

実行②
  └─ ArtifactからDBをダウンロード → 既読チェック → 新着のみ送信 → DBを上書き保存
```

- Artifactは **90日間保持**（`retention-days: 90` で変更可能）
- 90日経過後はDBがリセットされるが、既読管理が崩れるだけでメール自体は届く

---

## 無料枠の目安

| リソース | 消費量 | 無料枠 |
|---------|--------|--------|
| GitHub Actions | 〜3分/回 × 30回 = 90分/月 | 2000分/月（private） |
| DeepL | 〜5000文字/回 × 30回 = 15万文字/月 | 50万文字/月 |

→ **完全無料で運用できます** 🎉
