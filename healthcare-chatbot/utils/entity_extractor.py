import pandas as pd
import re

# Load dataset
symptoms_df = pd.read_csv("data/symptoms.csv")

# Normalize column names (important)
symptoms_df.columns = [col.lower() for col in symptoms_df.columns]
DISEASE_COLUMN = "diseases"
SYMPTOM_LOOKUP = {}

for column in symptoms_df.columns:
    if column == DISEASE_COLUMN:
        continue
    cleaned_column = re.sub(r"[^a-zA-Z0-9\s]", "", column.lower()).strip()
    if cleaned_column:
        SYMPTOM_LOOKUP[cleaned_column] = column

# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text

# -----------------------------
# EXTRACT SYMPTOMS FROM USER INPUT
# -----------------------------
def extract_symptoms(user_input):
    cleaned_input = clean_text(user_input)
    detected_symptoms = []

    for cleaned_column, original_column in SYMPTOM_LOOKUP.items():
        pattern = rf"\b{re.escape(cleaned_column)}\b"
        if re.search(pattern, cleaned_input) and original_column not in detected_symptoms:
            detected_symptoms.append(original_column)

    return detected_symptoms

# -----------------------------
# GET POSSIBLE CONDITIONS
# -----------------------------
def get_possible_conditions(symptoms):
    results = []

    for symptom in symptoms:
        if symptom in symptoms_df.columns:
            matching_rows = symptoms_df[symptoms_df[symptom] == 1]
            diseases = matching_rows[DISEASE_COLUMN].dropna().astype(str).tolist()
            results.extend(diseases)

    return list(dict.fromkeys(results))
