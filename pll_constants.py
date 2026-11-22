"""Konstanten: Regler-Grenzen, Auswahllisten, feste Annahmen, Farben, Presets und Erklärtabellen."""

FAHRZEUGE = ("wuerfel", "tour7", "nk", "gitter", "zufall")
FAHRZEUG_TEXT = {
    "wuerfel": "Würfel mit drei Bits (von Hand)",
    "tour7": "Rundtour mit 7 Städten (von Hand)",
    "nk": "NK-Modell mit Stufen",
    "gitter": "Rundtour auf dem Gitter ohne Rauschen",
    "zufall": "Rundtour mit Zufallskoordinaten",
}
METRIKEN = ("manhattan", "euklid")
METRIK_TEXT = {"manhattan": "Manhattan (ganzzahlig)", "euklid": "euklidisch"}
GLEICHHEIT = ("toleranz", "streng")
GLEICHHEIT_TEXT = {"toleranz": "mit Toleranz (auf 1e-9 gerundet)", "streng": "streng (Gleitkommazahlen bitgenau)"}
FAMILIEN = ("gleich", "cluster", "gitter", "netz")
FAMILIE_TEXT = {"gleich": "gleichverteilt", "cluster": "geclustert", "gitter": "Gitter mit Rauschen", "netz": "Straßennetz"}
STUFEN = (2, 3, 4, 6, 10, 30, 1000, 1000000)

N_MIN, N_MAX, DEFAULT_N = 10, 16, 14
K_MIN, K_MAX, DEFAULT_K = 0, 8, 2          # K_MAX < N_MIN: K zählt die weiteren Loci
STAEDTE_MIN, STAEDTE_MAX, DEFAULT_STAEDTE = 6, 9, 9
SEIT_MIN, SEIT_MAX, DEFAULT_SEIT = 0, 50, 50
SEED_MAX, DEFAULT_SEED = 999999, 100000
DEFAULT_STUFEN = 3
WUERFEL_STANDARD = "2, 2, 1, 4, 2, 0, 3, 2"
WUERFEL_OHNE_NUTZEN = "0, 0, 1, 2, 1, 0, 0, 2"
WUERFEL_WERT_MIN, WUERFEL_WERT_MAX = -99, 99
BUDGET_C = (20, 120, 600, 3000)             # Budgets in Vielfachen der Nachbarzahl M
BUDGET_LAEUFE_LIVE = 100

COLOR_STRENG = "#2F6B65"
COLOR_SCHEIN = "#d9822b"
COLOR_PLATEAU = "#e8c15a"
COLOR_SONST = "rgba(150,150,150,0.75)"
COLOR_LINE = "#4c78a8"
COLOR_R = {"R0": "#4c78a8", "R1": "#9aa7b8", "R2": "#d9822b"}

_BASIS = {"fahrzeug": "wuerfel", "wuerfel": WUERFEL_STANDARD, "n": DEFAULT_N, "k": DEFAULT_K, "stufen": DEFAULT_STUFEN,
          "staedte": DEFAULT_STAEDTE, "metrik": "manhattan", "gleichheit": "toleranz", "familie": "gleich", "seed": DEFAULT_SEED,
          "seit": DEFAULT_SEIT}

