"""Messreihen für README und App-Texte (feste Zufalls-Seeds, deterministisch). `tools/make_measurements.py` schreibt sie nach data/measurements.json; tests/test_claims.py rechnet sie neu."""

from __future__ import annotations

import glb_evaluation as V
import glb_protocol as PR
import glb_simulation as S

MEAS_SEED = 20261108
RUNS_MAIN = 1000          # Läufe für Standard und zehn Zähler bei n = 100
RUNS_GRID = 400           # Läufe je Wert von t
RUNS_SCALE = 200          # Läufe je Größe


def measure_main() -> dict:
    """n = 100, Schalter anfangs aus: ein Zähler und zehn Zähler, je 1000 Läufe (derselbe Zufalls-Seed, also dieselben Besucherfolgen)."""
    out = {}
    for t in (1, 10):
        r = S.simulate_many(PR.Protocol(100, t), RUNS_MAIN, MEAS_SEED, False)
        sm = S.summary(r)
        out[f"t{t}"] = {"mean": sm["mean_days"], "se": sm["se"], "median": sm["median_days"], "max": sm["max_days"], "finished": sm["finished"], "wrong_share": sm["wrong_share"],
                        "on_share": sm["on_share"], "all_visited": sm["mean_all_visited"]}
    out["formula"] = PR.expected_standard(100)
    out["all_visited_formula"] = PR.expected_all_visited(100)
    out["on_share_formula"] = 100 * 99 / PR.expected_standard(100)
    out["factor"] = out["t1"]["mean"] / out["t10"]["mean"]
    return out


def measure_grid() -> list[dict]:
    return V.experiment_counters(100, RUNS_GRID, MEAS_SEED)


def measure_scale() -> list[dict]:
    return V.experiment_scaling(RUNS_SCALE, MEAS_SEED)


def measure_all() -> dict:
    return {"main": measure_main(), "grid": measure_grid(), "scale": measure_scale()}
