"""Hundert Gefangene und eine Glühbirne - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Team, ein Bit: n Gefangene und ein Schalter; jeden Tag kommt eine zufällige Person in den Raum. Wann kann jemand sicher sagen „alle waren schon einmal hier“?
Standardprotokoll mit einem Zähler, Protokoll mit mehreren Zählern (Marken- und Talentphasen), Schalter-Anfangszustand, exakte Rechnung für kleine n.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import glb_constants as C
import glb_evaluation as V
import glb_protocol as PR
from glb_layout import dunkles_design, kopf_css
from glb_pdf_export import build_pdf
from glb_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from glb_visualization import (
    build_counters,
    build_histogram,
    build_scaling,
    build_timeline,
    day_rows,
)

st.set_page_config(page_title="Hundert Gefangene und eine Glühbirne – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return V.analyse(settings)


@st.cache_data(show_spinner=False)
def _counters(n, runs, seed):
    return V.experiment_counters(n, runs, seed)


@st.cache_data(show_spinner=False)
def _scaling(runs, seed):
    return V.experiment_scaling(runs, seed)


@st.cache_data(show_spinner=False)
def _start():
    return V.experiment_start()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in glb_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Hundert Gefangene und eine Glühbirne")
st.markdown(
    """
**n Gefangene** sehen sich nie, nur ein **Schalter** im Besucherraum trägt ein einziges Bit. Jeden Tag wird eine zufällige Person in den Raum geführt, sieht den Schalter und darf ihn umlegen.
Sobald jemand **sicher** weiß, dass alle schon einmal im Raum waren, darf er es melden; eine falsche Meldung ist verboten. Vorher dürfen sich die Gefangenen auf ein Protokoll einigen.
Diese Demo rechnet nach, wie lange das Standardprotokoll mit **einem Zähler** braucht, warum es so lange dauert, und wie viel **mehrere Zähler** in Marken- und Talentphasen davon sparen,
wenn die Tagesnummer bekannt ist. Dazu: was geschieht, wenn der **Schalter anfangs an** ist.

