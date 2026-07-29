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
EXCEL_FILE = "daten.xlsx"  # Hier ggf. den genauen Namen deiner Excel-Datei eintragen

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
    Guten Morgen,

    Mein Name ist Matthias. Ich habe immer wieder Probleme mit Gichtschüben. Daher haben wir ein Gichttagebuch angefangen. Mein Ziel ist eine Body-Recomposition: Mein Gewicht darf stabil bleiben oder leicht steigen, der Fokus liegt aber auf der gezielten Reduktion des Bauchfetts bei gleichzeitigem Erhalt der gesamten Muskelmasse, unter strikter Einhaltung purinarmer Ernährung (Gicht-Prävention). Wir kombinieren in unserem Tagebuch Körperwerte, Essen, Getränke, Training und Subs.

    Analysiere diese(s) Bild(er) / diesen Text ({text_prompt}). Wenn mehrere Bilder vorhanden sind, kombiniere alle erfassten Mahlzeiten/Daten zu einer Gesamtsumme bzw. Auswertung.

    Du analysierst diese Mahlzeiten auf KCAL, Protein und vergibst für jede Mahlzeit genau einen Ampel-Wert (Dropdown: grün, gelb, rot) nach folgender fester Logik:
    - GRÜN: Vegetarisch oder rein purinarm (z. B. Milchprodukte, Eier, Gemüse, Obst, Haferflocken).
    - GELB: Hühnchen / Geflügel (moderate Purine).
    - ROT: Alle anderen Fleischsorten (z. B. Rind, Schwein, Fisch/Meeresfrüchte – stark purinhaltig).

    Der allgemeine "Gicht Status" am Ende des Tages richtet sich nach den vergebenen Ampeln der Mahlzeiten (wenn alles grün/gelb bleibt, ist der Status grün/gelb; so bald rotes Fleisch dabei ist, schlägt der Gicht-Status entsprechend an).

    Zu jeder Mahlzeit gibst du mir eine Notiz – überlege dir was. Fokus auf Gicht, aber es können auch motivierende oder mahnende Worte sein. 
    Wenn es eine Waage ist: Lies Gewicht, KFA und Skelettmuskelmasse ab. Setze gicht_bewertung auf "grün" und erstelle ein motivierendes Feedback.

    Gib das Ergebnis STRENG im folgenden JSON-Format zurück:
    {{
        "gewicht": float oder null,
        "kfa": float oder null,
        "skelettmuskel": float oder null,
        "kcal": int oder 0,
        "protein": int oder 0,
        "beschreibung": "Kurze prägnante Zusammenfassung der Speisen/Bilder",
        "gicht_bewertung": "rot" oder "gelb" oder "grün",
        "mahlzeit_notiz": "Kurze Notiz/Feedback zur Mahlzeit mit Fokus auf Gicht, Purine, Motivation oder Mahnung."
    }}
    """
    
    contents = [prompt]
    if images:
        for img in images:
            contents.append(img)
        
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(response.text)

def analyze_workout(images, text_prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Du bist der persönliche Fitness-Coach von Matthias.
    Analysiere diese(s) Bild(er) (Workout-Screenshot, Fitness-Tracker, E-Bike App) und/oder diesen Text: {text_prompt}.
    Fasse ALLE erkennbaren Trainingsleistungen zusammen. Gib mir Notizen, die motivierend sein sollen.
    Gib das Ergebnis STRENG im folgenden JSON-Format zurück:
    {{
        "schritte": int oder 0,
        "zirkel_min": int oder 0,
        "zirkel_details": "Beschreibung von Übungen/Wiederholungen falls erkennbar",
        "bike_km": float oder 0.0,
        "bike_modus": "z.B. Eco, Tour, Sport, Turbo falls angegeben",
        "sonstiges": "Andere Sportarten wie Schwimmen/Seilspringen",
        "workout_notiz": "Ein sehr motivierender, lobender oder anspornender Satz zur Tages-Trainingsleistung von Matthias."
    }}
    """
    contents = [prompt]
    if images:
        for img in images:
            contents.append(img)
        
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(response.text)

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

# ---------------------------------------------------------
# TAB-NAVIGATION
# ---------------------------------------------------------
tabs = st.tabs(["⚖️ Waage", "🥐 Frühstück", "🥗 Mittag", "🍝 Abend", "🍏 Snacks", "🥤 Getränke", "🏋️‍♂️ Training", "📊 Abschluss"])

