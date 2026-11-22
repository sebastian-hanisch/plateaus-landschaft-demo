"""Gleichstandsregeln des steilsten Abstiegs: Erfolg und Kosten exakt, dazu die Stichprobe bei festem Budget (nur numpy).

Abstieg = steilster Abstieg: alle M Nachbarn werden bewertet (Zählweise „voll“), es wird nur bei strikter Verbesserung gezogen.
* R0: unter mehreren besten Nachbarn der erste in fester Zugreihenfolge, nie seitwärts.
* R1: ein zufälliger unter den besten Nachbarn (gleichverteilt), nie seitwärts.
* R2: wie R1; ohne strikt besseren Nachbarn ein Seitwärtsschritt zu einem zufälligen gleich guten Nachbarn, höchstens `seit`
  Seitwärtsschritte hintereinander (der Zähler wird bei jeder Verbesserung zurückgesetzt).
Erfolg eines Abstiegs = Anteil der Starts (gleichverteilt über alle Zustände), die in einem Zustand mit dem besten Wert enden.
Kosten: eine Durchsuchung der Nachbarschaft kostet M Auswertungen, der Start 1; ein Abstieg kostet 1 + M * Durchsuchungen
(auch die letzte Durchsuchung ohne Verbesserung zählt).

Werte V sind ganzzahlig, KLEINER ist besser; nbi ist die Nachbarmatrix in fester Zugreihenfolge.
"""

import numpy as np

REGELN = ("R0", "R1", "R2")
SEIT_STANDARD = 50
_GAMMA = np.uint64(0x9E3779B97F4A7C15)
_C1 = np.uint64(0xBF58476D1CE4E5B9)
_C2 = np.uint64(0x94D049BB133111EB)


def _vorbereiten(V, nbi):
    V = np.asarray(V)
    nbv = V[nbi]
    mn = nbv.min(1)
    imp = mn < V                                   # hat einen strikt besseren Nachbarn
    best = (nbv == mn[:, None]) & imp[:, None]     # die besten (strikt besseren) Nachbarn
    gleich = nbv == V[:, None]
    return V, nbv, imp, best, gleich


def regel_r0(V, nbi) -> dict:
    """R0 exakt: Nachfolger = erster bester Nachbar; Endzustand und Zahl der Durchsuchungen durch Zeigerverdopplung."""
    V = np.asarray(V)
    S = len(V)
    if nbi.shape[1] == 0:
        return {"erfolg": float((V == V.min()).mean()), "scans": 1.0, "ende": np.arange(S), "treffer": V == V.min()}
    nbv = V[nbi]
    imp = nbv.min(1) < V
    nxt = np.where(imp, nbi[np.arange(S), nbv.argmin(1)], np.arange(S))   # argmin nimmt den ersten kleinsten Wert
    sprung, weite = nxt.copy(), imp.astype(np.int64)
    for _ in range(64):
        weite_neu, sprung_neu = weite + weite[sprung], sprung[sprung]
        if np.array_equal(sprung_neu, sprung):
            break
        weite, sprung = weite_neu, sprung_neu
    treffer = V[sprung] == V.min()
    return {"erfolg": float(treffer.mean()), "scans": float((weite + 1).mean()), "ende": sprung, "treffer": treffer}


