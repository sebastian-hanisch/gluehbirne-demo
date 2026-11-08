"""Plotly-Abbildungen und die Tag-für-Tag-Tabelle. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import glb_constants as C
import glb_protocol as PR

POINTS = 700            # so viele Stützstellen hat die Zeitachse höchstens
BINS = 80               # Fenster der Schalter-Anteile
MAX_BANDS = 24          # so viele Phasen werden höchstens eingefärbt


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def thin(days: int, points: int = POINTS) -> np.ndarray:
    """Tage 1 bis `days`, auf höchstens `points` Stützstellen ausgedünnt; der letzte Tag bleibt erhalten."""
    if days <= points:
        return np.arange(1, days + 1)
    step = int(np.ceil(days / points))
    idx = np.arange(1, days + 1, step)
    return idx if idx[-1] == days else np.append(idx, days)


def phase_bands(sched: PR.Schedule | None, days: int) -> list[tuple[int, int, int]]:
    """(Beginn, Ende, Phase) der ersten MAX_BANDS Phasen bis zum Tag `days`."""
    if sched is None:
        return []
    bands, start, k = [], 1, 0
    lengths = [sched.first_mark, sched.first_talent]
    while start <= days and k < MAX_BANDS:
        length = lengths[k] if k < 2 else sched.recovery
        phase = PR.MARKE if k % 2 == 0 else PR.TALENT
        bands.append((start, min(start + length - 1, days), phase))
        start += length
        k += 1
    return bands


def build_timeline(trace: dict, n: int, sched: PR.Schedule | None, declared_day: int | None, wrong: bool):
    """Oben: wie viele Gefangene noch nie im Raum waren und wie viele Marken (Talente) die Zähler noch einsammeln müssen. Unten: Anteil der Tage, an denen der Schalter an war."""
    days = len(trace["who"])
    if days == 0:
        return _base(go.Figure())
    d = thin(days)
    unseen = n - np.array(trace["visited"])
    goal = np.array(trace["goal_left"])
    talent = np.array(trace["talent_left"])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38], vertical_spacing=0.06)
    for a, b, ph in phase_bands(sched, days):
        color = C.COLOR_PHASE_MARK if ph == PR.MARKE else C.COLOR_PHASE_TALENT
        fig.add_vrect(x0=a - 0.5, x1=b + 0.5, fillcolor=color, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=d, y=unseen[d - 1], mode="lines", line=dict(color=C.COLOR_VISITED, width=2.5, shape="hv"), name="Gefangene, die noch nie im Raum waren",
                             hovertemplate="Tag %{x}: %{y}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=d, y=goal[d - 1], mode="lines", line=dict(color=C.COLOR_COUNT, width=2.5, shape="hv"), name="Marken, die die Zähler noch einsammeln müssen",
                             hovertemplate="Tag %{x}: %{y}<extra></extra>"), row=1, col=1)
    if talent.max() > 0:
        fig.add_trace(go.Scatter(x=d, y=talent[d - 1], mode="lines", line=dict(color=C.COLOR_LIGHT, width=2, dash="dash", shape="hv"), name="Talente, die der Kopf noch einsammeln muss",
                                 hovertemplate="Tag %{x}: %{y}<extra></extra>"), row=1, col=1)
    saw = np.array(trace["saw"], dtype=float)
    edges = np.linspace(0, days, min(BINS, max(1, days)) + 1).astype(int)
    mids, share = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi > lo:
            mids.append((lo + hi + 1) / 2)
            share.append(100.0 * saw[lo:hi].mean())
    fig.add_trace(go.Bar(x=mids, y=share, marker_color=C.COLOR_LIGHT, name="Anteil der Tage mit Schalter an gesehen (%)", hovertemplate="um Tag %{x:.0f}: %{y:.0f} %<extra></extra>"), row=2, col=1)
    if declared_day is not None:
        label = "falsche Meldung" if wrong else "Meldung"
        fig.add_vline(x=declared_day, line=dict(color=C.COLOR_RED, width=2, dash="dot"))
        fig.add_annotation(x=declared_day, y=n, text=f"{label}: Tag {declared_day}", showarrow=False, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.88)", font=dict(color=C.COLOR_RED),
                           row=1, col=1)
    fig.update_xaxes(range=[0, max(days, 1) + 0.5], title_text="Tag", row=2, col=1)
    fig.update_yaxes(range=[0, n * 1.02], title_text="Anzahl", row=1, col=1)
    fig.update_yaxes(range=[0, 100], title_text="Schalter an (%)", row=2, col=1)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.18), plot_bgcolor="rgba(0,0,0,0)", bargap=0.05)
    return lock_axes(fig)


def build_histogram(days, formula: float, mean: float):
    """Meldetage der Läufe; senkrecht: Mittel der Läufe und, wo es eine Formel gibt, ihr Wert."""
    fig = go.Figure(go.Histogram(x=list(days), nbinsx=30, marker_color=C.COLOR_COUNT, hovertemplate="%{x}: %{y} Läufe<extra></extra>", name="Läufe"))
    fig.add_vline(x=mean, line=dict(color=C.COLOR_LIGHT, width=3), annotation_text="Mittel der Läufe", annotation_position="top left")
    if formula:
        fig.add_vline(x=formula, line=dict(color=C.COLOR_RED, width=2, dash="dash"), annotation_text="Formel (ein Zähler)", annotation_position="top right")
    fig.update_xaxes(title_text="Tag der Meldung")
    fig.update_yaxes(title_text="Läufe")
    return _base(fig, 320)


def build_counters(rows):
    """Mittlere Dauer je Zahl der Zähler, zerlegt in Tage mit Schalter an gesehen (der Zähler wird erwartet) und aus gesehen (ein Halter wird erwartet)."""
    xs = [f"t = {r['t']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["on_days"] for r in rows], name="Tage mit Schalter an gesehen", marker_color=C.COLOR_LIGHT, hovertemplate="%{x}: %{y:.0f} Tage<extra></extra>"))
    fig.add_trace(go.Bar(x=xs, y=[r["off_days"] for r in rows], name="Tage mit Schalter aus gesehen", marker_color=C.COLOR_COUNT, hovertemplate="%{x}: %{y:.0f} Tage<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Zahl der Zähler", type="category")
    fig.update_yaxes(title_text="mittlere Dauer (Tage)", rangemode="tozero")
    return _base(fig)


def build_scaling(rows):
    """Ein Zähler gegen ⌊√n⌋ Zähler über die Größe n."""
    xs = [f"n = {r['n']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["single"] for r in rows], name="ein Zähler", marker_color=C.COLOR_LIGHT, hovertemplate="%{x}: %{y:.0f} Tage<extra></extra>"))
    fig.add_trace(go.Bar(x=xs, y=[r["multi"] for r in rows], name="⌊√n⌋ Zähler", marker_color=C.COLOR_COUNT, hovertemplate="%{x}: %{y:.0f} Tage<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["all_visited"] for r in rows], mode="lines+markers", name="bis alle einmal im Raum waren (n·H(n))", line=dict(color=C.COLOR_VISITED, width=2),
                             hovertemplate="%{x}: %{y:.0f} Tage<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="mittlere Dauer (Tage)", rangemode="tozero")
    return _base(fig)


def day_rows(trace: dict, n: int, sched: PR.Schedule | None, start: int, count: int) -> list[dict]:
    """Tabellenzeilen der Tage start bis start + count - 1 (Tag 1 ist der erste). Gefangene werden ab 1 nummeriert; Gefangener 1 ist der Kopf-Zähler."""
    rows = []
    last = len(trace["who"])
    for day in range(start, min(start + count, last + 1)):
        i = day - 1
        phase, first, _ = PR.phase_info(sched, day)
        saw, after = trace["saw"][i], trace["light"][i]
        what = "legt ab (schaltet an)" if (not saw and after) else "nimmt auf (schaltet aus)" if (saw and not after) else "lässt den Schalter"
        rows.append({
            "Tag": day, "Phase": "Marken" if phase == PR.MARKE else "Talente", "Gefangener": trace["who"][i] + 1, "sah den Schalter": "an" if saw else "aus",
            "Handlung": what, "Schalter danach": "an" if after else "aus", "Kopf: Marken": trace["head_tok"][i], "Kopf: Talente": trace["head_tal"][i],
            "bisher im Raum": trace["visited"][i], "von": n,
        })
    return rows
