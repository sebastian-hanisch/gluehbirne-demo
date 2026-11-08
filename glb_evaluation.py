"""Kennzahlen, Verdikt-Logik (reine Funktionen: Art und Text) und Experimente der Glühbirnen-Demo."""

from __future__ import annotations

import math
from dataclasses import dataclass

import glb_constants as C
import glb_exact as X
import glb_protocol as PR
import glb_simulation as S


# --- Zahlenformat ---------------------------------------------------------------------------------------------------------------------------
def de(x: float, nd: int = 1) -> str:
    """Zahl mit deutschem Dezimalkomma."""
    text = f"{x:.{nd}f}"
    if float(text) == 0.0:
        text = text.lstrip("-")
    return text.replace(".", ",").replace("-", "−")


def thousands(x: float) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{int(round(x)):,}".replace(",", ".")


def days_text(x: float) -> str:
    """Tage mit einer Nachkommastelle und Tausenderpunkt: 10417,7 → „10.417,7“."""
    whole, _, frac = f"{x:.1f}".partition(".")
    return f"{int(whole):,}".replace(",", ".") + "," + frac


def pct(x: float, nd: int = 1) -> str:
    return f"{de(100.0 * x, nd)} %"


def fraction_text(p: float) -> str:
    """Wahrscheinlichkeit als Bruch 1/k, wenn 1/p ganzzahlig ist (Toleranz 1e-9), sonst als Prozent."""
    if p <= 0:
        return "0"
    k = 1.0 / p
    return f"1/{round(k)}" if abs(k - round(k)) < 1e-9 * k else pct(p, 2)


def years(days: float) -> str:
    return de(days / 365.0, 1)


# --- Einstellungen und Hauptanalyse ---------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    t: int = C.DEFAULT_T
    init: str = C.DEFAULT_INIT
    reset: str = C.DEFAULT_RESET
    runs: int = C.DEFAULT_RUNS
    seed: int = C.DEFAULT_SEED

    @property
    def protocol(self) -> PR.Protocol:
        return PR.Protocol(self.n, self.t, reset=(self.reset == "ja"))

    @property
    def init_light(self) -> bool:
        return self.init == "an"


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    t_eff: int
    summary: dict
    days: tuple                  # Meldetage der Läufe mit Meldung
    trace: dict                  # Zeitachse von Lauf 0 (Tag für Tag)
    run0_day: int | None
    run0_wrong: bool
    standard_formula: float      # n (n - 1) + n H(n - 1)
    all_visited_formula: float   # n H(n)
    exact: dict | None           # exakte Rechnung über alle Zustände (nur kleine n)


def exact_small(s: Settings) -> dict | None:
    """Exakter Erwartungswert und Wahrscheinlichkeit einer falschen Meldung für n <= EXACT_N_MAX; sonst None."""
    if s.n > C.EXACT_N_MAX:
        return None
    track = s.init_light and s.reset == "nein"
    return X.propagate(s.protocol, s.init_light, track_visited=track)


def analyse(s: Settings) -> Analysis:
    p = s.protocol
    many = S.simulate_many(p, s.runs, s.seed, s.init_light)
    vis = S.visitor_sequence(s.seed, 0, s.runs, s.n, min(S.day_cap(s.n), C.TRACE_MAX_DAYS))
    run0 = S.simulate_run(p, vis, s.init_light, record=True)
    ok = many.days >= 0
    return Analysis(
        settings=s, t_eff=p.t_eff, summary=S.summary(many), days=tuple(int(d) for d in many.days[ok]),
        trace=run0.trace, run0_day=run0.declared_day, run0_wrong=run0.wrong,
        standard_formula=PR.expected_standard(s.n), all_visited_formula=PR.expected_all_visited(s.n), exact=exact_small(s),
    )


