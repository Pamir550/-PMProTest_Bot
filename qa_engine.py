from categories import CATEGORIES
from evidence import repo_tree, read_file, http_probe

def run():
    tree = repo_tree()
    files = tree["files"]
    results = []

    for number, (name, required) in CATEGORIES.items():
        missing = [p for p in required if p not in files]
        evidence = []
        for path in required:
            if path in files:
                content = read_file(path)
                evidence.append({"path": path, "readable": content is not None, "size": len(content) if content is not None else None})

        if tree["status"] != "PASS":
            status = "NOT TESTED"
            detail = tree["detail"]
        elif missing:
            status = "WARNING"
            detail = "Missing expected file(s): " + ", ".join(missing)
        else:
            status = "PASS"
            detail = "Expected repository evidence found"

        results.append({"category": number, "name": name, "status": status, "detail": detail, "evidence": evidence})

    return {
        "target_repo": __import__("os").getenv("TARGET_REPO", "not configured"),
        "target_url": __import__("os").getenv("TARGET_URL", "not configured"),
        "repository": {"status": tree["status"], "detail": tree["detail"], "file_count": len(files)},
        "http": http_probe(),
        "categories": results,
        "read_only": True,
    }

def summary(report):
    counts = {"PASS": 0, "WARNING": 0, "FAIL": 0, "NOT TESTED": 0}
    for x in report["categories"]:
        counts[x["status"]] += 1
    return counts