PRESETS = {
    "Von Hand (Würfel, 8 Zustände)": dict(_BASIS),
    "Von Hand (Tour, 7 Städte)": dict(_BASIS, fahrzeug="tour7"),
    "NK grob (3 Stufen)": dict(_BASIS, fahrzeug="nk"),
    "NK fein (Kontrolle)": dict(_BASIS, fahrzeug="nk", stufen=1000000),
    "Gitter Manhattan n = 9": dict(_BASIS, fahrzeug="gitter", metrik="manhattan"),
    "Gitter euklidisch n = 9": dict(_BASIS, fahrzeug="gitter", metrik="euklid"),
    "Zufallskoordinaten": dict(_BASIS, fahrzeug="zufall", seed=0),
    "Würfel: Seitwärts ohne Nutzen": dict(_BASIS, wuerfel=WUERFEL_OHNE_NUTZEN, seit=3),
}
PRESET_HELP = {
    "Von Hand (Würfel, 8 Zustände)": "Acht Zustände mit von Hand gesetzten Werten: drei schwache Optima, aber nur zwei geschlossene Plateaus; 000 ist ein Scheinoptimum.",
    "Von Hand (Tour, 7 Städte)": "Sieben Gitterpunkte, Manhattan-Längen, 360 Touren, 2-opt: zwei schwache Optima, ein geschlossenes Plateau.",
    "NK grob (3 Stufen)": "NK-Modell mit N = 14, K = 2 und drei ganzzahligen Werten je Beitrag: viele gleich gute Nachbarn.",
    "NK fein (Kontrolle)": "Dieselbe Bauart mit 1 000 000 Werten je Beitrag: In dieser Instanz ist kein Nachbarpaar gleich gut.",
    "Gitter Manhattan n = 9": "Neun Zellen eines 4 × 4-Gitters ohne Rauschen, Manhattan-Längen (ganze Zahlen), 2-opt.",
    "Gitter euklidisch n = 9": "Dieselben neun Zellen mit euklidischen Längen: weniger Gleichstände, und „gleich“ braucht eine Regel für Gleitkommazahlen.",
    "Zufallskoordinaten": "Neun Punkte mit Zufallskoordinaten (Instanz 0 der Familie „gleichverteilt“): die Kontrolle ohne Plateaus.",
    "Würfel: Seitwärts ohne Nutzen": "Würfel mit anderen Werten und Seitwärtsgrenze 3: Seitwärtsschritte (R2) treffen hier seltener als die feste Zugreihenfolge (R0).",
}

REGEL_TABELLE = """
| Regel | Bei mehreren besten Nachbarn | Ohne strikt besseren Nachbarn |
|---|---|---|
| **R0** fester Gleichstand | der erste in der festen Zugreihenfolge | bleibt stehen |
| **R1** zufälliger Gleichstand | ein zufälliger unter den besten (gleichverteilt) | bleibt stehen |
| **R2** Seitwärtsschritte | wie R1 | geht zu einem zufälligen gleich guten Nachbarn, höchstens S Schritte hintereinander; jede Verbesserung setzt den Zähler zurück |
"""

ZAEHLWEISEN_TABELLE = """
| Zählweise | Bedingung | Zähleinheit |
|---|---|---|
| **schwaches Optimum** | kein Nachbar ist strikt besser | Zustand |
| **strenges Optimum** | alle Nachbarn sind strikt schlechter | Zustand |
| **geschlossenes Plateau** | zusammenhängende Menge gleich guter Zustände, von denen keiner einen strikt besseren Nachbarn hat (auch ein einzelner Zustand) | Plateau |
| **Scheinoptimum** | schwaches Optimum auf einem Plateau mit Ausgang: irgendein Zustand des Plateaus hat einen strikt besseren Nachbarn | Zustand |
"""

FAHRZEUG_TABELLE = """
| Fahrzeug | Zustände und Züge | Woher die Gleichstände kommen |
|---|---|---|
| **Würfel** | 8 Bitfolgen, Zug = ein Bit umdrehen (Reihenfolge Bit 0, 1, 2) | von Hand gesetzte ganze Zahlen |
| **NK-Modell** | 2^N Bitfolgen, Zug = ein Bit umdrehen; jeder der N Beiträge hängt an seinem Locus und K weiteren (zyklisch benachbart) | jeder Beitrag ist eine ganze Zahl von 0 bis Stufen − 1 |
| **Gitter ohne Rauschen** | alle (n − 1)!/2 Rundtouren durch n Zellen eines 4 × 4-Gitters, Zug = 2-opt (ein Abschnitt wird umgedreht) | ganzzahlige Koordinaten: viele Touren sind gleich lang |
| **Zufallskoordinaten** | wie oben, Punkte aus den vier Familien der Reihe (Koordinaten 0 bis 9999) | in den gemessenen Instanzen keine: Kontrolle |
"""
