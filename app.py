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
    Guten Morgen,

    Mein Name ist Matthias. Ich habe immer wieder Probleme mit Gichtschüben. Daher haben wir an unserer App gefeilt. Mein Ziel ist eine Body-Recomposition: Mein Gewicht darf stabil bleiben oder leicht steigen, der Fokus liegt aber auf der gezielten Reduktion des Bauchfetts bei gleichzeitigem Erhalt der gesamten Muskelmasse, unter strikter Einhaltung purinarmer Ernährung (Gicht-Prävention). Wir kombinieren in unserem Tagebuch Körperwerte, Essen, Getränke, Training und Subs.

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
tabs = st.tabs([
    "📊 Statistik & Bilanz", 
    "⚖️ Waage", 
    "🥐 Frühstück", 
    "🥗 Mittag", 
    "🍝 Abend", 
    "🍏 Snacks", 
    "🥤 Getränke", 
    "🏋️‍♂️ Training", 
    "📊 Abschluss"
])

# --- TAB 0: STATISTIK & BILANZ ---
with tabs[0]:
    st.subheader("📈 Historische Auswertungen, Wochen- & Monatsbilanz")
    
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            
            if not df.empty:
                # Spaltennamen bereinigen
                df.columns = [str(c).strip() for c in df.columns]
                
                # Spalte 'Skel.Musk' für die Anzeige im Diagramm schick ausschreiben
                if 'Skel.Musk' in df.columns:
                    df.rename(columns={'Skel.Musk': 'Skelettmuskel (%)'}, inplace=True)
                
                # Zahlenkonvertierung für wichtige Spalten erzwingen
                numeric_cols = ['KG', 'KFA', 'Skelettmuskel (%)', 'KCAL', 'Prot', 'Schritte']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # Datums-Spalte verarbeiten
                date_col = None
                for c in df.columns:
                    if 'datum' in c.lower() or 'date' in c.lower():
                        date_col = c
                        break
                
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df = df.sort_values(by=date_col, ascending=False) # Neueste zuerst für Wochenbilanz
                    df['Monat-Jahr'] = df[date_col].dt.strftime('%Y-%m')
                    
                    # --- NEU: WOCHEN- & MONATSBILANZ BOX ---
                    st.markdown("### 📊 Aktuelle Bilanzen (Durchschnitte)")
                    
                    # Die letzten 7 Tage berechnen
                    recent_7 = df.head(7)
                    avg_7_kcal = int(recent_7['KCAL'].mean()) if 'KCAL' in recent_7.columns and not recent_7['KCAL'].dropna().empty else 0
                    avg_7_prot = int(recent_7['Prot'].mean()) if 'Prot' in recent_7.columns and not recent_7['Prot'].dropna().empty else 0
                    avg_7_steps = int(recent_7['Schritte'].mean()) if 'Schritte' in recent_7.columns and not recent_7['Schritte'].dropna().empty else 0
                    
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("Ø KCAL (Letzte 7 Tage)", f"{avg_7_kcal} kcal")
                    col_b2.metric("Ø Protein (Letzte 7 Tage)", f"{avg_7_prot} g")
                    col_b3.metric("Ø Schritte (Letzte 7 Tage)", f"{avg_7_steps}")

                    st.markdown("---")

                    # Filter UI für Diagramme
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

                # 1. Körperwerte
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

                # 2. Schritte
                st.markdown("### 🚶‍♂️ Schritte-Verlauf (Ziel: 10.000 Schritte)")
                if 'Schritte' in df_filtered.columns:
                    chart_data = df_filtered[[date_col, 'Schritte']].copy() if date_col else pd.DataFrame({'Schritte': df_filtered['Schritte']})
                    if date_col:
                        chart_data = chart_data.set_index(date_col)
                    chart_data['Ziel (10k)'] = 10000
                    st.line_chart(chart_data)

                st.markdown("---")

                # 3. Kalorien & Protein
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

                st.markdown("---")

                # 4. Gicht-Status Auswertung
                status_col = None
                for c in df_filtered.columns:
                    if 'gicht' in c.lower() or 'status' in c.lower() or 'ampel' in c.lower():
                        status_col = c
                        break
                
                if status_col:
                    st.markdown(f"### 🛡️ Gicht-Ampel Historie")
                    green_count, yellow_count, red_count = 0, 0, 0
                    
                    for val in df_filtered[status_col]:
                        v_str = str(val).lower()
                        if 'rot' in v_str or 'red' in v_str or '🔴' in v_str: red_count += 1
                        elif 'gelb' in v_str or 'yellow' in v_str or '🟡' in v_str: yellow_count += 1
                        else: green_count += 1

                    am_c1, am_c2, am_c3 = st.columns(3)
                    am_c1.metric("🟢 Grüne Tage", f"{green_count}")
                    am_c2.metric("🟡 Gelbe Tage", f"{yellow_count}")
                    am_c3.metric("🔴 Rote Tage", f"{red_count}")
                    
                    counts_df = pd.DataFrame({'Anzahl Tage': [green_count, yellow_count, red_count]}, index=['Grün', 'Gelb', 'Rot'])
                    st.bar_chart(counts_df)

            else:
                st.info("Deine Excel-Datei ist noch leer.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Excel: {e}")
    else:
        st.warning(f"Die Excel-Datei '{EXCEL_FILE}' wurde auf GitHub nicht gefunden.")

