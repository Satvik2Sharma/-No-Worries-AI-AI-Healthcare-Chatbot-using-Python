import csv
import io
import zipfile
import re
import os

# -----------------------------
# DYNAMIC PATH HANDLING
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "data", "symptoms.csv.zip")

# Global variables for the processed data
DISEASE_MAP = {}
SYMPTOM_LOOKUP = {}

def load_data_without_pandas():
    global SYMPTOM_LOOKUP, DISEASE_MAP
    
    if not os.path.exists(ZIP_PATH):
        print(f"❌ File not found: {ZIP_PATH}")
        return

    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as z:
            # Get the name of the CSV inside the zip
            csv_filename = z.namelist()[0] 
            
            with z.open(csv_filename) as f:
                # Wrap the binary stream in a text wrapper for the CSV reader
                wrapper = io.TextIOWrapper(f, encoding='utf-8')
                reader = csv.DictReader(wrapper)
                
                # Get symptoms from the header (everything except 'diseases')
                # Lowercase and clean them immediately
                raw_headers = reader.fieldnames
                disease_col = "diseases" # Change this if your column name is different
                
                symptom_cols = [h for h in raw_headers if h.lower().strip() != disease_col]
                
                # Pre-build lookup for extraction
                for s in symptom_cols:
                    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", s.lower()).strip()
                    SYMPTOM_LOOKUP[clean_name] = s
                    DISEASE_MAP[s] = set() # Use a set to avoid duplicates

                # Process row by row (This keeps RAM usage very low)
                for row in reader:
                    current_disease = row.get(disease_col)
                    if not current_disease:
                        continue
                        
                    for s in symptom_cols:
                        # Only link if the value is '1' (present)
                        if row.get(s) == '1':
                            DISEASE_MAP[s].add(current_disease)

        # Convert sets back to lists for easier use later
        for s in DISEASE_MAP:
            DISEASE_MAP[s] = list(DISEASE_MAP[s])

        print(f"✅ Successfully loaded {len(DISEASE_MAP)} symptoms via Streaming.")

    except Exception as e:
        print(f"❌ Ultra-Lightweight Load Error: {e}")

# Initial load
load_data_without_pandas()

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
    # Remove duplicates
    return list(dict.fromkeys(results))
