# run mit streamlit run app.py

import datetime
import io
import streamlit as st
import yfinance as yf
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
# matplotlib backend agg ist nicht interaktiv und öffnet kein fenster
# das brauche ich weil streamlit kein eigenes grafik fenster hat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
# fpdf2 baut die pdf datei seitenweise auf
from fpdf import FPDF


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

        # kommagetrennte eingabe für vergleichsunternehmen
        # der standardwert zeigt direkt ein beispiel damit das format klar ist
        peers_eingabe = st.text_input("Vergleichsunternehmen (Ticker, kommagetrennt)", value="MSFT, GOOGL")

        abgeschickt = st.form_submit_button("Kurs abrufen")

    return ticker, start, ende, peers_eingabe, abgeschickt


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


# gibt die namen der wichtigsten treiber kpis zurück beitrag größer 0 und höchstens zwei
def nenne_treiber_kpis(beitraege):
    relevante_namen = []
    for beitrag, name in beitraege:
        if beitrag > 0:
            relevante_namen.append(name)

    relevante_namen = relevante_namen[:2]
    return " und ".join(relevante_namen)


# zeigt die einschätzung als farbige box an und nennt die treiber kpis
# grün bei unterbewertet gelb bei fair rot bei überbewertet
def zeige_einschaetzung_farbig(einschaetzung, punkte_dict, gewichte_dict):
    namen = ["Forward KGV", "KGV", "KBV", "Dividende"]

    # für jeden kpi den positiven beitrag zum score und den fehlbetrag zum maximum sammeln
    positive_beitraege = []
    fehlbetraege = []
    for name in namen:
        gewicht = gewichte_dict[name]
        punkte = punkte_dict[name]
        positive_beitraege.append((gewicht * punkte, name))
        fehlbetraege.append((gewicht * (100 - punkte), name))

    # absteigend sortieren größter beitrag zuerst
    positive_beitraege.sort(reverse=True)
    fehlbetraege.sort(reverse=True)

    if einschaetzung == "möglicherweise unterbewertet":
        # die kpis mit dem größten positiven beitrag tragen den hohen score
        hoechste = nenne_treiber_kpis(positive_beitraege)
        meldung = "möglicherweise unterbewertet – günstigste Bewertung bei " + hoechste
        st.success(meldung)
    elif einschaetzung == "fair bewertet":
        st.warning(einschaetzung)
    else:
        # die kpis mit dem größten fehlbetrag drücken den score am stärksten
        groesste_treiber = nenne_treiber_kpis(fehlbetraege)
        meldung = "möglicherweise überbewertet – hauptsächlich wegen " + groesste_treiber
        st.error(meldung)


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


# liest die historischen eps werte aus der jahres guv von yfinance
# gibt ein dict jahr zu eps zurück negative und fehlende werte werden übersprungen
def lade_historische_eps(ticker):
    try:
        aktie = yf.Ticker(ticker)
        jahres_guv = aktie.income_stmt

        if jahres_guv is None or jahres_guv.empty:
            return {}

        if "Diluted EPS" not in jahres_guv.index:
            return {}

        # die zeile mit dem verwässerten eps auswählen
        eps_zeile = jahres_guv.loc["Diluted EPS"]

        # für jedes jahr prüfen ob ein gültiger positiver eps wert vorliegt
        eps_pro_jahr = {}
        for datum, wert in eps_zeile.items():
            if not pd.isna(wert) and wert > 0:
                jahr = datum.year
                eps_pro_jahr[jahr] = wert

        return eps_pro_jahr

    except Exception:
        return {}


