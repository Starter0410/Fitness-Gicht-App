import streamlit as st
import pandas as pd
from datetime import date

# Importiere deine Ansichten
from views_meals import render_meal_page, render_snacks_page, render_drinks_page
from views_training import render_waage_page, render_training_page, render_statistik_page
from logic_gemini import analyze_images_or_text

# Excel-Dateiname
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"

# -------------------------------------------------------------------------
# SESSION STATE INITIALISIERUNG
# -------------------------------------------------------------------------
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "🏠 Startseite"

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

if "meals" not in st.session_state:
    st.session_state["meals"] = {
        "fruehstueck": [],
        "mittagessen": [],
        "abendessen": [],
        "snacks": []
    }

if "drinks" not in st.session_state:
    st.session_state["drinks"] = {
        "wasser_soda": 3.0,
        "kaffee": 3,
        "whey_scoops": 1,
        "redbull": 0,
        "sonstiges_txt": "",
        "sonstiges_kcal": 0,
        "sonstiges_prot": 0
    }

if "daily_meta" not in st.session_state:
    st.session_state["daily_meta"] = {
        "gewicht": 69.7,
        "kfa": 13.4,
        "skel_musk": 34.3,
        "schritte": 8000,
        "notizen": ""
    }

if "workout" not in st.session_state:
    st.session_state["workout"] = {
        "schritte": 8000,
        "zirkel_min": 0,
        "zirkel_details": "",
        "bike_km": 0.0,
        "bike_modus": "",
        "sonstiges": "",
        "notiz": ""
    }

# -------------------------------------------------------------------------
# HILFSFUNKTIONEN
# -------------------------------------------------------------------------
def get_worst_gicht_status(items):
    """
    Ermittelt den schlechtesten Gicht-Status aus einer Liste von Items.
    Priorität: Rot (3) > Gelb (2) > Grün (1)
    """
    if not items:
        return "Grün"
    
    rank = {"grün": 1, "gelb": 2, "rot": 3}
    worst_score = 1
    worst_word = "Grün"
    
    for item in items:
        status = str(item.get('gicht_status', 'Grün')).strip().lower()
        current_score = rank.get(status, 1)
        
        if current_score > worst_score:
            worst_score = current_score
            worst_word = status.capitalize()
            
    return worst_word

def generate_summary_string():
    """Generiert den zusammenfassenden Text aller Mahlzeiten inkl. Notizen & Gicht-Status für den Export."""
    m = st.session_state["meals"]
    parts = []
    
    for cat_label, cat_key in [("Frühstück", "fruehstueck"), ("Mittag", "mittagessen"), ("Abend", "abendessen"), ("Snacks", "snacks")]:
        items = m.get(cat_key, [])
        if items:
            worst_status = get_worst_gicht_status(items)
            item_strs = []
            for itm in items:
                status = itm.get('gicht_status', 'Grün')
                txt = f"{itm['desc']} ({itm['kcal']} kcal, {itm['prot']}g, Gicht: {status})"
                if itm.get('notiz'):
                    txt += f" [Notiz: {itm['notiz']}]"
                item_strs.append(txt)
            parts.append(f"{cat_label} [Gesamt-Gicht: {worst_status}]: {'; '.join(item_strs)}")
            
    return " | ".join(parts) if parts else "Keine Mahlzeiten erfasst"

def save_current_day_to_excel():
    """Schreibt den aktuellen Tag fehlerfrei in die Excel-Datei."""
    totals_kcal, totals_prot = get_todays_totals()
    meta = st.session_state["daily_meta"]
    
    summary_text = generate_summary_string()
    if meta.get("notizen"):
        all_desc = f"{summary_text} | Tagesnotiz: {meta['notizen']}"
    else:
        all_desc = summary_text

    new_row = {
        "Datum": str(date.today()),
        "KG": meta["gewicht"],
        "KFA": meta["kfa"],
        "Skel.Musk": meta["skel_musk"],
        "Schritte": meta["schritte"],
        "KCAL": totals_kcal,
        "Prot": totals_prot,
        "Notizen": all_desc
    }

    try:
        df = pd.read_excel(EXCEL_FILE)
        if not df.empty and "Datum" in df.columns:
            df = df[df["Datum"] != str(date.today())]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([new_row])

    df.to_excel(EXCEL_FILE, index=False)

