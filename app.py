import os
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import json
import datetime
import streamlit.components.v1 as components

# Importiere die ausgelagerten Views & Logiken
from views_meals import render_meal_page, render_snacks_page, render_drinks_page
from views_training import render_waage_page, render_training_page, render_statistik_page

# =========================================================
# API-KEY LADEN (Priorität: Streamlit Secrets -> Fallback)
# =========================================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
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

# Automatisches Scrollen nach oben bei jedem Klick
components.html(
    """
    <script>
        window.parent.document.querySelector('.main').scrollTop = 0;
    </script>
    """,
    height=0,
)

# Session State für Navigation initialisieren
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "🏠 Startseite"

# ---------------------------------------------------------
# PERSISTENTE DATEN LADEN & SPEICHERN
# ---------------------------------------------------------
def save_daily_backup():
    data = {
        "meals": st.session_state.get("meals"),
        "drinks": st.session_state.get("drinks"),
        "workout": st.session_state.get("workout"),
        "waage_data": st.session_state.get("waage_data"),
        "saved_g": st.session_state.get("saved_g"),
        "saved_k": st.session_state.get("saved_k"),
        "saved_m": st.session_state.get("saved_m")
    }
    try:
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_daily_backup():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if data.get("meals"): st.session_state["meals"] = data["meals"]
                    if data.get("drinks"): st.session_state["drinks"] = data["drinks"]
                    if data.get("workout"): st.session_state["workout"] = data["workout"]
                    if data.get("waage_data"): st.session_state["waage_data"] = data["waage_data"]
                    if data.get("saved_g") is not None: st.session_state["saved_g"] = data["saved_g"]
                    if data.get("saved_k") is not None: st.session_state["saved_k"] = data["saved_k"]
                    if data.get("saved_m") is not None: st.session_state["saved_m"] = data["saved_m"]
        except Exception:
            pass

