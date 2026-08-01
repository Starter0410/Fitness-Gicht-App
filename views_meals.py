import streamlit as st
import pandas as pd
from datetime import date

# Allgemeine Hilfsfunktion für die KI-Analyse (kann an deinen echten API-Key angebunden werden)
def analyze_food_with_ai(description, uploaded_files):
    # Dummy-Auswertung als Fallback
    cal = 500
    prot = 30
    notiz = f"KI-Analyse für: {description if description else 'Hochgeladenes Bild'}"
    gicht = "Gelb"
    return cal, prot, notiz, gicht

def render_meal_section(key, title, api_key, save_callback):
    st.markdown(f"### 🍽️ {title} erfassen")
    st.write("Lade Fotos hoch oder tippe die Mahlzeit ein. Die KI berechnet Nährwerte und den Gicht-Status.")

    uploaded_images = st.file_uploader(f"📸 Foto(s) für {title} hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_{key}")
    
    if uploaded_images:
        st.image(uploaded_images, width=150)

    desc_input = st.text_input(f"Beschreibung / Text für {title}", key=f"desc_{key}")

    if st.button(f"✨ {title} per KI analysieren & eintragen", key=f"ai_btn_{key}"):
        if uploaded_images or desc_input:
            with st.spinner("KI analysiert Nährwerte und Gicht-Risiko..."):
                cal, prot, notiz, gicht = analyze_food_with_ai(desc_input, uploaded_images)
                
                if key not in st.session_state:
                    st.session_state[key] = []
                
                st.session_state[key].append({
                    "titel": desc_input if desc_input else title,
                    "kalorien": cal,
                    "protein": prot,
                    "notiz": notiz,
                    "gicht_status": gicht
                })
                save_callback()
                st.success(f"Erfolgreich hinzugefügt! Gicht-Status: **{gicht}**")
        else:
            st.warning("Bitte lade mindestens ein Bild hoch oder gib eine Beschreibung ein.")

    st.markdown("---")
    st.markdown(f"**Bisherige Einträge für {title}:**")
    
    if key in st.session_state and st.session_state[key]:
        for idx, item in enumerate(st.session_state[key]):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"- **{item['titel']}** ({item['kalorien']} kcal, {item['protein']}g Protein) | *Gicht: {item.get('gicht_status', 'None')}*")
                if item.get('notiz'):
                    st.caption(f"Notiz: {item['notiz']}")
            with cols[1]:
                if st.button("❌", key=f"del_{key}_{idx}"):
                    st.session_state[key].pop(idx)
                    save_callback()
                    st.rerun()
    else:
        st.info("Noch keine Einträge.")

# Wrapper-Funktionen, die exakt von deiner app.py importiert werden:
def render_meal_page(api_key, save_callback):
    # Falls das die Hauptseite für Mahlzeiten ist, teilen wir es in Tabs oder zeigen Frühstück/Mittag/Abend
    tab1, tab2, tab3 = st.tabs(["🌅 Frühstück", "☀️ Mittagessen", "🌙 Abendessen"])
    with tab1:
        render_meal_section("fruehstueck", "Frühstück", api_key, save_callback)
    with tab2:
        render_meal_section("mittag", "Mittagessen", api_key, save_callback)
    with tab3:
        render_meal_section("abend", "Abendessen", api_key, save_callback)

def render_snacks_page(api_key, save_callback):
    render_meal_section("snacks", "Snacks & Zwischenmahlzeiten", api_key, save_callback)

def render_drinks_page(api_key, save_callback):
    render_meal_section("getraenke", "Getränke", api_key, save_callback)
