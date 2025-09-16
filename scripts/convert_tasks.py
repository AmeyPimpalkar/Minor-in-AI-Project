# scripts/convert_tasks.py
import json, os

SRC = "data/coding_task.json"
OUT = "data/coding_task_converted.json"

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

new = []
for task in data:
    t = dict(task)  # copy
    if "test_cases" not in t:
        ex_in = t.pop("example_input", "")
        ex_out = t.pop("expected_output", "")
        t["test_cases"] = [{"input": ex_in, "expected_output": ex_out}]
    new.append(t)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(new, f, indent=2)

print("Wrote", OUT)