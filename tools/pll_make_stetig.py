"""Stetiger Ausblick (kein Gegenstand der Demo): Sattelanteil unter den GEFUNDENEN stationären Punkten erfundener Gauß-Kuppen.

Aufruf (im Demo-Ordner, Test-venv, braucht scipy):
    python tools/pll_make_stetig.py            schreibt data/pll_stetig.json
    python tools/pll_make_stetig.py --check    rechnet neu und vergleicht als Band (Anteile auf 0,05, Zählungen auf 15 %)
    python tools/pll_make_stetig.py --nur-mehr-starts    ergänzt nur den Abschnitt mit 3 000 Starts in der vorhandenen Datei

Funktion: f(x) = Summe von 20 Gauß-Kuppen in [0, 1]^d, Zentren gleichverteilt, Höhen in [0,5; 1), Breite 0,08 * Wurzel(d) * [0,5; 1).
Alles ist erfunden (keine reale Datenquelle). Zwei Suchverfahren aus denselben Starts (gleichverteilt in [0, 1]^d):
 (1) Newton-Verfahren auf den Gradienten mit auf 0,5 begrenzter Schrittlänge, höchstens 200 Schritte;
 (2) Levenberg-Marquardt (scipy.optimize.root, method="lm") mit analytischer Hesse-Matrix.
Ein Start zählt als konvergiert, wenn der Gradient betragsmäßig höchstens 1e-10 ist, f mindestens 1e-6 und alle |x_i| <= 5.
Punkte näher als 1e-6 gelten als derselbe. Art nach den Eigenwerten der Hesse-Matrix (Schwelle 1e-9).
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import root

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pll_rng import SplitMix64  # noqa: E402

STAND = "2026-11-21"
KUPPEN = 20
BREITE = 0.08
DIMENSIONEN = (2, 4, 8)
INSTANZEN = 10
STARTS = 300
STROM = {"A": 0, "B": 100}


VIELE_STARTS = 3000


def instanz(d: int, idx: int, starts: int = STARTS):
    rng = SplitMix64(9_000_011 + 1009 * d + 7919 * idx)
    zentren = np.array([[rng.random() for _ in range(d)] for _ in range(KUPPEN)])
    hoehen = np.array([0.5 + 0.5 * rng.random() for _ in range(KUPPEN)])
    breiten = np.array([BREITE * np.sqrt(d) * (0.5 + 0.5 * rng.random()) for _ in range(KUPPEN)])
    starts = np.array([[rng.random() for _ in range(d)] for _ in range(starts)])
    return zentren, hoehen, breiten, starts


def f_g_h(x, zentren, hoehen, breiten):
    r = x[None, :] - zentren
    e = hoehen * np.exp(-(r ** 2).sum(-1) / (2 * breiten ** 2))
    w2 = e / breiten ** 2
    g = -(w2[:, None] * r).sum(0)
    h = np.einsum("m,md,me->de", e / breiten ** 4, r, r) - w2.sum() * np.eye(len(x))
    return e.sum(), g, h


def newton(x0, inst, schritt=0.5, runden=200):
    x = x0.copy()
    for _ in range(runden):
        _, g, h = f_g_h(x, *inst)
        if np.abs(g).max() <= 1e-10:
            break
        try:
            s = np.linalg.solve(h, -g)
        except np.linalg.LinAlgError:
            return None
        laenge = np.linalg.norm(s)
        if not np.isfinite(laenge):
            return None
        if laenge > schritt:
            s = s * (schritt / laenge)
        x = x + s
    return x


def lm(x0, inst):
    return root(lambda x: f_g_h(x, *inst)[1], x0, jac=lambda x: f_g_h(x, *inst)[2], method="lm").x


def suche(verfahren, inst):
    zentren, hoehen, breiten, starts = inst
    kern = (zentren, hoehen, breiten)
    punkte, konvergiert = [], 0
    for x0 in starts:
        x = newton(x0, kern) if verfahren == "newton" else lm(x0, kern)
        if x is None or not np.all(np.isfinite(x)):
            continue
        f, g, _ = f_g_h(x, *kern)
        if np.abs(g).max() <= 1e-10 and f >= 1e-6 and (np.abs(x) <= 5).all():
            konvergiert += 1
            if not any(np.linalg.norm(x - q) <= 1e-6 for q in punkte):
                punkte.append(x)
    arten = {"maximum": 0, "minimum": 0, "sattel": 0, "entartet": 0}
    for p in punkte:
        ev = np.linalg.eigvalsh(f_g_h(p, *kern)[2])
        if (np.abs(ev) <= 1e-9).any():
            arten["entartet"] += 1
        elif (ev < 0).all():
            arten["maximum"] += 1
        elif (ev > 0).all():
            arten["minimum"] += 1
        else:
            arten["sattel"] += 1
    return {"konvergenz": konvergiert / len(starts), "punkte": len(punkte), **arten}


def zelle(d, verfahren, strom, starts: int = STARTS):
    zeilen = [suche(verfahren, instanz(d, STROM[strom] + i, starts)) for i in range(INSTANZEN)]
    mit = [z for z in zeilen if z["punkte"] > 0]
    return {"instanzen": INSTANZEN, "starts": starts, "konvergenz": float(np.mean([z["konvergenz"] for z in zeilen])),
            "punkte_je_instanz": float(np.mean([z["punkte"] for z in zeilen])),
            "instanzen_mit_punkten": len(mit),
            "sattelanteil": float(np.mean([z["sattel"] / z["punkte"] for z in mit])) if mit else None}


def mehr_starts():
    """Dieselben Instanzen bei d = 4, Newton, mit 3 000 statt 300 Starts (die ersten 300 Starts sind dieselben)."""
    out = {}
    for strom in STROM:
        t0 = time.time()
        out[strom] = {"4|newton": zelle(4, "newton", strom, VIELE_STARTS)}
        print("mehr Starts", strom, out[strom], f"({time.time() - t0:.0f} s)", flush=True)
    return out


def rechne(nur_mehr_starts: bool = False, alt: dict | None = None):
    out = {"quelle": "tools/pll_make_stetig.py", "stand": STAND,
           "parameter": f"{KUPPEN} erfundene Gauß-Kuppen, Breite {BREITE} * Wurzel(d), {INSTANZEN} Instanzen je Zelle, {STARTS} Starts je Instanz und Verfahren "
                        f"(Abschnitt mehr_starts: {VIELE_STARTS} Starts, nur d = 4 und Newton); "
                        "Strom A = Instanzen 0 bis 9, Strom B = Instanzen 100 bis 109; Sattelanteil = Mittel je Instanz über die Instanzen mit mindestens einem gefundenen Punkt",
           "zellen": {}}
    if nur_mehr_starts:
        out["zellen"] = alt["zellen"]
    else:
        for strom in STROM:
            out["zellen"][strom] = {}
            for d in DIMENSIONEN:
                for verfahren in ("newton", "lm"):
                    t0 = time.time()
                    out["zellen"][strom][f"{d}|{verfahren}"] = zelle(d, verfahren, strom)
                    print(strom, d, verfahren, out["zellen"][strom][f"{d}|{verfahren}"], f"({time.time() - t0:.0f} s)", flush=True)
    out["mehr_starts"] = mehr_starts()
    return out


def main(argv):
    ziel = ROOT / "data" / "pll_stetig.json"
    nur = "--nur-mehr-starts" in argv          # ergänzt nur den Abschnitt mehr_starts in der vorhandenen Datei
    neu = rechne(nur, json.loads(ziel.read_text(encoding="utf-8")) if nur else None)
    if "--check" in argv:
        alt = json.loads(ziel.read_text(encoding="utf-8"))
        ab = []
        paare = [(f"{strom} {key}", z, neu["zellen"][strom][key]) for strom, zellen in alt["zellen"].items() for key, z in zellen.items()]
        paare += [(f"mehr Starts {strom} {key}", z, neu["mehr_starts"][strom][key]) for strom, zellen in alt["mehr_starts"].items() for key, z in zellen.items()]
        for name, z, n in paare:
            if True:
                if (z["sattelanteil"] is None) != (n["sattelanteil"] is None):
                    ab.append(f"{name}: Sattelanteil vorhanden/fehlt")
                elif z["sattelanteil"] is not None and abs(z["sattelanteil"] - n["sattelanteil"]) > 0.05:
                    ab.append(f"{name}: Sattelanteil {z['sattelanteil']} gegen {n['sattelanteil']}")
                if abs(z["punkte_je_instanz"] - n["punkte_je_instanz"]) > 0.15 * max(1.0, z["punkte_je_instanz"]):
                    ab.append(f"{name}: Punkte {z['punkte_je_instanz']} gegen {n['punkte_je_instanz']}")
        print("ok (Band)" if not ab else "ABWEICHUNG: " + "; ".join(ab))
        return 1 if ab else 0
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(neu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
