"""Handbeispiele des Plans als exakte Tests (Brüche und ganze Zahlen): Würfel H1 und H1b, Tour H2, Gleitkomma H3, Kosinus H4.

Die erwarteten Werte stehen als Handrechnung im Test; gerechnet wird mit den Routinen der Demo."""

import itertools
import math
from fractions import Fraction as Fr

import numpy as np
import pytest

import pll_evaluation as ev
import pll_landscape as L
import pll_rules as R
import pll_scenario as S

EXAKT = dict(rel=0, abs=1e-12)


def test_h1_neutralitaet_optima_plateaus():
    w = S.wuerfel(S.WUERFEL_H1)
    k = L.kennzahlen(w.V, w.nbi)
    # gleich sind nur die Paare {000, 001} und {000, 100}: 4 von 24 geordneten Paaren
    assert (k.gleiche_paare, k.paare) == (4, 24) and Fr(k.gleiche_paare, k.paare) == Fr(1, 6)
    e = L.einteilung(w.V, w.nbi)
    assert list(np.nonzero(e["schwach"])[0]) == [0b000, 0b011, 0b110]
    assert list(np.nonzero(e["streng"])[0]) == [0b011, 0b110]
    assert list(np.nonzero(e["schein"])[0]) == [0b000]
    assert (k.schwach, k.streng, k.geschlossen, k.plateaus, k.groesstes_plateau, k.scheinoptima) == (3, 2, 2, 1, 3, 1)
    assert sorted(np.nonzero(e["marke"] == e["marke"][0])[0]) == [0b000, 0b001, 0b100]      # das Plateau
    assert k.mit_gleichem_nachbarn == 3 and k.globale_optima == 1


def test_h1_tabelle_der_nachbarwerte():
    w = S.wuerfel(S.WUERFEL_H1)
    erwartet = {0b000: [2, 1, 2], 0b001: [2, 4, 0], 0b010: [4, 2, 3], 0b011: [1, 2, 2], 0b100: [0, 3, 2], 0b101: [2, 2, 2], 0b110: [2, 2, 1], 0b111: [3, 0, 4]}
    assert {s: list(w.werte[w.nbi[s]]) for s in range(8)} == erwartet


def test_h1_erfolg_und_kosten_der_drei_regeln():
    w = S.wuerfel(S.WUERFEL_H1)
    r = R.alle_regeln(w.V, w.nbi, 50)
    # R0: 000, 100, 101, 110 scheitern; 001, 010, 011, 111 treffen: 4/8. R1: 101 hat drei beste Nachbarn, zwei führen zum Ziel: (4 + 2/3)/8 = 7/12.
    # R2: zusätzlich geht 000 seitwärts zu 001 (Ziel) oder 100 (scheitert), und 101 erreicht 000 nicht: (4 + 2/3 + 1/2)/8 = 31/48.
    assert r["R0"]["erfolg"] == pytest.approx(4 / 8, **EXAKT)
    assert r["R1"]["erfolg"] == pytest.approx((4 + Fr(2, 3)) / 8, **EXAKT) and (4 + Fr(2, 3)) / 8 == Fr(7, 12)
    assert r["R2"]["erfolg"] == pytest.approx((4 + Fr(2, 3) + Fr(1, 2)) / 8, **EXAKT) and (4 + Fr(2, 3) + Fr(1, 2)) / 8 == Fr(31, 48)
    # Durchsuchungen je Start (R0): 1, 2, 2, 1, 2, 3, 1, 2 = 14, also 14/8; Auswertungen 1 + 3 * 14/8 = 25/4
    assert r["R0"]["scans"] == pytest.approx((1 + 2 + 2 + 1 + 2 + 3 + 1 + 2) / 8, **EXAKT)
    assert r["R0"]["auswertungen"] == pytest.approx(25 / 4, **EXAKT) and r["R1"]["auswertungen"] == pytest.approx(25 / 4, **EXAKT)
    assert r["R2"]["auswertungen"] == pytest.approx(1 + 3 * 16 / 8, **EXAKT)
    # Auswertungen je Treffer: 12,5 gegen 7 * 48 / 31 = 10,84
    assert r["R0"]["auswertungen"] / r["R0"]["erfolg"] == pytest.approx(12.5, **EXAKT)
    assert r["R2"]["auswertungen"] / r["R2"]["erfolg"] == pytest.approx(7 * 48 / 31, **EXAKT)
    assert r["R0"]["treffer_je_1000"] == pytest.approx(1000 / 12.5, **EXAKT)


