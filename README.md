# Aktien-Fundamentalanalyse

**Aktienkennzahlen abrufen, ein nachvollziehbares Bewertungsmodell berechnen und Unternehmen vergleichen.**

[English](README.en.md) · [Lizenz](LICENSE)

Ein Python-Projekt von **Yakub Uyar**. Die deutschsprachige Streamlit-Anwendung
verbindet Datenabruf, Kennzahlenberechnung, interaktive Diagramme und PDF-Export.
Sie macht sichtbar, wie Kennzahlen und Gewichtungen eine Modelleinschätzung
beeinflussen. Ergebnisse sind keine Anlageberatung und keine Kauf- oder
Verkaufsempfehlung.

## Einblicke

Die Screenshots zeigen die laufende Anwendung mit **fiktiven Beispieldaten**.
Die Tickersymbole veranschaulichen die Eingabe; die Werte sind keine echten
Börsenkurse oder Unternehmensbewertungen.

### Übersicht

Kennzahlen, individueller Gesamtscore und Einzelpunkte mit einstellbarer Gewichtung.

![Deutsche Übersicht mit Kennzahlen, Gewichtung und Bewertungsdiagramm](assets/screenshots/uebersicht.png)

### Kurs und Korridor

Schlusskursverlauf und historische KGV-Werte mit Durchschnitt als Referenz.

![Kursverlauf und historischer KGV-Korridor mit Beispieldaten](assets/screenshots/kurs-korridor.png)

### Vergleichsunternehmen

Gemeinsame Kennzahlentabelle, Scores und Rangfolge der gewählten Unternehmen.

![Peer-Vergleich mit Kennzahlentabelle und Gesamtscores](assets/screenshots/vergleich.png)

## Funktionen und Aufbau

- Ticker, Zeitraum und Vergleichsunternehmen eingeben
- Kursverlauf und Fundamentaldaten über yfinance laden
- Forward-KGV über Finviz auslesen, mit yfinance als Fallback
- KGV, KBV und Dividendenrendite berechnen
- Vier Kennzahlen auf 0 bis 100 Punkte normalisieren und individuell gewichten
- Gewichte auf insgesamt 100 % normalisieren
- Historische KGV-Werte aus Jahres-EPS und Jahresendkursen vergleichen
- Einen PDF-Bericht mit Kennzahlen, Gewichtung, Diagrammen und Peer-Vergleich herunterladen

| Bereich | Umsetzung |
| --- | --- |
| Oberfläche | Streamlit mit Formular, Session-State, Schiebereglern und vier Tabs |
| Daten | yfinance sowie Requests und Beautiful Soup für Finviz |
| Verarbeitung | Pandas für Kursreihen und Vergleichstabellen |
| Diagramme | Altair in der Oberfläche, Matplotlib für den Bericht |
| PDF | fpdf2; Bilder und Bericht entstehen im Arbeitsspeicher |
| Tests | unittest und Streamlit AppTest mit kontrollierten Datenquellen |

Die Anwendung bleibt in `app.py`. Hauptaktie und Peers verwenden dieselben
Berechnungsfunktionen. Abgerufene Daten bleiben in der Sitzung erhalten;
Gewichtsänderungen benötigen keinen erneuten Datenabruf.

## Bewertungsmodell

| Kennzahl | Berechnung | 100 Punkte | 0 Punkte | Standardgewicht |
| --- | --- | --- | --- | --- |
| Forward-KGV | Wert der Quelle auf Basis erwarteter Gewinne | ≤ 12 | ≥ 35 | 35 % |
| KGV | Schlusskurs / Gewinn je Aktie | ≤ 12 | ≥ 35 | 25 % |
| KBV | Schlusskurs / Buchwert je Aktie | ≤ 1,5 | ≥ 5 | 20 % |
| Dividendenrendite | Jährliche Dividende / Schlusskurs × 100 | ≥ 4 % | 0 % | 20 % |

Zwischen den Grenzen wird linear normalisiert. Der Gesamtscore ist die gewichtete
Summe. Ab 65 Punkten lautet die Modelleinschätzung „möglicherweise unterbewertet“,
ab 40 „fair bewertet“, darunter „möglicherweise überbewertet“. Die Grenzen sind
feste Modellannahmen, keine empirisch validierten Signale. Fehlende Kennzahlen
verhindern Gesamtscore und PDF-Export. Eine bestätigte Dividende von null ist
gültig; ein fehlender Dividendenwert bleibt unbekannt.

## Lokal starten

Voraussetzungen: **Python 3.12** und Internetzugang für Installation und Datenabruf.
API-Schlüssel, `.env`-Datei und Datenbank sind nicht erforderlich.

