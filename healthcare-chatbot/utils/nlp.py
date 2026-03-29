import pickle
import re
import os

# 1. Safety Check: Make sure the model files actually exist!
if not os.path.exists("model/intent_model.pkl") or not os.path.exists("model/vectorizer.pkl"):
    raise FileNotFoundError("❌ Model files are missing! Please run 'python train.py' first.")

# 2. Load trained model and fitted vectorizer
model = pickle.load(open("model/intent_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text

def predict_intent(user_input, threshold=0.15):
    cleaned = clean_text(user_input)
    
    # This transform works now because the vectorizer is fitted!
    vector = vectorizer.transform([cleaned]) 

    probabilities = model.predict_proba(vector)[0]
    max_prob = max(probabilities)
    predicted_index = probabilities.argmax()
    predicted_tag = model.classes_[predicted_index]

    # Trigger fallback if confidence is too low
    if max_prob < threshold:
        return "fallback", max_prob

    return predicted_tag, max_prob
