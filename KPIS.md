FORWARD KGV (Kurs-Gewinn-Verhältnis, zukunftsbasiert)

Das Forward KGV gibt an, zum wie vielfachen des für das nächste Geschäftsjahr prognostizierten Gewinns eine Aktie aktuell gehandelt wird. Statt auf den tatsächlich erzielten Gewinn der Vergangenheit greift man dabei auf den Analystenkonsens für den erwarteten Gewinn zurück. Ein niedriger Wert bedeutet, man zahlt wenig pro Euro erwartetem Gewinn; ein hoher Wert zeigt, dass der Markt für künftige Gewinne eine Prämie bezahlt. Der Wert wird von Finviz per Web Scraping bezogen und bei Nichtverfügbarkeit auf yfinance zurückgefallen.

Formel: Forward KGV = Kurs / Erwarteter Gewinn je Aktie

Legende:
Kurs: aktueller Aktienkurs am letzten Handelstag des gewählten Zeitraums
Erwarteter Gewinn je Aktie: Analystenkonsens für den Gewinn je Aktie im nächsten Geschäftsjahr, abgerufen von Finviz per Web Scraping mit BeautifulSoup; Fallback auf yfinance

Begründung: Investoren bewerten Aktien nicht auf Basis vergangener, sondern erwarteter Ertragskraft. Das Forward KGV bildet diese marktübliche Perspektive ab. Zudem erfüllt es die Projektanforderung einer zweiten externen Datenquelle, da der Wert per Web Scraping von Finviz bezogen wird und damit eine andere Quelle als yfinance zum Einsatz kommt.


KGV (Kurs-Gewinn-Verhältnis, historisch)

Das KGV ist die in der Praxis am häufigsten verwendete Bewertungskennzahl. Man teilt den aktuellen Kurs durch den im letzten abgeschlossenen Geschäftsjahr tatsächlich erzielten Gewinn je Aktie. Ein niedriger Wert bedeutet, man zahlt wenig pro Euro Gewinn; ein hoher Wert, dass der Markt eine Wachstums- oder Qualitätsprämie einpreist. Im Unterschied zum Forward KGV stützt man sich hier auf geprüfte und veröffentlichte Ist-Zahlen, die keinen Schätzrisiken unterliegen. Bei Verlustunternehmen, also negativem Gewinn je Aktie, ist das KGV nicht aussagekräftig und wird als nicht verfügbar ausgewiesen.

Formel: KGV = Kurs / Gewinn je Aktie

Legende:
Kurs: aktueller Aktienkurs am letzten Handelstag des gewählten Zeitraums
Gewinn je Aktie (Trailing EPS): tatsächlich erzielter Gewinn je Aktie des letzten vollen Geschäftsjahres, abgerufen über yfinance (Feld trailingEps)

Begründung: Das historische KGV ergänzt das Forward KGV, weil es zeigt, was das Unternehmen tatsächlich verdient hat, unabhängig von Prognosen. Zusammen bilden beide eine Bewertungsperspektive aus Vergangenheit und Erwartung. Die Kombination ist robuster als eine einzelne Kennzahl, da Analystenschätzungen mitunter stark von der tatsächlichen Entwicklung abweichen.


KBV (Kurs-Buchwert-Verhältnis)

Das KBV vergleicht den Marktwert einer Aktie mit ihrem bilanziellen Substanzwert. Man teilt den Kurs durch den Buchwert je Aktie, also das Eigenkapital des Unternehmens pro Aktie. Damit erhält man ein Verhältnis, das angibt, wie viel der Markt im Vergleich zum buchhalterischen Wert des Unternehmens zahlt. Ein KBV unter 1 bedeutet, der Markt bewertet das Unternehmen unter seinem Buchwert, was auf eine mögliche Unterbewertung hindeuten kann. Ein KBV deutlich über 1 zeigt, dass Anleger bereit sind, eine Prämie über den bilanziellen Wert zu zahlen, etwa wegen erwarteten Wachstums oder eines Wettbewerbsvorteils.

Formel: KBV = Kurs / Buchwert je Aktie

Legende:
Kurs: aktueller Aktienkurs am letzten Handelstag des gewählten Zeitraums
Buchwert je Aktie: bilanzielles Eigenkapital pro Aktie, abgerufen über yfinance (Feld bookValue)

Begründung: Das KBV bringt eine Substanzperspektive ins Modell, die rein gewinnbasierte Kennzahlen nicht abdecken. Es ist eine eigenständige Berechnung aus Kurs und Buchwert, wobei der Kurs aus der eigenen Kurshistorie und der Buchwert aus den Fundamentaldaten stammt. Einschränkung: Bei Technologie- und Dienstleistungsunternehmen mit hohem immateriellem Vermögen, etwa Markenwert oder Patente, bildet der Buchwert den tatsächlichen Unternehmenswert oft unvollständig ab. Dieser Punkt ist im Rahmen der kritischen Reflexion zu benennen.


DIVIDENDENRENDITE

Die Dividendenrendite gibt an, wie viel Prozent des aktuellen Aktienkurses ein Anleger jährlich als Ausschüttung erhält. Man berechnet sie, indem man die Dividende je Aktie durch den Kurs teilt und mit 100 multipliziert. Sie misst den laufenden Ertrag einer Investition unabhängig von Kursveränderungen. Zahlt ein Unternehmen keine Dividende, wie bei vielen Wachstumsunternehmen üblich, ergibt sich ein Wert von 0 %. Das ist kein Datenfehler, sondern eine strategische Entscheidung des Unternehmens, Gewinne zu reinvestieren statt auszuschütten.

Formel: Dividendenrendite = (Dividende je Aktie / Kurs) x 100

Legende:
Dividende je Aktie: zuletzt ausgeschütteter jährlicher Betrag pro Aktie, abgerufen über yfinance (Feld dividendRate)
Kurs: aktueller Aktienkurs am letzten Handelstag des gewählten Zeitraums

Begründung: Die Dividendenrendite bringt eine Ertragsdimension ins Modell, die die drei Bewertungskennzahlen nicht erfassen. Sie ist für einkommensorientierte Anleger besonders relevant und zeigt, welchen direkten Rückfluss eine Investition unabhängig von Kursentwicklungen erzeugt. Eine Dividendenrendite von 0 % wird im Modell als neutral gewertet, nicht als negatives Signal.
