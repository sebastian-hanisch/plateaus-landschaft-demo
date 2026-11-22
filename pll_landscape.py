"""Landschaft mit Gleichständen: Neutralitätsgrad, Plateaus, drei Zählweisen des Optimums (nur numpy).

Eine Landschaft ist ein Paar (V, nbi): V sind ganzzahlige Werte (KLEINER ist besser; beim Maximieren wird V = -Fitness gesetzt),
nbi ist die Matrix der Nachbarn (Zeile = Zustand, Spalte = Zug in fester Zugreihenfolge). Die Nachbarschaft ist symmetrisch.
Zähleinheit aller Kennzahlen ist der ZUSTAND (bei ν das geordnete Nachbarpaar).

Begriffe:
* Neutralitätsgrad ν: Anteil der geordneten Nachbarpaare (x, y) mit V(x) = V(y).
* Plateau: Zusammenhangskomponente der Gleichheitskanten mit mindestens zwei Zuständen.
* schwaches Optimum: kein Nachbar strikt besser. Strenges Optimum: alle Nachbarn strikt schlechter.
* geschlossenes Plateau: Komponente (auch ein einzelner Zustand), in der kein Zustand einen strikt besseren Nachbarn hat.
* Scheinoptimum: schwaches Optimum, dessen Komponente einen Ausgang hat (ein Zustand mit strikt besserem Nachbarn).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Kennzahlen:
    zustaende: int
    zuege: int                 # M, Nachbarn je Zustand
    paare: int                 # geordnete Nachbarpaare S * M
    gleiche_paare: int
    mit_gleichem_nachbarn: int  # Zustände mit mindestens einem gleich guten Nachbarn
    schwach: int
    streng: int
    geschlossen: int           # geschlossene Plateaus (Komponenten ohne Ausgang, auch einzelne Zustände)
    plateaus: int              # Komponenten mit mindestens zwei Zuständen
    groesstes_plateau: int     # Zustände im größten Plateau (0, wenn es keines gibt)
    scheinoptima: int
    globale_optima: int        # Zustände mit dem besten Wert

    @property
    def nu(self) -> float:
        return self.gleiche_paare / self.paare if self.paare else 0.0

    @property
    def anteil_mit_gleichem(self) -> float:
        return self.mit_gleichem_nachbarn / self.zustaende

    @property
    def anteil_groesstes(self) -> float:
        return self.groesstes_plateau / self.zustaende

    @property
    def anteil_schein(self) -> float:
        """Anteil der Scheinoptima an den schwachen Optima."""
        return self.scheinoptima / self.schwach if self.schwach else 0.0

    @property
    def faktor(self) -> float:
        """Schwache Optima je geschlossenem Plateau (mindestens 1: jedes geschlossene Plateau enthält ein schwaches Optimum)."""
        return self.schwach / self.geschlossen if self.geschlossen else 0.0


def masken(V: np.ndarray, nbi: np.ndarray) -> dict:
    """Je Zustand: gleich gute Nachbarn (Matrix), hat gleich guten, hat strikt besseren Nachbarn."""
    V = np.asarray(V)
    if nbi.shape[1] == 0:
        leer = np.zeros(len(V), dtype=bool)
        return {"gleich": np.zeros(nbi.shape, dtype=bool), "hat_gleich": leer, "hat_besser": leer.copy()}
    nbv = V[nbi]
    gleich = nbv == V[:, None]
    return {"gleich": gleich, "hat_gleich": gleich.any(1), "hat_besser": (nbv < V[:, None]).any(1)}


def komponenten(V: np.ndarray, nbi: np.ndarray) -> np.ndarray:
    """Marke je Zustand = kleinster Zustandsindex seiner Komponente der Gleichheitskanten (Ausbreitung der kleinsten Marke)."""
    S = len(V)
    marke = np.arange(S)
    if nbi.shape[1] == 0:
        return marke
    gleich = V[nbi] == np.asarray(V)[:, None]
    if not gleich.any():
        return marke
    for _ in range(S + 1):
        kandidat = np.where(gleich, marke[nbi], S).min(1)
        neu = np.minimum(marke, kandidat)
        neu = neu[neu]  # Abkürzung: die Marke der Marke liegt in derselben Komponente und ist nicht größer
        if np.array_equal(neu, marke):
            break
        marke = neu
    return marke


def einteilung(V: np.ndarray, nbi: np.ndarray) -> dict:
    """Masken je Zustand: schwach, streng, Scheinoptimum, Marke der Komponente, Komponente hat Ausgang, Größe der Komponente."""
    V = np.asarray(V)
    S = len(V)
    m = masken(V, nbi)
    marke = komponenten(V, nbi)
    ausgang = np.bincount(marke, weights=m["hat_besser"].astype(float), minlength=S) > 0
    groesse = np.bincount(marke, minlength=S)
    schwach = ~m["hat_besser"]
    return {
        "schwach": schwach, "streng": schwach & ~m["hat_gleich"], "schein": schwach & ausgang[marke], "marke": marke,
        "ausgang": ausgang[marke], "groesse": groesse[marke], "gleich": m["gleich"], "hat_gleich": m["hat_gleich"],
        "hat_besser": m["hat_besser"],
    }


def plateaugroessen(V: np.ndarray, nbi: np.ndarray) -> np.ndarray:
    """Größen aller Plateaus (Komponenten mit mindestens zwei Zuständen), absteigend sortiert."""
    g = np.bincount(komponenten(V, nbi), minlength=len(V))
    return np.sort(g[g >= 2])[::-1]


def kennzahlen(V: np.ndarray, nbi: np.ndarray) -> Kennzahlen:
    V = np.asarray(V)
    S, M = nbi.shape
    e = einteilung(V, nbi)
    wurzel = e["marke"] == np.arange(S)
    groesse = np.bincount(e["marke"], minlength=S)
    plateau = groesse >= 2
    return Kennzahlen(
        zustaende=S, zuege=M, paare=S * M, gleiche_paare=int(e["gleich"].sum()), mit_gleichem_nachbarn=int(e["hat_gleich"].sum()),
        schwach=int(e["schwach"].sum()), streng=int(e["streng"].sum()), geschlossen=int((wurzel & ~e["ausgang"]).sum()),
        plateaus=int(plateau.sum()), groesstes_plateau=int(groesse.max()) if plateau.any() else 0,
        scheinoptima=int(e["schein"].sum()), globale_optima=int((V == V.min()).sum()),
    )