Weiter unten: die Zeitachse eines Laufs, drei **🔬 Experimente**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Protokoll", expanded=True):
    st.markdown(
        """
1. **Marken.** Jeder Gefangene außer dem Zähler besitzt eine Marke. Der **Zähler** (Gefangener 1) muss n − 1 Marken einsammeln. Der Schalter ist der einzige Kanal: **an** heißt „im Raum liegt eine Marke“.
2. **Ablegen.** Wer eine Marke hat und den Schalter **aus** sieht, schaltet ihn an und legt damit seine Marke ab, genau einmal.
3. **Einsammeln.** Sieht der Zähler den Schalter **an**, schaltet er aus und zählt eine Marke. Hat er n − 1 gezählt, meldet er.
4. **Warum das sicher ist:** Marken gehen nie verloren oder entstehen neu (Summe aller Stände plus Raum bleibt gleich). Hat der Zähler n − 1 Marken, hat (bei Schalter anfangs aus oder mit Rücksetzung) jeder andere seine Marke abgelegt und war damit im Raum.
5. **Mehrere Zähler.** t Zähler sammeln je einen Teil der Marken, um das Warten auf den einen Zähler zu verteilen. Danach müssen die anderen Zähler dem Kopf melden, dass sie fertig sind (**Talente**). Marken und Talente teilen sich den Schalter in
   festen Phasen; dafür müssen alle die **Tagesnummer** kennen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("👥 Gefangene und Zähler")
    n = st.slider("Zahl der Gefangenen n", *bounds("n_slider"), key="n_slider", step=1, help="Wie viele Gefangene es gibt; einer davon ist der Kopf-Zähler.")
    t = st.slider("Zahl der Zähler t", *bounds("t_slider"), key="t_slider", step=1,
                  help="Mit t = 1 das Standardprotokoll. Mit t > 1 sammeln t Zähler in Marken- und Talentphasen; t wird auf n // 2 begrenzt (jeder Zähler braucht mindestens eine Marke).")
    st.header("🔦 Schalter")
    init = st.selectbox("Schalter am Anfang", C.INIT_STATES, key="init_select", help="In welchem Zustand der Warden den Schalter vor Tag 1 hinterlässt. Die Gefangenen wissen es nicht.")
    reset = st.selectbox("Tag 1 setzt den Schalter zurück", C.RESET_CHOICES, key="reset_select",
                         help="ja: der erste Besucher behandelt den Schalter als aus (verabredet; braucht die Tagesnummer). Bei Schalter anfangs aus ändert das nichts.")
    st.header("🎲 Simulation")
    runs = st.slider("Läufe", *bounds("runs_slider"), key="runs_slider", step=10, help="Wie viele unabhängige Läufe nebeneinander simuliert werden; Lauf 1 ist der, den die Zeitachse zeigt.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Zufalls-Seed ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "t_slider": int(t), "init_select": init, "reset_select": reset, "runs_slider": int(runs), "seed_input": int(seed)})

settings = V.Settings(n=int(n), t=int(t), init=init, reset=reset, runs=int(runs), seed=int(seed))
with st.spinner("Simuliere …"):
    a = _analysis(settings)
verdicts = []   # Verdikte für den PDF-Export

# --- Hauptansicht --------------------------------------------------------------------------------------------------------------------------
st.markdown("## 📊 Wie lange dauert es, bis jemand sicher ist?")
if a.t_eff != settings.t:
    st.info(f"Mit n = {settings.n} Gefangenen sind höchstens {a.t_eff} Zähler möglich (n // 2): gerechnet wird mit t = {a.t_eff}.")
sm = a.summary
m1, m2, m3, m4 = st.columns(4)
if a.t_eff == 1:
    m1.metric("Mittlere Dauer bis zur Meldung", f"{V.days_text(sm['mean_days'])} Tage", help=f"Mittel über die {sm['finished']} Läufe mit Meldung, Standardfehler {V.de(sm['se'], 1)} Tage.")
else:
    m1.metric("Mittlere Dauer bis zur Meldung", f"{V.days_text(sm['mean_days'])} Tage", delta=f"{V.days_text(sm['mean_days'] - a.standard_formula)} gegen einen Zähler (Formel)", delta_color="inverse",
              help=f"Mittel über die {sm['finished']} Läufe mit Meldung, Standardfehler {V.de(sm['se'], 1)} Tage.")
m2.metric("Formel für einen Zähler", f"{V.days_text(a.standard_formula)} Tage", help="n·H(n−1) + n(n−1), bekannt; gilt für Schalter anfangs aus (oder Rücksetzung am ersten Tag).")
m3.metric("Bis alle einmal im Raum waren", f"{V.days_text(sm['mean_all_visited'])} Tage", help=f"Mittel der Simulation; die Formel n·H(n) gibt {V.days_text(a.all_visited_formula)} Tage. Unabhängig vom Protokoll.")
m4.metric("Falsche Meldungen", V.pct(sm["wrong_share"]), help="Anteil der Läufe, in denen gemeldet wurde, obwohl jemand nie im Raum war.")
if a.exact is not None:
    st.caption(f"Exakt über alle Zustände (n ≤ {C.EXACT_N_MAX}): Erwartungswert {V.de(a.exact['mean'], 3)} Tage"
               + (f", Wahrscheinlichkeit einer falschen Meldung {V.de(a.exact['wrong'], 4)}." if a.exact["wrong"] > 0 or (settings.init == "an" and settings.reset == "nein") else "."))

st.markdown("#### ❓ Kernfrage: Wann ist jemand sicher?")
kind, text = V.verdict_main(a)
getattr(st, kind)(text)
verdicts.append(text)

st.markdown("#### Die Zeitachse von Lauf 1")
st.plotly_chart(build_timeline(a.trace, settings.n, PR.schedule(settings.n, settings.t), a.run0_day, a.run0_wrong), width="stretch", key="timeline_chart")
st.caption("Grün: Gefangene, die noch nie im Raum waren; blau: Marken, die die Zähler noch einsammeln müssen. Der Tag, an dem die grüne Linie 0 erreicht („alle waren da“), liegt vor der sicheren Meldung. "
           "Unten der Anteil der Tage, an denen der Besucher den Schalter an sah. Bei mehreren Zählern färben blaue Streifen die Markenphasen, orange die Talentphasen.")

n_days = len(a.trace["who"])
first_day = st.slider("Tag-für-Tag-Tabelle ab Tag", 1, max(2, n_days), 1, key="table_start", help=f"Zeigt {C.TABLE_ROWS} Tage von Lauf 1: wer im Raum war, was er sah und tat.") if n_days > 1 else 1
st.dataframe(day_rows(a.trace, settings.n, PR.schedule(settings.n, settings.t), int(first_day), C.TABLE_ROWS), hide_index=True, width="stretch")
st.caption("Gefangener 1 ist der Kopf-Zähler. „Kopf: Marken“ ist sein Stand: negativ, solange ihm Marken fehlen; bei 0 (und 0 Talenten) meldet er.")

st.plotly_chart(build_histogram(a.days, a.standard_formula if a.t_eff == 1 else 0.0, sm["mean_days"]), width="stretch", key="hist_chart")
st.caption(f"Meldetage der {sm['finished']} Läufe. Der langsamste Lauf braucht {V.thousands(sm['max_days'])} Tage, der Median liegt bei {V.days_text(sm['median_days'])}.")

# PDF-Export (erst nach Klick erzeugt)
if st.button("PDF erstellen", key="pdf_button"):
    st.session_state["pdf_bytes"] = build_pdf(a, text)
if st.session_state.get("pdf_bytes"):
    st.download_button("⬇️ PDF herunterladen", st.session_state["pdf_bytes"], file_name="gluehbirne.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------
st.subheader("🔬 Experiment 1: Wie viele Zähler?")
st.caption(f"Schalter anfangs aus, {settings.runs} Läufe je Wert von t, n = {settings.n} wie in der Seitenleiste, dieselbe Besucherfolge für alle t. Die Phasenlängen folgen der Formel in der Annahmentabelle.")
sig1 = (settings.n, settings.runs, settings.seed)
if st.button("▶️ Zahl der Zähler vergleichen", key="e1_button", help="Simuliert jeden Wert von t aus {1, 2, 3, 4, 6, 8, 10, 12, 16, 20} bis n // 2; bei n = 100 und 100 Läufen einige Sekunden."):
    st.session_state["e1_signature"] = sig1
if st.session_state.get("e1_signature") == sig1:
    with st.spinner("Vergleiche die Zahl der Zähler …"):
        rows1 = _counters(*sig1)
    st.plotly_chart(build_counters(rows1), width="stretch", key="e1_chart")
    kind1, text1 = V.verdict_counters(rows1)
    getattr(st, kind1)(text1)
    st.caption("Zerlegung: Jede Marke wartet zuerst, bis ein Halter den Raum betritt („aus gesehen“), dann, bis ein Zähler kommt („an gesehen“). Mehr Zähler verkürzen das zweite Warten, kosten aber Zeit für Talentphasen und Phasenpuffer (nicht einzeln gemessen).")

st.subheader("🔬 Experiment 2: Der Schalter ist anfangs an")
st.caption("Exakt gerechnet für n = 2 bis 6 (alle Zustände, alle Besuchsfolgen, auch die schlimmsten). Naiv heißt: das Standardprotokoll, das annimmt, der Schalter sei anfangs aus.")
with st.spinner("Zähle alle Zustände …"):
    rows2 = _start()
st.dataframe(
    [{"n": r["n"], "falsche Meldung (naiv)": V.fraction_text(r["wrong_naive"]), "kürzestes Gegenbeispiel (Tage)": r["ce_days"],
      "Besuchsfolge (Gefangener 1 = Zähler)": " ".join(str(w + 1) for w in r["ce_visitors"]), "nie im Raum": ", ".join(str(w + 1) for w in r["ce_unvisited"]),
      "Tage naiv (Schalter aus)": round(r["days_off"], 2), "Tage mit Rücksetzung (an)": round(r["days_reset_on"], 2),
      "Tage doppelte Marken (aus)": round(r["days_double_off"], 2), "Tage doppelte Marken (an)": round(r["days_double_on"], 2)} for r in rows2],
    hide_index=True, width="stretch",
)
kind2, text2 = V.verdict_start(rows2)
getattr(st, kind2)(text2)
lo = min(r["days_double_on"] / r["days_off"] for r in rows2)
hi = max(r["days_double_off"] / r["days_off"] for r in rows2)
st.caption(f"Rücksetzung: der erste Besucher behandelt den Schalter als aus (kostet nichts, braucht die Tagesnummer). Doppelte Marken (ohne Tagesnummer): jeder Nicht-Zähler hat zwei Marken, der Zähler meldet nach 2n − 2 Marken, "
           f"weil höchstens eine Marke aus dem Anfangszustand stammen kann; das kostet das {V.de(lo, 2)}- bis {V.de(hi, 2)}-fache der Spalte „Tage naiv (Schalter aus)“ (Spalten rechts, n = 2 bis 6).")

st.subheader("🔬 Experiment 3: Wie wächst der Vorsprung mit n?")
st.caption(f"Ein Zähler gegen ⌊√n⌋ Zähler, Schalter anfangs aus, {settings.runs} Läufe je Größe, n = 10, 20, 30, 50 und 100.")
sig3 = (settings.runs, settings.seed)
if st.button("▶️ Größen vergleichen", key="e3_button", help="Simuliert beide Protokolle für fünf Größen; bei 100 Läufen einige Sekunden."):
    st.session_state["e3_signature"] = sig3
if st.session_state.get("e3_signature") == sig3:
    with st.spinner("Vergleiche die Größen …"):
        rows3 = _scaling(*sig3)
    st.plotly_chart(build_scaling(rows3), width="stretch", key="e3_chart")
    kind3, text3 = V.verdict_scaling(rows3)
    getattr(st, kind3)(text3)
    st.caption("Die grüne Linie ist die Zeit, bis wirklich alle einmal im Raum waren: ein sicheres Protokoll darf erst melden, wenn wirklich alle da waren.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wo es steht |
|---|---|---|
| **Jeden Tag kommt ein gleichverteilter, unabhängiger Besucher** | Wählt der Warden die Besucher, bleiben die Meldungen der sicheren Varianten sicher (Erhaltung), aber die Dauer ist nicht mehr beschränkt: er kann den Zähler beliebig lange fernhalten. | Experiment 2 (Aufzählung aller Besuchsfolgen), Sicherheit |
| **Der Schalter ist anfangs aus (bekannt)** | Das naive Protokoll meldet bei Schalter anfangs an mit Wahrscheinlichkeit 1/2^(n−1) zu früh (exakt für n = 2 bis 6) und hat Besuchsfolgen, die es sicher zur falschen Meldung bringen. | Experiment 2 |
| **Die Tagesnummer ist allen bekannt** | Mehrere Zähler und die Rücksetzung am ersten Tag brauchen sie. Ohne sie bleiben der Standard und die doppelten Marken. | Seitenleiste, Experiment 2 |
| **Alle halten das Protokoll fehlerfrei ein** | Eine einzige vergessene Marke oder ein falscher Handgriff kann die Erhaltung verletzen; Fehlertoleranz wird nicht untersucht. | nicht gemessen |
| **Phasenlängen nach einer Formel** | Die Faktoren sind bei n = 100 abgestimmt, nicht optimal bewiesen; bei kleinem n (zum Beispiel n = 10) sind mehrere Zähler langsamer als einer. | Experiment 3, README |
| **Ein Bit als Kanal** | Mit mehr Zuständen am Schalter (oder mehr Schaltern) ist es ein anderes Rätsel; nicht untersucht. | Majerech klammert Schalter mit mehr als zwei Zuständen aus |
| **Ein Modell** | Eine Aussage über das Rätsel, nicht über Menschen. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown("**Gegeben und gesucht.** Gegeben sind n Gefangene und ein Schalter $L_d \\in \\{0, 1\\}$. An Tag $d$ kommt ein gleichverteilter, unabhängiger Besucher $X_d \\in \\{1, \\dots, n\\}$, sieht $L_{d-1}$ und setzt $L_d$. Gesucht ist ein Protokoll, "
                "dessen Meldung nie falsch ist, mit kleiner erwarteter Zeit $T$ bis zur Meldung.")
    st.markdown(
        r"""
| Symbol | Bedeutung |
|---|---|
| $n$ | Zahl der Gefangenen |
| $t$ | Zahl der Zähler |
| $H_m$ | harmonische Zahl $1 + \tfrac12 + \dots + \tfrac1m$ |
| $T$ | Tag der Meldung |
| $\mathrm{tok}_i$, $\mathrm{tal}_i$ | Marken- und Talentstand von Gefangenem $i$ |
"""
    )
    st.markdown(r"""**Erhaltung.** Marken (und getrennt Talente) werden nur zwischen einem Gefangenen und dem Raum bewegt; mit $r_d \in \{0, 1\}$ Marken im Raum nach Tag $d$ gilt für alle $d$:""")
    st.latex(r"\sum_{i=1}^{n} \mathrm{tok}_i + r_d = 0 .")
    st.markdown(r"""Nicht-Zähler haben nie einen negativen Stand. Meldet der Kopf bei $\mathrm{tok}_1 = 0$ und $\mathrm{tal}_1 = 0$, sind alle Stände null, also hat jeder Nicht-Zähler seine Marke einmal abgelegt und war im Raum.""")
    st.markdown(r"""**Standardprotokoll (bekannt).** Je Marke wartet man auf einen Halter, solange der Schalter aus ist ($i$ Halter: im Mittel $n/i$ Tage), und auf den Zähler, solange er an ist ($n$ Tage):""")
    st.latex(r"\mathbb{E}[T] = \sum_{i=1}^{n-1} \left( \frac{n}{i} + n \right) = n H_{n-1} + n(n-1) .")
    st.markdown(r"""**Untergrenze durch das Sammelproblem.** Bis alle Gefangenen einmal im Raum waren, vergehen im Mittel (bekannt)""")
    st.latex(r"\mathbb{E}[\text{letzter Erstbesuch}] = n H_n .")
    st.markdown(
        r"""**Mehrere Zähler.** Die Markenphase wartet je Marke im Zustand „an“ im Mittel $n/t$ Tage statt $n$, solange $t$ Zähler offene Ziele haben. Richtwerte für die Phasenlängen (Heuristik, nicht bewiesen optimal):"""
    )
    st.latex(r"E_M = \frac{n(n-t)}{t} + n H_{n-t}, \qquad E_T = n(t-1) + n H_{t-1} .")
    def _tex(x):
        return V.de(x, 2).rstrip("0").rstrip(",").replace(",", "{,}")

    st.markdown(f"Die erste Markenphase dauert ${_tex(C.PHASE_A)}\\,E_M$ Tage, die erste Talentphase ${_tex(C.PHASE_B)}\\,E_T$ Tage, "
                f"danach wechseln Phasen der Länge ${_tex(C.PHASE_R)}\\,n$ ab (aufgerundet auf ganze Tage).")
    st.markdown(
        """**Literatur.** Vladan Majerech, „100 prisoners and a lightbulb – looking back“ (Manuskript auf der Seite des Autors, selbst gelesen; laut Zusammenfassung lagen veröffentlichte Lösungen für 100 Gefangene
über 3850 Besuchen im Mittel und seine eigenen unter 3390; beschreibt Schneeball-Vorphase, mehrere Zähler und Talente). Dehaye, Ford, Segerman, „One hundred prisoners and a lightbulb“, The Mathematical Intelligencer (DOI 10.1007/BF02984862;
nur Titel und Autoren bestätigt, Jahr in den Quellen uneinheitlich, Inhalt nicht selbst gelesen)."""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
