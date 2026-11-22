"""Eigenschaften, die für jede Landschaft gelten müssen (feste Zufalls-Seeds, je 20 bis 30 Instanzen)."""

import numpy as np
import pytest

import pll_landscape as L
import pll_rules as R
import pll_scenario as S
from pll_rng import SplitMix64

TOL = dict(rel=1e-12, abs=1e-12)


def _instanzen(anzahl=24):
    for i in range(anzahl):
        n = 6 + i % 4
        yield S.nk_landschaft(n, i % 3 + 1, 2 + i % 3, 5000 + i)


def _zahlen(V, nbi, seit=50):
    k = L.kennzahlen(V, nbi)
    r = R.alle_regeln(V, nbi, seit)
    return k, r


def test_streng_monotone_transformation_aendert_nichts():
    """f -> 3f + 7 und f -> f^3 ändern weder ν noch Plateaus, Optima oder den Erfolg der drei Regeln."""
    for land in _instanzen():
        k0, r0 = _zahlen(land.V, land.nbi)
        for V in (3 * land.V + 7, land.V ** 3):
            k1, r1 = _zahlen(V, land.nbi)
            assert k1 == k0
            for name in R.REGELN:
                assert r1[name]["erfolg"] == pytest.approx(r0[name]["erfolg"], **TOL)
                assert r1[name]["scans"] == pytest.approx(r0[name]["scans"], **TOL)


def test_umnummerieren_der_bits_aendert_nur_die_namen():
    """Eine Permutation der Bits (und damit der Zugreihenfolge) ändert Kennzahlen, R1 und R2 nicht.
    R0 ist ausgenommen: Die feste Zugreihenfolge ist dort eine Stellschraube."""
    rng = SplitMix64(31)
    r0_verschieden = 0
    for land in _instanzen():
        n = land.zuege
        perm = list(range(n))
        rng.shuffle(perm)
        s = np.arange(land.zustaende)
        neu = np.zeros_like(s)
        for i in range(n):
            neu |= ((s >> i) & 1) << perm[i]                 # Zustand s heißt nach dem Umnummerieren neu[s]
        V2 = np.zeros_like(land.V)
        V2[neu] = land.V
        k0, r0 = _zahlen(land.V, land.nbi)
        k1, r1 = _zahlen(V2, land.nbi)
        assert k1 == k0
        for name in ("R1", "R2"):
            assert r1[name]["erfolg"] == pytest.approx(r0[name]["erfolg"], **TOL)
            assert r1[name]["scans"] == pytest.approx(r0[name]["scans"], **TOL)
        r0_verschieden += abs(r1["R0"]["erfolg"] - r0["R0"]["erfolg"]) > 1e-12
    assert r0_verschieden > 0          # die Ausnahme ist echt: R0 hängt an der Zugreihenfolge


def test_umnummerieren_der_staedte_aendert_die_zahlen_nicht():
    rng = SplitMix64(77)
    for seed in range(6):
        punkte = S.gitter_punkte(7, 9000 + seed)
        gemischt = list(punkte)
        rng.shuffle(gemischt)
        a = S.tour_landschaft(punkte, "manhattan")
        b = S.tour_landschaft(gemischt, "manhattan")
        ka, ra = _zahlen(a.V, a.nbi)
        kb, rb = _zahlen(b.V, b.nbi)
        assert ka == kb
        for name in ("R1", "R2"):
            assert ra[name]["erfolg"] == pytest.approx(rb[name]["erfolg"], **TOL)


def test_r2_ohne_seitwaertsschritte_ist_r1():
    for land in _instanzen():
        r = R.alle_regeln(land.V, land.nbi, 0)
        assert r["R2"]["erfolg"] == pytest.approx(r["R1"]["erfolg"], **TOL)
        assert r["R2"]["scans"] == pytest.approx(r["R1"]["scans"], **TOL)


def test_ohne_gleichstand_sind_alle_regeln_gleich():
    """Werte ohne jeden Gleichstand (eine Permutation der Zahlen 0 … S-1): R0 = R1 = R2, ν = 0, schwach = streng = geschlossen."""
    rng = SplitMix64(5)
    for n in (4, 6, 8):
        werte = list(range(1 << n))
        rng.shuffle(werte)
        V = np.array(werte)
        k, r = _zahlen(V, S.bit_nachbarn(n))
        assert k.gleiche_paare == 0 and k.plateaus == 0 and k.schwach == k.streng == k.geschlossen and k.scheinoptima == 0
        for name in ("R1", "R2"):
            assert r[name]["erfolg"] == pytest.approx(r["R0"]["erfolg"], **TOL)
            assert r[name]["auswertungen"] == pytest.approx(r["R0"]["auswertungen"], **TOL)


def test_r2_trifft_nie_seltener_als_r1():
    """Kopplung: R2 geht denselben Weg wie R1, bis R1 stehen bleibt; danach wird der Wert nie schlechter."""
    for land in _instanzen(30):
        for seit in (1, 3, 50):
            r = R.alle_regeln(land.V, land.nbi, seit)
            assert r["R2"]["erfolg"] >= r["R1"]["erfolg"] - 1e-12
            assert r["R2"]["scans"] >= r["R1"]["scans"] - 1e-12


def test_ordnung_der_zaehlweisen_und_summe_der_einzugsgebiete():
    """streng <= geschlossen <= schwach; Scheinoptima <= schwach - streng; die Einzugsgebiete unter R0 zerlegen den Raum."""
    for land in _instanzen():
        k = L.kennzahlen(land.V, land.nbi)
        assert k.streng <= k.geschlossen <= k.schwach
        assert k.scheinoptima <= k.schwach - k.streng
        assert k.gleiche_paare % 2 == 0                       # symmetrische Nachbarschaft: jedes gleiche Paar zählt in beiden Richtungen
        r0 = R.regel_r0(land.V, land.nbi)
        gebiete = np.bincount(r0["ende"], minlength=land.zustaende)
        assert gebiete.sum() == land.zustaende
        e = L.einteilung(land.V, land.nbi)
        assert set(np.nonzero(gebiete)[0]) <= set(np.nonzero(e["schwach"])[0])     # jeder Abstieg endet in einem schwachen Optimum


def test_erfolg_liegt_zwischen_null_und_eins_und_kosten_mindestens_eine_durchsuchung():
    for land in _instanzen():
        r = R.alle_regeln(land.V, land.nbi, 50)
        for name in R.REGELN:
            assert 0.0 <= r[name]["erfolg"] <= 1.0 + 1e-12
            assert r[name]["scans"] >= 1.0 and r[name]["auswertungen"] == pytest.approx(1 + land.zuege * r[name]["scans"], rel=1e-12)
        assert r["R0"]["erfolg"] >= (land.V == land.V.min()).mean() - 1e-12       # mindestens die Starts im Optimum selbst
