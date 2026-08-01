import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image

def analyze_food_with_ai(description, uploaded_files, api_key):
    """Echte KI-Analyse für Mahlzeiten (Bilder + Text) inklusive Gicht-Bewertung."""
    if not api_key:
        return 0, 0.0, "Kein API-Key hinterlegt.", "None"
    
    genai.configure(api_key=api_key)
    # Verwende ein geeignetes Gemini-Modell für Multimodalität (Text + Bild)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Analysiere die folgende Mahlzeit (Beschreibung: '{description}'). 
    Gib mir das Ergebnis exakt in folgendem Format zurück, ohne zusätzlichen Text drumherum:
    KALORIEN: [Zahl in kcal]
    PROTEIN: [Zahl in Gramm]
    NOTIZ: [Kurze Beschreibung/Analyse der Inhaltsstoffe]
    GICHT: [Grün, Gelb oder Rot - je nach Purin-Gehalt/Gicht-Verträglichkeit]
    """
    
    content_parts = [prompt]
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f)
            content_parts.append(img)
            
    try:
        response = model.generate_content(content_parts)
        text = response.text
        
        # Werte aus dem KI-Antworttext parsen
        cal, prot, notiz, gicht = 0, 0.0, "KI-Analyse erfolgreich", "Gelb"
        for line in text.split("\n"):
            if "KALORIEN:" in line:
                cal = int(''.join(filter(str.isdigit, line)))
            elif "PROTEIN:" in line:
                prot = float(''.join(filter(lambda c: c.isdigit() or c=='.', line)))
            elif "NOTIZ:" in line:
                notiz = line.replace("NOTIZ:", "").strip()
            elif "GICHT:" in line:
                gicht_val = line.replace("GICHT:", "").strip().capitalize()
                if gicht_val in ["Grün", "Gelb", "Rot"]:
                    gicht = gicht_val
                    
        return cal, prot, notiz, gicht
    except Exception as e:
        return 0, 0.0, f"Fehler bei KI-Analyse: {str(e)}", "None"

def render_meal_page(title, key, api_key, save_callback):
    st.markdown(f"### 🍽️ {title} erfassen")
    st.write("Lade Fotos hoch oder tippe die Mahlzeit ein. Die KI berechnet Nährwerte und den Gicht-Status.")

    uploaded_images = st.file_uploader(f"📸 Foto(s) für {title} hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_{key}")
    
    if uploaded_images:
        st.image(uploaded_images, width=150)

    desc_input = st.text_input(f"Beschreibung / Text für {title}", key=f"desc_{key}")

    if st.button(f"✨ {title} per KI analysieren & eintragen", key=f"ai_btn_{key}"):
        if uploaded_images or desc_input:
            with st.spinner("KI analysiert Nährwerte und Gicht-Risiko..."):
                cal, prot, notiz, gicht = analyze_food_with_ai(desc_input, uploaded_images, api_key)
                
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

def render_snacks_page(api_key, save_callback):
    render_meal_page("Snacks", "snacks", api_key, save_callback)

def render_drinks_page(api_key, save_callback):
    render_meal_page("Getränke", "getraenke", api_key, save_callback)
