"""Messreihen der Demo: je Zelle 30 feste Instanzen, vollständig aufgezählt. Die Ergebnisse liegen eingefroren in data/*.json
(erzeugt von tools/pll_make_frozen.py); dieselben Funktionen rechnen in den Tests einzelne Instanzen nach.

Zwei Zufallsströme: A (Zufalls-Seeds 100000 bis 100029) ist die Messung, B (200000 bis 200029) die Gegenprobe.
Bei den Zufallskoordinaten zählt die laufende Nummer der Basis-Instanz (A: 0 bis 29, B: 30 bis 59).
"""


import pll_basis as B
import pll_landscape as L
import pll_rules as R
import pll_scenario as S
from pll_rng import SplitMix64

INSTANZEN = 30
STROM = {"A": 100000, "B": 200000}
STROM_ZUFALL = {"A": 0, "B": 30}
STUFEN_REIHE = (2, 3, 4, 6, 10, 30, 1000, 10**6)
FEIN = 10**6
NK_ZELLEN_N = (14, 16)
NK_ZELLEN_STUFEN = (3, 4, FEIN)
NK_ZELLEN_K = (2, 4, 8)
GITTER_N = (8, 9, 10)
GITTER_VARIANTEN = ("manhattan", "euklid_toleranz", "euklid_streng")
BUDGET_C = (20, 120, 600, 3000)
BUDGET_C_GITTER = (20, 120)
BUDGET_LAEUFE = 100
BOOTSTRAP = 2000
EPS = 1e-12


def seeds(strom: str) -> list:
    return [STROM[strom] + i for i in range(INSTANZEN)]


def _mittel(werte) -> float:
    return float(sum(werte) / len(werte))


def instanz_zeile(land: S.Landschaft, mit_regeln: bool = True, seit: int = R.SEIT_STANDARD) -> dict:
    """Kennzahlen und (wahlweise) die exakten Regeln einer Landschaft als flaches Wörterbuch."""
    k = L.kennzahlen(land.V, land.nbi)
    z = {"nu": k.nu, "anteil_mit_gleichem": k.anteil_mit_gleichem, "anteil_groesstes": k.anteil_groesstes, "schwach": k.schwach,
         "streng": k.streng, "geschlossen": k.geschlossen, "plateaus": k.plateaus, "anteil_schein": k.anteil_schein,
         "globale_optima": k.globale_optima}
    if mit_regeln:
        r = R.alle_regeln(land.V, land.nbi, seit)
        for name in R.REGELN:
            z[f"erfolg_{name}"] = r[name]["erfolg"]
            z[f"ausw_{name}"] = r[name]["auswertungen"]
    return z


def zelle_zusammenfassen(zeilen: list) -> dict:
    """Mittel über die Instanzen einer Zelle; Verhältnisse als Quotient der Mittel; Spannen der Differenzen je Instanz."""
    out = {"instanzen": len(zeilen)}
    for feld in ("nu", "anteil_mit_gleichem", "anteil_groesstes", "schwach", "streng", "geschlossen", "plateaus", "anteil_schein"):
        out[feld] = _mittel([z[feld] for z in zeilen])
    out["faktor"] = out["schwach"] / out["geschlossen"]
    out["schwach_ungleich_streng"] = sum(1 for z in zeilen if z["schwach"] != z["streng"])
    out["mehrere_globale_optima"] = sum(1 for z in zeilen if z["globale_optima"] > 1)
    out["nu_max"] = max(z["nu"] for z in zeilen)
    if "erfolg_R0" in zeilen[0]:
        for name in R.REGELN:
            out[f"erfolg_{name}"] = _mittel([z[f"erfolg_{name}"] for z in zeilen])
            out[f"ausw_{name}"] = _mittel([z[f"ausw_{name}"] for z in zeilen])
            out[f"treffer_{name}"] = 1000.0 * out[f"erfolg_{name}"] / out[f"ausw_{name}"]
        for name in ("R1", "R2"):
            d = [z[f"erfolg_{name}"] - z["erfolg_R0"] for z in zeilen]
            out[f"d_{name}_mittel"], out[f"d_{name}_min"], out[f"d_{name}_max"] = _mittel(d), min(d), max(d)
        out["r2_unter_r0"] = sum(1 for z in zeilen if z["erfolg_R2"] < z["erfolg_R0"] - EPS)
        out["r2_unter_r1"] = sum(1 for z in zeilen if z["erfolg_R2"] < z["erfolg_R1"] - EPS)
        out["kostenfaktor_R2"] = out["ausw_R2"] / out["ausw_R0"]
        out["erfolg_je_instanz"] = {name: [z[f"erfolg_{name}"] for z in zeilen] for name in R.REGELN}
    return out


