"""Simulation: ein Lauf Tag für Tag (skalar, für die Zeitachse und als Vergleichsfassung) und viele Läufe nebeneinander (numpy, Achse 0 = Läufe).

Beide Fassungen wenden dieselben Regeln aus glb_protocol an und lesen dieselben Besucher: `visitors_block(seed, chunk, runs, n)` liefert die Besucher von CHUNK Tagen
für alle Läufe, `visitor_sequence` schneidet daraus die Folge eines Laufs. Gleiche Besucherfolge, gleiches Ergebnis: das prüft tests/test_simulation.py."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import glb_constants as C
import glb_protocol as PR
from glb_rng import uniform_block


def day_cap(n: int) -> int:
    return C.CAP_FACTOR * n * n + C.CAP_BASE


def chunk_seed(seed: int, chunk: int) -> int:
    return (int(seed) << 24) + int(chunk)


def visitors_block(seed: int, chunk: int, runs: int, n: int) -> np.ndarray:
    """Besucher von CHUNK aufeinanderfolgenden Tagen für `runs` Läufe, Form (CHUNK, runs), Werte 0 bis n - 1 gleichverteilt."""
    u = uniform_block(chunk_seed(seed, chunk), C.CHUNK * runs).reshape(C.CHUNK, runs)
    return np.minimum((u * n).astype(np.int64), n - 1)


def visitor_sequence(seed: int, run: int, runs: int, n: int, days: int) -> np.ndarray:
    """Die Besucher der ersten `days` Tage von Lauf `run` (identisch mit den Spalten der Blöcke der Vielfach-Simulation)."""
    out = []
    for chunk in range((days + C.CHUNK - 1) // C.CHUNK):
        out.append(visitors_block(seed, chunk, runs, n)[:, run])
    return np.concatenate(out)[:days] if out else np.zeros(0, dtype=np.int64)


@dataclass
class RunResult:
    declared_day: int | None        # Tag der Meldung, None: bis zur Tagesgrenze keine Meldung
    wrong: bool                     # gemeldet, obwohl jemand nie im Raum war
    unvisited: int                  # so viele Gefangene waren bei der Meldung nie im Raum
    seen_on: int                    # an so vielen Tagen sah der Besucher den Schalter an (bis zur Meldung)
    all_visited_day: int | None     # Tag, an dem der letzte Gefangene zum ersten Mal im Raum war
    trace: dict = field(default_factory=dict)


def simulate_run(p: PR.Protocol, visitors, init_light: bool, cap: int | None = None, record: bool = False) -> RunResult:
    """Ein Lauf Tag für Tag mit den gegebenen Besuchern (Folge von Gefangenen-Nummern). Die Meldung beendet den Lauf."""
    tok, tal = PR.initial_counts(p)
    sched = PR.schedule(p.n, p.t)
    visited = [False] * p.n
    n_visited = 0
    light = bool(init_light)
    seen_on = 0
    all_visited_day = None
    cap = len(visitors) if cap is None else min(cap, len(visitors))
    goal_left = -sum(min(v, 0) for v in tok)       # Marken, die die Zähler noch einsammeln müssen
    talent_left = -sum(min(v, 0) for v in tal)
    trace = {k: [] for k in ("who", "saw", "light", "head_tok", "head_tal", "visited", "goal_left", "talent_left")} if record else {}
    for day in range(1, cap + 1):
        who = int(visitors[day - 1])
        if not visited[who]:
            visited[who] = True
            n_visited += 1
            if n_visited == p.n:
                all_visited_day = day
        saw = light
        seen_on += 1 if saw else 0
        old_tok, old_tal = tok[who], tal[who]
        tok[who], tal[who], light = PR.apply_visit(old_tok, old_tal, saw, day, sched, p.reset)
        goal_left -= min(tok[who], 0) - min(old_tok, 0)
        talent_left -= min(tal[who], 0) - min(old_tal, 0)
        done = PR.declares(who, tok[who], tal[who])
        if record:
            trace["who"].append(who)
            trace["saw"].append(saw)
            trace["light"].append(light)
            trace["head_tok"].append(tok[0])
            trace["head_tal"].append(tal[0])
            trace["visited"].append(n_visited)
            trace["goal_left"].append(goal_left)
            trace["talent_left"].append(talent_left)
        if done:
            return RunResult(day, n_visited < p.n, p.n - n_visited, seen_on, all_visited_day, trace)
    return RunResult(None, False, p.n - n_visited, seen_on, all_visited_day, trace)


@dataclass
class ManyResult:
    days: np.ndarray               # Meldetag je Lauf, -1: keine Meldung bis zur Tagesgrenze
    wrong: np.ndarray              # bool: falsche Meldung
    unvisited: np.ndarray          # Zahl der nie Besuchten bei der Meldung
    seen_on: np.ndarray            # Tage mit gesehenem Schalter „an“ bis zur Meldung
    all_visited_day: np.ndarray    # Tag des letzten Erstbesuchs (-1: nie)


def simulate_many(p: PR.Protocol, runs: int, seed: int, init_light: bool, cap: int | None = None, sched="auto") -> ManyResult:
    """`runs` Läufe nebeneinander. Je Tag ein Besucher je Lauf; abgeschlossene Läufe ändern ihre Ergebnisse nicht mehr.

    `sched`: "auto" nimmt den Phasenplan des Protokolls (PR.schedule); ein Schedule (oder None) ersetzt ihn, nur für die Abstimmung der Phasenlängen."""
    n = p.n
    cap = day_cap(n) if cap is None else cap
    sched = PR.schedule(n, p.t) if isinstance(sched, str) else sched
    tok0, tal0 = PR.initial_counts(p)
    tok = np.tile(np.array(tok0, dtype=np.int32), (runs, 1)).ravel()
    tal = np.tile(np.array(tal0, dtype=np.int32), (runs, 1)).ravel()
    visited = np.zeros(runs * n, dtype=bool)
    n_visited = np.zeros(runs, dtype=np.int32)
    light = np.full(runs, bool(init_light))
    rows = np.arange(runs, dtype=np.int64)
    base = rows * n
    days = np.full(runs, -1, dtype=np.int64)
    wrong = np.zeros(runs, dtype=bool)
    unvisited = np.zeros(runs, dtype=np.int32)
    seen_on = np.zeros(runs, dtype=np.int64)
    all_visited = np.full(runs, -1, dtype=np.int64)
    done = np.zeros(runs, dtype=bool)
    block = None
    for day in range(1, cap + 1):
        off = (day - 1) % C.CHUNK
        if off == 0:
            block = visitors_block(seed, (day - 1) // C.CHUNK, runs, n)
        who = block[off]
        idx = base + who
        fresh = ~visited[idx]
        visited[idx] = True
        n_visited += fresh
        newly_all = (n_visited == n) & (all_visited < 0)
        all_visited[newly_all] = day
        saw = light.copy()
        active = ~done
        seen_on += (saw & active)
        s = np.zeros_like(saw) if (day == 1 and p.reset) else saw
        phase, start, prev = PR.phase_info(sched, day)
        tk = tok[idx]
        tl = tal[idx]
        if start and day > 1 and prev is not None:
            pick = s
            if prev == PR.MARKE:
                tk = tk + pick
            else:
                tl = tl + pick
            s = s & ~pick
        if phase == PR.MARKE:
            take = s & (tk < 0)
            drop = (~s) & (tk > 0)
            tk = tk + take - drop
            s = np.where(take, False, np.where(drop, True, s))
        else:
            take = s & (tl < 0)
            drop = (~s) & (tl > 0) & (tk == 0)
            tl = tl + take - drop
            s = np.where(take, False, np.where(drop, True, s))
        tok[idx] = tk
        tal[idx] = tl
        light = s
        fin = active & (who == 0) & (tk == 0) & (tl == 0)
        if fin.any():
            days[fin] = day
            unvisited[fin] = n - n_visited[fin]
            wrong[fin] = n_visited[fin] < n
            done |= fin
            if done.all():
                break
    return ManyResult(days, wrong, unvisited, seen_on, all_visited)


def summary(r: ManyResult) -> dict:
    """Kennzahlen über die Läufe: Mittel der Meldetage (nur Läufe mit Meldung), Standardfehler, Anteil falscher Meldungen und ohne Meldung."""
    ok = r.days >= 0
    runs = len(r.days)
    d = r.days[ok].astype(float)
    mean = float(d.mean()) if d.size else float("nan")
    se = float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else float("nan")
    return {
        "runs": runs,
        "finished": int(ok.sum()),
        "mean_days": mean,
        "se": se,
        "median_days": float(np.median(d)) if d.size else float("nan"),
        "max_days": int(d.max()) if d.size else -1,
        "wrong_share": float(r.wrong.sum() / runs),
        "mean_all_visited": float(r.all_visited_day[r.all_visited_day >= 0].mean()) if (r.all_visited_day >= 0).any() else float("nan"),
        "on_share": float(r.seen_on[ok].sum() / d.sum()) if d.size and d.sum() > 0 else float("nan"),
    }
