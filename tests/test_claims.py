"""Jede Zahl der README wird hier nachgerechnet (DEMO-PLAYBOOK §4, §11a): die Messreihen aus glb_measure (feste Seeds), die exakten Werte aus glb_exact, die Formeln aus glb_protocol.

Zahlen aus der Literatur (Majerech: 3850, 3500, 3390) stehen als Konstanten unten und sind nur an den Wortlaut der README gebunden; sie sind keine Messung dieser Demo."""

import json
import math
import re
from pathlib import Path

import pytest

import glb_evaluation as V
import glb_exact as X
import glb_measure as M
import glb_protocol as PR
import glb_simulation as S

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
VORMESSUNG = ROOT.parent / "teamraetsel-planung" / "vormessung" / "out_e3b_gluehbirne_protokolle.txt"
LITERATURE = {"published": 3850, "forum": 3500, "best": 3390}      # Majerech, Zusammenfassung (Manuskript selbst gelesen am 2026-11-08)


def has(text):
    assert text in README, f"README enthält nicht: {text!r}"


@pytest.fixture(scope="module")
def meas():
    return M.measure_all()


def test_standard_formula_and_years():
    f = PR.expected_standard(100)
    has(f"{V.days_text(f)} Tage")
    has(f"rund {V.years(f)} Jahre")
    assert V.days_text(f) == "10.417,7" and V.years(f) == "28,5"


def test_standard_simulation_text_matches_the_measurement(meas):
    t1 = meas["main"]["t1"]
    has(f"{V.days_text(t1['mean'])} ± {V.de(t1['se'], 1)} Tage (1000 Läufe")
    assert M.RUNS_MAIN == 1000 and t1["finished"] == 1000 and t1["wrong_share"] == 0
    assert abs(t1["mean"] - PR.expected_standard(100)) < 4 * t1["se"]


def test_exact_fractions_listed_in_the_readme():
    has("4, 21/2, 58/3, 365/12, 437/10")
    fractions = [str(PR.expected_standard_exact(n)) for n in range(2, 7)]
    assert fractions == ["4", "21/2", "58/3", "365/12", "437/10"]
    for n in range(2, 7):
        assert X.expected_days_linear(PR.Protocol(n, 1), False) == PR.expected_standard_exact(n)
    has("für n = 2 bis 10")


def test_on_share(meas):
    t1 = meas["main"]["t1"]
    formula = 100 * 99 / PR.expected_standard(100)
    assert V.pct(t1["on_share"]) == "95,0 %" and V.pct(formula) == "95,0 %"
    has("An **95,0 %** der Tage")
    has(f"Simulation {V.pct(t1['on_share'])}, Formel n(n−1) / E[T] = {V.pct(formula)}")


def test_collector_time_and_factors(meas):
    c = PR.expected_all_visited(100)
    assert V.days_text(c) == "518,7"
    has(f"n·H(n) = **{V.days_text(c)} Tagen**")
    has(f"**{V.de(PR.expected_standard(100) / c, 1)}-fache**")
    has(f"zehn Zähler das **{V.de(meas['main']['t10']['mean'] / c, 1)}-fache**")
    assert V.de(PR.expected_standard(100) / c, 1) == "20,1" and V.de(meas["main"]["t10"]["mean"] / c, 1) == "7,0"


def test_ten_counters(meas):
    t10 = meas["main"]["t10"]
    has(f"**{V.days_text(t10['mean'])} ± {V.de(t10['se'], 1)} Tage**")
    f = PR.expected_standard(100) / t10["mean"]
    has(f"**{V.de(f, 2)} mal so schnell**")
    has(f"({V.days_text(PR.expected_standard(100))} / {V.days_text(t10['mean'])})")
    has(f"an {V.pct(t10['on_share'])} der Tage den Schalter an")
    assert t10["finished"] == 1000 and t10["wrong_share"] == 0


