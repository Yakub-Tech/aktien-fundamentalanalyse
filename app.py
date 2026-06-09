# run mit streamlit run app.py

import datetime
import streamlit as st
import yfinance as yf
import re
import requests
from bs4 import BeautifulSoup


# zeigt das eingabeformular an und gibt die eingaben zurück
def zeige_eingabe_formular():
    # standardwerte für den zeitraum bestimmen, heute und vor einem jahr
    heute = datetime.date.today()
    ein_jahr_zurueck = heute - datetime.timedelta(days=365)

    # formular aufbauen, abgeschickt wird erst beim klick auf den button
    with st.form("eingabe_formular"):
        ticker = st.text_input("Ticker", value="AAPL")
        start = st.date_input("Startdatum", value=ein_jahr_zurueck)
        ende = st.date_input("Enddatum", value=heute)
        abgeschickt = st.form_submit_button("Kurs abrufen")

    return ticker, start, ende, abgeschickt


# holt den kursverlauf für einen ticker und zeitraum über yfinance
# gibt einen bereinigten dataframe zurück oder None wenn keine daten gefunden wurden
def lade_kurshistorie(ticker, start, ende):
    try:
        # tickerobjekt erstellen und kursverlauf abrufen
        aktie = yf.Ticker(ticker)
        verlauf = aktie.history(start=start, end=ende)

        if verlauf.empty:
            return None

        # nur die spalten behalten die ich brauche und leere zeilen entfernen
        spalten_die_ich_brauche = ["Open", "High", "Low", "Close", "Volume"]
        verlauf = verlauf[spalten_die_ich_brauche]
        verlauf = verlauf.dropna()

        if verlauf.empty:
            return None

        return verlauf

    except Exception:
        return None


# holt die fundamentaldaten marktkapitalisierung eps buchwert und dividende über yfinance
def lade_fundamentaldaten(ticker):
    try:
        aktie = yf.Ticker(ticker)
        info = aktie.info

        # die vier benötigten felder einzeln auslesen
        # get statt eckiger klammer verwenden damit fehlende felder nicht zum absturz führen
        marktkapitalisierung = info.get("marketCap")
        gewinn_je_aktie = info.get("trailingEps")
        buchwert_je_aktie = info.get("bookValue")
        dividende_je_aktie = info.get("dividendRate")

        fundamentaldaten = {
            "Marktkapitalisierung": marktkapitalisierung,
            "Gewinn je Aktie": gewinn_je_aktie,
            "Buchwert je Aktie": buchwert_je_aktie,
            "Dividende je Aktie": dividende_je_aktie,
        }
        return fundamentaldaten

    except Exception:
        return None


# holt das forward kgv von finviz.com per web scraping
def lade_forward_kgv(ticker):
    try:
        url = "https://finviz.com/quote.ashx?t=" + ticker

        # ohne user agent header sperrt finviz die anfrage mit 403 forbidden
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        antwort = requests.get(url, headers=headers, timeout=10)
        antwort.raise_for_status()

        # html text parsen und alles als reinen text extrahieren
        suppe = BeautifulSoup(antwort.text, "html.parser")
        gesamter_text = suppe.get_text()

        # mit regex nach forward p/e suchen und die direkt folgende zahl auslesen
        treffer = re.search(r"Forward P/E([\d.]+)", gesamter_text)

        if treffer is None:
            return None

        return float(treffer.group(1))

    except Exception:
        return None


# fallback für das forward kgv liest forwardPE direkt aus yfinance aus
def lade_forward_kgv_yfinance(ticker):
    try:
        aktie = yf.Ticker(ticker)
        info = aktie.info
        return info.get("forwardPE")
    except Exception:
        return None


# formel forward kgv ist kurs durch erwarteten eps der wert kommt von finviz schon fertig
# reine durchleitung damit alle vier kpis gleich strukturiert sind
def berechne_forward_kgv(forward_kgv_wert):
    if forward_kgv_wert is None:
        return None
    return forward_kgv_wert


