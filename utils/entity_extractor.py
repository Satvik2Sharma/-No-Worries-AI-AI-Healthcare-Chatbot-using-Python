import csv
import io
import zipfile
import re
import os
import pandas as pd
import gc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "data", "symptoms.csv.zip")
PRECAUTIONS_PATH = os.path.join(BASE_DIR, "data", "precautions.csv")
NUTRITION_PATH = os.path.join(BASE_DIR, "data", "nutrition.xlsx")

# Global data stores
DISEASE_MAP = {}
SYMPTOM_LOOKUP = {}
PRECAUTION_MAP = {}
NUTRITION_MAP = {}

def load_all_data():
    global SYMPTOM_LOOKUP, DISEASE_MAP, PRECAUTION_MAP, NUTRITION_MAP
    
    # 1. Load Symptoms (Streaming ZIP to save RAM)
    if os.path.exists(ZIP_PATH):
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as z:
                csv_filename = z.namelist()[0] 
                with z.open(csv_filename) as f:
                    wrapper = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.DictReader(wrapper)
                    disease_col = next((h for h in reader.fieldnames if h.lower().strip() == "diseases"), "diseases")
                    symptom_cols = [h for h in reader.fieldnames if h != disease_col]
                    
                    for s in symptom_cols:
                        clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", s.lower()).strip()
                        SYMPTOM_LOOKUP[clean_name] = s
                        DISEASE_MAP[s] = set()

                    for row in reader:
                        disease = row.get(disease_col)
                        if disease:
                            for s in symptom_cols:
                                if str(row.get(s, "0")).strip().split('.')[0] == '1':
                                    DISEASE_MAP[s].add(disease.strip())
            for s in DISEASE_MAP: DISEASE_MAP[s] = list(DISEASE_MAP[s])
            print("✅ Symptoms loaded.")
        except Exception as e: print(f"❌ Symptom Error: {e}")

    # 2. Load Precautions (CSV)
    if os.path.exists(PRECAUTIONS_PATH):
        try:
            with open(PRECAUTIONS_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader) # Skip header
                for row in reader:
                    if len(row) > 1:
                        disease = row[0].strip().lower()
                        precautions = [p.strip() for p in row[1:] if p.strip()]
                        PRECAUTION_MAP[disease] = precautions
            print("✅ Precautions loaded.")
        except Exception as e: print(f"❌ Precaution Error: {e}")

    # 3. Load Nutrition (Excel - Memory sensitive)
    if os.path.exists(NUTRITION_PATH):
        try:
            # We load, extract to dict, then DELETE the dataframe immediately
            df_nut = pd.read_excel(NUTRITION_PATH)
            # Assuming columns: 'Disease' and 'Diet'
            for _, row in df_nut.iterrows():
                disease = str(row[0]).strip().lower()
                diet = str(row[1]).strip()
                NUTRITION_MAP[disease] = diet
            del df_nut
            gc.collect()
            print("✅ Nutrition loaded.")
        except Exception as e: print(f"❌ Nutrition Error: {e}")

load_all_data()

# Helper to get extra info
def get_details(disease_name):
    name = disease_name.lower().strip()
    return {
        "precautions": PRECAUTION_MAP.get(name, ["Consult a professional"]),
        "nutrition": NUTRITION_MAP.get(name, "Maintain a balanced diet")
    }

# Keep your existing extract_symptoms and get_possible_conditions functions below...
def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())

def extract_symptoms(user_input):
    cleaned_input = clean_text(user_input)
    detected = []
    for cleaned_name, original_name in SYMPTOM_LOOKUP.items():
        if re.search(rf"\b{re.escape(cleaned_name)}\b", cleaned_input):
            detected.append(original_name)
    return detected

def get_possible_conditions(symptoms):
    results = []
    for s in symptoms:
        results.extend(DISEASE_MAP.get(s, []))
    return list(dict.fromkeys(results))
