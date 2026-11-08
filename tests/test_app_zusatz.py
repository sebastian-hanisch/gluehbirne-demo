"""App-Verhalten über den Rauchtest hinaus: Permalink, Auswahlregler, Eckfall-Kombinationen (DEMO-PLAYBOOK §1d), Experimente nach Klick, Hinweis bei begrenztem t, PDF."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import glb_constants as C
import glb_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_values_are_taken_over_and_clamped():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["n"] = "500"          # über dem Maximum
    at.query_params["t"] = "4"
    at.query_params["start"] = "an"
    at.query_params["reset"] = "ja"
    at.query_params["laeufe"] = "30"
    at.run()
    assert not at.exception
    assert at.session_state["n_slider"] == C.N_MAX and at.session_state["t_slider"] == 4
    assert at.session_state["init_select"] == "an" and at.session_state["reset_select"] == "ja" and at.session_state["runs_slider"] == 30


def test_permalink_ignores_values_outside_the_choices():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["start"] = "vielleicht"
    at.run()
    assert not at.exception and at.session_state["init_select"] == C.DEFAULT_INIT


@pytest.mark.parametrize("init", C.INIT_STATES)
@pytest.mark.parametrize("reset", C.RESET_CHOICES)
def test_every_combination_of_the_two_choice_controls_runs(init, reset):
    at = _app()
    at.session_state["init_select"] = init
    at.session_state["reset_select"] = reset
    at.session_state["n_slider"] = 6
    at.run()
    assert not at.exception, [str(e) for e in at.exception]


def test_all_minima_and_all_maxima_together_run():
    for pick in ("lo", "hi"):
        at = _app()
        for key, spec in P.SETTING_SPECS.items():
            if spec.choices is None and key != "seed_input":
                at.session_state[key] = spec.lo if pick == "lo" else spec.hi
        at.run()
        assert not at.exception, (pick, [str(e) for e in at.exception])


def test_too_many_counters_are_clamped_with_a_note():
    at = _app()
    at.session_state["n_slider"] = 6
    at.session_state["t_slider"] = 20
    at.run()
    assert not at.exception
    assert any("höchstens 3 Zähler" in i.value for i in at.info)


def test_no_note_when_the_counters_fit():
    at = _app()
    at.session_state["t_slider"] = 10
    at.run()
    assert not any("höchstens" in i.value for i in at.info)


def test_start_on_without_reset_for_few_prisoners_shows_the_error_verdict_and_the_exact_line():
    at = _app()
    at.session_state["n_slider"] = 4
    at.session_state["init_select"] = "an"
    at.session_state["runs_slider"] = 400
    at.run()
    assert not at.exception
    assert any("zu früh" in e.value for e in at.error)
    assert any("Exakt über alle Zustände" in c.value and "0,1250" in c.value for c in at.caption)


def test_counter_experiment_shows_chart_and_verdict_after_the_click():
    at = _app()
    assert not any("Bester Wert" in s.value for s in at.success)
    at.button(key="e1_button").click().run()
    assert not at.exception
    assert any("Bester Wert t =" in s.value for s in at.success)


def test_scaling_experiment_shows_verdict_after_the_click():
    at = _app()
    at.button(key="e3_button").click().run()
    assert not at.exception
    assert any("geprüften Größen" in i.value for i in at.info)


def test_start_experiment_table_is_there_without_a_click():
    at = _app()
    assert any("naive Standardprotokoll" in w.value for w in at.warning)
    assert at.dataframe, "Tabelle des Anfangszustand-Experiments fehlt"


def test_pdf_is_built_only_after_the_click():
    at = _app()
    assert "pdf_bytes" not in at.session_state
    at.button(key="pdf_button").click().run()
    assert not at.exception
    assert at.session_state["pdf_bytes"][:5] == b"%PDF-"


def test_math_expander_has_one_formula_per_block_and_the_symbol_table():
    at = _app()
    expander = next(e for e in at.expander if e.label == "📐 Mathematische Formulierung")
    assert expander is not None
    assert len(at.get("latex")) >= 4                            # je Display-Gleichung ein Block
    assert any("| Symbol | Bedeutung |" in m.value for m in at.markdown)
