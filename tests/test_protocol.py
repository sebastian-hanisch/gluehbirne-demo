"""Einheiten der Protokolle (glb_protocol), jede an einer von Hand gerechneten Mini-Instanz (DEMO-PLAYBOOK §1b)."""

import pytest

import glb_protocol as PR
import glb_simulation as S


def _first_declaration(p, seq, init_light=False):
    return S.simulate_run(p, seq, init_light).declared_day


def test_goals_split_n_minus_t_marks_over_t_counters():
    # n = 10, t = 3: 7 Marken, 7 = 3 + 2 + 2 (die ersten bekommen den Rest)
    assert PR.goals(10, 3) == [3, 2, 2]
    assert PR.goals(4, 2) == [1, 1]
    assert PR.goals(100, 1) == [99]
    assert sum(PR.goals(100, 10)) == 90


def test_effective_t_is_between_one_and_half_n():
    assert PR.effective_t(2, 5) == 1 and PR.effective_t(3, 5) == 1
    assert PR.effective_t(4, 5) == 2 and PR.effective_t(100, 20) == 20 and PR.effective_t(100, 99) == 50
    assert PR.effective_t(100, 0) == 1


def test_initial_counts_one_counter():
    tok, tal = PR.initial_counts(PR.Protocol(5, 1))
    assert tok == [-4, 1, 1, 1, 1] and tal == [0] * 5
    tok2, _ = PR.initial_counts(PR.Protocol(5, 1, marks=2))
    assert tok2 == [-8, 2, 2, 2, 2]


def test_initial_counts_conserve_the_sum():
    for n, t, marks in ((5, 1, 1), (5, 1, 2), (4, 2, 1), (10, 3, 1), (100, 10, 1), (100, 50, 1)):
        tok, tal = PR.initial_counts(PR.Protocol(n, t, marks=marks))
        assert sum(tok) == 0 and sum(tal) == 0, (n, t, marks)
        assert all(v >= 0 for v in tok[PR.effective_t(n, t):]), "Nicht-Zähler haben nie einen negativen Stand"


def test_initial_counts_several_counters_by_hand():
    tok, tal = PR.initial_counts(PR.Protocol(4, 2))
    assert tok == [-1, -1, 1, 1] and tal == [-1, 1, 0, 0]


def test_schedule_by_hand(hand_four_two_counters):
    sched = PR.schedule(4, 2)
    assert (sched.first_mark, sched.first_talent, sched.recovery) == hand_four_two_counters["phases"]
    assert PR.schedule(100, 1) is None


def test_phase_info_boundaries():
    sched = PR.Schedule(15, 10, 12)
    assert PR.phase_info(sched, 1) == (PR.MARKE, True, None)
    assert PR.phase_info(sched, 15) == (PR.MARKE, False, None)
    assert PR.phase_info(sched, 16) == (PR.TALENT, True, PR.MARKE)
    assert PR.phase_info(sched, 25) == (PR.TALENT, False, PR.MARKE)
    assert PR.phase_info(sched, 26) == (PR.MARKE, True, PR.TALENT)
    assert PR.phase_info(sched, 37) == (PR.MARKE, False, PR.TALENT)
    assert PR.phase_info(sched, 38) == (PR.TALENT, True, PR.MARKE)
    assert PR.phase_info(sched, 50) == (PR.MARKE, True, PR.TALENT)
    assert PR.phase_info(None, 1) == (PR.MARKE, True, None) and PR.phase_info(None, 999) == (PR.MARKE, False, None)


def test_mark_rule_cases():
    assert PR.mark_rule(-3, True) == (-2, False)   # Zähler nimmt auf
    assert PR.mark_rule(-3, False) == (-3, False)  # Zähler sieht aus: nichts
    assert PR.mark_rule(1, False) == (0, True)     # Halter legt ab
    assert PR.mark_rule(1, True) == (1, True)      # Halter sieht an: nichts
    assert PR.mark_rule(0, True) == (0, True) and PR.mark_rule(0, False) == (0, False)
    assert PR.mark_rule(2, False) == (1, True)     # nur eine Marke je Besuch


