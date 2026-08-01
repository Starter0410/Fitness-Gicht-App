import streamlit as st
import pandas as pd
from datetime import date

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

def generate_summary_string():
    m = st.session_state["meals"]
    w = st.session_state["workout"]
    meta = st.session_state["daily_meta"]
    
    total_kcal, total_prot = get_todays_totals()
    target_kcal = 2150
    target_prot = 140
    
    all_statuses = []
    for cat_key in ["fruehstueck", "mittagessen", "abendessen", "snacks"]:
        items = m.get(cat_key, [])
        if items:
            all_statuses.append(get_worst_gicht_status(items))
            
    if "Rot" in all_statuses:
        gicht_part = "heute war gicht-technisch leider etwas Vorsicht geboten wegen purinreicherer Kost,"
    elif "Gelb" in all_statuses:
        gicht_part = "bei der Gicht hatten wir heute ein solides Mittelfeld,"
    elif all_statuses:
        gicht_part = "gicht-technisch war das heute absolut vorbildlich im grünen Bereich,"
    else:
        gicht_part = "gicht-technisch gab es heute noch keine großen Einträge,"

    kcal_diff = total_kcal - target_kcal
    if abs(kcal_diff) <= 150:
        kcal_part = f"beim Kalorienziel hast du mit {total_kcal} von {target_kcal} kcal eine Punktlandung für die Recomp hingelegt"
    elif kcal_diff < 0:
        kcal_part = f"du hast mit {total_kcal} kcal ein sauberes Defizit für den Fettabbau erreicht"
    else:
        kcal_part = f"du warst mit {total_kcal} kcal heute im leichten Überschuss für den Muskelaufbau"

    if total_prot >= target_prot:
        prot_part = f"und dein Proteinziel mit starken {total_prot}g komplett geknackt!"
    else:
        prot_part = f"wobei du bei bisher {total_prot}g Protein das Ziel von {target_prot}g noch etwas nach oben schrauben darfst."

    training_active = (w.get("zirkel_min", 0) > 0) or (w.get("bike_km", 0.0) > 0) or bool(w.get("sonstiges"))
    steps = meta.get("schritte", 0)
    
    if training_active and steps >= 8000:
        move_part = f"Dazu hast du mit starkem Training und {steps} Schritten richtig abgeliefert – weiter so, du bist auf dem perfekten Weg!"
    elif training_active:
        move_part = f"Das Training hast du durchgezogen, und mit {steps} Schritten war das eine runde Sache."
    elif steps >= 10000:
        move_part = f"Auch ohne formelles Zusatztraining hast du dich mit {steps} Schritten extrem gut bewegt – echter Maschinen-Modus!"
    elif steps >= 7500:
        move_part = f"Mit solider Bewegung von {steps} Schritten hast du deinen Alltag gut aktiv gehalten."
    else:
        move_part = f"Mit {steps} Schritten war es heute etwas ruhiger – aber morgen ist ein neuer Tag, um wieder voll anzugreifen!"

    return f"Heute war ein Tag, an dem {gicht_part} {kcal_part} {prot_part} {move_part}"

def format_meal_column(items):
    if not items:
        return ""
    return "; ".join([f"{item['desc']} ({item['kcal']} kcal, {item['prot']}g)" for item in items])

def format_meal_note(items):
    if not items:
        return ""
    notes = [item.get('notiz', '') for item in items if item.get('notiz')]
    return " | ".join(notes) if notes else ""

def clear_todays_data():
    """Setzt alle Daten und Widget-Werte im Session State sauber zurück."""
    st.session_state["meals"] = {"fruehstueck": [], "mittagessen": [], "abendessen": [], "snacks": []}
    st.session_state["drinks"] = {"wasser_soda": 3.0, "kaffee": 3, "whey_scoops": 1, "redbull": 0, "sonstiges_txt": "", "sonstiges_kcal": 0, "sonstiges_prot": 0}
    st.session_state["workout"] = {"schritte": 8000, "zirkel_min": 0, "zirkel_details": "", "bike_km": 0.0, "bike_modus": "", "sonstiges": "", "notiz": ""}
    st.session_state["daily_meta"] = {"gewicht": 69.7, "kfa": 13.4, "skel_musk": 34.3, "schritte": 8000, "notizen": ""}
    
    # Alle Widget-Keys, die in den Eingabefeldern genutzt werden, explizit auf Standardwerte setzen
    for key in list(st.session_state.keys()):
        if key not in ["nav_tab", "api_key"]:
            del st.session_state[key]