def test_counter_grid(meas):
    rows = meas["grid"]
    assert [r["t"] for r in rows] == list(V.C.EXP_T_GRID)
    best = min(rows, key=lambda r: r["mean"])
    one = rows[0]
    assert best["t"] == 10
    has(f"bestes t = **{best['t']}** mit {V.days_text(best['mean'])} Tagen gegen {V.days_text(one['mean'])} bei t = 1")
    near = [r["t"] for r in rows if r["mean"] <= 1.10 * best["mean"]]
    assert near == [8, 10, 12]
    has(f"**{len(near)} von {len(rows)}** Werten (t = 8, 10, 12)")
    t20 = next(r for r in rows if r["t"] == 20)
    has(f"bei t = 20 sind es {V.days_text(t20['mean'])} Tage")
    assert all(r["wrong"] == 0 and r["finished"] == M.RUNS_GRID for r in rows)
    has("400 Läufe je Wert")


def test_scaling(meas):
    rows = {r["n"]: r for r in meas["scale"]}
    assert list(rows) == [10, 20, 30, 50, 100] and [r["t"] for r in rows.values()] == [3, 4, 5, 7, 10]
    assert rows[10]["multi"] > rows[10]["single"], "bei n = 10 ist ein Zähler schneller"
    has(f"t = 3 braucht {V.days_text(rows[10]['multi'])} Tage gegen {V.days_text(rows[10]['single'])} bei einem Zähler")
    assert rows[20]["multi"] < rows[20]["single"]
    has(f"({V.days_text(rows[20]['multi'])} gegen {V.days_text(rows[20]['single'])})")
    has(f"bei n = 100 sind es {V.days_text(rows[100]['multi'])} gegen {V.days_text(rows[100]['single'])} Tage")
    wins = sum(1 for r in rows.values() if r["multi"] < r["single"])
    has(f"**{wins} von {len(rows)}** Größen")
    assert wins == 4
    has("200 Läufe je Größe, t = ⌊√n⌋")


def test_exact_values_for_several_counters_and_their_distance_to_the_simulation():
    zmax = 0.0
    parts = []
    for n, t in ((4, 2), (5, 2), (6, 2), (6, 3)):
        p = PR.Protocol(n, t)
        exact = X.propagate(p, False, track_visited=False)["mean"]
        sm = S.summary(S.simulate_many(p, 20000, 3, False))
        zmax = max(zmax, abs(sm["mean_days"] - exact) / sm["se"])
        parts.append((n, t, exact))
    for n, t, exact in parts:
        has(f"n = {n}, t = {t}: {V.de(exact, 3)}" if (n, t) == (4, 2) else f"{V.de(exact, 3)}")
    has("20.000 Läufe (Zufalls-Seed 3)")
    assert round(zmax, 1) == 1.3, zmax
    has(f"Größter Abstand der Simulation: {V.de(zmax, 1)} Standardfehler")


def test_start_state_numbers():
    for n in range(2, 7):
        assert X.wrong_probability_linear(PR.Protocol(n, 1), True) == pytest.approx(2.0 ** -(n - 1), rel=1e-9)
        assert X.shortest_violation(PR.Protocol(n, 1), True)["days"] == 2 * n - 3
    has("1/2, 1/4, 1/8, 1/16, 1/32")
    has("2n − 3 Tage")
    for p, init in ((PR.Protocol(6, 1, reset=True), True), (PR.Protocol(6, 1, marks=2), True), (PR.Protocol(6, 1, marks=2), False)):
        r = X.shortest_violation(p, init)
        assert not r["found"] and r["complete"]
    for n, t in ((4, 2), (5, 2), (6, 2), (6, 3)):
        r = X.shortest_violation(PR.Protocol(n, t, reset=True), True, max_states=3_000_000)
        assert not r["found"] and r["complete"]
    has("(n, t) = (4, 2), (5, 2), (6, 2), (6, 3)")


