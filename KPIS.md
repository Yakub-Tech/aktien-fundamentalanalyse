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


---


SCORING-MODELL


Warum ich die KPIs nicht einfach addieren kann

Die vier KPIs bewegen sich auf völlig unterschiedlichen Skalen. Das Forward KGV und das KGV liegen typischerweise zwischen 5 und 50, das KBV zwischen 0,5 und 10, die Dividendenrendite zwischen 0 und 8 Prozent. Dazu kommt, dass die Richtungen unterschiedlich sind: beim Forward KGV, KGV und KBV ist ein niedriger Wert besser, bei der Dividendenrendite ist ein hoher Wert besser. Wenn ich die Rohwerte einfach gewichten und addieren würde, käme Unsinn heraus. Ich muss sie deshalb zuerst in eine einheitliche Punkteskala übersetzen, bevor ich sie zusammenführen kann.


Wie ich die Normalisierung gemacht habe

Ich habe mich für eine schwellenwertbasierte lineare Normalisierung entschieden. Das Prinzip ist einfach: ich lege für jeden KPI einen Wert fest, der als "gut" gilt, und einen, der als "schlecht" gilt. Der tatsächliche KPI-Wert wird dann linear zwischen diesen beiden Grenzen auf eine Skala von 0 bis 100 Punkte abgebildet. Liegt der Wert besser als die "gut"-Grenze, bekommt er 100 Punkte. Liegt er schlechter als die "schlecht"-Grenze, bekommt er 0 Punkte.

Für KPIs, bei denen niedriger besser ist (Forward KGV, KGV, KBV), lautet die Formel:

punkte = (schwellenwert_schlecht - kpi_wert) / (schwellenwert_schlecht - schwellenwert_gut) * 100

Für die Dividendenrendite, bei der höher besser ist, dreht sich die Formel um:

punkte = (kpi_wert - schwellenwert_schlecht) / (schwellenwert_gut - schwellenwert_schlecht) * 100

In beiden Fällen wird das Ergebnis auf den Bereich 0 bis 100 begrenzt.

Ich habe mich gegen ein einfaches Ampel-System (gut / mittel / schlecht) entschieden, weil es zu grob wäre. Ein KGV von 5 und ein KGV von 14 würden beide als "gut" gewertet, obwohl 5 deutlich günstiger ist. Die lineare Normalisierung behält diese Abstufung und lässt sich in der Präsentation besser begründen.


Die Schwellenwerte, die ich festgelegt habe

Beim Forward KGV und beim KGV gilt für mich ein Wert von 12 oder darunter als günstig. Das liegt deutlich unter dem historischen Durchschnittskurs des S&P 500, der langfristig bei etwa 15 bis 18 liegt. Ab einem Wert von 35 gilt die Aktie in meinem Modell als teuer bewertet, weil man dann eine erhebliche Wachstumsprämie zahlt.

Beim KBV habe ich 1,5 als gute Grenze festgelegt. Das bedeutet, der Markt bewertet das Unternehmen nur leicht über seinem bilanziellen Substanzwert. Ab einem KBV von 5 gilt die Bewertung in meinem Modell als hoch, weil man dann das Fünffache des Buchwertes zahlt.

Bei der Dividendenrendite gilt 4 Prozent als guter Wert, weil das deutlich über der durchschnittlichen Dividendenrendite des S&P 500 liegt, die historisch bei etwa 1,5 bis 2 Prozent liegt. 0 Prozent ist der schlechteste Wert, bedeutet aber keine Bestrafung, sondern nur keine Belohnung im Modell. Eine fehlende Dividende ist eine strategische Entscheidung, kein Fehler.

Eine wichtige Einschränkung: Diese Schwellenwerte sind bewusst branchenunabhängig. Ein KGV von 30 kann bei einem Technologieunternehmen mit hohem Wachstum völlig normal sein, bei einem Versorger wäre es schon ungewöhnlich teuer. Das Modell berücksichtigt keine Branchennormen, was ich in der kritischen Reflexion ansprechen werde.


Wie ich die Gewichtung festgelegt habe

Nachdem jeder KPI in Punkte übersetzt wurde, werden die vier Werte gewichtet und zu einem Gesamtscore addiert. Die Summe der Gewichte ergibt immer 100 Prozent.

Meine Standardgewichtung ist folgende: Forward KGV mit 35 Prozent, KGV mit 25 Prozent, KBV mit 20 Prozent und Dividendenrendite mit 20 Prozent.

Die Begründung dahinter ist, dass Aktien am Kapitalmarkt primär nach ihrer zukünftigen Ertragskraft bewertet werden. Deshalb bekommt das Forward KGV das höchste Gewicht, weil es die Markterwartung an die künftigen Gewinne abbildet. Das historische KGV ist wichtig als Kontrolle, denn Analystenschätzungen können stark vom tatsächlichen Ergebnis abweichen, deshalb bekommt es das zweitgrößte Gewicht. KBV und Dividendenrendite ergänzen das Bild um Substanz- und Ausschüttungsaspekte, sind aber aus meiner Sicht nachrangig gegenüber der Ertragsperspektive.


Warum die Gewichte in der App als Schieberegler einstellbar sind

Die Gewichte sind eine Modellannahme, keine objektive Wahrheit. Ein einkommensorientierter Anleger würde der Dividendenrendite deutlich mehr Gewicht geben als ein Wachstumsinvestor. Die Schieberegler in der App machen genau das sichtbar: das Ergebnis hängt vom Modell ab und nicht nur von den Daten. Wer die Regler verschiebt, sieht sofort, wie sich der Gesamtscore verändert. Das ist kein Fehler im Modell, sondern zeigt bewusst, dass jede Gewichtung eine Annahme ist.

In der App erscheint deshalb ein Hinweis: "Die Standardgewichte spiegeln eine gewinnorientierte Anlegerperspektive wider. Das Verschieben der Regler verändert den Gesamtscore und damit die Bewertungseinschätzung. Jede Gewichtung ist eine Annahme."


Wie ich den Gesamtscore interpretiere

Der Gesamtscore liegt immer zwischen 0 und 100 Punkten. Ab einem Score von 65 werte ich die Aktie als möglicherweise unterbewertet, zwischen 40 und 64 als fair bewertet und unter 40 als möglicherweise überbewertet.

Die 65-Grenze für "unterbewertet" liegt bewusst über der Mitte, weil eine Aktie bei gewinnorientierter Gewichtung in mehreren Dimensionen gleichzeitig günstig sein muss, um dieses Urteil zu verdienen. Die 40-Grenze für "überbewertet" liegt leicht unterhalb der Mitte, weil ein deutliches Signal in mehreren KPIs ausreicht, um auf eine teure Bewertung hinzuweisen.

Der Score ist kein Kauf- oder Verkaufssignal. Er ist ein formalisiertes Bewertungsmodell auf Basis von vier Kennzahlen zu einem Stichtag. Qualitative Faktoren wie Managementqualität, Wettbewerbssituation, Schuldenstruktur oder Branchentrends fließen nicht ein.
