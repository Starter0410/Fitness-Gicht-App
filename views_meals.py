import streamlit as st
from PIL import Image
from logic_gemini import analyze_images_or_text

def render_back_button():
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state['nav_tab'] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

def display_gicht_badge(status, notiz=""):
    if status == "rot":
        st.error("🔴 **Gichtgefahr (Hoher Puringehalt)**\n\n💡 *" + notiz + "*")
    elif status == "gelb":
        st.warning("🟡 **Moderat (Mittlerer Puringehalt)**\n\n💡 *" + notiz + "*")
    else:
        st.success("🟢 **Gichtfreundlich (Purinarm)**\n\n💡 *" + notiz + "*")

def show_image_previews(files):
    if files:
        cols = st.columns(min(len(files), 4))
        for idx, file in enumerate(files):
            cols[idx % 4].image(Image.open(file), use_container_width=True)

def render_meal_page(tab_name, meal_key, api_key, save_callback):
    render_back_button()
    st.subheader(f"Mahlzeit erfassen: {tab_name}")
    
    if meal_key == 'fruehstueck':
        st.markdown("⭐ **Schnell-Auswahl (Favoriten):**")
        fav_wahl = st.selectbox(
            "Wähle ein oft gegessenes Frühstück:", 
            ["-- Manuell / Foto eingeben --", "Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)"],
            key=f"{meal_key}_fav_select"
        )
        if fav_wahl == "Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)":
            st.session_state['meals'][meal_key] = {
                'kcal': 455, 
                'prot': 45, 
                'desc': 'Overnight-Oats (Griechischer Joghurt + Proteinpulver und Früchte)', 
                'gicht': 'grün', 
                'notiz': 'Hervorragender proteinreicher und purinarmer Start in den Tag!'
            }
            save_callback()
        st.markdown("---")

    imgs = st.file_uploader(f"Foto(s) von {tab_name} hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"{meal_key}_img")
    show_image_previews(imgs)
    
    txt = st.text_input(f"Oder beschreibe dein {tab_name}", key=f"{meal_key}_txt")
    
    if st.button(f"🤖 {tab_name} analysieren", key=f"{meal_key}_btn", type="primary"):
        if imgs or txt:
            pil_imgs = [Image.open(f) for f in imgs] if imgs else []
            res = analyze_images_or_text(api_key, pil_imgs, txt if txt else "Kein Text angegeben")
            st.session_state['meals'][meal_key] = {
                'kcal': int(res.get('kcal', 0)),
                'prot': int(res.get('protein', 0)),
                'desc': res.get('beschreibung', txt),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            }
            save_callback()
            st.success(f"{tab_name} erfolgreich ausgewertet!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    current = st.session_state['meals'][meal_key]
    if current['kcal'] > 0 or current['desc']:
        st.info(f"**Erfasst:** {current['desc']} | **{current['kcal']} kcal** | **{current['prot']}g Protein**")
        display_gicht_badge(current['gicht'], current.get('notiz', ''))

def render_snacks_page(api_key, save_callback):
    render_back_button()
    st.subheader("🍏 Snacks & Zwischenmahlzeiten")
    imgs_s = st.file_uploader("Foto(s) vom Snack", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="snack_img")
    show_image_previews(imgs_s)
    
    txt_s = st.text_input("Oder Snack beschreiben", key="snack_txt")
    
    if st.button("🤖 Snack hinzufügen", type="primary"):
        if imgs_s or txt_s:
            pil_imgs = [Image.open(f) for f in imgs_s] if imgs_s else []
            res = analyze_images_or_text(api_key, pil_imgs, txt_s if txt_s else "Kein Text angegeben")
            st.session_state['meals']['snacks'].append({
                'kcal': int(res.get('kcal', 0)),
                'prot': int(res.get('protein', 0)),
                'desc': res.get('beschreibung', txt_s),
                'gicht': res.get('gicht_bewertung', 'grün'),
                'notiz': res.get('mahlzeit_notiz', '')
            })
            save_callback()
            st.success("Snack zur Tagesliste hinzugefügt!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    if st.session_state['meals']['snacks']:
        st.markdown("### 🍿 Heutige Snacks:")
        for idx, s in enumerate(st.session_state['meals']['snacks'], 1):
            st.write(f"**{idx}.** {s['desc']} — {s['kcal']} kcal | {s['prot']}g Protein")
            display_gicht_badge(s['gicht'], s.get('notiz', ''))

def render_drinks_page(save_callback):
    render_back_button()
    st.subheader("🥤 Getränke-Zähler")
    d = st.session_state['drinks']
    
    col1, col2 = st.columns(2)
    with col1:
        d['wasser_soda'] = st.number_input("💧 Wasser / Soda / Zitrone (Liter)", value=float(d['wasser_soda']), step=0.5)
        d['kaffee'] = st.number_input("☕ Kaffee (Tassen)", value=int(d['kaffee']), step=1)
    with col2:
        d['whey_scoops'] = st.number_input("🐮 Whey / Iso Clear (Scoops)", value=int(d['whey_scoops']), step=1)
        d['redbull'] = st.number_input("⚡ Red Bull (Dosen)", value=int(d['redbull']), step=1)
        
    st.markdown("---")
    st.write("**🥤 Sonstiges Getränk:**")
    d['sonstiges_txt'] = st.text_input("Name des Getränks", value=d['sonstiges_txt'])
    cs1, cs2 = st.columns(2)
    d['sonstiges_kcal'] = cs1.number_input("Kalorien (kcal)", value=int(d['sonstiges_kcal']), step=10)
    d['sonstiges_prot'] = cs2.number_input("Protein (g)", value=int(d['sonstiges_prot']), step=1)
    save_callback()
