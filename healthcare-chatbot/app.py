import json
import os
import random

from flask import Flask, jsonify, render_template, request

from utils.entity_extractor import extract_symptoms, get_possible_conditions
from utils.nlp import predict_intent


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents.json")

with open(INTENTS_PATH, "r", encoding="utf-8") as file:
    intents_data = json.load(file)

INTENT_RESPONSES = {
    intent["tag"]: intent.get("responses", [])
    for intent in intents_data.get("intents", [])
}

PRIORITY_TAGS = {"greeting", "goodbye", "fallback"}

app = Flask(__name__, template_folder="templates")


def format_name(value):
    return value.replace("_", " ").strip().title()


def pick_response(tag):
    responses = INTENT_RESPONSES.get(tag, [])
    if not responses:
        return None
    return random.choice(responses)


def add_confidence(response, confidence):
    if confidence >= 0.8:
        return f"{response}\n\nConfidence: {confidence:.0%}"
    return response


def build_symptom_response(symptoms, confidence):
    conditions = get_possible_conditions(symptoms)

    if conditions:
        formatted_conditions = ", ".join(format_name(item) for item in conditions[:5])
        response = (
            f"You may be experiencing symptoms related to: {formatted_conditions}.\n"
            "Suggestions:\n"
            "- Rest\n"
            "- Stay hydrated\n\n"
            "This is not a diagnosis. Please consult a doctor if symptoms persist."
        )
    else:
        formatted_symptoms = ", ".join(format_name(item) for item in symptoms[:5])
        response = (
            f"I noticed these symptoms: {formatted_symptoms}.\n"
            "Suggestions:\n"
            "- Rest\n"
            "- Stay hydrated\n\n"
            "This is not a diagnosis. Please consult a doctor if symptoms persist."
        )

    return add_confidence(response, confidence)


def generate_response(message):
    intent, confidence = predict_intent(message)
    symptoms = extract_symptoms(message)

    if intent in PRIORITY_TAGS:
        response = pick_response(intent) or "I am here to help with general health questions."
        return add_confidence(response, confidence)

    if symptoms:
        return build_symptom_response(symptoms, confidence)

    response = pick_response(intent)
    if response:
        return add_confidence(response, confidence)

    fallback = pick_response("fallback") or "Please rephrase your health-related question."
    return fallback


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or request.form
    message = str(data.get("message", "")).strip() if data else ""

    if not message:
        return jsonify({"response": "Please type a message so I can help you."})

    response = generate_response(message)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)