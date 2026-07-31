import streamlit as st
import pandas as pd
import os
from PIL import Image
from logic_gemini import analyze_waage, analyze_workout

def render_back_button():
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True):
        st.session_state["nav_tab"] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

def show_image_previews(files):
    if files:
        cols = st.columns(min(len(files), 4))
        for idx, file in enumerate(files):
            cols[idx % 4].image(Image.open(file), use_container_width=True)

def render_waage_page(api_key, save_callback):
    render_back_button()
    st.subheader("⚖️ Waagen-Messung")
    
    imgs_w = st.file_uploader("Foto(s) der Waage / App wählen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="w_img")
    show_image_previews(imgs_w)
    
    # Stabiler Button mit direktem Feedback
    if st.button("🤖 Waage analysieren", type="primary", key="btn_analyze_waage"):
        if imgs_w:
            with st.spinner("Analysiere Waagen-Bild mit Gemini..."):
                try:
                    pil_imgs = [Image.open(f) for f in imgs_w]
                    res = analyze_waage(api_key, pil_imgs)
                    
                    st.write("DEBUG ERGEBNIS:", res) # Zeigt dir sofort an, was zurückkommt
                    
                    st.session_state["waage_data"] = res
                    
                    if res.get("gewicht") is not None: 
                        st.session_state["saved_g"] = res["gewicht"]
                    if res.get("kfa") is not None: 
                        st.session_state["saved_k"] = res["kfa"]
                    if res.get("skelettmuskel") is not None: 
                        st.session_state["saved_m"] = res["skelettmuskel"]
                    
                    save_callback()
                    st.success("Waagendaten erfolgreich erkannt und übernommen!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler bei der Bildverarbeitung: {e}")
        else:
            st.warning("Bitte lade zuerst mindestens ein Bild der Waage hoch!")

    w_data = st.session_state.get("waage_data", {})
    with st.form("waage_form"):
        col1, col2, col3 = st.columns(3)
        
        def_g = w_data.get("gewicht") if w_data.get("gewicht") is not None else st.session_state.get("saved_g", 0.0)
        def_k = w_data.get("kfa") if w_data.get("kfa") is not None else st.session_state.get("saved_k", 0.0)
        def_m = w_data.get("skelettmuskel") if w_data.get("skelettmuskel") is not None else st.session_state.get("saved_m", 0.0)

        g = col1.number_input("Gewicht (kg)", value=float(def_g), step=0.1)
        k = col2.number_input("KFA (%)", value=float(def_k), step=0.1)
        m = col3.number_input("Skelettmuskel (%)", value=float(def_m), step=0.1)
        
        if st.form_submit_button("💾 Waagendaten merken"):
            st.session_state["saved_g"] = g
            st.session_state["saved_k"] = k
            st.session_state["saved_m"] = m
            save_callback()
            st.success("Waagendaten im Zwischenspeicher gesichert!")

def render_training_page(api_key, save_callback):
    render_back_button()
    st.subheader("🏋️‍♂️ Training & Aktivitäten erfassen")
    imgs_tr = st.file_uploader("Screenshots hochladen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="tr_imgs")
    show_image_previews(imgs_tr)
    
    txt_tr = st.text_input("Oder Training beschreiben", key="tr_txt")
    
    if st.button("🤖 Training analysieren", type="primary"):
        if imgs_tr or txt_tr:
            pil_imgs = [Image.open(f) for f in imgs_tr] if imgs_tr else []
            res_tr = analyze_workout(api_key, pil_imgs, txt_tr if txt_tr else "Kein Text angegeben")
            
            st.session_state["workout"]["schritte"] = int(res_tr.get("schritte") or st.session_state["workout"]["schritte"])
            st.session_state["workout"]["zirkel_min"] = int(res_tr.get("zirkel_min") or st.session_state["workout"]["zirkel_min"])
            st.session_state["workout"]["zirkel_details"] = res_tr.get("zirkel_details") or st.session_state["workout"]["zirkel_details"]
            st.session_state["workout"]["bike_km"] = float(res_tr.get("bike_km") or st.session_state["workout"]["bike_km"])
            st.session_state["workout"]["bike_modus"] = res_tr.get("bike_modus") or st.session_state["workout"]["bike_modus"]
            st.session_state["workout"]["sonstiges"] = res_tr.get("sonstiges") or st.session_state["workout"]["sonstiges"]
            st.session_state["workout"]["notiz"] = res_tr.get("workout_notiz", "")
            save_callback()
            st.success("Training erfolgreich analysiert!")
        else:
            st.warning("Bitte lade ein Bild hoch oder gib einen Text ein.")

    w = st.session_state["workout"]
    st.markdown("---")
    w["schritte"] = st.number_input("🚶 Schritte Anzahl", value=int(w["schritte"]), step=500)
    col_z1, col_z2 = st.columns([1, 2])
    w["zirkel_min"] = col_z1.number_input("⏱️ Zirkel (Min)", value=int(w["zirkel_min"]), step=5)
    w["zirkel_details"] = col_z2.text_input("Übungen / Wdh", value=w["zirkel_details"])
    col_b1, col_b2 = st.columns(2)
    w["bike_km"] = col_b1.number_input("🚴 Fahrrad (km)", value=float(w["bike_km"]), step=1.0)
    w["bike_modus"] = col_b2.text_input("E-Bike Modus", value=w["bike_modus"])
    w["sonstiges"] = st.text_input("🏊 Sonstiges", value=w["sonstiges"])
    save_callback()

def render_statistik_page(excel_file):
    render_back_button()
    st.subheader("📈 Historische Auswertungen, Wochen- & Monatsbilanz")
    
    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file)
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                if "Skel.Musk" in df.columns:
                    df.rename(columns={"Skel.Musk": "Skelettmuskel (%)"}, inplace=True)
                
                numeric_cols = ["KG", "KFA", "Skelettmuskel (%)", "KCAL", "Prot", "Schritte"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                date_col = None
                for c in df.columns:
                    if "datum" in c.lower() or "date" in c.lower():
                        date_col = c
                        break
                
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                    df = df.sort_values(by=date_col, ascending=False)
                    df["Monat-Jahr"] = df[date_col].dt.strftime("%Y-%m")
                    
                    st.markdown("### 📊 Aktuelle Bilanzen (Durchschnitte)")
                    recent_7 = df.head(7)
                    
                    avg_7_kcal = int(recent_7["KCAL"].mean()) if "KCAL" in recent_7.columns and not recent_7["KCAL"].dropna().empty else 0
                    avg_7_prot = int(recent_7["Prot"].mean()) if "Prot" in recent_7.columns and not recent_7["Prot"].dropna().empty else 0
                    avg_7_steps = int(recent_7["Schritte"].mean()) if "Schritte" in recent_7.columns and not recent_7["Schritte"].dropna().empty else 0
                    
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("Ø KCAL (Letzte 7 Tage)", f"{avg_7_kcal} kcal")
                    col_b2.metric("Ø Protein (Letzte 7 Tage)", f"{avg_7_prot} g")
                    col_b3.metric("Ø Schritte (Letzte 7 Tage)", f"{avg_7_steps}")
                    st.markdown("---")

                    verfuegbare_monate = sorted(df["Monat-Jahr"].dropna().unique(), reverse=True)
                    if verfuegbare_monate:
                        selected_month = st.selectbox(
                            "📅 Nach Monat für Diagramme filtern:", 
                            ["Alle Monate"] + list(verfuegbare_monate)
                        )
                        df_filtered = df[df["Monat-Jahr"] == selected_month] if selected_month != "Alle Monate" else df
                    else:
                        df_filtered = df
                else:
                    df_filtered = df

                st.success(f"📊 {len(df_filtered)} Datensätze in der Auswertung aktiv.")
                x_col = date_col if date_col else None

                st.markdown("### 🧬 Körperwerte (Body Recomp)")
                col_k1, col_k2, col_k3 = st.columns(3)
                with col_k1:
                    st.markdown("**Gewicht (KG)**")
                    if "KG" in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)["KG"] if x_col else df_filtered["KG"])
                with col_k2:
                    st.markdown("**KFA (%)**")
                    if "KFA" in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)["KFA"] if x_col else df_filtered["KFA"])
                with col_k3:
                    st.markdown("**Skelettmuskel (%)**")
                    if "Skelettmuskel (%)" in df_filtered.columns:
                        st.line_chart(df_filtered.set_index(x_col)["Skelettmuskel (%)"] if x_col else df_filtered["Skelettmuskel (%)"])

                st.markdown("---")
                st.markdown("### 🚶‍♂️ Schritte-Verlauf (Ziel: 10.000 Schritte)")
                if "Schritte" in df_filtered.columns:
                    chart_data = df_filtered[[date_col, "Schritte"]].copy() if date_col else pd.DataFrame({"Schritte": df_filtered["Schritte"]})
                    if date_col:
                        chart_data = chart_data.set_index(date_col)
                    chart_data["Ziel (10k)"] = 10000
                    st.line_chart(chart_data)

                st.markdown("---")
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    st.markdown("### 🥗 Kalorien-Trend (kcal)")
                    if "KCAL" in df_filtered.columns:
                        kc_data = df_filtered.set_index(date_col)[["KCAL"]].copy() if date_col else pd.DataFrame({"KCAL": df_filtered["KCAL"]})
                        kc_data["Ziel (2300 kcal)"] = 2300
                        st.line_chart(kc_data)
                with col_n2:
                    st.markdown("### 🥩 Protein-Trend (g)")
                    if "Prot" in df_filtered.columns:
                        pr_data = df_filtered.set_index(date_col)[["Prot"]].copy() if date_col else pd.DataFrame({"Prot": df_filtered["Prot"]})
                        pr_data["Ziel (145g)"] = 145
                        st.line_chart(pr_data)
            else:
                st.info("Deine Excel-Datei ist noch leer.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Excel: {e}")
    else:
        st.warning(f"Die Excel-Datei '{excel_file}' wurde nicht gefunden.")
