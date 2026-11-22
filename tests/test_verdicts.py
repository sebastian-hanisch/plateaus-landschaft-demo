"""Verdikte an von Hand gesetzten Werten: jede Schwelle der Art und jede Zahl im Text; dazu je Preset die erwartete Verdikt-Zeile.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Kennzahlen oder Zeilen, keine Zufalls-Seeds."""

import pytest

import pll_constants as C
import pll_evaluation as ev
import pll_landscape as L


def _kenn(**kw):
    basis = dict(zustaende=100, zuege=4, paare=400, gleiche_paare=40, mit_gleichem_nachbarn=30, schwach=10, streng=4, geschlossen=5,
                 plateaus=7, groesstes_plateau=12, scheinoptima=5, globale_optima=1)
    basis.update(kw)
    return L.Kennzahlen(**basis)


def _regeln(e0, e1, e2, a0=50.0, a1=50.0, a2=200.0):
    return {name: {"erfolg": e, "auswertungen": a, "scans": 1.0, "treffer_je_1000": 1000 * e / a} for name, e, a in (("R0", e0, a0), ("R1", e1, a1), ("R2", e2, a2))}


def test_verdict_optimum_drei_zweige():
    art, text = ev.verdict_optimum(_kenn())
    assert art == "warning" and "**10 schwache**" in text and "**4 strenge**" in text and "**5 geschlossene Plateaus**" in text and "5 der 10 schwachen" in text
    art, text = ev.verdict_optimum(_kenn(gleiche_paare=0, schwach=6, streng=6, geschlossen=6, scheinoptima=0))
    assert art == "info" and "keinen Gleichstand" in text and "6 schwache = 6 strenge Optima = 6 geschlossene Plateaus" in text
    art, text = ev.verdict_optimum(_kenn(gleiche_paare=2, schwach=6, streng=6, geschlossen=6, scheinoptima=0))
    assert art == "info" and "keiner liegt an einem Optimum" in text and "ν = 0,0050" in text


def test_verdict_neutral():
    art, text = ev.verdict_neutral(_kenn())
    assert art == "success" and "**ν = 0,1000**" in text and "40 von 400" in text and "30,0 % der 100 Zustände" in text
    assert "7 Plateaus" in text and "12 Zustände (12,0 % des Raums)" in text
    art, text = ev.verdict_neutral(_kenn(gleiche_paare=0))
    assert art == "info" and "Keine Neutralität" in text and "400 geordneten Nachbarpaaren" in text and "ν = 0" in text


def test_verdict_regeln_vier_zweige():
    art, text = ev.verdict_regeln(_regeln(0.2, 0.2, 0.2, 50, 50, 50), 50)
    assert art == "info" and "Alle drei Regeln sind hier gleich" in text
    art, text = ev.verdict_regeln(_regeln(0.5, 0.4, 0.45), 7)
    assert art == "warning" and "trifft R2 **seltener** als R0" in text and "S = 7" in text
    art, text = ev.verdict_regeln(_regeln(0.2, 0.2, 0.5, 50, 50, 500), 50)        # je Abstieg besser, je Auswertung schlechter: 4,00 gegen 1,00
    assert art == "warning" and "**je Auswertung** trifft R0 häufiger" in text
    assert "**0,2000** (R0), **0,2000** (R1), **0,5000** (R2, S = 50)" in text and "50,0 / 50,0 / 500,0" in text and "4,00 / 4,00 / 1,00" in text
    art, text = ev.verdict_regeln(_regeln(0.2, 0.2, 0.5, 50, 50, 100), 50)        # 4,00 gegen 5,00
    assert art == "success" and "lohnen hier auch je Auswertung" in text


def test_verdict_regeln_gleichheit_ist_inklusive():
    assert ev.verdict_regeln(_regeln(0.2, 0.2, 0.2 + 1e-14, 50, 50, 50), 50)[0] == "info"
    assert ev.verdict_regeln(_regeln(0.2, 0.2, 0.2 - 1e-6, 50, 50, 50), 50)[0] == "warning"


