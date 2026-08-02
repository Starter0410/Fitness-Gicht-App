import datetime
import json
import os
from datetime import date
import pandas as pd
import streamlit as st

# Importiere deine Ansichten & Logik
from views_meals import (
    render_meal_page,
    render_snacks_page,
    render_drinks_page,
    render_preset_creator_page,
)
from views_training import (
    render_waage_page,
    render_training_page,
    render_statistik_page,
)
from logic_gemini import analyze_images_or_text

# Excel-Dateiname & Cache-Datei
EXCEL_FILE = "Gicht_Fitnees_APP.xlsx"
CACHE_FILE = "daily_cache.json"

# -------------------------------------------------------------------------
# SEITENKONFIGURATION (Muss als Erstes stehen!)
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Gicht & Fitness Tracker", page_icon="🏋️‍♂️", layout="centered"
)

# -------------------------------------------------------------------------
# AUTOMATISCHES ZWISCHENSPEICHERN & LADEN (JSON CACHE)
# -------------------------------------------------------------------------
today_str = datetime.date.today().isoformat()


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == today_str:
                    return data.get("state", {})
        except Exception:
            pass
    return None


def save_cache():
    if "meals" in st.session_state:
        state_to_save = {
            "date": today_str,
            "meals": st.session_state.get("meals", {}),
            "drinks": st.session_state.get("drinks", {}),
            "workout": st.session_state.get("workout", {}),
            "daily_meta": st.session_state.get("daily_meta", {}),
        }
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=4)
        except Exception:
            pass


# Cache vor der Initialisierung laden
cached_state = load_cache()

# -------------------------------------------------------------------------
# SESSION STATE INITIALISIERUNG (Mit sicherem Fallback auf Cache)
# -------------------------------------------------------------------------
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "🏠 Startseite"

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

# 1. Meals
if "meals" not in st.session_state:
    if cached_state and cached_state.get("meals"):
        st.session_state["meals"] = cached_state["meals"]
    else:
        st.session_state["meals"] = {
            "fruehstueck": [],
            "mittagessen": [],
            "abendessen": [],
            "snacks": [],
        }

# 2. Drinks
if "drinks" not in st.session_state:
    if cached_state and cached_state.get("drinks"):
        st.session_state["drinks"] = cached_state["drinks"]
    else:
        st.session_state["drinks"] = {
            "wasser_soda": 0,
            "kaffee": 0,
            "whey_scoops": 0,
            "redbull": 0,
            "sonstiges_txt": "",
            "sonstiges_kcal": 0,
            "sonstiges_prot": 0,
        }

# 3. Daily Meta
if "daily_meta" not in st.session_state:
    if cached_state and cached_state.get("daily_meta"):
        st.session_state["daily_meta"] = cached_state["daily_meta"]
    else:
        st.session_state["daily_meta"] = {
            "gewicht": 0.0,
            "kfa": 0.0,
            "skel_musk": 0.0,
            "schritte": 0,
            "notizen": "",
        }

# 4. Workout
if "workout" not in st.session_state:
    if cached_state and cached_state.get("workout"):
        st.session_state["workout"] = cached_state["workout"]
    else:
        st.session_state["workout"] = {
            "schritte": 8000,
            "zirkel_min": 0,
            "zirkel_details": "",
            "bike_km": 0.0,
            "bike_modus": "",
            "sonstiges": "",
            "notiz": "",
        }

