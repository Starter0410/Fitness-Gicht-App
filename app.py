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
    layout="wide"
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

# Session State für Navigation initialisieren, falls nicht vorhanden
if 'nav_tab' not in st.session_state:
    st.session_state['nav_tab'] = "🏠 Startseite"

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
    except Exception:
        return {
            "schritte": 0, "zirkel_min": 0, "zirkel_details": "",
            "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "workout_notiz": "Starke Leistung!"
        }

def display_gicht_badge(status, notiz=""):
    if status == "rot":
        st.error(f"🔴 **Gichtgefahr (Hoher Puringehalt)**\n\n💡 *{notiz}*")
    elif status == "gelb":
        st.warning(f"🟡 **Moderat (Mittlerer Puringehalt)**\n\n💡 *{notiz}*")
    else:
        st.success(f"🟢 **Gichtfreundlich (Purinarm)**\n\n💡 *{notiz}*")

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
    snack_kcal = sum(s['kcal'] for s in m['snacks'])
    snack_prot = sum(s['prot'] for s in m['snacks'])
    
    total_kcal = m['fruehstueck']['kcal'] + m['mittagessen']['kcal'] + m['abendessen']['kcal'] + snack_kcal + total_drink_kcal
    total_prot = m['fruehstueck']['prot'] + m['mittagessen']['prot'] + m['abendessen']['prot'] + snack_prot + total_drink_prot
    return total_kcal, total_prot

def render_gauge_svg(current, target, title, unit, color="#ff4b4b"):
    pct = min(float(current) / float(target), 1.0) if target > 0 else 0
    dashoffset = 251.2 * (1 - pct)
    pct_int = int(pct * 100)
    
    svg_code = f"""
    <div style='background: #ffffff; border: 1px solid #e2e8f0; padding: 18px; border-radius: 16px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
        <h4 style='margin: 0 0 10px 0; color: #1e293b; font-size: 16px;'>{title}</h4>
        <svg viewBox='0 0 200 110' style='width: 100%; max-width: 160px; height: auto;'>
            <path d='M 20 100 A 80 80 0 0 1 180 100' fill='none' stroke='#f1f5f9' stroke-width='16' stroke-linecap='round'/>
            <path d='M 20 100 A 80 80 0 0 1 180 100' fill='none' stroke='{color}' stroke-width='16' stroke-linecap='round'
                  stroke-dasharray='251.2' stroke-dashoffset='{dashoffset}'/>
            <text x='100' y='75' text-anchor='middle' font-size='24' font-weight='bold' fill='#0f172a'>{current}</text>
            <text x='100' y='95' text-anchor='middle' font-size='11' fill='#64748b'>Ziel: {target} {unit}</text>
        </svg>
        <div style='margin-top: 8px; font-size: 13px; font-weight: 600; color: {color};'>{pct_int}% erreicht</div>
    </div>
    """
    st.markdown(svg_code, unsafe_allow_html=True)

# Hilfsfunktion für den Zurück-Button auf allen Unterseiten
def render_back_button():
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state['nav_tab'] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
tabs = [
    "🏠 Startseite", 
    "⚖️ Waage", 
    "🍳 Frühstück", 
    "🍲 Mittag", 
    "🌙 Abend", 
    "🍏 Snacks", 
    "🥤 Getränke", 
    "🏋️‍♂️ Training", 
    "✅ Abschluss",
    "📈 Statistik & Bilanz"
]

with st.sidebar:
    st.title("🏋️‍♂️ Fitness & Gicht")
    st.markdown("---")
    
    selected_tab = st.radio("Navigation", tabs, index=tabs.index(st.session_state['nav_tab']) if st.session_state['nav_tab'] in tabs else 0, label_visibility="collapsed")
    st.session_state['nav_tab'] = selected_tab
    
    st.markdown("---")
    st.caption("Body Recomp & Purinarm-Tracking")

# ---------------------------------------------------------
# INHALTE DER SEITEN
# ---------------------------------------------------------

