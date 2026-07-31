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
                if isinstance(data, dict):
                    if data.get('meals'): st.session_state['meals'] = data['meals']
                    if data.get('drinks'): st.session_state['drinks'] = data['drinks']
                    if data.get('workout'): st.session_state['workout'] = data['workout']
                    if data.get('waage_data'): st.session_state['waage_data'] = data['waage_data']
                    if data.get('saved_g') is not None: st.session_state['saved_g'] = data['saved_g']
                    if data.get('saved_k') is not None: st.session_state['saved_k'] = data['saved_k']
                    if data.get('saved_m') is not None: st.session_state['saved_m'] = data['saved_m']
        except Exception:
            pass

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

if 'waage_data' not in st.session_state:
    st.session_state['waage_data'] = {'gewicht': None, 'kfa': None, 'skelettmuskel': None}

# Beim Start einmalig Backup laden, falls noch nicht im Session State
if 'initialized_backup' not in st.session_state:
    load_daily_backup()
    st.session_state['initialized_backup'] = True

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

def analyze_waage(images):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = """
    Du bist ein präziser Daten-Extraktor für RENPHO Körperzusammensetzungs-Berichte. 
    Analysiere das übergebene Bild des Berichts. 
    Suche in der Tabelle 'Körperzusammensetzung' bzw. der oberen Haupttabelle nach folgenden exakten Werten:
    1. "gewicht": Der Wert bei 'Gewicht' in kg (z.B. 70.45).
    2. "kfa": Der Körperfettanteil (entweder aus der Tabelle oder dem 'Körperfettanteil: 13.9%' weiter rechts / unten, als Prozentzahl z.B. 13.9).
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
    except Exception as e:
        return {"gewicht": None, "kfa": None, "skelettmuskel": None}

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
    except Exception as e:
        return {
            "schritte": 0, "zirkel_min": 0, "zirkel_details": "",
            "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": f"Starke Leistung! (Fallback: {e})"
        }

def display_gicht_badge(status, notiz=""):
    if status == "rot":
        st.error("🔴 **Gichtgefahr (Hoher Puringehalt)**\n\n💡 *" + notiz + "*")
    elif status == "gelb":
        st.warning("🟡 **Moderat (Mittlerer Puringehalt)**\n\n💡 *" + notiz + "*")
    else:
        st.success("🟢 **Gichtfreundlich (Purinarm)**\n\n💡 *" + notiz + "*")

def show_image_previews(files):
    if files:
        cols = st.columns(min(len(files), 4))
        for idx, file in enumerate(files):
            cols[idx % 4].image(Image.open(file), use_container_width=True)

def get_todays_totals():
    m = st.session_state['meals']
    d = st.session_state['drinks']
    
    whey_kcal = d['whey_scoops'] * 120
    whey_prot = d['whey_scoops'] * 30
    total_drink_kcal = whey_kcal + d['sonstiges_kcal']
    total_drink_prot = whey_prot + d['sonstiges_prot']
    
    snack_kcal = sum([s['kcal'] for s in m['snacks']])
    snack_prot = sum([s['prot'] for s in m['snacks']])
    
    total_kcal = m['fruehstueck']['kcal'] + m['mittagessen']['kcal'] + m['abendessen']['kcal'] + snack_kcal + total_drink_kcal
    total_prot = m['fruehstueck']['prot'] + m['mittagessen']['prot'] + m['abendessen']['prot'] + snack_prot + total_drink_prot
    return total_kcal, total_prot

def render_gauge_svg(current, target, title, unit, color="#ff4b4b"):
    pct = (min(float(current) / float(target), 1.0) if target > 0 else 0) if target else 0
    dashoffset = 251.2 * (1 - pct)
    pct_int = int(pct * 100)
    
    svg_code = (
        '<div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 18px; border-radius: 16px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">'
        f'<h4 style="margin: 0 0 10px 0; color: #1e293b; font-size: 16px;">{title}</h4>'
        '<svg viewBox="0 0 200 110" style="width: 100%; max-width: 160px; height: auto;">'
        '<path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#f1f5f9" stroke-width="16" stroke-linecap="round"/>'
        f'<path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round" '
        f'stroke-dasharray="251.2" stroke-dashoffset="{dashoffset}"/>'
        f'<text x="100" y="75" text-anchor="middle" font-size="24" font-weight="bold" fill="#0f172a">{current}</text>'
        f'<text x="100" y="95" text-anchor="middle" font-size="11" fill="#64748b">Ziel: {target} {unit}</text>'
        '</svg>'
        f'<div style="margin-top: 8px; font-size: 13px; font-weight: 600; color: {color};">{pct_int}% erreicht</div>'
        '</div>'
    )
    st.markdown(svg_code, unsafe_allow_html=True)

def render_back_button():
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state['nav_tab'] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

def render_meal_page(tab_name, meal_key):
    render_back_button()
    st.subheader(f"Mahlzeit erfassen: {tab_name}")
    
    if meal_key == 'fruehstueck':
        st.markdown("⭐ **Schnell-Auswahl (Favoriten):**")
        fav_wahl = st.selectbox(
            "Wähle ein oft gegessenes Frühstück:", 
            ["-- Manuell / Foto eingeben --", "Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)"],
            key=f"{meal_key}_fav_select"
        )
        if fav_wahl == "Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)":
            st.session_state['meals'][meal_key] = {
                'kcal': 455, 
                'prot': 45, 
                'desc': 'Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)', 
                'gicht': 'grün', 
                'notiz': 'Hervorragender proteinreicher und