# Sofort nach dem Laden einmal absichern
save_cache()

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
        status = str(item.get("gicht_status", "Grün")).strip().lower()
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

    if not isinstance(d, dict):
        d = {
            "wasser_soda": 0,
            "kaffee": 0,
            "whey_scoops": 0,
            "redbull": 0,
            "sonstiges_txt": "",
            "sonstiges_kcal": 0,
            "sonstiges_prot": 0,
        }
        st.session_state["drinks"] = d

    whey_kcal = d.get("whey_scoops", 0) * 120
    whey_prot = d.get("whey_scoops", 0) * 30
    total_drink_kcal = whey_kcal + d.get("sonstiges_kcal", 0)
    total_drink_prot = whey_prot + d.get("sonstiges_prot", 0)

    total_kcal = (
        fruehstueck_kcal
        + mittag_kcal
        + abend_kcal
        + snack_kcal
        + total_drink_kcal
    )
    total_prot = (
        fruehstueck_prot
        + mittag_prot
        + abend_prot
        + snack_prot
        + total_drink_prot
    )
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
        gicht_part = (
            "heute war gicht-technisch leider etwas Vorsicht geboten wegen"
            " purinreicherer Kost,"
        )
    elif "Gelb" in all_statuses:
        gicht_part = "bei der Gicht hatten wir heute ein solides Mittelfeld,"
    elif all_statuses:
        gicht_part = (
            "gicht-technisch war das heute absolut vorbildlich im grünen"
            " Bereich,"
        )
    else:
        gicht_part = (
            "gicht-technisch gab es heute noch keine großen Einträge,"
        )

    kcal_diff = total_kcal - target_kcal
    if abs(kcal_diff) <= 150:
        kcal_part = (
            f"beim Kalorienziel hast du mit {total_kcal} von {target_kcal} kcal"
            " eine Punktlandung für die Recomp hingelegt"
        )
    elif kcal_diff < 0:
        kcal_part = (
            f"du hast mit {total_kcal} kcal ein sauberes Defizit für den"
            " Fettabbau erreicht"
        )
    else:
        kcal_part = (
            f"du warst mit {total_kcal} kcal heute im leichten Überschuss für"
            " den Muskelaufbau"
        )

    if total_prot >= target_prot:
        prot_part = (
            f"und dein Proteinziel mit starken {total_prot}g komplett geknackt!"
        )
    else:
        prot_part = (
            f"wobei du bei bisher {total_prot}g Protein das Ziel von"
            f" {target_prot}g noch etwas nach oben schrauben darfst."
        )

    training_active = (
        (w.get("zirkel_min", 0) > 0)
        or (w.get("bike_km", 0.0) > 0)
        or bool(w.get("sonstiges"))
    )
    steps = meta.get("schritte", 0)

    if training_active and steps >= 8000:
        move_part = (
            f"Dazu hast du mit starkem Training und {steps} Schritten richtig"
            " abgeliefert – weiter so, du bist auf dem perfekten Weg!"
        )
    elif training_active:
        move_part = (
            f"Das Training hast du durchgezogen, und mit {steps} Schritten war"
            " das eine runde Sache."
        )
    elif steps >= 10000:
        move_part = (
            f"Auch ohne formelles Zusatztraining hast du dich mit {steps}"
            " Schritten extrem gut bewegt – echter Maschinen-Modus!"
        )
    elif steps >= 7500:
        move_part = (
            f"Mit solider Bewegung von {steps} Schritten hast du deinen Alltag"
            " gut aktiv gehalten."
        )
    else:
        move_part = (
            f"Mit {steps} Schritten war es heute etwas ruhiger – aber morgen"
            " ist ein neuer Tag, um wieder voll anzugreifen!"
        )

    return f"Heute war ein Tag, an dem {gicht_part} {kcal_part} {prot_part} {move_part}"


def format_meal_column(items):
    if not items:
        return ""
    return "; ".join(
        [
            f"{item['desc']} ({item['kcal']} kcal, {item['prot']}g)"
            for item in items
        ]
    )


def format_meal_note(items):
    if not items:
        return ""
    notes = [item.get("notiz", "") for item in items if item.get("notiz")]
    return " | ".join(notes) if notes else ""