if st.session_state['nav_tab'] == "🏠 Startseite":
    st.subheader("🏠 Tages-Dashboard")
    st.write("Willkommen zurück, Matthias! Hier ist dein moderner Überblick über den heutigen Tag.")
    
    cur_kcal, cur_prot = get_todays_totals()
    target_kcal = 2300 
    target_prot = 145
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        render_gauge_svg(cur_kcal, target_kcal, "🔥 Kalorien", "kcal", "#f97316")
    with col_d2:
        render_gauge_svg(cur_prot, target_prot, "🥩 Protein", "g", "#3b82f6")
    with col_d3:
        steps = st.session_state['workout']['schritte']
        render_gauge_svg(steps, 10000, "🚶 Schritte", "Steps", "#10b981")

    st.markdown("---")
    st.markdown("### 📱 Schnell-Übersicht & Navigation")
    st.write("Wähle direkt einen Bereich aus:")

    grid_cols = st.columns(3)
    if grid_cols[0].button("⚖️ Waage", use_container_width=True):
        st.session_state['nav_tab'] = "⚖️ Waage"
        st.rerun()
    if grid_cols[1].button("🍳 Frühstück", use_container_width=True):
        st.session_state['nav_tab'] = "🍳 Frühstück"
        st.rerun()
    if grid_cols[2].button("🍲 Mittag", use_container_width=True):
        st.session_state['nav_tab'] = "🍲 Mittag"
        st.rerun()

    grid_cols_2 = st.columns(3)
    if grid_cols_2[0].button("🌙 Abend", use_container_width=True):
        st.session_state['nav_tab'] = "🌙 Abend"
        st.rerun()
    if grid_cols_2[1].button("🍏 Snacks", use_container_width=True):
        st.session_state['nav_tab'] = "🍏 Snacks"
        st.rerun()
    if grid_cols_2[2].button("🥤 Getränke", use_container_width=True):
        st.session_state['nav_tab'] = "🥤 Getränke"
        st.rerun()

    grid_cols_3 = st.columns(3)
    if grid_cols_3[0].button("🏋️‍♂️ Training", use_container_width=True):
        st.session_state['nav_tab'] = "🏋️‍♂️ Training"
        st.rerun()
    if grid_cols_3[1].button("✅ Abschluss", use_container_width=True):
        st.session_state['nav_tab'] = "✅ Abschluss"
        st.rerun()
    if grid_cols_3[2].button("📈 Statistik", use_container_width=True):
        st.session_state['nav_tab'] = "📈 Statistik & Bilanz"
        st.rerun()

