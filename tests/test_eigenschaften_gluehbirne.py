"""Eigenschaftstests: Invarianten, die für jede Besuchsfolge gelten müssen (nicht nur für gleichverteilte)."""

import numpy as np
import pytest

import glb_protocol as PR
import glb_simulation as S

CONFIGS = [(6, 1, 1), (6, 1, 2), (9, 2, 1), (12, 3, 1), (20, 4, 1), (40, 5, 1)]     # (n, t, marks)


def _sequences(n, rng, count, length):
    """Gleichverteilte Folgen und bösartige: der Kopf oft, ein einzelner Gefangener oft, Gefangene nur in einer Hälfte."""
    for _ in range(count):
        yield rng.integers(0, n, size=length)
    for _ in range(count):
        w = np.ones(n)
        w[0] = 12.0
        yield rng.choice(n, size=length, p=w / w.sum())
    for _ in range(count):
        w = np.ones(n)
        w[int(rng.integers(0, n))] = 30.0
        yield rng.choice(n, size=length, p=w / w.sum())
    for _ in range(count):
        half = max(2, n // 2)
        yield rng.integers(0, half, size=length)


def _step_all(p, seq, init):
    """Alle Stände nach jedem Tag (eigene Schleife über apply_visit): liefert Liste von (Tag, tok, tal, Schalter, Phase) und das Ende."""
    tok, tal = PR.initial_counts(p)
    sched = PR.schedule(p.n, p.t)
    light = init
    for day, who in enumerate(seq, start=1):
        phase, _, _ = PR.phase_info(sched, day)
        tok[who], tal[who], light = PR.apply_visit(tok[who], tal[who], light, day, sched, p.reset)
        yield day, who, list(tok), list(tal), light, phase


@pytest.mark.parametrize("n,t,marks", CONFIGS)
@pytest.mark.parametrize("reset,init", [(True, False), (True, True), (False, False)])
def test_conservation_and_sign_invariants_hold_on_every_day(n, t, marks, reset, init):
    p = PR.Protocol(n, t, marks=marks, reset=reset)
    rng = np.random.default_rng(5)
    t_eff = p.t_eff
    for seq in _sequences(n, rng, 2, 400):
        for day, who, tok, tal, light, phase in _step_all(p, seq, init):
            room_tok = 1 if (light and phase == PR.MARKE) else 0
            room_tal = 1 if (light and phase == PR.TALENT) else 0
            assert sum(tok) + room_tok == 0 and sum(tal) + room_tal == 0, (day, tok, tal, light, phase)
            assert all(v >= 0 for v in tok[t_eff:]), "Nicht-Zähler dürfen nie einen negativen Markenstand haben"
            assert all(v >= 0 for v in tal[1:]), "nur der Kopf darf einen negativen Talentstand haben"


def test_phantom_token_breaks_the_invariant_exactly_by_one_for_the_naive_protocol():
    """Zweig-Test: naives Protokoll, Schalter anfangs an: die Erhaltung gilt nur bis auf die eine Phantom-Marke."""
    p = PR.Protocol(6, 1)
    rng = np.random.default_rng(1)
    for seq in _sequences(6, rng, 3, 120):
        for day, who, tok, tal, light, phase in _step_all(p, seq, True):
            assert sum(tok) + (1 if light else 0) == 1


@pytest.mark.parametrize("n,t,marks", CONFIGS)
def test_safe_variants_never_declare_early_for_any_visit_sequence(n, t, marks):
    rng = np.random.default_rng(11)
    for reset, init in ((True, True), (True, False), (False, False)):
        p = PR.Protocol(n, t, marks=marks, reset=reset)
        for seq in _sequences(n, rng, 15, 1500):
            r = S.simulate_run(p, seq, init)
            assert not r.wrong, (n, t, marks, reset, init)
            if r.declared_day is not None:
                assert r.all_visited_day is not None and r.all_visited_day <= r.declared_day


def test_double_marks_are_safe_for_both_start_states():
    rng = np.random.default_rng(3)
    p = PR.Protocol(7, 1, marks=2)
    for seq in _sequences(7, rng, 25, 1500):
        for init in (False, True):
            assert not S.simulate_run(p, seq, init).wrong


def test_declaration_never_precedes_the_last_first_visit_in_uniform_runs():
    for n, t in ((10, 1), (30, 3), (60, 6)):
        r = S.simulate_many(PR.Protocol(n, t), 60, seed=4, init_light=False)
        assert (r.days >= r.all_visited_day).all() and (r.all_visited_day > 0).all()


def test_the_naive_protocol_does_err_on_adversarial_sequences():
    """Zweig-Test: ohne Rücksetzung gibt es bei Schalter anfangs an Folgen mit falscher Meldung (sonst prüften die Sicherheitstests nichts)."""
    p = PR.Protocol(5, 1)
    rng = np.random.default_rng(2)
    assert any(S.simulate_run(p, seq, True).wrong for seq in _sequences(5, rng, 40, 300))


def test_relabeling_non_counters_does_not_change_the_day():
    """Die Nicht-Zähler sind austauschbar: vertauscht man ihre Nummern in der Besuchsfolge, ändert sich der Meldetag nicht."""
    rng = np.random.default_rng(9)
    for n, t in ((10, 1), (20, 4)):
        p = PR.Protocol(n, t)
        t_eff = p.t_eff
        for seq in _sequences(n, rng, 3, 3000):
            perm = np.arange(n)
            perm[t_eff:] = rng.permutation(np.arange(t_eff, n))
            assert S.simulate_run(p, seq, False).declared_day == S.simulate_run(p, perm[seq], False).declared_day
