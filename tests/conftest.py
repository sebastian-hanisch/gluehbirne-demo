"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b). Alle Erwartungswerte stehen als Rechnung dabei."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def hand_two():
    """n = 2, ein Zähler (Gefangener 0 braucht n - 1 = 1 Marke, Gefangener 1 hat sie), Schalter anfangs aus.
    Besuchsfolge 1, 0: Tag 1 legt Gefangener 1 seine Marke ab (Schalter an), Tag 2 nimmt sie der Zähler (Stand −1 → 0): Meldung an Tag 2.
    Besuchsfolge 0, 1, 1, 0: Tag 1 der Zähler sieht aus, nichts; Tag 2 Ablage; Tag 3 der Besucher hat keine Marke mehr; Tag 4 Meldung.
    Erwartung: auf den Halter warten im Mittel 2 Tage (Wahrscheinlichkeit 1/2 je Tag), dann auf den Zähler 2 Tage: 4 Tage = n·H(1) + n(n−1) = 2 + 2."""
    return {"short": ([1, 0], 2), "long": ([0, 1, 1, 0], 4), "expected": 4}


@pytest.fixture
def hand_three():
    """n = 3, ein Zähler: zwei Marken. Erwartung = 3·H(2) + 3·2 = 3·1,5 + 6 = 4,5 + 6 = 10,5 = 21/2.
    Besuchsfolge 1, 2, 0, 0: Tag 1 Ablage (an), Tag 2 Gefangener 2 sieht an, legt nichts ab, Tag 3 der Zähler nimmt auf (Stand −2 → −1, aus), Tag 4 der Zähler sieht aus: nichts. Noch keine Meldung."""
    return {"seq_open": [1, 2, 0, 0], "expected": 10.5}


@pytest.fixture
def hand_four_two_counters():
    """n = 4, t = 2: Ziele (4 − 2) / 2 = 1 je Zähler, Zähler 0 (Kopf) hält −1 Marke und −1 Talent, Zähler 1 hält −1 Marke und +1 Talent, Gefangene 2 und 3 je +1 Marke.
    Phasen: E_M = 4·2/2 + 4·H(2) = 4 + 6 = 10 → erste Markenphase 1,5 · 10 = 15 Tage; E_T = 4·1 + 4·H(1) = 8 → erste Talentphase 1,25 · 8 = 10 Tage (Tage 16 bis 25); danach je 3 · 4 = 12 Tage (Tage 26 bis 37 Marken, 38 bis 49 Talente).
    Besuchsfolge: Tag 1 Gefangener 2 legt ab (an); Tag 2 der Kopf nimmt auf (Stand 0, Marken); Tag 3 Gefangener 3 legt ab; Tag 4 Zähler 1 nimmt auf (Stand 0); Tage 5 bis 15 Gefangener 2 (nichts mehr zu tun);
    Tag 16 (Talentphase) Zähler 1 legt sein Talent ab (Marken erreicht); Tag 17 der Kopf nimmt das Talent: Stand 0 und 0, Meldung an Tag 17."""
    return {"seq": [2, 0, 3, 1] + [2] * 11 + [1, 0], "declared": 17, "phases": (15, 10, 12)}
