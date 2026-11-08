"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Kennzahlen und das Verdikt. Erst nach Klick erzeugt (DEMO-PLAYBOOK §1c)."""

from __future__ import annotations

from fpdf import FPDF

import glb_evaluation as V

_REPLACE = {"–": "-", "—": "-", "≤": "<=", "≥": ">=", "≠": "!=", "√": "Wurzel", "²": "2", "Σ": "Summe", "·": "*", "−": "-", "„": '"', "“": '"', "”": '"', "→": "->", "×": "x", "≈": "~",
            "…": "...", "⌊": "[", "⌋": "]", "’": "'", "‘": "'"}


def _latin(text: str) -> str:
    """Kernschriften kennen nur Latin-1: Sonderzeichen ersetzen, Markdown-Sterne entfernen."""
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.replace("**", "").replace("`", "").encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: V.Analysis, verdict_text: str) -> bytes:
    s = a.settings
    sm = a.summary
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _latin("Hundert Gefangene und eine Glühbirne"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _latin(f"n = {s.n} Gefangene; {a.t_eff} Zähler; Schalter anfangs {s.init}; Tag 1 setzt zurück: {s.reset}; {s.runs} Läufe; Zufalls-Seed {s.seed}."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Kennzahlen", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    lines = [
        f"Mittlere Dauer bis zur Meldung: {V.days_text(sm['mean_days'])} Tage (Standardfehler {V.de(sm['se'], 1)}), Läufe mit Meldung: {sm['finished']} von {sm['runs']}.",
        f"Formel für einen Zähler, Schalter anfangs aus: n*(n-1) + n*H(n-1) = {V.days_text(a.standard_formula)} Tage.",
        f"Bis alle Gefangenen einmal im Raum waren (n*H(n)): {V.days_text(a.all_visited_formula)} Tage.",
        f"Anteil falscher Meldungen: {V.pct(sm['wrong_share'])}.",
    ]
    if a.exact is not None:
        lines.append(f"Exakt über alle Zustände (n <= 6): Erwartungswert {V.de(a.exact['mean'], 3)} Tage, falsche Meldung mit Wahrscheinlichkeit {V.de(a.exact['wrong'], 4)}.")
    for line in lines:
        pdf.multi_cell(0, 5, _latin(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Verdikt", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _latin(verdict_text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _latin("Modell eines Rätsels, keine Aussage über Menschen oder Gefängnisse. Annahmen: jeden Tag ein gleichverteilter, unabhängiger Besucher; alle halten das Protokoll fehlerfrei ein; "
                                "bei mehreren Zählern und bei der Rücksetzung ist die Tagesnummer allen bekannt."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
