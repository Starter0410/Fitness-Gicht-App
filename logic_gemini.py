from google import genai
from google.genai import types
import json
import traceback

def call_gemini_sdk(api_key, prompt_text, pil_imgs):
    try:
        client = genai.Client(api_key=api_key)
        
        contents = [prompt_text]
        if pil_imgs:
            contents.extend(pil_imgs)
        
        # Nutzen des aktuellen Modells gemäß Google AI Studio
        response = client.models.generate_content(
            model='gemini-3.1-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        return json.loads(response.text)
        
    except Exception as e:
        print("\n" + "="*50)
        print("🚨 EXAKTER GEMINI-FEHLER IM HINTERGRUND:")
        traceback.print_exc()
        print("="*50 + "\n")
        
        return {
            "gewicht": 0.0, "kfa": 0.0, "skelettmuskel": 0.0,
            "schritte": 0, "zirkel_min": 0, "zirkel_details": "", 
            "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": "",
            "kcal": 0, "protein": 0, "beschreibung": "", 
            "gicht_bewertung": "grün", "mahlzeit_notiz": ""
        }

def analyze_waage(api_key, pil_imgs):
    prompt = (
        "Analysiere dieses Waagen- oder Körperfettwaagen-Foto. "
        "Extrahiere folgende Werte: Gewicht in kg, KFA in %, Skelettmuskel in %. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln (als Float oder null): "
        '{"gewicht": 0.0, "kfa": 0.0, "skelettmuskel": 0.0}'
    )
    return call_gemini_sdk(api_key, prompt, pil_imgs)

def analyze_workout(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere das Workout basierend auf diesem Text: '{txt_input}' und den eventuellen Bildern. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": ""}'
    )
    return call_gemini_sdk(api_key, prompt, pil_imgs)

def analyze_images_or_text(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere diese Mahlzeit basierend auf dem Text: '{txt_input}' und den Bildern. "
        "Ermittle realistische, genaue Nährwerte (Kalorien, Protein) und den Purin- bzw. Gicht-Status. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"kcal": 0, "protein": 0, "beschreibung": "", "gicht_bewertung": "grün", "mahlzeit_notiz": ""}'
    )
    return call_gemini_sdk(api_key, prompt, pil_imgs)
