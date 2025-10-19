import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.naive_bayes import MultinomialNB 
from sklearn.svm import LinearSVC 
from sklearn.pipeline import Pipeline 
from sklearn.model_selection import train_test_split, GridSearchCV 
from sklearn.metrics import classification_report, accuracy_score

DATA_PATH = Path("data/error_training_data.json")
MODEL_PATH = Path("models/error_classifier.pkl")

# Load dataset safely 
if not DATA_PATH.exists():
    raise FileNotFoundError(f" Training data not found at {DATA_PATH}")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"⚠️ Error decoding JSON from {DATA_PATH}: {e}")

# Extract texts and labels, handling potential missing keys 
texts = [item.get("error_message", "") for item in data]
labels = [item.get("category", "Unknown") for item in data]

# Sanity check the data
if not texts or not labels or len(texts) != len(labels):
    raise ValueError("⚠️ Training data seems empty, malformed, or texts/labels mismatch.")
if len(set(labels)) < 2:
    raise ValueError("⚠️ Training data requires at least two distinct classes (labels).")

print(f"Loaded {len(texts)} samples.")

# Pipeline for explicit naming of steps
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LinearSVC(dual="auto")) # Using LinearSVC, dual="auto" is often recommended
])

# Define parameter ranges to search. 
parameters = {
    'tfidf__ngram_range': [(1, 1), (1, 2)], 
    'tfidf__max_df': [0.85, 0.95, 1.0],     
    'tfidf__min_df': [1, 2],                
    'clf__C': [0.1, 1, 10],                
    
}

# Perform Grid Search with Cross-Validation 
print("Starting GridSearchCV (this might take a while)...")
grid_search = GridSearchCV(pipeline, parameters, cv=5, n_jobs=-1, verbose=1)
grid_search.fit(texts, labels) 

# Report Best Results
print("\n--- Grid Search Results ---")
print(f"✅ Best parameters found: {grid_search.best_params_}")
print(f"✅ Best cross-validation accuracy score: {grid_search.best_score_:.3f}")

# Evaluate Best Model on a Hold-Out Test Set
print("\n--- Evaluating on Hold-Out Test Set ---")
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42, stratify=labels 
)

best_model = grid_search.best_estimator_ 
# best_model.fit(X_train, y_train)
predictions = best_model.predict(X_test)
final_accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy on hold-out test set: {final_accuracy:.3f}")
print("\nClassification Report on hold-out test set:\n", classification_report(y_test, predictions, zero_division=0))

# Best Trained Model Saved
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(MODEL_PATH, "wb") as f:
    pickle.dump(best_model, f)

print(f"\n✅ Best model saved successfully at: {MODEL_PATH.resolve()}")