def test_verdict_wuerfel_und_tour():
    art, text = ev.verdict_wuerfel(_kenn(zustaende=8, zuege=3, paare=24, gleiche_paare=4, schwach=3, streng=2, geschlossen=2, scheinoptima=1), _regeln(0.5, 7 / 12, 31 / 48, 6.25, 6.25, 7.0), 50)
    assert art == "warning" and "3 schwache, 2 strenge Optima, 2 geschlossene Plateaus, 1 Scheinoptima" in text and "ν = 4/24 = 0,1667" in text
    assert "0,5000 / 0,5833 / 0,6458" in text and "6,25 / 6,25 / 7,00" in text
    assert ev.verdict_wuerfel(_kenn(scheinoptima=0), _regeln(0.5, 0.5, 0.5), 50)[0] == "info"
    art, text = ev.verdict_tour7(_kenn(zustaende=360, zuege=14, schwach=2, streng=1, geschlossen=1, plateaus=8, groesstes_plateau=80, paare=5040, gleiche_paare=1344))
    assert art == "info" and "360 Touren, 14 Nachbarn" in text and "2 schwache Optima, 1 strenges, 1 geschlossenes Plateau, 8 Plateaus (das größte mit 80 Touren)" in text and "ν = 0,2667" in text


def test_verdict_stufen():
    zeilen = {2: {"nu": 0.25, "instanzen": 30}, 30: {"nu": 0.015, "instanzen": 30}, 1000000: {"nu": 0.0, "instanzen": 30}}
    art, text = ev.verdict_stufen(zeilen)
    assert art == "success" and "0,2500 bei 2" in text and "0,0150 bei 30" in text and "0,0000 bei 1\u202f000\u202f000" in text and "über 30 Instanzen" in text
    zeilen[30]["nu"] = 0.3
    assert ev.verdict_stufen(zeilen)[0] == "warning"


def test_verdict_zufall():
    zelle = {"instanzen": 30, "schwach_ungleich_streng": 0, "mehrere_globale_optima": 0, "nu_max": 0.0}
    art, text = ev.verdict_zufall({("gleich", 8): zelle, ("netz", 9): dict(zelle)})
    assert art == "info" and "in 0 von 60 aufgezählten Instanzen" in text and "keinen einzigen Gleichstand" in text
    art, text = ev.verdict_zufall({("gleich", 8): zelle, ("netz", 9): dict(zelle, schwach_ungleich_streng=2, nu_max=0.001)})
    assert art == "warning" and "in 2 von 60" in text and "0,001000" in text


def test_verdict_toleranz():
    tol = {"nu": 0.04, "schwach": 3.6, "instanzen": 30}
    art, text = ev.verdict_toleranz(tol, {"nu": 0.03, "schwach": 3.2}, 9)
    assert art == "warning" and "n = 9" in text and "ν = 0,0300 bei bitgenauem" in text and "0,0400 mit Toleranz" in text and "übersieht 25 %" in text and "3,20 gegen 3,60" in text
    assert ev.verdict_toleranz({"nu": 0.0, "schwach": 2.0, "instanzen": 30}, {"nu": 0.0, "schwach": 2.0}, 8)[0] == "info"


def test_verdict_zaehlweise():
    nk = {(14, 3, 2): {"faktor": 12.0, "anteil_schein": 0.8}, (14, 4, 8): {"faktor": 1.9, "anteil_schein": 0.41}}
    gitter = {(8, "manhattan"): {"faktor": 21.0}, (8, "euklid_toleranz"): {"faktor": 1.7}, (8, "euklid_streng"): {"faktor": 99.0}}
    art, text = ev.verdict_zaehlweise(nk, gitter)
    assert art == "warning" and "**1,9 bis 12,0** in den 2 groben NK-Zellen" in text and "**1,7 bis 21,0** in den 2 Gitter-Zellen" in text and "41 bis 80 %" in text


def _zelle(**kw):
    z = dict(instanzen=30, d_R1_mittel=-0.005, d_R1_min=-0.04, d_R1_max=0.03, d_R2_mittel=0.25, d_R2_min=0.02, d_R2_max=0.6, r2_unter_r0=0, r2_unter_r1=0,
             kostenfaktor_R2=9.0, treffer_R0=4.0, treffer_R2=1.0)
    z.update(kw)
    return z


def test_verdict_gleichstand():
    zellen = {(14, 3, 2): _zelle(), (14, 4, 8): _zelle(d_R1_mittel=0.002, d_R1_max=0.05, d_R2_mittel=0.004, d_R2_min=-0.001, r2_unter_r0=6, kostenfaktor_R2=3.0, treffer_R2=1.6)}
    art, text = ev.verdict_gleichstand(zellen)
    assert art == "warning" and text.startswith("2 grobe NK-Zellen (N = 14; Stufen 3, 4; K = 2, 8; 60 Instanzen, exakt)")
    assert "um -0,0050 bis +0,0020" in text and "je Instanz um -0,040 bis +0,050" in text
    assert "um +0,0040 bis +0,2500" in text and "je Instanz -0,0010 bis +0,600" in text
    assert "in 1 der 2 Zellen" in text and "(6 Instanzen), unter R1 in 0" in text
    assert "das 3,0- bis 9,0-Fache" in text and "R0 2,5- bis 4,0-mal so oft" in text


