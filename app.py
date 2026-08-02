import streamlit as st
import pandas as pd
from datetime import date
import json
import os

# Importiere deine Views
from views_meals import render_meal_page, render_snacks_page, render_drinks_page

# Excel-Dateiname & Draft-Datei
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"
DRAFT_FILE = "tages_draft.json"

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
        "wasser_soda": 0.0,
        "kaffee": 0,
        "whey_scoops": 0,
        "redbull": 0,
        "sonstiges_txt": "",
        "sonstiges_kcal": 0,
        "sonstiges_prot": 0
    }

if "daily_meta" not in st.session_state:
    st.session_state["daily_meta"] = {
        "gewicht": 0.0,
        "kfa": 0.0,
        "skel_musk": 0.0,
        "schritte": 0,
        "notizen": ""
    }

if "workout" not in st.session_state:
    st.session_state["workout"] = {
        "schritte": 0,
        "zirkel_min": 0,
        "zirkel_details": "",
        "bike_km": 0.0,
        "bike_modus": "",
        "sonstiges": "",
        "notiz": ""
    }

# -------------------------------------------------------------------------
# ZWISCHENSPEICHER (AUTO-SAVE) FUNKTIONEN
# -------------------------------------------------------------------------
def save_draft():
    """Speichert den aktuellen Zwischenstand unsichtbar ab."""
    draft_data = {
        "meals": st.session_state.get("meals", {}),
        "drinks": st.session_state.get("drinks", {}),
        "daily_meta": st.session_state.get("daily_meta", {}),
        "workout": st.session_state.get("workout", {})
    }
    try:
        with open(DRAFT_FILE, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_draft():
    """Lädt den Zwischenstand beim Start automatisch wieder rein."""
    if os.path.exists(DRAFT_FILE) and not st.session_state.get("draft_loaded", False):
        try:
            with open(DRAFT_FILE, "r", encoding="utf-8") as f:
                draft_data = json.load(f)
                st.session_state["meals"] = draft_data.get("meals", st.session_state["meals"])
                st.session_state["drinks"] = draft_data.get("drinks", st.session_state["drinks"])
                st.session_state["daily_meta"] = draft_data.get("daily_meta", st.session_state["daily_meta"])
                st.session_state["workout"] = draft_data.get("workout", st.session_state["workout"])
                st.session_state["draft_loaded"] = True
        except Exception:
            pass

# Draft beim Start laden
load_draft()

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
    """Setzt alle heutigen Daten sauber auf 0 zurück und leert den Draft."""
    st.session_state["meals"] = {"fruehstueck": [], "mittagessen": [], "abendessen": [], "snacks": []}
    st.session_state["drinks"] = {"wasser_soda": 0.0, "kaffee": 0, "whey_scoops": 0, "redbull": 0, "sonstiges_txt": "", "sonstiges_kcal": 0, "sonstiges_prot": 0}
    st.session_state["workout"] = {"schritte": 0, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "notiz": ""}
    st.session_state["daily_meta"] = {"gewicht": 0.0, "kfa": 0.0, "skel_musk": 0.0, "schritte": 0, "notizen": ""}
    
    widget_keys_to_reset = [
        "input_wasser_soda", "input_kaffee", "input_whey_scoops", "input_redbull",
        "input_sonstiges_txt", "input_sonstiges_kcal", "input_sonstiges_prot"
    ]
    for wk in widget_keys_to_reset:
        if wk in st.session_state:
            del st.session_state[wk]
            
    save_draft()

def save_current_day_to_excel():
    save_draft()
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    meta = st.session_state["daily_meta"]
    
    totals_kcal, totals_prot = get_todays_totals()
    target_kcal = 2150
    defizit_ueberschuss = totals_kcal - target_kcal

    all_cat_items = m.get("fruehstueck", []) + m.get("mittagessen", []) + m.get("abendessen", []) + m.get("snacks", [])
    overall_gicht = get_worst_gicht_status(all_cat_items)

    new_row = {
        "Datum": str(date.today()),
        "KG": meta["gewicht"],
        "KCAL": totals_kcal,
        "Prot": totals_prot,
        "Defizit/Überschuss": defizit_ueberschuss,
        "Wasser/Soda/Zitrone": d["wasser_soda"],
        "Red-": d["redbull"],
        "Kaffe": d["kaffee"],
        "Whey": d["whey_scoops"],
        "Getränke-Sonstige": d["sonstiges_txt"],
        "Gicht Status": overall_gicht
    }

    try:
        df = pd.read_excel(EXCEL_FILE)
        if not df.empty and "Datum" in df.columns:
            df = df[df["Datum"] != str(date.today())]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([new_row])

    df.to_excel(EXCEL_FILE, index=False)

# -------------------------------------------------------------------------
# HAUPTSEITE & NAVIGATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered")

save_draft()

with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input("Gemini API Key", value=st.session_state["api_key"], type="password")
    st.markdown("---")
    if st.button("🧹 Heutigen Tag zurücksetzen (Clear All)", type="secondary"):
        clear_todays_data()
        st.success("Alle heutigen Einträge gelöscht!")
        st.rerun()

tab = st.session_state["nav_tab"]

if tab != "🏠 Startseite":
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True, key="global_back_btn"):
        st.session_state["nav_tab"] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

if tab == "🏠 Startseite":
    st.title("Gicht & Body-Recomposition Tracker")
    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
    
    total_kcal, total_prot = get_todays_totals()
    
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
    if st.button("⚖️ Waage & KI-Auslese", use_container_width=True):
        st.session_state["nav_tab"] = "Waage"
        st.rerun()
    if st.button("🏁 Tagesabschluss & Kontrollansicht", use_container_width=True):
        st.session_state["nav_tab"] = "Tagesabschluss"
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

elif tab == "Waage":
    st.title("⚖️ Waage & KI-Auslese")
    st.write("Hier kannst du das Foto deiner Waage hochladen oder die Werte manuell erfassen.")
    meta = st.session_state["daily_meta"]
    meta["gewicht"] = st.number_input("Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1)
    meta["kfa"] = st.number_input("Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1)
    meta["skel_musk"] = st.number_input("Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1)
    if st.button("💾 Werte speichern"):
        save_draft()
        st.success("Waage-Daten gespeichert!")

elif tab == "Tagesabschluss":
    st.title("🏁 Tagesabschluss & Kontrollansicht")
    total_kcal, total_prot = get_todays_totals()
    st.metric("Gesamtbilanz", f"{total_kcal} kcal", f"{total_prot} g Protein")
    if st.button("🚀 In Excel speichern & Download vorbereiten"):
        save_current_day_to_excel()
        st.success("Erfolgreich in die Excel-Tabelle geschrieben!")
