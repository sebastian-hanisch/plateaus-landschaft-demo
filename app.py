"""Plateaus: wenn gleich gut nicht fertig heißt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Landschaften mit Gleichständen: Neutralitätsgrad, Plateaus mit und ohne Ausgang, drei Zählweisen des Optimums und die
Gleichstandsregeln R0, R1, R2 des steilsten Abstiegs (exakt gerechnet). Aufbau nach DEMO-PLAYBOOK.md §2.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import pll_constants as C
import pll_evaluation as ev
import pll_landscape as L
import pll_layout as LY
import pll_messung as M
import pll_presets as P
import pll_scenario as S
import pll_visualization as viz
import modul_frisch

modul_frisch.aktualisieren(__file__)      # geänderte Hilfsmodule nach einem Update neu laden (die Cloud behält sie sonst bis zum Neustart)

st.set_page_config(page_title="Plateaus – Sebastian Hanisch", layout="wide")
de = ev.de


@st.cache_data(show_spinner=False, max_entries=12)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False, max_entries=8)
def _wuerfel(werte, seit):
    land = S.wuerfel(werte)
    return ev.analyse_land(land, seit), L.einteilung(land.V, land.nbi)


@st.cache_data(show_spinner=False)
def _tour7():
    return ev.analyse_land(S.tour_landschaft(S.TOUR_H2, "manhattan"), 50)


def _zeige(verdikt):
    art, text = verdikt
    getattr(st, art)(text)


def _zellen_tabelle(zellen, spalten):
    """Markdown-Tabelle aus eingefrorenen Zellen: spalten = [(Titel, Funktion der Zelle)]."""
    kopf = "| Zelle | " + " | ".join(t for t, _ in spalten) + " |\n|---|" + "---|" * len(spalten)
    zeilen = [f"| {name} | " + " | ".join(f(z) for _, f in spalten) + " |" for name, z in zellen]
    return kopf + "\n" + "\n".join(zeilen)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in pll_layout.py).
st.html(LY.kopf_css(LY.dunkles_design()))
with st.container(key="kopf"):
    st.title("🏔️ Plateaus: wenn gleich gut nicht fertig heißt")
st.markdown(
    """
Stück der Reihe **Landschaften, Einstellung und Vergleich**. Die beiden Stücke davor nehmen an, dass jeder Zustand seinen eigenen Wert hat und ein lokales Optimum ein einzelner
Zustand ist. Sind die Werte **grob oder ganzzahlig**, stimmt das nicht mehr: Viele Nachbarn sind **gleich gut**, aus Optima werden **Plateaus mit oder ohne Ausgang**, und der
steilste Abstieg braucht eine **Gleichstandsregel**. Diese Demo zählt beides vollständig aus, an einem **NK-Modell mit wenigen Stufen je Beitrag** und an **Rundtouren auf einem
ganzzahligen Gitter**; Rundtouren mit Zufallskoordinaten dienen als Kontrolle ohne Plateaus.

Weiter unten: die Abschnitte **🔬 Experiment 1 bis 5**, der Expander **🔭 Ausblick: stetige Landschaften**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Zählung von Plateaus", expanded=True):
    st.markdown(
        """
1. **Alle Zustände aufzählen** (alle Bitfolgen oder alle Rundtouren) und jeden mit seinen Nachbarn vergleichen. Der **Neutralitätsgrad ν** ist der Anteil der geordneten Nachbarpaare mit gleichem Wert.
2. **Gleich gute Nachbarn zu Plateaus verbinden** und je Plateau fragen, ob es einen **Ausgang** hat: einen Zustand mit einem strikt besseren Nachbarn. Ein Plateau ohne Ausgang heißt **geschlossen**.
3. **Den Abstieg unter drei Gleichstandsregeln exakt rechnen** (R0, R1, R2): Erfolg = Anteil aller Starts, die im globalen Optimum enden; Kosten = Auswertungen (jede Bewertung eines Nachbarn zählt 1, alle Nachbarn werden bewertet).
        """
    )
    st.markdown(C.ZAEHLWEISEN_TABELLE)
    st.caption("„Abstieg“ und „Einzugsgebiet“ stammen aus dem Stück über Einzugsgebiete: Der steilste Abstieg geht immer zum besten Nachbarn, das Einzugsgebiet eines Optimums sind die Starts, die dort enden.")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