def nk_zelle(n: int, k: int, stufen: int, strom: str = "A", mit_regeln: bool = True) -> dict:
    return zelle_zusammenfassen([instanz_zeile(S.nk_landschaft(n, k, stufen, s), mit_regeln) for s in seeds(strom)])


def gitter_land(n: int, seed: int, variante: str) -> S.Landschaft:
    if variante == "manhattan":
        return S.gitter_landschaft(n, seed, "manhattan")
    return S.gitter_landschaft(n, seed, "euklid", "toleranz" if variante == "euklid_toleranz" else "streng")


def gitter_zelle(n: int, variante: str, strom: str = "A") -> dict:
    mit_regeln = variante != "euklid_streng"
    return zelle_zusammenfassen([instanz_zeile(gitter_land(n, s, variante), mit_regeln) for s in seeds(strom)])


def zufall_zelle(familie: str, n: int, strom: str = "A") -> dict:
    start = STROM_ZUFALL[strom]
    zeilen = [instanz_zeile(S.zufall_landschaft(familie, n, start + i, "toleranz"), False) for i in range(INSTANZEN)]
    return zelle_zusammenfassen(zeilen)


def bootstrap_intervall(werte: list, seed: int, wiederholungen: int = BOOTSTRAP) -> tuple:
    """95-%-Intervall des Mittels (Perzentil-Bootstrap über die Instanzen, SplitMix64): Rang 2,5 % und 97,5 % der sortierten Mittel."""
    rng = SplitMix64(seed)
    n = len(werte)
    mittel = sorted(sum(werte[rng.below(n)] for _ in range(n)) / n for _ in range(wiederholungen))
    return mittel[int(0.025 * wiederholungen)], mittel[int(0.975 * wiederholungen) - 1]


def budget_instanz(land: S.Landschaft, budgets, kennung: int, strom: str = "A", laeufe: int = BUDGET_LAEUFE) -> dict:
    """Je Regel und Budget: mittlere Lücke (Prozent) und Anteil der Läufe am Optimum; `kennung` trennt die Zufalls-Seeds der Instanzen."""
    versatz = 0 if strom == "A" else 1000
    out = {}
    for nr, regel in enumerate(R.REGELN):
        lauf_seeds = [B.lauf_seed(kennung, nr, versatz + lauf) for lauf in range(laeufe)]
        bester = R.budget_laeufe(land.V, land.nbi, regel, budgets, lauf_seeds)
        luecke = S.luecke_prozent(land, bester)
        out[regel] = {"luecke": [float(x) for x in luecke.mean(1)], "am_optimum": [float(x) for x in (bester == land.V.min()).mean(1)]}
    return out


def budget_zusammenfassen(je_instanz: list, budgets, boot_seed: int) -> list:
    """Je Budget: Mittel über die Instanzen, R2 - R0 mit Bootstrap-Intervall, Zahl der Instanzen mit R2 besser."""
    zeilen = []
    for b, budget in enumerate(budgets):
        z = {"budget": int(budget), "instanzen": len(je_instanz)}
        for regel in R.REGELN:
            z[f"luecke_{regel}"] = _mittel([inst[regel]["luecke"][b] for inst in je_instanz])
            z[f"am_optimum_{regel}"] = _mittel([inst[regel]["am_optimum"][b] for inst in je_instanz])
        d = [inst["R2"]["luecke"][b] - inst["R0"]["luecke"][b] for inst in je_instanz]
        z["d_R2_R0"] = _mittel(d)
        z["d_unten"], z["d_oben"] = bootstrap_intervall(d, boot_seed + b)
        z["r2_besser_instanzen"] = sum(1 for x in d if x < -EPS)
        z["d_je_instanz"] = d
        zeilen.append(z)
    return zeilen


def budget_nk_zelle(k: int, strom: str = "A", n: int = 14, stufen: int = 3) -> list:
    budgets = [c * n for c in BUDGET_C]
    je = [budget_instanz(S.nk_landschaft(n, k, stufen, s), budgets, 1000 * k + i, strom) for i, s in enumerate(seeds(strom))]
    return budget_zusammenfassen(je, budgets, 777_000 + k)


def budget_gitter_zelle(n: int, strom: str = "A") -> list:
    m = n * (n - 3) // 2
    budgets = [c * m for c in BUDGET_C_GITTER]
    je = [budget_instanz(S.gitter_landschaft(n, s, "manhattan"), budgets, 50_000 + 100 * n + i, strom) for i, s in enumerate(seeds(strom))]
    return budget_zusammenfassen(je, budgets, 778_000 + n)
