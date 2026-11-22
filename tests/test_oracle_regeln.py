"""Orakel für die Gleichstandsregeln: die Rechnung der Demo (wiederholtes Einsetzen mit numpy) gegen
(a) eine unabhängige Rekursion über alle Zufallsentscheidungen mit Brüchen (tests/conftest.py),
(b) eine Stichprobe einzelner Abstiege mit einem Python-Abstieg und SplitMix64,
(c) R0 gegen eine Python-Schleife.
Die Rekursion (a) ist selbst am Handbeispiel H1 geprüft (1/2, 7/12, 31/48)."""

from fractions import Fraction as Fr

import numpy as np
import pytest
from conftest import bit_nbrs, ref_regeln

import pll_rules as R
import pll_scenario as S
from pll_rng import SplitMix64


def _zufall_werte(rng, n, stufen):
    return [rng.below(stufen) for _ in range(1 << n)]


def test_das_orakel_selbst_stimmt_am_handbeispiel(h1):
    F, nbrs = h1
    r = ref_regeln(F, nbrs, 50)
    assert (r["R0"][0], r["R1"][0], r["R2"][0]) == (Fr(1, 2), Fr(7, 12), Fr(31, 48))
    assert (r["R0"][1], r["R1"][1], r["R2"][1]) == (Fr(7, 4), Fr(7, 4), Fr(2))


@pytest.mark.parametrize("seit", [0, 1, 3, 50])
def test_erfolg_und_kosten_gegen_die_rekursion_mit_bruechen(seit):
    rng = SplitMix64(4711 + seit)
    geprueft = 0
    for n in (3, 4, 5, 6):
        nbrs = bit_nbrs(n)
        nbi = S.bit_nachbarn(n)
        for stufen in (2, 3, 5):
            for _ in range(4):
                F = _zufall_werte(rng, n, stufen)
                ref = ref_regeln(F, nbrs, seit)
                r = R.alle_regeln(-np.array(F), nbi, seit)
                for name in R.REGELN:
                    assert r[name]["erfolg"] == pytest.approx(float(ref[name][0]), rel=1e-12, abs=1e-12), (n, stufen, name)
                    assert r[name]["scans"] == pytest.approx(float(ref[name][1]), rel=1e-12, abs=1e-12), (n, stufen, name)
                    geprueft += 2
    assert geprueft == 4 * 3 * 4 * 3 * 2


def test_nk_landschaft_mit_stufen_gegen_die_rekursion():
    for seed, (n, k, stufen) in enumerate(((6, 2, 3), (7, 3, 2), (8, 2, 4))):
        land = S.nk_landschaft(n, k, stufen, seed)
        ref = ref_regeln([int(f) for f in land.werte], bit_nbrs(n), 50)
        r = R.alle_regeln(land.V, land.nbi, 50)
        for name in R.REGELN:
            assert r[name]["erfolg"] == pytest.approx(float(ref[name][0]), rel=1e-12, abs=1e-12)
            assert r[name]["auswertungen"] == pytest.approx(1 + n * float(ref[name][1]), rel=1e-12)


def test_tour_landschaft_gegen_die_rekursion():
    land = S.gitter_landschaft(6, 3, "manhattan")
    nbrs = [list(map(int, zeile)) for zeile in land.nbi]
    ref = ref_regeln([-int(v) for v in land.V], nbrs, 50)
    r = R.alle_regeln(land.V, land.nbi, 50)
    for name in R.REGELN:
        assert r[name]["erfolg"] == pytest.approx(float(ref[name][0]), rel=1e-12, abs=1e-12)
        assert r[name]["scans"] == pytest.approx(float(ref[name][1]), rel=1e-12)


def abstieg(V, nbi, start, regel, seit, rng):
    """Ein einzelner Abstieg als Python-Schleife: (Endzustand, Durchsuchungen)."""
    x, scans, k = start, 0, 0
    while True:
        scans += 1
        werte = [int(V[y]) for y in nbi[x]]
        m = min(werte)
        if m < V[x]:
            beste = [int(y) for y, w in zip(nbi[x], werte) if w == m]
            x = beste[0] if regel == "R0" else beste[rng.below(len(beste))]
            k = 0
            continue
        gleich = [int(y) for y, w in zip(nbi[x], werte) if w == V[x]]
        if regel == "R2" and gleich and k < seit:
            x = gleich[rng.below(len(gleich))]
            k += 1
            continue
        return x, scans


@pytest.mark.parametrize("regel", ["R0", "R1", "R2"])
def test_stichprobe_einzelner_abstiege_liegt_im_band_um_den_exakten_wert(regel):
    land = S.nk_landschaft(8, 2, 3, 12)
    exakt = R.alle_regeln(land.V, land.nbi, 50)[regel]
    rng = SplitMix64(99 + R.REGELN.index(regel))
    starts = 2000
    treffer, scans = [], []
    for _ in range(starts):
        ende, s = abstieg(land.V, land.nbi, rng.below(land.zustaende), regel, 50, rng)
        treffer.append(land.V[ende] == land.V.min())
        scans.append(s)
    p = exakt["erfolg"]
    fehler = (p * (1 - p) / starts) ** 0.5
    assert abs(np.mean(treffer) - p) <= 4.5 * fehler + 1e-12
    assert abs(np.mean(scans) - exakt["scans"]) <= 4.5 * np.std(scans) / starts ** 0.5 + 1e-12


def test_r0_gegen_die_python_schleife():
    for seed in range(6):
        land = S.nk_landschaft(7, 2, 3, 40 + seed)
        r0 = R.regel_r0(land.V, land.nbi)
        for x in range(land.zustaende):
            ende, _ = abstieg(land.V, land.nbi, x, "R0", 0, None)
            assert r0["ende"][x] == ende