P.load_permalink_settings()
P.init_session_state_defaults()

with st.sidebar:
    P.sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Fahrzeug**")
    fahrzeug = st.selectbox("Landschaft", C.FAHRZEUGE, format_func=C.FAHRZEUG_TEXT.get, key="fahrzeug_select",
                            help="Welche Landschaft vollständig aufgezählt wird. Regler, die für das gewählte Fahrzeug keine Bedeutung haben, sind gesperrt.")
    wuerfel_text = st.text_input("Werte des Würfels (000 bis 111)", key="wuerfel_text", max_chars=80,
                                 help="Acht ganze Zahlen von -99 bis 99, durch Komma getrennt: die Werte der Zustände 000, 001, …, 111 (größer ist besser). Gilt für das Fahrzeug Würfel und für Experiment 1.")
    ist_nk = fahrzeug == "nk"
    st.markdown("**NK-Modell**")
    n = st.slider("Länge N", *P.bounds("n_slider"), key="n_slider", disabled=not ist_nk, help="Zahl der Bits; die Landschaft hat 2^N Zustände und N Nachbarn je Zustand.")
    k = st.slider("Kopplung K", *P.bounds("k_slider"), key="k_slider", disabled=not ist_nk, help="Jeder Beitrag hängt an seinem Locus und K weiteren (K zählt ohne den Locus selbst).")
    stufen = st.select_slider("Stufen je Beitrag", C.STUFEN, key="stufen_select", disabled=not ist_nk,
                              help="Jeder der N Beiträge ist eine ganze Zahl von 0 bis Stufen − 1. Wenige Stufen: viele Gleichstände. 1 000 000: feine Kontrolle.")
    ist_tour = fahrzeug in ("gitter", "zufall")
    st.markdown("**Rundtour**")
    staedte = st.slider("Städte n", *P.bounds("staedte_slider"), key="staedte_slider", disabled=not ist_tour, help="Alle (n − 1)!/2 Rundtouren werden aufgezählt; Nachbarschaft 2-opt mit n(n − 3)/2 Zügen.")
    metrik = st.radio("Längenmaß (Gitter)", C.METRIKEN, format_func=C.METRIK_TEXT.get, key="metrik_radio", disabled=fahrzeug != "gitter",
                      help="Manhattan: ganze Zahlen. Euklidisch: Wurzeln, Gleichstände nur bei gleich gebauten Touren.")
    euklid = fahrzeug == "zufall" or (fahrzeug == "gitter" and metrik == "euklid")
    gleichheit = st.radio("Wann sind zwei Längen gleich?", C.GLEICHHEIT, format_func=C.GLEICHHEIT_TEXT.get, key="gleichheit_radio", disabled=not euklid,
                          help="Nur bei euklidischen Längen von Bedeutung: Mathematisch gleiche Summen können sich als Gleitkommazahlen im letzten Bit unterscheiden.")
    familie = st.selectbox("Familie (Zufallskoordinaten)", C.FAMILIEN, format_func=C.FAMILIE_TEXT.get, key="familie_select", disabled=fahrzeug != "zufall",
                           help="Die vier Punktfamilien der Reihe mit ganzzahligen Koordinaten von 0 bis 9999.")
    st.markdown("**Zufall und Abstieg**")
    seed = st.number_input("Zufalls-Seed der Instanz", *P.bounds("seed_input"), key="seed_input", step=1, disabled=fahrzeug in ("wuerfel", "tour7"),
                           help="NK-Modell und Gitter: Zufalls-Seed der Instanz (die Messreihen nutzen 100000 bis 100029). Zufallskoordinaten: laufende Nummer der Instanz der Familie.")
    seit = st.slider("Seitwärtsgrenze S (Regel R2)", *P.bounds("seit_slider"), key="seit_slider",
                     help="Höchstzahl der Seitwärtsschritte hintereinander; S = 0 macht R2 zu R1. Die Messreihen nutzen S = 50.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=P.randomize_seed, disabled=fahrzeug in ("wuerfel", "tour7"))

P.sync_query_params({"fahrzeug_select": fahrzeug, "wuerfel_text": wuerfel_text, "n_slider": int(n), "k_slider": int(k), "stufen_select": int(stufen),
                   "staedte_slider": int(staedte), "metrik_radio": metrik, "gleichheit_radio": gleichheit, "familie_select": familie, "seed_input": int(seed),
                   "seit_slider": int(seit)})

settings = ev.Settings(fahrzeug=fahrzeug, wuerfel=wuerfel_text, n=int(n), k=int(k), stufen=int(stufen), staedte=int(staedte), metrik=metrik,
                       gleichheit=gleichheit, familie=familie, seed=int(seed), seit=int(seit))
wuerfel_werte, wuerfel_gueltig = ev.wuerfel_werte(wuerfel_text)
if not wuerfel_gueltig:
    st.warning("Die Werte des Würfels sind keine acht ganzen Zahlen; gerechnet wird mit dem Handbeispiel 2, 2, 1, 4, 2, 0, 3, 2.")
if settings.fahrzeug == "nk" and settings.n == C.N_MAX:
    with st.spinner("Zähle 65 536 Zustände aus (etwa 2 bis 5 Sekunden) …"):
        a = _analysis(settings)
else:
    a = _analysis(settings)
kenn, regeln = a.kenn, a.regeln

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Gewählte Landschaft: **{a.land.beschreibung}**; {kenn.zustaende} Zustände, {kenn.zuege} Nachbarn je Zustand, vollständig aufgezählt. "
           + ("Größer ist besser (Fitness)." if a.land.maximieren else "Kürzer ist besser (Tourlänge)."))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Neutralitätsgrad ν", de(kenn.nu, 4), help="Anteil der geordneten Nachbarpaare mit gleichem Wert.")
