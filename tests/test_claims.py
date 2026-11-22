"""Claims: jede Zahl der README wird hier nachgerechnet oder aus den eingefrorenen Messreihen neu formatiert und in der README gesucht.

Drei Arten (so steht es auch in der Zahl-Test-Tabelle der README):
* exakt: Handbeispiele und Zählungen, hier neu gerechnet;
* Datei: Zahl der eingefrorenen Messreihe (data/pll_*.json), hier aus der Datei formatiert; dass die Datei zur Rechnung passt,
  prüft tests/test_messung.py an einzelnen Instanzen als Band;
* Band: Aussage, die auch im zweiten Zufallsstrom (B) gelten muss.
Aufruf als Skript druckt alle Textbausteine: python tests/test_claims.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pll_constants as C  # noqa: E402
import pll_evaluation as ev  # noqa: E402
import pll_messung as M  # noqa: E402
import pll_rules as R  # noqa: E402
import pll_scenario as S  # noqa: E402
from pll_evaluation import de, ganz, vz  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")


def _spanne(werte, stellen, faktor=1.0):
    return f"{de(faktor * min(werte), stellen)} bis {de(faktor * max(werte), stellen)}"


def bausteine() -> dict:
    """Name -> Textbaustein, der wörtlich in der README steht (alle aus Strom A, wenn nicht anders gesagt)."""
    g, gb = ev.grobe_zellen("A"), ev.grobe_zellen("B")
    nk = ev.nk_zellen("A")
    fein = {k: z for k, z in nk.items() if k[1] == M.FEIN}
    gi = ev.gitter_zellen("A")
    zu, zub = ev.zufall_zellen("A"), ev.zufall_zellen("B")
    st = ev.stufen_zeilen("A")
    b = {}
    b["nk_nu"] = "ν = " + _spanne([z["nu"] for z in g.values()], 3)
    b["nk_anteil"] = _spanne([z["anteil_mit_gleichem"] for z in g.values()], 0, 100) + " % der Zustände"
    b["nk_groesstes"] = _spanne([z["anteil_groesstes"] for z in g.values()], 1, 100) + " % des Zustandsraums"
    b["fein_nu_max"] = f"größter Neutralitätsgrad einer der {sum(z['instanzen'] for z in fein.values())} feinen Instanzen: {de(max(z['nu_max'] for z in fein.values()), 6)}"
    for v, name in (("manhattan", "Manhattan"), ("euklid_toleranz", "euklidisch mit Toleranz"), ("euklid_streng", "euklidisch bitgenau")):
        b[f"gitter_nu_{v}"] = f"{name}: ν = " + " / ".join(de(gi[(n, v)]["nu"], 3) for n in M.GITTER_N)
    b["gitter_nicht_streng"] = _spanne([1 - gi[(n, "manhattan")]["streng"] / gi[(n, "manhattan")]["schwach"] for n in M.GITTER_N], 1, 100) + " % der schwachen Optima"
    b["zufall_a"] = f"in {sum(z['schwach_ungleich_streng'] for z in zu.values())} von {sum(z['instanzen'] for z in zu.values())} Instanzen"
    b["zufall_b"] = f"in {sum(z['schwach_ungleich_streng'] for z in zub.values())} von {sum(z['instanzen'] for z in zub.values())} Instanzen"
    for s in M.STUFEN_REIHE:
        z = st[s]
        b[f"stufen_{s}"] = (f"| {ganz(s)} | {de(z['nu'], 4)} | {de(z['anteil_mit_gleichem'], 3)} | {de(z['schwach'], 1)} | {de(z['streng'], 1)} | "
                            f"{de(z['geschlossen'], 1)} | {de(z['anteil_schein'], 3)} |")
    b["faktor_nk"] = _spanne([z["faktor"] for z in g.values()], 1) + " bei NK"
    b["faktor_gitter"] = _spanne([z["faktor"] for (n, v), z in gi.items() if v != "euklid_streng"], 1) + " auf dem Gitter"
    b["schein_nk"] = _spanne([z["anteil_schein"] for z in g.values()], 0, 100) + " % der schwachen Optima"
    z = g[(16, 3, 2)]
    b["zelle_16_3_2"] = f"{de(z['schwach'], 1)} schwache, {de(z['streng'], 1)} strenge Optima und {de(z['geschlossen'], 1)} geschlossene Plateaus"
    z = gi[(10, "manhattan")]
    b["zelle_gitter_10"] = f"{de(z['schwach'], 1)} schwache Optima gegen {de(z['geschlossen'], 1)} geschlossene Plateaus"
    for key in ((14, 3, 2), (14, 3, 4), (14, 3, 8), (16, 3, 2), (16, 4, 2), (16, M.FEIN, 2)):
        z = nk[key]
        name = f"N = {key[0]}, {'fein' if key[1] == M.FEIN else str(key[1]) + ' Stufen'}, K = {key[2]}"
        b[f"regel_{key}"] = (f"| {name} | {de(z['erfolg_R0'], 4)} | {de(z['erfolg_R1'], 4)} | {de(z['erfolg_R2'], 4)} | {de(z['ausw_R0'], 1)} / {de(z['ausw_R2'], 1)} | "
                             f"{de(z['treffer_R0'], 2)} / {de(z['treffer_R2'], 2)} |")
    b["r1_mittel"] = "Zellenmittel " + f"{vz(min(z['d_R1_mittel'] for z in g.values()), 4)} bis {vz(max(z['d_R1_mittel'] for z in g.values()), 4)}"
    b["r1_instanz"] = "je Instanz " + f"{vz(min(z['d_R1_min'] for z in g.values()), 3)} bis {vz(max(z['d_R1_max'] for z in g.values()), 3)}"
    b["r1_instanz_b"] = "Strom B: " + f"{vz(min(z['d_R1_min'] for z in gb.values()), 3)} bis {vz(max(z['d_R1_max'] for z in gb.values()), 3)}"
    b["r2_mittel"] = "im Zellenmittel um " + f"{vz(min(z['d_R2_mittel'] for z in g.values()), 4)} bis {vz(max(z['d_R2_mittel'] for z in g.values()), 4)}"
    b["r2_instanz"] = "je Instanz " + f"{vz(min(z['d_R2_min'] for z in g.values()), 4)} bis {vz(max(z['d_R2_max'] for z in g.values()), 3)}"
    b["r2_unter_r0"] = (f"in {sum(1 for z in g.values() if z['r2_unter_r0'])} der {len(g)} Zellen ({sum(z['r2_unter_r0'] for z in g.values())} von {sum(z['instanzen'] for z in g.values())} Instanzen)")
    b["r2_unter_r0_b"] = (f"in {sum(1 for z in gb.values() if z['r2_unter_r0'])} der {len(gb)} Zellen ({sum(z['r2_unter_r0'] for z in gb.values())} von {sum(z['instanzen'] for z in gb.values())} Instanzen)")
    b["r2_min_b"] = "kleinster Wert " + vz(min(z["d_R2_min"] for z in gb.values()), 4)
    b["stufen_kurz"] = " / ".join(de(st[x]["nu"], 3 if x < 1000 else 4) for x in (2, 30, 1000))
    b["kosten"] = "das " + f"{de(min(z['kostenfaktor_R2'] for z in g.values()), 1)}- bis {de(max(z['kostenfaktor_R2'] for z in g.values()), 1)}-Fache"
    t = [z["treffer_R0"] / z["treffer_R2"] for z in g.values()]
    b["treffer"] = f"{de(min(t), 1)}- bis {de(max(t), 1)}-mal so oft"
    b["gitter_r2_mittel"] = "Manhattan " + " / ".join(vz(gi[(n, "manhattan")]["d_R2_mittel"], 3) for n in M.GITTER_N)
    b["gitter_r2_mittel_euklid"] = "euklidisch mit Toleranz " + " / ".join(vz(gi[(n, "euklid_toleranz")]["d_R2_mittel"], 3) for n in M.GITTER_N)
    b["gitter_r2_min"] = f"mindestens {de(min(min(gi[(n, 'manhattan')]['erfolg_je_instanz']['R2']) for n in M.GITTER_N), 5)}"
    b["gitter_kosten"] = "Manhattan das " + " / ".join(de(gi[(n, "manhattan")]["kostenfaktor_R2"], 1) for n in M.GITTER_N) + "-Fache"
    b["gitter_r2_unter_r0"] = (f"in {sum(gi[(n, 'euklid_toleranz')]['r2_unter_r0'] for n in M.GITTER_N)} von {sum(gi[(n, 'euklid_toleranz')]['instanzen'] for n in M.GITTER_N)} "
                               "euklidischen Gitter-Instanzen")
    for n in M.GITTER_N:
        tol, streng = gi[(n, "euklid_toleranz")], gi[(n, "euklid_streng")]
        b[f"toleranz_{n}"] = f"n = {n}: {de(streng['nu'], 4)} gegen {de(tol['nu'], 4)}"
    b["toleranz_anteil"] = _spanne([100 * (gi[(n, 'euklid_toleranz')]['nu'] - gi[(n, 'euklid_streng')]['nu']) / gi[(n, 'euklid_toleranz')]['nu'] for n in M.GITTER_N], 0) + " % der Gleichstände"
    for k, zeilen in sorted(ev.budget_nk("A").items()):
        for z in zeilen:
            b[f"budget_{k}_{z['budget']}"] = (f"| {k} | {ganz(z['budget'])} | {de(z['luecke_R0'], 3)} | {de(z['luecke_R2'], 3)} | {vz(z['d_R2_R0'], 3)} [{vz(z['d_unten'], 3)}; {vz(z['d_oben'], 3)}] | "
                                              f"{de(z['am_optimum_R0'], 2)} / {de(z['am_optimum_R2'], 2)} | {z['r2_besser_instanzen']} |")
    bil = ev.budget_bilanz(ev.budget_nk("A"))
    b["budget_bilanz"] = f"in {bil['besser']} von {bil['zellen']} Zellen besser, in {bil['schlechter']} schlechter, in {bil['gleich']} gleich; das 95-%-Intervall liegt in {bil['gesichert_schlechter']} Zellen ganz über 0"
    for n, zeilen in sorted(ev.budget_gitter("A").items()):
        z = zeilen[0]
        b[f"budget_gitter_{n}"] = f"n = {n}, {z['budget']} Auswertungen: {de(z['luecke_R0'], 2)} % (R0) gegen {de(z['luecke_R2'], 2)} % (R2), Differenz {vz(z['d_R2_R0'], 2)} [{vz(z['d_unten'], 2)}; {vz(z['d_oben'], 2)}]"
    stet, stetb = ev.stetig_zellen("A"), ev.stetig_zellen("B")
    for d in (2, 4, 8):
        for v in ("newton", "lm"):
            z = stet[(d, v)]
            anteil = de(z["sattelanteil"], 2) if z["sattelanteil"] is not None else "kein Punkt"
            b[f"stetig_{d}_{v}"] = f"| {d} | {'Newton' if v == 'newton' else 'Levenberg-Marquardt'} | {de(100 * z['konvergenz'], 1)} % | {de(z['punkte_je_instanz'], 1)} | {anteil} |"
    zb = stetb[(4, "newton")], stetb[(4, "lm")]
    b["stetig_b"] = f"Strom B bei d = 4: {de(zb[0]['sattelanteil'], 2)} (Newton) gegen {de(zb[1]['sattelanteil'], 2)} (Levenberg-Marquardt)"
    ma, mb = ev.stetig_mehr_starts("A"), ev.stetig_mehr_starts("B")
    b["stetig_mehr"] = (f"{de(ma['punkte_je_instanz'], 1)} statt {de(stet[(4, 'newton')]['punkte_je_instanz'], 1)} Punkte je Instanz, Sattelanteil {de(ma['sattelanteil'], 2)} statt "
                        f"{de(stet[(4, 'newton')]['sattelanteil'], 2)} (Strom B: {de(mb['sattelanteil'], 2)} statt {de(stetb[(4, 'newton')]['sattelanteil'], 2)})")
    b["stetig_d8"] = f"Bei d = 8 stützen sich die Anteile auf wenige Punkte (Strom A: Newton {de(stet[(8, 'newton')]['sattelanteil'], 2)}, Strom B: {de(stetb[(8, 'newton')]['sattelanteil'], 2)})"
    b["stetig_lm8"] = f"in {stet[(8, 'lm')]['instanzen_mit_punkten']} von {stet[(8, 'lm')]['instanzen']} Instanzen"
    return b


def test_jeder_baustein_aus_den_messreihen_steht_woertlich_in_der_readme():
    fehlend = {name: text for name, text in bausteine().items() if text not in README}
    assert not fehlend, fehlend


def test_handbeispiele_der_readme_exakt():
    w = ev.analyse_land(S.wuerfel(S.WUERFEL_H1), 50)
    assert (w.kenn.schwach, w.kenn.streng, w.kenn.geschlossen, w.kenn.scheinoptima, w.kenn.gleiche_paare, w.kenn.paare) == (3, 2, 2, 1, 4, 24)
    assert "ν = 4/24 = 1/6" in README and "drei schwache, zwei strenge Optima, aber zwei geschlossene Plateaus" in README
    assert abs(w.regeln["R0"]["erfolg"] - 1 / 2) < 1e-12 and abs(w.regeln["R1"]["erfolg"] - 7 / 12) < 1e-12 and abs(w.regeln["R2"]["erfolg"] - 31 / 48) < 1e-12
    assert "1/2 (R0), 7/12 (R1) und 31/48 (R2)" in README
    assert abs(w.regeln["R0"]["auswertungen"] - 6.25) < 1e-12 and abs(w.regeln["R2"]["auswertungen"] - 7) < 1e-12
    assert "6,25 (R0 und R1) und 7 (R2)" in README and "12,5 gegen 10,84 Auswertungen je Treffer" in README
    assert de(w.regeln["R2"]["auswertungen"] / w.regeln["R2"]["erfolg"], 2) == "10,84"
    b1 = ev.analyse_land(S.wuerfel(S.WUERFEL_H1B), 3)
    assert abs(b1.regeln["R0"]["erfolg"] - 7 / 8) < 1e-12 and abs(b1.regeln["R2"]["erfolg"] - 13 / 16) < 1e-12 and "7/8 (R0) gegen 13/16 (R1 und R2)" in README
    assert "56 von 6 305" in README                                                # gezählt in tests/test_handbeispiele.py
    t = ev.analyse_land(S.tour_landschaft(S.TOUR_H2, "manhattan"), 50)
    assert (t.kenn.zustaende, t.kenn.zuege, t.kenn.schwach, t.kenn.streng, t.kenn.geschlossen, t.kenn.plateaus, t.kenn.groesstes_plateau) == (360, 14, 2, 1, 1, 8, 80)
    assert t.kenn.gleiche_paare * 15 == t.kenn.paare * 4 and "ν = 4/15" in README
    assert "360 Touren" in README and "acht Plateaus, das größte mit 80 Touren" in README


def test_zaehlungen_der_readme():
    assert len(S.alle_touren(9)) == 20160 and len(S.alle_touren(8)) == 2520 and S.zwei_opt_nachbarn(9).shape[1] == 27
    assert "20 160 Touren" in README and "27 Nachbarn" in README and "181 440" in README           # 9!/2 = 181 440 für n = 10
    assert 2 ** 16 == 65536 and "65 536" in README
    assert ev.sattel_summe_kosinus(4) == (16, 14, 0.875) and "0,5 / 0,875 / 0,992" in README
    fein_max = max(z["nu_max"] for key, z in ev.nk_zellen("A").items() if key[1] == M.FEIN)
    assert abs(fein_max - 2 / (2 ** 14 * 14)) < 1e-15 and "ein einzelnes gleich gutes Nachbarpaar" in README      # zwei geordnete Paare von 2^14 * 14
    assert M.INSTANZEN == 30 and M.BUDGET_LAEUFE == 100 and M.BOOTSTRAP == 2000 and R.SEIT_STANDARD == 50
    assert len(C.PRESETS) == 8 and "acht Presets" in README


def test_band_die_aussagen_gelten_auch_im_zweiten_zufallsstrom():
    """Gegenprobe (Strom B, andere Instanzen): Richtung und Größenordnung jeder Kernaussage; keine bitgleichen Zahlen."""
    a, b = ev.stufen_zeilen("A"), ev.stufen_zeilen("B")
    for s in M.STUFEN_REIHE:
        assert abs(a[s]["nu"] - b[s]["nu"]) <= 0.006                                 # README: „weicht um höchstens 0,006 ab“
    for strom in (a, b):
        werte = [strom[s]["nu"] for s in M.STUFEN_REIHE]
        assert werte == sorted(werte, reverse=True) and strom[M.FEIN]["nu"] == 0.0
    ga, gb = ev.grobe_zellen("A"), ev.grobe_zellen("B")
    for key, zb in gb.items():
        za = ga[key]
        assert abs(za["nu"] - zb["nu"]) <= 0.005
        assert abs(zb["d_R1_mittel"]) <= 0.01 and zb["d_R2_mittel"] > 0 and zb["r2_unter_r1"] == 0
        assert zb["treffer_R0"] > 2 * zb["treffer_R2"] and zb["kostenfaktor_R2"] > 3
        assert zb["faktor"] > 1.8
    for za in ga.values():
        assert abs(za["d_R1_mittel"]) <= 0.01 and za["d_R2_mittel"] > 0 and za["r2_unter_r1"] == 0 and za["treffer_R0"] > 2 * za["treffer_R2"]
    for strom in ("A", "B"):
        for key, z in ev.nk_zellen(strom).items():
            if key[1] == M.FEIN:
                assert z["d_R1_mittel"] == 0.0 and z["d_R2_mittel"] == 0.0 and z["schwach_ungleich_streng"] == 0 and z["nu_max"] < 1e-5
        for z in ev.zufall_zellen(strom).values():
            assert z["schwach_ungleich_streng"] == 0 and z["nu_max"] == 0.0 and z["mehrere_globale_optima"] == 0
        for (n, v), z in ev.gitter_zellen(strom).items():
            if v == "manhattan":
                assert 0.33 <= z["nu"] <= 0.36 and z["d_R2_mittel"] > 0.2 and min(z["erfolg_je_instanz"]["R2"]) > 0.9999
            elif v == "euklid_toleranz":
                assert 0.03 <= z["nu"] <= 0.04 and z["nu"] > ev.gitter_zellen(strom)[(n, "euklid_streng")]["nu"]
        bil = ev.budget_bilanz(ev.budget_nk(strom))
        assert bil == {"zellen": 12, "besser": 0, "schlechter": 11, "gleich": 1, "gesichert_schlechter": 10, "gesichert_besser": 0}
        for k, zeilen in ev.budget_nk(strom).items():
            assert all(z["d_unten"] > 0 for z in zeilen[:3])                          # 280, 1 680, 8 400: in allen 9 Zellen gesichert schlechter
            assert zeilen[3]["d_unten"] > 0 if k == 8 else zeilen[3]["d_unten"] <= 1e-12   # 42 000: nur K = 8
        for zeilen in ev.budget_gitter(strom).values():                              # 120 M: alle Regeln in allen Läufen am Optimum
            assert all(zeilen[1][f"am_optimum_{r}"] == 1.0 and zeilen[1][f"luecke_{r}"] == 0.0 for r in R.REGELN)
        z9 = ev.budget_gitter(strom)[9]
        assert z9[0]["d_oben"] < 0 and abs(z9[1]["d_R2_R0"]) <= 1e-12 and z9[1]["am_optimum_R0"] == 1.0   # R2 besser bei 20 M, Decke bei 120 M
    sa, sb = ev.stetig_zellen("A"), ev.stetig_zellen("B")
    for s in (sa, sb):
        assert s[(4, "lm")]["sattelanteil"] > s[(2, "lm")]["sattelanteil"] and s[(4, "newton")]["sattelanteil"] > s[(2, "newton")]["sattelanteil"]
        assert s[(8, "newton")]["konvergenz"] < s[(4, "newton")]["konvergenz"] < s[(2, "newton")]["konvergenz"]
        assert abs(s[(4, "lm")]["sattelanteil"] - s[(4, "newton")]["sattelanteil"]) <= 0.05 and abs(s[(2, "lm")]["sattelanteil"] - s[(2, "newton")]["sattelanteil"]) <= 0.05
    for strom, s in (("A", sa), ("B", sb)):
        mehr = ev.stetig_mehr_starts(strom)
        assert mehr["starts"] == 3000 and mehr["punkte_je_instanz"] > 2 * s[(4, "newton")]["punkte_je_instanz"]
        assert mehr["sattelanteil"] < s[(4, "newton")]["sattelanteil"] - 0.05          # mehr Starts: kleinerer Sattelanteil unter den gefundenen


if __name__ == "__main__":
    for name, text in bausteine().items():
        print(f"{name}: {text}")
