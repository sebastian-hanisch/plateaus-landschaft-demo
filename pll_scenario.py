"""Fahrzeuge der Demo: Würfel von Hand, NK-Modell mit Stufen, Rundtour mit 2-opt (Gitter ohne Rauschen, Zufallskoordinaten).

Jede Funktion liefert eine `Landschaft`: ganzzahlige Werte V (kleiner ist besser), die Nachbarmatrix in fester Zugreihenfolge
und die echten Werte (Fitness oder Tourlänge) für die Anzeige. Der Zufall kommt aus SplitMix64 (pll_rng.py), die Instanzen der
Zufallsfamilien und das NK-Modell aus der gemeinsamen Basis der Linie (pll_basis.py, unveränderte Kopie).
"""

import itertools
import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import pll_basis as B
from pll_rng import SplitMix64

GITTERSEITE = 4                      # Gitter ohne Rauschen: 4 x 4 Zellen mit ganzzahligen Koordinaten 0..3
TOLERANZ_STELLEN = 1e9               # „mit Toleranz“: Längen werden auf 1e-9 gerundet und dann ganzzahlig verglichen
WUERFEL_H1 = (2, 2, 1, 4, 2, 0, 3, 2)    # Handbeispiel: Werte der Zustände 000, 001, …, 111 (Maximieren)
WUERFEL_H1B = (0, 0, 1, 2, 1, 0, 0, 2)   # Handbeispiel: Seitwärtsschritte liegen hier unter R0
TOUR_H2 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 3), (3, 3), (4, 0))   # Handbeispiel: sieben Gitterpunkte


@dataclass(frozen=True, eq=False)
class Landschaft:
    art: str                 # "wuerfel", "nk", "tour"
    V: np.ndarray            # ganzzahlig, kleiner ist besser
    nbi: np.ndarray          # (S, M) Nachbarn in fester Zugreihenfolge
    werte: np.ndarray        # echte Werte: Fitness (größer ist besser) oder Tourlänge (kleiner ist besser)
    maximieren: bool
    beschreibung: str
    punkte: tuple = ()
    touren: np.ndarray | None = None

    @property
    def zustaende(self) -> int:
        return len(self.V)

    @property
    def zuege(self) -> int:
        return self.nbi.shape[1]


# ---------------------------------------------------------------------------------------------------------------- Bitfolgen

def bit_nachbarn(n: int) -> np.ndarray:
    """Zustand s (Bit i = Locus i), Zug i dreht Bit i um; Zugreihenfolge Bit 0, 1, …, n-1."""
    s = np.arange(1 << n, dtype=np.int64)
    return s[:, None] ^ (1 << np.arange(n, dtype=np.int64))[None, :]


def wuerfel(werte) -> Landschaft:
    """Würfel mit drei Bits: `werte` sind die acht Fitnesswerte der Zustände 000 … 111 (Maximieren)."""
    f = np.asarray([int(v) for v in werte], dtype=np.int64)
    if len(f) != 8:
        raise ValueError("der Würfel braucht genau acht Werte")
    return Landschaft("wuerfel", -f, bit_nachbarn(3), f, True, "Würfel mit drei Bits (von Hand gesetzte Werte)")


def nk_fitness(tabellen: list) -> np.ndarray:
    """Fitness aller 2^N Zustände des NK-Modells der Basis (Zustand s: Bit i = x_i), vektorisiert."""
    n = len(tabellen)
    k = len(tabellen[0]).bit_length() - 2
    s = np.arange(1 << n, dtype=np.int64)
    gesamt = 0
    for i in range(n):
        index = np.zeros(1 << n, dtype=np.int64)
        for j in range(k + 1):
            index = (index << 1) | ((s >> ((i + j) % n)) & 1)
        gesamt = gesamt + np.asarray(tabellen[i])[index]
    return gesamt


def nk_landschaft(n: int, k: int, stufen: int, seed: int) -> Landschaft:
    """NK-Modell mit ganzzahligen Beiträgen 0..stufen-1 je Locus (K zählt die WEITEREN Loci, zyklisch benachbart)."""
    if stufen < 2:
        raise ValueError("mindestens zwei Stufen je Beitrag")
    tab = B.nk_tabellen(SplitMix64(seed), n, k, stufen)
    f = nk_fitness(tab)
    return Landschaft("nk", -f, bit_nachbarn(n), f, True, f"NK-Modell, N = {n}, K = {k}, {stufen} Stufen je Beitrag")


# ---------------------------------------------------------------------------------------------------------------- Rundtouren

@lru_cache(maxsize=4)
def alle_touren(n: int) -> np.ndarray:
    """Alle (n-1)!/2 Rundtouren: Stadt 0 vorn, zweite Stadt kleiner als die letzte; lexikographisch sortiert."""
    if n < 3:
        raise ValueError("eine Rundtour braucht mindestens drei Städte")
    perm = np.array(list(itertools.permutations(range(1, n))), dtype=np.int64).reshape(-1, n - 1)
    perm = perm[perm[:, 0] < perm[:, -1]]
    return np.concatenate([np.zeros((len(perm), 1), dtype=np.int64), perm], axis=1)


def zwei_opt_zuege(n: int) -> list:
    """Züge (i, j): die Positionen i..j der Tour werden umgedreht; feste Zugreihenfolge lexikographisch. n(n-3)/2 Züge."""
    return [(i, j) for i in range(1, n) for j in range(i + 1, n) if not (i == 1 and j == n - 1)]


