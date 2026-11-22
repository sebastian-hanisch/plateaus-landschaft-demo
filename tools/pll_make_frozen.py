"""Erzeugt die eingefrorenen Messreihen data/pll_<teil>.json (je Zelle 30 Instanzen, vollständig aufgezählt).

Aufruf (im Demo-Ordner, Test-venv):
    python tools/pll_make_frozen.py <teil> [<teil> ...]      schreibt die genannten Teile
    python tools/pll_make_frozen.py --check <teil> [...]     rechnet neu und vergleicht (Gleitkommazahlen relativ 1e-9, sonst exakt)
    python tools/pll_make_frozen.py --liste                  nennt die Teile

Die Teile sind so geschnitten, dass keiner länger als einige Minuten rechnet. Jede Datei nennt Quelle (dieses Skript, Teil),
Stand, Zufallsstrom und Parameter. Der stetige Ausblick hat ein eigenes Skript (tools/pll_make_stetig.py).
"""

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pll_basis as B  # noqa: E402
import pll_messung as M  # noqa: E402

STAND = "2026-11-21"
DATA = ROOT / "data"


def teil_stufen():
    return {"parameter": "NK-Modell, N = 14, K = 4, Stufen je Beitrag wie Schlüssel, 30 Instanzen je Zeile und Strom",
            "zeilen": {strom: {str(st): M.nk_zelle(14, 4, st, strom, mit_regeln=False) for st in M.STUFEN_REIHE} for strom in ("A", "B")}}


def _nk_zellen(n, ks, stroeme):
    return {"parameter": f"NK-Modell, N = {n}, K in {list(ks)}, Stufen 3, 4 und 1 000 000 (fein), 30 Instanzen je Zelle, Seitwärtsgrenze 50",
            "zellen": {strom: {f"{n}|{st}|{k}": M.nk_zelle(n, k, st, strom) for st in M.NK_ZELLEN_STUFEN for k in ks} for strom in stroeme}}


def _gitter(n, stroeme):
    return {"parameter": f"Rundtour auf dem 4x4-Gitter ohne Rauschen, n = {n}, 2-opt, 30 Instanzen je Zelle, Seitwärtsgrenze 50",
            "zellen": {strom: {f"{n}|{v}": M.gitter_zelle(n, v, strom) for v in M.GITTER_VARIANTEN} for strom in stroeme}}


def _zufall(ns, stroeme):
    return {"parameter": f"Rundtour mit Zufallskoordinaten der gemeinsamen Basis, n in {list(ns)}, euklidisch, auf 1e-9 gerundet, 2-opt, 30 Instanzen je Zelle",
            "zellen": {strom: {f"{fam}|{n}": M.zufall_zelle(fam, n, strom) for fam in B.FAMILIEN for n in ns} for strom in stroeme}}


def teil_budget_nk():
    return {"parameter": "NK-Modell, N = 14, 3 Stufen, K = 2, 4, 8; Budgets 20, 120, 600, 3 000 mal M = 14 Auswertungen; 100 Läufe je Instanz und Regel; "
                         "Lücke in Prozent des Betrags des Optimums; Intervall = 95-%-Bootstrap über die 30 Instanzen (2 000 Ziehungen)",
            "zellen": {strom: {str(k): M.budget_nk_zelle(k, strom) for k in M.NK_ZELLEN_K} for strom in ("A", "B")}}


def teil_budget_gitter():
    return {"parameter": "Rundtour auf dem Gitter ohne Rauschen, Manhattan, n = 9 und 10, 2-opt; Budgets 20 und 120 mal M Auswertungen (M = 27 bzw. 35); "
                         "100 Läufe je Instanz und Regel; Lücke in Prozent der kürzesten Länge",
            "zellen": {"A": {str(n): M.budget_gitter_zelle(n, "A") for n in (9, 10)}, "B": {"9": M.budget_gitter_zelle(9, "B")}}}


TEILE = {
    "stufen": teil_stufen,
    "zellen14": lambda: _nk_zellen(14, M.NK_ZELLEN_K, ("A", "B")),
    "zellen16k2": lambda: _nk_zellen(16, (2,), ("A",)),
    "zellen16k4": lambda: _nk_zellen(16, (4,), ("A",)),
    "zellen16k8": lambda: _nk_zellen(16, (8,), ("A",)),
    "gitter8": lambda: _gitter(8, ("A", "B")),
    "gitter9": lambda: _gitter(9, ("A", "B")),
    "gitter10": lambda: _gitter(10, ("A",)),
    "zufall89": lambda: _zufall((8, 9), ("A", "B")),
    "zufall10": lambda: _zufall((10,), ("A",)),
    "budget_nk": teil_budget_nk,
    "budget_gitter": teil_budget_gitter,
}


def gleich(a, b, pfad=""):
    """Vergleich mit Band: Gleitkommazahlen relativ 1e-9 (absolut 1e-12), alles andere exakt. Rückgabe: Liste der Abweichungen."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [f"{pfad}: Schlüssel verschieden"]
        return [x for k in a for x in gleich(a[k], b[k], f"{pfad}/{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{pfad}: Länge verschieden"]
        return [x for i, (u, v) in enumerate(zip(a, b)) for x in gleich(u, v, f"{pfad}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        return [] if math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) else [f"{pfad}: {a} != {b}"]
    return [] if a == b else [f"{pfad}: {a} != {b}"]


def main(argv):
    if "--liste" in argv or not [a for a in argv if not a.startswith("--")]:
        print("Teile:", ", ".join(TEILE))
        return 0
    check = "--check" in argv
    fehler = 0
    for name in [a for a in argv if not a.startswith("--")]:
        t0 = time.time()
        inhalt = {"quelle": f"tools/pll_make_frozen.py {name}", "stand": STAND,
                  "zufall": "SplitMix64; Strom A = Zufalls-Seeds 100000 bis 100029, Strom B = 200000 bis 200029 (Zufallskoordinaten: Instanzen 0 bis 29 bzw. 30 bis 59 der Basis)"}
        inhalt.update(TEILE[name]())
        inhalt = json.loads(json.dumps(inhalt))
        ziel = DATA / f"pll_{name}.json"
        if check:
            alt = json.loads(ziel.read_text(encoding="utf-8"))
            ab = gleich(alt, inhalt)
            fehler += len(ab)
            print(f"{name}: {'ok' if not ab else 'ABWEICHUNG ' + '; '.join(ab[:5])} ({time.time() - t0:.0f} s)", flush=True)
        else:
            DATA.mkdir(exist_ok=True)
            ziel.write_text(json.dumps(inhalt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            print(f"{name}: geschrieben ({time.time() - t0:.0f} s)", flush=True)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
