import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# 1. Load your intents dataset
print("Loading dataset...")
with open('data/intents.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

tags = []
patterns = []

# Extract all patterns and their corresponding tags
for intent in data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])

# 2. Vectorize the text data (THIS fits the vectorizer!)
print("Fitting vectorizer...")
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(patterns)
y = tags

# 3. Train the model
print("Training model...")
model = LogisticRegression(random_state=42, max_iter=200)
model.fit(X, y)

# 4. Save the fitted vectorizer and trained model
# Create the 'model' directory if it doesn't exist
os.makedirs('model', exist_ok=True)

with open('model/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

with open('model/intent_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Training complete! Model and vectorizer saved in the 'model/' folder.")
