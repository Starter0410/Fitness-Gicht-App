import streamlit as st

def render_meal_page(title, meal_key, api_key, save_callback):
    st.subheader(f"🍳 {title} erfassen")
    
    desc = st.text_input(f"Beschreibung für {title}", key=f"desc_{meal_key}")
    kcal = st.number_input("Kalorien (kcal)", min_value=0, step=10, key=f"kcal_{meal_key}")
    prot = st.number_input("Protein (g)", min_value=0.0, step=1.0, key=f"prot_{meal_key}")
    
    if st.button("➕ Hinzufügen", key=f"btn_{meal_key}"):
        if desc:
            st.session_state["meals"][meal_key].append({"desc": desc, "kcal": kcal, "prot": prot})
            save_callback()
            st.success(f"{title} hinzugefügt!")
            st.rerun()
        else:
            st.warning("Bitte gib eine Beschreibung ein.")

    st.markdown("---")
    st.write(f"**Bisherige Einträge für {title}:**")
    
    items = st.session_state["meals"].get(meal_key, [])
    if not items:
        st.info("Noch keine Einträge.")
    for idx, item in enumerate(items):
        col1, col2 = st.columns([4, 1])
        col1.write(f"- {item['desc']} ({item['kcal']} kcal, {item['prot']}g Protein)")
        if col2.button("❌", key=f"del_{meal_key}_{idx}"):
            st.session_state["meals"][meal_key].pop(idx)
            save_callback()
            st.rerun()

def render_snacks_page(api_key, save_callback):
    st.subheader("🍏 Snacks & Zwischenmahlzeiten")
    
    desc = st.text_input("Snack Beschreibung", key="desc_snacks")
    kcal = st.number_input("Kalorien (kcal)", min_value=0, step=10, key="kcal_snacks")
    prot = st.number_input("Protein (g)", min_value=0.0, step=1.0, key="prot_snacks")
    
    if st.button("➕ Snack hinzufügen", key="btn_snacks"):
        if desc:
            st.session_state["meals"]["snacks"].append({"desc": desc, "kcal": kcal, "prot": prot})
            save_callback()
            st.success("Snack hinzugefügt!")
            st.rerun()
        else:
            st.warning("Bitte gib eine Beschreibung ein.")

    st.markdown("---")
    st.write("**Bisherige Snacks:**")
    
    items = st.session_state["meals"].get("snacks", [])
    if not items:
        st.info("Noch keine Snacks erfasst.")
    for idx, item in enumerate(items):
        col1, col2 = st.columns([4, 1])
        col1.write(f"- {item['desc']} ({item['kcal']} kcal, {item['prot']}g Protein)")
        if col2.button("❌", key=f"del_snacks_{idx}"):
            st.session_state["meals"]["snacks"].pop(idx)
            save_callback()
            st.rerun()

def render_drinks_page(save_callback):
    st.subheader("🥤 Getränke-Zähler")
    
    d = st.session_state["drinks"]
    
    d["wasser_soda"] = st.number_input("Wasser / Soda (Liter)", value=float(d["wasser_soda"]), step=0.5)
    d["kaffee"] = st.number_input("Kaffee (Tassen)", value=int(d["kaffee"]), step=1)
    d["whey_scoops"] = st.number_input("Whey Protein (Scoops)", value=int(d["whey_scoops"]), step=1)
    d["redbull"] = st.number_input("Red Bull / Energy (Dosen)", value=int(d["redbull"]), step=1)
    
    st.markdown("---")
    st.write("**Sonstige Getränke (optional)**")
    d["sonstiges_txt"] = st.text_input("Beschreibung", value=d["sonstiges_txt"])
    d["sonstiges_kcal"] = st.number_input("Kalorien (kcal)", value=int(d["sonstiges_kcal"]), step=10)
    d["sonstiges_prot"] = st.number_input("Protein (g)", value=float(d["sonstiges_prot"]), step=1.0)
    
    if st.button("💾 Getränke speichern"):
        save_callback()
        st.success("Getränkewerte aktualisiert!")