m2.metric("Schwache Optima", f"{kenn.schwach}", help="Zustände ohne strikt besseren Nachbarn.")
m3.metric("Strenge Optima", f"{kenn.streng}", help="Zustände, deren Nachbarn alle strikt schlechter sind.")
m4.metric("Geschlossene Plateaus", f"{kenn.geschlossen}", help="Plateaus ohne Ausgang, einzelne Zustände mitgezählt.")
m5.metric("Scheinoptima", f"{kenn.scheinoptima}", help="Schwache Optima auf einem Plateau mit Ausgang.")
c1, c2 = st.columns(2)
c1.plotly_chart(viz.build_zaehlweisen(kenn), width="stretch", key="main_chart")
if len(a.plateaus):
    c2.plotly_chart(viz.build_plateaus(a.plateaus), width="stretch", key="plateau_chart")
else:
    c2.info("Diese Landschaft hat kein Plateau: Kein Zustand hat einen gleich guten Nachbarn.")
st.caption("Links: dieselbe Landschaft, drei Zählweisen. Rechts: Wie groß die Plateaus sind (Zusammenhangskomponenten gleich guter Nachbarn mit mindestens zwei Zuständen).")

# --- Kernfragen ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage 1: Was ist ein Optimum, wenn Nachbarn gleich gut sind?")
_zeige(ev.verdict_optimum(kenn))
st.markdown("## ❓ Kernfrage 2: Wie viel Neutralität hat diese Landschaft?")
_zeige(ev.verdict_neutral(kenn))
st.markdown("## ❓ Kernfrage 3: Hilft es, bei Gleichstand zufällig zu wählen oder seitwärts zu gehen, und was kostet es?")
_zeige(ev.verdict_regeln(regeln, settings.seit))
st.caption("Gilt für die gewählte Landschaft, steilsten Abstieg, Zählweise „voll“ (alle Nachbarn werden bewertet, keine Nachbarlisten, keine Warteschlange; "
           "andere Zählweisen behandelt das Stück über Nachbarschaften). Zähleinheit: Zustand beziehungsweise Auswertung.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Von Hand: ein Würfel und eine Tour")
