import joblib
import os

MODEL_PATH = "models/error_classifier.pkl"
VECTORIZER_PATH = "models/vectorizer.pkl"

def load_ai_model():
    # Safely load the trained AI model and its vectorizer if available.
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        print("⚠️ AI model not found. Please run train_error_classifier.py to train it first.")
        return None, None

    try:
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        return model, vectorizer
    except Exception as e:
        print(f"⚠️ Failed to load AI model: {e}")
        return None, None

def predict_error_category(error_message):
    # Takes an error message and predicts its category and confidence.
    model, vectorizer = load_ai_model()
    if model is None or vectorizer is None:
        return {"category": None, "confidence": 0.0}

    X = vectorizer.transform([error_message])
    prediction = model.predict(X)[0]
    confidence = max(model.predict_proba(X)[0])
    return {"category": prediction, "confidence": confidence}

