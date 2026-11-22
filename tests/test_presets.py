"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung, erwartete Befunde je Preset."""

import pll_constants as C
import pll_evaluation as ev
import pll_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    assert len(C.PRESETS) == 8
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.options is not None:
                assert preset[key] in spec.options, (name, key)
            elif spec.caster is int:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert ev.wuerfel_werte(preset["wuerfel"])[1], name


def test_kopplung_passt_in_jede_laenge():
    assert C.K_MAX < C.N_MIN


def test_default_preset_equals_the_default_settings():
    assert _settings(next(iter(C.PRESETS))) == ev.Settings()
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        assert getattr(ev.Settings(), key) == spec.default, state_key


def test_setting_specs_cover_every_preset_key_and_every_settings_field():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert set(P.PRESET_KEYS) == set(ev.Settings.__dataclass_fields__)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


def test_permalink_begrenzt_zahlen_und_rastet_auswahlen_ein():
    assert P.begrenzen(P.SETTING_SPECS["n_slider"], "99") == C.N_MAX
    assert P.begrenzen(P.SETTING_SPECS["n_slider"], "-3") == C.N_MIN
    assert P.begrenzen(P.SETTING_SPECS["n_slider"], "abc") is None
    assert P.begrenzen(P.SETTING_SPECS["stufen_select"], "5") is None            # 5 steht nicht in der Auswahl
    assert P.begrenzen(P.SETTING_SPECS["stufen_select"], "30") == 30
    assert P.begrenzen(P.SETTING_SPECS["fahrzeug_select"], "nk") == "nk"
    assert P.begrenzen(P.SETTING_SPECS["fahrzeug_select"], "auto") is None
    assert len(P.begrenzen(P.SETTING_SPECS["wuerfel_text"], "1," * 200)) == 80


def test_presets_zeigen_was_ihr_name_und_hilfetext_sagen():
    """Je Preset der erwartete Befund an der Landschaft selbst (die Verdikt-Zeilen dazu prüft tests/test_verdicts.py)."""
    k = {name: ev.analyse(_settings(name)) for name in C.PRESETS}
    wuerfel = k["Von Hand (Würfel, 8 Zustände)"].kenn
    assert (wuerfel.schwach, wuerfel.streng, wuerfel.geschlossen, wuerfel.scheinoptima) == (3, 2, 2, 1)
    tour = k["Von Hand (Tour, 7 Städte)"].kenn
    assert (tour.zustaende, tour.schwach, tour.geschlossen) == (360, 2, 1)
    grob, fein = k["NK grob (3 Stufen)"].kenn, k["NK fein (Kontrolle)"].kenn
    assert grob.zustaende == fein.zustaende == 2 ** 14
    assert grob.nu > 0.1 and grob.schwach > grob.geschlossen and grob.scheinoptima > 0
    assert fein.gleiche_paare == 0 and fein.plateaus == 0 and fein.schwach == fein.streng == fein.geschlossen       # KEINE Neutralität
    manhattan, euklid = k["Gitter Manhattan n = 9"].kenn, k["Gitter euklidisch n = 9"].kenn
    assert manhattan.zustaende == euklid.zustaende == 20160 and manhattan.zuege == 27
    assert manhattan.nu > euklid.nu > 0                                             # euklidisch: weniger Gleichstände
    zufall = k["Zufallskoordinaten"].kenn
    assert zufall.gleiche_paare == 0 and zufall.plateaus == 0 and zufall.scheinoptima == 0                          # KEINE Plateaus
    ohne = k["Würfel: Seitwärts ohne Nutzen"]
    assert ohne.seit == 3 and ohne.regeln["R2"]["erfolg"] < ohne.regeln["R0"]["erfolg"]


def test_aktives_preset_ist_zustandslos_und_genau():
    key_of = {key: state_key for key, state_key in P.PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        werte = {key_of[k]: v for k, v in preset.items()}
        assert P.aktives_preset_fuer(werte) == name
        assert P.aktives_preset_fuer(dict(werte, seit_slider=17)) is None
    assert P.aktives_preset_fuer({}) == next(iter(C.PRESETS))          # fehlende Regler meinen den Standardwert
