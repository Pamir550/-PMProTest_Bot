import base64
import os
from typing import Any, Dict
import requests

TARGET_REPO = os.getenv("TARGET_REPO", "").strip()
TARGET_URL = os.getenv("TARGET_URL", "").strip().rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

def headers():
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

def repo_tree():
    if not TARGET_REPO:
        return {"status": "NOT TESTED", "detail": "TARGET_REPO is not configured", "files": {}}
    url = f"https://api.github.com/repos/{TARGET_REPO}/git/trees/main?recursive=1"
    try:
        r = requests.get(url, headers=headers(), timeout=20)
        if r.status_code != 200:
            return {"status": "FAIL", "detail": f"GitHub tree HTTP {r.status_code}", "files": {}}
        data = r.json()
        return {"status": "PASS", "detail": f"GitHub tree read successfully: {len(data.get('tree', []))} entries", "files": {x.get("path", ""): x.get("type", "") for x in data.get("tree", [])}}
    except Exception as e:
        return {"status": "FAIL", "detail": f"GitHub request error: {type(e).__name__}", "files": {}}

def read_file(path: str):
    if not TARGET_REPO:
        return None
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{path}"
    try:
        r = requests.get(url, headers=headers(), timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("encoding") != "base64":
            return None
        return base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
    except Exception:
        return None

def http_probe():
    if not TARGET_URL:
        return {"status": "NOT TESTED", "detail": "TARGET_URL is not configured"}
    try:
        r = requests.get(TARGET_URL + "/health", timeout=20, allow_redirects=True)
        return {"status": "PASS" if 200 <= r.status_code < 300 else "WARNING", "detail": f"/health HTTP {r.status_code}; {len(r.content)} bytes", "status_code": r.status_code}
    except Exception as e:
        return {"status": "FAIL", "detail": f"HTTP probe error: {type(e).__name__}"}
