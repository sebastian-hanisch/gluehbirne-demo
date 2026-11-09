# Hundert Gefangene und eine Glühbirne – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-gluehbirne-demo.streamlit.app/)**

Stück 3 der Linie „Teamrätsel“ in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Ein Team hat **ein gemeinsames Ziel**, darf **vorher eine Strategie festlegen** und handelt dann mit **beschränkter Information**: hier ein einziges Bit, der Schalter einer Glühbirne. Die Linie fragt, was eine abgesprochene Strategie bringt und wie viel zusätzliche Information wert ist. Das Stück hängt in der Planung an `gefangene-kaesten-demo` (Stück 1, Idee: ein Kanal als knappe Ressource); es setzt dessen Wissen nicht voraus. Abgrenzung: Die Koordinationsspiele-Linie (zum Beispiel `fokalpunkt-demo`) behandelt Eigennutz und Gleichgewichtsauswahl, hier geht es um ein gemeinsames Ziel und eine Strategie unter Informationsbeschränkung.

## Warum dieses Problem

*100 Gefangene, ein Besucherraum mit einem Schalter. Jeden Tag wird eine zufällige Person in den Raum geführt, sieht den Schalter und darf ihn umlegen. Sobald jemand **sicher** ist, dass alle schon einmal im Raum waren, darf er das melden; eine falsche Meldung ist verboten.* Das Standardprotokoll mit **einem Zähler** ist Lehrbuchwissen und braucht bei 100 Gefangenen im Mittel rund 28,5 Jahre. Die Demo rechnet nach, **warum** es so lange dauert (der Schalter wartet fast immer auf den einen Zähler), und baut ein **Protokoll mit mehreren Zählern** nach, das die Wartezeit auf mehrere Zähler verteilt und dafür Marken- und Talentphasen braucht. **Kernfrage: Wann kann jemand sicher sein, und wie viel von der Wartezeit ist Vorsicht, wie viel Informationsmangel?**

## Modell

* n Gefangene, ein Schalter mit zwei Zuständen. An Tag d kommt ein **gleichverteilter, unabhängiger** Besucher, sieht den Schalter und setzt ihn. Gemeldet wird nur, wenn sicher alle schon im Raum waren.
* **Marken.** Jeder Nicht-Zähler besitzt eine Marke, der Zähler muss n − 1 Marken einsammeln. Schalter an heißt: im Raum liegt eine Marke. Die Summe aller Stände plus Rauminhalt bleibt unverändert; Nicht-Zähler haben nie einen negativen Stand. Hat der Zähler seinen Stand auf 0 gebracht, sind (bei Schalter anfangs aus oder mit Rücksetzung) alle Stände 0, und jeder Nicht-Zähler hat seine Marke einmal im Raum abgelegt (**Sicherheitsargument**, im 📐-Expander der App).
* **Mehrere Zähler.** t Zähler sammeln je einen Teil der n − t Marken. Weil die anderen Zähler dem Kopf-Zähler melden müssen, dass sie fertig sind, gibt es einen zweiten Stoff, die **Talente**; Marken und Talente teilen sich den Schalter in festen Phasen (Marke, Talent, danach abwechselnd). Am ersten Tag einer Phase sammelt der Besucher einen Rest der Vorphase ein, damit die Erhaltung gilt. Das braucht die **Tagesnummer** als gemeinsames Wissen; das Standardprotokoll braucht sie nicht.
* **Anfangszustand.** Das Standardprotokoll nimmt an, der Schalter sei anfangs aus. Ist er an, zählt der Zähler eine Marke, die nie jemand gegeben hat. Zwei Reparaturen: **Rücksetzung** (der erste Besucher behandelt den Schalter als aus, braucht die Tagesnummer) und **doppelte Marken** (jeder Nicht-Zähler hat zwei, der Zähler meldet nach 2n − 2 Marken; ohne Tagesnummer).
* Bekannt sind: die Formel für einen Zähler, die Sammelzeit n·H(n), das Sicherheitsargument und die Idee mehrerer Zähler mit Marken und Talenten (Majerech, siehe unten). Eigene Fassung: die konkreten Regeln, die Phasenlängen, die Aufzählung aller Besuchsfolgen und die exakte Rechnung für kleine n.