# berechnet das kgv für jedes jahr im eps dict jeweils auf basis des kurses am 31.12.
def berechne_kgv_verlauf(ticker, eps_pro_jahr):
    if not eps_pro_jahr:
        return {}
    try:
        aktie = yf.Ticker(ticker)
        kurshistorie_lang = aktie.history(period="5y")

        if kurshistorie_lang.empty:
            return {}

        close_serie = kurshistorie_lang["Close"].copy()

        # timezone aus dem index entfernen sonst schlägt der vergleich mit pd.Timestamp fehl
        if close_serie.index.tz is not None:
            close_serie.index = close_serie.index.tz_convert(None)

        # für jedes jahr den kurs am jahresende suchen und das kgv berechnen
        kgv_verlauf = {}
        for jahr, eps in eps_pro_jahr.items():
            zieldatum = pd.Timestamp(str(jahr) + "-12-31")
            # asof nimmt den letzten handelstag vor dem zieldatum falls der 31.12. auf ein wochenende fällt
            kurs_am_jahresende = close_serie.asof(zieldatum)

            if pd.isna(kurs_am_jahresende):
                continue

            kgv_verlauf[jahr] = kurs_am_jahresende / eps

        return kgv_verlauf

    except Exception:
        return {}


# holt den letzten verfügbaren schlusskurs period 5d wegen wochenenden und feiertagen
def lade_letzten_kurs(ticker):
    try:
        aktie = yf.Ticker(ticker)
        verlauf = aktie.history(period="5d")
        if verlauf.empty:
            return None
        return verlauf["Close"].iloc[-1]
    except Exception:
        return None


# fasst die gesamte kpi berechnung für einen ticker zusammen
# hauptaktie und peers nutzen dieselbe funktion
def berechne_alle_kpis(ticker, kurs):
    fundamentaldaten = lade_fundamentaldaten(ticker)

    # forward kgv zuerst über finviz versuchen sonst yfinance als fallback
    forward_kgv_wert = lade_forward_kgv(ticker)
    forward_kgv_quelle = "Finviz"
    if forward_kgv_wert is None:
        forward_kgv_wert = lade_forward_kgv_yfinance(ticker)
        forward_kgv_quelle = "yfinance (Fallback)"

    kpi_forward_kgv = berechne_forward_kgv(forward_kgv_wert)

    gewinn_je_aktie = fundamentaldaten.get("Gewinn je Aktie") if fundamentaldaten else None
    kpi_kgv = berechne_kgv(kurs, gewinn_je_aktie)

    buchwert_je_aktie = fundamentaldaten.get("Buchwert je Aktie") if fundamentaldaten else None
    kpi_kbv = berechne_kbv(kurs, buchwert_je_aktie)

    dividende_je_aktie = fundamentaldaten.get("Dividende je Aktie") if fundamentaldaten else None
    kpi_dividendenrendite = berechne_dividendenrendite(dividende_je_aktie, kurs)

    return {
        "Forward KGV": kpi_forward_kgv,
        "KGV": kpi_kgv,
        "KBV": kpi_kbv,
        "Dividende": kpi_dividendenrendite,
        "forward_kgv_quelle": forward_kgv_quelle,
        "fundamentaldaten": fundamentaldaten,
    }


# erstellt das kpi balkendiagramm als png im arbeitsspeicher io.BytesIO
def erzeuge_kpi_balken_png(punkte_dict):
    namen = list(punkte_dict.keys())
    # fehlende werte None als 0 darstellen
    werte = [wert if wert is not None else 0 for wert in punkte_dict.values()]

    fig, ax = plt.subplots(figsize=(6, 2.5))
    balken = ax.bar(namen, werte, color="#4472C4")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Punkte (0–100)")
    ax.set_title("KPI-Einzelpunkte")

    # über jedem balken den punktwert als text anzeigen
    for element, wert in zip(balken, werte):
        ax.text(
            element.get_x() + element.get_width() / 2,
            element.get_height() + 1,
            str(round(wert, 1)),
            ha="center", va="bottom", fontsize=9,
        )

    plt.tight_layout()
    # diagramm in einen byte puffer statt auf die festplatte schreiben
    puffer = io.BytesIO()
    plt.savefig(puffer, format="png", dpi=100)
    # leseposition zurück auf den anfang setzen
    puffer.seek(0)
    plt.close(fig)
    return puffer


