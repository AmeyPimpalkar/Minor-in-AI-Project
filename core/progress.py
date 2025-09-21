# core/progress.py
import json
import os
from datetime import datetime

PROGRESS_DB = "data/progress.json"
TASKS_DB = "data/coding_task.json"

def log_progress(username, task_id, passed, total, code, duration):
    """Log progress into progress.json with difficulty info."""
    record = {
        "username": username,
        "task_id": task_id,
        "passed": passed,
        "total": total,
        "code": code,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": duration,
        "difficulty": get_difficulty(task_id)
    }

    os.makedirs(os.path.dirname(PROGRESS_DB), exist_ok=True)
    data = []
    if os.path.exists(PROGRESS_DB):
        try:
            with open(PROGRESS_DB, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            data = []

    data.append(record)

    with open(PROGRESS_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_progress(username=None):
    if not os.path.exists(PROGRESS_DB):
        return []
    try:
        with open(PROGRESS_DB, "r", encoding="utf-8") as f:
            data = json.load(f)
            if username:
                return [d for d in data if d["username"] == username]
            return data
    except json.JSONDecodeError:
        return []

def get_difficulty(task_id):
    """Fetch difficulty from coding_task.json if available."""
    if not os.path.exists(TASKS_DB):
        return "Unknown"
    try:
        with open(TASKS_DB, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            for t in tasks:
                if t.get("id") == task_id:
                    return t.get("difficulty", "Unknown")
    except Exception:
        pass
    return "Unknown"