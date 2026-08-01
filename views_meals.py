import streamlit as st
import pandas as pd
from datetime import date

def render_meals_page(api_key, save_callback):
    st.subheader("🍽️ Ernährungs- & Mahlzeiten-Erfassung (mit KI-Analyse)")
    st.write("Lade Fotos hoch oder tippe die Mahlzeit ein. Die KI berechnet Kalorien, Protein und bewertet den Gicht-Status.")

    # Beispielhafte Hilfsfunktion für die KI-Analyse
    def analyze_food_with_ai(description, uploaded_files):
        # Hier greift deine KI-Logik (z.B. Gemini Vision für Fotos / Text)
        # Dummy-Werte als Fallback:
        cal = 500
        prot = 30
        notiz = f"KI-Analyse für: {description if description else 'Hochgeladenes Bild'}"
        gicht = "Gelb"
        return cal, prot, notiz, gicht

    # Tabs für die Mahlzeiten
    tabs = st.tabs(["🌅 Frühstück", "☀️ Mittagessen", "🌙 Abendessen", "🍎 Snacks"])

    meal_types = [("fruehstueck", "Frühstück"), ("mittag", "Mittagessen"), ("abend", "Abendessen"), ("snacks", "Snacks")]

    for i, (key, title) in enumerate(meal_types):
        with tabs[i]:
            st.markdown(f"### {title} erfassen")
            
            # 1. Bildupload für KI-Analyse
            uploaded_images = st.file_uploader(f"📸 Foto(s) für {title} hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_{key}")
            
            if uploaded_images:
                st.image(uploaded_images, width=150, caption=[f"Bild {idx+1}" for idx in range(len(uploaded_images))])

            # 2. Beschreibung / Text-Eingabe
            desc_input = st.text_input(f"Beschreibung / Text für {title}", key=f"desc_{key}")

            # Button zur KI-Analyse & automatischen Übernahme
            if st.button(f"✨ {title} per KI analysieren & eintragen", key=f"ai_btn_{key}"):
                if uploaded_images or desc_input:
                    with st.spinner("KI analysiert Nährwerte und Gicht-Risiko..."):
                        cal, prot, notiz, gicht = analyze_food_with_ai(desc_input, uploaded_images)
                        
                        # In den Session State eintragen
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
            
            # Einträge anzeigen und löschbar machen
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
