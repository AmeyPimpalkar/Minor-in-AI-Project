import json

ERRORS_DB = "data/errors.json"

def load_errors():
    """Load error explanations from JSON."""
    with open(ERRORS_DB, "r") as f:
        return json.load(f)

def explain_error(error_message):
    """Return explanation and hint if error found in DB."""
    errors = load_errors()
    for err_name, details in errors.items():
        if err_name in error_message:  # simple substring match
            return details["explanation"], details["fix_hint"], details["example_code"]
    return None, None, None