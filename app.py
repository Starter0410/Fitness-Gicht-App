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
        cleaned_text = clean_json_response(response.text)
        return json.loads(cleaned_text)
    except Exception as e:
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
        cleaned_text = clean_json_response(response.text)
        return json.loads(cleaned_text)
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

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏋️‍♂️ Fitness & Gicht")
    st.markdown("---")
    
    selected_tab = st.selectbox(
        "Navigation",
        [
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
    )
    st.markdown("---")
    st.caption("Body Recomp & Purinarm-Tracking")

# ---------------------------------------------------------
# INHALTE DER SEITEN
# ---------------------------------------------------------

if selected_tab == "🏠 Startseite":
    st.subheader("🏠 Tages-Dashboard")
    st.write("Willkommen zurück, Matthias! Hier hast du den schnellen Überblick über deinen aktuellen Tag.")
    
    cur_kcal, cur_prot = get_todays_totals()
    target_kcal = 2300 
    target_prot = 145
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("### 🔥 Kalorien-Stand")
        st.metric("Aktuell erfasst", f"{cur_kcal} kcal", f"Ziel: {target_kcal} kcal")
        progress_val = min(float(cur_kcal) / float(target_kcal), 1.0)
        st.progress(progress_val, text=f"Fortschritt zum Kalorienziel ({int(progress_val * 100)}%)")

    with col_d2:
        st.markdown("### 🥩 Protein-Stand")
        st.metric("Aktuell erfasst", f"{cur_prot} g", f"Ziel: {target_prot} g")
        progress_prot = min(float(cur_prot) / float(target_prot), 1.0)
        st.progress(progress_prot, text=f"Fortschritt zum Proteinziel ({int(progress_prot * 100)}%)")

    st.markdown("---")
    st.markdown("### 🚀 Schnell-Navigation")
    st.info("Nutze die linke Sidebar, um Mahlzeiten hinzuzufügen, dein Training einzutragen oder den Tagesabschluss zu machen.")

elif selected_tab == "⚖️ Waage":
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

if selected_tab == "🍳 Frühstück":
    render_meal_page("Frühstück", "fruehstueck")
elif selected_tab == "🍲 Mittag":
    render_meal_page("Mittagessen", "mittagessen")
elif selected_tab == "🌙 Abend":
    render_meal_page("Abendessen", "abendessen")

elif selected_tab == "🍏 Snacks":
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

elif selected_tab == "🥤 Getränke":
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

elif selected_tab == "🏋️‍♂️ Training":
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
    w['sonstiges'] = st.text_input("🏊 Sonstiges", value=w['sonstiges'])

elif selected_tab == "✅ Abschluss":
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
                    st.success(f"✅ Tageseintrag erfolgreich gespeichert!")
                except Exception as e:
                    st.error(f"Fehler: {e}")
            else:
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.append([str(datum), g_val, k_val, m_val, kc_val, pr_val, notizen])
                wb.save(EXCEL_FILE)
                st.success(f"✅ Neue Excel erstellt & gespeichert!")

    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 Aktuelle Excel-Datei auf Laptop herunterladen",
                data=file,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

elif selected_tab == "📈 Statistik & Bilanz":
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