def get_todays_totals():
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    
    fruehstueck_kcal = sum([item["kcal"] for item in m.get("fruehstueck", [])])
    fruehstueck_prot = sum([item["prot"] for item in m.get("fruehstueck", [])])
    
    mittag_kcal = sum([item["kcal"] for item in m.get("mittagessen", [])])
    mittag_prot = sum([item["prot"] for item in m.get("mittagessen", [])])
    
    abend_kcal = sum([item["kcal"] for item in m.get("abendessen", [])])
    abend_prot = sum([item["prot"] for item in m.get("abendessen", [])])
    
    snack_kcal = sum([s["kcal"] for s in m.get("snacks", [])])
    snack_prot = sum([s["prot"] for s in m.get("snacks", [])])
    
    whey_kcal = d["whey_scoops"] * 120
    whey_prot = d["whey_scoops"] * 30
    total_drink_kcal = whey_kcal + d["sonstiges_kcal"]
    total_drink_prot = whey_prot + d["sonstiges_prot"]
    
    total_kcal = fruehstueck_kcal + mittag_kcal + abend_kcal + snack_kcal + total_drink_kcal
    total_prot = fruehstueck_prot + mittag_prot + abend_prot + snack_prot + total_drink_prot
    return total_kcal, total_prot

# -------------------------------------------------------------------------
# HAUPTSEITE & NAVIGATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered")

with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input("Gemini API Key", value=st.session_state["api_key"], type="password")
    st.markdown("---")
    if st.button("🔄 App Daten zurücksetzen"):
        st.session_state.clear()
        st.rerun()

tab = st.session_state["nav_tab"]

if tab != "🏠 Startseite":
    if st.button("⬅️ Zurück zur Startseite", use_container_width=True, key="global_back_btn"):
        st.session_state["nav_tab"] = "🏠 Startseite"
        st.rerun()
    st.markdown("---")

