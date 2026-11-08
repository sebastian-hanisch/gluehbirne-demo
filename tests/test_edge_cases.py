"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 2, t an der Grenze n // 2, Phasengrenzen inklusive, kleinste und größte Reglerwerte."""

import numpy as np
import pytest

import glb_constants as C
import glb_evaluation as V
import glb_protocol as PR
import glb_simulation as S


def test_exactly_two_prisoners():
    """n = 2: der kleinste Fall (ein Zähler, ein Halter); jedes t wird auf 1 begrenzt, die Dauer ist im Mittel 4 Tage."""
    for t in (1, 2, 20):
        assert PR.Protocol(2, t).t_eff == 1
    r = S.simulate_many(PR.Protocol(2, 1), 4000, seed=1, init_light=False)
    sm = S.summary(r)
    assert abs(sm["mean_days"] - 4.0) < 4 * sm["se"] and sm["wrong_share"] == 0 and sm["max_days"] >= 2


def test_three_prisoners_cannot_have_two_counters():
    assert PR.Protocol(3, 5).t_eff == 1 and PR.Protocol(4, 5).t_eff == 2 and PR.Protocol(5, 5).t_eff == 2


def test_one_prisoner_is_rejected():
    with pytest.raises(ValueError):
        PR.Protocol(1, 1)


def test_half_the_prisoners_as_counters_all_goals_one():
    """t = n // 2 bei geradem n: jeder Zähler soll genau eine Marke einsammeln (n − t = t)."""
    assert PR.goals(40, 20) == [1] * 20
    r = S.simulate_many(PR.Protocol(40, 20), 30, seed=2, init_light=False)
    assert (r.days > 0).all() and not r.wrong.any()


def test_odd_n_gives_the_rest_to_the_first_counters():
    assert PR.goals(11, 5) == [2, 1, 1, 1, 1] and sum(PR.goals(11, 5)) == 6
    r = S.simulate_many(PR.Protocol(11, 5), 30, seed=2, init_light=False)
    assert (r.days > 0).all() and not r.wrong.any()


def test_phase_boundaries_are_inclusive_on_the_first_day_of_the_new_phase():
    s = PR.Schedule(5, 3, 4)
    assert [PR.phase_info(s, d)[0] for d in (5, 6, 8, 9, 12, 13)] == [PR.MARKE, PR.TALENT, PR.TALENT, PR.MARKE, PR.MARKE, PR.TALENT]
    assert [PR.phase_info(s, d)[1] for d in (5, 6, 8, 9, 12, 13)] == [False, True, False, True, False, True]


def test_phases_are_never_shorter_than_one_day():
    for n in (4, 5, 8, 30, 100):
        for t in range(2, n // 2 + 1):
            s = PR.schedule(n, t)
            assert s.first_mark >= 1 and s.first_talent >= 1 and s.recovery >= 1


def test_single_run_and_minimum_runs():
    r = S.simulate_many(PR.Protocol(5, 1), 1, seed=1, init_light=False)
    assert r.days.shape == (1,) and r.days[0] >= 8
    sm = S.summary(r)
    assert sm["finished"] == 1 and np.isnan(sm["se"])


def test_settings_at_every_slider_bound_run():
    for n in (C.N_MIN, C.N_MAX):
        for t in (C.T_MIN, C.T_MAX):
            a = V.analyse(V.Settings(n=n, t=t, runs=C.RUNS_MIN))
            assert a.summary["finished"] == C.RUNS_MIN and a.t_eff == max(1, min(t, n // 2))
            assert len(a.trace["who"]) > 0


def test_worst_case_at_the_slider_maximum_finishes():
    """Standardprotokoll bei n = 100 mit der größten Zahl Läufe: alle Läufe melden vor der Tagesgrenze (kein Hänger, kein Aufblähen)."""
    r = S.simulate_many(PR.Protocol(C.N_MAX, 1), C.RUNS_MAX, seed=77, init_light=False)
    assert (r.days > 0).all() and r.days.max() < S.day_cap(C.N_MAX) / 4


def test_trace_is_capped_and_complete_for_a_normal_run():
    a = V.analyse(V.Settings(n=100, t=1, runs=C.RUNS_MIN, seed=3))
    assert a.run0_day == len(a.trace["who"])


def test_exact_small_is_none_above_the_limit():
    assert V.exact_small(V.Settings(n=C.EXACT_N_MAX + 1)) is None
    e = V.exact_small(V.Settings(n=3, t=1))
    assert e["mean"] == pytest.approx(10.5, abs=1e-9) and e["wrong"] == 0.0


def test_exact_small_reports_the_error_probability_for_start_on():
    e = V.exact_small(V.Settings(n=4, t=1, init="an", reset="nein"))
    assert e["wrong"] == pytest.approx(1 / 8, rel=1e-9)


def test_default_counters_rule():
    assert [V.default_counters(n) for n in (10, 20, 30, 50, 100)] == [3, 4, 5, 7, 10]
    assert V.default_counters(2) == 1 and V.default_counters(3) == 1
