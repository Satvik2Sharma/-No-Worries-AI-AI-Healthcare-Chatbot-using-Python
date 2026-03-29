import pandas as pd
import re
import os
import gc # Garbage Collector to free RAM

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "data", "symptoms.csv.zip")

# Global variables to hold only the processed data
DISEASE_MAP = {}
SYMPTOM_LOOKUP = {}

def load_data_efficiently():
    global SYMPTOM_LOOKUP, DISEASE_MAP
    try:
        # 1. Load the data. We assume symptoms are 0/1 (integers).
        # Loading symptoms as 'int8' uses 1/4 the memory of default integers.
        df = pd.read_csv(ZIP_PATH, compression='zip')
        
        # Normalize columns
        df.columns = [col.lower().strip() for col in df.columns]
        disease_col = "diseases"

        # 2. Build a mapping of symptom -> list of diseases
        # This is MUCH lighter than keeping a 190MB DataFrame in RAM
        symptom_cols = [c for c in df.columns if c != disease_col]
        
        for symptom in symptom_cols:
            # Get names of diseases where this symptom == 1
            matching_diseases = df[df[symptom] == 1][disease_col].unique().tolist()
            if matching_diseases:
                DISEASE_MAP[symptom] = matching_diseases
            
            # Clean name for lookup
            cleaned_name = re.sub(r"[^a-zA-Z0-9\s]", "", symptom).strip()
            SYMPTOM_LOOKUP[cleaned_name] = symptom

        print(f"✅ Loaded {len(DISEASE_MAP)} symptoms into memory.")

        # 3. CRITICAL: Delete the big DataFrame and clear RAM
        del df
        gc.collect() 

    except Exception as e:
        print(f"❌ Memory Load Error: {e}")

# Run the loader immediately
load_data_efficiently()

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
