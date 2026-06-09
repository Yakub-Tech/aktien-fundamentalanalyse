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


# hauptteil
st.set_page_config(layout="wide")
st.title("Fundamentalanalyse einer Aktie")

# eingabeformular anzeigen und eingaben einsammeln
ticker, start, ende, abgeschickt = zeige_eingabe_formular()

# bei klick auf den button kurshistorie, fundamentaldaten und kpis laden und anzeigen
if abgeschickt:
    kurshistorie = lade_kurshistorie(ticker, start, ende)

    # letzter_schlusskurs auch außerhalb des else blocks verfügbar machen
    letzter_schlusskurs = None

    if kurshistorie is None:
        st.error("Keine Kursdaten gefunden. Bitte Ticker und Zeitraum prüfen.")
    else:
        # letzten schlusskurs aus der close spalte nehmen
        letzter_schlusskurs = kurshistorie["Close"].iloc[-1]
        st.metric("Letzter Schlusskurs im Zeitraum", round(letzter_schlusskurs, 2))

        # gesamte bereinigte tabelle anzeigen
        st.dataframe(kurshistorie)

    # fundamentaldaten unabhängig von der kurshistorie laden und anzeigen
    fundamentaldaten = lade_fundamentaldaten(ticker)

    if fundamentaldaten is None:
        st.warning("Keine Fundamentaldaten gefunden.")
    else:
        st.subheader("Fundamentaldaten")
        # nur die vier rohwerte anzeigen, die kpis kommen separat im nächsten abschnitt
        felder_anzeigen = ["Marktkapitalisierung", "Gewinn je Aktie", "Buchwert je Aktie", "Dividende je Aktie"]
        for bezeichnung in felder_anzeigen:
            wert = fundamentaldaten.get(bezeichnung)
            if wert is None:
                st.write(bezeichnung + ": nicht verfügbar")
            else:
                st.write(bezeichnung + ": " + str(wert))

    # forward kgv zuerst über finviz versuchen sonst yfinance als fallback
    forward_kgv = lade_forward_kgv(ticker)
    forward_kgv_quelle = "Finviz"
    if forward_kgv is None:
        forward_kgv = lade_forward_kgv_yfinance(ticker)
        forward_kgv_quelle = "yfinance (Fallback)"

    # alle vier kpis berechnen, fehlende rohwerte führen zu None und werden als n/a angezeigt
    kpi_forward_kgv = berechne_forward_kgv(forward_kgv)

    gewinn_je_aktie = fundamentaldaten.get("Gewinn je Aktie") if fundamentaldaten else None
    kpi_kgv = berechne_kgv(letzter_schlusskurs, gewinn_je_aktie)

    buchwert_je_aktie = fundamentaldaten.get("Buchwert je Aktie") if fundamentaldaten else None
    kpi_kbv = berechne_kbv(letzter_schlusskurs, buchwert_je_aktie)

    dividende_je_aktie = fundamentaldaten.get("Dividende je Aktie") if fundamentaldaten else None
    kpi_dividendenrendite = berechne_dividendenrendite(dividende_je_aktie, letzter_schlusskurs)

    # alle vier kpis nebeneinander in vier spalten anzeigen
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
