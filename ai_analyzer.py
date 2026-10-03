import json
import os
import requests

AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-120b").strip()

SYSTEM = """You are a software QA report analyzer.
Use ONLY the supplied test evidence.
Do not invent runtime results.
Do not claim a component is broken when evidence is insufficient.
Separate observed facts from hypotheses.
Return concise JSON with:
summary, confirmed_issues, warnings, not_tested, next_checks.
Each confirmed issue must cite the supplied category/evidence."""

def analyze(report):
    if not AI_API_KEY:
        return {"enabled": False, "reason": "AI_API_KEY is not configured"}

    payload = {
        "model": AI_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(report, ensure_ascii=False)},
        ],
    }
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            AI_BASE_URL + "/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if r.status_code != 200:
            return {"enabled": True, "status": "FAIL", "detail": f"AI HTTP {r.status_code}"}
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"summary": content}
        return {"enabled": True, "status": "PASS", "analysis": parsed}
    except Exception as e:
        return {"enabled": True, "status": "FAIL", "detail": f"AI request error: {type(e).__name__}"}
