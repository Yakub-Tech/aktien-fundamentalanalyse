import requests

from bs4 import BeautifulSoup

# URL der Seite, die wir untersuchen möchten

url = "https://live.deutsche-boerse.com"

# HTML der Webseite herunterladen

antwort = requests.get(url)

# Prüfen, ob der Abruf funktioniert hat (200 = OK)

print("Status:", antwort.status_code)

# HTML-Text in BeautifulSoup einlesen,

# damit wir später Elemente suchen können

suppe = BeautifulSoup(antwort.text, "html.parser")

# Erstes <td>-Element auf der Seite suchen

testFeldAusHtml = suppe.find("td")

# Gefundenes Element ausgeben

print("TD:", testFeldAusHtml)

# Die ersten 2000 Zeichen des HTML anzeigen,

# damit wir sehen, was requests tatsächlich bekommen hat

print(antwort.text[:2000])

# Prüfen, ob der Wert "163,20" überhaupt im HTML vorkommt

print("163,20" in antwort.text)


## da die werte hier auf der seite erst nach dem js code kommen in die html , 
# die html aber erst geladen ist vor dem js daten get 
# - ist das problem dass ich die 163,20 euro ganricht bekomme !