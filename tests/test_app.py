import datetime
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

AppTest.from_string('import app', default_timeout=30).run()
import app


from tests.beispieldaten import BeispielTicker


class BerechnungenTest(unittest.TestCase):
    def test_kennzahlen_und_ungueltige_nenner(self):
        self.assertEqual(app.berechne_kgv(100, 5), 20)
        self.assertEqual(app.berechne_kbv(100, 40), 2.5)
        self.assertEqual(app.berechne_dividendenrendite(2, 100), 2)
        self.assertEqual(app.berechne_dividendenrendite(0, 100), 0)
        for eps in [None, 0, -2]:
            self.assertIsNone(app.berechne_kgv(100, eps))
        self.assertIsNone(app.berechne_kbv(100, 0))
        self.assertIsNone(app.berechne_dividendenrendite(2, 0))

    def test_fehlende_dividende_ist_keine_bestaetigte_null(self):
        self.assertIsNone(app.berechne_dividendenrendite(None, 100))

    def test_score_und_fehlende_kennzahlen(self):
        self.assertEqual(app.normalisiere_niedriger_besser(12, 12, 35), 100)
        self.assertEqual(app.normalisiere_niedriger_besser(40, 12, 35), 0)
        self.assertEqual(app.normalisiere_hoeher_besser(2, 4, 0), 50)
        self.assertIsNone(app.normalisiere_niedriger_besser(float('nan'), 12, 35))
        self.assertEqual(app.berechne_gesamtscore(100, 80, 50, 0, .35, .25, .2, .2), 65)
        self.assertIsNone(app.berechne_gesamtscore(None, 80, 50, 0, .35, .25, .2, .2))
        self.assertEqual(app.interpretiere_score(65), 'möglicherweise unterbewertet')
        self.assertEqual(app.interpretiere_score(40), 'fair bewertet')
        self.assertEqual(app.interpretiere_score(39.9), 'möglicherweise überbewertet')

    def test_normalisierung_erzeugt_keine_negativen_gewichte(self):
        state = {'zuletzt_geaendert': 'g_forward_kgv', 'g_forward_kgv': 97,
                 'g_kgv': 50, 'g_kbv': 50, 'g_dividende': 0}
        with patch.object(app.st, 'session_state', state):
            app.normalisiere_gewichte()
        values = [state[key] for key in ['g_forward_kgv', 'g_kgv', 'g_kbv', 'g_dividende']]
        self.assertEqual(sum(values), 100)
        self.assertEqual(values[0], 97)
        self.assertGreaterEqual(min(values), 0)

    def test_letzter_kurs_ueberspringt_nan(self):
        frame = pd.DataFrame({'Close': [100., float('nan')]})
        with patch('yfinance.Ticker') as ticker:
            ticker.return_value.history.return_value = frame
            self.assertEqual(app.lade_letzten_kurs('AAPL'), 100)
            ticker.return_value.history.return_value = frame.iloc[0:0]
            self.assertIsNone(app.lade_letzten_kurs('AAPL'))


class OberflaecheTest(unittest.TestCase):
    def setUp(self):
        self.ticker = patch('yfinance.Ticker', BeispielTicker)
        self.http = patch('requests.get', side_effect=ConnectionError('Test ohne Netzwerk'))
        self.ticker.start()
        self.http.start()
        self.addCleanup(self.ticker.stop)
        self.addCleanup(self.http.stop)
        self.ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()

    def abrufen(self):
        self.ui.date_input[0].set_value(datetime.date(2025, 1, 1))
        self.ui.date_input[1].set_value(datetime.date(2026, 1, 1))
        self.ui.button[0].click().run()

    def test_analyse_peers_und_pdf(self):
        self.abrufen()
        self.assertFalse(self.ui.exception)
        self.assertEqual(len(self.ui.tabs), 4)
        self.assertEqual(self.ui.session_state['haupt_ticker'], 'AAPL')
        self.assertEqual(len(self.ui.session_state['peer_kpis_liste']), 2)
        self.assertEqual(self.ui.metric[0].value, '18.0')
        self.assertEqual(len(self.ui.get('download_button')), 1)
        self.assertEqual(len(self.ui.session_state['kgv_verlauf']), 4)

    def test_ungueltige_eingabe_entfernt_alte_ergebnisse(self):
        self.abrufen()
        self.ui.text_input[0].set_value('   ')
        self.ui.button[0].click().run()
        self.assertFalse(self.ui.exception)
        self.assertTrue(self.ui.error)
        self.assertNotIn('kurshistorie', self.ui.session_state)
        self.assertEqual(len(self.ui.get('download_button')), 0)

    def test_ungueltiger_zeitraum(self):
        self.ui.date_input[0].set_value(datetime.date(2026, 1, 1))
        self.ui.date_input[1].set_value(datetime.date(2025, 1, 1))
        self.ui.button[0].click().run()
        self.assertTrue(self.ui.error)
        self.assertNotIn('kurshistorie', self.ui.session_state)


if __name__ == '__main__':
    unittest.main()
