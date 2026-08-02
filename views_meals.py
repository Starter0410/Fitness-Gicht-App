import streamlit as st
import json
import os
from PIL import Image
from logic_gemini import analyze_images_or_text

PRESETS_FILE = "meal_presets.json"

def load_meal_presets():
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "Frühstück": [],
        "Mittagessen": [],
        "Abendessen": [],
        "Snacks": []
    }

def save_meal_presets(presets):
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def render_preset_creator_page(save_callback):
    st.markdown("### 📝 Feste Mahlzeit / Vorlage erstellen")
    st.write("Erstelle hier deine Standard-Gerichte. Sie stehen dir danach direkt in den jeweiligen Tabs zur Auswahl.")

    presets = load_meal_presets()

    with st.form("preset_form"):
        kategorie = st.selectbox("Kategorie", ["Frühstück", "Mittagessen", "Abendessen", "Snacks"])
        titel = st.text_input("Titel (z. B. Protein-Porridge)")
        inhalt = st.text_area("Inhalt / Beschreibung (z. B. 80g Haferflocken, 30g Whey, Beeren)")
        
        col1, col2 = st.columns(2)
        with col1:
            kcal = st.number_input("Kalorien (kcal)", min_value=0, step=10, value=350)
        with col2:
            protein = st.number_input("Protein (g)", min_value=0.0, step=1.0, value=30.0)

        submitted = st.form_submit_button("💾 Vorlage speichern")
        if submitted:
            if titel.strip():
                new_entry = {
                    "titel": titel,
                    "inhalt": inhalt,
                    "kcal": int(kcal),
                    "prot": float(protein),
                    "gicht_status": "Grün"
                }
                if kategorie not in presets:
                    presets[kategorie] = []
                presets[kategorie].append(new_entry)
                save_meal_presets(presets)
                st.success(f"Vorlage '{titel}' unter '{kategorie}' erfolgreich gespeichert!")
            else:
                st.warning("Bitte gib mindestens einen Titel ein.")

    st.markdown("---")
    st.subheader("📚 Deine bisherigen Vorlagen")
    
    for kat, items in presets.items():
        with st.expander(f"{kat} ({len(items)} Vorlagen)"):
            if items:
                for idx, item in enumerate(items):
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.markdown(f"**{item['titel']}** – 🔥 {item['kcal']} kcal | 🥩 {item['prot']}g Protein")
                        if item.get('inhalt'):
                            st.caption(f"Inhalt: {item['inhalt']}")
                    with cols[1]:
                        if st.button("❌ Löschen", key=f"del_preset_{kat}_{idx}"):
                            items.pop(idx)
                            save_meal_presets(presets)
                            st.rerun()
            else:
                st.info("Keine Vorlagen in dieser Kategorie.")

