import csv
import io
import zipfile
import re
import os
import random

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "data", "symptoms.csv.zip")
PRECAUTIONS_PATH = os.path.join(BASE_DIR, "data", "precautions.csv")
NUTRIENTS_PATH = os.path.join(BASE_DIR, "data", "nutrients.csv") 

# Data Containers
DISEASE_MAP = {}
SYMPTOM_LOOKUP = {}
PRECAUTION_MAP = {}
FOOD_DB = [] # New dynamic food database

def normalize(text):
    """Standardizes names: 'Fungal_infection' -> 'fungal infection'"""
    if not text: return ""
    return re.sub(r"[^a-zA-Z0-9\s]", " ", str(text).lower()).strip().replace("  ", " ")

def safe_float(val):
    """Converts strings like '1,419' or 't' (trace) to safe floats."""
    try:
        clean_val = re.sub(r'[^\d.]', '', str(val))
        return float(clean_val) if clean_val else 0.0
    except:
        return 0.0

def load_all_data():
    global SYMPTOM_LOOKUP, DISEASE_MAP, PRECAUTION_MAP, FOOD_DB
    
    # 1. Load Symptoms (ZIP)
    if os.path.exists(ZIP_PATH):
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as z:
                with z.open(z.namelist()[0]) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                    disease_col = next((h for h in reader.fieldnames if "disease" in h.lower()), "diseases")
                    symptom_cols = [h for h in reader.fieldnames if h != disease_col]
                    
                    for s in symptom_cols:
                        clean_name = normalize(s)
                        SYMPTOM_LOOKUP[clean_name] = s
                        DISEASE_MAP[s] = set()

                    for row in reader:
                        d = row.get(disease_col)
                        if d:
                            for s in symptom_cols:
                                if str(row.get(s, "0")).strip() == '1':
                                    DISEASE_MAP[s].add(d.strip())
            for s in DISEASE_MAP: DISEASE_MAP[s] = list(DISEASE_MAP[s])
            print("✅ Symptoms loaded.")
        except Exception as e: print(f"❌ Symptom Error: {e}")

    # 2. Load Precautions
    if os.path.exists(PRECAUTIONS_PATH):
        try:
            with open(PRECAUTIONS_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader) # skip header
                for row in reader:
                    if len(row) > 1:
                        disease_key = normalize(row[0])
                        PRECAUTION_MAP[disease_key] = [p.strip() for p in row[1:] if p.strip()]
            print("✅ Precautions loaded.")
        except Exception as e: print(f"❌ Precaution Error: {e}")

    # 3. Load Nutrients (Dynamic Engine)
    if os.path.exists(NUTRIENTS_PATH):
        try:
            with open(NUTRIENTS_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    FOOD_DB.append({
                        "name": row.get("Food", "Unknown").strip(),
                        "measure": row.get("Measure", "1 serving").strip(),
                        "calories": safe_float(row.get("Calories")),
                        "protein": safe_float(row.get("Protein")),
                        "fat": safe_float(row.get("Sat.Fat")),
                        "fiber": safe_float(row.get("Fiber")),
                        "carbs": safe_float(row.get("Carbs"))
                    })
            print(f"✅ Nutrients loaded ({len(FOOD_DB)} foods).")
        except Exception as e: print(f"❌ Nutrients Error: {e}")

load_all_data()

def get_dietary_advice(disease_name):
    """Generates food recommendations based on the disease profile."""
    name = disease_name.lower()
    advice = ""
    recommended_foods = []

    # If food DB failed to load
    if not FOOD_DB: return "Maintain a balanced, healthy diet and stay hydrated."

    # Rules Engine
    if any(x in name for x in ["diabetes", "sugar"]):
        advice = "Focus on low-carbohydrate, high-fiber foods to manage blood sugar."
        options = [f for f in FOOD_DB if f['carbs'] < 15 and f['fiber'] > 2]
    elif any(x in name for x in ["hypertension", "heart", "blood pressure", "cholesterol"]):
        advice = "Maintain a heart-healthy diet low in saturated fats."
        options = [f for f in FOOD_DB if f['fat'] < 2 and f['calories'] < 200]
    elif any(x in name for x in ["gastroenteritis", "ulcer", "gerd", "stomach", "acid"]):
        advice = "Eat bland, low-fat foods that are easy to digest."
        options = [f for f in FOOD_DB if f['fat'] < 5 and f['fiber'] < 3 and f['protein'] < 15]
    elif any(x in name for x in ["constipation", "digestion", "bowel"]):
        advice = "Increase your dietary fiber intake significantly."
        options = [f for f in FOOD_DB if f['fiber'] > 4]
    elif any(x in name for x in ["fatigue", "anemia", "weakness", "muscle", "weight"]):
        advice = "Consume nutrient-dense, high-protein foods to regain energy and strength."
        options = [f for f in FOOD_DB if f['protein'] > 12]
    else:
        advice = "Maintain a balanced diet to support your immune system and recovery."
        options = [f for f in FOOD_DB if 5 < f['protein'] < 20 and f['calories'] < 250]

    # Pick 3 random foods from the filtered options to keep responses fresh
    if options:
        recommended_foods = random.sample(options, min(3, len(options)))
        food_list = [f"- **{f['name'].title()}** ({f['measure']}): {f['calories']} kcal, {f['protein']}g protein" for f in recommended_foods]
        return f"{advice}\n\n*Suggested additions to your diet:*\n" + "\n".join(food_list)
    
    return advice

def get_details(disease_name):
    key = normalize(disease_name)
    return {
        "precautions": PRECAUTION_MAP.get(key, ["Follow general health guidelines", "Rest and stay hydrated", "Consult a doctor if symptoms worsen"]),
        "nutrition": get_dietary_advice(disease_name)
    }

def extract_symptoms(user_input):
    cleaned_input = normalize(user_input)
    detected = []
    sorted_lookup = sorted(SYMPTOM_LOOKUP.items(), key=lambda x: len(x[0]), reverse=True)
    for cleaned_name, original_name in sorted_lookup:
        if re.search(rf"\b{re.escape(cleaned_name)}\b", cleaned_input):
            if original_name not in detected:
                detected.append(original_name)
    return detected

def get_possible_conditions(symptoms):
    if not symptoms: return []
    results = []
    for s in symptoms:
        results.extend(DISEASE_MAP.get(s, []))
    return list(dict.fromkeys(results))[:2] # Limit to top 2 to avoid overwhelming output
