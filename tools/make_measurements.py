"""Schreibt die Messreihen der README nach data/measurements.json (feste Zufalls-Seeds, deterministisch).

Aufruf aus dem Demo-Ordner:  python tools/make_measurements.py
`tests/test_claims.py` rechnet dieselben Messungen neu und vergleicht sie mit der Datei und mit den Zahlen im README."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import glb_measure as M  # noqa: E402


def main() -> None:
    data = M.measure_all()
    data["seeds"] = {"seed": M.MEAS_SEED, "runs_main": M.RUNS_MAIN, "runs_grid": M.RUNS_GRID, "runs_scale": M.RUNS_SCALE}
    out = ROOT / "data" / "measurements.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"geschrieben: {out}")


if __name__ == "__main__":
    main()
