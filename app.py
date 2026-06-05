# run mit streamlit run app.py

import datetime
import streamlit as st
import yfinance as yf


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


# holt über yfinance den kursverlauf und gibt den letzten schlusskurs zurück
# gibt None zurück wenn der ticker ungültig ist oder keine daten gefunden wurden
def lade_kursdaten(ticker, start, ende):
    try:
        # tickerobjekt erstellen und kursverlauf abrufen
        aktie = yf.Ticker(ticker)
        verlauf = aktie.history(start=start, end=ende)

        if verlauf.empty:
            return None

        # letzten schlusskurs aus der close spalte nehmen
        letzter_schlusskurs = verlauf["Close"].iloc[-1]
        return letzter_schlusskurs

    except Exception:
        return None


# hauptteil
st.set_page_config(layout="wide")
st.title("Fundamentalanalyse einer Aktie")

# eingabeformular anzeigen und eingaben einsammeln
ticker, start, ende, abgeschickt = zeige_eingabe_formular()

# bei klick auf den button kurs laden und anzeigen
if abgeschickt:
    kurs = lade_kursdaten(ticker, start, ende)

    if kurs is None:
        st.error("Keine Kursdaten gefunden. Bitte Ticker und Zeitraum prüfen.")
    else:
        st.metric("Letzter Schlusskurs im Zeitraum", round(kurs, 2))
