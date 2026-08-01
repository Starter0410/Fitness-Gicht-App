import streamlit as st
import pandas as pd
from datetime import date

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
        "gewicht": 69.7,
        "kfa": 13.4,
        "skel_musk": 34.3,
        "schritte": 8000,
        "notizen": ""
    }

if "workout" not in st.session_state:
    st.session_state["workout"] = {
        "schritte": 8000,
        "zirkel_min": 0,
        "zirkel_details": "",
        "bike_km": 0.0,
        "bike_modus": "",
        "sonstiges": "",
        "notiz": ""
    }

# -------------------------------------------------------------------------
# HILFSFUNKTIONEN
# -------------------------------------------------------------------------
def get_worst_gicht_status(items):
    if not items:
        return "Grün"
    rank = {"grün": 1, "gelb": 2, "rot": 3}
    worst_score = 1
    worst_word = "Grün"
    for item in items:
        status = str(item.get('gicht_status', 'Grün')).strip().lower()
        current_score = rank.get(status, 1)
        if current_score > worst_score:
            worst_score = current_score
            worst_word = status.capitalize()
    return worst_word

def get_todays_totals():
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    
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

def clear_todays_data():
    """Setzt alle heutigen Daten und die Widget-Schlüssel sicher zurück, ohne die App zu stören."""
    st.session_state["meals"] = {"fruehstueck": [], "mittagessen": [], "abendessen": [], "snacks": []}
    st.session_state["drinks"] = {"wasser_soda": 3.0, "kaffee": 3, "whey_scoops": 1, "redbull": 0, "sonstiges_txt": "", "sonstiges_kcal": 0, "sonstiges_prot": 0}
    st.session_state["workout"] = {"schritte": 8000, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "notiz": ""}
    st.session_state["daily_meta"] = {"gewicht": 69.7, "kfa": 13.4, "skel_musk": 34.3, "schritte": 8000, "notizen": ""}
    
    # Gezieltes Löschen der spezifischen Widget-Keys, damit Eingabefelder im UI sofort auf Standard springen
    widget_keys_to_reset = [
        "input_wasser_soda", "input_kaffee", "input_whey_scoops", "input_redbull",
        "input_sonstiges_txt", "input_sonstiges_kcal", "input_sonstiges_prot"
    ]
    for wk in widget_keys_to_reset:
        if wk in st.session_state:
            del st.session_state[wk]

# -------------------------------------------------------------------------
# SEITEN-LAYOUT & NAVIGATION (Beispielhafter Rahmen)
# -------------------------------------------------------------------------
st.set_page_config(page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered")

with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input("Gemini API Key", value=st.session_state["api_key"], type="password")
    st.markdown("---")
    if st.button("🧹 Heutigen Tag zurücksetzen (Clear All)", type="secondary"):
        clear_todays_data()
        st.success("Alle heutigen Einträge gelöscht!")
        st.rerun()

# Rest deiner app.py mit den entsprechenden Aufrufen von render_drinks_page() etc.
