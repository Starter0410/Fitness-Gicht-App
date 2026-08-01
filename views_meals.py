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
        st.info("Noch keine Einträge.")  # <--- Hier war die Einrückung korrigiert