st.caption("Der Würfel nutzt die acht Werte aus der Seitenleiste (Zugreihenfolge: Bit 0, Bit 1, Bit 2) und die Seitwärtsgrenze S. Die Tour ist ein festes Handbeispiel mit sieben Gitterpunkten und Manhattan-Längen.")
wa, wein = _wuerfel(wuerfel_werte, settings.seit)
e1, e2 = st.columns([3, 2])
e1.plotly_chart(viz.build_wuerfel(wuerfel_werte, wein), width="stretch", key="wuerfel_chart")
zeilen = ["| Zustand | Wert | Werte der Nachbarn (Bit 0, 1, 2 umgedreht) | Rolle |", "|---|---|---|---|"]
for s in range(8):
    rolle = "strenges Optimum" if wein["streng"][s] else ("Scheinoptimum" if wein["schein"][s] else ("schwaches Optimum" if wein["schwach"][s] else ("Plateau" if wein["groesse"][s] >= 2 else "keine besondere")))
    zeilen.append(f"| {s:03b} | {wuerfel_werte[s]} | {', '.join(str(wuerfel_werte[s ^ (1 << b)]) for b in range(3))} | {rolle} |")
e2.markdown("\n".join(zeilen))
_zeige(ev.verdict_wuerfel(wa.kenn, wa.regeln, settings.seit))
_zeige(ev.verdict_tour7(_tour7().kenn))
st.caption("Im Tour-Beispiel hat die zweite Falle (Länge 16 statt 14) drei gleich lange Nachbarn und liegt auf einem Plateau mit vier Touren und Ausgang: ein Scheinoptimum.")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Wie viel Neutralität entsteht wo?")
st.caption("Eingefrorene Messreihen: je Zeile 30 Instanzen mit festen Zufalls-Seeds, jede vollständig aufgezählt. Die Tabellen der Beiträge sind je Stufenzahl andere (kein kontrollierter Einzelvergleich).")
stz = ev.stufen_zeilen("A")
st.plotly_chart(viz.build_stufen(stz), width="stretch", key="stufen_chart")
_zeige(ev.verdict_stufen(stz))
gz = ev.gitter_zellen("A")
st.markdown(_zellen_tabelle(
    [(f"Gitter n = {nn}, {'Manhattan' if v == 'manhattan' else ('euklidisch, mit Toleranz' if v == 'euklid_toleranz' else 'euklidisch, bitgenau')}", gz[(nn, v)])
     for nn in M.GITTER_N for v in M.GITTER_VARIANTEN],
    [("ν", lambda z: de(z["nu"], 4)), ("Zustände mit gleich gutem Nachbarn", lambda z: de(100 * z["anteil_mit_gleichem"], 1) + " %"),
     ("schwache Optima", lambda z: de(z["schwach"], 2)), ("strenge", lambda z: de(z["streng"], 2)), ("geschlossene Plateaus", lambda z: de(z["geschlossen"], 2))]))
st.caption("Mittel über 30 Instanzen je Zeile (Gitter ohne Rauschen, 2-opt).")
_zeige(ev.verdict_toleranz(gz[(9, "euklid_toleranz")], gz[(9, "euklid_streng")], 9))
_zeige(ev.verdict_zufall(ev.zufall_zellen("A")))

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Was zählt als Optimum?")
gk = ev.grobe_zellen("A")
st.markdown(_zellen_tabelle(
    [(f"NK N = {nn}, {st_} Stufen, K = {kk}", z) for (nn, st_, kk), z in sorted(gk.items())],
    [("schwache Optima", lambda z: de(z["schwach"], 1)), ("strenge", lambda z: de(z["streng"], 1)), ("geschlossene Plateaus", lambda z: de(z["geschlossen"], 1)),
     ("schwach je geschlossenem Plateau", lambda z: de(z["faktor"], 1)), ("Scheinoptima unter den schwachen", lambda z: de(100 * z["anteil_schein"], 0) + " %")]))