def test_double_marks_cost():
    std = float(PR.expected_standard_exact(6))
    off = float(X.expected_days_linear(PR.Protocol(6, 1, marks=2), False))
    on = float(X.expected_days_linear(PR.Protocol(6, 1, marks=2), True))
    has(f"{V.de(off, 2)} Tage (Schalter anfangs aus) und {V.de(on, 2)} (an) gegen {V.de(std, 2)}")
    has(f"**{V.de(off / std, 2)}-fache** bzw. **{V.de(on / std, 2)}-fache**")
    ratios_on = [float(X.expected_days_linear(PR.Protocol(n, 1, marks=2), True) / PR.expected_standard_exact(n)) for n in range(2, 7)]
    ratios_off = [float(X.expected_days_linear(PR.Protocol(n, 1, marks=2), False) / PR.expected_standard_exact(n)) for n in range(2, 7)]
    has(f"zwischen {V.de(min(ratios_on), 2)} und {V.de(max(ratios_off), 2)}")


def test_reset_is_free_in_every_run():
    for n in range(2, 7):
        assert X.expected_days_linear(PR.Protocol(n, 1, reset=True), True) == PR.expected_standard_exact(n)
        assert X.expected_days_linear(PR.Protocol(n, 1, reset=True), False) == PR.expected_standard_exact(n)
    has("Tag für Tag gleich")


def test_literature_numbers_in_the_readme():
    has(f"über {LITERATURE['published']} Besuchen")
    has(f"um {LITERATURE['forum']}")
    has(f"unter {LITERATURE['best']}")


def test_tuning_numbers_match_the_pre_measurement_file():
    if not VORMESSUNG.exists():
        pytest.skip("Vormessung liegt nicht im Portfolio-Ordner")
    text = VORMESSUNG.read_text(encoding="utf-8")
    m = re.search(r"beste Zelle ([\d.]+) ± ([\d.]+); gewählte Faktoren \(1,5; 1,25; 3\) ([\d.]+) ± ([\d.]+)", text)
    assert m, "Zeile der Prüfung fehlt in der Vormessung"
    best, best_se, mine, mine_se = (float(x) for x in m.groups())
    has(f"bei 3.{round(mine) % 1000:03d} ± {round(mine_se)} Tagen, die beste Gitterzelle bei 3.{round(best) % 1000:03d} ± {round(best_se)}")


def test_preset_help_numbers(meas):
    h = V.C.PRESET_HELP
    t1, t10 = meas["main"]["t1"], meas["main"]["t10"]
    assert f"Formel {V.days_text(PR.expected_standard(100))} Tage, Simulation {V.days_text(t1['mean'])} ± {V.de(t1['se'], 1)} Tage (1000 Läufe" in h["Standard: 100 Gefangene, ein Zähler"]
    assert f"{V.days_text(t10['mean'])} ± {V.de(t10['se'], 1)} Tage (1000 Läufe" in h["Zehn Zähler (t = 10)"]
    assert str(PR.expected_standard_exact(4)) == "58/3" and "58/3 Tage" in h["Kleiner Fall: 4 Gefangene"]
    assert X.wrong_probability_linear(PR.Protocol(4, 1), True) == pytest.approx(1 / 8) and "1/8" in h["Schalter anfangs an, naiv"]


def test_phase_factors_named_in_the_app_are_the_constants():
    assert (V.C.PHASE_A, V.C.PHASE_B, V.C.PHASE_R) == (1.5, 1.25, 3.0)


def test_phase_factors_matter():
    """Zweig-Test: wesentlich kürzere Phasen sind bei n = 100, t = 10 langsamer (die Abstimmung ist keine Zierde)."""
    n, t = 100, 10
    good = S.summary(S.simulate_many(PR.Protocol(n, t), 150, 5, False))["mean_days"]
    short = PR.Schedule(300, 300, 30)
    bad = S.summary(S.simulate_many(PR.Protocol(n, t), 150, 5, False, sched=short))["mean_days"]
    assert bad > 1.2 * good, (good, bad)


