"""Capacity map of IEEE 118 in line style: every bus a circle whose size is the MW of new generation it can take,
unfilled black outline on a transparent background; a static SVG (summer, N-0 vs P1) and a GIF cycling seasons.
Reads grid-engine results/capacity_case118.json. Needs the grid-engine Python env (power_grid_model)."""
import json, sys
from pathlib import Path
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
sys.path.insert(0, str(Path.home() / "certinter/grid-engine"))
from gridengine import Engine, load_case

K, BG = "#111111", "#ebe8e1"
OUT = Path(__file__).resolve().parent / "assets"
R = json.load(open(Path.home() / "certinter/grid-engine/results/capacity_case118.json"))
eng = Engine(load_case("case118"))
G = nx.Graph([(b["f"], b["t"]) for b in eng.branches])
pos = nx.kamada_kawai_layout(G)
nodes = list(G.nodes)
plt.rcParams.update({"font.family": "monospace", "font.size": 9, "text.color": K})
SEAS = dict(summer_peak="summer peak", winter_peak="winter peak", light_load="light load")


def draw(ax, mw, title):
    ax.set_axis_off()
    for u, v in G.edges():
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=K, lw=0.45, alpha=0.55, zorder=1)
    s = np.array([mw.get(n, 0.0) for n in nodes])
    ax.scatter([pos[n][0] for n in nodes], [pos[n][1] for n in nodes], s=8 + 1.1 * s, facecolors=BG, edgecolors=K, linewidths=0.9, zorder=2)
    zero = [n for n in nodes if mw.get(n, 0.0) <= 1e-6]
    ax.scatter([pos[n][0] for n in zero], [pos[n][1] for n in zero], marker="x", s=22, color=K, linewidths=1.0, zorder=3)
    ax.set_title(title, fontsize=9.5)


def legend(ax):
    for mw, y in ((50, 0.13), (150, 0.08), (300, 0.02)):
        ax.scatter([0.03], [y], s=8 + 1.1 * mw, facecolors=BG, edgecolors=K, linewidths=0.9, transform=ax.transAxes, clip_on=False)
        ax.text(0.07, y, f"{mw} MW", transform=ax.transAxes, va="center", fontsize=8)
    ax.scatter([0.03], [-0.04], marker="x", s=22, color=K, transform=ax.transAxes, clip_on=False)
    ax.text(0.07, -0.04, "0 MW", transform=ax.transAxes, va="center", fontsize=8)


m = {(x["season"], x["kind"]): x for x in R["map"]}
fig, ax = plt.subplots(1, 2, figsize=(10, 5.2))
for a, k, t in zip(ax, ("N0", "P1"), ("no outages (N-0)", "every single-line outage (P1)")):
    mw = {x["bus"]: x[k]["mw"] for x in R["map"] if x["season"] == "summer_peak" and x["kind"] == "gen"}
    draw(a, mw, f"summer peak, {t}: median {np.median(list(mw.values())):.0f} MW")
legend(ax[0])
fig.suptitle("IEEE 118: how much new generation each bus can take (circle size = MW)", fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "f_capmap.svg", transparent=True); plt.close(fig)

for kind, what in (("gen", "new generation"), ("load", "new load")):
    fig, ax = plt.subplots(figsize=(7, 7.2)); fig.patch.set_facecolor(BG)
    w = PillowWriter(fps=0.9)
    with w.saving(fig, OUT / f"capmap_{kind}.gif", dpi=100):
        for s in SEAS:
            for k in ("N0", "P1"):
                ax.clear()
                mw = {x["bus"]: x[k]["mw"] for x in R["map"] if x["season"] == s and x["kind"] == kind}
                draw(ax, mw, f"IEEE 118: MW of {what} each bus can take\n{SEAS[s]}, {'no outages' if k == 'N0' else 'every single-line outage'}"
                              f"  (median {np.median(list(mw.values())):.0f} MW)")
                legend(ax); w.grab_frame(facecolor=BG)
    plt.close(fig)
print("maps done")