if tab == "🏠 Startseite":
    _, col_logo, _ = st.columns([3, 1, 3])
    with col_logo:
        st.markdown("# 🏋️‍♂️")
        
    st.title("Gicht & Body-Recomposition Tracker")
    st.markdown("<p style='text-align: center; color: gray;'>the best version of me @ starter</p>", unsafe_allow_html=True)
    
    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
    
    total_kcal, total_prot = get_todays_totals()
    
    col1, col2 = st.columns(2)
    col1.metric("Heutige Kalorien", f"{total_kcal} kcal")
    col2.metric("Heutiges Protein", f"{total_prot} g")
    
    st.markdown("---")
    st.subheader("⚡ Macro & Target Status")
    
    target_kcal = 2150
    target_prot = 140
    
    kcal_progress = min(total_kcal / target_kcal, 1.0)
    prot_progress = min(total_prot / target_prot, 1.0)
    
    st.write(f"Kalorien-Ziel ({total_kcal} / {target_kcal} kcal)")
    st.progress(kcal_progress)
    
    st.write(f"Protein-Ziel ({total_prot} / {target_prot} g)")
    st.progress(prot_progress)
    
    st.markdown("---")
    st.subheader("📌 Menü")
    
    if st.button("⚖️ Waagen-Analyse (Foto)", use_container_width=True):
        st.session_state["nav_tab"] = "Waage"
        st.rerun()
    if st.button("🍳 Frühstück erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Frühstück"
        st.rerun()
    if st.button("🥗 Mittagessen erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Mittagessen"
        st.rerun()
    if st.button("🍲 Abendessen erfassen", use_container_width=True):
        st.session_state["nav_tab"] = "Abendessen"
        st.rerun()
    if st.button("🍏 Snacks & Zwischenmahlzeiten", use_container_width=True):
        st.session_state["nav_tab"] = "Snacks"
        st.rerun()
    if st.button("🥤 Getränke-Zähler", use_container_width=True):
        st.session_state["nav_tab"] = "Getränke"
        st.rerun()
    if st.button("🏋️‍♂️ Training & Aktivitäten", use_container_width=True):
        st.session_state["nav_tab"] = "Training"
        st.rerun()
    if st.button("📊 Statistiken & Tabellen", use_container_width=True):
        st.session_state["nav_tab"] = "Statistiken"
        st.rerun()
    if st.button("🏁 Tagesabschluss & Endkontrolle", use_container_width=True):
        st.session_state["nav_tab"] = "Abschluss"
        st.rerun()

elif tab == "Frühstück":
    render_meal_page("Frühstück", "fruehstueck", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Mittagessen":
    render_meal_page("Mittagessen", "mittagessen", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Abendessen":
    render_meal_page("Abendessen", "abendessen", st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Snacks":
    render_snacks_page(st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Getränke":
    render_drinks_page(save_current_day_to_excel)

elif tab == "Waage":
    render_waage_page(st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Training":
    render_training_page(st.session_state["api_key"], save_current_day_to_excel)

elif tab == "Statistiken":
    render_statistik_page(EXCEL_FILE)

elif tab == "Abschluss":
    st.subheader("🔍 Tagesabschluss & Kontrollansicht")
    
    total_kcal, total_prot = get_todays_totals()
    
    # Erweiterte Kontrollbox mit Notizen und Gicht-Status pro Mahlzeit inklusive Worst-Case-Ermittlung
    with st.expander("👀 Übersicht der erfassten Mahlzeiten, Notizen & Gicht-Status (Kontrolle)", expanded=True):
        m = st.session_state["meals"]
        d = st.session_state["drinks"]
        
        st.markdown(f"**Gesamtbilanz:** 🔥 {total_kcal} kcal | 🥩 {total_prot} g Protein")
        st.markdown("---")
        
        for cat_label, cat_key in [("🍳 Frühstück", "fruehstueck"), ("🥗 Mittagessen", "mittagessen"), ("🍲 Abendessen", "abendessen"), ("🍏 Snacks", "snacks")]:
            items = m.get(cat_key, [])
            if items:
                worst = get_worst_gicht_status(items)
                st.markdown(f"**{cat_label}** *(Kategorie-Gichtstatus: **{worst}**)*:")
                for itm in items:
                    gicht = itm.get('gicht_status', 'Grün')
                    st.markdown(f"- **{itm['desc']}** ({itm['kcal']} kcal, {itm['prot']}g Protein) | *Gicht: **{gicht}***")
                    if itm.get('notiz'):
                        st.caption(f"  📝 Notiz: {itm['notiz']}")
            else:
                st.markdown(f"**{cat_label}:** *Keine Einträge*")
        
        st.markdown("---")
        st.markdown(f"**🥤 Getränke:** Wasser/Soda: {d['wasser_soda']}L | Kaffee: {d['kaffee']} Tassen | Whey: {d['whey_scoops']} Scoops | Energy: {d['redbull']} Dosen")
        if d['sonstiges_txt']:
            st.markdown(f"*Sonstiges:* {d['sonstiges_txt']} ({d['sonstiges_kcal']} kcal, {d['sonstiges_prot']}g Protein)")

    st.markdown("---")
    
    meta = st.session_state["daily_meta"]
    meta["gewicht"] = st.number_input("Heutiges Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1)
    meta["kfa"] = st.number_input("Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1)
    meta["skel_musk"] = st.number_input("Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1)
    meta["schritte"] = st.number_input("Heutige Schritte", value=int(meta["schritte"]), step=500)
    
    if st.button("✨ Tagesnotiz aus Mahlzeiten generieren"):
        meta["notizen"] = generate_summary_string()
        st.success("Tagesnotiz erfolgreich aus den Mahlzeiten generiert!")
        st.rerun()

    meta["notizen"] = st.text_area("Tagesnotizen / Befinden (wird in Excel gespeichert)", value=meta["notizen"])
    
    st.info(f"**Bisherige Tagesbilanz:** {total_kcal} kcal | {total_prot} g Protein")
    
    if st.button("🚀 In Excel speichern & Download vorbereiten", type="primary"):
        save_current_day_to_excel()
        st.success("Tagesdaten erfolgreich in die Excel-Tabelle geschrieben!")
        
        with open(EXCEL_FILE, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label="📥 Excel-Datei herunterladen",
            data=excel_bytes,
            file_name=EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
