import json
import os
import random

from flask import Flask, jsonify, render_template, request

# Updated import to include get_details for precautions and nutrition
from utils.entity_extractor import extract_symptoms, get_possible_conditions, get_details
from utils.nlp import predict_intent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents.json")

# Load Intent data
with open(INTENTS_PATH, "r", encoding="utf-8") as file:
    intents_data = json.load(file)

INTENT_RESPONSES = {
    intent["tag"]: intent.get("responses", [])
    for intent in intents_data.get("intents", [])
}

PRIORITY_TAGS = {"greeting", "goodbye", "fallback"}

app = Flask(__name__, template_folder="templates")


def format_name(value):
    """Formats internal names (e.g., fungal_infection) to readable titles (Fungal Infection)."""
    return value.replace("_", " ").strip().title()


def pick_response(tag):
    responses = INTENT_RESPONSES.get(tag, [])
    if not responses:
        return None
    return random.choice(responses)


def add_confidence(response, confidence):
    """Appends confidence level if it's reasonably high."""
    if confidence >= 0.8:
        return f"{response}\n\n*Confidence: {confidence:.0%}*"
    return response


def build_symptom_response(symptoms, confidence):
    """
    Core logic: Fetches possible conditions, then grabs matching 
    precautions and nutrition tips for the top result.
    """
    conditions = get_possible_conditions(symptoms)

    if conditions:
        # Take the most likely condition (first match) to provide specific details
        primary_condition = conditions[0]
        details = get_details(primary_condition)
        
        formatted_conditions = ", ".join(format_name(item) for item in conditions[:3])
        
        # Format precautions into a clean list
        precautions_list = "\n".join([f"- {p}" for p in details['precautions']])
        
        response = (
            f"Based on your symptoms, this could be related to: **{formatted_conditions}**.\n\n"
            f"📋 **Precautions to take:**\n{precautions_list}\n\n"
            f"🍎 **Dietary Advice:**\n{details['nutrition']}\n\n"
            "⚠️ *Disclaimer: This is an automated suggestion. If symptoms are severe, please consult a medical professional.*"
        )
    else:
        # If symptoms are found but no disease match exists in our dataset
        formatted_symptoms = ", ".join(format_name(item) for item in symptoms[:5])
        response = (
            f"I noticed these symptoms: **{formatted_symptoms}**, but I couldn't find a specific diagnosis in my records.\n\n"
            "**General Suggestions:**\n"
            "- Monitor your temperature\n"
            "- Rest and stay hydrated\n"
            "- Consult a doctor if you feel worse."
        )

    return add_confidence(response, confidence)


def generate_response(message):
    intent, confidence = predict_intent(message)
    symptoms = extract_symptoms(message)

    # 1. Handle Priority Greetings/Goodbyes
    if intent in PRIORITY_TAGS:
        response = pick_response(intent) or "I am here to help with general health questions."
        return add_confidence(response, confidence)

    # 2. Handle Symptom detection
    if symptoms:
        return build_symptom_response(symptoms, confidence)

    # 3. Handle General Intents
    response = pick_response(intent)
    if response:
        return add_confidence(response, confidence)

    # 4. Fallback if nothing matches
    fallback = pick_response("fallback") or "Please rephrase your health-related question."
    return fallback


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    # Supports both JSON and Form data for flexibility
    data = request.get_json(silent=True) or request.form
    message = str(data.get("message", "")).strip() if data else ""

    if not message:
        return jsonify({"response": "Please type a message so I can help you."})

    response = generate_response(message)
    return jsonify({"response": response})


if __name__ == "__main__":
    # Crucial for Render: Bind to the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    # 'debug=True' should be disabled in a real production environment, 
    # but is fine for testing.
    app.run(host="0.0.0.0", port=port)
