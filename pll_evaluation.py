"""Einstellungen, Analyse der gewählten Landschaft, eingefrorene Messreihen und alle Verdikte (reine Funktionen: (Art, Text))."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

import pll_constants as C
import pll_landscape as L
import pll_messung as M
import pll_rules as R
import pll_scenario as S

DATA = Path(__file__).resolve().parent / "data"
EPS = 1e-12


@dataclass(frozen=True, kw_only=True)
class Settings:
    fahrzeug: str = "wuerfel"
    wuerfel: str = C.WUERFEL_STANDARD
    n: int = C.DEFAULT_N
    k: int = C.DEFAULT_K
    stufen: int = C.DEFAULT_STUFEN
    staedte: int = C.DEFAULT_STAEDTE
    metrik: str = "manhattan"
    gleichheit: str = "toleranz"
    familie: str = "gleich"
    seed: int = C.DEFAULT_SEED
    seit: int = C.DEFAULT_SEIT


@dataclass(frozen=True, eq=False)
class Analysis:
    land: S.Landschaft
    kenn: L.Kennzahlen
    regeln: dict
    plateaus: np.ndarray     # Größen der Plateaus, absteigend
    seit: int


def de(x: float, stellen: int = 2) -> str:
    """Zahl mit Dezimalkomma und festen Nachkommastellen; Tausender mit schmalem Abstand ab 10 000."""
    text = f"{x:,.{stellen}f}".replace(",", "\u202f").replace(".", ",")
    return text if abs(x) >= 10000 else text.replace("\u202f", "")


def ganz(x: int) -> str:
    """Ganze Zahl mit schmalem Abstand als Tausendertrenner ab 1 000 (nur die Zahl, nie ein ganzer Satz)."""
    return f"{int(x):,}".replace(",", "\u202f") if abs(x) >= 1000 else str(int(x))


def vz(x: float, stellen: int = 2) -> str:
    """Wie de(), aber mit Vorzeichen (+ bei positiven Werten)."""
    return ("+" if x > 0 else "") + de(x, stellen)


def wuerfel_werte(text: str) -> tuple:
    """Acht ganze Zahlen aus dem Textfeld (Komma, Semikolon oder Leerzeichen); bei ungültiger Eingabe das Handbeispiel.
    Rückgabe: (Werte, gültig)."""
    try:
        teile = [int(t) for t in text.replace(";", ",").replace(" ", ",").split(",") if t.strip()]
    except ValueError:
        return S.WUERFEL_H1, False
    if len(teile) != 8:
        return S.WUERFEL_H1, False
    return tuple(max(C.WUERFEL_WERT_MIN, min(C.WUERFEL_WERT_MAX, t)) for t in teile), True


def landschaft(s: Settings) -> S.Landschaft:
    if s.fahrzeug == "wuerfel":
        return S.wuerfel(wuerfel_werte(s.wuerfel)[0])
    if s.fahrzeug == "tour7":
        return S.tour_landschaft(S.TOUR_H2, "manhattan", beschreibung="Rundtour mit 7 Städten (Handbeispiel), Manhattan, 2-opt")
    if s.fahrzeug == "nk":
        return S.nk_landschaft(s.n, min(s.k, s.n - 1), s.stufen, s.seed)
    if s.fahrzeug == "gitter":
        return S.gitter_landschaft(s.staedte, s.seed, s.metrik, s.gleichheit)
    if s.fahrzeug == "zufall":
        return S.zufall_landschaft(s.familie, s.staedte, s.seed, s.gleichheit)
    raise ValueError(f"unbekanntes Fahrzeug: {s.fahrzeug}")


def analyse_land(land: S.Landschaft, seit: int) -> Analysis:
    return Analysis(land, L.kennzahlen(land.V, land.nbi), R.alle_regeln(land.V, land.nbi, seit), L.plateaugroessen(land.V, land.nbi), seit)


def analyse(s: Settings) -> Analysis:
    return analyse_land(landschaft(s), s.seit)


def budget_live(land: S.Landschaft, kennung: int = 0, laeufe: int = C.BUDGET_LAEUFE_LIVE) -> list:
    """Stichprobe bei festem Budget für EINE Landschaft: je Budget c * M die mittlere Lücke und der Anteil der Läufe am Optimum."""
    budgets = [c * land.zuege for c in C.BUDGET_C]
    inst = M.budget_instanz(land, budgets, 900_000 + kennung, "A", laeufe)
    return [{"c": c, "budget": b, **{f"luecke_{r}": inst[r]["luecke"][i] for r in R.REGELN}, **{f"am_optimum_{r}": inst[r]["am_optimum"][i] for r in R.REGELN}}
            for i, (c, b) in enumerate(zip(C.BUDGET_C, budgets))]


# ---------------------------------------------------------------------------------------------------------------- eingefrorene Messreihen

@lru_cache(maxsize=None)
def lade(teil: str) -> dict:
    return json.loads((DATA / f"pll_{teil}.json").read_text(encoding="utf-8"))


def stufen_zeilen(strom: str = "A") -> dict:
    return {int(k): v for k, v in lade("stufen")["zeilen"][strom].items()}


def nk_zellen(strom: str = "A") -> dict:
    """{(N, Stufen, K): Zelle}; Strom B gibt es nur für N = 14."""
    out = {}
    for teil in ("zellen14", "zellen16k2", "zellen16k4", "zellen16k8"):
        for key, z in lade(teil)["zellen"].get(strom, {}).items():
            n, st, k = (int(x) for x in key.split("|"))
            out[(n, st, k)] = z
    return out


def grobe_zellen(strom: str = "A") -> dict:
    return {key: z for key, z in nk_zellen(strom).items() if key[1] != M.FEIN}


def gitter_zellen(strom: str = "A") -> dict:
    out = {}
    for teil in ("gitter8", "gitter9", "gitter10"):
        for key, z in lade(teil)["zellen"].get(strom, {}).items():
            n, variante = key.split("|")
            out[(int(n), variante)] = z
    return out


def zufall_zellen(strom: str = "A") -> dict:
    out = {}
    for teil in ("zufall89", "zufall10"):
        for key, z in lade(teil)["zellen"].get(strom, {}).items():
            fam, n = key.split("|")
            out[(fam, int(n))] = z
    return out


def budget_nk(strom: str = "A") -> dict:
    return {int(k): z for k, z in lade("budget_nk")["zellen"][strom].items()}


def budget_gitter(strom: str = "A") -> dict:
    return {int(n): z for n, z in lade("budget_gitter")["zellen"][strom].items()}


def stetig_zellen(strom: str = "A") -> dict:
    out = {}
    for key, z in lade("stetig")["zellen"][strom].items():
        d, verfahren = key.split("|")
        out[(int(d), verfahren)] = z
    return out


def stetig_mehr_starts(strom: str = "A") -> dict:
    """Dieselben Instanzen bei d = 4 mit dem Newton-Verfahren und 3 000 statt 300 Starts."""
    return lade("stetig")["mehr_starts"][strom]["4|newton"]


def sattel_summe_kosinus(d: int) -> tuple:
    """f(x) = Summe cos(x_i) auf [0, 2π)^d: (stationäre Punkte, Sattelpunkte, Sattelanteil) = (2^d, 2^d - 2, 1 - 2^(1-d))."""
    return 2 ** d, 2 ** d - 2, 1.0 - 2.0 ** (1 - d)


def budget_bilanz(zellen: dict) -> dict:
    """Zählung über alle (K, Budget)-Zellen: R2 im Mittel besser / schlechter / gleich als R0, Intervall ganz über 0."""
    zeilen = [z for k in sorted(zellen) for z in zellen[k]]
    return {
        "zellen": len(zeilen),
        "besser": sum(1 for z in zeilen if z["d_R2_R0"] < -EPS),
        "schlechter": sum(1 for z in zeilen if z["d_R2_R0"] > EPS),
        "gleich": sum(1 for z in zeilen if abs(z["d_R2_R0"]) <= EPS),
        "gesichert_schlechter": sum(1 for z in zeilen if z["d_unten"] > EPS),
        "gesichert_besser": sum(1 for z in zeilen if z["d_oben"] < -EPS),
    }


# ---------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_optimum(k: L.Kennzahlen) -> tuple:
    """Kernfrage 1: Was ist ein Optimum, wenn Nachbarn gleich gut sind?"""
    if k.gleiche_paare == 0:
        return "info", (f"In dieser Landschaft gibt es **keinen Gleichstand zwischen Nachbarn**: Die drei Zählweisen stimmen überein "
                        f"({k.schwach} schwache = {k.streng} strenge Optima = {k.geschlossen} geschlossene Plateaus), es gibt kein Plateau und kein Scheinoptimum.")
    if k.schwach == k.streng:
        return "info", (f"Es gibt Gleichstände (ν = {de(k.nu, 4)}), aber keiner liegt an einem Optimum: {k.schwach} schwache = {k.streng} strenge Optima "
                        f"= {k.geschlossen} geschlossene Plateaus.")
    return "warning", (f"Die Antwort hängt an der Zählweise: **{k.schwach} schwache**, **{k.streng} strenge** Optima, aber **{k.geschlossen} geschlossene Plateaus**. "
                       f"{k.scheinoptima} der {k.schwach} schwachen Optima sind Scheinoptima: Ihr Plateau hat einen Ausgang, der Abstieg bleibt dort nur stehen, "
                       f"weil kein Nachbar strikt besser ist.")


def verdict_neutral(k: L.Kennzahlen) -> tuple:
    """Kernfrage 2: Wie viel Neutralität hat diese Landschaft?"""
    if k.gleiche_paare == 0:
        return "info", f"Keine Neutralität: Unter den {k.paare} geordneten Nachbarpaaren ist kein einziges gleich gut (ν = 0), es gibt kein Plateau."
    return "success", (f"Neutralitätsgrad **ν = {de(k.nu, 4)}** ({k.gleiche_paare} von {k.paare} geordneten Nachbarpaaren sind gleich gut); "
                       f"{de(100 * k.anteil_mit_gleichem, 1)} % der {k.zustaende} Zustände haben mindestens einen gleich guten Nachbarn; {k.plateaus} Plateaus, "
                       f"das größte umfasst {k.groesstes_plateau} Zustände ({de(100 * k.anteil_groesstes, 1)} % des Raums).")


def verdict_regeln(regeln: dict, seit: int) -> tuple:
    """Kernfrage 3: Hilft zufälliger Gleichstand oder Seitwärtsgehen, und was kostet es? (diese eine Landschaft, exakt)"""
    r0, r1, r2 = regeln["R0"], regeln["R1"], regeln["R2"]
    kopf = (f"Erfolg eines Abstiegs (exakt, Start gleichverteilt): **{de(r0['erfolg'], 4)}** (R0), **{de(r1['erfolg'], 4)}** (R1), **{de(r2['erfolg'], 4)}** (R2, S = {seit}); "
            f"Auswertungen je Abstieg {de(r0['auswertungen'], 1)} / {de(r1['auswertungen'], 1)} / {de(r2['auswertungen'], 1)}; "
            f"Treffer je 1 000 Auswertungen {de(r0['treffer_je_1000'], 2)} / {de(r1['treffer_je_1000'], 2)} / {de(r2['treffer_je_1000'], 2)}.")
    if abs(r2["erfolg"] - r0["erfolg"]) <= EPS and abs(r1["erfolg"] - r0["erfolg"]) <= EPS and abs(r2["auswertungen"] - r0["auswertungen"]) <= 1e-9:
        return "info", kopf + " Alle drei Regeln sind hier gleich: Kein Abstieg trifft auf einen Gleichstand, der etwas entscheidet."
    if r2["erfolg"] < r0["erfolg"] - EPS:
        return "warning", kopf + " In dieser Landschaft trifft R2 **seltener** als R0: Der zufällige beste Nachbar ist hier schlechter als der erste in der festen Zugreihenfolge."
    if r2["treffer_je_1000"] < r0["treffer_je_1000"] - EPS:
        return "warning", kopf + " Seitwärtsschritte erhöhen hier den Erfolg je Abstieg, aber **je Auswertung** trifft R0 häufiger."
    return "success", kopf + " Seitwärtsschritte lohnen hier auch je Auswertung."


def verdict_wuerfel(k: L.Kennzahlen, regeln: dict, seit: int) -> tuple:
    """Experiment 1, Würfel: Zählweisen und Erfolg der drei Regeln."""
    text = (f"Würfel: {k.schwach} schwache, {k.streng} strenge Optima, {k.geschlossen} geschlossene Plateaus, {k.scheinoptima} Scheinoptima; "
            f"ν = {k.gleiche_paare}/{k.paare} = {de(k.nu, 4)}. Erfolg R0 / R1 / R2 (S = {seit}): {de(regeln['R0']['erfolg'], 4)} / {de(regeln['R1']['erfolg'], 4)} / "
            f"{de(regeln['R2']['erfolg'], 4)}; Auswertungen je Abstieg {de(regeln['R0']['auswertungen'], 2)} / {de(regeln['R1']['auswertungen'], 2)} / {de(regeln['R2']['auswertungen'], 2)}.")
    if k.scheinoptima:
        return "warning", text + " Wer Optima als Zustände zählt, zählt hier mehr Fallen, als es geschlossene Plateaus gibt."
    return "info", text + " Hier gibt es kein Scheinoptimum."


def verdict_tour7(k: L.Kennzahlen) -> tuple:
    """Experiment 1, Tour mit 7 Städten (Handbeispiel, Manhattan, 2-opt)."""
    return "info", (f"Tour mit 7 Städten (Manhattan, 2-opt, {k.zustaende} Touren, {k.zuege} Nachbarn je Tour): {k.schwach} schwache Optima, {k.streng} strenges, "
                    f"{k.geschlossen} geschlossenes Plateau, {k.plateaus} Plateaus (das größte mit {k.groesstes_plateau} Touren), ν = {de(k.nu, 4)}.")


def verdict_stufen(zeilen: dict) -> tuple:
    """Experiment 2: ν gegen die Zahl der Stufen (NK, N = 14, K = 4, Mittel über die Instanzen je Zeile)."""
    stufen = sorted(zeilen)
    teile = ", ".join(f"{de(zeilen[st]['nu'], 4)} bei {ganz(st)}" for st in stufen)
    fallend = all(zeilen[a]["nu"] >= zeilen[b]["nu"] for a, b in zip(stufen, stufen[1:]))
    n = zeilen[stufen[0]]["instanzen"]
    art = "success" if fallend else "warning"
    schluss = "Der Mittelwert fällt von Zeile zu Zeile: Neutralität ist ein Regler, kein Schalter." if fallend else "Der Mittelwert fällt nicht in jeder Zeile."
    return art, f"NK-Modell, N = 14, K = 4, Mittel über {n} Instanzen je Zeile: ν = {teile} Stufen je Beitrag. {schluss}"


def verdict_zufall(zellen: dict) -> tuple:
    """Experiment 2: Zufallskoordinaten als Kontrolle (Zählung über alle Zellen)."""
    gesamt = sum(z["instanzen"] for z in zellen.values())
    verschieden = sum(z["schwach_ungleich_streng"] for z in zellen.values())
    mehrfach = sum(z["mehrere_globale_optima"] for z in zellen.values())
    nu_max = max(z["nu_max"] for z in zellen.values())
    text = (f"Zufallskoordinaten (vier Familien, n = 8 bis 10, 2-opt, Längen auf 1e-9 gerundet): in {verschieden} von {gesamt} aufgezählten Instanzen weicht die Zahl der "
            f"schwachen von der der strengen Optima ab, in {mehrfach} gibt es mehr als eine kürzeste Tour; größter Neutralitätsgrad einer Instanz: {de(nu_max, 6)}.")
    if verschieden == 0 and nu_max == 0:
        return "info", text + " Mit diesen Punkten gibt es keinen einzigen Gleichstand zwischen Nachbarn: Plateaus brauchen hier eigene Fahrzeuge."
    return "warning", text


def verdict_toleranz(tol: dict, streng: dict, n: int) -> tuple:
    """Experiment 2: dieselben euklidischen Gitter-Touren, einmal bitgenau, einmal auf 1e-9 gerundet verglichen."""
    if tol["nu"] <= EPS:
        return "info", f"Gitter euklidisch, n = {n}: kein Gleichstand, die Gleichheitsregel spielt keine Rolle."
    fehlt = 100.0 * (tol["nu"] - streng["nu"]) / tol["nu"]
    return "warning", (f"Gitter euklidisch, n = {n}, Mittel über {tol['instanzen']} Instanzen: ν = {de(streng['nu'], 4)} bei bitgenauem Vergleich der Gleitkommazahlen, "
                       f"{de(tol['nu'], 4)} mit Toleranz; der bitgenaue Vergleich übersieht {de(fehlt, 0)} % der Gleichstände. Schwache Optima: {de(streng['schwach'], 2)} gegen {de(tol['schwach'], 2)}.")


def verdict_zaehlweise(nk: dict, gitter: dict) -> tuple:
    """Experiment 3: Faktor schwache Optima je geschlossenem Plateau (Quotient der Zellenmittel) über die groben NK-Zellen und das Gitter."""
    f_nk = [z["faktor"] for z in nk.values()]
    f_gi = [z["faktor"] for (n, v), z in gitter.items() if v != "euklid_streng"]
    s_nk = [100 * z["anteil_schein"] for z in nk.values()]
    return "warning", (f"Schwache Optima je geschlossenem Plateau (Quotient der Zellenmittel): **{de(min(f_nk), 1)} bis {de(max(f_nk), 1)}** in den {len(f_nk)} groben NK-Zellen, "
                       f"**{de(min(f_gi), 1)} bis {de(max(f_gi), 1)}** in den {len(f_gi)} Gitter-Zellen. Scheinoptima unter den schwachen Optima bei NK: {de(min(s_nk), 0)} bis {de(max(s_nk), 0)} % "
                       f"(Mittel je Zelle). Wer Optima als Zustände zählt, überschätzt in diesen Zellen die Zahl der Fallen.")


def verdict_gleichstand(zellen: dict) -> tuple:
    """Experiment 4: Zählung über die groben NK-Zellen (exakte Regeln, je Zelle 30 Instanzen)."""
    m = len(zellen)
    inst = sum(z["instanzen"] for z in zellen.values())

    def liste(stelle):
        return ", ".join(str(x) for x in sorted({key[stelle] for key in zellen}))

    d1 = [z["d_R1_mittel"] for z in zellen.values()]
    d2 = [z["d_R2_mittel"] for z in zellen.values()]
    unter = sum(1 for z in zellen.values() if z["r2_unter_r0"] > 0)
    unter_inst = sum(z["r2_unter_r0"] for z in zellen.values())
    unter_r1 = sum(z["r2_unter_r1"] for z in zellen.values())
    kosten = [z["kostenfaktor_R2"] for z in zellen.values()]
    treffer = [z["treffer_R0"] / z["treffer_R2"] for z in zellen.values()]
    return "warning", (
        f"{m} grobe NK-Zellen (N = {liste(0)}; Stufen {liste(1)}; K = {liste(2)}; {inst} Instanzen, exakt): **zufälliger Gleichstand (R1)** ändert den Erfolg im Zellenmittel um "
        f"{vz(min(d1), 4)} bis {vz(max(d1), 4)}, je Instanz um {vz(min(z['d_R1_min'] for z in zellen.values()), 3)} bis {vz(max(z['d_R1_max'] for z in zellen.values()), 3)} "
        f"(beobachtete Spanne, keine Grenze). **Seitwärtsschritte (R2, S = 50)** erhöhen ihn im Zellenmittel um {vz(min(d2), 4)} bis {vz(max(d2), 4)}, "
        f"je Instanz {vz(min(z['d_R2_min'] for z in zellen.values()), 4)} bis {vz(max(z['d_R2_max'] for z in zellen.values()), 3)}; in {unter} der {m} Zellen liegt R2 in mindestens "
        f"einer Instanz unter R0 ({unter_inst} Instanzen), unter R1 in {unter_r1}. Ein R2-Abstieg kostet das {de(min(kosten), 1)}- bis {de(max(kosten), 1)}-Fache an Auswertungen; "
        f"**je 1 000 Auswertungen trifft R0 {de(min(treffer), 1)}- bis {de(max(treffer), 1)}-mal so oft** wie R2.")


def verdict_budget_nk(zellen: dict) -> tuple:
    """Experiment 5, NK: Bilanz R2 gegen R0 über alle (K, Budget)-Zellen."""
    b = budget_bilanz(zellen)
    budgets = sorted({z["budget"] for zs in zellen.values() for z in zs})
    text = (f"NK-Modell (N = 14, 3 Stufen, K = {', '.join(str(k) for k in sorted(zellen))}; Budgets {', '.join(ganz(x) for x in budgets)} Auswertungen; "
            f"30 Instanzen, 100 Läufe je Instanz und Regel): R2 hat im Mittel in **{b['besser']} von {b['zellen']} Zellen** die kleinere Lücke als R0, in {b['schlechter']} die größere, "
            f"in {b['gleich']} dieselbe; das 95-%-Intervall der Differenz liegt in {b['gesichert_schlechter']} Zellen ganz über 0 und in {b['gesichert_besser']} ganz darunter.")
    if b["besser"] == 0:
        return "warning", text + " Bei festem Budget sind Seitwärtsschritte auf diesen Landschaften in keiner gemessenen Zelle besser."
    return "info", text


def verdict_budget_gitter(zellen: dict) -> tuple:
    """Experiment 5, Gitter Manhattan: Lücke R0 gegen R2 je n und Budget."""
    teile = []
    besser = 0
    gesamt = 0
    for n in sorted(zellen):
        for z in zellen[n]:
            gesamt += 1
            besser += z["d_oben"] < -EPS
            teile.append(f"n = {n}, {ganz(z['budget'])} Auswertungen: {de(z['luecke_R0'], 2)} % (R0) gegen {de(z['luecke_R2'], 2)} % (R2)")
    art = "success" if besser else "info"
    return art, ("Gitter ohne Rauschen, Manhattan (30 Instanzen, 100 Läufe je Instanz und Regel), mittlere Lücke zur kürzesten Tour: " + "; ".join(teile)
                 + f". In {besser} von {gesamt} Zellen ist R2 gesichert besser (95-%-Intervall der Differenz ganz unter 0). Die Richtung hängt an Landschaft und Budget.")


def verdict_budget_live(zeilen: list, laeufe: int) -> tuple:
    """Experiment 5, eine Landschaft live: je Budget, welche Regel die kleinere mittlere Lücke hat (eine Stichprobe, kein Intervall)."""
    teile = []
    for z in zeilen:
        d = z["luecke_R2"] - z["luecke_R0"]
        urteil = "gleich" if abs(d) <= EPS else ("R2 kleiner" if d < 0 else "R0 kleiner")
        teile.append(f"{ganz(z['budget'])} Auswertungen: {de(z['luecke_R0'], 2)} % (R0) gegen {de(z['luecke_R2'], 2)} % (R2), {urteil}")
    return "info", f"Diese eine Landschaft, {laeufe} Läufe je Regel (Stichprobe ohne Intervall), mittlere Lücke: " + "; ".join(teile) + "."