def render_meal_page(title, key, api_key, save_callback):
    st.markdown(f"### 🍽️ {title} erfassen")
    st.write("Wähle eine gespeicherte Vorlage, lade ein Foto hoch oder tippe die Mahlzeit ein.")

    # --- SCHNELL-AUSWAHL AUS GESPEICHERTEN VORLAGEN ---
    presets = load_meal_presets()
    category_presets = presets.get(title, [])
    if category_presets:
        preset_titles = ["-- Vorlage wählen (optional) --"] + [p["titel"] for p in category_presets]
        selected_preset_title = st.selectbox(f"⭐ Schnellauswahl für {title}", preset_titles, key=f"preset_picker_{key}")
        
        if selected_preset_title != "-- Vorlage wählen (optional) --":
            matched = next((p for p in category_presets if p["titel"] == selected_preset_title), None)
            if matched:
                if st.button(f"⚡ Vorlage '{matched['titel']}' sofort eintragen", key=f"add_preset_btn_{key}"):
                    if key not in st.session_state["meals"]:
                        st.session_state["meals"][key] = []
                    
                    st.session_state["meals"][key].append({
                        "titel": matched["titel"],
                        "desc": matched['inhalt'],
                        "kcal": matched["kcal"],
                        "prot": matched["prot"],
                        "notiz": matched['inhalt'],
                        "gicht_status": matched.get("gicht_status", "Grün")
                    })
                    save_callback()
                    st.success(f"'{matched['titel']}' erfolgreich zur Mahlzeit hinzugefügt!")
                    st.rerun()
        st.markdown("---")

    uploaded_images = st.file_uploader(f"📸 Foto(s) für {title} hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_{key}")
    
    pil_imgs = []
    if uploaded_images:
        for f in uploaded_images:
            try:
                pil_imgs.append(Image.open(f))
            except Exception:
                pass
        st.image(uploaded_images, width=150)

    # Eingabefeld für den manuellen Titel
    titel_input = st.text_input(f"Mahlzeiten-Titel (z. B. Bio Banane)", key=f"titel_{key}")
    desc_input = st.text_input(f"Beschreibung / Notiz für {title}", key=f"desc_{key}")

    if st.button(f"✨ {title} per KI analysieren & eintragen", key=f"ai_btn_{key}"):
        if uploaded_images or desc_input or titel_input:
            with st.spinner("KI analysiert Nährwerte und Gicht-Risiko..."):
                ai_result = analyze_images_or_text(api_key, pil_imgs, desc_input)
                
                cal = ai_result.get("kcal", 0)
                prot = ai_result.get("protein", 0)
                notiz = ai_result.get("mahlzeit_notiz") or ai_result.get("beschreibung", "KI-Analyse")
                gicht = ai_result.get("gicht_bewertung", "grün").capitalize()
                
                # Titel Prio: Manuell eingegebener Titel > KI-Titel > Standard-Kategorie
                final_titel = titel_input if titel_input else ai_result.get("titel", title)
                
                if key not in st.session_state["meals"]:
                    st.session_state["meals"][key] = []
                
                st.session_state["meals"][key].append({
                    "titel": final_titel,
                    "desc": desc_input,
                    "kcal": cal,
                    "prot": prot,
                    "notiz": notiz,
                    "gicht_status": gicht
                })
                save_callback()
                st.success(f"Erfolgreich hinzugefügt! Gicht-Status: **{gicht}**")
        else:
            st.warning("Bitte lade mindestens ein Bild hoch oder gib einen Titel/Beschreibung ein.")

    st.markdown("---")
    st.markdown(f"**Bisherige Einträge für {title}:**")
    
    meal_items = st.session_state["meals"].get(key, [])
    if meal_items:
        for idx, item in enumerate(meal_items):
            cols = st.columns([4, 1])
            with cols[0]:
                title_val = item.get('titel', '')
                kcal_val = item.get('kcal', 0)
                prot_val = item.get('prot', 0.0)
                gicht_val = item.get('gicht_status', 'Grün')
                notiz_val = item.get('notiz', '')

                # Angepasste Beschriftung je nach Kategorie (z.B. Frühstück-Titel)
                prefix_label = title[:-1] if title.endswith('en') and title != 'Snacks' else title
                if title == 'Snacks':
                    prefix_label = 'Snack'
                
                st.markdown(f"• **{prefix_label}-Titel : {title_val}**")
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;({kcal_val} kcal, {prot_val}g Protein) | *Gicht: {gicht_val}*")
                if notiz_val:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;Notiz: {notiz_val}")
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
    
    d["wasser_soda"] = st.number_input("Wasser / Soda (Liter)", value=float(d["wasser_soda"]), step=0.5, key="input_wasser_soda")
    d["kaffee"] = st.number_input("Kaffee (Tassen)", value=int(d["kaffee"]), step=1, key="input_kaffee")
    d["whey_scoops"] = st.number_input("Whey Protein (Scoops)", value=int(d["whey_scoops"]), step=1, key="input_whey_scoops")
    d["redbull"] = st.number_input("Red Bull / Energy (Dosen)", value=int(d["redbull"]), step=1, key="input_redbull")
    
    d["sonstiges_txt"] = st.text_input("Sonstige Getränke (Beschreibung)", value=d["sonstiges_txt"], key="input_sonstiges_txt")
    d["sonstiges_kcal"] = st.number_input("Sonstige Getränke Kalorien (kcal)", value=int(d["sonstiges_kcal"]), step=10, key="input_sonstiges_kcal")
    d["sonstiges_prot"] = st.number_input("Sonstige Getränke Protein (g)", value=float(d["sonstiges_prot"]), step=5.0, key="input_sonstiges_prot")

    if st.button("💾 Getränke speichern"):
        save_callback()
        st.success("Getränkewerte aktualisiert!")