st.caption("Mittel über 30 Instanzen je Zelle; „schwach je geschlossenem Plateau“ ist der Quotient der beiden Mittel. Die Zeile der gewählten Landschaft steht oben unter „Ergebnis“.")
_zeige(ev.verdict_zaehlweise(gk, gz))

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Wer entscheidet beim Gleichstand?")
st.markdown(C.REGEL_TABELLE)
r1, r2 = st.columns(2)
r1.plotly_chart(viz.build_regeln(regeln), width="stretch", key="regeln_chart")
r2.plotly_chart(viz.build_treffer(regeln), width="stretch", key="treffer_chart")
st.caption(f"Gewählte Landschaft ({a.land.beschreibung}), Seitwärtsgrenze S = {settings.seit}; exakt gerechnet (Erwartungswert über alle Zufallsentscheidungen, Start gleichverteilt über alle Zustände).")
zelle = ev.nk_zellen("A").get((settings.n, settings.stufen, settings.k)) if settings.fahrzeug == "nk" else None
if zelle is not None:
    st.caption(f"Zum Vergleich das Mittel über die 30 Instanzen dieser Zelle (S = 50): Erfolg {de(zelle['erfolg_R0'], 4)} (R0), {de(zelle['erfolg_R1'], 4)} (R1), {de(zelle['erfolg_R2'], 4)} (R2); "
               f"Auswertungen je Abstieg {de(zelle['ausw_R0'], 1)} (R0) gegen {de(zelle['ausw_R2'], 1)} (R2).")
st.markdown(_zellen_tabelle(
    [(f"NK N = {nn}, {'fein' if st_ == M.FEIN else str(st_) + ' Stufen'}, K = {kk}", z) for (nn, st_, kk), z in sorted(ev.nk_zellen("A").items())],
    [("Erfolg R0", lambda z: de(z["erfolg_R0"], 4)), ("R1", lambda z: de(z["erfolg_R1"], 4)), ("R2", lambda z: de(z["erfolg_R2"], 4)),
     ("Auswertungen je Abstieg R0 / R2", lambda z: f"{de(z['ausw_R0'], 1)} / {de(z['ausw_R2'], 1)}"),
     ("Treffer je 1 000 Auswertungen R0 / R2", lambda z: f"{de(z['treffer_R0'], 2)} / {de(z['treffer_R2'], 2)}"),
     ("Instanzen mit R2 unter R0", lambda z: f"{z['r2_unter_r0']} von {z['instanzen']}")]))
st.caption("Mittel über 30 Instanzen je Zelle, S = 50; „fein“ = 1 000 000 Stufen je Beitrag.")
_zeige(ev.verdict_gleichstand(gk))
st.caption("Eine andere Abstiegsregel („zufällig verbessernd“ statt „steilster“) verschiebt die Einzugsgebiete auch ohne Gleichstand; das ist ein anderer Regler und Gegenstand des Stücks über Einzugsgebiete. "
           "R1 wählt nur unter den gleich guten besten Nachbarn.")

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Bei festem Budget")
st.caption("Abstieg mit Neustarts, bis das Budget an Auswertungen verbraucht ist (Neustart 1, jede Durchsuchung M Auswertungen). Stichprobe: 30 Instanzen, 100 Läufe je Instanz und Regel, "
           "Intervall = 95-%-Bootstrap über die Instanzen. Lücke = Abstand des besten besuchten Zustands zum Optimum in Prozent.")
bnk = ev.budget_nk("A")
st.plotly_chart(viz.build_budget(bnk), width="stretch", key="budget_chart")
st.markdown("| K | Budget | Lücke R0 | Lücke R1 | Lücke R2 | R2 − R0 [95-%-Intervall] | Läufe am Optimum R0 / R2 | Instanzen mit R2 besser |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(
    f"| {kk} | {z['budget']} | {de(z['luecke_R0'], 3)} % | {de(z['luecke_R1'], 3)} % | {de(z['luecke_R2'], 3)} % | {ev.vz(z['d_R2_R0'], 3)} [{ev.vz(z['d_unten'], 3)}; {ev.vz(z['d_oben'], 3)}] | "
    f"{de(z['am_optimum_R0'], 2)} / {de(z['am_optimum_R2'], 2)} | {z['r2_besser_instanzen']} von {z['instanzen']} |"
    for kk in sorted(bnk) for z in bnk[kk]))
_zeige(ev.verdict_budget_nk(bnk))
_zeige(ev.verdict_budget_gitter(ev.budget_gitter("A")))
st.caption("Deutung, nicht gemessen: Ein R2-Abstieg kann nicht wissen, dass er am Ziel ist, und geht auch auf dem Plateau des globalen Optimums bis zu S Schritte weiter; jeder kostet M Auswertungen.")
if st.button("Für die gewählte Landschaft nachrechnen (100 Läufe je Regel)", key="budget_live_button"):
    with st.spinner("Rechne 300 Läufe mit je bis zu 3 000 Durchsuchungen (etwa 1 bis 5 Sekunden) …"):
        st.session_state["budget_live"] = (settings, ev.budget_live(a.land, settings.seed))
