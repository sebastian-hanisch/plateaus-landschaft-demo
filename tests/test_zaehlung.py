"""Zähltest: Die gezählten Auswertungen stimmen an Mini-Instanzen mit der Handzählung überein, und die Stichprobe bei festem
Budget (viele Läufe zugleich mit numpy) stimmt Lauf für Lauf mit einer Python-Schleife überein, die jede Auswertung einzeln zählt."""

import numpy as np
import pytest

import pll_basis as B
import pll_rules as R
import pll_scenario as S
from pll_rng import SplitMix64

GROSS = np.iinfo(np.int64).max


def test_auswertungen_je_abstieg_am_wuerfel_von_hand():
    """Würfel H1, R0: Durchsuchungen je Start 000:1, 001:2, 010:2, 011:1, 100:2, 101:3, 110:1, 111:2.
    Jede Durchsuchung bewertet alle M = 3 Nachbarn, der Start kostet 1: Auswertungen 4, 7, 7, 4, 7, 10, 4, 7, Mittel 50/8."""
    w = S.wuerfel(S.WUERFEL_H1)
    hand = [1 + 3 * s for s in (1, 2, 2, 1, 2, 3, 1, 2)]
    assert hand == [4, 7, 7, 4, 7, 10, 4, 7]
    assert R.alle_regeln(w.V, w.nbi, 50)["R0"]["auswertungen"] == pytest.approx(sum(hand) / 8)


def test_vektor_zufall_ist_dieselbe_folge_wie_splitmix64():
    seeds = [0, 1, 12345, 2**63 + 5]
    zustand = np.array(seeds, dtype=np.uint64)
    einzeln = [SplitMix64(s) for s in seeds]
    for _ in range(5):
        u = R._naechste_u64(zustand)
        assert [int(x) for x in u] == [r.next_u64() for r in einzeln]


def lauf_schleife(V, nbi, regel, budgets, seed, seit):
    """Ein Lauf als Python-Schleife mit einem Zähler, der jede Auswertung einzeln zählt. Rückgabe: bester Wert je Budget."""
    S_, M = nbi.shape
    rng = SplitMix64(seed)
    grenze = max(budgets)
    bester = [GROSS] * len(budgets)
    zaehler_ausw = 0
    x, neustart, k = None, True, 0

    def merke(zustand):
        for i, b in enumerate(budgets):
            if zaehler_ausw <= b:
                bester[i] = min(bester[i], int(V[zustand]))

    while True:
        kosten = 1 if neustart else M
        if zaehler_ausw + kosten > grenze:
            return bester
        u = rng.next_u64()
        if neustart:
            x = u % S_
            zaehler_ausw += 1                      # Bewertung des Startzustands
            k, neustart = 0, False
            merke(x)
            continue
        werte = []
        for y in nbi[x]:
            werte.append(int(V[y]))
            zaehler_ausw += 1                      # jede Bewertung eines Nachbarn zählt 1
        m = min(werte)
        if m < V[x]:
            beste = [int(y) for y, wert in zip(nbi[x], werte) if wert == m]
            x = beste[0] if regel == "R0" else beste[u % len(beste)]
            k = 0
            merke(x)
            continue
        gleich = [int(y) for y, wert in zip(nbi[x], werte) if wert == V[x]]
        if regel == "R2" and gleich and k < seit:
            x = gleich[u % len(gleich)]
            k += 1
            merke(x)
            continue
        neustart = True


@pytest.mark.parametrize("regel", ["R0", "R1", "R2"])
def test_budget_laeufe_stimmen_lauf_fuer_lauf_mit_der_schleife(regel):
    for land, budgets, seit in ((S.wuerfel(S.WUERFEL_H1), [1, 3, 4, 7, 40], 50), (S.nk_landschaft(6, 2, 3, 3), [20, 60, 300], 5),
                                (S.gitter_landschaft(6, 1, "manhattan"), [15, 100, 500], 50)):
        seeds = [B.lauf_seed(3, R.REGELN.index(regel), lauf) for lauf in range(12)]
        vektor = R.budget_laeufe(land.V, land.nbi, regel, budgets, seeds, seit)
        for spalte, seed in enumerate(seeds):
            assert vektor[:, spalte].tolist() == lauf_schleife(land.V, land.nbi, regel, budgets, seed, seit)


def test_budget_von_hand_am_wuerfel():
    """Budget 1 bis 3: nur der Startzustand ist bewertet (eine Durchsuchung kostet 3 und passt nicht mehr).
    Budget 4: genau eine Durchsuchung, R0 steht danach auf dem ersten besten Nachbarn."""
    w = S.wuerfel(S.WUERFEL_H1)
    seeds = list(range(40))
    starts = [SplitMix64(s).next_u64() % 8 for s in seeds]
    b = R.budget_laeufe(w.V, w.nbi, "R0", [1, 3, 4], seeds)
    assert b[0].tolist() == [int(w.V[s]) for s in starts]
    assert b[1].tolist() == b[0].tolist()
    nach_einem_schritt = {0: 0, 1: 3, 2: 3, 3: 3, 4: 6, 5: 4, 6: 6, 7: 3}          # Handtabelle: Zustand nach einer Durchsuchung (R0)
    assert b[2].tolist() == [min(int(w.V[s]), int(w.V[nach_einem_schritt[s]])) for s in starts]


def test_kleineres_budget_ist_der_anfang_desselben_laufs():
    land = S.nk_landschaft(8, 2, 3, 9)
    seeds = [B.lauf_seed(1, 2, lauf) for lauf in range(20)]
    gemeinsam = R.budget_laeufe(land.V, land.nbi, "R2", [50, 400], seeds)
    einzeln = R.budget_laeufe(land.V, land.nbi, "R2", [50], seeds)
    assert gemeinsam[0].tolist() == einzeln[0].tolist()
    assert (gemeinsam[1] <= gemeinsam[0]).all()                                    # mehr Budget ist nie schlechter


def test_luecke_in_prozent_des_optimums():
    land = S.nk_landschaft(6, 2, 3, 3)
    opt = int(land.V.min())
    assert S.luecke_prozent(land, np.array([opt]))[0] == 0.0
    zweit = int(np.unique(land.V)[1])
    assert S.luecke_prozent(land, np.array([zweit]))[0] == pytest.approx(100.0 * (zweit - opt) / abs(opt))
    tour = S.gitter_landschaft(6, 1, "euklid", "streng")                            # Rangwerte: die Lücke rechnet trotzdem in echten Längen
    v2 = int(np.unique(tour.V)[1])
    laengen = np.unique(tour.werte)
    assert S.luecke_prozent(tour, np.array([v2]))[0] == pytest.approx(100.0 * (laengen[1] - laengen[0]) / laengen[0])
