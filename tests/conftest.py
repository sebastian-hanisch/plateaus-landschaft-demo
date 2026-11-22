"""Gemeinsame Hilfen der Tests: Importpfad, unabhängige Referenzrechnungen (Schleifen und Brüche) für die Mini-Instanzen."""

import sys
from fractions import Fraction as Fr
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def ref_analyse(F, nbrs):
    """Unabhängige Zählung (Maximieren von F) mit Schleifen und Union-Find; Rückgabe als Wörterbuch mit Brüchen und Listen."""
    S = len(F)
    paare = [(x, y) for x in range(S) for y in nbrs[x]]
    gleich = [(x, y) for (x, y) in paare if F[x] == F[y]]
    besser = [[y for y in nbrs[x] if F[y] > F[x]] for x in range(S)]
    schwach = [x for x in range(S) if not besser[x]]
    streng = [x for x in schwach if all(F[y] < F[x] for y in nbrs[x])]
    comp = list(range(S))

    def find(a):
        while comp[a] != a:
            comp[a] = comp[comp[a]]
            a = comp[a]
        return a

    for x, y in gleich:
        comp[find(x)] = find(y)
    gruppen = {}
    for x in range(S):
        gruppen.setdefault(find(x), []).append(x)
    ausgang = {g: any(besser[x] for x in xs) for g, xs in gruppen.items()}
    return {
        "nu": Fr(len(gleich), len(paare)) if paare else Fr(0), "gleiche_paare": len(gleich), "schwach": schwach, "streng": streng,
        "geschlossen": sorted(sorted(xs) for g, xs in gruppen.items() if not ausgang[g]),
        "plateaus": sorted(sorted(xs) for xs in gruppen.values() if len(xs) >= 2),
        "schein": [x for x in schwach if ausgang[find(x)]],
        "mit_gleichem": sorted({x for x, _ in gleich}),
    }


def ref_regeln(F, nbrs, seit):
    """Unabhängige Rekursion über ALLE Zufallsentscheidungen mit Brüchen (Maximieren von F): Erfolg und Durchsuchungen je Regel."""
    S = len(F)
    top = max(F)
    besser = [[y for y in nbrs[x] if F[y] > F[x]] for x in range(S)]

    def beste(x):
        m = max(F[y] for y in besser[x])
        return [y for y in nbrs[x] if F[y] == m]

    def r0(x):
        if not besser[x]:
            return (Fr(1 if F[x] == top else 0), Fr(1))
        p, c = r0(beste(x)[0])
        return (p, 1 + c)

    def r1(x):
        if not besser[x]:
            return (Fr(1 if F[x] == top else 0), Fr(1))
        ps = [r1(y) for y in beste(x)]
        return (sum(p for p, _ in ps) / len(ps), 1 + sum(c for _, c in ps) / len(ps))

    memo = {}

    def r2(x, k):
        if (x, k) in memo:
            return memo[(x, k)]
        if besser[x]:
            ps = [r2(y, 0) for y in beste(x)]
            out = (sum(p for p, _ in ps) / len(ps), 1 + sum(c for _, c in ps) / len(ps))
        else:
            eqs = [y for y in nbrs[x] if F[y] == F[x]]
            if eqs and k < seit:
                ps = [r2(y, k + 1) for y in eqs]
                out = (sum(p for p, _ in ps) / len(ps), 1 + sum(c for _, c in ps) / len(ps))
            else:
                out = (Fr(1 if F[x] == top else 0), Fr(1))
        memo[(x, k)] = out
        return out

    out = {}
    for name, fn in (("R0", r0), ("R1", r1), ("R2", lambda x: r2(x, 0))):
        res = [fn(x) for x in range(S)]
        out[name] = (sum(p for p, _ in res) / S, sum(c for _, c in res) / S)
    return out


def bit_nbrs(n):
    return [[s ^ (1 << i) for i in range(n)] for s in range(1 << n)]


@pytest.fixture
def h1():
    """Würfel des Handbeispiels: Werte der Zustände 000 … 111 (Maximieren), Nachbarn Bit 0, 1, 2 umgedreht."""
    return [2, 2, 1, 4, 2, 0, 3, 2], bit_nbrs(3)
