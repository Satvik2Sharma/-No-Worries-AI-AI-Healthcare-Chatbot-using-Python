import pandas as pd
import re
import os

# -----------------------------
# DYNAMIC PATH HANDLING
# -----------------------------
# This finds the absolute path to your 'data' folder
# Since this file is in 'utils/', we go up one level (..) to reach the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "data", "symptoms.csv.zip")

# -----------------------------
# LOAD DATASET
# -----------------------------
try:
    # Pandas automatically detects the CSV inside the .zip
    symptoms_df = pd.read_csv(ZIP_PATH, compression='zip')
    print("✅ Successfully loaded symptoms.csv.zip")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    # Fallback to an empty dataframe so the app doesn't crash entirely
    symptoms_df = pd.DataFrame(columns=["diseases"])

# Normalize column names
symptoms_df.columns = [col.lower().strip() for col in symptoms_df.columns]
DISEASE_COLUMN = "diseases"
SYMPTOM_LOOKUP = {
    re.sub(r"[^a-zA-Z0-9\s]", "", col.lower()).strip(): col 
    for col in symptoms_df.columns if col != DISEASE_COLUMN
}

def clean_text(text):
    text = text.lower()
    return re.sub(r"[^a-zA-Z0-9\s]", "", text)

def extract_symptoms(user_input):
    cleaned_input = clean_text(user_input)
    detected_symptoms = []

    for cleaned_column, original_column in SYMPTOM_LOOKUP.items():
        pattern = rf"\b{re.escape(cleaned_column)}\b"
        if re.search(pattern, cleaned_input) and original_column not in detected_symptoms:
            detected_symptoms.append(original_column)

    return detected_symptoms

def get_possible_conditions(symptoms):
    results = []
    for symptom in symptoms:
        if symptom in symptoms_df.columns:
            matching_rows = symptoms_df[symptoms_df[symptom] == 1]
            diseases = matching_rows[DISEASE_COLUMN].dropna().astype(str).tolist()
            results.extend(diseases)
    return list(dict.fromkeys(results))