def regeln_exakt(V, nbi, seit: int = SEIT_STANDARD) -> dict:
    """Erfolg und erwartete Durchsuchungen je Start unter R1 und R2, exakt (Erwartungswert über alle Zufallsentscheidungen).

    Rechenweg: Die Trefferwahrscheinlichkeit eines Zustands hängt nur von strikt besseren Zuständen ab und, auf einem Plateau,
    vom Seitwärtszähler k. Nur Zustände ohne strikt besseren, aber mit gleich gutem Nachbarn (Menge W) brauchen den Zähler.
    Die Gleichungen werden wiederholt eingesetzt, bis sich nichts mehr ändert (endlich viele Runden, weil kein Weg zurückführt:
    eine Verbesserung senkt den Wert, ein Seitwärtsschritt erhöht den Zähler)."""
    V, nbv, imp, best, gleich = _vorbereiten(V, nbi)
    S, M = nbi.shape
    ziel = (V == V.min()).astype(float)
    nbest = np.maximum(best.sum(1), 1)
    w = np.nonzero(~imp & gleich.any(1))[0]
    pos_w = np.zeros(S, dtype=np.int64)
    pos_w[w] = np.arange(len(w))
    nb_w, gleich_w = nbi[w], gleich[w]
    imp_nb_w = imp[nb_w]
    zahl_gleich_w = np.maximum(gleich_w.sum(1), 1)
    ist_w = np.zeros(S, dtype=bool)
    ist_w[w] = True
    bestf = best.astype(float)
    gleichf = gleich_w.astype(float)

    p1, e1 = ziel.copy(), np.ones(S)
    pa, ea = ziel.copy(), np.ones(S)                          # R2: Werte der Zustände mit Verbesserung (unabhängig vom Zähler)
    q = np.tile(ziel[w], (seit + 1, 1))                       # R2: Werte auf W je Zählerstand
    eq_ = np.ones((seit + 1, len(w)))
    for _ in range(S + seit + 5):
        p1_neu = np.where(imp, (p1[nbi] * bestf).sum(1) / nbest, ziel)
        e1_neu = 1.0 + np.where(imp, (e1[nbi] * bestf).sum(1) / nbest, 0.0)
        p0 = np.where(imp, pa, ziel)
        e0 = np.where(imp, ea, 1.0)
        if len(w):
            p0[w], e0[w] = q[0], eq_[0]
        pa_neu = np.where(imp, (p0[nbi] * bestf).sum(1) / nbest, ziel)
        ea_neu = 1.0 + np.where(imp, (e0[nbi] * bestf).sum(1) / nbest, 0.0)
        q_neu, eq_neu = q.copy(), eq_.copy()
        if len(w):
            q_neu[seit], eq_neu[seit] = ziel[w], 1.0
            for k in range(seit - 1, -1, -1):
                q_neu[k] = (np.where(imp_nb_w, pa_neu[nb_w], q_neu[k + 1][pos_w[nb_w]]) * gleichf).sum(1) / zahl_gleich_w
                eq_neu[k] = 1.0 + (np.where(imp_nb_w, ea_neu[nb_w], eq_neu[k + 1][pos_w[nb_w]]) * gleichf).sum(1) / zahl_gleich_w
        fertig = (np.array_equal(p1_neu, p1) and np.array_equal(e1_neu, e1) and np.array_equal(pa_neu, pa) and np.array_equal(ea_neu, ea)
                  and np.array_equal(q_neu, q) and np.array_equal(eq_neu, eq_))
        p1, e1, pa, ea, q, eq_ = p1_neu, e1_neu, pa_neu, ea_neu, q_neu, eq_neu
        if fertig:
            break
    p2 = np.where(imp, pa, ziel)
    e2 = np.where(imp, ea, 1.0)
    if len(w):
        p2[w], e2[w] = q[0], eq_[0]
    return {"R1": {"erfolg": float(p1.mean()), "scans": float(e1.mean()), "p": p1},
            "R2": {"erfolg": float(p2.mean()), "scans": float(e2.mean()), "p": p2}}


def alle_regeln(V, nbi, seit: int = SEIT_STANDARD) -> dict:
    """Erfolg, Durchsuchungen, Auswertungen je Abstieg und Treffer je 1 000 Auswertungen für R0, R1, R2."""
    M = nbi.shape[1]
    r0 = regel_r0(V, nbi)
    if M == 0:
        ex = {"R1": {"erfolg": r0["erfolg"], "scans": 1.0}, "R2": {"erfolg": r0["erfolg"], "scans": 1.0}}
    else:
        ex = regeln_exakt(V, nbi, seit)
    out = {}
    for name, r in (("R0", r0), ("R1", ex["R1"]), ("R2", ex["R2"])):
        ausw = 1.0 + M * r["scans"]
        out[name] = {"erfolg": r["erfolg"], "scans": r["scans"], "auswertungen": ausw, "treffer_je_1000": 1000.0 * r["erfolg"] / ausw}
    return out


def _naechste_u64(zustand: np.ndarray) -> np.ndarray:
    """Ein Schritt von SplitMix64 für viele unabhängige Ströme zugleich (dieselbe Folge wie pll_rng.SplitMix64.next_u64)."""
    zustand += _GAMMA
    z = zustand.copy()
    z = (z ^ (z >> np.uint64(30))) * _C1
    z = (z ^ (z >> np.uint64(27))) * _C2
    return z ^ (z >> np.uint64(31))


