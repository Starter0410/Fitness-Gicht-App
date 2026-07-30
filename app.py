import os
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from google import genai
from google.genai import types
from PIL import Image
import json
import datetime
import streamlit.components.v1 as components

# =========================================================
# DEIN API-KEY HIER EINTRAGEN:
# =========================================================
GEMINI_API_KEY = "AQ.Ab8RN6JBdMOINycPw0LdsUMe_kH9YVbflYGVvh1T-Jc0XTGCmQ" 
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"
BACKUP_FILE = "tagesentwurf.json"

# ---------------------------------------------------------
# SETUP & KONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gicht & Body Recomp Tracking", 
    page_icon="💪", 
    layout="wide"
)

# Automatisches Scrollen nach oben bei jedem Seitenwechsel / Klick
components.html(
    """
    <script>
        window.parent.document.querySelector('.main').scrollTop = 0;
    </script>
    """,
    height=0,
)

# Custom CSS für moderne UI-Cards & saubere Buttons
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State für Navigation initialisieren
if 'nav_tab' not in st.session_state:
    st.session_state['nav_tab'] = "🏠 Startseite"

# ---------------------------------------------------------
# PERSISTENTE DATEN LADEN & SPEICHERN (SCHUTZ VOR REBOOT)
# ---------------------------------------------------------
def save_daily_backup():
    data = {
        'meals': st.session_state.get('meals'),
        'drinks': st.session_state.get('drinks'),
        'workout': st.session_state.get('workout'),
        'waage_data': st.session_state.get('waage_data'),
        'saved_g': st.session_state.get('saved_g'),
        'saved_k': st.session_state.get('saved_k'),
        'saved_m': st.session_state.get('saved_m')
    }
    try:
        with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_daily_backup():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'meals' in data: st.session_state['meals'] = data['meals']
                if 'drinks' in data: st.session_state['drinks'] = data['drinks']
                if 'workout' in data: st.session_state['workout'] = data['workout']
                if 'waage_data' in data: st.session_state['waage_data'] = data['waage_data']
                if 'saved_g' in data: st.session_state['saved_g'] = data['saved_g']
                if 'saved_k' in data: st.session_state['saved_k'] = data['saved_k']
                if 'saved_m' in data: st.session_state['saved_m'] = data['saved_m']
        except Exception:
            pass

# Beim Start einmalig Backup laden, falls noch nicht im Session State
if 'initialized_backup' not in st.session_state:
    load_daily_backup()
    st.session_state['initialized_backup'] = True

# Tages-Speicher initialisieren, falls leer
if 'meals' not in st.session_state:
    st.session_state['meals'] = {
        'fruehstueck': {'kcal': 0, 'prot': 0, 'desc': '', 'gicht': 'grün', 'notiz': ''},
        'mittagessen': {'kcal': 0, 'prot': 0, 'desc': '', 'gicht': 'grün', 'notiz': ''},
        'abendessen': {'kcal': 0, 'prot': 0, 'desc': '', 'gicht': 'grün', 'notiz': ''},
        'snacks': []
    }

if 'drinks' not in st.session_state:
    st.session_state['drinks'] = {
        'wasser_soda': 0.0,
        'kaffee': 0,
        'whey_scoops': 0,
        'redbull': 0,
        'sonstiges_txt': '',
        'sonstiges_kcal': 0,
        'sonstiges_prot': 0
    }

if 'workout' not in st.session_state:
    st.session_state['workout'] = {
        'schritte': 0,
        'zirkel_min': 0,
        'zirkel_details': '',
        'bike_km': 0.0,
        'bike_modus': '',
        'sonstiges': '',
        'notiz': ''
    }

# ---------------------------------------------------------
# HELFER-FUNKTIONEN (GEMINI & UI)
# ---------------------------------------------------------
def clean_json_response(text_res):
    text_res = text_res.strip()
    if text_res.startswith("```json"):
        text_res = text_res[7:]
    elif text_res.startswith("```"):
        text_res = text_res[3:]
    if text_res.endswith("```"):
        text_res = text_res[:-3]
    return text_res.strip()

def analyze_images_or_text(images, text_prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
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
        "gewicht": null,
        "kfa": null,
        "skelettmuskel": null,
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
            "gewicht": None, "kfa": None, "skelettmuskel": None,
            "kcal": 250, "protein": 5, "beschreibung": text_prompt,
            "gicht_bewertung": "grün", "mahlzeit_notiz": f"Erfasst via Text (Fallback: {e})"
        }

def analyze_workout(images, text_prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
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