```sh
git clone https://github.com/Yakub-Tech/aktien-fundamentalanalyse.git
cd aktien-fundamentalanalyse
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Unter Windows mit Python 3.12 stattdessen die Umgebung so erstellen und aktivieren:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Anschließend dieselben Installations- und Startbefehle mit `python` verwenden.
`http://localhost:8501` öffnen, beispielsweise `AAPL` und `MSFT, GOOGL` als Peers
eingeben, Zeitraum wählen und **Kurs abrufen** klicken. Das Enddatum ist beim
Kursabruf exklusiv. Gewichte anpassen und bei Bedarf **Auf 100 % normalisieren**
klicken. Der PDF-Download befindet sich im Tab **Report**.

Beenden mit `Ctrl+C`, die Umgebung mit `deactivate` verlassen. Es gibt keine
eigene dauerhafte Datenspeicherung. Berichte selbst sichern; yfinance kann lokale
Verbindungs- und Zeitzonencaches anlegen.

## Entwicklung und Prüfungen

```sh
python -m unittest discover -s tests -v
python -m compileall -q app.py spikes tests
```

Die Tests prüfen Berechnungen, fehlende Werte, Gewichtsnormalisierung,
Eingabevalidierung sowie Analyse, Peer-Vergleich und PDF-Erzeugung. Externe Quellen
werden durch fiktive Testdaten ersetzt. GitHub Actions führt diese Prüfungen unter
Python 3.12 aus, ohne auf Yahoo oder Finviz zugreifen zu müssen.

```text
app.py                  Datenabruf, Berechnungen, Oberfläche und PDF
requirements.txt        Festgelegte Abhängigkeiten
.streamlit/config.toml  Dunkles Oberflächenthema
tests/                  Berechnungs- und Oberflächentests, Beispieldaten
spikes/                 Ursprüngliche Bibliotheks-Experimente
assets/screenshots/     Ansichten der laufenden Anwendung
.github/workflows/      Automatische Prüfungen
```

Die frühen Experimente in `spikes/` gehören nicht zum Hauptablauf.
Start: `python spikes/spike_yfinance.py`, `python spikes/spike_bs4.py` oder
`python -m streamlit run spikes/spike_streamlit.py`.

## Grenzen und sichere Nutzung

- Yahoo und Finviz können Anfragen sperren, begrenzen oder Schnittstellen ändern.
  Fehlende Kurse werden gemeldet; Finviz-Ausfälle nutzen den Fallback.
- Die Hauptaktie verwendet den letzten Schlusskurs im gewählten Zeitraum.
  Fundamentaldaten und Peer-Kurse werden zum Abrufzeitpunkt geladen. Ein alter
  Zeitraum rekonstruiert deshalb keine damalige Unternehmensbewertung.
- Der historische Korridor nutzt den 31. Dezember als Referenz und nur verfügbare
  positive Jahres-EPS. Geschäftsjahresenden können abweichen; wenige Datenpunkte
  und fehlende Jahre begrenzen die Aussagekraft.
- Branchen, Währungen, Wachstum, Verschuldung und qualitative Faktoren werden
  nicht ausgeglichen. Peers werden manuell gewählt.
- Die Anwendung hat keine Anmeldung. Der dokumentierte Start bindet sie an den
  eigenen Rechner. Öffentlicher Serverbetrieb erfordert separate Absicherung.
- Die Softwarelizenz erteilt keine Marktdatenrechte. yfinance weist auf persönliche
  Nutzung der Yahoo-Daten hin. Vor Weitergabe oder geschäftlicher Datenverwendung
  müssen die Anbieterbedingungen separat geprüft werden. Siehe [Drittanbieter](THIRD_PARTY.md).

## Lizenz und Verantwortung

Copyright © 2026 **Yakub Uyar**. Die [eigene zweisprachige Lizenz](LICENSE) erlaubt
Ansehen, Herunterladen, eigene Nutzung und Anpassung sowie kostenlose Weitergabe
mit Quellcode und Hinweisen. Vereine und Unternehmen dürfen den eigenen Code
für ihre Arbeit verwenden. Verkauf der Software oder abgeleiteter Versionen
und kostenpflichtige Softwaredienste benötigen eine ausdrückliche Erlaubnis.
Rechte Dritter bleiben unberührt. Dies ist keine Open-Source-Lizenz.

Nutzung auf eigene Verantwortung, im vorhandenen Zustand und soweit gesetzlich
zulässig. Vor realer Nutzung Eignung, Berechnungen, Sicherheit, Datenschutz und
geltende Anforderungen prüfen. Betreiber sind für Einrichtung, Zugriffsrechte,
Betrieb, Sicherung und Wiederherstellung verantwortlich. Wartung, Unterstützung
oder bestimmte Ergebnisse werden nicht zugesagt. Zwingende Gewährleistungs-
und Haftungsrechte bleiben erhalten.