def _bzeile(d, unten, oben, budget=280):
    return {"budget": budget, "d_R2_R0": d, "d_unten": unten, "d_oben": oben, "luecke_R0": 1.0, "luecke_R2": 1.0 + d}


def test_budget_bilanz_und_verdict_nk():
    zellen = {2: [_bzeile(1.0, 0.5, 1.5), _bzeile(0.0, 0.0, 0.0, 42000)], 4: [_bzeile(0.01, 0.0, 0.03), _bzeile(0.5, 0.1, 0.9, 42000)]}
    assert ev.budget_bilanz(zellen) == {"zellen": 4, "besser": 0, "schlechter": 3, "gleich": 1, "gesichert_schlechter": 2, "gesichert_besser": 0}
    art, text = ev.verdict_budget_nk(zellen)
    assert art == "warning" and "K = 2, 4" in text and "280, 42\u202f000 Auswertungen" in text and "**0 von 4 Zellen**" in text and "in 3 die größere" in text
    assert "in 1 dieselbe" in text and "in 2 Zellen ganz über 0 und in 0 ganz darunter" in text and "in keiner gemessenen Zelle besser" in text
    zellen[2][0] = _bzeile(-0.4, -0.7, -0.1)
    assert ev.budget_bilanz(zellen)["besser"] == 1 and ev.budget_bilanz(zellen)["gesichert_besser"] == 1
    assert ev.verdict_budget_nk(zellen)[0] == "info"


def test_verdict_budget_gitter_und_live():
    zellen = {9: [dict(_bzeile(-0.4, -0.7, -0.1, 540), luecke_R0=0.42, luecke_R2=0.02), dict(_bzeile(0.0, 0.0, 0.0, 3240), luecke_R0=0.0, luecke_R2=0.0)]}
    art, text = ev.verdict_budget_gitter(zellen)
    assert art == "success" and "n = 9, 540 Auswertungen: 0,42 % (R0) gegen 0,02 % (R2)" in text and "In 1 von 2 Zellen ist R2 gesichert besser" in text
    zellen[9][0]["d_oben"] = 0.1
    assert ev.verdict_budget_gitter(zellen)[0] == "info"
    live = [{"budget": 280, "luecke_R0": 2.0, "luecke_R2": 3.0}, {"budget": 42000, "luecke_R0": 0.0, "luecke_R2": 0.0}, {"budget": 540, "luecke_R0": 0.5, "luecke_R2": 0.1}]
    art, text = ev.verdict_budget_live(live, 100)
    assert art == "info" and "100 Läufe je Regel" in text and "280 Auswertungen: 2,00 % (R0) gegen 3,00 % (R2), R0 kleiner" in text
    assert "42\u202f000 Auswertungen: 0,00 % (R0) gegen 0,00 % (R2), gleich" in text and "540 Auswertungen: 0,50 % (R0) gegen 0,10 % (R2), R2 kleiner" in text


ERWARTET = {
    "Von Hand (Würfel, 8 Zustände)": ("warning", "success", "success"),
    "Von Hand (Tour, 7 Städte)": ("warning", "success", None),
    "NK grob (3 Stufen)": ("warning", "success", "warning"),
    "NK fein (Kontrolle)": ("info", "info", "info"),
    "Gitter Manhattan n = 9": ("warning", "success", None),
    "Gitter euklidisch n = 9": ("warning", "success", None),
    "Zufallskoordinaten": ("info", "info", "info"),
    "Würfel: Seitwärts ohne Nutzen": ("warning", "success", "warning"),
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_je_preset_die_erwartete_verdikt_zeile(name):
    """„NK fein“ meldet KEINE Neutralität, „Zufallskoordinaten“ KEINE Plateaus; die groben Presets melden die Zählweisen-Falle."""
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    optimum, neutral, regeln = ERWARTET[name]
    assert ev.verdict_optimum(a.kenn)[0] == optimum
    assert ev.verdict_neutral(a.kenn)[0] == neutral
    if regeln is not None:
        assert ev.verdict_regeln(a.regeln, a.seit)[0] == regeln
    if name in ("NK fein (Kontrolle)", "Zufallskoordinaten"):
        assert "keinen Gleichstand" in ev.verdict_optimum(a.kenn)[1] and "Keine Neutralität" in ev.verdict_neutral(a.kenn)[1]
        assert "Alle drei Regeln sind hier gleich" in ev.verdict_regeln(a.regeln, a.seit)[1]
    if name == "Würfel: Seitwärts ohne Nutzen":
        assert "seltener" in ev.verdict_regeln(a.regeln, a.seit)[1]