def clear_todays_data():
    st.session_state["meals"] = {
        "fruehstueck": [],
        "mittagessen": [],
        "abendessen": [],
        "snacks": [],
    }
    st.session_state["drinks"] = {
        "wasser_soda": 0,
        "kaffee": 0,
        "whey_scoops": 0,
        "redbull": 0,
        "sonstiges_txt": "",
        "sonstiges_kcal": 0,
        "sonstiges_prot": 0,
    }
    st.session_state["workout"] = {
        "schritte": 8000,
        "zirkel_min": 0,
        "zirkel_details": "",
        "bike_km": 0.0,
        "bike_modus": "",
        "sonstiges": "",
        "notiz": "",
    }
    st.session_state["daily_meta"] = {
        "gewicht": 0.0,
        "kfa": 0.0,
        "skel_musk": 0.0,
        "schritte": 0,
        "notizen": "",
    }
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
    save_cache()


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

    all_cat_items = (
        m.get("fruehstueck", [])
        + m.get("mittagessen", [])
        + m.get("abendessen", [])
        + m.get("snacks", [])
    )
    overall_gicht = get_worst_gicht_status(all_cat_items)

    new_row = {
        "Datum": str(date.today()),
        "KG": meta["gewicht"],
        "KFA": f"{meta['kfa']}%"
        if isinstance(meta["kfa"], (int, float))
        else meta["kfa"],
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
        "Wasser/Soda/Zitrone": d.get("wasser_soda", 0),
        "Red-": d.get("redbull", 0),
        "Kaffe": d.get("kaffee", 0),
        "Whey": d.get("whey_scoops", 0),
        "Getränke-Sonstige": d.get("sonstiges_txt", ""),
        "Schritte": meta["schritte"],
        "Training": w.get("zirkel_min", 0),
        "Fahrrad (km)": w.get("bike_km", 0.0),
        "Training-Sonstiges": w.get("sonstiges", ""),
        "Notiz11 Training": w.get("notiz", ""),
        "Notiz12 Tageszusammenfassung": meta["notizen"],
        "Gicht Status": overall_gicht,
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
with st.sidebar:
    st.subheader("⚙️ Konfiguration")
    st.session_state["api_key"] = st.text_input(
        "Gemini API Key", value=st.session_state["api_key"], type="password"
    )
    st.markdown("---")
    if st.button("🧹 Heutigen Tag zurücksetzen (Clear All)", type="secondary"):
        clear_todays_data()
        st.success("Heutige Einträge gelöscht!")
        st.rerun()
    st.markdown("---")
    if st.button("🔄 App Daten komplett zurücksetzen"):
        st.session_state.clear()
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        st.rerun()

tabs_mapping = {
    "🏠 Startseite": "Startseite",
    "⚖️ Waagen-Analyse (Foto)": "Waage",
    "📝 Mahlzeiten-Vorlagen": "Vorlagen",
    "🍳 Frühstück": "Frühstück",
    "🥗 Mittagessen": "Mittagessen",
    "🍲 Abendessen": "Abendessen",
    "🍏 Snacks": "Snacks",
    "🥤 Getränke": "Getränke",
    "🏋️‍♂️ Training": "Training",
    "🏁 Tagesabschluss": "Abschluss",
    "📊 Statistiken": "Statistiken",
}

with st.sidebar:
    st.markdown("---")
    st.subheader("📌 Navigation")
    selected_menu = st.radio(
        "Menü auswählen",
        list(tabs_mapping.keys()),
        index=list(tabs_mapping.values()).index(st.session_state["nav_tab"])
        if st.session_state["nav_tab"] in tabs_mapping.values()
        else 0,
    )
    if tabs_mapping[selected_menu] != st.session_state["nav_tab"]:
        st.session_state["nav_tab"] = tabs_mapping[selected_menu]
        st.rerun()

tab = st.session_state["nav_tab"]

if tab == "Startseite":
    _, col_logo, _ = st.columns([3, 1, 3])
    with col_logo:
        st.markdown("# 🏋️‍♂️")
    st.title("Gicht & Body-Recomposition Tracker")
    st.markdown(
        "<p style='text-align: center; color: gray;'>the best version of me @"
        " starter (Auto-Save aktiv 🟢)</p>",
        unsafe_allow_html=True,
    )
    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")

    total_kcal, total_prot = get_todays_totals()
    col1, col2 = st.columns(2)
    col1.metric("Heutige Kalorien", f"{total_kcal} kcal")
    col2.metric("Heutiges Protein", f"{total_prot} g")

    st.markdown("---")
    st.subheader("⚡ Macro & Target Status")
    target_kcal, target_prot = 2150, 140
    st.write(f"Kalorien-Ziel ({total_kcal} / {target_kcal} kcal)")
    st.progress(min(total_kcal / target_kcal, 1.0))
    st.write(f"Protein-Ziel ({total_prot} / {target_prot} g)")
    st.progress(min(total_prot / target_prot, 1.0))

    st.markdown("---")
    st.subheader("📌 Schnellauswahl")
    col_btn_a, col_btn_b = st.columns(2)
    with col_btn_a:
        if st.button("⚖️ Waagen-Analyse", use_container_width=True):
            st.session_state["nav_tab"] = "Waage"
            st.rerun()
        if st.button("🍳 Frühstück", use_container_width=True):
            st.session_state["nav_tab"] = "Frühstück"
            st.rerun()
        if st.button("🥗 Mittagessen", use_container_width=True):
            st.session_state["nav_tab"] = "Mittagessen"
            st.rerun()
        if st.button("🍲 Abendessen", use_container_width=True):
            st.session_state["nav_tab"] = "Abendessen"
            st.rerun()
        if st.button("📝 Vorlagen", use_container_width=True):
            st.session_state["nav_tab"] = "Vorlagen"
            st.rerun()
    with col_btn_b:
        if st.button("🍏 Snacks", use_container_width=True):
            st.session_state["nav_tab"] = "Snacks"
            st.rerun()
        if st.button("🥤 Getränke", use_container_width=True):
            st.session_state["nav_tab"] = "Getränke"
            st.rerun()
        if st.button("🏋️‍♂️ Training", use_container_width=True):
            st.session_state["nav_tab"] = "Training"
            st.rerun()
        if st.button("🏁 Tagesabschluss", use_container_width=True):
            st.session_state["nav_tab"] = "Abschluss"
            st.rerun()
        if st.button("📊 Statistiken", use_container_width=True):
            st.session_state["nav_tab"] = "Statistiken"
            st.rerun()

elif tab == "Vorlagen":
    render_preset_creator_page(save_current_day_to_excel)

elif tab == "Frühstück":
    render_meal_page(
        "Frühstück",
        "fruehstueck",
        st.session_state["api_key"],
        save_current_day_to_excel,
    )

elif tab == "Mittagessen":
    render_meal_page(
        "Mittagessen",
        "mittagessen",
        st.session_state["api_key"],
        save_current_day_to_excel,
    )

elif tab == "Abendessen":
    render_meal_page(
        "Abendessen",
        "abendessen",
        st.session_state["api_key"],
        save_current_day_to_excel,
    )

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
    d_safe = (
        st.session_state["drinks"]
        if isinstance(st.session_state["drinks"], dict)
        else {}
    )

    with st.expander(
        "👀 Übersicht der erfassten Mahlzeiten, Notizen & Gicht-Status (Kontrolle)",
        expanded=True,
    ):
        m = st.session_state["meals"]
        st.markdown(
            f"**Gesamtbilanz:** 🔥 {total_kcal} kcal | 🥩 {total_prot} g Protein"
        )
        st.markdown("---")
        for cat_label, cat_key in [
            ("🍳 Frühstück", "fruehstueck"),
            ("🥗 Mittagessen", "mittagessen"),
            ("🍲 Abendessen", "abendessen"),
            ("🍏 Snacks", "snacks"),
        ]:
            items = m.get(cat_key, [])
            if items:
                worst = get_worst_gicht_status(items)
                st.markdown(
                    f"**{cat_label}** *(Kategorie-Gichtstatus: **{worst}**)*:"
                )
                for itm in items:
                    gicht = itm.get("gicht_status", "Grün")
                    st.markdown(
                        f"- **{itm['desc']}** ({itm['kcal']} kcal, {itm['prot']}g Protein) | *Gicht: **{gicht}***"
                    )
                    if itm.get("notiz"):
                        st.caption(f"  📝 Notiz: {itm['notiz']}")
            else:
                st.markdown(f"**{cat_label}:** *Keine Einträge*")

        st.markdown("---")
        st.markdown(
            f"**🥤 Getränke:** Wasser/Soda: {d_safe.get('wasser_soda', 0)}L | Kaffee: {d_safe.get('kaffee', 0)} Tassen | Whey: {d_safe.get('whey_scoops', 0)} Scoops | Energy: {d_safe.get('redbull', 0)} Dosen"
        )
        if d_safe.get("sonstiges_txt"):
            st.markdown(
                f"*Sonstiges:* {d_safe.get('sonstiges_txt')} ({d_safe.get('sonstiges_kcal', 0)} kcal, {d_safe.get('sonstiges_prot', 0)}g Protein)"
            )

    st.markdown("---")
    meta = st.session_state["daily_meta"]
    meta["gewicht"] = st.number_input(
        "Heutiges Körpergewicht (kg)", value=float(meta["gewicht"]), step=0.1
    )
    meta["kfa"] = st.number_input(
        "Körperfettanteil KFA (%)", value=float(meta["kfa"]), step=0.1
    )
    meta["skel_musk"] = st.number_input(
        "Skelettmuskulatur (kg)", value=float(meta["skel_musk"]), step=0.1
    )
    meta["schritte"] = st.number_input(
        "Heutige Schritte", value=int(meta["schritte"]), step=500
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✨ Motivierende Tagesnotiz generieren"):
            meta["notizen"] = generate_summary_string()
            save_cache()
            st.success("Motivierende Tagesnotiz erfolgreich erstellt!")
            st.rerun()
    with col_btn2:
        if st.button("🧹 Heutigen Tag leeren"):
            clear_todays_data()
            st.success("Tagesdaten zurückgesetzt!")
            st.rerun()

    meta["notizen"] = st.text_area(
        "Tagesnotizen / Motivations-Feedback (wird in Excel gespeichert)",
        value=meta["notizen"],
    )

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# -------------------------------------------------------------------------
# CACHE AM ENDE SPEICHERN
# -------------------------------------------------------------------------
save_cache()
