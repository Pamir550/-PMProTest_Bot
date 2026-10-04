import os
import secrets
import threading
import time
from urllib.parse import quote

import requests
from flask import Flask, jsonify, request, send_from_directory

from ai_analyzer import analyze
from self_test_engine import run, summary

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

API = f"https://api.telegram.org/bot{TOKEN}"
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://pmprotest-bot-1.onrender.com/").strip().rstrip("/")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "web"), static_url_path="/static")
sessions = {}
jobs = {}
history = []
lock = threading.Lock()


def tg(method, payload=None):
    r = requests.post(f"{API}/{method}", json=payload or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def send(chat_id, text, reply_markup=None):
    for i in range(0, len(text), 3800):
        payload = {"chat_id": chat_id, "text": text[i:i + 3800]}
        if reply_markup and i == 0:
            payload["reply_markup"] = reply_markup
        tg("sendMessage", payload)


def mini_app_markup(session_id):
    url = f"{WEBAPP_URL}/?session={quote(session_id)}&ui=7"
    return {"inline_keyboard": [[{"text": "Открыть Mini App", "web_app": {"url": url}}]]}


def start_job(session_id):
    with lock:
        job = jobs.get(session_id)
        if not job or job["status"] == "running":
            return False
        job.update({"status": "running", "progress": 0, "report": None, "error": None})

    def worker():
        try:
            report = run(progress_callback=lambda current, total, item: update_progress(session_id, current, total, item))
            report["ai"] = analyze(report)
            with lock:
                jobs[session_id].update({"status": "completed", "progress": 100, "report": report})
                history.insert(0, {
                    "session": session_id,
                    "created_at": time.time(),
                    "summary": summary(report),
                    "target": jobs[session_id]["target"],
                })
                del history[10:]
        except Exception as exc:
            with lock:
                jobs[session_id].update({"status": "failed", "error": type(exc).__name__, "progress": 100})

    threading.Thread(target=worker, daemon=True).start()
    return True


def update_progress(session_id, current, total, item):
    with lock:
        if session_id in jobs:
            completed = jobs[session_id].setdefault("completed_categories", [])
            if not completed or completed[-1].get("number") != current:
                completed.append({"number": current, "name": item, "done": True})
            jobs[session_id].update({
                "progress": int(current * 100 / max(total, 1)),
                "current": current,
                "total": total,
                "current_name": item,
                "categories": completed[-10:],
            })


def handle(message):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start":
        with lock:
            sessions[chat_id] = {"stage": "name"}
        send(chat_id, "Добро пожаловать! 👋\n\nЯ — PMSignalPro Tester\nБот для полной проверки вашего проекта на GitHub и Render (только чтение).\n\nДля начала отправьте:\n1. Имя вашего бота\n2. Username вашего бота\n\nНапример:\nИмя: PMSignalPro\nUsername: @PMSignalPro_bot")
        return

    with lock:
        state = sessions.get(chat_id)

    if state and state.get("stage") == "name" and text and not text.startswith("/"):
        with lock:
            sessions[chat_id] = {"stage": "username", "name": text}
        send(chat_id, "Теперь отправьте username этого бота.\n\nНапример: @PMSignalPro_bot")
        return

    if state and state.get("stage") == "username" and text and not text.startswith("/"):
        session_id = secrets.token_urlsafe(18)
        target = {"name": state["name"], "username": text}
        with lock:
            sessions[chat_id] = {"stage": "ready", "target": target, "session": session_id}
            jobs[session_id] = {"status": "ready", "progress": 0, "target": target}
        send(chat_id, f"Данные сохранены!\n\nИмя: {target['name']}\nUsername: {target['username']}\n\nТеперь откройте мини приложение для тестирования.", mini_app_markup(session_id))
        return

    if text == "/status":
        send(chat_id, "Откройте Mini App → GitHub/Render для read-only статуса.")
        return

    if text == "/test":
        with lock:
            state = sessions.get(chat_id)
        if not state or not state.get("session"):
            send(chat_id, "Сначала отправьте /start и укажите имя и username бота.")
            return
        start_job(state["session"])
        send(chat_id, "Полная read-only проверка запущена в Mini App.")
        return

    send(chat_id, "Отправьте /start, чтобы начать тестирование.")


def poll():
    offset = 0
    try:
        # This bot uses long polling; remove an old webhook so getUpdates can work.
        tg("deleteWebhook", {"drop_pending_updates": False})
        print("[telegram] polling initialized", flush=True)
    except Exception as exc:
        print(f"[telegram] webhook cleanup failed: {type(exc).__name__}: {exc}", flush=True)

    while True:
        try:
            data = tg("getUpdates", {"timeout": 25, "offset": offset, "allowed_updates": ["message"]})
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    try:
                        handle(message)
                    except Exception as exc:
                        print(f"[telegram] message handling failed: {type(exc).__name__}: {exc}", flush=True)
                        try:
                            send(message["chat"]["id"], "Ошибка обработки запроса. Проверьте Render logs.")
                        except Exception as send_exc:
                            print(f"[telegram] error reply failed: {type(send_exc).__name__}: {send_exc}", flush=True)
        except Exception as exc:
            print(f"[telegram] getUpdates failed: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(5)


@app.get("/")
def root():
    response = send_from_directory(app.static_folder, "index.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "PMProTest_Bot", "read_only": True})


@app.get("/api/session")
def api_session():
    sid = request.args.get("session", "")
    with lock:
        job = jobs.get(sid)
        if not job:
            return jsonify({"ok": False, "error": "session_not_found"}), 404
        return jsonify({"ok": True, "target": job["target"], "status": job["status"]})


@app.post("/api/test/start")
def api_test_start():
    sid = request.args.get("session", "")
    if not start_job(sid):
        return jsonify({"ok": False, "error": "already_running_or_invalid"}), 409
    return jsonify({"ok": True})


@app.get("/api/test/status")
def api_test_status():
    sid = request.args.get("session", "")
    with lock:
        job = jobs.get(sid)
        if not job:
            return jsonify({"ok": False, "error": "session_not_found"}), 404
        return jsonify({k: job.get(k) for k in ("status", "progress", "current", "total", "current_name", "categories", "error")})


@app.get("/api/test/report")
def api_test_report():
    sid = request.args.get("session", "")
    with lock:
        job = jobs.get(sid)
        if not job or not job.get("report"):
            return jsonify({"ok": False, "error": "report_not_ready"}), 404
        return jsonify({"ok": True, "report": job["report"]})


@app.get("/api/test/history")
def api_test_history():
    with lock:
        return jsonify({"ok": True, "history": history})


if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
