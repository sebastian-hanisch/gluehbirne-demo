"""Regeln der Zähler-Protokolle (Marken und Talente), jede Regel eine eigene reine Funktion (DEMO-PLAYBOOK §1b).

Modell. Jeder Gefangene führt einen ganzzahligen Stand `tok` (Marken) und `tal` (Talente). Der Schalter trägt je nach Phase eine Marke oder ein Talent (an) oder nichts (aus).
Die Summe aller Stände plus der Inhalt des Raums ist erhaltene Größe: jeder Schritt gibt einem Gefangenen genau so viel, wie er dem Raum nimmt. Nur Zähler (Anfangsstand
negativ) können einen negativen Stand haben. Der Kopf-Zähler (Gefangener 0) meldet, wenn sein Stand an Marken und Talenten null ist; dann sind, wegen der Erhaltung und weil
alle anderen Stände nie negativ sind, alle Stände null: jeder Gefangene hat seine Marke einmal im Raum abgegeben und war damit im Raum.

Phasen (nur bei mehr als einem Zähler): Marken-, Talentphase, danach abwechselnd. In einer Markenphase bedeutet „an“: eine Marke liegt im Raum, in einer Talentphase: ein Talent.
Am ersten Tag einer neuen Phase sammelt der Besucher einen liegengebliebenen Rest der Vorphase ein (Erhaltung), bevor er nach den Regeln der neuen Phase handelt.
Die Tagesnummer muss dafür allen bekannt sein."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

import glb_constants as C

MARKE, TALENT = 0, 1


@dataclass(frozen=True)
class Protocol:
    n: int                 # Zahl der Gefangenen
    t: int = 1             # Zahl der Zähler (wirksam: effective_t)
    marks: int = 1         # Marken je Nicht-Zähler (1 normal, 2 doppelt; nur mit t = 1)
    reset: bool = False    # Tag 1: der erste Besucher behandelt den Schalter als aus und lässt ihn nach Regel zurück

    def __post_init__(self):
        if self.n < 2:
            raise ValueError("mindestens zwei Gefangene")
        if self.marks not in (1, 2):
            raise ValueError("marks muss 1 oder 2 sein")
        if self.marks == 2 and effective_t(self.n, self.t) != 1:
            raise ValueError("doppelte Marken gibt es nur mit einem Zähler")

    @property
    def t_eff(self) -> int:
        return effective_t(self.n, self.t)


@dataclass(frozen=True)
class Schedule:
    first_mark: int        # Länge der ersten Markenphase (Tage)
    first_talent: int      # Länge der ersten Talentphase
    recovery: int          # Länge jeder weiteren Phase (abwechselnd Marke, Talent)


def harmonic(m: int) -> float:
    return math.fsum(1.0 / k for k in range(1, m + 1))


def effective_t(n: int, t: int) -> int:
    """Zahl der Zähler: höchstens n // 2 (jeder Zähler soll mindestens eine Marke sammeln), mindestens 1."""
    return max(1, min(int(t), n // 2))


def goals(n: int, t: int) -> list[int]:
    """Marken, die jeder Zähler einsammeln soll: n - t Marken verteilt auf t Zähler, die ersten bekommen den Rest."""
    t = effective_t(n, t)
    base, rest = divmod(n - t, t)
    return [base + (1 if j < rest else 0) for j in range(t)]


def initial_counts(p: Protocol) -> tuple[list[int], list[int]]:
    """Anfangsstände (Marken, Talente) aller Gefangenen. Gefangener 0 ist der Kopf-Zähler.

    Ein Zähler: Gefangener 0 sammelt n - 1 Marken (marks = 2: 2 (n - 1)). Mit t Zählern sind die Gefangenen 0 bis t - 1 Zähler mit Ziel g_j; die Zähler 1 bis t - 1 halten je ein Talent,
    der Kopf-Zähler sammelt t - 1 Talente."""
    t = p.t_eff
    tok = [p.marks] * p.n
    tal = [0] * p.n
    if t == 1:
        tok[0] = -p.marks * (p.n - 1)
        return tok, tal
    for j, g in enumerate(goals(p.n, t)):
        tok[j] = -g
        tal[j] = 1 if j > 0 else -(t - 1)
    return tok, tal


def schedule(n: int, t: int) -> Schedule | None:
    """Phasenlängen; bei einem Zähler gibt es keine Phasen (None).

    Erwartung der Markenphase: E_M = n (n - t) / t + n H(n - t) Tage (jede der n - t Marken wartet im Mittel n / t Tage auf einen Zähler, dazu das Warten auf einen Marken-
    Halter); der Talentphase: E_T = n (t - 1) + n H(t - 1). Die Faktoren stehen in glb_constants."""
    t = effective_t(n, t)
    if t == 1:
        return None
    e_mark = n * (n - t) / t + n * harmonic(n - t)
    e_talent = n * (t - 1) + n * harmonic(t - 1)
    return Schedule(max(1, math.ceil(C.PHASE_A * e_mark)), max(1, math.ceil(C.PHASE_B * e_talent)), max(1, math.ceil(C.PHASE_R * n)))


def phase_info(sched: Schedule | None, day: int) -> tuple[int, bool, int | None]:
    """(Phase an diesem Tag, erster Tag der Phase, Vorphase). Tag 1 ist der erste Tag; ohne Phasenplan ist es immer eine Markenphase."""
    if sched is None:
        return MARKE, day == 1, None
    a, b, r = sched.first_mark, sched.first_talent, sched.recovery
    if day <= a:
        return MARKE, day == 1, None
    if day <= a + b:
        return TALENT, day == a + 1, MARKE
    k, off = divmod(day - a - b - 1, r)
    phase = MARKE if k % 2 == 0 else TALENT
    return phase, off == 0, 1 - phase


def effective_light(observed: bool, day: int, reset: bool) -> bool:
    """Was der Besucher als Zustand des Schalters ansieht: am ersten Tag mit Rücksetzung „aus“, sonst das Gesehene."""
    return False if (day == 1 and reset) else observed


def collect_leftover(tok: int, tal: int, light: bool, phase_start: bool, prev: int | None, day: int) -> tuple[int, int, bool]:
    """Erster Tag einer neuen Phase: liegt noch etwas von der Vorphase im Raum (Schalter an), nimmt es der Besucher an sich."""
    if phase_start and day > 1 and light and prev is not None:
        if prev == MARKE:
            tok += 1
        else:
            tal += 1
        light = False
    return tok, tal, light


def mark_rule(tok: int, light: bool) -> tuple[int, bool]:
    """Markenphase: ein Zähler mit offenem Ziel (Stand < 0) nimmt eine Marke aus dem Raum (Schalter an → aus); ein Halter (Stand > 0) legt eine ab (aus → an)."""
    if light and tok < 0:
        return tok + 1, False
    if (not light) and tok > 0:
        return tok - 1, True
    return tok, light


def talent_rule(tok: int, tal: int, light: bool) -> tuple[int, bool]:
    """Talentphase: der Kopf (Talentstand < 0) nimmt ein Talent; ein Zähler, dessen Marken-Ziel erreicht ist (Stand 0), legt sein Talent ab."""
    if light and tal < 0:
        return tal + 1, False
    if (not light) and tal > 0 and tok == 0:
        return tal - 1, True
    return tal, light


def apply_visit(tok: int, tal: int, observed: bool, day: int, sched: Schedule | None, reset: bool) -> tuple[int, int, bool]:
    """Ein Besuch: (Marken, Talente, Schalter nachher) aus (Marken, Talente, gesehener Schalter, Tag)."""
    light = effective_light(observed, day, reset)
    phase, start, prev = phase_info(sched, day)
    tok, tal, light = collect_leftover(tok, tal, light, start, prev, day)
    if phase == MARKE:
        tok, light = mark_rule(tok, light)
    else:
        tal, light = talent_rule(tok, tal, light)
    return tok, tal, light


def declares(who: int, tok: int, tal: int) -> bool:
    """Meldung: der Kopf-Zähler (Gefangener 0) ist im Raum und hat Stand null an Marken und Talenten."""
    return who == 0 and tok == 0 and tal == 0


def expected_standard(n: int) -> float:
    """Bekannte geschlossene Formel für einen Zähler (Schalter anfangs aus): n (n - 1) + n H(n - 1) Tage."""
    return n * (n - 1) + n * harmonic(n - 1)


def expected_standard_exact(n: int) -> Fraction:
    h = sum(Fraction(1, k) for k in range(1, n))
    return n * (n - 1) + n * h


def expected_all_visited(n: int) -> float:
    """Sammelproblem: bis jeder Gefangene mindestens einmal im Raum war, vergehen im Mittel n H(n) Tage (unabhängig vom Protokoll)."""
    return n * harmonic(n)
