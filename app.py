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


# hauptteil
st.set_page_config(layout="wide")
st.title("Fundamentalanalyse einer Aktie")

# eingabeformular anzeigen und eingaben einsammeln
ticker, start, ende, abgeschickt = zeige_eingabe_formular()

# bei klick auf den button kurshistorie und fundamentaldaten laden und anzeigen
if abgeschickt:
    kurshistorie = lade_kurshistorie(ticker, start, ende)

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
        for bezeichnung, wert in fundamentaldaten.items():
            if wert is None:
                st.write(bezeichnung + ": nicht verfügbar")
            else:
                st.write(bezeichnung + ": " + str(wert))