# erstellt das kgv korridor diagramm als png im arbeitsspeicher
def erzeuge_kgv_korridor_png(kgv_verlauf, aktuelles_kgv):
    if not kgv_verlauf:
        return None

    # jahre aufsteigend sortieren damit die linie von links nach rechts verläuft
    jahre = sorted(kgv_verlauf.keys())
    werte = [kgv_verlauf[j] for j in jahre]
    durchschnitt = sum(werte) / len(werte)

    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.plot(jahre, werte, marker="o", color="#4472C4", label="KGV historisch")
    ax.axhline(durchschnitt, linestyle="--", color="#808080",
               label="Ø " + str(round(durchschnitt, 1)))
    if aktuelles_kgv is not None:
        ax.axhline(aktuelles_kgv, linestyle=":", color="#E74C3C",
                   label="Aktuell " + str(round(aktuelles_kgv, 1)))

    ax.set_xlabel("Jahr")
    ax.set_ylabel("KGV")
    ax.set_title("KGV-Korridor")
    ax.legend(fontsize=8)
    plt.tight_layout()

    puffer = io.BytesIO()
    plt.savefig(puffer, format="png", dpi=100)
    puffer.seek(0)
    plt.close(fig)
    return puffer


# baut den vollständigen pdf bericht und gibt ihn als bytes zurück
# fpdf2 arbeitet seitenweise add_page öffnet eine seite dann werden mit cell multi_cell und image inhalte platziert
# pdf.ln bewegt den cursor eine zeile weiter
def erzeuge_pdf_report(
    ticker,
    datum,
    kpi_forward_kgv,
    kpi_kgv,
    kpi_kbv,
    kpi_dividendenrendite,
    punkte_dict,
    gewichte_dict,
    gesamtscore,
    einschaetzung,
    kgv_verlauf,
    peer_kpis_liste,
    png_balken,
    png_korridor,
):
    # hilfsfunktion zum formatieren von zahlen None wird zu n/a
    def als_text(wert, stellen=2, einheit=""):
        if wert is None:
            return "n/a"
        return str(round(wert, stellen)) + einheit

    pdf = FPDF()
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # titelzeile
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Fundamentalanalyse - " + ticker)
    pdf.ln()
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Erstellt am " + datum)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # kpi tabelle
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "KPIs")
    pdf.ln()
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 6, "Kennzahl", border=1)
    pdf.cell(40, 6, "Wert", border=1)
    pdf.ln()
    pdf.set_font("Helvetica", size=9)

    kpi_zeilen = [
        ("Forward-KGV",      kpi_forward_kgv,      ""),
        ("KGV",              kpi_kgv,              ""),
        ("KBV",              kpi_kbv,              ""),
        ("Dividendenrendite", kpi_dividendenrendite, " %"),
    ]
    for bezeichnung, wert, einheit in kpi_zeilen:
        pdf.cell(80, 6, bezeichnung, border=1)
        pdf.cell(40, 6, als_text(wert, einheit=einheit), border=1)
        pdf.ln()

    pdf.ln(5)

    # scoring modell
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Scoring-Modell")
    pdf.ln()

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Gewichtung:")
    pdf.ln()
    pdf.set_font("Helvetica", size=9)
    reihenfolge = ["Forward KGV", "KGV", "KBV", "Dividende"]
    for name in reihenfolge:
        pdf.cell(45, 6, name + ": " + str(gewichte_dict.get(name, 0)) + " %", border=1)
    pdf.ln()
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Einzelpunkte (0-100):")
    pdf.ln()
    pdf.set_font("Helvetica", size=9)
    for name in reihenfolge:
        punkte = punkte_dict.get(name)
        pdf.cell(45, 6, name + ": " + als_text(punkte, stellen=1), border=1)
    pdf.ln()
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Gesamtscore: " + als_text(gesamtscore, stellen=1) + " / 100")
    pdf.ln()
    pdf.cell(0, 7, "Einschaetzung: " + (einschaetzung or "n/a"))
    pdf.ln()
    pdf.ln(3)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "Hinweis: Dieses Modell basiert auf vier Kennzahlen mit festen Schwellenwerten. "
        "Die Einschaetzung ist eine vereinfachende Naeherung und keine Kauf- oder Verkaufsempfehlung.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # kpi balkendiagramm
    if png_balken is not None:
        # bild ist ca 75mm hoch plus überschrift ca 17mm
        # wenn nicht genug platz übrig ist fange ich eine neue seite an
        # damit überschrift und bild zusammen auf derselben seite landen
        verbleibend = pdf.h - pdf.get_y() - pdf.b_margin
        if verbleibend < 92:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "KPI-Visualisierung")
        pdf.ln()
        png_balken.seek(0)
        pdf.image(png_balken, x=15, w=180)
        pdf.ln(5)

    # kgv korridor
    if png_korridor is not None:
        # gleiche prüfung überschrift und bild müssen auf dieselbe seite passen
        verbleibend = pdf.h - pdf.get_y() - pdf.b_margin
        if verbleibend < 92:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "KGV-Korridor (historisch)")
        pdf.ln()
        png_korridor.seek(0)
        pdf.image(png_korridor, x=15, w=180)
        pdf.ln(5)

    # peer vergleich
    if peer_kpis_liste:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Peer-Vergleich")
        pdf.ln()

        # gewichte als anteile zwischen 0 und 1 für die score berechnung der peers
        w_fkgv = gewichte_dict.get("Forward KGV", 0) / 100
        w_kgv  = gewichte_dict.get("KGV", 0) / 100
        w_kbv  = gewichte_dict.get("KBV", 0) / 100
        w_div  = gewichte_dict.get("Dividende", 0) / 100

        spalten = ["Ticker", "Fwd-KGV", "KGV", "KBV", "Div%", "Score", "Einschaetzung"]
        breiten = [22, 22, 22, 22, 22, 20, 50]
        pdf.set_font("Helvetica", "B", 8)
        for spalte, breite in zip(spalten, breiten):
            pdf.cell(breite, 6, spalte, border=1)
        pdf.ln()

        # erste zeile ist die hauptaktie dann folgen die peers
        alle_zeilen = [
            {
                "ticker":      ticker,
                "Forward KGV": kpi_forward_kgv,
                "KGV":         kpi_kgv,
                "KBV":         kpi_kbv,
                "Dividende":   kpi_dividendenrendite,
            }
        ] + peer_kpis_liste

        pdf.set_font("Helvetica", size=8)
        for zeile in alle_zeilen:
            p_fkgv = normalisiere_niedriger_besser(zeile.get("Forward KGV"), 12, 35)
            p_kgv  = normalisiere_niedriger_besser(zeile.get("KGV"),         12, 35)
            p_kbv  = normalisiere_niedriger_besser(zeile.get("KBV"),         1.5, 5)
            p_div  = normalisiere_hoeher_besser(zeile.get("Dividende"),      4,   0)
            zeilen_score = berechne_gesamtscore(
                p_fkgv, p_kgv, p_kbv, p_div, w_fkgv, w_kgv, w_kbv, w_div)
            zeilen_einschaetzung = interpretiere_score(zeilen_score) or "n/a"

            pdf.cell(22, 6, zeile.get("ticker", ""),          border=1)
            pdf.cell(22, 6, als_text(zeile.get("Forward KGV")), border=1)
            pdf.cell(22, 6, als_text(zeile.get("KGV")),          border=1)
            pdf.cell(22, 6, als_text(zeile.get("KBV")),          border=1)
            pdf.cell(22, 6, als_text(zeile.get("Dividende")),    border=1)
            pdf.cell(20, 6, als_text(zeilen_score, stellen=1),   border=1)
            pdf.cell(50, 6, zeilen_einschaetzung,                border=1)
            pdf.ln()

    return bytes(pdf.output())


