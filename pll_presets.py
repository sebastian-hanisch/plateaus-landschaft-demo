"""Permalink (Begrenzen, Einrasten auf die Auswahlliste), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import pll_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None     # Auswahlliste: Werte außerhalb fallen auf den Standard zurück


SETTING_SPECS = {
    "fahrzeug_select": SettingSpec("f", str, "wuerfel", options=C.FAHRZEUGE),
    "wuerfel_text": SettingSpec("w", str, C.WUERFEL_STANDARD),
    "n_slider": SettingSpec("N", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "k_slider": SettingSpec("K", int, C.DEFAULT_K, C.K_MIN, C.K_MAX),
    "stufen_select": SettingSpec("st", int, C.DEFAULT_STUFEN, options=C.STUFEN),
    "staedte_slider": SettingSpec("n", int, C.DEFAULT_STAEDTE, C.STAEDTE_MIN, C.STAEDTE_MAX),
    "metrik_radio": SettingSpec("m", str, "manhattan", options=C.METRIKEN),
    "gleichheit_radio": SettingSpec("g", str, "toleranz", options=C.GLEICHHEIT),
    "familie_select": SettingSpec("fam", str, "gleich", options=C.FAMILIEN),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "seit_slider": SettingSpec("S", int, C.DEFAULT_SEIT, C.SEIT_MIN, C.SEIT_MAX),
}
PRESET_KEYS = {
    "fahrzeug": "fahrzeug_select", "wuerfel": "wuerfel_text", "n": "n_slider", "k": "k_slider", "stufen": "stufen_select",
    "staedte": "staedte_slider", "metrik": "metrik_radio", "gleichheit": "gleichheit_radio", "familie": "familie_select",
    "seed": "seed_input", "seit": "seit_slider",
}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def begrenzen(spec: SettingSpec, roh):
    """Wert aus der Adresszeile auf den Regler abbilden: Zahlen begrenzen, Auswahlen einrasten; None bei unlesbarem Wert."""
    try:
        value = spec.caster(roh)
    except (ValueError, TypeError):
        return None
    if spec.options is not None:
        return value if value in spec.options else None
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    if spec.caster is str:
        value = value[:80]
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            value = begrenzen(spec, qp[spec.url_param])
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset_fuer(werte: dict):
    """Name des Presets, dessen Werte GENAU den übergebenen Einstellungen {state_key: Wert} entsprechen, sonst None.

    Verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert).
    Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS, dann hebt auch seine Änderung die Markierung auf
    (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(werte.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default) for state_key, spec in SETTING_SPECS.items()):
            return name
    return None


def aktives_preset():
    """Zustandslos: das Preset, das genau den aktuellen Einstellungen im Session State entspricht, sonst None."""
    return aktives_preset_fuer({state_key: st.session_state[state_key] for state_key in SETTING_SPECS if state_key in st.session_state})


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