def test_h1_seitwaertsgrenze_null_ist_r1_und_eins_genuegt():
    w = S.wuerfel(S.WUERFEL_H1)
    assert R.alle_regeln(w.V, w.nbi, 0)["R2"]["erfolg"] == pytest.approx(7 / 12, **EXAKT)
    assert R.alle_regeln(w.V, w.nbi, 1)["R2"]["erfolg"] == pytest.approx(31 / 48, **EXAKT)


def test_h1b_seitwaertsschritte_unter_r0():
    w = S.wuerfel(S.WUERFEL_H1B)
    for seit in (3, 50):
        r = R.alle_regeln(w.V, w.nbi, seit)
        assert r["R0"]["erfolg"] == pytest.approx(7 / 8, **EXAKT)
        assert r["R1"]["erfolg"] == pytest.approx(13 / 16, **EXAKT)
        assert r["R2"]["erfolg"] == pytest.approx(13 / 16, **EXAKT)


def test_h1b_alle_6305_wertetabellen_r2_nie_unter_r1_und_56_mal_unter_r0():
    nbi = S.bit_nachbarn(3)
    tabellen = unter_r1 = unter_r0 = 0
    for werte in itertools.product(range(3), repeat=8):
        if max(werte) != 2:
            continue
        tabellen += 1
        r = R.alle_regeln(-np.array(werte), nbi, 3)
        unter_r1 += r["R2"]["erfolg"] < r["R1"]["erfolg"] - 1e-12
        unter_r0 += r["R2"]["erfolg"] < r["R0"]["erfolg"] - 1e-12
    assert tabellen == 3 ** 8 - 2 ** 8 == 6305
    assert unter_r1 == 0
    assert unter_r0 == 56


def test_h2_tour_mit_sieben_staedten():
    t = S.tour_landschaft(S.TOUR_H2, "manhattan")
    k = L.kennzahlen(t.V, t.nbi)
    assert (k.zustaende, k.zuege) == (360, 7 * 4 // 2)
    verteilung = sorted((int(v), int(c)) for v, c in zip(*np.unique(t.werte, return_counts=True)))
    assert verteilung == [(14, 1), (16, 6), (18, 23), (20, 60), (22, 73), (24, 80), (26, 71), (28, 38), (30, 8)]
    assert Fr(k.gleiche_paare, k.paare) == Fr(4, 15)
    assert (k.plateaus, k.groesstes_plateau, k.schwach, k.streng, k.geschlossen, k.scheinoptima) == (8, 80, 2, 1, 1, 1)
    e = L.einteilung(t.V, t.nbi)
    schwach = [tuple(int(c) for c in t.touren[i]) for i in np.nonzero(e["schwach"])[0]]
    assert schwach == [(0, 1, 2, 3, 4, 5, 6), (0, 1, 3, 4, 5, 6, 2)]
    stern = int(np.nonzero(e["schein"])[0][0])
    assert t.werte[stern] == 16 and sorted(int(x) for x in t.werte[t.nbi[stern]]) == [16, 16, 16, 18, 18, 18, 18, 20, 20, 20, 20, 22, 22, 24]
    assert e["groesse"][stern] == 4 and e["ausgang"][stern]


def test_h3_gleich_bei_gleitkommazahlen():
    a1, a2 = (0.1 + 0.2) + 0.3, 0.1 + (0.2 + 0.3)
    assert a1 != a2 and abs(a1 - a2) < 1e-15
    streng = S.laengen_zu_stufen(np.array([a1, a2]), "streng")
    toleranz = S.laengen_zu_stufen(np.array([a1, a2]), "toleranz")
    assert streng[0] != streng[1] and toleranz[0] == toleranz[1]
    w = math.sqrt(2)
    assert S.laengen_zu_stufen(np.array([w + 1 + w + 1 + 1, 1 + w + 1 + w + 1]), "toleranz").tolist() == [5828427125, 5828427125]


def test_h4_summe_von_kosinus():
    for d in (2, 3, 4, 5):
        zahl = {"max": 0, "min": 0, "sattel": 0}
        for muster in itertools.product((0, 1), repeat=d):       # 1 = π; Hesse-Matrix diag(-cos x_i): -1 bei 0, +1 bei π
            positiv = sum(muster)
            zahl["max" if positiv == 0 else ("min" if positiv == d else "sattel")] += 1
        assert ev.sattel_summe_kosinus(d) == (2 ** d, zahl["sattel"], float(Fr(zahl["sattel"], 2 ** d)))
        assert zahl["max"] == zahl["min"] == 1 and zahl["sattel"] == 2 ** d - 2
    assert [ev.sattel_summe_kosinus(d)[2] for d in (2, 4, 8)] == [0.5, 0.875, 0.9921875]
