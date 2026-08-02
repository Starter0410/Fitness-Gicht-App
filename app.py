import streamlit as st
import pandas as pd
import os
from datetime import date

# Seitenkonfiguration
st.set_page_config(page_title="Project ZEAL", page_icon="⚡", layout="wide")

EXCEL_FILE = "Gichttagebuch_Finale_Sicherung_python.xlsx"  # Passe den Dateinamen an falls nötig

def render_statistik_page_clean(excel_file):
    st.subheader("📊 Statistiken & Historie")
    if not os.path.exists(excel_file):
        st.info("Noch keine Excel-Datei vorhanden. Erfasse zuerst Daten.")
        return

    try:
        df = pd.read_excel(excel_file)
        if df.empty:
            st.info("Die Excel-Datei ist leer.")
            return

        # 1. Datum sauber als datetime parsen für korrekte chronologische Sortierung
        if "Datum" in df.columns:
            df["Datum_dt"] = pd.to_datetime(df["Datum"], errors="coerce")
            df = df.sort_values("Datum_dt", ascending=True)
            df["Datum"] = df["Datum_dt"].dt.strftime("%Y-%m-%d")
            df = df.drop(columns=["Datum_dt"])

        df = df.fillna("")

        # 2. Intelligentes Filtern für die Tabelle (Heutiger Tag bleibt, Platzhalter raus)
        today_str = str(date.today())
        
        if "KCAL" in df.columns and "Datum" in df.columns:
            is_today = (df["Datum"] == today_str)
            has_content = (
                ((df["KCAL"] != 0) & (df["KCAL"] != "") & (df["KCAL"] != -2200)) | 
                ((df["KG"] != 0) & (df["KG"] != ""))
            )
            df_filtered = df[is_today | has_content]
        else:
            df_filtered = df

        # 3. Diagramme aufbereiten (Numerische Typen erzwingen & als Zeitreihe indexieren)
        if "Datum" in df.columns:
            chart_df = df.copy()
            chart_df["Datum"] = pd.to_datetime(chart_df["Datum"], errors="coerce")
            chart_df = chart_df.sort_values("Datum").set_index("Datum")

            col_ch1, col_ch2 = st.columns(2)
            
            with col_ch1:
                if "KG" in chart_df.columns:
                    st.markdown("### ⚖️ Gewichtsentwicklung")
                    weight_data = pd.to_numeric(chart_df["KG"], errors="coerce").replace(0, pd.NA).dropna()
                    if not weight_data.empty:
                        st.line_chart(weight_data)
                    else:
                        st.info("Keine Gewichtsdaten vorhanden.")
                        
            with col_ch2:
                if "KCAL" in chart_df.columns:
                    st.markdown("### 🔥 Kalorienverlauf")
                    kcal_data = pd.to_numeric(chart_df["KCAL"], errors="coerce")
                    kcal_data = kcal_data.replace(0, pd.NA)
                    kcal_data = kcal_data[kcal_data != -2200].dropna()
                    if not kcal_data.empty:
                        st.line_chart(kcal_data)
                    else:
                        st.info("Keine Kaloriendaten vorhanden.")

            # Zusätzliche alte Statistiken / Metriken (z.B. KFA & Protein)
            col_ch3, col_ch4 = st.columns(2)
            with col_ch3:
                if "KFA" in chart_df.columns:
                    st.markdown("### 📉 Körperfettanteil (KFA)")
                    kfa_data = pd.to_numeric(chart_df["KFA"], errors="coerce").replace(0, pd.NA).dropna()
                    if not kfa_data.empty:
                        st.line_chart(kfa_data)
            with col_ch4:
                if "Prot" in chart_df.columns:
                    st.markdown("### 🥩 Proteinverlauf (g)")
                    prot_data = pd.to_numeric(chart_df["Prot"], errors="coerce").replace(0, pd.NA).dropna()
                    if not prot_data.empty:
                        st.line_chart(prot_data)

        st.markdown("---")
        st.markdown("### 📋 Vollständige Datentabelle (chronologisch sortiert & gefiltert)")
        
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        st.error(f"Fehler beim Laden der Statistiken: {e}")

# Haupt-App Struktur (Navigation / Seitenaufruf)
def main():
    st.title("⚡ Project ZEAL - Dashboard")
    
    # Sidebar für Navigation
    page = st.sidebar.selectbox("Navigation", ["Statistiken & Historie", "Dateneingabe"])
    
    if page == "Statistiken & Historie":
        render_statistik_page_clean(EXCEL_FILE)
    elif page == "Dateneingabe":
        st.subheader("📝 Dateneingabe")
        st.info("Hier kannst du deine täglichen Werte erfassen.")
        # Platzhalter für deine Erfassungsmaske falls gewünscht

if __name__ == "__main__":
    main()
