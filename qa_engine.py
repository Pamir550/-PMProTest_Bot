import os
from categories import CATEGORIES
from evidence import inspect_source, read_file, repo_tree, http_probe, render_probe


def run(progress_callback=None):
    tree = repo_tree()
    files = tree["files"]
    results = []
    total = len(CATEGORIES)

    for index, (number, spec) in enumerate(CATEGORIES.items(), start=1):
        name, required = spec
        missing = [p for p in required if p not in files]
        evidence = []
        syntax_fail = False
        readable_fail = False
        function_count = 0

        for path in required:
            if path in files:
                content = read_file(path)
                item = {"path": path, "readable": content is not None}
                if content is None:
                    readable_fail = True
                else:
                    info = inspect_source(content) if path.endswith(".py") else {"syntax": "NOT_APPLICABLE", "functions": [], "classes": []}
                    item.update(info)
                    function_count += len(info.get("functions", []))
                    syntax_fail = syntax_fail or info.get("syntax") == "FAIL"
                evidence.append(item)

        if tree["status"] != "PASS":
            status, detail = "NOT TESTED", tree["detail"]
        elif missing:
            status, detail = "WARNING", "Missing expected file(s): " + ", ".join(missing)
        elif readable_fail or syntax_fail:
            status, detail = "FAIL", "File could not be read or Python syntax check failed"
        else:
            status, detail = "PASS", f"Repository evidence found; {function_count} Python function(s) inspected"

        results.append({
            "category": number,
            "name": name,
            "status": status,
            "detail": detail,
            "evidence": evidence,
        })
        if progress_callback:
            progress_callback(index, total, name)

    return {
        "target_repo": os.getenv("TARGET_REPO", "not configured"),
        "target_url": os.getenv("TARGET_URL", "not configured"),
        "repository": {"status": tree["status"], "detail": tree["detail"], "file_count": len(files)},
        "render": render_probe(),
        "http": http_probe(),
        "categories": results,
        "read_only": True,
    }


def summary(report):
    counts = {"PASS": 0, "WARNING": 0, "FAIL": 0, "NOT TESTED": 0}
    for x in report["categories"]:
        counts[x["status"]] += 1
    return counts
