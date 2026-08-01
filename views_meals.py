import streamlit as st
from PIL import Image
from logic import analyze_images_or_text

def render_meal_page(title, key, api_key, save_callback):
    st.markdown(f"### 🍽️ {title} erfassen")
    st.write("Lade Fotos hoch oder tippe die Mahlzeit ein. Die KI berechnet Nährwerte und den Gicht-Status.")

    uploaded_images = st.file_uploader(f"📸 Foto(s) für {title} hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_{key}")
    
    pil_imgs = []
    if uploaded_images:
        for f in uploaded_images:
            try:
                pil_imgs.append(Image.open(f))
            except Exception:
                pass
        st.image(uploaded_images, width=150)

    desc_input = st.text_input(f"Beschreibung / Text für {title}", key=f"desc_{key}")

    if st.button(f"✨ {title} per KI analysieren & eintragen", key=f"ai_btn_{key}"):
        if uploaded_images or desc_input:
            with st.spinner("KI analysiert Nährwerte und Gicht-Risiko..."):
                # Nutzung der zentralen Logik-Funktion
                ai_result = analyze_images_or_text(api_key, pil_imgs, desc_input)
                
                cal = ai_result.get("kcal", 0)
                prot = ai_result.get("protein", 0)
                notiz = ai_result.get("mahlzeit_notiz") or ai_result.get("beschreibung", "KI-Analyse")
                gicht = ai_result.get("gicht_bewertung", "grün").capitalize()
                
                if key not in st.session_state["meals"]:
                    st.session_state["meals"][key] = []
                
                st.session_state["meals"][key].append({
                    "desc": desc_input if desc_input else title,
                    "kcal": cal,
                    "prot": prot,
                    "notiz": notiz,
                    "gicht_status": gicht
                })
                save_callback()
                st.success(f"Erfolgreich hinzugefügt! Gicht-Status: **{gicht}**")
        else:
            st.warning("Bitte lade mindestens ein Bild hoch oder gib eine Beschreibung ein.")

    st.markdown("---")
    st.markdown(f"**Bisherige Einträge für {title}:**")
    
    meal_items = st.session_state["meals"].get(key, [])
    if meal_items:
        for idx, item in enumerate(meal_items):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"- **{item['desc']}** ({item['kcal']} kcal, {item['prot']}g Protein) | *Gicht: {item.get('gicht_status', 'Grün')}*")
                if item.get('notiz'):
                    st.caption(f"Notiz: {item['notiz']}")
            with cols[1]:
                if st.button("❌", key=f"del_{key}_{idx}"):
                    meal_items.pop(idx)
                    save_callback()
                    st.rerun()
    else:
                    st.info("Noch keine Einträge.")

def render_snacks_page(api_key, save_callback):
    render_meal_page("Snacks", "snacks", api_key, save_callback)

def render_drinks_page(save_callback):
    st.subheader("🥤 Getränke-Zähler")
    d = st.session_state["drinks"]
    
    d["wasser_soda"] = st.number_input("Wasser / Soda (Liter)", value=float(d["wasser_soda"]), step=0.5)
    d["kaffee"] = st.number_input("Kaffee (Tassen)", value=int(d["kaffee"]), step=1)
    d["whey_scoops"] = st.number_input("Whey Protein (Scoops)", value=int(d["whey_scoops"]), step=1)
    d["redbull"] = st.number_input("Red Bull / Energy (Dosen)", value=int(d["redbull"]), step=1)
    
    d["sonstiges_txt"] = st.text_input("Sonstige Getränke (Beschreibung)", value=d["sonstiges_txt"])
    d["sonstiges_kcal"] = st.number_input("Sonstige Getränke Kalorien (kcal)", value=int(d["sonstiges_kcal"]), step=10)
    d["sonstiges_prot"] = st.number_input("Sonstige Getränke Protein (g)", value=float(d["sonstiges_prot"]), step=5.0)

    if st.button("💾 Getränke speichern"):
        save_callback()
        st.success("Getränkewerte aktualisiert!")
