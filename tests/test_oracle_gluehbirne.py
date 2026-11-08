"""Orakel-Test gluehbirne-demo / gluehbirne: Kern gegen unabhängige Rechenwege.

Orakel (anderer Rechenweg als die Demo, DEMO-PLAYBOOK §12):
1. Erwartungswert des Standardprotokolls: geschlossene Formel n·H(n−1) + n(n−1) gegen eine Markov-Kette über (Halter, Schalter) mit numpy.linalg.solve (hier im Test gebaut)
   und gegen das Bruch-Gleichungssystem über alle Zustände (glb_exact), dazu die Handwerte 4 und 21/2.
2. Protokoll mit mehreren Zählern: Wahrscheinlichkeits-Weiterschieben über alle Zustände gegen die Simulation (z-Wert), und eine zweite, im Test geschriebene Fassung der Regeln
   gegen glb_protocol auf denselben Besuchsfolgen.
3. Sammelproblem n·H(n) gegen die Simulation des letzten Erstbesuchs.
4. Sicherheit: Breitensuche über ALLE Besuchsfolgen (auch bösartige) findet für Schalter anfangs an nur beim naiven Protokoll eine falsche Meldung; die exakte Fehlerwahrscheinlichkeit.
"""

import math
from fractions import Fraction

import numpy as np
import pytest

import glb_exact as X
import glb_protocol as PR
import glb_simulation as S


# --- Orakel 1: Standardprotokoll -------------------------------------------------------------------------------------------------------------------
def chain_expected_days(n):
    """Markov-Kette: Zustand (h, lt) = (Halter, die ihre Marke noch nicht abgelegt haben; Schalter an?). Besucher: Zähler 1/n, Halter h/n, übrige (n−1−h)/n.
    Zähler nimmt bei „an“ auf (lt → 0) und meldet, wenn dann h = 0 ist; ein Halter legt bei „aus“ ab (h → h−1, lt → 1)."""
    states = [(h, lt) for h in range(n) for lt in (0, 1) if h + lt >= 1]
    idx = {s: i for i, s in enumerate(states)}
    a = np.eye(len(states))
    b = np.ones(len(states))
    for (h, lt), i in idx.items():
        # Zähler
        if lt == 1:
            if h > 0:
                a[i, idx[(h, 0)]] -= 1 / n
            # h == 0: Meldung (Wert 0)
        else:
            a[i, i] -= 1 / n
        # Halter
        if h > 0:
            if lt == 0:
                a[i, idx[(h - 1, 1)]] -= h / n
            else:
                a[i, i] -= h / n
        # übrige
        a[i, i] -= (n - 1 - h) / n
    x = np.linalg.solve(a, b)
    return float(x[idx[(n - 1, 0)]])


@pytest.mark.parametrize("n", range(2, 11))
def test_standard_formula_equals_markov_chain(n):
    assert chain_expected_days(n) == pytest.approx(PR.expected_standard(n), rel=1e-9)


def test_hand_values_n2_n3():
    assert PR.expected_standard_exact(2) == 4 and chain_expected_days(2) == pytest.approx(4.0)
    assert PR.expected_standard_exact(3) == Fraction(21, 2) and chain_expected_days(3) == pytest.approx(10.5)


@pytest.mark.parametrize("n", range(2, 7))
def test_exact_state_enumeration_equals_formula_with_fractions(n):
    p = PR.Protocol(n, 1)
    assert X.expected_days_linear(p, False) == PR.expected_standard_exact(n)
    # Rücksetzung am ersten Tag: Schalter anfangs an hat dieselbe exakte Dauer
    assert X.expected_days_linear(PR.Protocol(n, 1, reset=True), True) == PR.expected_standard_exact(n)


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_propagation_agrees_with_linear_system(n):
    p = PR.Protocol(n, 1)
    assert X.propagate(p, False)["mean"] == pytest.approx(float(PR.expected_standard_exact(n)), abs=1e-9)


