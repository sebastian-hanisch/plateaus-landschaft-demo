"""Texte: App und README nennen dieselben Tabellen, Presets und Voraussetzungen; Hauswörter der Reihe; keine Gerüst-Reste."""

import re
from pathlib import Path

import pll_constants as C

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
QUELLEN = {p.name: p.read_text(encoding="utf-8") for p in list(ROOT.glob("*.py")) + [ROOT / "README.md"] if p.name not in ("pll_basis.py", "pll_rng.py")}


def test_erklaertabellen_der_app_stehen_woertlich_in_der_readme():
    for tabelle in (C.REGEL_TABELLE, C.ZAEHLWEISEN_TABELLE):
        for zeile in tabelle.strip().splitlines():
            assert zeile in README, zeile


def test_jedes_preset_steht_in_der_readme():
    for name in C.PRESETS:
        assert name in README, name


def test_keine_geruest_reste():
    for name, text in QUELLEN.items():
        assert "TODO" not in text, name
        assert "pll_algorithm" not in text, name


def test_hauswoerter_der_reihe():
    verboten = (r"\bBecken\b", r"Saatwert", r"\bSchwanz", r"\bträgt\b", r"\btragen\b", r"läuft lokal", r"strasse", r"\bReue\b", r"\boptimal\b")
    for name, text in QUELLEN.items():
        for muster in verboten:
            assert not re.search(muster, text), (name, muster)


def test_voraussetzungen_stehen_in_readme_und_app():
    app = QUELLEN["app.py"]
    for text in (README, app):
        assert "Zählweise „voll“" in text and "steilste" in text
    assert "Zufalls-Seed" in README and "Auswertung" in README and "erfunden" in README.lower()


def test_keine_verweise_auf_das_gestrichene_stueck_und_keine_fremden_verfahrensnamen():
    for name, text in QUELLEN.items():
        for wort in ("Stück 9", "Verlustlandschaft", "LKH", "EAX", "concorde", "ortools"):
            assert wort not in text, (name, wort)