# --- TAB 1: WAAGE ---
with tabs[1]:
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

# --- HAUPTMAHLZEITEN (MIT FRÜHSTÜCKS-FAVORITEN) ---
def render_meal_tab(tab_name, meal_key):
    st.subheader(f"Mahlzeit erfassen: {tab_name}")
    
    # NEU: Schnell-Auswahl für Favoriten beim Frühstück
    if meal_key == 'fruehstueck':
        st.markdown("⭐ **Schnell-Auswahl (Favoriten):**")
        fav_wahl = st.selectbox(
            "Wähle ein oft gegessenes Frühstück:", 
            ["-- Manuell / Foto eingeben --", "Quarkbrot mit Haferflocken & Beeren", "Protein-Porridge mit Joghurt"]
        )
        if fav_wahl == "Quarkbrot mit Haferflocken & Beeren":
            st.session_state['meals'][meal_key] = {'kcal': 450, 'prot': 35, 'desc': 'Quarkbrot mit Haferflocken & Beeren', 'gicht': 'grün', 'notiz': 'Perfekter purinarmer Start mit viel Protein!'}
        elif fav_wahl == "Protein-Porridge mit Joghurt":
            st.session_state['meals'][meal_key] = {'kcal': 400, 'prot': 30, 'desc': 'Protein-Porridge mit Joghurt', 'gicht': 'grün', 'notiz': 'Guter Eiweißgehalt, ideal für den Muskelerhalt.'}
        st.markdown("---")

    imgs = st.file_uploader(f"Foto(s) von {tab_name} hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"{meal_key}_img")
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

with tabs[2]: render_meal_tab("Frühstück", "fruehstueck")
with tabs[3]: render_meal_tab("Mittagessen", "mittagessen")
with tabs[4]: render_meal_tab("Abendessen", "abendessen")

# --- TAB 5: SNACKS ---
with tabs[5]:
    st.subheader("🍏 Snacks & Zwischenmahlzeiten")
    imgs_s = st.file_uploader("Foto(s) vom Snack", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="snack_img")
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
            }
            )
            st.success("Snack zur Tagesliste hinzugefügt!")

    if st.session_state['meals']['snacks']:
        st.markdown("### 🍿 Heutige Snacks:")
        for idx, s in enumerate(st.session_state['meals']['snacks'], 1):
            st.write(f"**{idx}.** {s['desc']} — {s['kcal']} kcal | {s['prot']}g Protein")
            display_gicht_badge(s['gicht'], s.get('notiz', ''))

# --- TAB 6: GETRÄNKE ---
with tabs[6]:
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

# --- TAB 7: TRAINING ---
with tabs[7]:
    st.subheader("🏋️‍♂️ Training & Aktivitäten erfassen")
    imgs_tr = st.file_uploader("Screenshots hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="tr_imgs")
    show_image_previews(imgs_tr)
    
    txt_tr = st.text_input("Oder Training beschreiben", key="tr_txt")
    
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
    w['schritte'] = st.number_input("🚶 Schritte Anzahl", value=int(w['schritte']), step=500)
    col_z1, col_z2 = st.columns([1, 2])
    w['zirkel_min'] = col_z1.number_input("⏱️ Zirkel (Min)", value=int(w['zirkel_min']), step=5)
    w['zirkel_details'] = col_z2.text_input("Übungen / Wdh", value=w['zirkel_details'])
    col_b1, col_b2 = st.columns(2)
    w['bike_km'] = col_b1.number_input("🚴 Fahrrad (km)", value=float(w['bike_km']), step=1.0)
    w['bike_modus'] = col_b2.text_input("E-Bike Modus", value=w['bike_modus'])
    w['sonstiges'] = st.text_input("🏊 Sonstiges", value=w['sonstiges'])

# --- TAB 8: TAGESABSCHLUSS ---
with tabs[8]:
    st.subheader("🔍 Tagesabschluss & Endkontrolle")
    m = st.session_state['meals']
    d = st.session_state['drinks']
    w = st.session_state['workout']
    
    whey_kcal = d['whey_scoops'] * 120
    whey_prot = d['whey_scoops'] * 30
    total_drink_kcal = whey_kcal + d['sonstiges_kcal']
    total_drink_prot = whey_prot + d['sonstiges_prot']
    snack_kcal = sum(s['kcal'] for s in m['snacks'])
    snack_prot = sum(s['prot'] for s in m['snacks'])
    
    total_kcal = m['fruehstueck']['kcal'] + m['mittagessen']['kcal'] + m['abendessen']['kcal'] + snack_kcal + total_drink_kcal
    total_prot = m['fruehstueck']['prot'] + m['mittagessen']['prot'] + m['abendessen']['prot'] + snack_prot + total_drink_prot

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