def test_simulation_agrees_with_formula_at_n100():
    r = S.simulate_many(PR.Protocol(100, 1), 400, seed=21, init_light=False)
    sm = S.summary(r)
    z = (sm["mean_days"] - PR.expected_standard(100)) / sm["se"]
    assert abs(z) < 4.0, z
    assert sm["finished"] == 400 and sm["wrong_share"] == 0


# --- Orakel 2: mehrere Zähler ----------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n,t", [(4, 2), (5, 2), (6, 2), (6, 3)])
def test_propagation_over_all_states_equals_simulation(n, t):
    p = PR.Protocol(n, t)
    exact = X.propagate(p, False, track_visited=False)
    assert exact["left"] < 1e-12 and exact["wrong"] == 0
    r = S.simulate_many(p, 20000, seed=3, init_light=False)
    sm = S.summary(r)
    z = (sm["mean_days"] - exact["mean"]) / sm["se"]
    assert abs(z) < 4.5, (n, t, exact["mean"], sm["mean_days"], z)
    assert sm["wrong_share"] == 0


def reference_run(n, t, visitors, a, b, r, init_on, reset):
    """Zweite Fassung der Regeln (Aufbau wie der Beschreibungstext der App), ohne Code aus glb_protocol: Rückgabe (Meldetag, alle besucht?)."""
    base, rem = divmod(n - t, t)
    tok = [1] * n
    tal = [0] * n
    for j in range(t):
        tok[j] = -(base + (1 if j < rem else 0))
        tal[j] = 1 if j else -(t - 1)
    light = init_on
    seen_by = set()
    last_phase = 0
    for day, p in enumerate(visitors, start=1):
        seen_by.add(p)
        if t == 1 or day <= a:
            phase, first = 0, day == 1
        elif day <= a + b:
            phase, first = 1, day == a + 1
        else:
            k, off = divmod(day - a - b - 1, r)
            phase, first = k % 2, off == 0
        s = False if (day == 1 and reset) else light
        if first and day > 1 and t > 1 and s:
            if last_phase == 0:
                tok[p] += 1
            else:
                tal[p] += 1
            s = False
        last_phase = phase
        if phase == 0:
            if s and tok[p] < 0:
                tok[p] += 1
                s = False
            elif (not s) and tok[p] > 0:
                tok[p] -= 1
                s = True
        else:
            if s and tal[p] < 0:
                tal[p] += 1
                s = False
            elif (not s) and tal[p] > 0 and tok[p] == 0:
                tal[p] -= 1
                s = True
        light = s
        if p == 0 and tok[0] == 0 and tal[0] == 0:
            return day, len(seen_by) == n
    return None, None


@pytest.mark.parametrize("n,t", [(5, 1), (8, 2), (12, 3), (30, 4), (60, 6), (100, 10)])
def test_second_implementation_of_the_rules_gives_the_same_days(n, t):
    sched = PR.schedule(n, t)
    a, b, r = (sched.first_mark, sched.first_talent, sched.recovery) if sched else (10 ** 9, 1, 10 ** 9)
    for run in range(6):
        seq = S.visitor_sequence(17, run, 6, n, S.day_cap(n))
        day, all_seen = reference_run(n, t, [int(x) for x in seq], a, b, r, False, True)
        mine = S.simulate_run(PR.Protocol(n, t, reset=True), seq, False)
        assert mine.declared_day == day and all_seen is True and not mine.wrong, (n, t, run)


# --- Orakel 3: Sammelproblem -----------------------------------------------------------------------------------------------------------------------
def test_coupon_collector_time_matches_n_h_n():
    n = 20
    r = S.simulate_many(PR.Protocol(n, 1), 4000, seed=8, init_light=False)
    d = r.all_visited_day.astype(float)
    z = (d.mean() - PR.expected_all_visited(n)) / (d.std(ddof=1) / math.sqrt(len(d)))
    assert abs(z) < 4.0, z
    assert (r.days >= r.all_visited_day).all(), "nie eine Meldung vor dem letzten Erstbesuch"


