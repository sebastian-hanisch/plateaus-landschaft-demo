"""Randfälle der Kernroutinen: entartete Landschaften, kleinste Größen, Grenzen der Regler."""

import numpy as np
import pytest

import pll_evaluation as ev
import pll_landscape as L
import pll_rules as R
import pll_scenario as S


def test_alle_werte_gleich_ist_ein_geschlossenes_plateau():
    V = np.zeros(8, dtype=np.int64)
    nbi = S.bit_nachbarn(3)
    k = L.kennzahlen(V, nbi)
    assert k.nu == 1.0 and (k.plateaus, k.groesstes_plateau, k.geschlossen) == (1, 8, 1)
    assert (k.schwach, k.streng, k.scheinoptima, k.globale_optima) == (8, 0, 0, 8)
    r = R.alle_regeln(V, nbi, 50)
    for name in R.REGELN:
        assert r[name]["erfolg"] == pytest.approx(1.0)
    assert r["R0"]["scans"] == 1.0 and r["R1"]["scans"] == 1.0
    assert r["R2"]["scans"] == pytest.approx(51.0)                # 50 Seitwärtsschritte und die letzte Durchsuchung


def test_ein_bit_zwei_zustaende():
    nbi = S.bit_nachbarn(1)
    k = L.kennzahlen(np.array([0, 1]), nbi)                      # Zustand 0 ist besser (kleiner)
    assert (k.zustaende, k.zuege, k.schwach, k.streng, k.geschlossen, k.gleiche_paare) == (2, 1, 1, 1, 1, 0)
    r = R.alle_regeln(np.array([0, 1]), nbi, 50)
    assert all(r[name]["erfolg"] == 1.0 for name in R.REGELN)
    assert r["R0"]["scans"] == pytest.approx(1.5)                # Start im Optimum: 1, sonst 2


def test_ein_einzelner_zustand_ohne_nachbarn():
    V, nbi = np.array([5]), np.zeros((1, 0), dtype=np.int64)
    k = L.kennzahlen(V, nbi)
    assert (k.zustaende, k.paare, k.nu, k.schwach, k.streng, k.geschlossen, k.plateaus) == (1, 0, 0.0, 1, 1, 1, 0)
    r = R.alle_regeln(V, nbi, 50)
    assert all(r[name]["erfolg"] == 1.0 and r[name]["auswertungen"] == 1.0 for name in R.REGELN)


def test_genau_ein_gleichstandspaar():
    V = -np.array([5, 5, 1, 2, 3, 0, 4, 6])                      # nur 000 und 001 sind gleich gut; 111 ist das Optimum
    k = L.kennzahlen(V, S.bit_nachbarn(3))
    assert (k.gleiche_paare, k.plateaus, k.groesstes_plateau, k.mit_gleichem_nachbarn) == (2, 1, 2, 2)


def test_mehrere_globale_optima_zaehlen_alle_als_treffer():
    V = -np.array([3, 0, 0, 3, 0, 3, 3, 0])                      # vier Optima (000, 011, 101, 110), keine zwei benachbart
    r = R.alle_regeln(V, S.bit_nachbarn(3), 50)
    assert L.kennzahlen(V, S.bit_nachbarn(3)).globale_optima == 4
    assert all(r[name]["erfolg"] == pytest.approx(1.0) for name in R.REGELN)


def test_gleitkomma_rauschen_unter_der_toleranz_zaehlt_als_gleich():
    laengen = np.array([10.0, 10.0 + 3e-13, 10.0 + 2e-6])
    assert len(set(S.laengen_zu_stufen(laengen, "toleranz")[:2].tolist())) == 1
    assert S.laengen_zu_stufen(laengen, "toleranz")[2] != S.laengen_zu_stufen(laengen, "toleranz")[0]
    assert len(set(S.laengen_zu_stufen(laengen, "streng").tolist())) == 3
    assert S.laengen_zu_stufen(np.array([4, 2, 4]), "streng").tolist() == [4, 2, 4]      # ganze Zahlen bleiben, wie sie sind


def test_grenzen_der_fahrzeuge():
    with pytest.raises(ValueError):
        S.wuerfel([1, 2, 3])
    with pytest.raises(ValueError):
        S.nk_landschaft(6, 2, 1, 0)
    with pytest.raises(ValueError):
        S.gitter_punkte(17, 0)
    with pytest.raises(ValueError):
        S.alle_touren(2)
    assert len(S.gitter_punkte(16, 0)) == 16 and len(set(S.gitter_punkte(16, 0))) == 16      # n = 16 inklusive
    assert S.nk_landschaft(4, 3, 2, 0).zustaende == 16                                       # K = N - 1 inklusive
    with pytest.raises(ValueError):
        R.budget_laeufe(np.array([0, 1]), S.bit_nachbarn(1), "R3", [5], [1])


def test_wuerfel_eingabe_wird_gelesen_begrenzt_oder_ersetzt():
    assert ev.wuerfel_werte("2, 2, 1, 4, 2, 0, 3, 2") == ((2, 2, 1, 4, 2, 0, 3, 2), True)
    assert ev.wuerfel_werte("2;2;1;4;2;0;3;2") == ((2, 2, 1, 4, 2, 0, 3, 2), True)
    assert ev.wuerfel_werte("1 2 3 4 5 6 7 500") == ((1, 2, 3, 4, 5, 6, 7, 99), True)        # begrenzt auf 99
    assert ev.wuerfel_werte("1, 2, 3") == (S.WUERFEL_H1, False)
    assert ev.wuerfel_werte("a, b") == (S.WUERFEL_H1, False)
    assert ev.wuerfel_werte("") == (S.WUERFEL_H1, False)


def test_kopplung_wird_auf_n_minus_eins_begrenzt():
    land = ev.landschaft(ev.Settings(fahrzeug="nk", n=10, k=8, stufen=2, seed=1))
    assert land.zustaende == 1024


def test_zahlformat():
    assert ev.de(0.5) == "0,50" and ev.de(1234.5, 1) == "1234,5" and ev.de(42000, 0) == "42 000"
    assert ev.vz(0.25, 2) == "+0,25" and ev.vz(-0.25, 2) == "-0,25" and ev.vz(0.0, 1) == "0,0"
