import os
from google import genai
from google.genai import types
import json

def get_client(api_key):
    # Setzt den Key explizit in die Umgebungsvariable, damit das SDK nicht nach OAuth sucht
    os.environ["GEMINI_API_KEY"] = api_key
    return genai.Client(api_key=api_key)

def analyze_waage(api_key, pil_imgs):
    client = get_client(api_key)
    prompt = (
        "Analysiere dieses Waagen- oder Körperfettwaagen-Foto. "
        "Extrahiere folgende Werte: Gewicht in kg, KFA in %, Skelettmuskel in %. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"gewicht": 0.0, "kfa": 0.0, "skelettmuskel": 0.0}'
    )
    contents = [prompt] + pil_imgs
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)

def analyze_workout(api_key, pil_imgs, txt_input):
    client = get_client(api_key)
    prompt = (
        f"Analysiere das Workout basierend auf diesem Text: '{txt_input}' und den Bildern. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": ""}'
    )
    contents = [prompt] + pil_imgs
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)

def analyze_images_or_text(api_key, pil_imgs, txt_input):
    client = get_client(api_key)
    prompt = (
        f"Analysiere diese Mahlzeit basierend auf dem Text: '{txt_input}' und den Bildern. "
        "Schätze die Nährwerte und den Purin- bzw. Gicht-Status. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"kcal": 0, "protein": 0, "beschreibung": "", "gicht_bewertung": "grün", "mahlzeit_notiz": ""}'
    )
    contents = [prompt] + pil_imgs
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)
