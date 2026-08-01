import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

# Importiere deine Ansichten
from views_meals import render_meal_page, render_snacks_page, render_drinks_page
from views_statistik import render_statistik_page

# Excel-Dateiname
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"

# -------------------------------------------------------------------------
# SESSION STATE INITIALISIERUNG
# -------------------------------------------------------------------------
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "🏠 Startseite"

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

if "meals" not in st.session_state:
    st.session_state["meals"] = {
        "fruehstueck": [],
        "mittagessen": [],
        "abendessen": [],
        "snacks": []
    }

if "drinks" not in st.session_state:
    st.session_state["drinks"] = {
        "wasser_soda": 3.0,
        "kaffee": 3,
        "whey_scoops": 1,
        "redbull": 0,
        "sonstiges_txt": "",
        "sonstiges_kcal": 0,
        "sonstiges_prot": 0
    }

if "daily_meta" not in st.session_state:
    st.session_state["daily_meta"] = {
        "gewicht": 80.0,
        "kfa": 15.0,
        "skel_musk": 38.0,
        "schritte": 8000,
        "notizen": ""
    }

# -------------------------------------------------------------------------
# HILFSFUNKTIONEN
# -------------------------------------------------------------------------
def save_current_day_to_excel():
    """Schreibt den aktuellen Tag in die Excel-Datei."""
    totals_kcal, totals_prot = get_todays_totals()
    meta = st.session_state["daily_meta"]
    
    # Mahlzeiten-Beschreibungen für die Excel-Notiz zusammenfassen
    m = st.session_state["meals"]
    f_desc = ", ".join([item["desc"] for item in m.get("fruehstueck", [])])
    m_desc = ", ".join([item["desc"] for item in m.get("mittagessen", [])])
    a_desc = ", ".join([item["desc"] for item in m.get("abendessen", [])])
    s_desc = ", ".join([s["desc"] for s in m.get("snacks", [])])
    
    all_desc = f"Frühstück: {f_desc} | Mittag: {m_desc} | Abend: {a_desc} | Snacks: {s_desc} | Notiz: {meta['notizen']}"

    new_row = {
        "Datum": str(date.today()),
        "Gewicht (kg)": meta["gewicht"],
        "KFA (%)": meta["kfa"],
        "Skel. Muskulatur (kg)": meta["skel_musk"],
        "Schritte": meta["schritte"],
        "KCAL": totals_kcal,
        "Protein (g)": totals_prot,
        "Notizen": all_desc
    }

    try:
        df = pd.read_excel(EXCEL_FILE)
        # Falls das Datum schon existiert, überschreiben oder anhängen
        if not df.empty and "Datum" in df.columns:
            df = df[df["Datum"] != str(date.today())]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([new_row])

    df.to_excel(EXCEL_FILE, index=False)

def get_todays_totals():
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    
    # Da Frühstück, Mittag und Abend nun Listen sind, summieren wir sie sauber auf:
    fruehstueck_kcal = sum([item["kcal"] for item in m.get("fruehstueck", [])])
    fruehstueck_prot = sum([item["prot"] for item in m.get("fruehstueck", [])])
    
    mittag_kcal = sum([item["kcal"] for item in m.get("mittagessen", [])])
    mittag_prot = sum([item["prot"] for item in m.get("mittagessen", [])])
    
    abend_kcal = sum([item["kcal"] for item in m.get("abendessen", [])])
    abend_prot = sum([item["prot"] for item in m.get("abendessen", [])])
    
    snack_kcal = sum([s["kcal"] for s in m.get("snacks", [])])
    snack_prot = sum([s["prot"] for s in m.get("snacks", [])])
    
    whey_kcal = d["whey_scoops"] * 120
    whey_prot = d["whey_scoops"] * 30
    total_drink_kcal = whey_kcal + d["sonstiges_kcal"]
    total_drink_prot = whey_prot + d["sonstiges_prot"]
    
    total_kcal = fruehstueck_kcal + mittag_kcal + abend_kcal + snack_kcal + total_drink_kcal
    total_prot = fruehstueck_prot + mittag_prot + abend_prot + snack_prot + total_drink_prot
    return total_kcal, total_prot

# -------------------------------------------------------------------------
# HAUPTSEITE & NAVIGATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered")

# API Key Eingabe (Sidebar)
with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input("Gemini API Key", value=st.session_state["api_key"], type="password")
    st.markdown("---")
    if st.button("🔄 App Daten zurücksetzen"):
        st.session_state.clear()
        st.rerun()

tab = st.session_state["nav_tab"]

if tab == "🏠 Startseite":
    st.title("🏋️‍♂️ Gicht & Body-Recomposition Tracker")
    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
    
    total_kcal, total_prot = get_todays_totals()
    
    # Dashboard Metriken
    col1, col2 = st.columns(2)
    col1.metric("Heutige Kalorien", f"{total_kcal} kcal")
    col2.metric("Heutiges Protein", f"{total_prot} g")
    
    st.markdown("---")
    st.subheader("📌 Menü")
    
    if st.button("🍳 Frühstück erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Frühstück"
        st.rerun()
    if st.button("🥗 Mittagessen erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Mittagessen"
        st.rerun()
    if st.button("🍲 Abendessen erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Abendessen"
        st.rerun()
    if st.button("🍏 Snacks & Zwischenmahlzeiten", use_container_width=True):
        st.session_state["nav_tab"] = "Snacks"
        st.rerun()
    if st.button("🥤 Getränke-Zähler", use_container_width=True):
        st.session_state["nav_tab"] = "Getränke"
        st.rerun()
    if st.button("📊 Statistiken & Tabellen", use_container_width=True):
        st.session_state["nav_tab"] = "Statistiken"
        st.rerun()
    if st.button("🏁 Tagesabschluss & Endkontrolle", use_container_width=True):
        st.session_state["nav_tab"] = "Abschluss"
        st.rerun()

elif tab == "Frühstück":
    render_meal_page("Frühstück", "fruehstueck", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Mittagessen":
    render_meal_page("Mittagessen", "mittagessen", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Abendessen":
    render_meal_page("Abendessen", "abendessen", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Snacks":
    render_snacks_page(st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Getränke":
    render_drinks_page(save_current_day_to_excel)

elif tab == "Statistiken":
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state["nav_tab"] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")
    render_statistik_page(EXCEL_FILE)

elif tab == "Abschluss":
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state["nav_tab"] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")
    st.subheader("🔍 Tagesabschluss & Endkontrolle")
    
    meta = st.session_state["daily_meta"]
    meta["gewicht"] = st.number_input("Heutiges Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1)
    meta["kfa"] = st.number_input("Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1)
    meta["skel_musk"] = st.number_input("Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1)
    meta["schritte"] = st.number_input("Heutige Schritte", value=int(meta["schritte"]), step=500)
    meta["notizen"] = st.text_area("Tagesnotizen / Befinden", value=meta["notizen"])
    
    total_kcal, total_prot = get_todays_totals()
    st.info(f"**Bisherige Tagesbilanz:** {total_kcal} kcal | {total_prot} g Protein")
    
    if st.button("🚀 In Excel speichern & Download vorbereiten", type="primary"):
        save_current_day_to_excel()
        st.success("Tagesdaten erfolgreich in die Excel-Tabelle geschrieben!")
        
        # Download Button bereitstellen
        with open(EXCEL_FILE, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label="📥 Excel-Datei herunterladen",
            data=excel_bytes,
            file_name=EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
