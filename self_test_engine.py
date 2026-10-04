import ast
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CHECKS = [
    ("Структура тестировщика", lambda: check_files(["bot.py","qa_engine.py","evidence.py","categories.py"])),
    ("Telegram Bot backend", lambda: check_python("bot.py")),
    ("Flask backend", lambda: check_contains("bot.py", ["Flask", "@app.get", "@app.post"])),
    ("Health endpoint", lambda: check_contains("bot.py", ["/health"])),
    ("Session API", lambda: check_contains("bot.py", ["/api/session"])),
    ("Test start API", lambda: check_contains("bot.py", ["/api/test/start"])),
    ("Test status API", lambda: check_contains("bot.py", ["/api/test/status"])),
    ("Test report API", lambda: check_contains("bot.py", ["/api/test/report"])),
    ("History API", lambda: check_contains("bot.py", ["/api/test/history"])),
    ("Background jobs", lambda: check_contains("bot.py", ["threading.Thread","jobs"])),
    ("Progress tracking", lambda: check_contains("bot.py", ["update_progress","progress"])),
    ("Read-only flag", lambda: check_contains("bot.py", ["read_only"])),
    ("QA engine", lambda: check_python("qa_engine.py")),
    ("Evidence module", lambda: check_python("evidence.py")),
    ("Category definitions", lambda: check_python("categories.py")),
    ("41 categories", lambda: check_category_count()),
    ("AI analyzer syntax", lambda: check_python("ai_analyzer.py")),
    ("Requirements file", lambda: check_files(["requirements.txt"])),
    ("Web index", lambda: check_files(["web/index.html"])),
    ("Web styles", lambda: check_files(["web/styles.css"])),
    ("Web application", lambda: check_files(["web/app.js"])),
    ("Mini App script", lambda: check_contains("web/index.html", ["telegram-web-app.js","app.js"])),
    ("Bottom navigation", lambda: check_contains("web/index.html", ["bottom-nav","results","errors","infra","history"])),
    ("Home screen", lambda: check_contains("web/app.js", ["function home","ТЕСТИРОВАТЬ"])),
    ("Results screen", lambda: check_contains("web/app.js", ["function results","reportList"])),
    ("Errors screen", lambda: check_contains("web/app.js", ["function errors","showCode"])),
    ("GitHub Render screen", lambda: check_contains("web/app.js", ["function infra"])),
    ("History screen", lambda: check_contains("web/app.js", ["function history","/api/test/history"])),
    ("Sections logic", lambda: check_contains("web/app.js", ["function sections"])),
    ("Navigation bindings", lambda: check_contains("web/app.js", ["addEventListener","data-screen"])),
    ("CSS home design", lambda: check_contains("web/styles.css", ["home-hero","home-only"])),
    ("CSS navigation", lambda: check_contains("web/styles.css", ["bottom-nav"])),
    ("CSS tester button", lambda: check_contains("web/styles.css", [".launch"])),
    ("Python syntax scan", lambda: python_syntax_scan()),
    ("No missing local imports", lambda: check_local_imports()),
    ("Environment safety", lambda: check_env()),
    ("Session storage", lambda: check_contains("bot.py", ["sessions = {}","jobs = {}"])),
    ("Thread locking", lambda: check_contains("bot.py", ["lock = threading.Lock()","with lock"])),
    ("Error handling", lambda: check_contains("bot.py", ["except Exception"])),
    ("Static cache control", lambda: check_contains("bot.py", ["Cache-Control","no-store"])),
    ("Server startup", lambda: check_contains("bot.py", ["app.run(","0.0.0.0","PORT"])),
]

def ok(detail="Проверка пройдена"):
    return {"status":"PASS","detail":detail}

def warn(detail):
    return {"status":"WARNING","detail":detail}

def fail(detail):
    return {"status":"FAIL","detail":detail}

def check_files(paths):
    missing=[p for p in paths if not (BASE_DIR/p).is_file()]
    return fail("Отсутствуют: "+", ".join(missing)) if missing else ok("Все необходимые файлы найдены")

def read(path):
    try:
        return (BASE_DIR/path).read_text(encoding="utf-8")
    except Exception:
        return None

def check_python(path):
    content=read(path)
    if content is None:
        return fail("Файл недоступен")
    try:
        ast.parse(content)
        return ok("Python syntax: PASS")
    except SyntaxError as e:
        return fail(f"SyntaxError: line {e.lineno}")

def check_contains(path, needles):
    content=read(path)
    if content is None:
        return fail("Файл недоступен")
    missing=[x for x in needles if x not in content]
    return fail("Не найдено: "+", ".join(missing)) if missing else ok("Все необходимые элементы найдены")

def check_category_count():
    try:
        content=read("categories.py")
        tree=ast.parse(content)
        count=0
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value,int):
                        count+=1
        return ok("Найдено 41 категории") if count==41 else fail(f"Найдено категорий: {count}")
    except Exception as e:
        return fail(type(e).__name__)

def python_syntax_scan():
    bad=[]
    for p in BASE_DIR.rglob("*.py"):
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            bad.append(str(p.relative_to(BASE_DIR)))
    return fail("Ошибки syntax: "+", ".join(bad)) if bad else ok("Все локальные Python-файлы синтаксически корректны")

def check_local_imports():
    required=["flask","requests"]
    missing=[]
    for name in required:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    return fail("Не установлен модуль: "+", ".join(missing)) if missing else ok("Основные runtime-зависимости доступны")

def check_env():
    token=bool(os.getenv("TELEGRAM_BOT_TOKEN","").strip())
    return ok("Telegram token configured") if token else warn("TELEGRAM_BOT_TOKEN не задан в текущем окружении")

def run(progress_callback=None):
    results=[]
    total=len(CHECKS)
    for i,(name,fn) in enumerate(CHECKS,1):
        try:
            result=fn()
        except Exception as e:
            result=fail(f"Исключение: {type(e).__name__}")
        results.append({
            "category":i,
            "name":name,
            "status":result["status"],
            "detail":result["detail"],
            "evidence":[{"path":"PMProTest_Bot","readable":True}],
        })
        if progress_callback:
            progress_callback(i,total,name)
    return {
        "target_repo":"PMProTest_Bot (self-test)",
        "target_url":"local service",
        "repository":{"status":"PASS","detail":"Локальный self-test выполнен","file_count":sum(1 for p in BASE_DIR.rglob("*") if p.is_file())},
        "render":{"status":"NOT TESTED","detail":"Внешний Render не запрашивался в self-test"},
        "http":{"status":"NOT TESTED","detail":"Внешний target URL не запрашивался в self-test"},
        "categories":results,
        "read_only":True,
    }

def summary(report):
    counts={"PASS":0,"WARNING":0,"FAIL":0,"NOT TESTED":0}
    for item in report["categories"]:
        counts[item["status"]]=counts.get(item["status"],0)+1
    return counts
