"""Kopie-Test: pll_basis.py ist die unveränderte gemeinsame Basis der Reihe und liefert mit pll_rng.py (SplitMix64) dieselben
Prüfwerte wie die Referenzfassung (tests/data/basis_eingefroren.json: Koordinaten, Längen, NK-Werte, Zufalls-Seeds)."""

import json
from pathlib import Path

import pll_basis as B
from pll_rng import SplitMix64

DATEN = json.loads((Path(__file__).resolve().parent / "data" / "basis_eingefroren.json").read_text(encoding="utf-8"))


def test_rundtour_punkte_und_laengen_wie_in_der_referenz():
    assert len(DATEN["rundtour"]) == 12
    for e in DATEN["rundtour"]:
        assert B.instanz_seed(e["familie"], e["n"], e["idx"]) == e["seed"]
        punkte = B.rundtour_punkte(SplitMix64(e["seed"]), e["familie"], e["n"])
        assert [list(p) for p in punkte[:4]] == e["erste_punkte"]
        assert sum(p[0] for p in punkte) == e["summe_x"] and sum(p[1] for p in punkte) == e["summe_y"]
        assert repr(B.tourlaenge(B.abstaende(punkte), list(range(e["n"])))) == e["laenge_identitaet"]


def test_nk_werte_wie_in_der_referenz():
    assert len(DATEN["nk"]) == 6
    for e in DATEN["nk"]:
        n = e["n"]
        tab = B.nk_tabellen(SplitMix64(e["seed"]), n, e["k"], e["stufen"])
        zustaende = [[0] * n, [1] * n, [(i * 7 + 3) % 2 for i in range(n)], [1 if i % 3 == 0 else 0 for i in range(n)]]
        assert [repr(B.nk_wert(tab, x)) for x in zustaende] == e["werte"]


def test_lauf_seeds_wie_in_der_referenz():
    assert B.lauf_seed(0, 0, 0) == DATEN["seeds"]["lauf_seed_0_0_0"]
    assert B.lauf_seed(5, 2, 7) == DATEN["seeds"]["lauf_seed_5_2_7"]


def test_familien_und_kein_verbotener_name():
    assert B.FAMILIEN == ("gleich", "cluster", "gitter", "netz")
