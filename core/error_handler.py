import json
import os

ERRORS_DB = "data/errors.json"

def load_errors():
    """Load error explanations safely from JSON."""
    if os.path.exists(ERRORS_DB):
        try:
            with open(ERRORS_DB, "r") as f:
                content = f.read().strip()
                if not content:  # if file is empty
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}

def explain_error(error_message):
    """Return explanation and hint if error found in DB."""
    errors = load_errors()
    for err_name, details in errors.items():
        if err_name in error_message:  # simple substring match
            return details["explanation"], details["fix_hint"], details["example_code"]
    return None, None, None