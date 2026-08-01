import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

    # Hilfsspalten für Monat und Jahr für den Filter erstellen
    df["JahrMonat"] = df["Datum"].dt.strftime("%Y-%m")
    
    # Verfügbare Monate ermitteln (absteigend, damit der neueste oben steht)
    verfuegbare_monate = sorted(df["JahrMonat"].unique(), reverse=True)
    
    # Aktueller Monat im Format "YYYY-MM" (heute ist August 2026 -> "2026-08")
    aktueller_monat_str = date.today().strftime("%Y-%m")

    st.markdown("### 📅 Zeitraum-Filter")
    filter_option = st.selectbox(
        "Wähle den anzuzeigenden Zeitraum:",
        ["Aktueller Monat", "Gesamter Zeitraum"] + [f"Monat: {m}" for m in verfuegbare_monate]
    )

    # DataFrame entsprechend dem Filter einschränken
    if filter_option == "Aktueller Monat":
        if aktueller_monat_str in verfuegbare_monate:
            filtered_df = df[df["JahrMonat"] == aktueller_monat_str].copy()
        else:
            # Fallback falls für den aktuellen Monat noch keine Daten existieren
            filtered_df = df.copy()
            st.info(f"Für den aktuellen Monat ({aktueller_monat_str}) sind noch keine Daten vorhanden. Zeige alle Daten.")
    elif filter_option == "Gesamter Zeitraum":
        filtered_df = df.copy()
    else:
        # Ausgewählter spezifischer Monat (z.B. "Monat: 2026-07")
        gewählter_monat = filter_option.replace("Monat: ", "")
        filtered_df = df[df["JahrMonat"] == gewählter_monat].copy()

    if filtered_df.empty:
        st.warning("Für den gewählten Zeitraum sind keine Daten vorhanden.")
        return

    st.markdown("---")

    # -------------------------------------------------------------------------
    # AMPEL-STATISTIK (bezogen auf den gefilterten Zeitraum)
    # -------------------------------------------------------------------------
    st.markdown("### 🚦 Tages-Bewertung (Ampel-Status)")
    st.write("Definition: 🟢 Perfekt im Ziel | 🟡 Moderater Puffer | 🔴 Stark abgewichen")
    
    target_k = 2150
    target_p = 140
    
    grün, gelb, rot = 0, 0, 0
    for _, row in filtered_df.iterrows():
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

    st.markdown("### 🧬 Körperwerte (Body Recomp)")
    
    # 1. Gewicht (Fester Bereich: 60 - 80)
    if "KG" in filtered_df.columns:
        fig_kg = px.line(filtered_df, x="Datum", y="KG", title="Gewicht (KG) – Bereich: 60 - 80 kg")
        fig_kg.update_yaxes(range=[60, 80])
        st.plotly_chart(fig_kg, use_container_width=True)

    # 2. KFA (Fester Bereich: 10 - 19)
    if "KFA" in filtered_df.columns:
        fig_kfa = px.line(filtered_df, x="Datum", y="KFA", title="Körperfettanteil KFA (%) – Bereich: 10 - 19 %")
        fig_kfa.update_yaxes(range=[10, 19])
        st.plotly_chart(fig_kfa, use_container_width=True)

    # 3. Skelettmuskulatur (Fester Bereich: 30 - 40)
    musk_col = next((col for col in ["Skel.Musk", "Skelettmuskulatur", "Muskeln"] if col in filtered_df.columns), None)
    if musk_col:
        fig_musk = px.line(filtered_df, x="Datum", y=musk_col, title=f"Skelettmuskulatur – Bereich: 30 - 40")
        fig_musk.update_yaxes(range=[30, 40])
        st.plotly_chart(fig_musk, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🥗 Ernährungs- & Aktivitäts-Balken (mit Ziellinie)")

    def create_bar_with_target(data, y_col, title, target_val):
        fig = px.bar(data, x="Datum", y=y_col, title=title)
        fig.add_hline(
            y=target_val, 
            line_dash="dash", 
            line_color="red", 
            annotation_text=f"Ziel: {target_val}", 
            annotation_position="top right"
        )
        st.plotly_chart(fig, use_container_width=True)

    if "Schritte" in filtered_df.columns:
        create_bar_with_target(filtered_df, "Schritte", "Schritte-Verlauf (Ziel: 10.000)", 10000)

    if "KCAL" in filtered_df.columns:
        create_bar_with_target(filtered_df, "KCAL", "Kalorien-Trend (Ziel: 2.150 kcal)", 2150)

    if "Prot" in filtered_df.columns:
        create_bar_with_target(filtered_df, "Prot", "Protein-Trend (Ziel: 140 g)", 140)

    st.markdown("---")
    st.markdown("### 📋 Vollständige Datentabelle (gefiltert)")
    st.dataframe(filtered_df)
