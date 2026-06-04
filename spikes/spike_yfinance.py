import yfinance as yf


aktie = yf.Ticker("AAPL")

#info ist ein Dictionary Schlüssel-Wert-Paare
infos = aktie.info
print("Firmenname:", infos.get("longName"))
print("aktuellerKurs:", infos.get("currentPrice"))
print("KGV:(trailingPE)", infos.get("trailingPE"))

verlauf = aktie.history(period="1mo")
print(verlauf)

print(infos.keys())

#ausführen mit python spike_yfinance.py