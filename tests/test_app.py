"""End-to-end-Tests mit Streamlits AppTest: Standardlauf, jeder Knopf, jeder Regler an seinen Grenzen, jede Auswahl,
Permalink, Schlüssel der Diagramme, Expander per Titel, Live-Rechnung bei festem Budget."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import pll_constants as C
import pll_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer
AUTOPLAY_MARKER = "▶"


def _fresh_app(**query) -> AppTest:
    at = AppTest.from_file(APP_PATH)
    for key, value in query.items():
        at.query_params[key] = value
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    teile = [m.value for m in at.markdown] + [c.value for c in at.caption]
    for art in ("success", "info", "warning"):
        teile += [e.value for e in getattr(at, art)]
    return "\n".join(teile)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert at.title[0].value.endswith("Plateaus: wenn gleich gut nicht fertig heißt")
    assert len(at.metric) == 5 and at.metric[0].value == "0,1667"            # Würfel: ν = 1/6
    assert [m.value for m in at.metric[1:]] == ["3", "2", "2", "1"]


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert len(labels) == len(C.PRESETS) + 2
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app(f="nk", N="10")                                          # im Fahrzeug NK ist jeder Knopf bedienbar
        assert not at.button[index].disabled, label
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


@pytest.mark.parametrize("fahrzeug", C.FAHRZEUGE)
def test_every_slider_at_its_min_and_max_does_not_raise(fahrzeug):
    labels = [s.label for s in _fresh_app(f=fahrzeug).slider]
    assert len(labels) == 4
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app(f=fahrzeug)
            slider = at.slider[index]
            if slider.disabled:
                continue                                                      # gesperrt, weil ohne Bedeutung für dieses Fahrzeug
            slider.set_value(int(slider.min if edge == "min" else slider.max)).run(timeout=TIMEOUT)
            assert not at.exception, (fahrzeug, label, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("state_key", [k for k, spec in P.SETTING_SPECS.items() if spec.options is not None])
def test_jede_auswahl_jeder_wert(state_key):
    spec = P.SETTING_SPECS[state_key]
    basis = {"metrik_radio": "gitter", "gleichheit_radio": "gitter", "familie_select": "zufall", "stufen_select": "nk"}.get(state_key)
    for wert in spec.options:
        query = {spec.url_param: str(wert)}
        if basis:
            query["f"] = basis
        if state_key == "gleichheit_radio":
            query["m"] = "euklid"
        at = _fresh_app(**query)
        assert at.session_state[state_key] == wert


def test_permalink_wird_begrenzt_und_gespiegelt():
    at = _fresh_app(f="nk", N="99", K="-4", st="5", S="7", seed="12")
    assert at.session_state["n_slider"] == C.N_MAX and at.session_state["k_slider"] == C.K_MIN
    assert at.session_state["stufen_select"] == C.DEFAULT_STUFEN and at.session_state["seit_slider"] == 7
    assert at.query_params["N"] in (str(C.N_MAX), [str(C.N_MAX)]) and at.query_params["f"] in ("nk", ["nk"]) and at.query_params["seed"] in ("12", ["12"])


def test_ungueltige_wuerfelwerte_warnen_und_rechnen_mit_dem_handbeispiel():
    at = _fresh_app(w="1,2,3")
    assert any("keine acht ganzen Zahlen" in w.value for w in at.warning)
    assert at.metric[0].value == "0,1667"


def test_gesperrte_regler_je_fahrzeug():
    at = _fresh_app()
    assert at.sidebar.slider(key="n_slider").disabled and at.sidebar.slider(key="staedte_slider").disabled and not at.sidebar.slider(key="seit_slider").disabled
    at = _fresh_app(f="nk")
    assert not at.sidebar.slider(key="n_slider").disabled and at.sidebar.slider(key="staedte_slider").disabled
    at = _fresh_app(f="gitter", m="euklid")
    assert not at.sidebar.radio(key="gleichheit_radio").disabled and at.sidebar.selectbox(key="familie_select").disabled
    at = _fresh_app(f="gitter", m="manhattan")
    assert at.sidebar.radio(key="gleichheit_radio").disabled


def test_expander_per_titel_und_fuenf_experimente():
    at = _fresh_app()
    titel = [e.label for e in at.expander]
    for erwartet in ("So funktioniert die Zählung von Plateaus", "🔭 Ausblick: stetige Landschaften (nicht Gegenstand dieses Stücks)", "📐 Mathematische Formulierung"):
        assert erwartet in titel
    experimente = [s.value for s in at.subheader if s.value.startswith("🔬 Experiment")]
    assert len(experimente) == 5                                              # höchstens fünf Experimente je Seite


def test_verdikte_der_app_sind_die_der_auswertung():
    at = _fresh_app()
    text = _texte(at)
    assert "**3 schwache**, **2 strenge** Optima, aber **2 geschlossene Plateaus**" in text
    assert "0,5000** (R0), **0,5833** (R1), **0,6458** (R2, S = 50)" in text
    assert "R2 hat im Mittel in **0 von 12 Zellen** die kleinere Lücke" in text
    at = _fresh_app(f="zufall", seed="0")
    text = _texte(at)
    assert "keinen Gleichstand zwischen Nachbarn" in text and "Keine Neutralität" in text and "Diese Landschaft hat kein Plateau" in text


def test_live_rechnung_bei_festem_budget_erscheint_nur_fuer_die_gerechnete_landschaft():
    at = _fresh_app(f="nk", N="10")
    at.button(key="budget_live_button").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Diese eine Landschaft, 100 Läufe je Regel" in i.value for i in at.info)
    at.sidebar.slider(key="k_slider").set_value(3).run(timeout=TIMEOUT)
    assert not any("Diese eine Landschaft, 100 Läufe je Regel" in i.value for i in at.info)


def test_kein_formelfehler_durch_ungeschuetztes_prozentzeichen():
    at = _fresh_app()
    formeln = [m.value for m in at.markdown if "$$" in m.value]
    assert formeln and all("%" not in f.split("**Literatur.**")[0] for f in formeln)
