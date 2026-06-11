voraussetzung: python 3 ist installiert und man befindet sich im projektordner.

venv erstellen (einmalig):
python3 -m venv .venv

venv aktivieren (jedes mal bevor man etwas startet):
source .venv/bin/activate

abhängigkeiten installieren (einmalig nach dem aktivieren):
pip install streamlit yfinance requests beautifulsoup4 pandas fpdf2 matplotlib

die haupt-app starten:
streamlit run app.py

einen spike (testskript) starten, z.b.:
python spikes/spike_yfinance.py
python spikes/spike_bs4.py
python spikes/spike_streamlit.py

venv beenden wenn man fertig ist:
deactivate