# formel kgv ist kurs durch gewinn je aktie trailing eps
def berechne_kgv(kurs, gewinn_je_aktie):
    if kurs is None or gewinn_je_aktie is None or gewinn_je_aktie <= 0:
        return None
    return kurs / gewinn_je_aktie


# formel kbv ist kurs durch buchwert je aktie
def berechne_kbv(kurs, buchwert_je_aktie):
    if kurs is None or buchwert_je_aktie is None or buchwert_je_aktie <= 0:
        return None
    return kurs / buchwert_je_aktie


# formel dividendenrendite ist dividende je aktie durch kurs mal 100
def berechne_dividendenrendite(dividende_je_aktie, kurs):
    if kurs is None or kurs <= 0:
        return None
    # keine dividende gemeldet also 0 prozent das ist ein gültiger wert
    if dividende_je_aktie is None:
        return 0.0
    return (dividende_je_aktie / kurs) * 100


# übersetzt einen kpi wert bei dem niedriger besser ist in punkte zwischen 0 und 100
def normalisiere_niedriger_besser(wert, gut_grenze, schlecht_grenze):
    if wert is None:
        return None
    # lineare normalisierung zwischen schlecht grenze 0 punkte und gut grenze 100 punkte
    punkte = (schlecht_grenze - wert) / (schlecht_grenze - gut_grenze) * 100
    # auf den bereich 0 bis 100 deckeln
    if punkte > 100:
        punkte = 100
    if punkte < 0:
        punkte = 0
    return punkte


# übersetzt einen kpi wert bei dem höher besser ist in punkte zwischen 0 und 100
def normalisiere_hoeher_besser(wert, gut_grenze, schlecht_grenze):
    if wert is None:
        return None
    punkte = (wert - schlecht_grenze) / (gut_grenze - schlecht_grenze) * 100
    if punkte > 100:
        punkte = 100
    if punkte < 0:
        punkte = 0
    return punkte


# berechnet den gewichteten gesamtscore aus den vier kpi punkten
# gibt None zurück wenn ein kpi wert fehlt
def berechne_gesamtscore(punkte_forward_kgv, punkte_kgv, punkte_kbv, punkte_dividende,
                          gewicht_forward_kgv, gewicht_kgv, gewicht_kbv, gewicht_dividende):
    if punkte_forward_kgv is None or punkte_kgv is None or punkte_kbv is None or punkte_dividende is None:
        return None
    # gewichtete summe aus allen vier punktwerten
    score = (gewicht_forward_kgv * punkte_forward_kgv
           + gewicht_kgv         * punkte_kgv
           + gewicht_kbv         * punkte_kbv
           + gewicht_dividende   * punkte_dividende)
    return score


# übersetzt den gesamtscore in eine texteinschätzung
# schwellenwerte 65 und 40 sind modellannahmen die ich in der präsentation begründe
def interpretiere_score(score):
    if score is None:
        return None
    if score >= 65:
        return "möglicherweise unterbewertet"
    elif score >= 40:
        return "fair bewertet"
    else:
        return "möglicherweise überbewertet"


# merkt sich welcher regler zuletzt bewegt wurde callback für on_change
def merke_aenderung_forward_kgv():
    st.session_state["zuletzt_geaendert"] = "g_forward_kgv"


def merke_aenderung_kgv():
    st.session_state["zuletzt_geaendert"] = "g_kgv"


def merke_aenderung_kbv():
    st.session_state["zuletzt_geaendert"] = "g_kbv"


def merke_aenderung_dividende():
    st.session_state["zuletzt_geaendert"] = "g_dividende"