## Methodik

* **Kern** in kleinen Einheiten (`glb_protocol.py`): Ziele, Anfangsstände, Phasenplan, Markenregel, Talentregel, Rest der Vorphase, Besuch, Meldung. Jede Regel ist eine reine Funktion und einzeln an einer Handrechnung geprüft.
* **Zwei Simulationen** mit denselben Besuchern (SplitMix64, Portfolio-Konvention): eine skalare, Tag für Tag (Zeitachse und Tabelle), eine vektorisierte über viele Läufe (Mittel, Verteilung).
* **Exakte Rechnung** (`glb_exact.py`) für kleine n: Erwartungswert als Bruch (Gleichungssystem), Weiterschieben der Wahrscheinlichkeiten Tag für Tag (mehrere Zähler), Wahrscheinlichkeit einer falschen Meldung, und die **Breitensuche über alle Besuchsfolgen** (auch bösartige): findet die kürzeste Folge mit falscher Meldung oder zeigt, dass es für jede Besuchsfolge beliebiger Länge keine gibt.
* **Phasenlängen** nach einer Formel aus den Erwartungswerten der beiden Phasen (Faktoren in `glb_constants.py`); bei n = 100 und t = 10 in der Nähe der besten Gitterzelle gewählt (Vormessung E3b; die beste Zelle hatte für die Wechselphasen 5,0 statt 3,0, beide gleich gut im Rahmen der Streuung), nicht als optimal bewiesen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: feste Zufalls-Seeds, Läufe wie genannt; `tests/test_claims.py` rechnet sie nach, die kleinen exakten Werte `tests/test_oracle_gluehbirne.py`.

