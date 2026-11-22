"""Orakel für Landschaft und Fahrzeuge (anderer Rechenweg als die Demo):
* Plateaus (Ausbreitung der kleinsten Marke) gegen scipy.sparse.csgraph.connected_components und gegen Union-Find mit Schleifen;
* alle Kennzahlen gegen die Schleifenzählung aus tests/conftest.py;
* NK-Fitness (vektorisiert) gegen die Einzelberechnung der Basis; Tourlängen gegen die Basis;
* 2-opt-Nachbarmatrix gegen eine unabhängige Erzeugung über Kantenmengen;
* kürzeste Tour der Aufzählung gegen das Bellman-Held-Karp-Verfahren (dynamische Programmierung)."""

import itertools

import numpy as np
import pytest
from conftest import bit_nbrs, ref_analyse

import pll_basis as B
import pll_landscape as L
import pll_scenario as S
from pll_rng import SplitMix64


def _vergleiche(land, F, nbrs):
    ref = ref_analyse(F, nbrs)
    k = L.kennzahlen(land.V, land.nbi)
    e = L.einteilung(land.V, land.nbi)
    assert k.gleiche_paare == ref["gleiche_paare"] and k.paare == sum(len(n) for n in nbrs)
    assert list(np.nonzero(e["schwach"])[0]) == ref["schwach"] and list(np.nonzero(e["streng"])[0]) == ref["streng"]
    assert list(np.nonzero(e["schein"])[0]) == ref["schein"]
    assert k.geschlossen == len(ref["geschlossen"]) and k.plateaus == len(ref["plateaus"])
    assert k.groesstes_plateau == max((len(p) for p in ref["plateaus"]), default=0)
    assert k.mit_gleichem_nachbarn == len(ref["mit_gleichem"])
    assert sorted(L.plateaugroessen(land.V, land.nbi).tolist()) == sorted(len(p) for p in ref["plateaus"])
    gruppen = {}
    for x, m in enumerate(e["marke"]):
        gruppen.setdefault(int(m), []).append(x)
    assert sorted(g for g in gruppen.values() if len(g) >= 2) == ref["plateaus"]


def test_kennzahlen_gegen_schleifen_auf_nk_landschaften():
    for seed, (n, k, stufen) in enumerate(((4, 1, 2), (6, 2, 3), (8, 3, 2), (9, 2, 4), (10, 4, 3), (8, 0, 2))):
        land = S.nk_landschaft(n, k, stufen, 700 + seed)
        _vergleiche(land, [int(f) for f in land.werte], bit_nbrs(n))


def test_kennzahlen_gegen_schleifen_auf_touren():
    for seed in range(3):
        for metrik in ("manhattan", "euklid"):
            land = S.gitter_landschaft(7, seed, metrik)
            _vergleiche(land, [-int(v) for v in land.V], [list(map(int, z)) for z in land.nbi])


def test_komponenten_gegen_scipy():
    csgraph = pytest.importorskip("scipy.sparse.csgraph")
    sparse = pytest.importorskip("scipy.sparse")
    for seed in range(5):
        land = S.nk_landschaft(10, 2, 2 + seed % 3, 900 + seed)
        gleich = land.V[land.nbi] == land.V[:, None]
        zeilen, spalten = np.nonzero(gleich)
        graph = sparse.coo_matrix((np.ones(len(zeilen)), (zeilen, land.nbi[zeilen, spalten])), shape=(land.zustaende, land.zustaende))
        zahl, marken = csgraph.connected_components(graph, directed=False)
        eigene = L.komponenten(land.V, land.nbi)
        assert len(set(eigene.tolist())) == zahl
        assert len(set(zip(eigene.tolist(), marken.tolist()))) == zahl          # dieselbe Zerlegung


def test_nk_fitness_gegen_die_einzelberechnung_der_basis():
    for seed, (n, k, stufen) in enumerate(((5, 0, 3), (7, 2, 0), (9, 4, 4), (10, 9, 2), (12, 3, 1000000))):
        tab = B.nk_tabellen(SplitMix64(seed), n, k, stufen)
        f = S.nk_fitness(tab)
        rng = SplitMix64(50 + seed)
        for s in [0, (1 << n) - 1] + [rng.below(1 << n) for _ in range(40)]:
            x = [(s >> i) & 1 for i in range(n)]
            assert f[s] == pytest.approx(B.nk_wert(tab, x), rel=1e-12, abs=0)


