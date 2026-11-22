# Plateaus: wenn gleich gut nicht fertig heißt – Streamlit-Demo

<!-- Nach dem Deploy direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-plateaus-landschaft-demo.streamlit.app/)** -->

Stück der Reihe **Landschaften, Einstellung und Vergleich** (Bereich Optimierung, Feld „Metaheuristiken und Suche“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo setzt an zwei Vorgängern an und hebt je eine ihrer Annahmen auf (beide Kanten sind Korrekturen einer Annahme): Das Stück über Rauigkeit nimmt an, dass jeder Zustand seinen eigenen Wert hat; das Stück über Einzugsgebiete nimmt an, dass jeder Start beim steilsten Abstieg zu genau einem lokalen Optimum gehört und dieses Optimum ein einzelner Zustand ist. Bei groben oder ganzzahligen Werten hängt der Endpunkt eines Abstiegs an der Gleichstandsregel, und ein „Optimum“ kann ein ganzes Plateau sein.

Fahrzeuge sind ein **NK-Modell mit wenigen ganzzahligen Stufen je Beitrag** und **Rundtouren auf einem ganzzahligen Gitter ohne Rauschen** (2-opt); Rundtouren mit Zufallskoordinaten sind die Kontrolle ohne Plateaus. Alle Instanzen sind erfunden (keine reale Datenquelle), alle Landschaften werden vollständig aufgezählt.

## Warum dieses Problem

„Anzahl lokaler Optima“ klingt wie eine Eigenschaft der Landschaft. Sind viele Nachbarn gleich gut, ist sie eine Eigenschaft der **Zählweise**: Ein Abstieg bleibt an einem Zustand stehen, der kein strikt besserer Nachbar hat, obwohl sein Plateau einen Ausgang hat. Die Kernfragen der Demo: Was ist ein Optimum, wenn Nachbarn gleich gut sind? Wie viel Neutralität entsteht wo? Hilft es, bei Gleichstand zufällig zu wählen oder seitwärts zu gehen, und was kostet es?

Nichts davon ist neu: Neutralität in Landschaften ist Lehrbuch- und Forschungsstoff. Die Demo macht den Stoff mit festen Zähleinheiten vorführbar.

## Modell

Eine Landschaft ist eine endliche Menge von Zuständen mit einem Wert je Zustand und einer Nachbarschaft in fester Zugreihenfolge. Die Formeln stehen im Expander „📐 Mathematische Formulierung“ der App.

- **Neutralitätsgrad ν:** Anteil der geordneten Nachbarpaare mit gleichem Wert. Zähleinheit: geordnetes Nachbarpaar.
- **Plateau:** Zusammenhangskomponente gleich guter Nachbarn mit mindestens zwei Zuständen. **Ausgang:** Ein Zustand des Plateaus hat einen strikt besseren Nachbarn.
- **Abstieg:** steilster Abstieg (bester Nachbar, nur bei strikter Verbesserung). **Erfolg eines Abstiegs:** Anteil aller Starts (gleichverteilt über die Zustände), die in einem Zustand mit dem besten Wert enden.
- **Auswertung:** Bewertung eines Nachbarn oder eines Startzustands. **Zählweise „voll“:** Jede Durchsuchung bewertet alle M Nachbarn, ohne Nachbarlisten und ohne Warteschlange; ein Abstieg kostet 1 + M · Durchsuchungen, auch die letzte ohne Verbesserung zählt. Andere Zählweisen sind Gegenstand des Stücks über Nachbarschaften.
- **NK-Modell:** N Bits, jeder der N Beiträge hängt an seinem Locus und K weiteren, zyklisch benachbarten (K zählt ohne den Locus selbst). **Stufen** ist die Zahl der ganzzahligen Werte je Beitrag (0 bis Stufen − 1); die Fitness ist die Summe der Beiträge und hat deshalb mehr als „Stufen“ verschiedene Werte. „Fein“ heißt 1 000 000 Stufen. Nachbar = ein Bit umgedreht, Zugreihenfolge Bit 0, 1, …, N − 1.
- **Gitter ohne Rauschen:** n verschiedene Zellen eines 4 × 4-Gitters mit Koordinaten 0 bis 3; alle (n − 1)!/2 Rundtouren; 2-opt mit n(n − 3)/2 Zügen in fester Reihenfolge. Längenmaß Manhattan (ganze Zahlen) oder euklidisch. Bei euklidischen Längen gelten zwei Touren als gleich lang, wenn ihre auf 1e-9 gerundeten Längen übereinstimmen („mit Toleranz“); „bitgenau“ vergleicht die Gleitkommazahlen selbst (Summe in Tourreihenfolge ab Stadt 0).
- **Zufallskoordinaten:** die vier Punktfamilien der Reihe (gleichverteilt, geclustert, Gitter mit Rauschen, Straßennetz) mit ganzzahligen Koordinaten 0 bis 9999, euklidisch, mit Toleranz.

Zählweisen des Optimums (dieselbe Tabelle wie in der App):

| Zählweise | Bedingung | Zähleinheit |
|---|---|---|
| **schwaches Optimum** | kein Nachbar ist strikt besser | Zustand |
| **strenges Optimum** | alle Nachbarn sind strikt schlechter | Zustand |
| **geschlossenes Plateau** | zusammenhängende Menge gleich guter Zustände, von denen keiner einen strikt besseren Nachbarn hat (auch ein einzelner Zustand) | Plateau |
| **Scheinoptimum** | schwaches Optimum auf einem Plateau mit Ausgang: irgendein Zustand des Plateaus hat einen strikt besseren Nachbarn | Zustand |

Gleichstandsregeln (dieselbe Tabelle wie in der App):

| Regel | Bei mehreren besten Nachbarn | Ohne strikt besseren Nachbarn |
|---|---|---|
| **R0** fester Gleichstand | der erste in der festen Zugreihenfolge | bleibt stehen |
| **R1** zufälliger Gleichstand | ein zufälliger unter den besten (gleichverteilt) | bleibt stehen |
| **R2** Seitwärtsschritte | wie R1 | geht zu einem zufälligen gleich guten Nachbarn, höchstens S Schritte hintereinander; jede Verbesserung setzt den Zähler zurück |

In den Messreihen ist die Seitwärtsgrenze S = 50.

## Methodik

- **Vollständige Aufzählung** statt Stichprobe: NK-Modell bis N = 16 (65 536 Zustände), Rundtour bis n = 10 (181 440 Touren; in der App bis n = 9, das sind 20 160 Touren mit je 27 Nachbarn).
- **Plateaus** durch Ausbreitung der kleinsten Zustandsnummer über Gleichheitskanten.
- **Erfolg und Kosten der drei Regeln exakt** (Erwartungswert über alle Zufallsentscheidungen): Die Gleichungen aus dem Formel-Expander werden wiederholt eingesetzt, bis sich nichts mehr ändert.
- **Festes Budget als Stichprobe:** Abstieg mit Neustarts (Neustart = gleichverteilter Zustand, 1 Auswertung), bis die nächste Aktion nicht mehr ins Budget passt; 100 Läufe je Instanz und Regel; Lücke = Abstand des besten besuchten Zustands zum Optimum in Prozent des Betrags des Optimums; 95-%-Intervall durch Bootstrap über die 30 Instanzen (2 000 Ziehungen).
- **Messreihen:** je Zelle 30 Instanzen mit festen Zufalls-Seeds (Strom A: 100000 bis 100029). Gegenprobe in einem zweiten Zufallsstrom (Strom B: 200000 bis 200029) für die Stufenreihe, NK mit N = 14, Gitter und Zufallskoordinaten mit n = 8 und 9, das Budget (NK und Gitter mit n = 9) und den stetigen Ausblick; NK mit N = 16 und Rundtouren mit n = 10 sind nur in Strom A gemessen. Zufall aus SplitMix64; Instanzen der Zufallskoordinaten und des NK-Modells aus der gemeinsamen Basis der Reihe (`pll_basis.py`, unveränderte Kopie).
- Die Messreihen liegen eingefroren in `data/pll_*.json` (Quelle, Stand und Parameter je Datei) und werden mit `tools/pll_make_frozen.py` und `tools/pll_make_stetig.py` erzeugt; die App rechnet die gewählte Landschaft live.

Die App hat acht Presets: „Von Hand (Würfel, 8 Zustände)“, „Von Hand (Tour, 7 Städte)“, „NK grob (3 Stufen)“, „NK fein (Kontrolle)“, „Gitter Manhattan n = 9“, „Gitter euklidisch n = 9“, „Zufallskoordinaten“ und „Würfel: Seitwärts ohne Nutzen“.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen gelten für diese Modelle und Größen (NK mit N = 14 und 16, Rundtour mit n = 8 bis 10), steilsten Abstieg, Zählweise „voll“, S = 50, Mittel über 30 Instanzen je Zelle (Strom A), wenn nichts anderes dasteht.

### Von Hand

- **Würfel** (drei Bits, Werte 2, 2, 1, 4, 2, 0, 3, 2 für 000 bis 111, größer ist besser): ν = 4/24 = 1/6; drei schwache, zwei strenge Optima, aber zwei geschlossene Plateaus; 000 ist ein Scheinoptimum (Plateau {000, 001, 100} mit Ausgang). Erfolg 1/2 (R0), 7/12 (R1) und 31/48 (R2); Auswertungen je Abstieg 6,25 (R0 und R1) und 7 (R2), also 12,5 gegen 10,84 Auswertungen je Treffer: Hier lohnt der Seitwärtsschritt knapp.
- **Würfel mit den Werten 0, 0, 1, 2, 1, 0, 0, 2** und S = 3: Erfolg 7/8 (R0) gegen 13/16 (R1 und R2). Unter allen 6 305 Wertetabellen des Würfels mit Werten 0 bis 2 und Maximum 2 liegt R2 nie unter R1, aber in 56 von 6 305 unter R0.
- **Tour mit 7 Städten** (Gitterpunkte, Manhattan, 2-opt): 360 Touren mit je 14 Nachbarn, ν = 4/15, acht Plateaus, das größte mit 80 Touren; zwei schwache Optima, ein strenges, ein geschlossenes Plateau. Die zweite Falle (Länge 16 statt 14) liegt auf einem Plateau mit vier Touren und Ausgang.

### Wie viel Neutralität

| Frage | Befund |
|---|---|
| NK grob (3 und 4 Stufen, N = 14 und 16, K = 2, 4, 8: 12 Zellen) | ν = 0,083 bis 0,192; 69 bis 97 % der Zustände haben mindestens einen gleich guten Nachbarn; das größte Plateau umfasst im Zellenmittel 0,3 bis 9,9 % des Zustandsraums |
| NK fein (1 000 000 Stufen, 6 Zellen) | Mittel von ν in jeder Zelle unter 0,00001; größter Neutralitätsgrad einer der 180 feinen Instanzen: 0,000009 (ein einzelnes gleich gutes Nachbarpaar); schwache = strenge Optima in allen feinen Instanzen |
| Gitter ohne Rauschen, n = 8 / 9 / 10 | Manhattan: ν = 0,347 / 0,351 / 0,352; euklidisch mit Toleranz: ν = 0,036 / 0,037 / 0,038; euklidisch bitgenau: ν = 0,031 / 0,031 / 0,031 |
| Gitter Manhattan: schwach, aber nicht streng | 98,6 bis 99,9 % der schwachen Optima sind nicht streng (n = 8 bis 10, Quotient der Zellenmittel) |
| Zufallskoordinaten (vier Familien, n = 8, 9, 10) | in 0 von 360 Instanzen weicht die Zahl der schwachen von der der strengen Optima ab, und ν ist in jeder dieser Instanzen genau 0; Gegenprobe mit anderen Instanzen (n = 8 und 9): in 0 von 240 Instanzen |

**Ein Regler, kein Schalter** (NK, N = 14, K = 4, 30 Instanzen je Zeile; die Tabellen der Beiträge sind je Stufenzahl andere, also kein kontrollierter Einzelvergleich):

| Stufen je Beitrag | ν | Zustände mit gleich gutem Nachbarn (Anteil) | schwache Optima | strenge | geschlossene Plateaus | Scheinoptima-Anteil |
|---|---|---|---|---|---|---|
| 2 | 0,2454 | 0,976 | 419,4 | 16,8 | 27,2 | 0,886 |
| 3 | 0,1518 | 0,895 | 237,6 | 32,6 | 44,8 | 0,733 |
| 4 | 0,1125 | 0,806 | 181,0 | 42,1 | 52,7 | 0,628 |
| 6 | 0,0740 | 0,655 | 148,2 | 57,3 | 66,9 | 0,464 |
| 10 | 0,0445 | 0,469 | 125,3 | 71,7 | 78,6 | 0,312 |
| 30 | 0,0140 | 0,179 | 94,3 | 78,0 | 80,4 | 0,119 |
| 1 000 | 0,0003 | 0,005 | 93,4 | 93,1 | 93,2 | 0,002 |
| 1 000 000 | 0,0000 | 0,000 | 95,2 | 95,2 | 95,2 | 0,000 |

Im zweiten Zufallsstrom weicht ν in jeder Zeile um höchstens 0,006 ab, und die Reihenfolge ist dieselbe.

**Gleich ist eine Entscheidung** (Gitter euklidisch, ν bitgenau gegen mit Toleranz): n = 8: 0,0307 gegen 0,0362; n = 9: 0,0308 gegen 0,0366; n = 10: 0,0311 gegen 0,0379. Der bitgenaue Vergleich übersieht 15 bis 18 % der Gleichstände, weil mathematisch gleiche Summen als Gleitkommazahlen im letzten Bit verschieden sein können ((0,1 + 0,2) + 0,3 ≠ 0,1 + (0,2 + 0,3)).

### Was zählt als Optimum

Schwache Optima je geschlossenem Plateau (Quotient der Zellenmittel): 1,9 bis 18,3 bei NK (12 grobe Zellen) und 1,7 bis 154,0 auf dem Gitter (6 Zellen: Manhattan und euklidisch mit Toleranz). Beispiele: NK mit N = 16, 3 Stufen, K = 2 hat im Mittel 206,6 schwache, 4,1 strenge Optima und 11,3 geschlossene Plateaus; das Gitter mit Manhattan-Längen und n = 10 hat 174,6 schwache Optima gegen 1,1 geschlossene Plateaus. Bei NK sind im Zellenmittel 41 bis 83 % der schwachen Optima Scheinoptima.

### Wer entscheidet beim Gleichstand

| Zelle | Erfolg R0 | R1 | R2 | Auswertungen je Abstieg R0 / R2 | Treffer je 1 000 Auswertungen R0 / R2 |
|---|---|---|---|---|---|
| N = 14, 3 Stufen, K = 2 | 0,2476 | 0,2404 | 0,5024 | 67,2 / 632,4 | 3,69 / 0,79 |
| N = 14, 3 Stufen, K = 4 | 0,0860 | 0,0865 | 0,1828 | 55,1 / 355,0 | 1,56 / 0,51 |
| N = 14, 3 Stufen, K = 8 | 0,0196 | 0,0198 | 0,0300 | 42,5 / 193,4 | 0,46 / 0,16 |
| N = 16, 3 Stufen, K = 2 | 0,2003 | 0,1974 | 0,4624 | 84,2 / 706,0 | 2,38 / 0,65 |
| N = 16, 4 Stufen, K = 2 | 0,1703 | 0,1690 | 0,4100 | 89,3 / 549,6 | 1,91 / 0,75 |
| N = 16, fein, K = 2 | 0,2163 | 0,2163 | 0,2163 | 109,4 / 109,4 | 1,98 / 1,98 |

(„Treffer je 1 000 Auswertungen“ ist der Quotient der beiden Zellenmittel mal 1 000. Alle 18 Zellen zeigt die App.)

- **Zufälliger Gleichstand (R1 gegen R0), 12 grobe NK-Zellen:** Zellenmittel -0,0072 bis +0,0022, je Instanz -0,059 bis +0,033 (Strom B: -0,045 bis +0,044). Das ist die beobachtete Spanne in diesen Instanzen, keine Grenze.
- **Seitwärtsschritte (R2 gegen R0), 12 grobe NK-Zellen:** Erfolg im Zellenmittel um +0,0042 bis +0,2621 höher, je Instanz -0,0010 bis +0,680. R2 liegt in einzelnen Instanzen unter R0: in 3 der 12 Zellen (8 von 360 Instanzen) in Strom A; in Strom B (nur N = 14) in 5 der 6 Zellen (6 von 180 Instanzen). Unter R1 liegt R2 in keiner Instanz (das folgt aus der Bauart: R2 geht denselben Weg wie R1, bis R1 stehen bleibt).
- **Kosten:** Ein R2-Abstieg kostet das 3,5- bis 9,4-Fache an Auswertungen; je 1 000 Auswertungen trifft R0 2,5- bis 4,6-mal so oft wie R2 (Quotient der Zellenmittel).
- **Fein:** In allen sechs feinen Zellen sind die drei Regeln im Zellenmittel gleich (Differenz 0).
- **Gitter:** Erfolg von R2 gegen R0 im Zellenmittel für n = 8 / 9 / 10: Manhattan +0,249 / +0,343 / +0,411, euklidisch mit Toleranz +0,065 / +0,103 / +0,210. Mit Manhattan-Längen trifft R2 in jeder der 90 Instanzen fast immer (Erfolg mindestens 0,99996), kostet aber Manhattan das 10,9 / 9,3 / 10,0-Fache an Auswertungen. Auch hier liegt R2 in 6 von 90 euklidischen Gitter-Instanzen unter R0.
- R0 hängt an der Zugreihenfolge: Ein Umnummerieren der Bits ändert den Erfolg von R0, nicht den von R1 und R2 (Eigenschaftstest).

### Bei festem Budget

NK-Modell, N = 14, 3 Stufen; Budget in Auswertungen (20, 120, 600 und 3 000 mal M = 14); Lücke in Prozent; R2 − R0 mit 95-%-Intervall; letzte Spalte: Instanzen (von 30), in denen R2 die kleinere mittlere Lücke hat.

| K | Budget | Lücke R0 | Lücke R2 | R2 − R0 [95-%-Intervall] | Läufe am Optimum R0 / R2 | R2 besser |
|---|---|---|---|---|---|---|
| 2 | 280 | 2,102 | 3,181 | +1,078 [+0,635; +1,563] | 0,63 / 0,53 | 6 |
| 2 | 1 680 | 0,071 | 0,941 | +0,870 [+0,554; +1,214] | 0,98 / 0,82 | 0 |
| 2 | 8 400 | 0,000 | 0,055 | +0,055 [+0,007; +0,121] | 1,00 / 0,99 | 0 |
| 2 | 42 000 | 0,000 | 0,000 | 0,000 [0,000; 0,000] | 1,00 / 1,00 | 0 |
| 4 | 280 | 4,839 | 6,163 | +1,325 [+1,070; +1,591] | 0,31 / 0,30 | 0 |
| 4 | 1 680 | 0,823 | 2,564 | +1,741 [+1,369; +2,139] | 0,82 / 0,58 | 0 |
| 4 | 8 400 | 0,005 | 0,334 | +0,328 [+0,172; +0,509] | 1,00 / 0,93 | 0 |
| 4 | 42 000 | 0,000 | 0,004 | +0,004 [0,000; +0,012] | 1,00 / 1,00 | 0 |
| 8 | 280 | 8,231 | 10,191 | +1,959 [+1,653; +2,254] | 0,12 / 0,09 | 0 |
| 8 | 1 680 | 2,846 | 5,966 | +3,119 [+2,797; +3,475] | 0,47 / 0,23 | 0 |
| 8 | 8 400 | 0,312 | 1,789 | +1,477 [+1,125; +1,900] | 0,92 / 0,65 | 0 |
| 8 | 42 000 | 0,001 | 0,138 | +0,137 [+0,052; +0,247] | 1,00 / 0,97 | 0 |

Bilanz über die 12 Zellen: R2 ist im Mittel in 0 von 12 Zellen besser, in 11 schlechter, in 1 gleich; das 95-%-Intervall liegt in 10 Zellen ganz über 0 (alle 9 Zellen mit 280, 1 680 und 8 400 Auswertungen und K = 8 bei 42 000). In beiden Zufallsströmen ist die Bilanz dieselbe; welche der beiden Zellen K = 2 und K = 4 bei 42 000 Auswertungen genau gleich ist, wechselt.

Auf dem **Gitter mit Manhattan-Längen** ist es umgekehrt: n = 9, 540 Auswertungen: 0,42 % (R0) gegen 0,01 % (R2), Differenz -0,41 [-0,68; -0,17]; n = 10, 700 Auswertungen: 0,86 % (R0) gegen 0,09 % (R2), Differenz -0,77 [-1,11; -0,47] (n = 10 nur Strom A). Beim sechsfachen Budget (120 · M) sind alle Regeln in allen Läufen am Optimum: Dieses Budget unterscheidet nichts. Die Richtung hängt an Landschaft und Budget.

Deutung, nicht gemessen: Ein R2-Abstieg kann nicht wissen, dass er am Ziel ist, und geht auch auf dem Plateau des globalen Optimums bis zu S Schritte weiter.

### Ausblick: stetige Landschaften (nicht Gegenstand dieses Stücks)

Exakt ist nur ein Baukasten-Beispiel: f(x) = Σ cos xᵢ hat 2^d stationäre Punkte, davon 2^d − 2 Sattelpunkte; der Sattelanteil 1 − 2^(1−d) ist 0,5 / 0,875 / 0,992 bei d = 2 / 4 / 8. Das ist eine kombinatorische Tatsache dieser Funktion, kein Befund über Landschaften allgemein.

Stichprobe an 10 erfundenen Funktionen je Zeile, jede die Summe von 20 Gauß-Kuppen (300 Starts je Funktion und Verfahren, Strom A): Anteil der Sattelpunkte unter den stationären Punkten, die das genannte Suchverfahren aus diesen Starts gefunden hat.

| d | Suchverfahren | Starts mit Konvergenz | gefundene Punkte je Instanz | Sattelanteil unter den gefundenen |
|---|---|---|---|---|
| 2 | Newton | 49,3 % | 19,1 | 0,47 |
| 2 | Levenberg-Marquardt | 46,3 % | 19,1 | 0,47 |
| 4 | Newton | 8,2 % | 17,9 | 0,83 |
| 4 | Levenberg-Marquardt | 9,3 % | 18,1 | 0,85 |
| 8 | Newton | 1,2 % | 3,2 | 0,98 |
| 8 | Levenberg-Marquardt | 0,1 % | 0,4 | 1,00 |

Strom B bei d = 4: 0,78 (Newton) gegen 0,82 (Levenberg-Marquardt). Bei gleichen Starts liegen die beiden Suchverfahren bei d = 2 und d = 4 um höchstens 0,05 auseinander (beide Zufallsströme). Die Zahl hängt aber an der Zahl der Starts: Mit 3 000 statt 300 Starts findet das Newton-Verfahren bei d = 4 in denselben Instanzen 49,5 statt 17,9 Punkte je Instanz, Sattelanteil 0,73 statt 0,83 (Strom B: 0,69 statt 0,78). Bei d = 8 konvergiert nur ein kleiner Teil der Starts; Levenberg-Marquardt findet dort nur in 4 von 10 Instanzen überhaupt einen Punkt. Bei d = 8 stützen sich die Anteile auf wenige Punkte (Strom A: Newton 0,98, Strom B: 0,89). Die Demo macht keine Aussage über höhere Dimensionen und keine über neuronale Netze.

## Zahl → Test

| Zahl oder Aussage | Test | Art |
|---|---|---|
| Handbeispiele (Würfel, Würfel ohne Nutzen, Tour, Gleitkomma, Kosinus), 56 von 6 305 | `tests/test_handbeispiele.py`, `tests/test_claims.py::test_handbeispiele_der_readme_exakt` | exakt |
| Zählungen (20 160, 27, 181 440, 65 536) | `tests/test_claims.py::test_zaehlungen_der_readme` | exakt |
| Alle Zahlen der Tabellen und Spannen in „Befunde“ | `tests/test_claims.py::test_jeder_baustein_aus_den_messreihen_steht_woertlich_in_der_readme` | Datei: aus `data/pll_*.json` formatiert, nicht neu gerechnet |
| Die Dateien passen zur Rechnung | `tests/test_messung.py` (einzelne Instanzen und zwei ganze Zellen neu gerechnet) | Band, relativ 1e-9 |
| Richtung und Größenordnung im zweiten Zufallsstrom | `tests/test_claims.py::test_band_die_aussagen_gelten_auch_im_zweiten_zufallsstrom` | Band |
| Erfolg und Kosten der Regeln | `tests/test_oracle_regeln.py` (Rekursion mit Brüchen, Stichprobe, Python-Schleife) | exakt bis 1e-12 |
| Gezählte Auswertungen, Budget-Läufe | `tests/test_zaehlung.py` (Handzählung, Python-Schleife Lauf für Lauf) | exakt |
| Stetiger Ausblick, Gauß-Kuppen | kein Neu-Rechnen im Test (braucht scipy und Minuten); `tools/pll_make_stetig.py --check` vergleicht als Band | Messung dieser README |

Die vollständigen Messreihen rechnet kein Test neu (Rechenzeit rund 20 Minuten); dafür gibt es `tools/pll_make_frozen.py --check <Teil>`.

## Ehrliche Grenzen

- Alle Aussagen gelten für diese Modelle, Größen und Parameter. Größere Räume (NK mit N > 16, Rundtouren mit n > 10) sind nicht gemessen.
- Nur steilster Abstieg und Zählweise „voll“. Die Abstiegsregel „zufällig verbessernd“ ist ein anderer Regler als R1 (R1 wählt nur unter den gleich guten besten Nachbarn) und Gegenstand des Stücks über Einzugsgebiete.
- Die Seitwärtsgrenze ist in den Messreihen 50; andere Grenzen zeigt die App nur an der gewählten Landschaft.
- Das Gitter ohne Rauschen ist eine eigene Familie dieses Stücks; die Zufallsfamilien der Reihe haben in den gemessenen Instanzen keine Plateaus.
- Die Budget-Zahlen sind Stichproben; die Läufe mit kleinerem Budget sind die Anfänge der Läufe mit größerem Budget (nicht unabhängig).
- Der Vergleich über die Stufenzahl ist nicht kontrolliert (andere Tabellen je Stufenzahl).

## Befunde und Korrekturen gegenüber dem Plan

Der Plan nannte Erwartungen aus einer Vormessung mit anderen Instanzen (anderer Zufallsgenerator, anderer Instanzbau). Im Bau neu gemessen:

| Aussage | Erwartung des Plans (Vormessung) | Im Bau gemessen |
|---|---|---|
| ν bei NK grob | 0,084 bis 0,214 (mit N = 18) | 0,083 bis 0,192 (N = 14 und 16; N = 18 hier nicht gemessen) |
| ν gegen Stufen (N = 14, K = 4) | 0,26 / 0,015 / 0,0004 bei 2 / 30 / 1 000 Stufen | 0,245 / 0,014 / 0,0003; dieselbe Richtung |
| NK fein | „ν = 0, keine Plateaus“ | im Zellenmittel unter 0,00001, aber nicht in jeder Instanz genau 0 (ein gleich gutes Nachbarpaar kommt vor); schwache = strenge Optima in allen feinen Instanzen |
| Schwache Optima je geschlossenem Plateau | NK 1,9 bis 35 (mit N = 18), Gitter 1,7 bis 156 | NK 1,9 bis 18,3, Gitter 1,7 bis 154,0 |
| Beispielzelle N = 16, 3 Stufen, K = 2 | 198 schwache, 2,3 strenge, 7,9 geschlossene | 206,6 / 4,1 / 11,3 |
| Zufälliger Gleichstand, je Instanz | −0,037 bis +0,045 („keine Grenze“) | -0,059 bis +0,033 (Strom A), -0,045 bis +0,044 (Strom B): die Spanne ist tatsächlich keine Grenze |
| Seitwärtsschritte, Zellenmittel | +0,005 bis +0,32 | +0,0042 bis +0,2621 |
| R2 unter R0 in einzelnen Instanzen | in 3 von 12 Zellen, kleinster Wert −0,0016 | Strom A: 3 von 12 Zellen (8 Instanzen); Strom B: 5 von 6 Zellen (6 Instanzen), kleinster Wert -0,0101. Häufiger und deutlicher als erwartet |
| Ankerzelle N = 14, 3 Stufen, K = 2 | Erfolg 0,2226 / 0,2225 / 0,5276; 65,6 gegen 625,1 Auswertungen | 0,2476 / 0,2404 / 0,5024; 67,2 gegen 632,4 |
| Kosten und Treffer | Kosten 3,8- bis 9,5-fach; R0 trifft 2,7- bis 4,5-mal so oft | 3,5- bis 9,4-fach; 2,5- bis 4,6-mal |
| Gitter, Erfolg von R2 gegen R0 | „bis +0,38“ | im Zellenmittel bis +0,411 (Manhattan, n = 10); neu: mit Manhattan-Längen trifft R2 in jeder der 90 Instanzen mit mindestens 0,99996 |
| Toleranz | der bitgenaue Vergleich übersieht 10 bis 13 % (n = 8, 9) | 15 bis 18 % (n = 8, 9, 10; n = 10 neu gemessen) |
| Zufallskoordinaten | 270 Instanzen aus drei Familien, ν nicht gemessen | 360 Instanzen aus vier Familien und 240 weitere als Gegenprobe; ν ist in jeder genau 0 |
| Festes Budget, NK | in 0 von 12 Zellen besser, 11 schlechter, 1 gleich, Intervall über 0 in 10 | dieselbe Bilanz in beiden Zufallsströmen; die Zahlen je Zeile weichen ab |
| Festes Budget, Gitter (20 · M) | n = 9 / 10: 0,53 / 0,86 % (R0) gegen 0,03 / 0,02 % (R2) | 0,42 / 0,86 % gegen 0,01 / 0,09 % |
| **Stetiger Ausblick (gedrehter Befund)** | „die Zahl hängt am Suchverfahren“ (d = 4: 0,71 Newton gegen 0,87 Levenberg-Marquardt, aber mit 4 000 gegen 400 Starts) | Bei **gleichen** Starts liegen die Verfahren nah beieinander (0,83 gegen 0,85); dagegen ändert die **Zahl der Starts** den Anteil (0,73 mit 3 000 Starts in denselben Instanzen). Dass der Unterschied der Vormessung daher stammt, ist eine Deutung, nicht gemessen. Gebaut ist der gemessene Befund |
| Eigenschaft „Umnummerieren ändert nur die Namen“ | für alle Zahlen | gilt für Kennzahlen, R1 und R2; **nicht für R0** (die feste Zugreihenfolge ist dort eine Stellschraube) |

Abweichungen im Zuschnitt der App: acht statt sieben Presets (neu „Würfel: Seitwärts ohne Nutzen“); NK-Länge N von 10 bis 16 (Plan: 8 bis 16), damit K bis 8 in jede Länge passt; die acht Würfelwerte stehen in einem Textfeld; Experiment 5 zeigt die vier festen Budgets der Messreihe und rechnet die gewählte Landschaft auf Knopfdruck nach (kein frei wählbares Budget); das Gitter mit n = 10 gibt es nur als Messreihe. In der Budget-Stichprobe sind die Läufe mit kleinerem Budget die Anfänge der Läufe mit größerem Budget.

## Tests

161 Tests in 17 Dateien; Laufzeit rund 160 Sekunden mit zwei Prozessen (`pytest tests -n 2`), eine Messung unter Last.

- **Handbeispiele (9):** Würfel, Würfel ohne Nutzen (auch alle 6 305 Wertetabellen), Tour mit 7 Städten, Gleitkomma-Gleichheit, Summe von Kosinus; die erwarteten Werte stehen als Handrechnung im Test.
- **Orakel (23):** Regeln gegen eine unabhängige Rekursion über alle Zufallsentscheidungen mit Brüchen (Seitwärtsgrenzen 0, 1, 3, 50), gegen eine Stichprobe einzelner Abstiege (Band von 4,5 Standardfehlern) und gegen eine Python-Schleife; Plateaus gegen `scipy.sparse.csgraph` und Union-Find; NK-Fitness und Tourlängen gegen die Basis; 2-opt-Nachbarn gegen Kantenmengen; kürzeste Tour gegen das Bellman-Held-Karp-Verfahren. Beim Bau zusätzlich 260 Zufallsinstanzen mit 3 120 Prüfungen ohne Fehler (nicht im Repo).
- **Eigenschaften (8):** streng monotone Transformation, Umnummerieren von Bits und Städten, R2 mit S = 0 gleich R1, ohne Gleichstand alle Regeln gleich, R2 nie unter R1, Ordnung der Zählweisen.
- **Randfälle (10):** alle Werte gleich, ein Bit, ein einzelner Zustand, genau ein Gleichstandspaar, mehrere globale Optima, Rauschen unter der Toleranz, Grenzen der Fahrzeuge, Eingabe der Würfelwerte.
- **Zähltest (8):** Auswertungen am Würfel von Hand; die Budget-Läufe stimmen Lauf für Lauf mit einer Python-Schleife überein, die jede Auswertung einzeln zählt.
- **Messreihen (9) und Claims (4):** Aufbau der Dateien, Neu-Rechnen einzelner Instanzen als Band, jede Zahl dieser README, Gegenprobe im zweiten Zufallsstrom.
- **Verdikte (20), Presets (8), Layout (23), App (19), Texte (6), Footer (2), Laufzeit-Importe (1), Kopie-Test der Basis (4), Neuladen der Hilfsmodule (7).**

Keine Mutationstests. Die App ist im Browser mit allen acht Presets und der Live-Rechnung bei festem Budget durchgeklickt (keine Fehlermeldung, keine fehlerhafte Formel); einzelne Regler wurden im Browser nicht von Hand bewegt, das deckt nur AppTest ab.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `data/pll_*.json` | eingefrorene Messreihen mit Quelle, Stand und Parametern |
| `modul_frisch.py` | lädt geänderte Hilfsmodule nach einem Update neu |
| `pll_basis.py` | gemeinsame Basis der Reihe (unveränderte Kopie): Punktfamilien, NK-Modell, Zufalls-Seeds, Zählregeln |
| `pll_constants.py` | Regler-Grenzen, Auswahllisten, Farben, Presets, Erklärtabellen |
| `pll_evaluation.py` | Einstellungen, Analyse der gewählten Landschaft, Laden der Messreihen, Verdikte |
| `pll_landscape.py` | Neutralitätsgrad, Plateaus, Zählweisen des Optimums |
| `pll_layout.py` | Fester Kopf (Stylesheet) |
| `pll_messung.py` | Messreihen: Zellen, Zusammenfassung, Bootstrap, Budget |
| `pll_presets.py` | Permalink (Begrenzen, Einrasten), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `pll_rng.py` | SplitMix64 (Kopie der Vorlage des Portfolios) |
| `pll_rules.py` | Gleichstandsregeln R0, R1, R2 exakt; Stichprobe bei festem Budget |
| `pll_scenario.py` | Fahrzeuge: Würfel, NK-Modell, Rundtouren mit 2-opt |
| `pll_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur Gegenproben und `tools/pll_make_stetig.py`) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handbeispiele, Orakel, Eigenschaften, Randfälle, Zähltest, Messreihen, Claims, Verdikte, Presets, Layout, App, Texte, Footer, Laufzeit-Importe, Kopie-Test der Basis, Neuladen der Hilfsmodule |
| `tools/pll_make_frozen.py` | erzeugt und prüft (`--check`) die Messreihen |
| `tools/pll_make_stetig.py` | erzeugt und prüft (`--check`, Band) die Stichprobe des stetigen Ausblicks |

## Bewusst nicht umgesetzt

🚧 Nicht enthalten und nicht gemessen:

- Plateaus bei anderen Nachbarschaften als „ein Bit umdrehen“ und 2-opt (zum Beispiel Or-opt).
- Zählweisen außer „voll“ (Nachbarlisten, Warteschlange) und Abstiegsregeln außer dem steilsten Abstieg.
- Rundtouren mit mehr als zehn Städten; gerundete Entfernungen bei Zufallskoordinaten (etwa auf ganze Kilometer), der naheliegende Praxisfall.
- NK-Modell mit N = 18 (in der Vormessung für die Plateau-Maße gemessen, hier nicht) und Seitwärtsgrenzen außer 50 als Messreihe.
- Der Budget-Vergleich exakt statt als Stichprobe; der Anteil der Seitwärtsschritte, die am Optimum selbst anfallen.
- Fitness-Distanz-Zusammenhänge bei Neutralität.
- Sattelpunkte als eigener Gegenstand: Der stetige Teil ist nur der gekennzeichnete Ausblick.
- Ein PDF-Export.

## Quellen

Stufe nach der Quellenliste der Reihe: „gelesen“ heißt im Volltext gelesen, sonst steht dabei, was gelesen wurde.

- C. M. Reidys, P. F. Stadler: Combinatorial landscapes. SIAM Review 44 (2002), doi 10.1137/S0036144501395952. Nur die Kurzfassung gelesen; Jahrgang und Seiten nicht an der Quelle geprüft. Übersicht zur Theorie der Landschaften.
- G. Ochoa, N. Veerapen: Mapping the global structure of TSP fitness landscapes. Journal of Heuristics 24(3), 265–294 (2018, online 2017), doi 10.1007/s10732-017-9334-0. Nur die Kurzfassung gelesen; sie berichtet hohe Neutralität bei strukturierten TSP-Instanzen. Ob damit regelmäßige Gitter gemeint sind, ist nicht geprüft.
- L. Altenberg: NK Fitness Landscapes. In: Handbook of Evolutionary Computation, Oxford University Press 1997 (Abschnitt B2.7.2). Gelesen (Text stellenweise durch Texterkennung verstümmelt). Daraus die Konvention, dass K die weiteren Loci zählt; das NK-Modell selbst geht auf S. A. Kauffman und E. D. Weinberger (1989) zurück, nicht gelesen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