| Frage | Befund |
|---|---|
| Wie lange braucht ein Zähler bei 100 Gefangenen? | Formel n·H(n−1) + n(n−1) = **10.417,7 Tage** (rund 28,5 Jahre). Simulation: 10.382,9 ± 30,5 Tage (1000 Läufe, Mittel ± Standardfehler). |
| Stimmt die Formel? | Exakt für n = 2 bis 6 als Bruch aus dem Gleichungssystem über alle Zustände: 4, 21/2, 58/3, 365/12, 437/10 (jeweils gleich der Formel); dazu eine unabhängig gebaute Markov-Kette über (Halter, Schalter) für n = 2 bis 10. |
| Wo geht die Zeit hin? | An **95,0 %** der Tage sieht der Besucher den Schalter **an** (Simulation 95,0 %, Formel n(n−1) / E[T] = 95,0 %): Der Schalter wartet auf den einen Zähler, nicht auf die Gefangenen. |
| Wann waren wirklich alle da? | Nach n·H(n) = **518,7 Tagen** im Mittel (Sammelproblem, unabhängig vom Protokoll). Das Standardprotokoll braucht das **20,1-fache**; zehn Zähler das **7,0-fache**. |
| Wie viel bringen mehrere Zähler bei n = 100? | Zehn Zähler: **3.646,1 ± 22,7 Tage** (1000 Läufe, derselbe Zufalls-Seed wie oben), also in dieser Messreihe **2,86 mal so schnell** wie die Formel für einen Zähler (10.417,7 / 3.646,1). Mit 20 anderen Zufalls-Seeds (je 1000 Läufe) liegt dieser Faktor zwischen 2,85 und 2,91, also bei etwa 2,9. Bei t = 10 sieht der Besucher an 63,6 % der Tage den Schalter an. |
| Welche Zahl der Zähler ist die beste? | Gitter t ∈ {1, 2, 3, 4, 6, 8, 10, 12, 16, 20}, 400 Läufe je Wert: bestes t = **10** mit 3.607,8 Tagen gegen 10.459,8 bei t = 1. **3 von 10** Werten (t = 8, 10, 12) liegen höchstens 10 % über dem Minimum; bei t = 20 sind es 4.325,2 Tage. Die Zählung gilt für diesen Zufalls-Seed: mit 10 anderen Zufalls-Seeds (je 400 Läufe) ist t = 10 in 9 Läufen und t = 12 in 1 Lauf das beste, 3 bis 5 Werte liegen innerhalb von 10 %, und t = 8, 10, 12 sind immer darunter. Die Reihenfolge nahe beieinander liegender Werte liegt im Rauschen. |
| Lohnt es sich bei kleinen Gruppen? | **Nicht bei n = 10:** t = 3 braucht 127,9 Tage gegen 115,1 bei einem Zähler. Bei n = 20 gewinnen mehrere Zähler (375,6 gegen 446,1), ebenso bei n = 30 und n = 50, bei n = 100 sind es 3.664,8 gegen 10.413,6 Tage (200 Läufe je Größe, t = ⌊√n⌋). Schneller als einer: **4 von 5** Größen. Zwischen den gemessenen Größen liegt die Schwelle (Nachmessung mit 10 Zufalls-Seeds und je 400 Läufen): bei n = 12 war t = ⌊√n⌋ = 3 in keinem Lauf schneller als ein Zähler, bei n = 14 in allen 10. |
| Stimmt die Simulation für mehrere Zähler? | Exakter Erwartungswert über alle Zustände gegen 20.000 Läufe (Zufalls-Seed 3): n = 4, t = 2: 29,518 Tage; n = 5, t = 2: 43,247; n = 6, t = 2: 59,474; n = 6, t = 3: 60,553. Größter Abstand der Simulation: 1,3 Standardfehler. |
| Was passiert, wenn der Schalter anfangs an ist? | Das naive Protokoll meldet **exakt mit Wahrscheinlichkeit 2^−(n−1)** zu früh (n = 2 bis 6: 1/2, 1/4, 1/8, 1/16, 1/32). **Eine kürzeste bösartige Besuchsfolge** hat 2n − 3 Tage: der Zähler wechselt sich mit den Gefangenen 2 bis n − 1 ab, Gefangener n war nie im Raum. |
| Sind die Reparaturen sicher? | Rücksetzung und doppelte Marken: Breitensuche über alle erreichbaren Zustände (jede Besuchsfolge beliebiger Länge) findet für n = 2 bis 6 keine falsche Meldung. Mehrere Zähler mit Rücksetzung (n, t) = (4, 2), (5, 2), (6, 2), (6, 3): ebenfalls keine. |
| Was kosten die doppelten Marken? | Bei n = 6: 82,85 Tage (Schalter anfangs aus) und 76,85 (an) gegen 43,70 für das Standardprotokoll, das **1,90-fache** bzw. **1,76-fache**. Über n = 2 bis 6 liegt das Verhältnis zwischen 1,50 und 2,00. |
| Und die Rücksetzung? | Nichts: Die Läufe sind für Schalter an und aus Tag für Tag gleich; die exakte Dauer ist n·H(n−1) + n(n−1) (n = 2 bis 6). |

**Einordnung gegen die Literatur** (nur laut Zusammenfassung des Manuskripts von Majerech, selbst gelesen): veröffentlichte Lösungen lagen für 100 Gefangene bei über 3850 Besuchen im Mittel, die besten Forenlösungen um 3500, seine eigene unter 3390. Die 3.646 Tage hier liegen in derselben Größenordnung; ein Vergleich im Einzelnen (Annahmen zum Tageszähler, Aufbau der Phasen) ist nicht erfolgt. Abstimmung der Phasenfaktoren (Vormessung E3b, `teamraetsel-planung/vormessung/`): bei n = 100, t = 10 liegen die gewählten Faktoren auf frischen Läufen bei 3.585 ± 33 Tagen, die beste Gitterzelle bei 3.610 ± 33.

## Ehrliche Grenzen

