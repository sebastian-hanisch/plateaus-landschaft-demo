"""Plotly-Figuren (alle Achsen fest, damit Touch-Scrollen nicht am Diagramm hängen bleibt)."""

import numpy as np
import plotly.graph_objects as go

import pll_constants as C

_FEST = dict(fixedrange=True)
_RAND = dict(l=10, r=10, t=40, b=10)


def _layout(fig, titel, hoehe=340, **extra):
    fig.update_layout(title=titel, height=hoehe, margin=_RAND, legend=dict(orientation="h", y=-0.2), **extra)
    fig.update_xaxes(**_FEST)
    fig.update_yaxes(**_FEST)
    return fig


def build_wuerfel(werte, einteilung: dict):
    """Würfel als Graph: Knoten = Zustand mit Wert, dicke Kanten = gleich gute Nachbarn; Farbe nach Rolle des Zustands."""
    pos = {s: (((s >> 0) & 1) + 0.45 * ((s >> 2) & 1), ((s >> 1) & 1) + 0.35 * ((s >> 2) & 1)) for s in range(8)}
    fig = go.Figure()
    for s in range(8):
        for bit in range(3):
            t = s ^ (1 << bit)
            if t < s:
                continue
            gleich = werte[s] == werte[t]
            fig.add_trace(go.Scatter(x=[pos[s][0], pos[t][0]], y=[pos[s][1], pos[t][1]], mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(width=6 if gleich else 1.5, color=C.COLOR_PLATEAU if gleich else "rgba(120,120,120,0.6)")))
    gruppen = (("strenges Optimum", C.COLOR_STRENG, einteilung["streng"]),
               ("Scheinoptimum", C.COLOR_SCHEIN, einteilung["schein"]),
               ("schwaches Optimum auf geschlossenem Plateau", "#7a4fa3", einteilung["schwach"] & ~einteilung["streng"] & ~einteilung["schein"]),
               ("übrige Zustände", C.COLOR_SONST, ~einteilung["schwach"]))
    for name, farbe, maske in gruppen:
        idx = [s for s in range(8) if maske[s]]
        if not idx:
            continue
        fig.add_trace(go.Scatter(x=[pos[s][0] for s in idx], y=[pos[s][1] for s in idx], mode="markers", name=name, hoverinfo="skip",
                                 marker=dict(size=34, color=farbe, line=dict(width=1, color="white"))))
    for s in range(8):
        fig.add_annotation(x=pos[s][0], y=pos[s][1], text=f"<b>{werte[s]}</b>", showarrow=False, font=dict(color="white", size=14))
        fig.add_annotation(x=pos[s][0], y=pos[s][1] - 0.17, text=format(s, "03b"), showarrow=False, font=dict(size=11), bgcolor="rgba(255,255,255,0.88)")
    _layout(fig, "Würfel: Wert je Zustand, dicke Kanten = gleich gute Nachbarn", 380)
    fig.update_xaxes(visible=False, range=[-0.25, 1.7])
    fig.update_yaxes(visible=False, range=[-0.35, 1.6])
    return fig


def build_zaehlweisen(kenn):
    namen = ["schwache Optima", "strenge Optima", "geschlossene Plateaus"]
    zahlen = [kenn.schwach, kenn.streng, kenn.geschlossen]
    fig = go.Figure(go.Bar(x=namen, y=zahlen, text=[str(z) for z in zahlen], textposition="outside", cliponaxis=False,
                           marker_color=[C.COLOR_SCHEIN, C.COLOR_STRENG, C.COLOR_LINE], hoverinfo="skip"))
    _layout(fig, "Was zählt als Optimum? Drei Zählweisen derselben Landschaft", 340)
    fig.update_yaxes(title="Anzahl", rangemode="tozero")
    return fig


