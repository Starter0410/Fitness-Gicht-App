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
                'notiz': 'Hervorragender proteinreicher und purinarmer Start in den Tag!'
            }
            save_daily_backup()
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
            save_daily_backup()
            st.success(f"{tab_name} erfolgreich ausgewertet!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    current = st.session_state['meals'][meal_key]
    if current['kcal'] > 0 or current['desc']:
        st.info(f"**Erfasst:** {current['desc']} | **{current['kcal']} kcal** | **{current['prot']}g Protein**")
        display_gicht_badge(current['gicht'], current.get('notiz', ''))

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
# INHALTE DER SEITEN (HAUPTSTRANG)
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
            res = analyze_waage(pil_imgs)
            st.session_state['waage_data'] = res
            
            if res.get('gewicht') is not None: st.session_state['saved_g'] = res['gewicht']
            if res.get('kfa') is not None: st.session_state['saved_k'] = res['kfa']
            if res.get('skelettmuskel') is not None: st.session_state['saved_m'] = res['skelettmuskel']
            
            save_daily_backup()
            st.success("Waagendaten erfolgreich erkannt und übernommen!")

    w_data = st.session_state.get('waage_data', {})
    with st.form("waage_form"):
        col1, col2, col3 = st.columns(3)
        
        def_g = w_data.get('gewicht') if w_data.get('gewicht') is not None else st.session_state.get('saved_g', 0.0)
        def_k = w_data.get('kfa') if w_data.get('kfa') is not None else st.session_state.get('saved_k', 0.0)
        def_m = w_data.get('skelettmuskel') if w_data.get('skelettmuskel') is not None else st.session_state.get('saved_m', 0.0)

        g = col1.number_input("Gewicht (kg)", value=float(def_g), step=0.1)
        k = col2.number_input("KFA (%)", value=float(def_k), step=0.1)
        m = col3.number_input("Skelettmuskel (%)", value=float(def_m), step=0.1)
        
        if st.form_submit_button("💾 Waagendaten merken"):
            st.session_state['saved_g'] = g
            st.session_state['saved_k'] = k
            st.session_state['saved_m'] = m
            save_daily_backup()
            st.success("Waagendaten im Zwischenspeicher gesichert!")

elif st.session_state['nav_tab'] == "🍳 Frühstück":
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
            save_daily_backup()
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
    save_daily_backup()

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
            save_daily_backup()
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
    w['sonstiges'] = st.text_input("🏊 Sonstiges", value=w['sonstiges'])
    save_daily_backup()

elif st.session_state['nav_tab'] == "✅ Abschluss":
    render_back_button()
    st.subheader("🔍 Tagesabschluss & Endkontrolle")
    m = st.session_state['meals']
    d = st.session_state['drinks']
    w = st.session_state['workout']
    
    total_kcal, total_prot = get_todays_totals()

    drink_list = []
    if d['wasser_soda'] > 0: drink_list.append(f"{d['wasser_soda']}L Wasser/Soda")
    if d['kaffee'] > 0: drink_list.append(f"{d['kaffee']}x Kaffee")
    if d['whey_scoops'] > 0: drink_list.append(f"{d['whey_scoops']} Scoop Whey")
    if d['redbull'] > 0: drink_list.append(f"{d['redbull']}x Red Bull")
    if d['sonstiges_txt']: drink_list.append(f"{d['sonstiges_txt']}")
    
    drink_summary = ", ".join(drink_list) if drink_list else "Keine Drinks"
    
    workout_list = []
    if w['schritte'] > 0: workout_list.append(f"{w['schritte']} Schritte")
    if w['zirkel_min'] > 0: workout_list.append(f"Zirkel {w['zirkel_min']}m")
    if w['bike_km'] > 0: workout_list.append(f"Bike {w['bike_km']}km")
    workout_summary = ", ".join(workout_list) if workout_list else "Keine Aktivität"

    col_a, col_b = st.columns(2)
    col_a.metric("Gesamtkalorien", f"{total_kcal} kcal")
    col_b.metric("Gesamtprotein", f"{total_prot} g")
    
    descriptions = []
    if m['fruehstueck']['desc']: descriptions.append(f"Frühstück: {m['fruehstueck']['desc']}")
    if m['mittagessen']['desc']: descriptions.append(f"Mittag: {m['mittagessen']['desc']}")
    if m['abendessen']['desc']: descriptions.append(f"Abend: {m['abendessen']['desc']}")
    if m['snacks']: descriptions.append("Snacks vorhanden")
    descriptions.append(f"Getränke: {drink_summary}")
    descriptions.append(f"Training: {workout_summary}")
    
    full_notes = " | ".join(descriptions)

    with st.form("final_excel_form"):
        datum = st.date_input("Datum", value=datetime.date.today())
        c1, c2, c3 = st.columns(3)
        
        g_val = c1.number_input("Gewicht (kg)", value=float(st.session_state.get('saved_g', 0.0)), step=0.1)
        k_val = c2.number_input("KFA (%)", value=float(st.session_state.get('saved_k', 0.0)), step=0.1)
        m_val = c3.number_input("Skelettmuskel (%)", value=float(st.session_state.get('saved_m', 0.0)), step=0.1)
        
        c4, c5 = st.columns(2)
        kc_val = c4.number_input("Kalorien Gesamt", value=total_kcal)
        pr_val = c5.number_input("Protein Gesamt", value=total_prot)
        
        notizen = st.text_area("Generierte Tagesnotiz für Excel", value=full_notes, height=100)
        
        if st.form_submit_button("🚀 In Excel speichern & Download vorbereiten"):
            if os.path.exists(EXCEL_FILE):
                try:
                    wb = load_workbook(EXCEL_FILE)
                    ws = wb.active
                    ws.append([str(datum), g_val, k_val, m_val, kc_val, pr_val, notizen])
                    wb.save(EXCEL_FILE)
                    st.success("✅ Tageseintrag erfolgreich gespeichert!")
                except Exception as e:
                    st.error(f"Fehler: {e}")
            else:
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.append([str(datum), g_val, k_val, m_val, kc_val, pr_val, notizen])
                wb.save(EXCEL_FILE)
                st.success("✅ Neue Excel erstellt & gespeichert!")

    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 Aktuelle Excel-Datei auf Laptop herunterladen",
                data=file,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

elif st.session_state['nav_tab'] == "📈 Statistik & Bilanz":
    render_back_button()
    st.subheader("📈 Historische Auswertungen, Wochen- & Monatsbilanz")
    
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                
                if 'Skel.Musk' in df.columns:
                    df.rename(columns={'Skel.Musk': 'Skelettmuskel (%)'}, inplace=True)
                
                numeric_cols = ['KG', 'KFA', 'Skelettmuskel (%)', 'KCAL', 'Prot', 'Schritte']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                date_col = None
                for c in df.columns:
                    if 'datum' in c.lower() or 'date' in c.lower():
                        date_col = c
                        break
                
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df = df.sort_values(by=date_col, ascending=False)
                    df['Monat-Jahr'] = df[date_col].dt.strftime('%Y-%m')
                    
                    st.markdown("### 📊 Aktuelle Bilanzen (Durchschnitte)")
                    recent_7 = df.head(7)
                    
                    avg_7_kcal = int(recent_7['KCAL'].mean()) if 'KCAL' in recent_7.columns and not recent_7['KCAL'].dropna().empty else 0
                    avg_7_prot = int(recent_7['Prot'].mean()) if 'Prot' in recent_7.columns and not recent_7['Prot'].dropna().empty else 0
                    avg_7_steps = int(recent_7['Schritte'].mean()) if 'Schritte' in recent_7.columns and not recent_7['Schritte'].dropna().empty else 0
                    
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("Ø KCAL (Letzte 7 Tage)", f"{avg_7_kcal} kcal")
                    col_b2.metric("Ø Protein (Letzte 7 Tage)", f"{avg_7_prot} g")
                    col_b3.metric("Ø Schritte (Letzte 7 Tage)", f"{avg_7_steps}")

                    st.markdown("---")

                    verfuegbare_monate = sorted(df['Monat-Jahr'].dropna().unique(), reverse=True)
                    if verfuegbare_monate:
                        selected_month = st.selectbox(
                            "📅 Nach Monat für Diagramme filtern:", 
                            ["Alle Monate"] + list(verfuegbare_monate)
                        )
                        if selected_month != "Alle Monate":
                            df_filtered = df[df['Monat-Jahr'] == selected_month]
                        else:
                            df_filtered = df
                    else:
                        df_filtered = df
                else:
                    df_filtered = df

                st.success(f"📊 {len(df_filtered)} Datensätze in der Auswertung aktiv.")
                x_col = date_col if date_col else None

                st.markdown("### 🧬 Körperwerte (Body Recomp)")
                col_k1, col_k2, col_k3 = st.columns(3)
                with col_k1:
                    st.markdown("**Gewicht (KG)**")
                    if 'KG' in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)['KG'] if x_col else df_filtered['KG'])
                with col_k2:
                    st.markdown("**KFA (%)**")
                    if 'KFA' in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)['KFA'] if x_col else df_filtered['KFA'])
                with col_k3:
                    st.markdown("**Skelettmuskel (%)**")
                    if 'Skelettmuskel (%)' in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)['Skelettmuskel (%)'] if x_col else df_filtered['Skelettmuskel (%)'])

                st.markdown("---")
                st.markdown("### 🚶‍♂️ Schritte-Verlauf (Ziel: 10.000 Schritte)")
                if 'Schritte' in df_filtered.columns:
                    chart_data = df_filtered[[date_col, 'Schritte']].copy() if date_col else pd.DataFrame({'Schritte': df_filtered['Schritte']})
                    if date_col:
                        chart_data = chart_data.set_index(date_col)
                    chart_data['Ziel (10k)'] = 10000
                    st.line_chart(chart_data)

                st.markdown("---")
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    st.markdown("### 🥗 Kalorien-Trend (kcal)")
                    if 'KCAL' in df_filtered.columns:
                        kc_data = df_filtered.set_index(date_col)[['KCAL']].copy() if date_col else pd.DataFrame({'KCAL': df_filtered['KCAL']})
                        kc_data['Ziel (2300 kcal)'] = 2300
                        st.line_chart(kc_data)
                with col_n2:
                    st.markdown("### 🥩 Protein-Trend (g)")
                    if 'Prot' in df_filtered.columns:
                        pr_data = df_filtered.set_index(date_col)[['Prot']].copy() if date_col else pd.DataFrame({'Prot': df_filtered['Prot']})
                        pr_data['Ziel (145g)'] = 145
                        st.line_chart(pr_data)

            else:
                st.info("Deine Excel-Datei ist noch leer.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Excel: {e}")
    else:
        st.warning(f"Die Excel-Datei '{EXCEL_FILE}' wurde auf GitHub nicht gefunden.")