def save_current_day_to_excel():
    m = st.session_state["meals"]
    d = st.session_state["drinks"]
    w = st.session_state["workout"]
    meta = st.session_state["daily_meta"]
    
    totals_kcal, totals_prot = get_todays_totals()
    target_kcal = 2150
    defizit_ueberschuss = totals_kcal - target_kcal
    
    if not meta.get("notizen"):
        meta["notizen"] = generate_summary_string()

    all_cat_items = m.get("fruehstueck", []) + m.get("mittagessen", []) + m.get("abendessen", []) + m.get("snacks", [])
    overall_gicht = get_worst_gicht_status(all_cat_items)

    new_row = {
        "Datum": str(date.today()),
        "KG": meta["gewicht"],
        "KFA": f"{meta['kfa']}%" if isinstance(meta['kfa'], (int, float)) else meta["kfa"],
        "Skel.Musk": meta["skel_musk"],
        "KCAL": totals_kcal,
        "Prot": totals_prot,
        "Defizit/Überschuss": defizit_ueberschuss,
        
        "Frühstück": format_meal_column(m.get("fruehstueck", [])),
        "Frühstück-Ampel": get_worst_gicht_status(m.get("fruehstueck", [])),
        "Frühstück-Notiz": format_meal_note(m.get("fruehstueck", [])),
        
        "Mittagessen": format_meal_column(m.get("mittagessen", [])),
        "Mittagessen-Ampel": get_worst_gicht_status(m.get("mittagessen", [])),
        "Mittagessen-Notiz": format_meal_note(m.get("mittagessen", [])),
        
        "Abendessen": format_meal_column(m.get("abendessen", [])),
        "Abendessen-Ampel": get_worst_gicht_status(m.get("abendessen", [])),
        "Abendessen-Notiz": format_meal_note(m.get("abendessen", [])),
        
        "Snacks": format_meal_column(m.get("snacks", [])),
        "Snack-Ampel": get_worst_gicht_status(m.get("snacks", [])),
        "Snacks-Notiz": format_meal_note(m.get("snacks", [])),
        
        "Wasser/Soda/Zitrone": d["wasser_soda"],
        "Red-": d["redbull"],
        "Kaffe": d["kaffee"],
        "Whey": d["whey_scoops"],
        "Getränke-Sonstige": d["sonstiges_txt"],
        
        "Schritte": meta["schritte"],
        "Training": w.get("zirkel_min", 0),
        "Fahrrad (km)": w.get("bike_km", 0.0),
        "Training-Sonstiges": w.get("sonstiges", ""),
        "Notiz11 Training": w.get("notiz", ""),
        
        "Notiz12 Tageszusammenfassung": meta["notizen"],
        "Gicht Status": overall_gicht
    }

    try:
        df = pd.read_excel(EXCEL_FILE)
        if not df.empty and "Datum" in df.columns:
            df = df[df["Datum"] != str(date.today())]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([new_row])

    df.to_excel(EXCEL_FILE, index=False)

# -------------------------------------------------------------------------
# HAUPTSEITE & NAVIGATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered")

with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input("Gemini API Key", value=st.session_state["api_key"], type="password")
    st.markdown("---")
    if st.button("🧹 Heutigen Tag zurücksetzen (Clear All)", type="secondary"):
        clear_todays_data()
        st.success("Alle heutigen Einträge gelöscht!")
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
    st.subheader("📌 Menü")
    
    if st.button("🥤 Getränke-Zähler", use_container_width=True):
        st.session_state["nav_tab"] = "Getränke"
        st.rerun()
    if st.button("🏁 Tagesabschluss & Endkontrolle", use_container_width=True):
        st.session_state["nav_tab"] = "Abschluss"
        st.rerun()

elif tab == "Getränke":
    st.subheader("🥤 Getränke & Flüssigkeit")
    d = st.session_state["drinks"]
    
    d["wasser_soda"] = st.slider("Wasser / Soda / Zitrone (Liter)", 0.0, 6.0, float(d["wasser_soda"]), 0.5, key="w_soda")
    d["kaffee"] = st.number_input("Kaffee (Tassen)", 0, 10, int(d["kaffee"]), key="w_kaffee")
    d["whey_scoops"] = st.number_input("Whey (Scoops)", 0, 5, int(d["whey_scoops"]), key="w_whey")
    d["redbull"] = st.number_input("Red Bull (Dosen)", 0, 5, int(d["redbull"]), key="w_redbull")
    
    if st.button("💾 Getränke speichern"):
        st.success("Gespeichert!")

elif tab == "Abschluss":
    st.subheader("🔍 Tagesabschluss & Kontrollansicht")
    total_kcal, total_prot = get_todays_totals()
    
    meta = st.session_state["daily_meta"]
    meta["gewicht"] = st.number_input("Heutiges Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1, key="m_gew")
    meta["kfa"] = st.number_input("Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1, key="m_kfa")
    meta["skel_musk"] = st.number_input("Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1, key="m_skel")
    meta["schritte"] = st.number_input("Heutige Schritte", value=int(meta["schritte"]), step=500, key="m_schr")
    
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
