"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink, Verdikt je Preset (DEMO-PLAYBOOK §11a, Regel 7)."""

import pytest

import glb_constants as C
import glb_evaluation as V
import glb_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.T_MIN <= preset["t"] <= C.T_MAX, name
        assert C.RUNS_MIN <= preset["runs"] <= C.RUNS_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name
        assert preset["init"] in C.INIT_STATES and preset["reset"] in C.RESET_CHOICES, name


def test_default_preset_equals_the_default_settings():
    assert V.Settings(**C.PRESETS["Standard: 100 Gefangene, ein Zähler"]) == V.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_list_their_allowed_values():
    assert P.SETTING_SPECS["init_select"].choices == C.INIT_STATES and P.SETTING_SPECS["reset_select"].choices == C.RESET_CHOICES
    assert P.SETTING_SPECS["init_select"].default in C.INIT_STATES


def test_presets_differ_from_each_other():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_its_verdict_matches_its_name(name):
    """Jedes Preset durchläuft die Analyse; die Verdikt-Art passt zum Namen (Preset ohne Fehler meldet keinen Fehler, naives Preset keinen Erfolg)."""
    s = V.Settings(**C.PRESETS[name])
    a = V.analyse(s)
    kind, text = V.verdict_main(a)
    assert a.summary["finished"] == s.runs
    if "naiv" in name:
        assert kind == "error" and a.summary["wrong_share"] > 0
    else:
        assert kind in ("success", "info") and a.summary["wrong_share"] == 0, (name, text)


def test_preset_help_numbers_for_the_start_state_presets_match_the_exact_probability():
    """Das naive Preset (n = 4) fehlt mit der exakten Wahrscheinlichkeit 1/8; in 400 Läufen sind das rund 50 falsche Meldungen."""
    s = V.Settings(**C.PRESETS["Schalter anfangs an, naiv"])
    a = V.analyse(s)
    assert a.exact["wrong"] == pytest.approx(0.125)
    assert abs(a.summary["wrong_share"] - 0.125) < 4 * (0.125 * 0.875 / s.runs) ** 0.5
