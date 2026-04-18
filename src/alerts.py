"""
MoltStreet Intelligence — Alert System
Email alerts + future: Discord/Telegram webhooks.
"""
import os
import smtplib
import urllib.request
import urllib.error
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_alert(results: list[dict], fg_data: dict) -> bool:
    """Send email alert for high-signal results.
    Returns True if sent successfully.
    """
    from src.config import EMAIL_FROM, EMAIL_TO, ALERT_THRESHOLD

    app_pw = os.environ.get("SMTP_PASSWORD") or os.environ.get("Mail_appassword", "")
    if not app_pw:
        print("  [INFO] No email credentials set (SMTP_PASSWORD). Skipping email.")
        return False

    alerts = [r for r in results if r["score"] >= ALERT_THRESHOLD]
    if not alerts:
        return False

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fg_index = fg_data.get("index", "?")
    fg_label = fg_data.get("label", "")

    # Plain text body
    lines = [f"MOLTSTREET INTELLIGENCE — {len(alerts)} ALERT(S) — {now}", ""]
    lines.append(f"Market Sentiment: F&G {fg_index} ({fg_label})")
    lines.append("")
    for r in alerts:
        signals = ", ".join(r.get("signals", [])[:4])
        lines.append(f"  {r['symbol']}: Score {r['score']} | ${r['price']:.4f} | {r['rating']}")
        if signals:
            lines.append(f"    → {signals}")
    lines.append("")
    lines.append("Not financial advice. DYOR.")

    text_body = "\n".join(lines)

    # HTML body
    rows_html = ""
    for r in alerts:
        color = "#ff4444" if r["score"] >= 78 else "#ffaa00"
        signals = " | ".join(r.get("signals", [])[:4])
        rows_html += (
            f'<tr>'
            f'<td style="padding:8px;font-weight:bold;color:#fff;">{r["symbol"]}</td>'
            f'<td style="padding:8px;color:{color};font-weight:bold;">{r["score"]}</td>'
            f'<td style="padding:8px;color:#aef;">${r["price"]:.4f}</td>'
            f'<td style="padding:8px;color:#0df;">{r["rating"]}</td>'
            f'<td style="padding:8px;color:#999;font-size:12px;">{signals}</td>'
            f'</tr>'
        )

    html_body = (
        f'<!DOCTYPE html><html><body style="background:#0d0d0d;color:#eee;font-family:monospace;padding:20px;">'
        f'<h2 style="color:#0df;">MoltStreet Intelligence — {len(alerts)} ALERT(S)</h2>'
        f'<p style="color:#888;">Market: F&G {fg_index} ({fg_label}) | {now}</p>'
        f'<table style="width:100%;border-collapse:collapse;margin-top:16px;">'
        f'<thead><tr style="background:#111;color:#888;text-align:left;">'
        f'<th style="padding:8px;">SYM</th><th>SCORE</th><th>PRICE</th><th>SIGNAL</th><th>WHY</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        f'<p style="color:#555;margin-top:20px;font-size:11px;">Not financial advice. DYOR.</p>'
        f'</body></html>'
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ MoltStreet: {len(alerts)} signal(s) | {now[:10]}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_FROM, app_pw)
            s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"  ✅ Email sent → {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"  ❌ Email error: {e}")
        return False


def send_telegram_alert(results: list[dict], fg_data: dict) -> bool:
    """Send Telegram alert for high-signal results.
    Returns True if sent successfully.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("  [INFO] Telegram credentials not set. Skipping Telegram alert.")
        return False

    from src.config import ALERT_THRESHOLD

    alerts = [r for r in results if r["score"] >= ALERT_THRESHOLD]
    if not alerts:
        return False

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fg_index = fg_data.get("index", "?")
    fg_label = fg_data.get("label", "")

    # Build message
    message_lines = [
        f"⚡ *MoltStreet Intelligence* — {len(alerts)} ALERT(S)",
        f"🕒 {now}",
        f"📊 Market Sentiment: F&G {fg_index} ({fg_label})",
        "",
    ]
    for r in alerts[:10]:  # Limit to 10 to avoid huge messages
        symbol = r["symbol"]
        score = r["score"]
        price = r["price"]
        rating = r["rating"]
        signals = ", ".join(r.get("signals", [])[:3])
        line = f"• *{symbol}*: Score {score} | ${price:.4f} | {rating}"
        if signals:
            line += f" → {signals}"
        message_lines.append(line)
    if len(alerts) > 10:
        message_lines.append(f"• ... and {len(alerts) - 10} more")
    message_lines.append("")
    message_lines.append("_Not financial advice. DYOR._")

    message = "\n".join(message_lines)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"  ✅ Telegram alert sent → chat {chat_id}")
                return True
            else:
                print(f"  ❌ Telegram error: HTTP {resp.status}")
                return False
    except urllib.error.URLError as e:
        print(f"  ❌ Telegram error: {e.reason}")
        return False
    except Exception as e:
        print(f"  ❌ Telegram error: {e}")
        return False