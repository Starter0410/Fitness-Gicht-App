import requests
import json
import io
import base64

def image_to_base64(pil_img):
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def call_gemini_api(api_key, prompt_text, pil_imgs):
    # Umstellung auf v1 mit gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    parts = [{"text": prompt_text}]
    for img in pil_imgs:
        img_b64 = image_to_base64(img)
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": img_b64
            }
        })
        
    payload = {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        raise Exception(f"API-Fehler ({response.status_code}): {response.text}")
        
    res_json = response.json()
    try:
        text_result = res_json["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text_result)
    except Exception as e:
        raise Exception(f"Fehler beim Parsen der JSON-Antwort: {e} | Rohdaten: {res_json}")

def analyze_waage(api_key, pil_imgs):
    prompt = (
        "Analysiere dieses Waagen- oder Körperfettwaagen-Foto. "
        "Extrahiere folgende Werte: Gewicht in kg, KFA in %, Skelettmuskel in %. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln (als Float oder null): "
        '{"gewicht": 0.0, "kfa": 0.0, "skelettmuskel": 0.0}'
    )
    return call_gemini_api(api_key, prompt, pil_imgs)

def analyze_workout(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere das Workout basierend auf diesem Text: '{txt_input}' und den Bildern. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": ""}'
    )
    return call_gemini_api(api_key, prompt, pil_imgs)

def analyze_images_or_text(api_key, pil_imgs, txt_input):
    prompt = (
        f"Analysiere diese Mahlzeit basierend auf dem Text: '{txt_input}' und den Bildern. "
        "Schätze die Nährwerte und den Purin- bzw. Gicht-Status. "
        "Antworte AUSSCHLIESSLICH im JSON-Format mit diesen exakten Schlüsseln: "
        '{"kcal": 0, "protein": 0, "beschreibung": "", "gicht_bewertung": "grün", "mahlzeit_notiz": ""}'
    )
    return call_gemini_api(api_key, prompt, pil_imgs)