def _kanten(tour):
    return frozenset(frozenset((tour[i], tour[(i + 1) % len(tour)])) for i in range(len(tour)))


@pytest.mark.parametrize("n", [4, 5, 6, 7])
def test_zwei_opt_nachbarn_gegen_kantenmengen(n):
    """Unabhängig: zwei Touren sind 2-opt-Nachbarn genau dann, wenn sie sich in genau zwei Kanten unterscheiden."""
    touren = S.alle_touren(n)
    nbi = S.zwei_opt_nachbarn(n)
    fakultaet = 1
    for i in range(2, n):
        fakultaet *= i
    assert len(touren) == fakultaet // 2 and nbi.shape == (len(touren), n * (n - 3) // 2)
    kanten = [_kanten(list(map(int, t))) for t in touren]
    for i in range(len(touren)):
        erwartet = {j for j in range(len(touren)) if len(kanten[i] - kanten[j]) == 2}
        assert set(nbi[i].tolist()) == erwartet and len(set(nbi[i].tolist())) == nbi.shape[1]


def test_tour_mit_vier_staedten():
    assert S.alle_touren(4).tolist() == [[0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3]]
    assert [sorted(z) for z in S.zwei_opt_nachbarn(4).tolist()] == [[1, 2], [0, 2], [0, 1]]      # jede der 3 Touren hat die beiden anderen als Nachbarn


def _held_karp(d):
    """Bellman-Held-Karp-Verfahren (dynamische Programmierung über Teilmengen): Länge der kürzesten Rundtour."""
    n = len(d)
    best = {(1, 0): 0.0}
    for groesse in range(2, n + 1):
        for teil in itertools.combinations(range(1, n), groesse - 1):
            maske = 1 | sum(1 << j for j in teil)
            for j in teil:
                vor = maske ^ (1 << j)
                best[(maske, j)] = min(best[(vor, i)] + d[i][j] for i in (0,) + teil if i != j and (vor, i) in best)
    voll = (1 << n) - 1
    return min(best[(voll, j)] + d[j][0] for j in range(1, n))


def test_kuerzeste_tour_der_aufzaehlung_gegen_held_karp():
    for seed in range(4):
        for metrik in ("manhattan", "euklid"):
            punkte = S.gitter_punkte(8, 300 + seed)
            land = S.tour_landschaft(punkte, metrik)
            assert float(land.werte.min()) == pytest.approx(_held_karp(S.abstandsmatrix(punkte, metrik).tolist()), rel=1e-12)
    for familie in B.FAMILIEN:
        punkte = S.zufall_punkte(familie, 8, 1)
        land = S.tour_landschaft(punkte, "euklid")
        assert float(land.werte.min()) == pytest.approx(_held_karp(B.abstaende(punkte)), rel=1e-12)


def test_tourlaengen_gegen_die_basis():
    punkte = S.zufall_punkte("cluster", 7, 2)
    land = S.tour_landschaft(punkte, "euklid")
    d = B.abstaende(punkte)
    for i in (0, 17, 123, 359):
        assert land.werte[i] == B.tourlaenge(d, [int(c) for c in land.touren[i]])      # gleiche Summenreihenfolge: bitgleich


def test_gegenprobe_gleiche_laengen_liegen_eng_verschiedene_weit_auseinander():
    """Die Rundung auf 1e-9 trennt sauber: Längen, die als gleich zählen, unterscheiden sich um höchstens 1e-12,
    verschiedene um mindestens 1e-6 (Gitter ohne Rauschen, euklidisch)."""
    for seed in range(5):
        land = S.gitter_landschaft(8, 100000 + seed, "euklid", "toleranz")
        ordnung = np.argsort(land.werte, kind="stable")
        w, v = land.werte[ordnung], land.V[ordnung]
        abstand = np.diff(w)
        gleich = np.diff(v) == 0
        assert abstand[gleich].max(initial=0.0) <= 1e-12
        assert abstand[~gleich].min() >= 1e-6