def test_talent_rule_cases():
    assert PR.talent_rule(0, -2, True) == (-1, False)   # Kopf nimmt ein Talent
    assert PR.talent_rule(0, 1, False) == (0, True)     # fertiger Zähler legt sein Talent ab
    assert PR.talent_rule(-1, 1, False) == (1, False)   # Ziel noch nicht erreicht: kein Talent
    assert PR.talent_rule(0, 1, True) == (1, True)
    assert PR.talent_rule(0, 0, False) == (0, False)


def test_collect_leftover_only_at_phase_start_and_when_on():
    assert PR.collect_leftover(1, 0, True, True, PR.MARKE, 16) == (2, 0, False)
    assert PR.collect_leftover(1, 0, True, True, PR.TALENT, 26) == (1, 1, False)
    assert PR.collect_leftover(1, 0, False, True, PR.MARKE, 16) == (1, 0, False)
    assert PR.collect_leftover(1, 0, True, False, PR.MARKE, 17) == (1, 0, True)
    assert PR.collect_leftover(1, 0, True, True, None, 1) == (1, 0, True)           # Tag 1: keine Vorphase
    assert PR.collect_leftover(1, 0, True, True, PR.MARKE, 1) == (1, 0, True)       # und Tag 1 sammelt nie ein


def test_apply_visit_boundary_hand_case():
    """Tag 16 (erste Talentphase), Gefangener 3 mit 1 Marke sieht „an“ (Rest der Markenphase): er nimmt die Marke auf (2) und schaltet aus; Talentregel danach: nichts."""
    sched = PR.Schedule(15, 10, 12)
    assert PR.apply_visit(1, 0, True, 16, sched, False) == (2, 0, False)


def test_effective_light_reset_only_on_day_one():
    assert PR.effective_light(True, 1, True) is False
    assert PR.effective_light(True, 1, False) is True
    assert PR.effective_light(True, 2, True) is True


def test_declares_requires_the_head_and_both_counts_zero():
    assert PR.declares(0, 0, 0)
    assert not PR.declares(1, 0, 0) and not PR.declares(0, -1, 0) and not PR.declares(0, 0, -1) and not PR.declares(0, 1, 0)


def test_hand_n2(hand_two):
    p = PR.Protocol(2, 1)
    for seq, day in (hand_two["short"], hand_two["long"]):
        assert _first_declaration(p, seq) == day


def test_hand_n3_open_sequence_does_not_declare(hand_three):
    assert _first_declaration(PR.Protocol(3, 1), hand_three["seq_open"]) is None


def test_hand_n4_two_counters(hand_four_two_counters):
    h = hand_four_two_counters
    p = PR.Protocol(4, 2)
    assert _first_declaration(p, h["seq"]) == h["declared"]
    assert _first_declaration(p, h["seq"][:-1]) is None, "ohne den letzten Besuch des Kopfes keine Meldung"
    # Der Kopf war an Tag 2 im Raum, hatte aber noch ein Talent offen: keine Meldung an Tag 2
    assert S.simulate_run(p, h["seq"], False).declared_day != 2


def test_closed_formulas():
    assert PR.expected_standard_exact(2) == 4 and PR.expected_standard_exact(3).numerator == 21 and PR.expected_standard_exact(3).denominator == 2
    assert PR.expected_standard(100) == pytest.approx(10417.7377517, rel=1e-9)
    assert PR.expected_all_visited(2) == pytest.approx(3.0) and PR.expected_all_visited(3) == pytest.approx(5.5)


def test_protocol_rejects_invalid_settings():
    with pytest.raises(ValueError):
        PR.Protocol(1, 1)
    with pytest.raises(ValueError):
        PR.Protocol(10, 2, marks=2)
    with pytest.raises(ValueError):
        PR.Protocol(10, 1, marks=3)
