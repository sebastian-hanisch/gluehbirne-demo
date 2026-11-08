"""Simulation: skalare Fassung (Tag für Tag) gegen die vektorisierte Fassung (viele Läufe nebeneinander), Zufallsstrom, Rücksetzung, Zweige."""

import numpy as np
import pytest

import glb_constants as C
import glb_protocol as PR
import glb_simulation as S

CASES = [(2, 1), (3, 1), (6, 1), (12, 2), (30, 3), (40, 5), (100, 10)]


def _independent_standard(n, visitors, init_light, reset):
    """Das Standardprotokoll noch einmal ohne gemeinsamen Code mit glb_protocol: Zähler 0, Marken als einfache Liste."""
    has_token = [True] * n
    has_token[0] = False
    light = init_light
    collected = 0
    for day, who in enumerate(visitors, start=1):
        seen = light
        if day == 1 and reset:
            seen = False
        if who == 0:
            if seen:
                collected += 1
                light = False
            else:
                light = seen
            if collected == n - 1:
                return day
        else:
            if (not seen) and has_token[who]:
                has_token[who] = False
                light = True
            else:
                light = seen
    return None


@pytest.mark.parametrize("n,t", CASES)
def test_vector_and_scalar_runs_agree_run_by_run(n, t):
    p = PR.Protocol(n, t)
    runs = 8
    many = S.simulate_many(p, runs, seed=7, init_light=False)
    for run in range(runs):
        seq = S.visitor_sequence(7, run, runs, n, S.day_cap(n))
        one = S.simulate_run(p, seq, False)
        assert one.declared_day == many.days[run]
        assert one.wrong == many.wrong[run]
        assert one.unvisited == many.unvisited[run]
        assert one.seen_on == many.seen_on[run]
        assert (one.all_visited_day or -1) == many.all_visited_day[run]


@pytest.mark.parametrize("reset,init", [(False, False), (True, False), (True, True), (False, True)])
def test_vector_and_scalar_agree_for_start_variants(reset, init):
    p = PR.Protocol(5, 1, reset=reset)
    many = S.simulate_many(p, 30, seed=3, init_light=init)
    for run in range(30):
        seq = S.visitor_sequence(3, run, 30, 5, S.day_cap(5))
        one = S.simulate_run(p, seq, init)
        assert (one.declared_day, one.wrong) == (many.days[run], many.wrong[run])


def test_vector_and_scalar_agree_for_double_marks():
    p = PR.Protocol(6, 1, marks=2)
    many = S.simulate_many(p, 20, seed=5, init_light=True)
    for run in range(20):
        one = S.simulate_run(p, S.visitor_sequence(5, run, 20, 6, S.day_cap(6)), True)
        assert (one.declared_day, one.wrong) == (many.days[run], many.wrong[run])


@pytest.mark.parametrize("n", [2, 3, 5, 8])
@pytest.mark.parametrize("reset", [False, True])
def test_one_counter_equals_an_independent_standard_implementation(n, reset):
    p = PR.Protocol(n, 1, reset=reset)
    for run in range(25):
        seq = S.visitor_sequence(11, run, 25, n, S.day_cap(n))
        for init in (False, True):
            if init and not reset:
                continue            # der naive Zähler zählt dann die Phantom-Marke; die Vergleichsfassung kennt die gleiche Regel, unten extra geprüft
            assert S.simulate_run(p, seq, init).declared_day == _independent_standard(n, seq, init, reset), (n, reset, init, run)


def test_independent_standard_also_matches_for_start_on_without_reset():
    p = PR.Protocol(5, 1)
    for run in range(60):
        seq = S.visitor_sequence(13, run, 60, 5, S.day_cap(5))
        assert S.simulate_run(p, seq, True).declared_day == _independent_standard(5, seq, True, False)


def test_reset_makes_the_start_state_irrelevant():
    """Mit Rücksetzung am ersten Tag sind die Läufe für Schalter anfangs an und aus Tag für Tag gleich."""
    for n, t in ((6, 1), (12, 2), (30, 3)):
        p = PR.Protocol(n, t, reset=True)
        a = S.simulate_many(p, 40, seed=9, init_light=False)
        b = S.simulate_many(p, 40, seed=9, init_light=True)
        assert np.array_equal(a.days, b.days)
        assert not a.wrong.any() and not b.wrong.any()


def test_without_reset_the_start_state_changes_the_runs():
    """Zweig-Test: ohne Rücksetzung unterscheiden sich Schalter an und aus (sonst wäre der Regler tot)."""
    p = PR.Protocol(4, 1)
    off = S.simulate_many(p, 200, seed=9, init_light=False)
    on = S.simulate_many(p, 200, seed=9, init_light=True)
    assert not np.array_equal(off.days, on.days)
    assert on.wrong.any() and not off.wrong.any()


def test_several_counters_differ_from_one_counter():
    one = S.simulate_many(PR.Protocol(30, 1), 40, seed=2, init_light=False)
    three = S.simulate_many(PR.Protocol(30, 3), 40, seed=2, init_light=False)
    assert not np.array_equal(one.days, three.days)


def test_stream_is_deterministic_and_seed_dependent():
    a = S.visitors_block(5, 0, 4, 10)
    assert np.array_equal(a, S.visitors_block(5, 0, 4, 10))
    assert not np.array_equal(a, S.visitors_block(6, 0, 4, 10))
    assert a.shape == (C.CHUNK, 4) and a.min() >= 0 and a.max() <= 9


def test_visitors_are_roughly_uniform():
    v = S.visitors_block(1, 0, 400, 10).ravel()
    counts = np.bincount(v, minlength=10)
    assert counts.min() > 0.9 * len(v) / 10 and counts.max() < 1.1 * len(v) / 10


def test_visitor_sequence_matches_block_columns_across_chunks():
    seq = S.visitor_sequence(4, 2, 5, 9, 2 * C.CHUNK + 10)
    assert len(seq) == 2 * C.CHUNK + 10
    assert np.array_equal(seq[: C.CHUNK], S.visitors_block(4, 0, 5, 9)[:, 2])
    assert np.array_equal(seq[C.CHUNK: 2 * C.CHUNK], S.visitors_block(4, 1, 5, 9)[:, 2])


def test_day_cap_stops_a_run_without_declaration():
    r = S.simulate_many(PR.Protocol(30, 1), 5, seed=1, init_light=False, cap=20)
    assert (r.days == -1).all()
    assert S.summary(r)["finished"] == 0


def test_summary_counts_and_shares():
    r = S.simulate_many(PR.Protocol(6, 1), 50, seed=1, init_light=False)
    sm = S.summary(r)
    assert sm["runs"] == 50 and sm["finished"] == 50 and sm["wrong_share"] == 0.0
    assert 0 < sm["on_share"] < 1 and sm["max_days"] >= sm["median_days"] >= 2 * (6 - 1)   # n − 1 Ablagen und n − 1 Aufnahmen brauchen je einen eigenen Tag
    assert sm["mean_all_visited"] < sm["mean_days"]


def test_trace_matches_the_declaration():
    p = PR.Protocol(6, 1)
    seq = S.visitor_sequence(2, 0, 1, 6, S.day_cap(6))
    r = S.simulate_run(p, seq, False, record=True)
    n_days = r.declared_day
    assert all(len(v) == n_days for v in r.trace.values())
    assert r.trace["goal_left"][-1] == 0 and r.trace["goal_left"][0] in (5, 4)
    assert r.trace["visited"][-1] <= 6 and r.trace["head_tok"][-1] == 0
    assert r.trace["goal_left"] == sorted(r.trace["goal_left"], reverse=True), "offene Marken können nur sinken"
