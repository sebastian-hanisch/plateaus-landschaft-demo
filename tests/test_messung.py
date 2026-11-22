"""Eingefrorene Messreihen (data/pll_*.json): Aufbau, Herkunftsangaben und Neu-Rechnen einzelner Instanzen als Band
(Gleitkommazahlen relativ 1e-9; die Summen können sich je Plattform im letzten Bit unterscheiden)."""

import importlib.util
import json
from pathlib import Path

import pytest

import pll_evaluation as ev
import pll_messung as M
import pll_rules as R
import pll_scenario as S

ROOT = Path(__file__).resolve().parent.parent
TEILE = ("stufen", "zellen14", "zellen16k2", "zellen16k4", "zellen16k8", "gitter8", "gitter9", "gitter10", "zufall89", "zufall10", "budget_nk", "budget_gitter", "stetig")
BAND = dict(rel=1e-9, abs=1e-12)


def _werkzeug():
    spec = importlib.util.spec_from_file_location("pll_make_frozen", ROOT / "tools" / "pll_make_frozen.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_jede_datei_nennt_quelle_stand_und_parameter():
    for teil in TEILE:
        d = json.loads((ROOT / "data" / f"pll_{teil}.json").read_text(encoding="utf-8"))
        assert d["quelle"].startswith("tools/pll_make_") and d["stand"] == "2026-11-21" and d["parameter"], teil
    assert set(_werkzeug().TEILE) == set(TEILE) - {"stetig"}


def test_umfang_der_messreihen():
    assert sorted(ev.stufen_zeilen("A")) == list(M.STUFEN_REIHE) == sorted(ev.stufen_zeilen("B"))
    assert len(ev.nk_zellen("A")) == 18 and len(ev.grobe_zellen("A")) == 12 and len(ev.nk_zellen("B")) == 9
    assert len(ev.gitter_zellen("A")) == 9 and len(ev.gitter_zellen("B")) == 6
    assert len(ev.zufall_zellen("A")) == 12 and len(ev.zufall_zellen("B")) == 8
    assert sorted(ev.budget_nk("A")) == [2, 4, 8] and all(len(z) == 4 for z in ev.budget_nk("A").values())
    assert [z["budget"] for z in ev.budget_nk("A")[2]] == [280, 1680, 8400, 42000]
    assert [z["budget"] for z in ev.budget_gitter("A")[9]] == [540, 3240] and [z["budget"] for z in ev.budget_gitter("A")[10]] == [700, 4200]
    for zellen in (ev.nk_zellen("A"), ev.gitter_zellen("A"), ev.zufall_zellen("A"), ev.stufen_zeilen("A")):
        assert all(z["instanzen"] == 30 for z in zellen.values())


def test_neu_rechnen_einzelner_nk_instanzen_im_band():
    zelle = ev.nk_zellen("A")[(14, 3, 2)]
    for i in (0, 7, 29):
        z = M.instanz_zeile(S.nk_landschaft(14, 2, 3, M.seeds("A")[i]))
        for name in R.REGELN:
            assert z[f"erfolg_{name}"] == pytest.approx(zelle["erfolg_je_instanz"][name][i], **BAND)


def test_neu_rechnen_einer_ganzen_zelle_im_band():
    neu = M.gitter_zelle(8, "manhattan", "A")
    alt = ev.gitter_zellen("A")[(8, "manhattan")]
    assert not _werkzeug().gleich(json.loads(json.dumps(neu)), alt)
    neu = M.zufall_zelle("netz", 8, "B")
    assert not _werkzeug().gleich(json.loads(json.dumps(neu)), ev.zufall_zellen("B")[("netz", 8)])


def test_neu_rechnen_einer_budget_instanz_im_band():
    land = S.nk_landschaft(14, 2, 3, M.seeds("A")[0])
    inst = M.budget_instanz(land, [c * 14 for c in M.BUDGET_C], 1000 * 2 + 0, "A")
    for b, zeile in enumerate(ev.budget_nk("A")[2]):
        assert inst["R2"]["luecke"][b] - inst["R0"]["luecke"][b] == pytest.approx(zeile["d_je_instanz"][0], **BAND)


def test_vergleich_mit_band_meldet_abweichungen():
    gleich = _werkzeug().gleich
    assert gleich({"a": [1.0, 2]}, {"a": [1.0 + 1e-12, 2]}) == []
    assert gleich({"a": [1.0, 2]}, {"a": [1.001, 2]}) and gleich({"a": [1.0, 2]}, {"a": [1.0, 3]})
    assert gleich({"a": 1}, {"b": 1}) and gleich([1], [1, 2])


def test_bootstrap_intervall():
    assert M.bootstrap_intervall([0.5] * 30, 1) == (0.5, 0.5)
    unten, oben = M.bootstrap_intervall([float(i) for i in range(30)], 2)
    assert 10.0 < unten < 14.5 < oben < 19.0                         # Mittel 14,5; Standardfehler etwa 1,6
    assert M.bootstrap_intervall([float(i) for i in range(30)], 2) == (unten, oben)       # fester Zufalls-Seed, gleiche Ziehungen


def test_zusammenfassung_einer_zelle_von_hand():
    zeilen = [
        {"nu": 0.2, "anteil_mit_gleichem": 0.5, "anteil_groesstes": 0.1, "schwach": 10, "streng": 2, "geschlossen": 4, "plateaus": 3, "anteil_schein": 0.5,
         "globale_optima": 1, "erfolg_R0": 0.2, "erfolg_R1": 0.25, "erfolg_R2": 0.5, "ausw_R0": 50.0, "ausw_R1": 50.0, "ausw_R2": 300.0},
        {"nu": 0.0, "anteil_mit_gleichem": 0.0, "anteil_groesstes": 0.0, "schwach": 2, "streng": 2, "geschlossen": 2, "plateaus": 0, "anteil_schein": 0.0,
         "globale_optima": 2, "erfolg_R0": 0.4, "erfolg_R1": 0.35, "erfolg_R2": 0.35, "ausw_R0": 70.0, "ausw_R1": 70.0, "ausw_R2": 100.0},
    ]
    z = M.zelle_zusammenfassen(zeilen)
    assert z["schwach"] == 6.0 and z["geschlossen"] == 3.0 and z["faktor"] == 2.0 and z["nu"] == pytest.approx(0.1) and z["nu_max"] == 0.2
    assert z["schwach_ungleich_streng"] == 1 and z["mehrere_globale_optima"] == 1
    assert z["erfolg_R2"] == pytest.approx(0.425) and z["ausw_R2"] == 200.0 and z["treffer_R2"] == pytest.approx(1000 * 0.425 / 200)
    assert z["d_R1_mittel"] == pytest.approx(0.0) and z["d_R1_min"] == pytest.approx(-0.05) and z["d_R1_max"] == pytest.approx(0.05)
    assert z["d_R2_mittel"] == pytest.approx(0.125) and z["r2_unter_r0"] == 1 and z["r2_unter_r1"] == 0
    assert z["kostenfaktor_R2"] == pytest.approx(200 / 60)


def test_stetig_datei_hat_beide_verfahren_und_stroeme():
    for strom in ("A", "B"):
        zellen = ev.stetig_zellen(strom)
        assert sorted(zellen) == [(d, v) for d in (2, 4, 8) for v in ("lm", "newton")]
        for z in zellen.values():
            assert z["instanzen"] == 10 and z["starts"] == 300 and 0.0 <= z["konvergenz"] <= 1.0
            assert z["sattelanteil"] is None or 0.0 <= z["sattelanteil"] <= 1.0
