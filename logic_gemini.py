import json
from google import genai
from google.genai import types
from PIL import Image

def clean_json_response(text_res):
    text_res = text_res.strip()
    if text_res.startswith("```json"):
        text_res = text_res[7:]
    elif text_res.startswith("```"):
        text_res = text_res[3:]
    if text_res.endswith("```"):
        text_res = text_res[:-3]
    return text_res.strip()

def analyze_waage(api_key, images):
    client = genai.Client(api_key=api_key)
    prompt = """
    Du bist ein präziser Daten-Extraktor für RENPHO Körperzusammensetzungs-Berichte. 
    Analysiere das übergebene Bild des Berichts. 
    Suche in der Tabelle 'Körperzusammensetzung' bzw. der oberen Haupttabelle nach folgenden exakten Werten:
    1. "gewicht": Der Wert bei 'Gewicht' in kg (z.B. 70.45).
    2. "kfa": Der Körperfettanteil (als Prozentzahl z.B. 13.9).
    3. "skelettmuskel": Der Wert bei 'Skelettmuskelmasse' in kg (z.B. 34.45).

    Falls ein Wert absolut nicht zu finden ist, setze ihn auf null.
    Gib das Ergebnis STRENG im folgenden JSON-Format zurück (kein zusätzlicher Text, nur das reine JSON):
    {
        "gewicht": 0.0,
        "kfa": 0.0,
        "skelettmuskel": 0.0
    }
    """
    contents = [prompt]
    if images:
        for img in images:
            contents.append(img)
            
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        res_json = json.loads(clean_json_response(response.text))
        
        def parse_val(val):
            if val is None:
                return None
            try:
                if isinstance(val, str):
                    val = val.replace(',', '.')
                return float(val)
            except Exception:
                return None

        return {
            "gewicht": parse_val(res_json.get("gewicht")),
            "kfa": parse_val(res_json.get("kfa")),
            "skelettmuskel": parse_val(res_json.get("skelettmuskel")),
        }
    except Exception:
        return {"gewicht": None, "kfa": None, "skelettmuskel": None}

def analyze_images_or_text(api_key, images, text_prompt):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Guten Tag,
    Mein Name ist Matthias. Ziel ist Body-Recomposition (Fettabbau bei Muskelerhalt) und strikte Purinarmut (Gicht-Prävention).
    Analysiere diesen Text / diese Speise: '{text_prompt}'. 
    Analysiere auf KCAL, Protein und vergib genau einen Ampel-Wert (grün, gelb, rot):
    - GRÜN: Vegetarisch oder purinarm (Milchprodukte, Eier, Gemüse, Obst, Haferflocken).
    - GELB: Hühnchen / Geflügel (moderate Purine).
    - ROT: Rind, Schwein, Fisch/Meeresfrüchte (stark purinhaltig).

    Gib das Ergebnis STRENG im folgenden JSON-Format zurück (nur das reine JSON):
    {{
        "kcal": 0,
        "protein": 0,
        "beschreibung": "Kurze prägnante Zusammenfassung",
        "gicht_bewertung": "grün",
        "mahlzeit_notiz": "Kurzes Feedback mit Fokus auf Gicht und Motivation."
    }}
    """
    contents = [prompt]
    if images:
        for img in images:
            contents.append(img)
        
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(clean_json_response(response.text))
    except Exception as e:
        return {
            "kcal": 250, "protein": 5, "beschreibung": text_prompt,
            "gicht_bewertung": "grün", "mahlzeit_notiz": f"Erfasst via Text (Fallback: {e})"
        }

def analyze_workout(api_key, images, text_prompt):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Du bist der Fitness-Coach von Matthias. Analysiere diese Aktivität: {text_prompt}.
    Gib das Ergebnis STRENG im JSON-Format zurück:
    {{
        "schritte": 0,
        "zirkel_min": 0,
        "zirkel_details": "Übungen/Wdh",
        "bike_km": 0.0,
        "bike_modus": "Modus",
        "sonstiges": "Sonstiges",
        "workout_notiz": "Motivierender Satz."
    }}
    """
    contents = [prompt]
    if images:
        for img in images:
            contents.append(img)
        
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(clean_json_response(response.text))
    except Exception as e:
        return {
            "schritte": 0, "zirkel_min": 0, "zirkel_details": "",
            "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": f"Starke Leistung! (Fallback: {e})"
        }