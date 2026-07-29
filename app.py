import os
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from google import genai
from google.genai import types
from PIL import Image
import json
import datetime

# =========================================================
# DEIN API-KEY HIER EINTRAGEN:
# =========================================================
GEMINI_API_KEY = "AQ.Ab8RN6JBdMOINycPw0LdsUMe_kH9YVbflYGVvh1T-Jc0XTGCmQ" 
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"

# ---------------------------------------------------------
# SETUP & KONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gicht & Body Recomp Tracking", 
    page_icon="💪", 
    layout="centered"
)

st.title("🏋️‍♂️ Fitness & Gicht-Tracking App")

# Tages-Speicher initialisieren
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
# HELFER-FUNKTIONEN (GEMINI PROMPTS)
# ---------------------------------------------------------
def analyze_images_or_text(images, text_prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Guten Tag,

    Mein Name ist Matthias. Ich habe immer wieder Probleme mit Gichtschüben. Daher haben wir an unserer App gefeilt. Mein Ziel ist eine Body-Recomposition: Mein Gewicht darf stabil bleiben oder leicht steigen, der Fokus liegt aber auf der gezielten Reduktion des Bauchfetts bei gleichzeitigem Erhalt der gesamten Muskelmasse, unter strikter Einhaltung purinarmer Ernährung (Gicht-Prävention). Wir kombinieren in unserem Tagebuch Körperwerte, Essen, Getränke, Training und Subs.

    Analysiere diesen Text / diese Speise: '{text_prompt}'. 

    Du analysierst diese Mahlzeit auf KCAL, Protein und vergibst genau einen Ampel-Wert (Dropdown: grün, gelb, rot) nach folgender fester Logik:
    - GRÜN: Vegetarisch oder rein purinarm (z. B. Milchprodukte, Eier, Gemüse, Obst, Haferflocken, Marmelade/Semmel ohne Fleisch).
    - GELB: Hühnchen / Geflügel (moderate Purine).
    - ROT: Alle anderen Fleischsorten (z. B. Rind, Schwein, Fisch/Meeresfrüchte – stark purinhaltig).

    Der allgemeine "Gicht Status" richtet sich nach der Ampel der Mahlzeit.
    Gib mir eine kurze Notiz dazu – mit Fokus auf Gicht, Purine, Motivation oder Mahnung.

    Gib das Ergebnis STRENG im folgenden JSON-Format zurück (ohne Markdown-Backticks drumherum, nur das reine JSON):
    {{
        "gewicht": null,
        "kfa": null,
        "skelettmuskel": null,
        "kcal": 0,
        "protein": 0,
        "beschreibung": "Kurze prägnante Zusammenfassung der Speise",
        "gicht_bewertung": "grün",
        "mahlzeit_notiz": "Kurze Notiz/Feedback zur Mahlzeit mit Fokus auf Gicht, Purine, Motivation oder Mahnung."
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
        text_res = response.text.strip()
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.startswith("```"):
            text_res = text_res[3:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]
        return json.loads(text_res.strip())
    except Exception as e:
        # Fallback falls JSON-Parsing scheitert
        return {
            "gewicht": None, "kfa": None, "skelettmuskel": None,
            "kcal": 250, "protein": 5, "beschreibung": text_prompt,
            "gicht_bewertung": "grün", "mahlzeit_notiz": f"Erfasst via Text (Fallback aktiv: {e})"
        }

def analyze_workout(images, text_prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Du bist der persönliche Fitness-Coach von Matthias.
    Analysiere diesen Text / diese Aktivität: {text_prompt}.
    Fasse ALLE erkennbaren Trainingsleistungen zusammen. Gib mir Notizen, die motivierend sein sollen.
    Gib das Ergebnis STRENG im folgenden JSON-Format zurück:
    {{
        "schritte": 0,
        "zirkel_min": 0,
        "zirkel_details": "Beschreibung von Übungen/Wiederholungen falls erkennbar",
        "bike_km": 0.0,
        "bike_modus": "z.B. Eco, Tour, Sport, Turbo falls angegeben",
        "sonstiges": "Andere Sportarten wie Schwimmen/Seilspringen",
        "workout_notiz": "Ein sehr motivierender, lobender oder anspornender Satz zur Tages-Trainingsleistung von Matthias."
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
        text_res = response.text.strip()
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.startswith("```"):
            text_res = text_res[3:]
        if text_res.endswith("