# Tages-Speicher initialisieren, falls leer
if "meals" not in st.session_state:
    st.session_state["meals"] = {
        "fruehstueck": {"kcal": 0, "prot": 0, "desc": "", "gicht": "grün", "notiz": ""},
        "mittagessen": {"kcal": 0, "prot": 0, "desc": "", "gicht": "grün", "notiz": ""},
        "abendessen": {"kcal": 0, "prot": 0, "desc": "", "gicht": "grün", "notiz": ""},
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

if "waage_data" not in st.session_state:
    st.session_state["waage_data"] = {"gewicht": None, "kfa": None, "skelettmuskel": None}

if "initialized_backup" not in st.session_state:
    load_daily_backup()
    st.session_state["initialized_backup"] = True

def get_todays_totals():
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    
    whey_kcal = d["whey_scoops"] * 120
    whey_prot = d["whey_scoops"] * 30
    total_drink_kcal = whey_kcal + d["sonstiges_kcal"]
    total_drink_prot = whey_prot + d["sonstiges_prot"]
    
    snack_kcal = sum([s["kcal"] for s in m["snacks"]])
    snack_prot = sum([s["prot"] for s in m["snacks"]])
    
    total_kcal = m["fruehstueck"]["kcal"] + m["mittagessen"]["kcal"] + m["abendessen"]["kcal"] + snack_kcal + total_drink_kcal
    total_prot = m["fruehstueck"]["prot"] + m["mittagessen"]["prot"] + m["abendessen"]["prot"] + snack_prot + total_drink_prot
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
    selected_tab = st.radio("Navigation", tabs, index=tabs.index(st.session_state["nav_tab"]) if st.session_state["nav_tab"] in tabs else 0, label_visibility="collapsed")
    st.session_state["nav_tab"] = selected_tab
    st.markdown("---")
    st.caption("Body Recomp & Purinarm-Tracking")

# ---------------------------------------------------------
# HAUPTSEITEN ROUTING
# ---------------------------------------------------------
if st.session_state["nav_tab"] == "🏠 Startseite":
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
        steps = st.session_state["workout"]["schritte"]
        render_gauge_svg(steps, 10000, "🚶 Schritte", "Steps", "#10b981")

    st.markdown("---")
    st.markdown("### 📱 Schnell-Übersicht & Navigation")
    
    grid_cols = st.columns(3)
    if grid_cols[0].button("⚖️ Waage", use_container_width=True):
        st.session_state["nav_tab"] = "⚖️ Waage"
        st.rerun()
    if grid_cols[1].button("🍳 Frühstück", use_container_width=True):
        st.session_state["nav_tab"] = "🍳 Frühstück"
        st.rerun()
    if grid_cols[2].button("🍲 Mittag", use_container_width=True):
        st.session_state["nav_tab"] = "🍲 Mittag"
        st.rerun()

    grid_cols_2 = st.columns(3)
    if grid_cols_2[0].button("🌙 Abend", use_container_width=True):
        st.session_state["nav_tab"] = "🌙 Abend"
        st.rerun()
    if grid_cols_2[1].button("🍏 Snacks", use_container_width=True):
        st.session_state["nav_tab"] = "🍏 Snacks"
        st.rerun()
    if grid_cols_2[2].button("🥤 Getränke", use_container_width=True):
        st.session_state["nav_tab"] = "🥤 Getränke"
        st.rerun()

    grid_cols_3 = st.columns(3)
    if grid_cols_3[0].button("🏋️‍♂️ Training", use_container_width=True):
        st.session_state["nav_tab"] = "🏋️‍♂️ Training"
        st.rerun()
    if grid_cols_3[1].button("✅ Abschluss", use_container_width=True):
        st.session_state["nav_tab"] = "✅ Abschluss"
        st.rerun()
    if grid_cols_3[2].button("📈 Statistik", use_container_width=True):
        st.session_state["nav_tab"] = "📈 Statistik & Bilanz"
        st.rerun()

elif st.session_state["nav_tab"] == "⚖️ Waage":
    render_waage_page(GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "🍳 Frühstück":
    render_meal_page("Frühstück", "fruehstueck", GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "🍲 Mittag":
    render_meal_page("Mittagessen", "mittagessen", GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "🌙 Abend":
    render_meal_page("Abendessen", "abendessen", GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "🍏 Snacks":
    render_snacks_page(GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "🥤 Getränke":
    render_drinks_page(save_daily_backup)

elif st.session_state["nav_tab"] == "🏋️‍♂️ Training":
    render_training_page(GEMINI_API_KEY, save_daily_backup)

elif st.session_state["nav_tab"] == "✅ Abschluss":
    from views_meals import render_back_button
    render_back_button()
    st.subheader("🔍 Tagesabschluss & Endkontrolle")
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    w = st.session_state["workout"]
    
    total_kcal, total_prot = get_todays_totals()

    drink_list = []
    if d["wasser_soda"] > 0: drink_list.append(f"{d['wasser_soda']}L Wasser/Soda")
    if d["kaffee"] > 0: drink_list.append(f"{d['kaffee']}x Kaffee")
    if d["whey_scoops"] > 0: drink_list.append(f"{d['whey_scoops']} Scoop Whey")
    if d["redbull"] > 0: drink_list.append(f"{d['redbull']}x Red Bull")
    if d["sonstiges_txt"]: drink_list.append(f"{d['sonstiges_txt']}")
    
    drink_summary = ", ".join(drink_list) if drink_list else "Keine Drinks"
    
    workout_list = []
    if w["schritte"] > 0: workout_list.append(f"{w['schritte']} Schritte")
    if w["zirkel_min"] > 0: workout_list.append(f"Zirkel {w['zirkel_min']}m")
    if w["bike_km"] > 0: workout_list.append(f"Bike {w['bike_km']}km")
    workout_summary = ", ".join(workout_list) if workout_list else "Keine Aktivität"

    col_a, col_b = st.columns(2)
    col_a.metric("Gesamtkalorien", f"{total_kcal} kcal")
    col_b.metric("Gesamtprotein", f"{total_prot} g")
    
    descriptions = []
    if m["fruehstueck"]["desc"]: descriptions.append(f"Frühstück: {m['fruehstueck']['desc']}")
    if m["mittagessen"]["desc"]: descriptions.append(f"Mittag: {m['mittagessen']['desc']}")
    if m["abendessen"]["desc"]: descriptions.append(f"Abend: {m['abendessen']['desc']}")
    if m["snacks"]: descriptions.append("Snacks vorhanden")
    descriptions.append(f"Getränke: {drink_summary}")
    descriptions.append(f"Training: {workout_summary}")
    
    full_notes = " | ".join(descriptions)

    with st.form("final_excel_form"):
        datum = st.date_input("Datum", value=datetime.date.today())
        c1, c2, c3 = st.columns(3)
        
        g_val = c1.number_input("Gewicht (kg)", value=float(st.session_state.get("saved_g", 0.0)), step=0.1)
        k_val = c2.number_input("KFA (%)", value=float(st.session_state.get("saved_k", 0.0)), step=0.1)
        m_val = c3.number_input("Skelettmuskel (%)", value=float(st.session_state.get("saved_m", 0.0)), step=0.1)
        
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

elif st.session_state["nav_tab"] == "📈 Statistik & Bilanz":
    render_statistik_page(EXCEL_FILE)