def build_plateaus(groessen: np.ndarray):
    """Verteilung der Plateaugrößen in Klassen (2, 3 bis 4, 5 bis 8, …)."""
    fig = go.Figure()
    if len(groessen):
        grenzen = [2]
        while grenzen[-1] <= int(groessen.max()):
            grenzen.append(grenzen[-1] * 2 - 1 if grenzen[-1] == 2 else (grenzen[-1] - 1) * 2 + 1)
        namen, zahlen = [], []
        for lo, hi in zip(grenzen, grenzen[1:]):
            namen.append(str(lo) if hi - 1 == lo else f"{lo} bis {hi - 1}")
            zahlen.append(int(((groessen >= lo) & (groessen < hi)).sum()))
        fig.add_trace(go.Bar(x=namen, y=zahlen, marker_color=C.COLOR_PLATEAU, text=[str(z) for z in zahlen], textposition="outside", cliponaxis=False, hoverinfo="skip"))
    _layout(fig, "Plateaus nach Größe (Zustände je Plateau)", 340)
    fig.update_xaxes(title="Zustände im Plateau", type="category")
    fig.update_yaxes(title="Anzahl Plateaus", rangemode="tozero")
    return fig


def build_stufen(zeilen: dict):
    stufen = sorted(zeilen)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[str(s) for s in stufen], y=[zeilen[s]["nu"] for s in stufen], mode="lines+markers", name="Neutralitätsgrad ν", line=dict(color=C.COLOR_LINE)))
    fig.add_trace(go.Scatter(x=[str(s) for s in stufen], y=[zeilen[s]["anteil_mit_gleichem"] for s in stufen], mode="lines+markers",
                             name="Anteil der Zustände mit gleich gutem Nachbarn", line=dict(color=C.COLOR_SCHEIN, dash="dot")))
    _layout(fig, "NK-Modell (N = 14, K = 4): Neutralität gegen Stufen je Beitrag, Mittel über 30 Instanzen", 360)
    fig.update_xaxes(title="Stufen je Beitrag", type="category")
    fig.update_yaxes(title="Anteil", range=[0, 1.05])
    return fig


def build_regeln(regeln: dict):
    namen = list(regeln)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=namen, y=[regeln[r]["erfolg"] for r in namen], name="Erfolg eines Abstiegs", marker_color=[C.COLOR_R[r] for r in namen],
                         text=[f"{regeln[r]['erfolg']:.3f}".replace(".", ",") for r in namen], textposition="outside", cliponaxis=False, hoverinfo="skip"))
    _layout(fig, "Erfolg eines Abstiegs je Gleichstandsregel (exakt)", 340, showlegend=False)
    fig.update_yaxes(title="Anteil der Starts, die im globalen Optimum enden", range=[0, 1.12])
    return fig


def build_treffer(regeln: dict):
    namen = list(regeln)
    fig = go.Figure(go.Bar(x=namen, y=[regeln[r]["treffer_je_1000"] for r in namen], marker_color=[C.COLOR_R[r] for r in namen],
                           text=[f"{regeln[r]['treffer_je_1000']:.2f}".replace(".", ",") for r in namen], textposition="outside", cliponaxis=False, hoverinfo="skip"))
    _layout(fig, "Treffer je 1 000 Auswertungen (exakt)", 340, showlegend=False)
    fig.update_yaxes(title="Treffer je 1 000 Auswertungen", rangemode="tozero")
    return fig


def build_budget(zellen: dict):
    """Mittlere Lücke gegen Budget, je K eine Linie für R0 (durchgezogen) und R2 (gestrichelt)."""
    fig = go.Figure()
    farben = {2: "#4c78a8", 4: "#2F6B65", 8: "#d9822b"}
    for k in sorted(zellen):
        x = [str(z["budget"]) for z in zellen[k]]
        fig.add_trace(go.Scatter(x=x, y=[z["luecke_R0"] for z in zellen[k]], mode="lines+markers", name=f"K = {k}, R0", line=dict(color=farben.get(k, C.COLOR_LINE))))
        fig.add_trace(go.Scatter(x=x, y=[z["luecke_R2"] for z in zellen[k]], mode="lines+markers", name=f"K = {k}, R2", line=dict(color=farben.get(k, C.COLOR_LINE), dash="dash")))
    _layout(fig, "NK-Modell (N = 14, 3 Stufen): mittlere Lücke bei festem Budget", 380)
    fig.update_xaxes(title="Budget in Auswertungen", type="category")
    fig.update_yaxes(title="Lücke zum Optimum in %", rangemode="tozero")
    return fig