def test_ten_counters_factor_band_over_other_seeds():
    """README: mit 20 anderen Zufalls-Seeds (je 1000 Läufe) liegt der Faktor Formel / Mittel von t = 10 zwischen 2,85 und 2,91."""
    formula = PR.expected_standard(100)
    factors = [formula / S.summary(S.simulate_many(PR.Protocol(100, 10), M.RUNS_MAIN, seed, False))["mean_days"] for seed in range(201, 221)]
    has("Mit 20 anderen Zufalls-Seeds (je 1000 Läufe) liegt dieser Faktor zwischen 2,85 und 2,91")
    assert (V.de(min(factors), 2), V.de(max(factors), 2)) == ("2,85", "2,91"), (min(factors), max(factors))


def test_counter_grid_band_over_other_seeds():
    """README: mit 10 anderen Zufalls-Seeds (je 400 Läufe) ist t = 10 in 9 Läufen und t = 12 in 1 Lauf das beste, 3 bis 5 Werte liegen innerhalb von 10 %, t = 8, 10, 12 immer darunter."""
    best_ts, near_sets = [], []
    for seed in range(201, 211):
        rows = V.experiment_counters(100, M.RUNS_GRID, seed)
        best = min(rows, key=lambda r: r["mean"])
        best_ts.append(best["t"])
        near_sets.append([r["t"] for r in rows if r["mean"] <= 1.10 * best["mean"]])
    has("mit 10 anderen Zufalls-Seeds (je 400 Läufe) ist t = 10 in 9 Läufen und t = 12 in 1 Lauf das beste, 3 bis 5 Werte liegen innerhalb von 10 %, und t = 8, 10, 12 sind immer darunter")
    assert best_ts.count(10) == 9 and best_ts.count(12) == 1
    assert min(len(s) for s in near_sets) == 3 and max(len(s) for s in near_sets) == 5
    assert all({8, 10, 12} <= set(s) for s in near_sets)


def test_threshold_between_n_12_and_n_14():
    """README: mit 10 Zufalls-Seeds und je 400 Läufen war t = ⌊√n⌋ = 3 bei n = 12 in keinem Lauf, bei n = 14 in allen 10 schneller als ein Zähler."""
    wins = {12: 0, 14: 0}
    for n in wins:
        t = math.isqrt(n)
        assert t == 3
        for seed in range(301, 311):
            one = S.summary(S.simulate_many(PR.Protocol(n, 1), 400, seed, False))["mean_days"]
            many = S.summary(S.simulate_many(PR.Protocol(n, t), 400, seed, False))["mean_days"]
            wins[n] += many < one
    has("bei n = 12 war t = ⌊√n⌋ = 3 in keinem Lauf schneller als ein Zähler, bei n = 14 in allen 10")
    assert wins == {12: 0, 14: 10}


def test_measurement_file_equals_the_recomputed_series(meas):
    data = json.loads((ROOT / "data" / "measurements.json").read_text(encoding="utf-8"))
    assert data["seeds"] == {"seed": M.MEAS_SEED, "runs_main": M.RUNS_MAIN, "runs_grid": M.RUNS_GRID, "runs_scale": M.RUNS_SCALE}
    for key in ("t1", "t10"):
        for field, value in meas["main"][key].items():
            assert data["main"][key][field] == pytest.approx(value, rel=1e-9, abs=1e-12), (key, field)
    for a, b in zip(data["grid"], meas["grid"]):
        assert a["t"] == b["t"] and a["mean"] == pytest.approx(b["mean"], rel=1e-9)
    for a, b in zip(data["scale"], meas["scale"]):
        assert a["n"] == b["n"] and a["multi"] == pytest.approx(b["multi"], rel=1e-9) and a["single"] == pytest.approx(b["single"], rel=1e-9)
    assert math.isclose(data["main"]["formula"], PR.expected_standard(100))
