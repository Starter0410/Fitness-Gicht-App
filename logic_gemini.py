import google.generativeai as genai
from PIL import Image
import json

def call_gemini_sdk(api_key, prompt_text, pil_imgs):
    genai.configure(api_key=api_key)
    
    # Das offizielle, stabile Standardmodell für das SDK
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Inhalt zusammenstellen (Prompt + Bilder)
    content = [prompt_text] + pil_imgs
    
    response = model.generate_content(
        content,
        generation_config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)

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
        f"Analysiere das Workout basierend auf diesem Text: '{txt_input}' und den Bildern. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": ""}'
    )
    return call_gemini_sdk(api_key, prompt, pil_imgs)

def analyze_images_or_text(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere diese Mahlzeit basierend auf dem Text: '{txt_input}' und den Bildern. "
        "Schätze die Nährwerte und den Purin- bzw. Gicht-Status. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"kcal": 0, "protein": 0, "beschreibung": "", "gicht_bewertung": "grün", "mahlzeit_notiz": ""}'
    )
    return call_gemini_sdk(api_key, prompt, pil_imgs)