def speedup(reference: float, mean_days: float) -> float:
    """Wie viel mal so schnell wie die Referenz: Referenz / eigener Wert (größer als 1: schneller)."""
    return float("nan") if mean_days <= 0 else reference / mean_days


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------
def verdict_main(a: Analysis) -> tuple[str, str]:
    """Kernfrage: wann kann jemand sicher sagen „alle waren schon im Raum“? Der Text nennt Läufe, Mittel, Formel und, falls nötig, die falschen Meldungen."""
    sm = a.summary
    s = a.settings
    runs = sm["runs"]
    if sm["wrong_share"] > 0:
        k = round(sm["wrong_share"] * runs)
        return "error", (f"In {k} von {runs} Läufen ({pct(sm['wrong_share'])}) meldete der Kopf-Zähler zu früh: Er hatte alle Marken, obwohl jemand nie im Raum war. "
                         "Das Protokoll ist für diesen Anfangszustand des Schalters nicht sicher (Experiment „Anfangszustand“ unten).")
    if sm["finished"] < runs:
        return "warning", f"{runs - sm['finished']} von {runs} Läufen meldeten bis zur Tagesgrenze von {thousands(S.day_cap(s.n))} Tagen nicht; das Mittel gilt nur für die {sm['finished']} anderen."
    mean = sm["mean_days"]
    span = f" (rund {years(mean)} Jahre)" if mean >= 365 else ""
    head = f"Im Mittel über {runs} Läufe meldet der Kopf-Zähler nach **{days_text(mean)} Tagen**{span}, ohne je zu früh gemeldet zu haben."
    if a.t_eff == 1 and s.n >= 2 and not (s.init_light and s.reset == "nein"):
        diff = mean - a.standard_formula
        return "success", (head + f" Die bekannte Formel n·H(n−1) + n(n−1) gibt {days_text(a.standard_formula)} Tage (Abstand der Simulation: {de(diff, 1)} Tage, "
                           f"zwei Standardfehler des Mittels: {de(2 * sm['se'], 1)} Tage).")
    if a.t_eff > 1:
        f = speedup(a.standard_formula, mean)
        return "success", (head + f" Ein einzelner Zähler bräuchte nach der Formel {days_text(a.standard_formula)} Tage: {de(f, 1)} mal so lang.")
    return "info", head


def verdict_counters(rows: list[dict]) -> tuple[str, str]:
    """Experiment „Wie viele Zähler?“: bestes t, Gewinn gegen t = 1 und die Zählung der Werte nahe am Minimum (innerhalb von 10 %)."""
    one = rows[0]
    best = min(rows, key=lambda r: r["mean"])
    near = [r["t"] for r in rows if r["mean"] <= 1.10 * best["mean"]]
    if len(rows) == 1:
        return "info", "Mit dieser Zahl von Gefangenen ist nur ein Zähler möglich (t ist höchstens n // 2): es gibt nichts zu vergleichen."
    if best["t"] == 1:
        return "info", (f"Hier gewinnt der einzelne Zähler (t = 1, {days_text(one['mean'])} Tage); mehr Zähler kosten hier mehr Zeit (Talentphasen, Phasenpuffer; nicht einzeln gemessen), als sie beim zweiten Warten sparen "
                        f"({len(rows)} Werte von t verglichen).")
    return "success", (f"Bester Wert t = {best['t']}: {days_text(best['mean'])} Tage statt {days_text(one['mean'])} bei t = 1 ({de(one['mean'] / best['mean'], 1)} mal so schnell). "
                       f"{len(near)} von {len(rows)} verglichenen Werten von t (t = {', '.join(str(t) for t in near)}) liegen höchstens 10 % über dem Minimum (Zählung bei diesem Zufalls-Seed; die Reihenfolge nahe beieinander liegender Werte liegt im Rauschen).")


def verdict_scaling(rows: list[dict]) -> tuple[str, str]:
    """Experiment „Größe“: Vorsprung der Mehr-Zähler-Regel gegen einen Zähler bei kleinstem und größtem n."""
    first, last = rows[0], rows[-1]
    wins = sum(1 for r in rows if r["multi"] < r["single"])
    return "info", (f"Bei n = {first['n']} Gefangenen braucht t = {first['t']} Zähler {days_text(first['multi'])} Tage gegen {days_text(first['single'])} bei einem Zähler "
                    f"(Faktor {de(first['single'] / first['multi'], 2)}), bei n = {last['n']} sind es {days_text(last['multi'])} gegen {days_text(last['single'])} "
                    f"(Faktor {de(last['single'] / last['multi'], 2)}). Mehrere Zähler sind in {wins} von {len(rows)} geprüften Größen schneller als einer.")