# --- Orakel 4: Sicherheit und Anfangszustand -------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n", range(2, 7))
def test_naive_protocol_with_start_on_errs_with_probability_two_to_minus_n_plus_one(n):
    assert X.wrong_probability_linear(PR.Protocol(n, 1), True) == pytest.approx(2.0 ** -(n - 1), rel=1e-9)
    assert X.wrong_probability_linear(PR.Protocol(n, 1), False) == 0.0


def test_naive_error_probability_by_hand_for_n2():
    """n = 2, Schalter anfangs an, naives Protokoll: Der Zähler (Stand −1) zählt die Phantom-Marke, sobald er den Schalter an sieht.
    Kommt er zuerst (Wahrscheinlichkeit 1/2), meldet er an Tag 1, und Gefangener 1 war nie im Raum: falsch.
    Kommt Gefangener 1 zuerst (1/2), sieht er „an“ und legt nichts ab; der Schalter bleibt an. Meldet der Zähler später, war Gefangener 1 schon im Raum: richtig.
    Also genau 1/2 = 2^-(n−1)."""
    assert X.wrong_probability_linear(PR.Protocol(2, 1), True) == pytest.approx(0.5)


@pytest.mark.parametrize("n", range(2, 7))
def test_shortest_counterexample_has_2n_minus_3_days_and_replays(n):
    v = X.shortest_violation(PR.Protocol(n, 1), True)
    assert v["found"] and v["days"] == 2 * n - 3
    replay = S.simulate_run(PR.Protocol(n, 1), v["visitors"], True)
    assert replay.declared_day == v["days"] and replay.wrong and replay.unvisited == len(v["unvisited"])


@pytest.mark.parametrize("n", range(2, 7))
def test_repairs_are_safe_for_every_visit_sequence(n):
    for p, init in ((PR.Protocol(n, 1, reset=True), True), (PR.Protocol(n, 1, reset=True), False), (PR.Protocol(n, 1), False),
                    (PR.Protocol(n, 1, marks=2), True), (PR.Protocol(n, 1, marks=2), False)):
        r = X.shortest_violation(p, init)
        assert not r["found"] and r["complete"], (n, p, init)


@pytest.mark.parametrize("n,t", [(4, 2), (5, 2), (6, 2), (6, 3)])
def test_several_counters_never_declare_early_for_any_visit_sequence(n, t):
    r = X.shortest_violation(PR.Protocol(n, t, reset=True), True, max_states=3_000_000)
    assert not r["found"] and r["complete"], (n, t, r)
    r2 = X.shortest_violation(PR.Protocol(n, t), False, max_states=3_000_000)
    assert not r2["found"] and r2["complete"], (n, t, r2)


def test_several_counters_without_reset_and_start_on_are_not_safe():
    """Zweig-Test: derselbe Phantom-Fehler tritt auch bei mehreren Zählern auf, wenn der Schalter anfangs an ist und nichts zurückgesetzt wird."""
    v = X.shortest_violation(PR.Protocol(4, 2), True)
    assert v["found"]
    assert S.simulate_run(PR.Protocol(4, 2), v["visitors"], True).wrong


def test_double_marks_cost_about_twice_the_standard_without_a_wrong_claim():
    for n in (4, 5, 6):
        d_off = float(X.expected_days_linear(PR.Protocol(n, 1, marks=2), False))
        d_on = float(X.expected_days_linear(PR.Protocol(n, 1, marks=2), True))
        std = float(PR.expected_standard_exact(n))
        assert 1.5 * std < d_on < d_off < 2.2 * std, (n, d_on, d_off, std)
        assert X.wrong_probability_linear(PR.Protocol(n, 1, marks=2), True) == 0.0
