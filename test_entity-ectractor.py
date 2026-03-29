from utils.entity_extractor import extract_symptoms, get_possible_conditions

text = "I have headache and fever"

symptoms = extract_symptoms(text)
print("Detected:", symptoms)

conditions = get_possible_conditions(symptoms)
print("Possible conditions:", conditions)
