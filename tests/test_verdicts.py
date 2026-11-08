"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import glb_evaluation as V


def _analysis(*, n=100, t=1, init="aus", reset="nein", runs=100, mean=10400.0, se=100.0, finished=None, wrong=0.0, t_eff=None, formula=10417.7):
    s = V.Settings(n=n, t=t, init=init, reset=reset, runs=runs)
    summary = {"runs": runs, "finished": runs if finished is None else finished, "mean_days": mean, "se": se, "median_days": mean, "max_days": int(mean * 1.3), "wrong_share": wrong,
               "mean_all_visited": 500.0, "on_share": 0.95}
    return V.Analysis(settings=s, t_eff=t if t_eff is None else t_eff, summary=summary, days=(1, 2), trace={}, run0_day=1, run0_wrong=False,
                      standard_formula=formula, all_visited_formula=518.7, exact=None)


def test_number_formats():
    assert V.days_text(10417.7377) == "10.417,7" and V.days_text(0.04) == "0,0" and V.days_text(999.96) == "1.000,0"
    assert V.de(-0.04, 1) == "0,0" and V.de(-2.5, 1) == "−2,5"
    assert V.thousands(10417.7) == "10.418" and V.pct(0.125, 1) == "12,5 %" and V.years(10417.7) == "28,5"
    assert V.fraction_text(0.125) == "1/8" and V.fraction_text(1 / 3) == "1/3" and V.fraction_text(0.4) == "40,00 %" and V.fraction_text(0) == "0"


def test_main_verdict_one_counter_names_mean_formula_and_difference():
    kind, text = V.verdict_main(_analysis(mean=10436.9, se=97.0))
    assert kind == "success"
    assert "10.436,9 Tagen" in text and "rund 28,6 Jahre" in text and "10.417,7 Tage" in text
    assert "19,2 Tage" in text and "194,0 Tage" in text                  # 10436,9 − 10417,7; zwei Standardfehler


def test_main_verdict_years_only_from_one_year_on():
    assert "Jahre" in V.verdict_main(_analysis(mean=365.0))[1]
    assert "Jahre" not in V.verdict_main(_analysis(mean=364.9))[1]


def test_main_verdict_several_counters_names_the_factor():
    kind, text = V.verdict_main(_analysis(t=10, mean=3700.0, formula=10417.7))
    assert kind == "success" and "3.700,0 Tagen" in text and "2,8 mal so lang" in text           # 10417,7 / 3700 = 2,816


def test_main_verdict_wrong_claims_are_an_error_with_count():
    kind, text = V.verdict_main(_analysis(init="an", wrong=0.125, runs=400, n=4))
    assert kind == "error" and "In 50 von 400 Läufen (12,5 %)" in text


def test_main_verdict_unfinished_runs_are_a_warning():
    kind, text = V.verdict_main(_analysis(finished=97, runs=100))
    assert kind == "warning" and "3 von 100 Läufen" in text and "die 97 anderen" in text


def test_main_verdict_start_on_without_reset_and_no_error_seen_is_neutral():
    kind, text = V.verdict_main(_analysis(init="an", reset="nein", n=100))
    assert kind == "info" and "Formel" not in text


def _grid(means):
    return [{"t": t, "mean": m} for t, m in means]


def test_counters_verdict_best_value_and_near_minimum_count():
    rows = _grid([(1, 10000.0), (2, 8000.0), (4, 5000.0), (8, 3700.0), (10, 3600.0), (12, 3950.0), (16, 4100.0)])
    kind, text = V.verdict_counters(rows)
    assert kind == "success" and "t = 10: 3.600,0 Tage statt 10.000,0" in text and "2,8 mal so schnell" in text
    assert "3 von 7" in text and "t = 8, 10, 12" in text                                          # 1,10 · 3600 = 3960: 3700, 3600 und 3950 zählen mit, 4100 nicht


def test_counters_verdict_threshold_is_inclusive_at_ten_percent():
    rows = _grid([(1, 1000.0), (2, 100.0), (4, 110.0), (8, 110.1)])
    _, text = V.verdict_counters(rows)
    assert "t = 2, 4)" in text and "2 von 4" in text


def test_counters_verdict_when_one_counter_wins():
    kind, text = V.verdict_counters(_grid([(1, 100.0), (2, 130.0)]))
    assert kind == "info" and "t = 1, 100,0 Tage" in text and "2 Werte von t" in text
    kind, text = V.verdict_counters(_grid([(1, 100.0)]))
    assert kind == "info" and "nur ein Zähler möglich" in text


def test_scaling_verdict_names_first_last_and_wins():
    rows = [{"n": 10, "t": 3, "single": 115.0, "multi": 130.0}, {"n": 50, "t": 7, "single": 2600.0, "multi": 1300.0}, {"n": 100, "t": 10, "single": 10400.0, "multi": 3700.0}]
    kind, text = V.verdict_scaling(rows)
    assert kind == "info"
    assert "Bei n = 10 Gefangenen braucht t = 3 Zähler 130,0 Tage gegen 115,0" in text and "Faktor 0,88" in text
    assert "bei n = 100 sind es 3.700,0 gegen 10.400,0" in text and "Faktor 2,81" in text
    assert "in 2 von 3 geprüften Größen" in text


def test_start_verdict_lists_probabilities_and_counts():
    rows = [
        {"n": 3, "wrong_naive": 0.25, "found": True, "safe_reset": True, "safe_double": True},
        {"n": 4, "wrong_naive": 0.125, "found": True, "safe_reset": True, "safe_double": False},
    ]
    kind, text = V.verdict_start(rows)
    assert kind == "warning"
    assert "n = 3: 1/4; n = 4: 1/8" in text and "für 2 von 2 Größen" in text and "in 1 von 2 Größen" in text
