import json, os, datetime

PROGRESS_DB = "db/progress.json"

def log_progress(username, task_id, passed, total, code, duration):
    """Append progress to db/progress.json"""
    entry = {
        "username": username,
        "task_id": task_id,
        "passed": passed,
        "total": total,
        "code": code,
        "timestamp": datetime.datetime.now().isoformat(),
        "duration_seconds": duration
    }
    
    # Load old progress
    if os.path.exists(PROGRESS_DB):
        with open(PROGRESS_DB, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    # Append new entry
    data.append(entry)
    
    # Save back
    with open(PROGRESS_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)