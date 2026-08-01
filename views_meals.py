import streamlit as st
import pandas as pd
from datetime import date

def render_waage_page(api_key, save_callback):
    st.subheader("⚖️ Waagen-Analyse (Foto-Upload)")
    st.write("Lade das Foto deiner Körperfettwaage hoch. Die KI liest die Werte aus und trägt sie ein.")
    
    uploaded_file = st.file_uploader("Waagen-Foto auswählen", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Hochgeladenes Waagen-Foto", use_column_width=True)
        if st.button("🔍 Werte per KI auslesen", type="primary"):
            st.info("KI-Auslesefunktion ist aktiv. (Beispielhaft übernommen)")

    st.markdown("---")
    st.subheader("Manuelle Kontrolle / Anpassung für heute")
    meta = st.session_state["daily_meta"]
    
    meta["gewicht"] = st.number_input("Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1)
    meta["kfa"] = st.number_input("Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1)
    meta["skel_musk"] = st.number_input("Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1)
    
    if st.button("💾 Speichern & übernehmen"):
        save_callback()
        st.success("Waagendaten für heute aktualisiert!")

def render_training_page(api_key, save_callback):
    st.subheader("🏋️‍♂️ Training & Aktivitäten")
    
    w = st.session_state["workout"]
    
    w["schritte"] = st.number_input("Heutige Schritte", value=int(w["schritte"]), step=500)
    st.session_state["daily_meta"]["schritte"] = w["schritte"]
    
    w["zirkel_min"] = st.number_input("Zirkeltraining Dauer (Minuten)", value=int(w["zirkel_min"]), step=5)
    w["zirkel_details"] = st.text_input("Zirkel Details (z.B. 14 kg pro Hantel plus Stange)", value=w["zirkel_details"])
    
    w["bike_km"] = st.number_input("Hometrainer / Bike (km)", value=float(w["bike_km"]), step=0.5)
    w["sonstiges"] = st.text_input("Sonstige Aktivitäten", value=w["sonstiges"])
    w["notiz"] = st.text_area("Training Notiz", value=w["notiz"])
    
    if st.button("💾 Training speichern"):
        save_callback()
        st.success("Trainingsdaten gespeichert!")

def render_statistik_page(excel_file):
    st.subheader("📊 Statistiken & Historie")
    
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        st.warning("Noch keine Excel-Datei vorhanden. Erfasse zuerst Daten und speichere sie ab.")
        return

    if df.empty or "Datum" not in df.columns:
        st.info("Die Excel-Tabelle ist noch leer.")
        return

    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df.sort_values("Datum")

    # -------------------------------------------------------------------------
    # AMPEL-STATISTIK (Grüne, Gelbe, Rote Tage)
    # -------------------------------------------------------------------------
    st.markdown("### 🚦 Tages-Bewertung (Ampel-Status)")
    st.write("Definition: 🟢 Perfekt im Ziel | 🟡 Moderater Puffer | 🔴 Stark abgewichen")
    
    target_k = 2150
    target_p = 140
    
    grün, gelb, rot = 0, 0, 0
    for _, row in df.iterrows():
        k = row.get("KCAL", 0)
        p = row.get("Prot", 0)
        
        if abs(k - target_k) <= 200 and p >= (target_p - 15):
            grün += 1
        elif abs(k - target_k) <= 400 and p >= (target_p - 30):
            gelb += 1
        else:
            rot += 1

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🟢 Grüne Tage", grün)
    col_b.metric("🟡 Gelbe Tage", gelb)
    col_c.metric("🔴 Rote Tage", rot)

    st.markdown("---")

    chart_df = df.set_index("Datum")

    st.markdown("### 🧬 Körperwerte (Body Recomp)")
    
    if "KG" in chart_df.columns:
        st.write("**Gewicht (KG) – Bereich: 60 - 80 kg**")
        st.line_chart(chart_df[["KG"]], yticks=list(range(60, 82, 5)))

    if "KFA" in chart_df.columns:
        st.write("**Körperfettanteil KFA (%) – Bereich: 10 - 18 %**")
        st.line_chart(chart_df[["KFA"]], yticks=list(range(10, 19, 2)))

    if "Skel.Musk" in chart_df.columns:
        st.write("**Skelettmuskulatur – Bereich: 30 - 40**")
        st.line_chart(chart_df[["Skel.Musk"]], yticks=list(range(30, 41, 2)))

    st.markdown("---")
    st.markdown("### 🥗 Ernährungs- & Aktivitäts-Balken")

    if "Schritte" in chart_df.columns:
        st.write("**Schritte-Verlauf**")
        st.bar_chart(chart_df["Schritte"])

    if "KCAL" in chart_df.columns:
        st.write("**Kalorien-Trend (kcal)**")
        st.bar_chart(chart_df["KCAL"])

    if "Prot" in chart_df.columns:
        st.write("**Protein-Trend (g)**")
        st.bar_chart(chart_df["Prot"])

    st.markdown("---")
    st.markdown("### 📋 Vollständige Datentabelle")
    st.dataframe(df)
