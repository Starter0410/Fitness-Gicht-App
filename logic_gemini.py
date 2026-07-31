from google import genai
from google.genai import types
import json

def call_new_genai(api_key, prompt_text, pil_imgs):
    client = genai.Client(api_key=api_key)
    contents = [prompt_text] + pil_imgs
    
    # Liste aller verfügbaren Modell-Optionen der Reihe nach durchgehen (Wenn-Dann-Logik)
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            continue
            
    raise Exception(Kein unterstütztes Modell gefunden. Letzter Fehler: {last_error})

def analyze_waage(api_key, pil_imgs):
    prompt = (
        "Analysiere dieses Waagen- oder Körperfettwaagen-Foto. "
        "Extrahiere folgende Werte: Gewicht in kg, KFA in %, Skelettmuskel in %. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln (als Float oder null): "
        '{"gewicht": 0.0, "kfa": 0.0, "skelettmuskel": 0.0}'
    )
    return call_new_genai(api_key, prompt, pil_imgs)

def analyze_workout(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere das Workout basierend auf diesem Text: '{txt_input}' und den Bildern. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": ""}'
    )
    return call_new_genai(api_key, prompt, pil_imgs)

def analyze_images_or_text(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere diese Mahlzeit basierend auf dem Text: '{txt_input}' und den Bildern. "
        "Schätze die Nährwerte und den Purin- bzw. Gicht-Status. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"kcal": 0, "protein": 0, "beschreibung": "", "gicht_bewertung": "grün", "mahlzeit_notiz": ""}'
    )
    return call_new_genai(api_key, prompt, pil_imgs)
