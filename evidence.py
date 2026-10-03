import ast
import base64
import os
import requests

TARGET_REPO = os.getenv("TARGET_REPO", "").strip()
TARGET_URL = os.getenv("TARGET_URL", "").strip().rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
RENDER_SERVICE_ID = os.getenv("TARGET_RENDER_SERVICE_ID", "").strip()


def github_headers():
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def render_headers():
    return {"Accept": "application/json", "Authorization": f"Bearer {RENDER_API_KEY}"}


def repo_tree():
    if not TARGET_REPO:
        return {"status": "NOT TESTED", "detail": "TARGET_REPO is not configured", "files": {}}
    url = f"https://api.github.com/repos/{TARGET_REPO}/git/trees/main?recursive=1"
    try:
        r = requests.get(url, headers=github_headers(), timeout=20)
        if r.status_code != 200:
            return {"status": "FAIL", "detail": f"GitHub tree HTTP {r.status_code}", "files": {}}
        data = r.json()
        return {
            "status": "PASS",
            "detail": f"GitHub tree read successfully: {len(data.get('tree', []))} entries",
            "files": {x.get("path", ""): x.get("type", "") for x in data.get("tree", [])},
        }
    except Exception as exc:
        return {"status": "FAIL", "detail": f"GitHub request error: {type(exc).__name__}", "files": {}}


def read_file(path):
    if not TARGET_REPO:
        return None
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/{path}"
    try:
        r = requests.get(url, headers=github_headers(), timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("encoding") != "base64":
            return None
        return base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
    except Exception:
        return None


def inspect_source(content):
    result = {"syntax": "UNKNOWN", "functions": [], "classes": []}
    try:
        tree = ast.parse(content)
        result["syntax"] = "PASS"
        result["functions"] = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        result["classes"] = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    except SyntaxError:
        result["syntax"] = "FAIL"
    return result


def http_probe():
    if not TARGET_URL:
        return {"status": "NOT TESTED", "detail": "TARGET_URL is not configured"}
    try:
        r = requests.get(TARGET_URL + "/health", timeout=20, allow_redirects=True)
        return {
            "status": "PASS" if 200 <= r.status_code < 300 else "WARNING",
            "detail": f"/health HTTP {r.status_code}; {len(r.content)} bytes",
            "status_code": r.status_code,
        }
    except Exception as exc:
        return {"status": "FAIL", "detail": f"HTTP probe error: {type(exc).__name__}"}


def render_probe():
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        return {"status": "NOT TESTED", "detail": "Render read-only credentials are not configured", "last_deploy": {"status": "NOT TESTED"}}
    try:
        service = requests.get(
            f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}",
            headers=render_headers(),
            timeout=20,
        )
        if service.status_code != 200:
            return {"status": "FAIL", "detail": f"Render service HTTP {service.status_code}", "last_deploy": {"status": "NOT TESTED"}}
        s = service.json()
        deploys = requests.get(
            f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=1",
            headers=render_headers(),
            timeout=20,
        )
        last = {"status": "NOT TESTED"}
        if deploys.status_code == 200:
            items = deploys.json()
            if items:
                d = items[0].get("deploy", items[0])
                commit = d.get("commit")
                last = {
                    "status": d.get("status", "UNKNOWN"),
                    "id": d.get("id"),
                    "createdAt": d.get("createdAt"),
                    "finishedAt": d.get("finishedAt"),
                    "commit": commit.get("id") if isinstance(commit, dict) else d.get("commitId"),
                }
        return {
            "status": "PASS",
            "detail": f"Render service read successfully: {s.get('name', RENDER_SERVICE_ID)}",
            "service": {
                "name": s.get("name"),
                "type": s.get("type"),
                "branch": s.get("branch"),
                "suspended": s.get("suspended"),
            },
            "last_deploy": last,
        }
    except Exception as exc:
        return {"status": "FAIL", "detail": f"Render request error: {type(exc).__name__}", "last_deploy": {"status": "NOT TESTED"}}