# normalisiert die gewichte so dass ihre summe genau 100 ergibt
# der zuletzt veränderte regler bleibt fix die anderen drei werden proportional angepasst
def normalisiere_gewichte():
    fixer_key = st.session_state.get("zuletzt_geaendert", "g_forward_kgv")
    fixer_wert = st.session_state[fixer_key]

    # die drei anzupassenden regler bestimmen alle außer dem fixierten
    if fixer_key == "g_forward_kgv":
        andere_keys = ["g_kgv", "g_kbv", "g_dividende"]
    elif fixer_key == "g_kgv":
        andere_keys = ["g_forward_kgv", "g_kbv", "g_dividende"]
    elif fixer_key == "g_kbv":
        andere_keys = ["g_forward_kgv", "g_kgv", "g_dividende"]
    else:
        andere_keys = ["g_forward_kgv", "g_kgv", "g_kbv"]

    # restbetrag der auf die drei anderen regler verteilt werden muss
    restbetrag = 100 - fixer_wert
    alte_summe = (st.session_state[andere_keys[0]]
                + st.session_state[andere_keys[1]]
                + st.session_state[andere_keys[2]])

    if alte_summe > 0:
        # proportional zur bisherigen verteilung aufteilen
        w1 = round(restbetrag * st.session_state[andere_keys[0]] / alte_summe)
        w2 = round(restbetrag * st.session_state[andere_keys[1]] / alte_summe)
        # der dritte bekommt den rest damit die summe exakt 100 ergibt
        w3 = restbetrag - w1 - w2
        st.session_state[andere_keys[0]] = w1
        st.session_state[andere_keys[1]] = w2
        st.session_state[andere_keys[2]] = w3
    else:
        # sonderfall alle drei stehen auf 0 also gleichmäßig verteilen
        st.session_state[andere_keys[0]] = restbetrag // 3
        st.session_state[andere_keys[1]] = restbetrag // 3
        st.session_state[andere_keys[2]] = restbetrag - 2 * (restbetrag // 3)


# hauptteil
st.set_page_config(layout="wide")
st.title("Fundamentalanalyse einer Aktie")

# eingabeformular anzeigen und eingaben einsammeln
ticker, start, ende, abgeschickt = zeige_eingabe_formular()

# bei klick auf den button alle daten laden und in session_state ablegen
# die anzeige passiert danach in einem eigenen block damit sie auch beim verschieben der regler bleibt
if abgeschickt:
    kurshistorie = lade_kurshistorie(ticker, start, ende)

    if kurshistorie is None:
        st.error("Keine Kursdaten gefunden. Bitte Ticker und Zeitraum prüfen.")
        # alten stand löschen damit keine veralteten daten angezeigt werden
        for key in ["kurshistorie", "letzter_schlusskurs", "fundamentaldaten",
                    "forward_kgv_quelle", "kpi_forward_kgv", "kpi_kgv",
                    "kpi_kbv", "kpi_dividendenrendite"]:
            st.session_state.pop(key, None)
    else:
        letzter_schlusskurs = kurshistorie["Close"].iloc[-1]
        fundamentaldaten = lade_fundamentaldaten(ticker)

        forward_kgv = lade_forward_kgv(ticker)
        forward_kgv_quelle = "Finviz"
        if forward_kgv is None:
            forward_kgv = lade_forward_kgv_yfinance(ticker)
            forward_kgv_quelle = "yfinance (Fallback)"

        kpi_forward_kgv = berechne_forward_kgv(forward_kgv)
        gewinn_je_aktie = fundamentaldaten.get("Gewinn je Aktie") if fundamentaldaten else None
        kpi_kgv = berechne_kgv(letzter_schlusskurs, gewinn_je_aktie)
        buchwert_je_aktie = fundamentaldaten.get("Buchwert je Aktie") if fundamentaldaten else None
        kpi_kbv = berechne_kbv(letzter_schlusskurs, buchwert_je_aktie)
        dividende_je_aktie = fundamentaldaten.get("Dividende je Aktie") if fundamentaldaten else None
        kpi_dividendenrendite = berechne_dividendenrendite(dividende_je_aktie, letzter_schlusskurs)

        # alles in session_state ablegen damit die anzeige unabhängig vom formular funktioniert
        st.session_state["kurshistorie"] = kurshistorie
        st.session_state["letzter_schlusskurs"] = letzter_schlusskurs
        st.session_state["fundamentaldaten"] = fundamentaldaten
        st.session_state["forward_kgv_quelle"] = forward_kgv_quelle
        st.session_state["kpi_forward_kgv"] = kpi_forward_kgv
        st.session_state["kpi_kgv"] = kpi_kgv
        st.session_state["kpi_kbv"] = kpi_kbv
        st.session_state["kpi_dividendenrendite"] = kpi_dividendenrendite


# anzeige läuft immer solange daten in session_state vorhanden sind
# bleibt so auch sichtbar wenn nur ein regler verschoben wird
if "kurshistorie" in st.session_state:
    kurshistorie = st.session_state["kurshistorie"]
    letzter_schlusskurs = st.session_state["letzter_schlusskurs"]
    fundamentaldaten = st.session_state["fundamentaldaten"]
    forward_kgv_quelle = st.session_state["forward_kgv_quelle"]
    kpi_forward_kgv = st.session_state["kpi_forward_kgv"]
    kpi_kgv = st.session_state["kpi_kgv"]
    kpi_kbv = st.session_state["kpi_kbv"]
    kpi_dividendenrendite = st.session_state["kpi_dividendenrendite"]

    # kurshistorie anzeigen
    st.metric("Letzter Schlusskurs im Zeitraum", round(letzter_schlusskurs, 2))
    st.dataframe(kurshistorie)

    # fundamentaldaten anzeigen
    if fundamentaldaten is None:
        st.warning("Keine Fundamentaldaten gefunden.")
    else:
        st.subheader("Fundamentaldaten")
        felder_anzeigen = ["Marktkapitalisierung", "Gewinn je Aktie", "Buchwert je Aktie", "Dividende je Aktie"]
        for bezeichnung in felder_anzeigen:
            wert = fundamentaldaten.get(bezeichnung)
            if wert is None:
                st.write(bezeichnung + ": nicht verfügbar")
            else:
                st.write(bezeichnung + ": " + str(wert))

    # kpis anzeigen
    st.subheader("KPIs")
    spalte1, spalte2, spalte3, spalte4 = st.columns(4)

    with spalte1:
        wert = round(kpi_forward_kgv, 2) if kpi_forward_kgv is not None else "n/a"
        st.metric("Forward-KGV (" + forward_kgv_quelle + ")", wert)
    with spalte2:
        wert = round(kpi_kgv, 2) if kpi_kgv is not None else "n/a"
        st.metric("KGV", wert)
    with spalte3:
        wert = round(kpi_kbv, 2) if kpi_kbv is not None else "n/a"
        st.metric("KBV", wert)
    with spalte4:
        wert = str(round(kpi_dividendenrendite, 2)) + " %" if kpi_dividendenrendite is not None else "n/a"
        st.metric("Dividendenrendite", wert)

    # scoring modell mit gewichtungsreglern
    st.subheader("Scoring-Modell")

    st.info(
        "Die Regler bestimmen, wie stark jeder KPI in die Gesamtbewertung einfließt. "
        "Die Standardwerte gehen davon aus, dass Gewinne wichtiger sind als Substanzwert oder Dividende. "
        "Wer das anders sieht, kann die Regler anpassen (der Score ändert sich sofort). "
        "Es gibt keine objektiv richtige Gewichtung, jede Verteilung ist eine Annahme."
    )

    # standardgewichte nur beim allerersten aufruf setzen
    if "g_forward_kgv" not in st.session_state:
        st.session_state["g_forward_kgv"] = 35
        st.session_state["g_kgv"] = 25
        st.session_state["g_kbv"] = 20
        st.session_state["g_dividende"] = 20

    # vier regler nebeneinander jeweils mit session_state verknüpft
    spalte1, spalte2, spalte3, spalte4 = st.columns(4)

    with spalte1:
        st.slider("Gewinnerwartung (Forward KGV) %", 0, 100,
                  key="g_forward_kgv", on_change=merke_aenderung_forward_kgv)
    with spalte2:
        st.slider("Bewährter Gewinn (KGV) %", 0, 100,
                  key="g_kgv", on_change=merke_aenderung_kgv)
    with spalte3:
        st.slider("Substanzwert (KBV) %", 0, 100,
                  key="g_kbv", on_change=merke_aenderung_kbv)
    with spalte4:
        st.slider("Ausschüttung (Dividende) %", 0, 100,
                  key="g_dividende", on_change=merke_aenderung_dividende)

    gewicht_forward_kgv = st.session_state["g_forward_kgv"]
    gewicht_kgv = st.session_state["g_kgv"]
    gewicht_kbv = st.session_state["g_kbv"]
    gewicht_dividende = st.session_state["g_dividende"]

    summe_gewichte = gewicht_forward_kgv + gewicht_kgv + gewicht_kbv + gewicht_dividende
    st.write("Summe der Gewichte: " + str(summe_gewichte) + " %")

    if summe_gewichte != 100:
        st.warning("Die Gewichte ergeben zusammen nicht 100 %. Bitte die Regler manuell anpassen oder den Button nutzen.")
        st.button("Auf 100 % normalisieren", on_click=normalisiere_gewichte)

    if summe_gewichte == 100:
        # jeden kpi in punkte zwischen 0 und 100 umrechnen
        # schwellenwerte forward kgv und kgv gut bei 12 schlecht ab 35
        # kbv gut bei 1.5 schlecht ab 5 dividendenrendite gut ab 4 prozent schlecht bei 0
        punkte_forward_kgv = normalisiere_niedriger_besser(
            st.session_state["kpi_forward_kgv"], gut_grenze=12, schlecht_grenze=35)
        punkte_kgv = normalisiere_niedriger_besser(
            st.session_state["kpi_kgv"], gut_grenze=12, schlecht_grenze=35)
        punkte_kbv = normalisiere_niedriger_besser(
            st.session_state["kpi_kbv"], gut_grenze=1.5, schlecht_grenze=5)
        punkte_dividende = normalisiere_hoeher_besser(
            st.session_state["kpi_dividendenrendite"], gut_grenze=4, schlecht_grenze=0)

        # einzelpunkte anzeigen damit der gesamtscore nachvollziehbar bleibt
        st.write("Einzelpunkte (0–100):")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            anzeige = str(round(punkte_forward_kgv, 1)) if punkte_forward_kgv is not None else "n/a"
            st.metric("Forward KGV", anzeige)
        with p2:
            anzeige = str(round(punkte_kgv, 1)) if punkte_kgv is not None else "n/a"
            st.metric("KGV", anzeige)
        with p3:
            anzeige = str(round(punkte_kbv, 1)) if punkte_kbv is not None else "n/a"
            st.metric("KBV", anzeige)
        with p4:
            anzeige = str(round(punkte_dividende, 1)) if punkte_dividende is not None else "n/a"
            st.metric("Dividendenrendite", anzeige)

        # gewichte von prozent in anteile umrechnen 35 prozent wird zu 0.35
        w_forward_kgv = gewicht_forward_kgv / 100
        w_kgv = gewicht_kgv / 100
        w_kbv = gewicht_kbv / 100
        w_dividende = gewicht_dividende / 100

        gesamtscore = berechne_gesamtscore(
            punkte_forward_kgv, punkte_kgv, punkte_kbv, punkte_dividende,
            w_forward_kgv, w_kgv, w_kbv, w_dividende)

        if gesamtscore is None:
            st.warning("Gesamtscore kann nicht berechnet werden, weil nicht alle KPIs verfügbar sind.")
        else:
            einschaetzung = interpretiere_score(gesamtscore)
            st.metric("Gesamtscore (0–100)", round(gesamtscore, 1))
            st.write("Einschätzung: " + einschaetzung)
