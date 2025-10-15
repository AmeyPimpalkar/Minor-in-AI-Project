import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DATA_PATH = Path("data/error_training_data.json")
MODEL_PATH = Path("models/error_classifier.pkl")

# Load dataset safely
if not DATA_PATH.exists():
    raise FileNotFoundError(f" Training data not found at {DATA_PATH}")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [item.get("error_message", "") for item in data if "error_message" in item]
labels = [item.get("category", "Unknown") for item in data if "category" in item]

# Sanity check
if not texts or not labels:
    raise ValueError("⚠️ Training data seems empty or malformed.")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42
)

# Create pipeline (TF-IDF + Naive Bayes)
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(X_train, y_train)

# Evaluate model
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("✅ Model trained successfully!")
print(f"Accuracy: {accuracy:.2f}")
print("\nClassification Report:\n", classification_report(y_test, predictions))

# Save trained model
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print(f"\n Model saved successfully at: {MODEL_PATH.resolve()}")