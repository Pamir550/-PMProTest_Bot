import os
import threading
import time
import requests
from flask import Flask, jsonify
from qa_engine import run, summary
from ai_analyzer import analyze

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

API = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)

@app.get("/")
def root():
    return "PMProTest_Bot is running"

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "PMProTest_Bot"})

def tg(method, payload=None):
    r = requests.post(f"{API}/{method}", json=payload or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def send(chat_id, text):
    for i in range(0, len(text), 3800):
        tg("sendMessage", {"chat_id": chat_id, "text": text[i:i+3800]})

def report_text(report, ai=None):
    counts = summary(report)
    lines = [
        "PMProTest_Bot — QA report",
        f"PASS: {counts['PASS']} | WARNING: {counts['WARNING']} | FAIL: {counts['FAIL']} | NOT TESTED: {counts['NOT TESTED']}",
        f"Repository: {report['target_repo']}",
        f"URL: {report['target_url']}",
        "",
    ]
    for x in report["categories"]:
        lines.append(f"{x['category']:02d}. {x['name']}: {x['status']} — {x['detail']}")
    lines.append("")
    lines.append(f"HTTP: {report['http']['status']} — {report['http']['detail']}")

    if ai:
        lines.append("")
        if ai.get("status") == "PASS":
            a = ai.get("analysis", {})
            lines.append("AI analysis:")
            lines.append(str(a.get("summary", "No summary")))
            for issue in a.get("confirmed_issues", [])[:10]:
                lines.append(f"- {issue}")
        elif ai.get("enabled") is False:
            lines.append("AI: not configured")
        else:
            lines.append(f"AI: {ai.get('detail', 'error')}")

    lines.append("")
    lines.append("Read-only: target files/settings/deployments are not modified.")
    return "\n".join(lines)

def handle(message):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start":
        send(chat_id, "PMProTest_Bot\nRead-only QA tester.\n\n/test — 41 categories + AI analysis\n/status — connection status\n/category N — one category")
        return

    if text == "/status":
        report = run()
        send(chat_id, f"Repository: {report['target_repo']}\nURL: {report['target_url']}\nGitHub: {report['repository']['status']}\nHTTP: {report['http']['status']}\nMode: READ-ONLY")
        return

    if text == "/test":
        send(chat_id, "Running read-only QA...")
        report = run()
        ai = analyze(report)
        send(chat_id, report_text(report, ai))
        return

    if text.startswith("/category"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            send(chat_id, "Usage: /category 1")
            return
        n = int(parts[1])
        report = run()
        item = next((x for x in report["categories"] if x["category"] == n), None)
        if not item:
            send(chat_id, "Category must be between 1 and 41.")
        else:
            send(chat_id, f"{item['category']:02d}. {item['name']}\nStatus: {item['status']}\n{item['detail']}")
        return

    send(chat_id, "Unknown command. Use /start.")

def poll():
    offset = 0
    while True:
        try:
            data = tg("getUpdates", {"timeout": 25, "offset": offset})
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    try:
                        handle(message)
                    except Exception:
                        send(message["chat"]["id"], "Test execution error. Check Render logs.")
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
