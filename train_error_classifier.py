import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Load data
with open("data/error_training_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract texts and labels
texts = [item["error_message"] for item in data]
labels = [item["category"] for item in data]

# Split for validation
X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

# Create a text classification pipeline (TF-IDF + Naive Bayes)
model = make_pipeline(TfidfVectorizer(), MultinomialNB())

# Train
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
print("✅ Model trained successfully!")
print("Accuracy:", accuracy_score(y_test, predictions))
print("\nClassification Report:\n", classification_report(y_test, predictions))

# Save model
with open("models/error_classifier.pkl", "wb") as f:
    pickle.dump(model, f)

print("\n💾 Model saved as models/error_classifier.pkl")