elif st.session_state['nav_tab'] == "⚖️ Waage":
    render_back_button()
    st.subheader("⚖️ Waagen-Messung")
    imgs_w = st.file_uploader("Foto(s) der Waage / App wählen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="w_img")
    show_image_previews(imgs_w)
    
    if imgs_w:
        if st.button("🤖 Waage analysieren", type="primary"):
            pil_imgs = [Image.open(f) for f in imgs_w]
            res = analyze_images_or_text(pil_imgs, "Waagen Display")
            st.session_state['waage_data'] = res
            st.success("Waagendaten erkannt!")

    w_data = st.session_state.get('waage_data', {})
    with st.form("waage_form"):
        col1, col2, col3 = st.columns(3)
        g = col1.number_input("Gewicht (kg)", value=float(w_data.get('gewicht') or 0.0), step=0.1)
        k = col2.number_input("KFA (%)", value=float(w_data.get('kfa') or 0.0), step=0.1)
        m = col3.number_input("Skelettmuskel (%)", value=float(w_data.get('skelettmuskel') or 0.0), step=0.1)
        if st.form_submit_button("💾 Waagendaten merken"):
            st.session_state['saved_g'] = g
            st.session_state['saved_k'] = k
            st.session_state['saved_m'] = m
            st.success("Waagendaten im Zwischenspeicher gesichert!")

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
                'notiz': 'Hervorragender proteinreicher und purinarmer Start in den Tag!'
            }
        st.markdown("---")

    imgs = st.file_uploader(f"Foto(s) von {tab_name} hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"{meal_key}_img")
    show_image_previews(imgs)
    
    txt = st.text_input(f"Oder beschreibe dein {tab_name}", key=f"{meal_key}_txt")
    
    if st.button(f"🤖 {tab_name} analysieren", key=f"{meal_key}_btn", type="primary"):
        if imgs or txt:
            pil_imgs = [Image.open(f) for f in imgs] if imgs else []
            res = analyze_images_or_text(pil_imgs, txt if txt else "Kein Text angegeben")
            st.session_state['meals'][meal_key] = {
                'kcal': int(res.get('kcal', 0)),
                'prot': int(res.get('protein', 0)),
                'desc': res.get('beschreibung', txt),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            }
            st.success(f"{tab_name} erfolgreich ausgewertet!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    current = st.session_state['meals'][meal_key]
    if current['kcal'] > 0 or current['desc']:
        st.info(f"**Erfasst:** {current['desc']} | **{current['kcal']} kcal** | **{current['prot']}g Protein**")
        display_gicht_badge(current['gicht'], current.get('notiz', ''))

if st.session_state['nav_tab'] == "🍳 Frühstück":
    render_meal_page("Frühstück", "fruehstueck")
elif st.session_state['nav_tab'] == "🍲 Mittag":
    render_meal_page("Mittagessen", "mittagessen")
elif st.session_state['nav_tab'] == "🌙 Abend":
    render_meal_page("Abendessen", "abendessen")

elif st.session_state['nav_tab'] == "🍏 Snacks":
    render_back_button()
    st.subheader("🍏 Snacks & Zwischenmahlzeiten")
    imgs_s = st.file_uploader("Foto(s) vom Snack", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="snack_img")
    show_image_previews(imgs_s)
    
    txt_s = st.text_input("Oder Snack beschreiben", key="snack_txt")
    
    if st.button("🤖 Snack hinzufügen", type="primary"):
        if imgs_s or txt_s:
            pil_imgs = [Image.open(f) for f in imgs_s] if imgs_s else []
            res = analyze_images_or_text(pil_imgs, txt_s if txt_s else "Kein Text angegeben")
            st.session_state['meals']['snacks'].append({
                'kcal': int(res.get('kcal', 0)),
                'prot': int(res.get('protein', 0)),
                'desc': res.get('beschreibung', txt_s),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            })
            st.success("Snack zur Tagesliste hinzugefügt!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    if st.session_state['meals']['snacks']:
        st.markdown("### 🍿 Heutige Snacks:")
        for idx, s in enumerate(st.session_state['meals']['snacks'], 1):
            st.write(f"**{idx}.** {s['desc']} — {s['kcal']} kcal | {s['prot']}g Protein")
            display_gicht_badge(s['gicht'], s.get('notiz', ''))

elif st.session_state['nav_tab'] == "🥤 Getränke":
    render_back_button()
    st.subheader("🥤 Getränke-Zähler")
    d = st.session_state['drinks']
    
    col1, col2 = st.columns(2)
    with col1:
        d['wasser_soda'] = st.number_input("💧 Wasser / Soda / Zitrone (Liter)", value=float(d['wasser_soda']), step=0.5)
        d['kaffee'] = st.number_input("☕ Kaffee (Tassen)", value=int(d['kaffee']), step=1)
    with col2:
        d['whey_scoops'] = st.number_input("🐮 Whey / Iso Clear (Scoops)", value=int(d['whey_scoops']), step=1)
        d['redbull'] = st.number_input("⚡ Red Bull (Dosen)", value=int(d['redbull']), step=1)
        
    st.markdown("---")
    st.write("**🥤 Sonstiges Getränk:**")
    d['sonstiges_txt'] = st.text_input("Name des Getränks", value=d['sonstiges_txt'])
    cs1, cs2 = st.columns(2)
    d['sonstiges_kcal'] = cs1.number_input("Kalorien (kcal)", value=int(d['sonstiges_kcal']), step=10)
    d['sonstiges_prot'] = cs2.number_input("Protein (g)", value=int(d['sonstiges_prot']), step=1)

elif st.session_state['nav_tab'] == "🏋️‍♂️ Training":
    render_back_button()
    st.subheader("🏋️‍♂️ Training & Aktivitäten erfassen")
    imgs_tr = st.file_uploader("Screenshots hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="tr_imgs")
    show_image_previews(imgs_tr)
    
    txt_tr = st.text_input("Oder Training beschreiben", key="tr_txt")
    
    if st.button("🤖 Training analysieren", type="primary"):
        if imgs_tr or txt_tr:
            pil_imgs = [Image.open(f) for f in imgs_tr] if imgs_tr else []
            res_tr = analyze_workout(pil_imgs, txt_tr if txt_tr else "Kein Text angegeben")
            
            st.session_state['workout']['schritte'] = int(res_tr.get('schritte') or st.session_state['workout']['schritte'])
            st.session_state['workout']['zirkel_min'] = int(res_tr.get('zirkel_min') or st.session_state['workout']['zirkel_min'])
            st.session_state['workout']['zirkel_details'] = res_tr.get('zirkel_details') or st.session_state['workout']['zirkel_details']
            st.session_state['workout']['bike_km'] = float(res_tr.get('bike_km') or st.session_state['workout']['bike_km'])
            st.session_state['workout']['bike_modus'] = res_tr.get('bike_modus') or st.session_state['workout']['bike_modus']
            st.session_state['workout']['sonstiges'] = res_tr.get('sonstiges') or st.session_state['workout']['sonstiges']
            st.session_state['workout']['notiz'] = res_tr.get('workout_notiz', '')
            st.success("Training erfolgreich analysiert!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    w = st.session_state['workout']
    st.markdown("---")
    w['schritte'] = st.number_input("🚶 Schritte Anzahl", value=int(w['schritte']), step=500)
    col_z1, col_z2 = st.columns([1, 2])
    w['zirkel_min'] = col_z1.number_input("⏱️ Zirkel (Min)", value=int(w['zirkel_min']), step=5)
    w['zirkel_details'] = col_z2.text_input("Übungen / Wdh", value=w['zirkel_details'])
    col_b1, col_b2 = st.columns(2)
    w['bike_km'] = col_b1.number_input("🚴 Fahrrad (km)", value=float(w['bike_km']), step=1.0)
    w['bike_modus'] = col_b2.text_input("E-Bike Modus", value=w['bike_modus'])
    w['sonstiges'] = st.text
