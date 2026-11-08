"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Rechenaufwand am Slider-Maximum (DEMO-PLAYBOOK §1c): ein Tag kostet O(Läufe) (ein Besucher je Lauf, wenige Zeilen numpy), die Läufe laufen nebeneinander (Achse 0).
Standardprotokoll bei n = 100 braucht im Mittel rund 10 400 Tage, der langsamste von 400 Läufen etwa das Doppelte; die Tagesschleife ist O(Tage), je Tag O(Läufe).
Die Einzellauf-Zeitachse (skalar, Tag für Tag) kostet O(Tage) mit einem Python-Schritt je Tag. Die exakte Aufzählung (glb_exact) ist nur für n <= EXACT_N_MAX gedacht.
"""

# --- Regler ---------------------------------------------------------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 2, 100, 100          # Zahl der Gefangenen
T_MIN, T_MAX, DEFAULT_T = 1, 20, 1             # Zahl der Zähler (wird auf n // 2 begrenzt)
RUNS_MIN, RUNS_MAX, DEFAULT_RUNS = 20, 400, 100  # Läufe (Wiederholungen) der Simulation
SEED_MAX, DEFAULT_SEED = 999_999, 35
INIT_STATES = ("aus", "an")                    # Anfangszustand des Schalters
DEFAULT_INIT = "aus"
RESET_CHOICES = ("nein", "ja")                 # Tag 1 setzt den Schalter zurück (braucht die Tagesnummer)
DEFAULT_RESET = "nein"

# --- Simulation -----------------------------------------------------------------------------------------------------------------------------
CHUNK = 256                                    # so viele Tage werden mit einem Block Zufallszahlen vorab gezogen
CAP_FACTOR, CAP_BASE = 12, 5_000               # Tagesgrenze eines Laufs: CAP_FACTOR * n^2 + CAP_BASE (Standard braucht im Mittel n^2 + n H(n-1))
TRACE_MAX_DAYS = 40_000                        # so viele Tage zeichnet die Zeitachse höchstens
TABLE_ROWS = 40                                # Zeilen der Tag-für-Tag-Tabelle
EXACT_N_MAX = 6                                # bis hier rechnet die App den Erwartungswert exakt aus (alle Zustände)
COUNTEREXAMPLE_N_MAX = 6                       # bis hier sucht die App das kürzeste Gegenbeispiel

# --- Phasenlängen der Protokolle mit mehreren Zählern ---------------------------------------------------------------------------------------
# erste Markenphase = PHASE_A * Erwartung, erste Talentphase = PHASE_B * Erwartung, danach abwechselnd Phasen der Länge PHASE_R * n
# (Faktoren in der Nähe der besten Gitterzelle bei n = 100 gewählt; die beste Zelle hatte PHASE_R = 5,0 statt 3,0, Messbericht vormessung/out_e3b_gluehbirne_protokolle.txt)
PHASE_A, PHASE_B, PHASE_R = 1.5, 1.25, 3.0

# --- Experimente ----------------------------------------------------------------------------------------------------------------------------
EXP_RUNS = 100                                 # Läufe je Zelle der Live-Experimente
EXP_SEED = 20261108
EXP_T_GRID = (1, 2, 3, 4, 6, 8, 10, 12, 16, 20)
EXP_N_GRID = (10, 20, 30, 50, 100)

# --- Farben ---------------------------------------------------------------------------------------------------------------------------------
COLOR_LIGHT = "#C0762B"          # Schalter
COLOR_VISITED = "#2F6B65"        # wahre Zahl der Besuchten
COLOR_COUNT = "#4c78a8"          # gezählte Marken
COLOR_RED = "#d62728"
COLOR_GREY = "rgba(150,150,150,0.65)"
COLOR_PHASE_MARK = "rgba(76,120,168,0.10)"
COLOR_PHASE_TALENT = "rgba(192,118,43,0.14)"

# --- Presets --------------------------------------------------------------------------------------------------------------------------------
BASE = {"n": DEFAULT_N, "t": DEFAULT_T, "init": DEFAULT_INIT, "reset": DEFAULT_RESET, "runs": DEFAULT_RUNS, "seed": DEFAULT_SEED}
PRESETS = {
    "Standard: 100 Gefangene, ein Zähler": dict(BASE),
    "Zehn Zähler (t = 10)": {**BASE, "t": 10},
    "Kleiner Fall: 4 Gefangene": {**BASE, "n": 4, "runs": 400},
    "Schalter anfangs an, naiv": {**BASE, "n": 4, "init": "an", "runs": 400},
    "Schalter anfangs an, Tag 1 setzt zurück": {**BASE, "n": 4, "init": "an", "reset": "ja", "runs": 400},
}
PRESET_HELP = {
    "Standard: 100 Gefangene, ein Zähler": "Hundert Gefangene, ein Zähler, Schalter anfangs aus: das Lehrbuchprotokoll. Formel 10.417,7 Tage, Simulation 10.382,9 ± 30,5 Tage (1000 Läufe, README).",
    "Zehn Zähler (t = 10)": "Dasselbe Rätsel mit zehn Zählern in Marken- und Talentphasen; braucht die Tagesnummer als gemeinsames Wissen. 3.646,1 ± 22,7 Tage (1000 Läufe, README).",
    "Kleiner Fall: 4 Gefangene": "Vier Gefangene, ein Zähler: klein genug, um den Erwartungswert exakt über alle Zustände zu rechnen (58/3 Tage, README).",
    "Schalter anfangs an, naiv": "Vier Gefangene, der Warden hat den Schalter angelassen, das Standardprotokoll weiß es nicht: der Zähler zählt eine Marke, die nie jemand gegeben hat. Exakte Wahrscheinlichkeit einer falschen Meldung: 1/8.",
    "Schalter anfangs an, Tag 1 setzt zurück": "Wie zuvor, aber am ersten Tag behandelt der erste Besucher den Schalter nach Verabredung als aus: keine falsche Meldung, und die Dauer ist dieselbe wie bei Schalter anfangs aus.",
}
