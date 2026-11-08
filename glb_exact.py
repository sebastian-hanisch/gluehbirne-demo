"""Exakte Rechnung für kleine n: Erwartungswert und Fehlerwahrscheinlichkeit über alle Zustände, und die Suche nach dem kürzesten Gegenbeispiel.

Die Regeln kommen aus glb_protocol (dieselben wie in der Simulation); neu ist nur die Zustandsverwaltung. Gleiche Gefangene werden zusammengefasst: Zustand =
(Schalter, Stand des Kopf-Zählers, geordnete Liste der Stände der übrigen), ein Besucher aus einer Klasse gleicher Gefangener hat die Wahrscheinlichkeit Vielfachheit / n.
Die Rechnung ist nur für kleine n gedacht (C.EXACT_N_MAX)."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction

import numpy as np

import glb_protocol as PR


def _initial(p: PR.Protocol, init_light: bool, track_visited: bool):
    tok, tal = PR.initial_counts(p)
    others = tuple(sorted((tok[i], tal[i], False) for i in range(1, p.n)))
    return (bool(init_light), (tok[0], tal[0]), others)


def _successors(p: PR.Protocol, state, day: int, sched, track_visited: bool):
    """Alle Folgezustände eines Tages: Liste (Wahrscheinlichkeit, Folgezustand oder None bei Meldung, falsche Meldung?)."""
    light, head, others = state
    out = []
    # Besuch des Kopf-Zählers
    tok, tal, new_light = PR.apply_visit(head[0], head[1], light, day, sched, p.reset)
    if PR.declares(0, tok, tal):
        wrong = any(not v for (_, _, v) in others) if track_visited else False
        out.append((Fraction(1, p.n), None, wrong))
    else:
        out.append((Fraction(1, p.n), (new_light, (tok, tal), others), False))
    # Besuch eines übrigen Gefangenen (Klassen gleicher Stände)
    for cls, mult in Counter(others).items():
        tk, tl, v = cls
        tk2, tl2, new_light = PR.apply_visit(tk, tl, light, day, sched, p.reset)
        rest = list(others)
        rest.remove(cls)
        rest.append((tk2, tl2, True if track_visited else False))
        out.append((Fraction(mult, p.n), (new_light, head, tuple(sorted(rest))), False))
    return out


def propagate(p: PR.Protocol, init_light: bool, track_visited: bool = True, eps: float = 1e-13, max_days: int = 200_000) -> dict:
    """Verteilung des Meldetags durch Weiterschieben der Wahrscheinlichkeiten Tag für Tag (alle Phasen), Gleitkomma.

    Liefert {"mean": E[T], "wrong": P(falsche Meldung), "left": noch nicht gemeldete Wahrscheinlichkeit am Ende, "days": letzter Tag}."""
    sched = PR.schedule(p.n, p.t)
    dist = {_initial(p, init_light, track_visited): 1.0}
    mean = 0.0
    wrong = 0.0
    left = 1.0
    day = 0
    cache: dict = {}
    while left > eps and day < max_days:
        day += 1
        # Ab dem Tag nach der letzten Besonderheit hängt der Schritt nicht mehr vom Tag ab, wenn es keine Phasen gibt (Zwischenspeicher je Tagesart)
        key_day = day if (sched is not None or day == 1) else 2
        nxt: dict = {}
        for state, prob in dist.items():
            ck = (key_day, state)
            succ = cache.get(ck)
            if succ is None:
                succ = _successors(p, state, key_day, sched, track_visited)
                cache[ck] = succ
            for q, new_state, was_wrong in succ:
                w = prob * float(q)
                if new_state is None:
                    mean += day * w
                    left -= w
                    if was_wrong:
                        wrong += w
                else:
                    nxt[new_state] = nxt.get(new_state, 0.0) + w
        dist = nxt
        if sched is not None and len(cache) > 400_000:
            cache.clear()
    return {"mean": mean, "wrong": wrong, "left": left, "days": day}


def expected_days_linear(p: PR.Protocol, init_light: bool) -> Fraction:
    """Exakter Erwartungswert (Bruch) für ein Protokoll ohne Phasen (ein Zähler): Gleichungssystem E(s) = 1 + Σ P(s → s') E(s'), gelöst durch Gauß mit Brüchen.

    Der erste Tag wird einzeln gerechnet (nur er kennt die Rücksetzung); danach ist der Schritt tagesunabhängig."""
    if PR.schedule(p.n, p.t) is not None:
        raise ValueError("nur ohne Phasen (ein Zähler)")
    start = _initial(p, init_light, False)
    first = _successors(p, start, 1, None, False)
    # Zustände aufzählen
    index: dict = {}
    todo = []
    for _, s, _ in first:
        if s is not None and s not in index:
            index[s] = len(index)
            todo.append(s)
    trans: dict = {}
    while todo:
        s = todo.pop()
        succ = _successors(p, s, 2, None, False)
        trans[s] = succ
        for _, s2, _ in succ:
            if s2 is not None and s2 not in index:
                index[s2] = len(index)
                todo.append(s2)
    m = len(index)
    a = [[Fraction(0)] * (m + 1) for _ in range(m)]
    for s, i in index.items():
        a[i][i] += 1
        a[i][m] = Fraction(1)
        for q, s2, _ in trans[s]:
            if s2 is not None:
                a[i][index[s2]] -= q
    for col in range(m):                                   # Gauß-Jordan mit Brüchen
        piv = next(r for r in range(col, m) if a[r][col] != 0)
        a[col], a[piv] = a[piv], a[col]
        inv = 1 / a[col][col]
        a[col] = [x * inv for x in a[col]]
        for r in range(m):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [x - f * y for x, y in zip(a[r], a[col])]
    e = {s: a[i][m] for s, i in index.items()}
    total = Fraction(1)
    for q, s, _ in first:
        if s is not None:
            total += q * e[s]
    return total


def wrong_probability_linear(p: PR.Protocol, init_light: bool) -> float:
    """Wahrscheinlichkeit einer falschen Meldung (ein Zähler) aus dem Gleichungssystem der Absorptionswahrscheinlichkeiten, Gleitkomma (numpy)."""
    if PR.schedule(p.n, p.t) is not None:
        raise ValueError("nur ohne Phasen (ein Zähler)")
    start = _initial(p, init_light, True)
    first = _successors(p, start, 1, None, True)
    index: dict = {}
    todo = []
    for _, s, _ in first:
        if s is not None and s not in index:
            index[s] = len(index)
            todo.append(s)
    trans: dict = {}
    while todo:
        s = todo.pop()
        succ = _successors(p, s, 2, None, True)
        trans[s] = succ
        for _, s2, _ in succ:
            if s2 is not None and s2 not in index:
                index[s2] = len(index)
                todo.append(s2)
    m = len(index)
    a = np.eye(m)
    b = np.zeros(m)
    for s, i in index.items():
        for q, s2, was_wrong in trans[s]:
            if s2 is None:
                b[i] += float(q) * (1.0 if was_wrong else 0.0)
            else:
                a[i, index[s2]] -= float(q)
    x = np.linalg.solve(a, b) if m else np.zeros(0)
    total = 0.0
    for q, s, was_wrong in first:
        total += float(q) * ((1.0 if was_wrong else 0.0) if s is None else x[index[s]])
    return total


def day_key(sched: PR.Schedule | None, day: int) -> int:
    """Tage mit gleichem Verhalten bekommen denselben Schlüssel: Tag 1 (Rücksetzung), dann bei einem Zähler alle Tage ab 2 gleich, mit Phasen ab dem Ende der beiden ersten Phasen periodisch."""
    if sched is None:
        return 1 if day == 1 else 2
    head = sched.first_mark + sched.first_talent
    if day <= head:
        return day
    return head + 1 + (day - head - 1) % (2 * sched.recovery)


def shortest_violation(p: PR.Protocol, init_light: bool, max_days: int = 100_000, max_states: int = 400_000):
    """Breitensuche über ALLE Besuchsfolgen (auch bösartige): die kürzeste Folge, nach der eine falsche Meldung fällt, sonst None.

    Zustand = (Schalter, Stände und Besuchtflags aller Gefangenen) zusammen mit der Tagesart (day_key). Ein Zustand mit gleicher Tagesart wird nur einmal erweitert: die Suche endet, wenn
    nichts Neues mehr erreichbar ist, und beweist dann für JEDE Besuchsfolge beliebiger Länge, dass keine falsche Meldung fällt (`complete`).
    Rückgabe bei Fund: {"found": True, "days", "visitors", "unvisited"}; sonst {"found": False, "complete", "states": Zahl erreichter Zustände, "layers": Zahl der Tage}."""
    sched = PR.schedule(p.n, p.t)
    tok, tal = PR.initial_counts(p)
    start = (bool(init_light), tuple((tok[i], tal[i], False) for i in range(p.n)))
    parent: dict = {(day_key(sched, 1), start): None}
    frontier = [(1, start)]
    day = 0
    while frontier and day < max_days:
        day += 1
        nxt = []
        for d_idx, state in frontier:
            light, pris = state
            key_here = (day_key(sched, day), state)
            for who in range(p.n):
                tk, tl, _ = pris[who]
                tk2, tl2, light2 = PR.apply_visit(tk, tl, light, day, sched, p.reset)
                new_pris = list(pris)
                new_pris[who] = (tk2, tl2, True)
                if PR.declares(who, tk2, tl2):
                    if not all(v for (_, _, v) in new_pris):
                        seq = [who]
                        cur = key_here
                        while parent[cur] is not None:
                            prev, prev_who = parent[cur]
                            seq.append(prev_who)
                            cur = prev
                        seq.reverse()
                        return {"found": True, "days": day, "visitors": seq, "unvisited": [i for i, (_, _, v) in enumerate(new_pris) if not v]}
                    continue
                s2 = (light2, tuple(new_pris))
                key2 = (day_key(sched, day + 1), s2)
                if key2 not in parent:
                    parent[key2] = (key_here, who)
                    nxt.append((day + 1, s2))
        frontier = nxt
        if len(parent) > max_states:
            return {"found": False, "complete": False, "states": len(parent), "layers": day}
    return {"found": False, "complete": not frontier, "states": len(parent), "layers": day}
