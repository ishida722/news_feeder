import logging
import smtplib
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def build_email_html(all_articles: list[dict]) -> str:
    """記事リストをHTML形式のメール本文に整形"""
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    total = len(all_articles)

    # フィード別にグループ化
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