def verdict_start(rows: list[dict]) -> tuple[str, str]:
    """Experiment „Anfangszustand“: exakte Fehlerwahrscheinlichkeit des naiven Protokolls und Dauer der Reparaturen."""
    parts = "; ".join(f"n = {r['n']}: {fraction_text(r['wrong_naive'])}" for r in rows)
    found = sum(1 for r in rows if r["found"])
    safe = sum(1 for r in rows if r["safe_reset"] and r["safe_double"])
    return "warning", (f"Bei Schalter anfangs an meldet das naive Standardprotokoll mit der exakten Wahrscheinlichkeit {parts} zu früh; für {found} von {len(rows)} Größen gibt es eine "
                       f"Besuchsfolge, die es zur falschen Meldung bringt (kürzeste in der Tabelle). Mit Rücksetzung am ersten Tag und mit doppelten Marken fällt in {safe} von {len(rows)} Größen "
                       "bei keiner Besuchsfolge eine falsche Meldung (alle erreichbaren Zustände durchsucht).")


# --- Experimente ----------------------------------------------------------------------------------------------------------------------------
def experiment_counters(n: int, runs: int, seed: int, grid=C.EXP_T_GRID) -> list[dict]:
    """Mittlere Dauer über die Zahl der Zähler t (nur t <= n // 2), Schalter anfangs aus, mit der Zerlegung in Tage „Schalter an“ und „aus“ gesehen."""
    rows = []
    for t in grid:
        if t > max(1, n // 2):
            continue
        sm = S.summary(S.simulate_many(PR.Protocol(n, t), runs, seed, False))
        rows.append({"t": t, "mean": sm["mean_days"], "se": sm["se"], "on_days": sm["mean_days"] * sm["on_share"], "off_days": sm["mean_days"] * (1 - sm["on_share"]),
                     "finished": sm["finished"], "wrong": sm["wrong_share"]})
    return rows


def default_counters(n: int) -> int:
    """Zahl der Zähler der Skalierungsreihe: ⌊√n⌋, mindestens 1 und höchstens n // 2."""
    return max(1, min(int(math.isqrt(n)), n // 2))


def experiment_scaling(runs: int, seed: int, sizes=C.EXP_N_GRID) -> list[dict]:
    """Ein Zähler gegen ⌊√n⌋ Zähler über die Größe n (Schalter anfangs aus)."""
    rows = []
    for n in sizes:
        t = default_counters(n)
        single = S.summary(S.simulate_many(PR.Protocol(n, 1), runs, seed, False))
        multi = S.summary(S.simulate_many(PR.Protocol(n, t), runs, seed, False)) if t > 1 else single
        rows.append({"n": n, "t": t, "single": single["mean_days"], "multi": multi["mean_days"], "formula": PR.expected_standard(n),
                     "all_visited": PR.expected_all_visited(n)})
    return rows


def _proved_safe(p: PR.Protocol, init_light: bool) -> bool:
    """Alle erreichbaren Zustände durchsucht (jede Besuchsfolge, beliebige Länge) und keine falsche Meldung gefunden."""
    r = X.shortest_violation(p, init_light)
    return (not r["found"]) and r["complete"]


def experiment_start(sizes=(2, 3, 4, 5, 6)) -> list[dict]:
    """Anfangszustand „an“, exakt für kleine n: naives Standardprotokoll (Fehlerwahrscheinlichkeit, kürzestes Gegenbeispiel), Rücksetzung am ersten Tag, doppelte Marken."""
    rows = []
    for n in sizes:
        naive = PR.Protocol(n, 1)
        reset = PR.Protocol(n, 1, reset=True)
        double = PR.Protocol(n, 1, marks=2)
        viol = X.shortest_violation(naive, True, max_days=100_000)
        rows.append({
            "n": n,
            "wrong_naive": X.wrong_probability_linear(naive, True),
            "found": bool(viol["found"]),
            "ce_days": viol.get("days"),
            "ce_visitors": viol.get("visitors"),
            "ce_unvisited": viol.get("unvisited"),
            "days_off": float(X.expected_days_linear(naive, False)),
            "days_reset_on": float(X.expected_days_linear(reset, True)),
            "days_double_off": float(X.expected_days_linear(double, False)),
            "days_double_on": float(X.expected_days_linear(double, True)),
            "wrong_reset": X.wrong_probability_linear(reset, True),
            "wrong_double": max(X.wrong_probability_linear(double, True), X.wrong_probability_linear(double, False)),
            "safe_reset": _proved_safe(reset, True),
            "safe_double": _proved_safe(double, True) and _proved_safe(double, False),
        })
    return rows
