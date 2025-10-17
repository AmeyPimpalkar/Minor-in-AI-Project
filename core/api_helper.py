# core/api_helper.py
import os
import requests
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".") / ".env")
HF_TOKEN = os.getenv("HF_API_TOKEN")

# Candidate models for classification and text-generation/explanation
CLASSIFY_MODELS = [
    "facebook/bart-large-mnli",
    "MoritzLaurer/mdeberta-v3-base-mnli-xnli",  # fallback if available
]
EXPLAIN_MODELS = [
    "google/flan-t5-large",       # good text generation (if available on HF inference)
    "google/flan-t5-small",
    "google/flan-t5-base"
]

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

def _post_with_retries(url, payload, headers=None, timeout=8, retries=2, backoff=1.2):
    headers = headers or HEADERS
    attempt = 0
    while attempt <= retries:
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            return r
        except Exception as e:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(backoff ** attempt)

def classify_error_hf(text, candidate_labels=None):
    """Zero-shot classification (returns best label or None)."""
    if not HF_TOKEN:
        return None, "HF API token not configured."
    candidate_labels = candidate_labels or ["SyntaxError", "NameError", "IndexError", "KeyError", "AttributeError", "LogicError"]
    for model in CLASSIFY_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {"inputs": text, "parameters": {"candidate_labels": candidate_labels}}
        try:
            r = _post_with_retries(url, payload)
            if r.status_code == 200:
                j = r.json()
                labels = j.get("labels", [])
                scores = j.get("scores", [])
                if labels:
                    return {"label": labels[0], "score": scores[0]}, None
            # try next model
        except Exception as e:
            last_err = str(e)
            continue
    return None, f"All classification attempts failed: {locals().get('last_err', 'none')}"

def explain_with_huggingface(prompt, max_length=256):
    """Return a human readable explanation using a text-generation model."""
    if not HF_TOKEN:
        return "⚠️ HF token missing. Configure HF_API_TOKEN in your .env / deployment secrets."

    # Try explain models one by one (fast fallback)
    for model in EXPLAIN_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {"inputs": prompt, "options": {"wait_for_model": True}, "parameters": {"max_new_tokens": 150}}
        try:
            r = _post_with_retries(url, payload, timeout=12, retries=2)
            if r.status_code == 200:
                j = r.json()
                # different models return different formats; try to extract the text
                if isinstance(j, dict) and j.get("error"):
                    continue
                # many generation endpoints return a list of dicts with 'generated_text'
                if isinstance(j, list) and len(j) and isinstance(j[0], dict):
                    text = j[0].get("generated_text") or j[0].get("text") or str(j[0])
                    return text
                # some endpoints return plain dict with 'generated_text'
                if isinstance(j, dict) and "generated_text" in j:
                    return j["generated_text"]
                # last fallback: str()
                return str(j)
        except Exception:
            continue

    return "⚠️ Could not get a response from external models. Try again later."

# small helper used in UI to both classify & explain
def classify_and_explain(error_message):
    classification, err = classify_error_hf(error_message)
    explanation = None
    if classification:
        label = classification["label"]
        score = classification["score"]
        # Create small explanation prompt for generator
        prompt = f"Explain in simple terms this Python error category '{label}' and what a beginner should do. Keep it short."
        explanation = explain_with_huggingface(prompt)
        return {"label": label, "score": score, "explanation": explanation}, None
    else:
        # fallback: try a raw explanation
        explanation = explain_with_huggingface(f"Explain this Python error: {error_message}")
        return {"label": None, "score": None, "explanation": explanation}, err