* **Die Besucher sind gleichverteilt und unabhängig.** Wählt der Warden die Besucher, bleiben die Meldungen der sicheren Varianten (Standard bei Schalter anfangs aus, Rücksetzung, doppelte Marken, mehrere Zähler mit Rücksetzung) sicher (Erhaltung; Breitensuche für kleine n), aber die Dauer ist nicht mehr beschränkt.
* **Der Schalter-Anfangszustand wird nur für „aus“ und „an“ geprüft;** ein Schalter, dessen Zustand sich zwischen den Tagen unbemerkt ändert, ist nicht modelliert.
* **Mehrere Zähler brauchen die Tagesnummer.** Ohne sie bleiben das Standardprotokoll und die doppelten Marken. Die Rücksetzung braucht sie auch.
* **Die Phasenlängen sind eine Faustformel,** bei n = 100 abgestimmt; bei kleinem n (zum Beispiel n = 10) ist ein Zähler schneller als mehrere. Optimale Längen sind nicht berechnet.
* **Fehlertoleranz fehlt.** Eine einzige vergessene Marke oder ein falscher Handgriff kann die Erhaltung verletzen.
* **Die Breitensuche** (alle Besuchsfolgen) läuft nur für kleine n; für n = 100 gilt das Sicherheitsargument, nicht die Aufzählung. Die exakte Rechnung reicht bis n = 6.
* **Ein Modell,** keine Aussage über Menschen oder Gefängnisse.

## Verifikation

- **Kern:** Regeln einzeln gegen Handrechnung (n = 2, n = 3, n = 4 mit zwei Zählern, Phasengrenzen), skalare gegen vektorisierte Simulation Lauf für Lauf, zweite Fassung der Regeln im Test, Randfälle (n = 2, t an der Grenze n // 2, Phasengrenzen inklusive, Regler an den Grenzen).
- **Orakel:** `tests/test_oracle_gluehbirne.py`: Formel gegen unabhängige Markov-Kette und Bruchrechnung, Weiterschieben über alle Zustände gegen die Simulation, Sammelproblem, exakte Fehlerwahrscheinlichkeit, kürzestes Gegenbeispiel, Breitensuche über alle Besuchsfolgen.
- **Eigenschaften:** Erhaltung und Vorzeichen der Stände an jedem Tag für gleichverteilte und bösartige Besuchsfolgen; keine falsche Meldung für die sicheren Varianten; das naive Protokoll scheitert nachweislich (Zweig-Test).
- **Messungen:** `tests/test_claims.py` rechnet jede Zahl dieses READMEs nach.
- **Oberfläche:** AppTest-Rauchtest, Eckfälle, Permalink, Experimente nach Klick, PDF; Layout und Footer.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `glb_protocol.py` | Kern: Regeln der Protokolle (Marken, Talente, Phasen), Formeln |
| `glb_simulation.py` | Simulation: skalar Tag für Tag und vektorisiert über viele Läufe |
| `glb_exact.py` | Exakte Rechnung für kleine n, Breitensuche über alle Besuchsfolgen |
| `glb_evaluation.py` | Kennzahlen, Verdikte (reine Funktionen), Experimente |
| `glb_measure.py` | Messreihen für README und Tests (feste Seeds) |
| `glb_visualization.py` | Plotly-Abbildungen (Achsen gesperrt), Tag-für-Tag-Tabelle |
| `glb_pdf_export.py` | PDF-Export (fpdf2), erst nach Klick |
| `glb_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `glb_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `glb_layout.py` | Fester Kopf (Stylesheet) |
| `glb_rng.py` | SplitMix64, wörtliche Kopie aus `ab-test-demo` |
| `tools/make_measurements.py` | schreibt `data/measurements.json` |
| `data/measurements.json` | die Messreihen der Befunde |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Tests: siehe Verifikation |

## Bewusst nicht umgesetzt

* **Schneeball-Vorphase** (dynamische Wahl des Zählers, bei Majerech beschrieben) und mehrere Schneebälle: nicht gebaut, daher keine Aussage über ihren Gewinn.
* **Bessere Protokolle für den Fall ohne Tagesnummer** als die doppelten Marken (Majerech beschreibt eine Variante mit Wartezustand); nicht gebaut.
* **Schalter mit mehr als zwei Zuständen** oder mehrere Schalter: ein anderes Rätsel.
* **Optimierung der Phasenlängen** über die Faustformel hinaus.
* **Fehlertolerante Protokolle** und Besucherfolgen, die nicht gleichverteilt sind (nur die Sicherheit wird dafür geprüft, nicht die Dauer).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Teamrätsel: Strategie ohne Verständigung](https://sebastianhanisch.net/konzepte-teamraetsel.html).