def _kter_wahrer(maske: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Spaltenindex des k-ten wahren Eintrags je Zeile (k ab 0)."""
    c = np.cumsum(maske, axis=1)
    return ((c == (k + 1)[:, None]) & maske).argmax(1)


def budget_laeufe(V, nbi, regel: str, budgets, seeds, seit: int = SEIT_STANDARD) -> np.ndarray:
    """Abstieg mit Neustarts bei festem Budget, viele Läufe zugleich. Rückgabe: bester Wert je (Budget, Lauf).

    Ablauf je Lauf: Ein Neustart wählt einen gleichverteilten Zustand und kostet 1 Auswertung; jede Durchsuchung kostet M.
    Bleibt der Abstieg stehen, folgt ein Neustart. Der Lauf endet, sobald die nächste Aktion nicht mehr ins Budget passt.
    Jede Aktion verbraucht genau eine Zufallszahl des Laufs (SplitMix64 mit dem Zufalls-Seed des Laufs), auch wenn die Regel sie
    nicht braucht; ein Lauf mit kleinerem Budget ist deshalb der Anfang desselben Laufs mit größerem Budget.
    „Bester Wert“ = kleinster Wert unter den Zuständen, auf denen der Lauf stand."""
    if regel not in REGELN:
        raise ValueError(f"unbekannte Regel: {regel}")
    V, nbv, imp, best, gleich = _vorbereiten(V, nbi)
    S, M = nbi.shape
    budgets = np.asarray(budgets, dtype=np.int64)
    erster = nbv.argmin(1)
    nbest = np.maximum(best.sum(1), 1)
    zahl_gleich = gleich.sum(1)
    zustand = np.array([int(s) & 0xFFFFFFFFFFFFFFFF for s in seeds], dtype=np.uint64)
    R = len(zustand)
    grenze = int(budgets.max())
    gross = np.iinfo(np.int64).max
    bester = np.full((len(budgets), R), gross, dtype=np.int64)
    ausw = np.zeros(R, dtype=np.int64)
    cur = np.zeros(R, dtype=np.int64)
    zaehler = np.zeros(R, dtype=np.int64)
    neustart = np.ones(R, dtype=bool)
    aktiv = np.ones(R, dtype=bool)
    while True:
        aktiv &= ausw + np.where(neustart, 1, M) <= grenze
        if not aktiv.any():
            break
        u = _naechste_u64(zustand)
        tut_neustart = aktiv & neustart
        tut_scan = aktiv & ~neustart
        neu = cur.copy()
        bewegt = tut_neustart.copy()
        if tut_neustart.any():
            neu[tut_neustart] = (u[tut_neustart] % np.uint64(S)).astype(np.int64)
            zaehler[tut_neustart] = 0
            ausw[tut_neustart] += 1
            neustart[tut_neustart] = False
        if tut_scan.any():
            idx = np.nonzero(tut_scan)[0]
            x = cur[idx]
            ux = u[idx]
            verb = imp[x]
            ziel = x.copy()
            if regel == "R0":
                ziel[verb] = nbi[x[verb], erster[x[verb]]]
            else:
                if verb.any():
                    xv = x[verb]
                    j = (ux[verb] % nbest[xv].astype(np.uint64)).astype(np.int64)
                    ziel[verb] = nbi[xv, _kter_wahrer(best[xv], j)]
            seitw = np.zeros(len(idx), dtype=bool)
            if regel == "R2":
                seitw = ~verb & (zahl_gleich[x] > 0) & (zaehler[idx] < seit)
                if seitw.any():
                    xs = x[seitw]
                    j = (ux[seitw] % zahl_gleich[xs].astype(np.uint64)).astype(np.int64)
                    ziel[seitw] = nbi[xs, _kter_wahrer(gleich[xs], j)]
                zaehler[idx[verb]] = 0
                zaehler[idx[seitw]] += 1
            ausw[idx] += M
            steht = ~verb & ~seitw
            neustart[idx[steht]] = True
            neu[idx] = ziel
            bewegt[idx[~steht]] = True
        cur = neu
        if bewegt.any():
            werte = np.where(bewegt, V[cur], gross)
            passt = ausw[None, :] <= budgets[:, None]
            bester = np.where(passt, np.minimum(bester, werte[None, :]), bester)
    return bester