live = st.session_state.get("budget_live")
if live is not None and live[0] == settings:
    _zeige(ev.verdict_budget_live(live[1], C.BUDGET_LAEUFE_LIVE))
    st.caption("Die Live-Rechnung nutzt die Seitwärtsgrenze 50 und die Budgets 20, 120, 600 und 3 000 mal M.")

st.markdown("---")

# --- Ausblick ------------------------------------------------------------------------------------------------------------------------------

with st.expander("🔭 Ausblick: stetige Landschaften (nicht Gegenstand dieses Stücks)"):
    st.markdown(
        """
Im Stetigen entspricht dem „Stehenbleiben ohne Optimum“ der **Sattelpunkt**: ein Punkt mit Gradient null, der weder Maximum noch Minimum ist. Dieser Ausblick ist **keine Kernaussage** der Demo.

**Exakt** ist nur ein Baukasten-Beispiel: $f(x) = \\sum_i \\cos x_i$ hat auf $[0, 2\\pi)^d$ genau $2^d$ stationäre Punkte (jede Koordinate 0 oder π), davon ein Maximum, ein Minimum und $2^d - 2$ Sattelpunkte.
Das ist eine kombinatorische Tatsache dieser Summenform, kein Befund über Landschaften allgemein.
"""
    )
    st.markdown("| d | stationäre Punkte | Sattelpunkte | Sattelanteil |\n|---|---|---|---|\n" + "\n".join(
        f"| {d} | {p} | {sa} | {de(an, 4)} |" for d in (2, 4, 8) for p, sa, an in [ev.sattel_summe_kosinus(d)]))
    stet = ev.stetig_zellen("A")
    st.markdown("**Stichprobe** an 10 erfundenen Funktionen je Zeile, jede die Summe von 20 Gauß-Kuppen (300 Starts je Funktion und Verfahren): Anteil der Sattelpunkte unter den stationären Punkten, die **dieses Suchverfahren aus dieser Zahl von Starts gefunden hat**.")
    st.markdown("| d | Suchverfahren | Starts mit Konvergenz | gefundene Punkte je Instanz | Sattelanteil unter den gefundenen |\n|---|---|---|---|---|\n" + "\n".join(
        f"| {d} | {'Newton, Schrittlänge höchstens 0,5' if v == 'newton' else 'Levenberg-Marquardt'} | {de(100 * z['konvergenz'], 1)} % | {de(z['punkte_je_instanz'], 1)} | "
        f"{de(z['sattelanteil'], 2) if z['sattelanteil'] is not None else 'kein Punkt gefunden'} |" for (d, v), z in sorted(stet.items())))
    mehr = ev.stetig_mehr_starts("A")
    st.caption(f"Bei gleichen Starts liegen die beiden Suchverfahren bei d = 2 und d = 4 nah beieinander. Die Zahl hängt aber an der Zahl der Starts: Mit {mehr['starts']} statt 300 Starts findet das "
               f"Newton-Verfahren bei d = 4 in denselben Instanzen {de(mehr['punkte_je_instanz'], 1)} statt {de(stet[(4, 'newton')]['punkte_je_instanz'], 1)} Punkte je Instanz, und der Sattelanteil unter den "
               f"gefundenen ist {de(mehr['sattelanteil'], 2)} statt {de(stet[(4, 'newton')]['sattelanteil'], 2)}. Bei d = 8 konvergiert nur ein kleiner Teil der Starts, die Anteile stützen sich dort auf wenige Punkte. "
               "Keine Aussage über höhere Dimensionen und keine Übertragung auf neuronale Netze.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Raum ist aufzählbar klein** (NK bis N = 16, Rundtour bis n = 10) | Größere Räume sind nicht gemessen; alle Zahlen gelten für diese Größen. | kein Stück der Reihe |
| **Zählweise „voll“, steilster Abstieg** | Nachbarlisten, Warteschlange und „erste Verbesserung“ sind hier nicht gemessen. | Stück über Nachbarschaften, Stück über Einzugsgebiete |
| **Nachbarschaft: ein Bit umdrehen beziehungsweise 2-opt** | Eine andere Nachbarschaft ändert auch die Neutralität (nicht gemessen). | Stück über Nachbarschaften |
| **Seitwärtsgrenze S = 50 in den Messreihen** | Andere Grenzen sind nur an der gewählten Landschaft live zu sehen, nicht als Messreihe. | kein Stück der Reihe |
| **Erfundene Instanzen** (keine reale Datenquelle) | Gerundete Straßenentfernungen als naheliegender Praxisfall sind nicht gemessen. | kein Stück der Reihe |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(C.FAHRZEUG_TABELLE)
    st.markdown(
        r"""
**Gegeben** eine endliche Menge $S$ von Zuständen, ein Wert $f(x)$ je Zustand (hier als zu minimierende Größe $V$; beim NK-Modell $V = -F$) und eine symmetrische Nachbarschaft $N(x)$ mit $|N(x)| = M$ in fester Zugreihenfolge.

**Neutralitätsgrad.**

$$\nu = \frac{|\{(x, y) : y \in N(x),\ V(x) = V(y)\}|}{|S| \cdot M}$$

**Plateaus.** Die Kanten $\{x, y\}$ mit $y \in N(x)$ und $V(x) = V(y)$ zerlegen $S$ in Zusammenhangskomponenten. Eine Komponente $P$ mit $|P| \ge 2$ heißt Plateau; sie hat einen **Ausgang**, wenn es $x \in P$ und $y \in N(x)$ mit $V(y) < V(x)$ gibt, sonst ist sie **geschlossen** (auch für $|P| = 1$).

**Optima.** $x$ ist ein schwaches Optimum, wenn $V(y) \ge V(x)$ für alle $y \in N(x)$, ein strenges, wenn $V(y) > V(x)$ für alle $y \in N(x)$. Ein Scheinoptimum ist ein schwaches Optimum in einer Komponente mit Ausgang.

**Abstieg.** Mit $B(x) = \arg\min_{y \in N(x)} V(y)$, falls $\min_{y \in N(x)} V(y) < V(x)$, und $G(x) = \{y \in N(x) : V(y) = V(x)\}$ ist die Trefferwahrscheinlichkeit unter R2 mit Seitwärtszähler $k$ und Grenze $S$

$$p_k(x) = \begin{cases} \dfrac{1}{|B(x)|} \sum_{y \in B(x)} p_0(y) & \text{wenn } x \text{ einen strikt besseren Nachbarn hat} \\ \dfrac{1}{|G(x)|} \sum_{y \in G(x)} p_{k+1}(y) & \text{sonst, wenn } G(x) \ne \emptyset \text{ und } k < S \\ [\,V(x) = \min V\,] & \text{sonst} \end{cases}$$

R1 ist der Fall $S = 0$; R0 ersetzt das Mittel über $B(x)$ durch den ersten Zug aus $B(x)$ in der Zugreihenfolge. Der **Erfolg** ist $\frac{1}{|S|} \sum_x p_0(x)$. Die erwartete Zahl $e_k(x)$ der Durchsuchungen erfüllt dieselbe Rekursion mit $+1$ in jedem Zweig; ein Abstieg kostet $1 + M \cdot e_0$ Auswertungen.

**Stetiger Ausblick.** Für $f(x) = \sum_{i=1}^{d} \cos x_i$ ist der Sattelanteil $1 - 2^{1-d}$.

**Literatur.** Neutralität in Landschaften ist Lehrbuch- und Forschungsstoff, nichts davon ist hier neu. C. M. Reidys, P. F. Stadler: Combinatorial landscapes, SIAM Review 44 (2002), nur die Kurzfassung gelesen.
G. Ochoa, N. Veerapen: Mapping the global structure of TSP fitness landscapes, Journal of Heuristics 24(3), 265–294 (2018), nur die Kurzfassung gelesen (sie berichtet hohe Neutralität bei strukturierten TSP-Instanzen).
L. Altenberg: NK Fitness Landscapes, Handbook of Evolutionary Computation (1997), gelesen; das NK-Modell geht auf S. A. Kauffman und E. D. Weinberger (1989) zurück, nicht gelesen. Konvention hier: K zählt die weiteren Loci.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