# hauptteil
st.set_page_config(layout="wide")
st.title("Fundamentalanalyse einer Aktie")

# eingabeformular anzeigen und eingaben einsammeln
ticker, start, ende, peers_eingabe, abgeschickt = zeige_eingabe_formular()

# bei klick auf den button alle daten laden und in session_state ablegen
# die anzeige passiert danach in einem eigenen block damit sie auch beim verschieben der regler bleibt
if abgeschickt:
    kurshistorie = lade_kurshistorie(ticker, start, ende)

    if kurshistorie is None:
        st.error("Keine Kursdaten gefunden. Bitte Ticker und Zeitraum prüfen.")
        # alten stand löschen damit keine veralteten daten angezeigt werden
        for key in ["haupt_ticker", "kurshistorie", "letzter_schlusskurs", "fundamentaldaten",
                    "forward_kgv_quelle", "kpi_forward_kgv", "kpi_kgv",
                    "kpi_kbv", "kpi_dividendenrendite", "peer_kpis_liste",
                    "historische_eps", "kgv_verlauf"]:
            st.session_state.pop(key, None)
    else:
        letzter_schlusskurs = kurshistorie["Close"].iloc[-1]

        # berechne_alle_kpis übernimmt das laden der fundamentaldaten und das berechnen der vier kpi werte
        # der kurs aus der bereits geladenen kurshistorie wird übergeben damit kein zweiter abruf nötig ist
        kpis = berechne_alle_kpis(ticker, letzter_schlusskurs)
        fundamentaldaten = kpis["fundamentaldaten"]

        historische_eps = lade_historische_eps(ticker)
        kgv_verlauf = berechne_kgv_verlauf(ticker, historische_eps)

        # alles in session_state ablegen damit die anzeige unabhängig vom formular funktioniert
        st.session_state["haupt_ticker"] = ticker
        st.session_state["historische_eps"] = historische_eps
        st.session_state["kgv_verlauf"] = kgv_verlauf
        st.session_state["kurshistorie"] = kurshistorie
        st.session_state["letzter_schlusskurs"] = letzter_schlusskurs
        st.session_state["fundamentaldaten"] = fundamentaldaten
        st.session_state["forward_kgv_quelle"] = kpis["forward_kgv_quelle"]
        st.session_state["kpi_forward_kgv"] = kpis["Forward KGV"]
        st.session_state["kpi_kgv"] = kpis["KGV"]
        st.session_state["kpi_kbv"] = kpis["KBV"]
        st.session_state["kpi_dividendenrendite"] = kpis["Dividende"]

        # peer ticker aus der eingabe parsen
        # ich trenne am komma entferne leerzeichen mit strip und wandle in großbuchstaben um
        # leere einträge zum beispiel bei einem komma am ende filtere ich heraus
        peer_ticker_liste = []
        for teil in peers_eingabe.split(","):
            bereinigt = teil.strip().upper()
            if bereinigt:
                peer_ticker_liste.append(bereinigt)

        # für jeden peer ticker kurs und kpis laden und in einer liste sammeln
        # schlägt ein ticker fehl überspringe ich ihn mit einer warnung statt die app abzustürzen
        peer_kpis_liste = []
        for peer_ticker in peer_ticker_liste:
            peer_kurs = lade_letzten_kurs(peer_ticker)
            if peer_kurs is None:
                st.warning("Für " + peer_ticker + " wurden keine Kursdaten gefunden – übersprungen.")
                continue
            peer_kpis = berechne_alle_kpis(peer_ticker, peer_kurs)
            # ticker als feld hinzufügen damit ich in der tabelle weiß zu wem die werte gehören
            peer_kpis["ticker"] = peer_ticker
            peer_kpis_liste.append(peer_kpis)

        st.session_state["peer_kpis_liste"] = peer_kpis_liste


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

    # kursverlauf als linie zeichnen ich übergebe nur die spalte close
    # weil st.line_chart mit einem ganzen dataframe alle spalten gleichzeitig zeichnet
    # volume ist viele tausend mal größer als der kurs das würde die skala so stauchen
    # dass die kurslinie kaum noch zu erkennen wäre
    st.line_chart(kurshistorie["Close"])

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

    # kgv korridor historisches kgv pro jahr als linie dazu der durchschnitt als referenz
    st.subheader("KGV-Korridor")
    kgv_verlauf = st.session_state.get("kgv_verlauf", {})

    if not kgv_verlauf:
        st.info("Für diese Aktie sind keine historischen EPS-Daten verfügbar – der KGV-Korridor kann nicht berechnet werden.")
    else:
        # durchschnitt über alle verfügbaren jahre berechnen
        kgv_werte = list(kgv_verlauf.values())
        kgv_durchschnitt = sum(kgv_werte) / len(kgv_werte)

        # jahre sortieren damit die x achse chronologisch läuft
        kgv_jahre = sorted(kgv_verlauf.keys())

        # dataframe mit zwei spalten einmal die jahreswerte einmal der durchschnitt
        # den durchschnitt als eigene spalte zu übergeben ist der einfachste weg
        # eine horizontale referenzlinie in st.line_chart darzustellen
        kgv_tabelle = pd.DataFrame(
            {
                "KGV (historisch)": [round(kgv_verlauf[j], 1) for j in kgv_jahre],
                "Durchschnitt":     [round(kgv_durchschnitt, 1) for _ in kgv_jahre],
            },
            index=kgv_jahre,
        )
        st.line_chart(kgv_tabelle)

        # einordnung aktuelles kgv gegen den historischen schnitt
        aktuelles_kgv = st.session_state.get("kpi_kgv")
        if aktuelles_kgv is not None:
            abweichung = ((aktuelles_kgv - kgv_durchschnitt) / kgv_durchschnitt) * 100
            richtung = "über" if abweichung > 0 else "unter"
            st.caption(
                "Historischer Durchschnitt ("
                + str(min(kgv_jahre)) + "–" + str(max(kgv_jahre)) + "): "
                + str(round(kgv_durchschnitt, 1))
                + "  |  Aktuelles KGV: " + str(round(aktuelles_kgv, 1))
                + "  |  Das aktuelle KGV liegt "
                + str(round(abs(abweichung), 1)) + " % "
                + richtung + " dem historischen Schnitt."
            )

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

            # farbige box für die einschätzung anzeigen
            # ich übergebe die vier einzelpunkte als dictionary damit die funktion die treiber benennen kann
            punkte_dict = {
                "Forward KGV": punkte_forward_kgv,
                "KGV": punkte_kgv,
                "KBV": punkte_kbv,
                "Dividende": punkte_dividende,
            }
            # die gewichte als anteile (0 bis 1) mitgeben, damit die treiber-aussage
            # die aktuelle reglerstellung berücksichtigt.
            gewichte_anteile = {
                "Forward KGV": w_forward_kgv,
                "KGV": w_kgv,
                "KBV": w_kbv,
                "Dividende": w_dividende,
            }
            zeige_einschaetzung_farbig(einschaetzung, punkte_dict, gewichte_anteile)

            # schwellenwerte transparent darstellen damit nachvollziehbar ist wie die einschätzung zustande kommt
            # st.caption zeigt kleinen grauen text
            st.caption(
                "Einordnung: ab 65 Punkte möglicherweise unterbewertet, "
                "40 bis 64 Punkte fair bewertet, "
                "unter 40 Punkte möglicherweise überbewertet. "
                "Die Grenzen sind eine Modellannahme."
            )

            # balkendiagramm der vier einzelpunkte
            # ich baue einen kleinen dataframe weil st.bar_chart beschriftungen aus dem index liest
            # die spalte heißt Punkte die zeilennamen werden zu den balken bezeichnungen
            punkte_uebersicht = pd.DataFrame(
                {"Punkte": [punkte_forward_kgv, punkte_kgv, punkte_kbv, punkte_dividende]},
                index=["Forward KGV", "KGV", "KBV", "Dividende"],
            )
            st.bar_chart(punkte_uebersicht)

            # peer vergleich nur anzeigen wenn peers geladen sind
            if "peer_kpis_liste" in st.session_state and st.session_state["peer_kpis_liste"]:
                st.subheader("Peer-Vergleich")

                # alle ticker in einer liste sammeln hauptaktie zuerst dann peers
                # haupt_ticker kommt aus session_state damit er auch nach einem neustart ohne formular klick noch korrekt ist
                haupt_ticker = st.session_state.get("haupt_ticker", "Hauptaktie")
                alle_ticker = [haupt_ticker]
                alle_kpi_werte = [{
                    "Forward KGV": st.session_state["kpi_forward_kgv"],
                    "KGV":         st.session_state["kpi_kgv"],
                    "KBV":         st.session_state["kpi_kbv"],
                    "Dividende":   st.session_state["kpi_dividendenrendite"],
                }]

                for peer in st.session_state["peer_kpis_liste"]:
                    alle_ticker.append(peer["ticker"])
                    alle_kpi_werte.append({
                        "Forward KGV": peer["Forward KGV"],
                        "KGV":         peer["KGV"],
                        "KBV":         peer["KBV"],
                        "Dividende":   peer["Dividende"],
                    })

                # für jeden ticker die punkte und den score mit denselben gewichten und schwellenwerten wie die hauptaktie berechnen
                zeilen = []
                for kpis in alle_kpi_werte:
                    p_fkgv = normalisiere_niedriger_besser(kpis["Forward KGV"], gut_grenze=12, schlecht_grenze=35)
                    p_kgv  = normalisiere_niedriger_besser(kpis["KGV"],         gut_grenze=12, schlecht_grenze=35)
                    p_kbv  = normalisiere_niedriger_besser(kpis["KBV"],         gut_grenze=1.5, schlecht_grenze=5)
                    p_div  = normalisiere_hoeher_besser(kpis["Dividende"],      gut_grenze=4,  schlecht_grenze=0)

                    score = berechne_gesamtscore(
                        p_fkgv, p_kgv, p_kbv, p_div,
                        w_forward_kgv, w_kgv, w_kbv, w_dividende)
                    einschaetzung_zeile = interpretiere_score(score)

                    # hilfsfunktion zum formatieren None wird zu n/a
                    def fmt(wert, nachkommastellen=2):
                        if wert is None:
                            return "n/a"
                        return round(wert, nachkommastellen)

                    zeile = {
                        "Forward KGV":        fmt(kpis["Forward KGV"]),
                        "KGV":                fmt(kpis["KGV"]),
                        "KBV":                fmt(kpis["KBV"]),
                        "Dividendenrendite %": fmt(kpis["Dividende"]),
                        "Score":              fmt(score, 1),
                        "Einschätzung":       einschaetzung_zeile if einschaetzung_zeile else "n/a",
                    }
                    zeilen.append(zeile)

                # dataframe bauen jede zeile ist ein ticker die ticker namen werden zum index
                vergleich_tabelle = pd.DataFrame(zeilen, index=alle_ticker)
                st.dataframe(vergleich_tabelle)

            # pdf download
            st.subheader("PDF-Report")

            # matplotlib diagramme im speicher erzeugen statt auf festplatte zu schreiben
            png_balken = erzeuge_kpi_balken_png(punkte_dict)
            kgv_verlauf_fuer_pdf = st.session_state.get("kgv_verlauf", {})
            png_korridor = erzeuge_kgv_korridor_png(
                kgv_verlauf_fuer_pdf,
                st.session_state.get("kpi_kgv"),
            )

            pdf_bytes = erzeuge_pdf_report(
                ticker=st.session_state.get("haupt_ticker", ""),
                datum=datetime.date.today().strftime("%d.%m.%Y"),
                kpi_forward_kgv=st.session_state["kpi_forward_kgv"],
                kpi_kgv=st.session_state["kpi_kgv"],
                kpi_kbv=st.session_state["kpi_kbv"],
                kpi_dividendenrendite=st.session_state["kpi_dividendenrendite"],
                punkte_dict=punkte_dict,
                gewichte_dict={
                    "Forward KGV": gewicht_forward_kgv,
                    "KGV":         gewicht_kgv,
                    "KBV":         gewicht_kbv,
                    "Dividende":   gewicht_dividende,
                },
                gesamtscore=gesamtscore,
                einschaetzung=einschaetzung,
                kgv_verlauf=kgv_verlauf_fuer_pdf,
                peer_kpis_liste=st.session_state.get("peer_kpis_liste", []),
                png_balken=png_balken,
                png_korridor=png_korridor,
            )

            # dateiname aus dem ticker alles kleingeschrieben
            dateiname = st.session_state.get("haupt_ticker", "aktie").lower() + "_fundamentalanalyse.pdf"
            st.download_button(
                label="Bericht als PDF herunterladen",
                data=pdf_bytes,
                file_name=dateiname,
                mime="application/pdf",
            )