# --- TAB 1: WAAGE ---
with tabs[0]:
    st.subheader("⚖️ Waagen-Messung")
    imgs_w = st.file_uploader("Foto(s) der Waage / App wählen (mehrere möglich)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="w_img")
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

# --- HAUPTMAHLZEITEN ---
def render_meal_tab(tab_name, meal_key):
    st.subheader(f"Mahlzeit erfassen: {tab_name}")
    imgs = st.file_uploader(f"Foto(s) von {tab_name} hochladen (mehrere möglich)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"{meal_key}_img")
    show_image_previews(imgs)
    
    txt = st.text_input(f"Oder beschreibe dein {tab_name}", key=f"{meal_key}_txt")
    
    if st.button(f"🤖 {tab_name} analysieren", key=f"{meal_key}_btn", type="primary"):
        if imgs or txt:
            pil_imgs = [Image.open(f) for f in imgs] if imgs else []
            res = analyze_images_or_text(pil_imgs, txt)
            st.session_state['meals'][meal_key] = {
                'kcal': res.get('kcal', 0),
                'prot': res.get('protein', 0),
                'desc': res.get('beschreibung', txt),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            }
            st.success(f"{tab_name} erfolgreich ausgewertet!")

    current = st.session_state['meals'][meal_key]
    if current['kcal'] > 0 or current['desc']:
        st.info(f"**Erfasst:** {current['desc']} | **{current['kcal']} kcal** | **{current['prot']}g Protein**")
        display_gicht_badge(current['gicht'], current.get('notiz', ''))

with tabs[1]: render_meal_tab("Frühstück", "fruehstueck")
with tabs[2]: render_meal_tab("Mittagessen", "mittagessen")
with tabs[3]: render_meal_tab("Abendessen", "abendessen")

# --- TAB 5: SNACKS ---
with tabs[4]:
    st.subheader("🍏 Snacks & Zwischenmahlzeiten")
    imgs_s = st.file_uploader("Foto(s) vom Snack (mehrere möglich)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="snack_img")
    show_image_previews(imgs_s)
    
    txt_s = st.text_input("Oder Snack beschreiben", key="snack_txt")
    
    if st.button("🤖 Snack hinzufügen", type="primary"):
        if imgs_s or txt_s:
            pil_imgs = [Image.open(f) for f in imgs_s] if imgs_s else []
            res = analyze_images_or_text(pil_imgs, txt_s)
            st.session_state['meals']['snacks'].append({
                'kcal': res.get('kcal', 0),
                'prot': res.get('protein', 0),
                'desc': res.get('beschreibung', txt_s),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            })
            st.success("Snack zur Tagesliste hinzugefügt!")

    if st.session_state['meals']['snacks']:
        st.markdown("### 🍿 Heutige Snacks:")
        for idx, s in enumerate(st.session_state['meals']['snacks'], 1):
            st.write(f"**{idx}.** {s['desc']} — {s['kcal']} kcal | {s['prot']}g Protein")
            display_gicht_badge(s['gicht'], s.get('notiz', ''))

# --- TAB 6: GETRÄNKE ---
with tabs[5]:
    st.subheader("🥤 Getränke-Zähler")
    
    d = st.session_state['drinks']
    
    col1, col2 = st.columns(2)
    with col1:
        d['wasser_soda'] = st.number_input("💧 Wasser / Soda / Zitrone (Liter)", value=float(d['wasser_soda']), step=0.5)
        d['kaffee'] = st.number_input("☕ Kaffee (Tassen)", value=int(d['kaffee']), step=1)
    
    with col2:
        d['whey_scoops'] = st.number_input("🐮 Whey / Iso Clear (Scoops = 30g Prot)", value=int(d['whey_scoops']), step=1)
        d['redbull'] = st.number_input("⚡ Red Bull (Dosen)", value=int(d['redbull']), step=1)
        
    st.markdown("---")
    st.write("**🥤 Sonstiges Getränk (z. B. Cola Zero):**")
    d['sonstiges_txt'] = st.text_input("Name des Getränks", value=d['sonstiges_txt'], placeholder="z. B. Cola Zero")
    cs1, cs2 = st.columns(2)
    d['sonstiges_kcal'] = cs1.number_input("Kalorien (kcal)", value=int(d['sonstiges_kcal']), step=10)
    d['sonstiges_prot'] = cs2.number_input("Protein (g)", value=int(d['sonstiges_prot']), step=1)

# --- TAB 7: TRAINING ---
with tabs[6]:
    st.subheader("🏋️‍♂️ Training & Aktivitäten erfassen")
    
    imgs_tr = st.file_uploader(
        "Screenshots vom Training / E-Bike / Tracker hochladen (mehrere möglich)", 
        type=["jpg", "png", "jpeg"], 
        accept_multiple_files=True, 
        key="tr_imgs"
    )
    show_image_previews(imgs_tr)
    
    txt_tr = st.text_input("Oder Training beschreiben", key="tr_txt", placeholder="z. B. 45 Min Zirkeltraining mit Kurzhanteln und Planks")
    
    if st.button("🤖 Training analysieren", type="primary"):
        if imgs_tr or txt_tr:
            pil_imgs = [Image.open(f) for f in imgs_tr] if imgs_tr else []
            res_tr = analyze_workout(pil_imgs, txt_tr)
            
            st.session_state['workout']['schritte'] = res_tr.get('schritte') or st.session_state['workout']['schritte']
            st.session_state['workout']['zirkel_min'] = res_tr.get('zirkel_min') or st.session_state['workout']['zirkel_min']
            st.session_state['workout']['zirkel_details'] = res_tr.get('zirkel_details') or st.session_state['workout']['zirkel_details']
            st.session_state['workout']['bike_km'] = float(res_tr.get('bike_km') or st.session_state['workout']['bike_km'])
            st.session_state['workout']['bike_modus'] = res_tr.get('bike_modus') or st.session_state['workout']['bike_modus']
            st.session_state['workout']['sonstiges'] = res_tr.get('sonstiges') or st.session_state['workout']['sonstiges']
            st.session_state['workout']['notiz'] = res_tr.get('workout_notiz', '')
            st.success("Training erfolgreich analysiert!")

    w = st.session_state['workout']
    
    st.markdown("---")
    st.write("✏️ **Manuelle Anpassung / Details:**")
    
    w['schritte'] = st.number_input("🚶 Schritte Anzahl", value=int(w['schritte']), step=500)
    
    col_z1, col_z2 = st.columns([1, 2])
    w['zirkel_min'] = col_z1.number_input("⏱️ Zirkel (Min)", value=int(w['zirkel_min']), step=5)
    w['zirkel_details'] = col_z2.text_input("Übungen / Wdh", value=w['zirkel_details'], placeholder="z.B. 3 Runden Kurzhanteln & Planks")
    
    col_b1, col_b2 = st.columns(2)
    w['bike_km'] = col_b1.number_input("🚴 Fahrrad (km)", value=float(w['bike_km']), step=1.0)
    w['bike_modus'] = col_b2.text_input("E-Bike Modus", value=w['bike_modus'], placeholder="z.B. Tour / Sport")
    
    w['sonstiges'] = st.text_input("🏊 Sonstiges (Schwimmen, Seilspringen)", value=w['sonstiges'])

    if w['notiz']:
        st.success(f"💪 **Coach-Feedback:** {w['notiz']}")

# --- TAB 8: TAGESABSCHLUSS ---
with tabs[7]:
    st.subheader("🔍 Tagesabschluss & Endkontrolle")
    
    m = st.session_state['meals']
    d = st.session_state['drinks']
    w = st.session_state['workout']
    
    # Nährwerte Getränke berechnen
    whey_kcal = d['whey_scoops'] * 120
    whey_prot = d['whey_scoops'] * 30
    
    total_drink_kcal = whey_kcal + d['sonstiges_kcal']
    total_drink_prot = whey_prot + d['sonstiges_prot']
    
    # Nährwerte Mahlzeiten berechnen
    snack_kcal = sum(s['kcal'] for s in m['snacks'])
    snack_prot = sum(s['prot'] for s in m['snacks'])
    
    total_kcal = m['fruehstueck']['kcal'] + m['mittagessen']['kcal'] + m['abendessen']['kcal'] + snack_kcal + total_drink_kcal
    total_prot = m['fruehstueck']['prot'] + m['mittagessen']['prot'] + m['abendessen']['prot'] + snack_prot + total_drink_prot

    # Getränke-Zusammenfassung
    drink_list = []
    if d['wasser_soda'] > 0: drink_list.append(f"{d['wasser_soda']}L Wasser/Soda")
    if d['kaffee'] > 0: drink_list.append(f"{d['kaffee']}x Kaffee")
    if d['whey_scoops'] > 0: drink_list.append(f"{d['whey_scoops']} Scoop(s) Whey")
    if d['redbull'] > 0: drink_list.append(f"{d['redbull']}x Red Bull")
    if d['sonstiges_txt']: drink_list.append(f"{d['sonstiges_txt']} ({d['sonstiges_kcal']} kcal / {d['sonstiges_prot']}g Prot)")
    
    drink_summary = ", ".join(drink_list) if drink_list else "Keine gesonderten Getränke erfasst"

    # Trainings-Zusammenfassung
    workout_list = []
    if w['schritte'] > 0: workout_list.append(f"{w['schritte']} Schritte")
    if w['zirkel_min'] > 0: workout_list.append(f"Zirkel {w['zirkel_min']}m ({w['zirkel_details']})")
    if w['bike_km'] > 0: workout_list.append(f"Bike {w['bike_km']}km [{w['bike_modus']}]")
    if w['sonstiges']: workout_list.append(f"Sonstiges: {w['sonstiges']}")
    
    workout_summary = ", ".join(workout_list) if workout_list else "Ruhetag / Keine Aktivitäten"

    st.markdown("### 📊 Tagesübersicht")
    col_a, col_b = st.columns(2)
    col_a.metric("Gesamtkalorien (inkl. Drinks)", f"{total_kcal} kcal")
    col_b.metric("Gesamtprotein (inkl. Drinks)", f"{total_prot} g")
    
    st.info(f"🥤 **Getränke:** {drink_summary}")
    st.success(f"🏋️‍♂️ **Training:** {workout_summary}")

    st.markdown("---")
    
    descriptions = []
    if m['fruehstueck']['desc']: descriptions.append(f"Frühstück: {m['fruehstueck']['desc']} [{m['fruehstueck']['gicht'].upper()}]")
    if m['mittagessen']['desc']: descriptions.append(f"Mittag: {m['mittagessen']['desc']} [{m['mittagessen']['gicht'].upper()}]")
    if m['abendessen']['desc']: descriptions.append(f"Abend: {m['abendessen']['desc']} [{m['abendessen']['gicht'].upper()}]")
    if m['snacks']: descriptions.append("Snacks: " + ", ".join(s['desc'] for s in m['snacks']))
    if drink_list: descriptions.append(f"Getränke: {drink_summary}")
    if workout_list: descriptions.append(f"Training: {workout_summary}")
    if w['notiz']: descriptions.append(f"Coach-Notiz: {w['notiz']}")
    
    full_notes = " | ".join(descriptions)

    with st.form("final_excel_form"):
        datum = st.date_input("Datum", value=datetime.date.today())
        
        st.write("**Waagendaten:**")
        c1, c2, c3 = st.columns(3)
        g_val = c1.number_input("Gewicht (kg)", value=float(st.session_state.get('saved_g', 0.0)), step=0.1)
        k_val = c2.number_input("KFA (%)", value=float(st.session_state.get('saved_k', 0.0)), step=0.1)
        m_val = c3.number_input("Skelettmuskel (%)", value=float(st.session_state.get('saved_m', 0.0)), step=0.1)
        
        st.write("**Nährwerte Gesamt:**")
        c4, c5 = st.columns(2)
        kc_val = c4.number_input("Kalorien Gesamt (kcal)", value=total_kcal)
        pr_val = c5.number_input("Protein Gesamt (g)", value=total_prot)
        
        notizen = st.text_area("Generierte Tagesnotiz für Excel", value=full_notes, height=120)
        
        if st.form_submit_button("🚀 In Excel speichern & Download vorbereiten"):
            if os.path.exists(EXCEL_FILE):
                try:
                    wb = load_workbook(EXCEL_FILE)
                    ws = wb.active
                    ws.append([str(datum), g_val, k_val, m_val, kc_val, pr_val, notizen])
                    wb.save(EXCEL_FILE)
                    st.success(f"✅ Tageseintrag für den {datum} erfolgreich in '{EXCEL_FILE}' gespeichert!")
                except Exception as e:
                    st.error(f"Fehler beim Speichern: {e}")
            else:
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.append([str(datum), g_val, k_val, m_val, kc_val, pr_val, notizen])
                wb.save(EXCEL_FILE)
                st.success(f"✅ Neue Excel erstellt und Eintrag gespeichert!")

    # --- DOWNLOAD BUTTON FÜR DEINEN LAPTOP ---
    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 Aktuelle Excel-Datei auf Laptop herunterladen",
                data=file,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