def _schluessel(t: np.ndarray) -> np.ndarray:
    n = t.shape[1]
    code = np.zeros(len(t), dtype=np.int64)
    for spalte in range(1, n):
        code = code * n + t[:, spalte]
    return code


@lru_cache(maxsize=4)
def zwei_opt_nachbarn(n: int) -> np.ndarray:
    """Nachbarmatrix der 2-opt-Nachbarschaft über alle Touren (Spalte = Zug in fester Zugreihenfolge)."""
    t = alle_touren(n)
    codes = _schluessel(t)
    zuege = zwei_opt_zuege(n)
    nbi = np.zeros((len(t), len(zuege)), dtype=np.int64)
    for spalte, (i, j) in enumerate(zuege):
        u = t.copy()
        u[:, i:j + 1] = t[:, i:j + 1][:, ::-1]
        drehen = u[:, 1] > u[:, -1]
        u[drehen, 1:] = u[drehen, 1:][:, ::-1]
        nbi[:, spalte] = np.searchsorted(codes, _schluessel(u))
    return nbi


def abstandsmatrix(punkte, metrik: str) -> np.ndarray:
    """„manhattan“: ganzzahlig. „euklid“: math.sqrt einer ganzen Zahl (wie in der Basis, auf jeder Plattform gleich gerundet)."""
    n = len(punkte)
    if metrik == "manhattan":
        return np.array([[abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in punkte] for a in punkte], dtype=np.int64)
    if metrik == "euklid":
        return np.array([[math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) for b in punkte] for a in punkte], dtype=float).reshape(n, n)
    raise ValueError(f"unbekannte Metrik: {metrik}")


def tourlaengen(touren: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Länge jeder Tour, summiert in Tourreihenfolge ab Position 0 (feste Reihenfolge wie in der Basis)."""
    n = touren.shape[1]
    gesamt = np.zeros(len(touren), dtype=d.dtype)
    for pos in range(n):
        gesamt = gesamt + d[touren[:, pos], touren[:, (pos + 1) % n]]
    return gesamt


def laengen_zu_stufen(laengen: np.ndarray, gleichheit: str) -> np.ndarray:
    """Ganzzahlige Vergleichswerte: „toleranz“ rundet auf 1e-9, „streng“ vergleicht die Gleitkommazahlen bitgenau (Rang)."""
    if np.issubdtype(laengen.dtype, np.integer):
        return laengen.astype(np.int64)
    if gleichheit == "toleranz":
        return np.rint(laengen * TOLERANZ_STELLEN).astype(np.int64)
    if gleichheit == "streng":
        return np.unique(laengen, return_inverse=True)[1].astype(np.int64)
    raise ValueError(f"unbekannte Gleichheitsregel: {gleichheit}")


def tour_landschaft(punkte, metrik: str, gleichheit: str = "toleranz", beschreibung: str = "") -> Landschaft:
    n = len(punkte)
    t = alle_touren(n)
    laengen = tourlaengen(t, abstandsmatrix(punkte, metrik))
    text = beschreibung or f"Rundtour mit {n} Städten, 2-opt"
    return Landschaft("tour", laengen_zu_stufen(laengen, gleichheit), zwei_opt_nachbarn(n), laengen, False, text, tuple(tuple(p) for p in punkte), t)


def gitter_punkte(n: int, seed: int) -> list:
    """n verschiedene Zellen des 4 x 4-Gitters OHNE Rauschen (ganzzahlige Koordinaten 0..3), gezogen mit SplitMix64."""
    if not 3 <= n <= GITTERSEITE * GITTERSEITE:
        raise ValueError("3 <= n <= 16 verlangt")
    zellen = [(i, j) for i in range(GITTERSEITE) for j in range(GITTERSEITE)]
    SplitMix64(seed).shuffle(zellen)
    return zellen[:n]


def gitter_landschaft(n: int, seed: int, metrik: str, gleichheit: str = "toleranz") -> Landschaft:
    name = "Manhattan" if metrik == "manhattan" else "euklidisch"
    return tour_landschaft(gitter_punkte(n, seed), metrik, gleichheit, f"Rundtour auf dem Gitter ohne Rauschen, n = {n}, {name}, 2-opt")


def zufall_punkte(familie: str, n: int, idx: int) -> list:
    """Instanz `idx` der Familie aus der gemeinsamen Basis (ganzzahlige Koordinaten 0..9999)."""
    return B.rundtour_punkte(SplitMix64(B.instanz_seed(familie, n, idx)), familie, n)


def zufall_landschaft(familie: str, n: int, idx: int, gleichheit: str = "toleranz") -> Landschaft:
    return tour_landschaft(zufall_punkte(familie, n, idx), "euklid", gleichheit,
                           f"Rundtour mit Zufallskoordinaten ({B.FAMILIEN_TEXT[familie]}), n = {n}, euklidisch, 2-opt")


def luecke_prozent(land: Landschaft, bester_v: np.ndarray) -> np.ndarray:
    """Lücke des besten gefundenen Zustands zum Optimum in Prozent des Betrags des Optimums, in den echten Werten gerechnet."""
    stufen, erster = np.unique(land.V, return_index=True)
    echt = land.werte[erster].astype(float)
    opt = echt[0]
    gefunden = echt[np.searchsorted(stufen, np.asarray(bester_v))]
    if opt == 0:
        return np.abs(gefunden - opt)
    return 100.0 * np.abs(gefunden - opt) / abs(opt)
