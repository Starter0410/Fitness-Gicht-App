import streamlit as st
import pandas as pd
from datetime import date
import os

from views_meals import render_meal_page, render_snacks_page, render_drinks_page, render_preset_creator_page

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Project Zeal - built differnt",
    page_icon="⚡",
    layout="wide"
)

# --- SESSION STATE INITIALISIERUNG ---
if "meals" not in st.session_state:
    st.session_state["meals"] = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
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
        "sonstiges_prot": 0.0
    }

if "body_data" not in st.session_state:
    st.session_state["body_data"] = {
        "weight": 75.0,
        "body_fat": 15.0,
        "muscle": 60.0,
        "steps": 8000
    }

EXCEL_FILE = "tagesprotokoll.xlsx"

def save_to_excel():
    """Dummy-Funktion zum Speichern der Daten in Excel."""
    pass

def format_meal_column(items):
    """Zieht für die Excel-Tabelle exakt den reinen Titel heraus."""
    if not items:
        return ""
    titles = []
    for item in items:
        title = (
            item.get("titel") 
            or item.get("name") 
            or item.get("desc") 
            or ""
        ).strip()
        if title:
            titles.append(title)
    return " | ".join(titles) if titles else ""

# --- SEITEN-NAVIGATION (SIDEBAR) ---
st.sidebar.title("⚡ Project Zeal")
st.sidebar.caption("built differnt - a new area")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation", 
    ["Frühstück", "Mittagessen", "Abendessen", "Snacks", "Getränke", "Waage & Körper", "Vorlagen verwalten", "Tagesabschluss & Kontrolle"]
)

# Sicherer Zugriff auf Streamlit Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = ""

# --- SEITEN LOGIK ---
if page == "Frühstück":
    render_meal_page("Frühstück", "breakfast", API_KEY, save_to_excel)

elif page == "Mittagessen":
    render_meal_page("Mittagessen", "lunch", API_KEY, save_to_excel)

elif page == "Abendessen":
    render_meal_page("Abendessen", "dinner", API_KEY, save_to_excel)

elif page == "Snacks":
    render_snacks_page(API_KEY, save_to_excel)

elif page == "Getränke":
    render_drinks_page(save_to_excel)

elif page == "Waage & Körper":
    st.markdown("### ⚖️ Waage & Körperwerte")
    b = st.session_state["body_data"]
    b["weight"] = st.number_input("Körpergewicht (kg)", value=float(b["weight"]), step=0.1)
    b["body_fat"] = st.number_input("Körperfett (%)", value=float(b["body_fat"]), step=0.1)
    b["muscle"] = st.number_input("Muskelmasse (kg)", value=float(b["muscle"]), step=0.1)
    b["steps"] = st.number_input("Schritte des Tages", value=int(b["steps"]), step=500)
    
    if st.button("💾 Körperwerte speichern"):
        save_to_excel()
        st.success("Körperwerte erfolgreich aktualisiert!")

elif page == "Vorlagen verwalten":
    render_preset_creator_page(save_to_excel)

elif page == "Tagesabschluss & Kontrolle":
    st.markdown("### 🔍 Tagesabschluss & Kontrollansicht")
    
    # Statistiken-Metriken oben
    b = st.session_state["body_data"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gewicht", f"{b['weight']} kg")
    col2.metric("Körperfett", f"{b['body_fat']} %")
    col3.metric("Muskelmasse", f"{b['muscle']} kg")
    col4.metric("Schritte", f"{b['steps']}")
    
    st.markdown("---")
    
    with st.expander("📊 Übersicht der erfassten Mahlzeiten, Notizen & Gicht-Status (Kontrolle)", expanded=True):
        
        total_kcal = 0
        total_prot = 0.0
        
        for key in ["breakfast", "lunch", "dinner", "snacks"]:
            for item in st.session_state["meals"].get(key, []):
                total_kcal += item.get("kcal", 0)
                total_prot += float(item.get("prot", 0.0))
        
        d = st.session_state["drinks"]
        total_kcal += int(d.get("sonstiges_kcal", 0))
        total_prot += float(d.get("sonstiges_prot", 0.0))
        
        st.markdown(f"**Gesamtbilanz:** 🔥 **{total_kcal} kcal** | 🥩 **{total_prot:.1f} g Protein**")
        st.markdown("---")
        
        categories = [
            ("Frühstück", "breakfast"),
            ("Mittagessen", "lunch"),
            ("Abendessen", "dinner"),
            ("Snacks", "snacks")
        ]
        
        for cat_name, key in categories:
            items = st.session_state["meals"].get(key, [])
            st.markdown(f"**🍽️ {cat_name}:**")
            
            if items:
                for item in items:
                    title_val = item.get('titel', '')
                    kcal_val = item.get('kcal', 0)
                    prot_val = item.get('prot', 0.0)
                    gicht_val = item.get('gicht_status', 'Grün')
                    notiz_val = item.get('notiz', '')
                    
                    prefix = cat_name[:-1] if cat_name.endswith('en') and cat_name != 'Snacks' else cat_name
                    if cat_name == 'Snacks':
                        prefix = 'Snack'
                    
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• **{prefix}-Titel : {title_val}**")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;({kcal_val} kcal, {prot_val}g Protein) | *Gicht: {gicht_val}*")
                    if notiz_val:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Notiz: {notiz_val}")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Keine Einträge*")
            
            st.write("")
            
        st.markdown("---")
        st.markdown(f"🥤 **Getränke:** Wasser/Soda: {d['wasser_soda']}L | Kaffee: {d['kaffee']} Tassen | Whey: {d['whey_scoops']} Scoops | Energy: {d['redbull']} Dosen")
        if d['sonstiges_txt']:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;Sonstiges: {d['sonstiges_txt']} ({d['sonstiges_kcal']} kcal, {d['sonstiges_prot']}g Protein)")
