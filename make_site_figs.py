"""Site figures: black line art on a transparent background, x markers, unfilled (hatched) bars.
Every number is read from a committed result file; nothing is typed in by hand.
Run: python make_site_figs.py  -> assets/f_*.svg"""
import json, os, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

H = Path.home()
GE = H / "certinter/grid-engine/results"
CS = H / "cluster-screen"
CC = H / "cluster-certify/results"
PQ = H / "certinter/pjm-queue-data/results/pjm_queue_stats.json"
OUT = Path(__file__).resolve().parent / "assets"
K = "#111111"
plt.rcParams.update({
    "font.family": "DejaVu Sans Mono", "font.size": 9.5, "text.color": K, "axes.labelcolor": K,
    "axes.edgecolor": K, "xtick.color": K, "ytick.color": K, "axes.linewidth": 0.9,
    "axes.facecolor": "none", "figure.facecolor": "none", "savefig.transparent": True,
    "axes.spines.top": False, "axes.spines.right": False, "hatch.color": K, "hatch.linewidth": 0.6,
    "legend.frameon": False, "svg.fonttype": "none"})
J = lambda p: json.load(open(p))
HATCH = ["", "////", "xxxx", "....", "\\\\\\\\"]


def bars(ax, x, h, i=0, w=0.38, label=None, err=None):
    ax.bar(x, h, w, fill=False, edgecolor=K, linewidth=1.0, hatch=HATCH[i], label=label)
    if err is not None:
        ax.errorbar(x, h, yerr=err, fmt="none", ecolor=K, elinewidth=0.9, capsize=3)


MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)
    t = (OUT / f"{name}.svg").read_text(encoding="utf-8")
    t = re.sub(r"font-family:[^;\"]*", "font-family:" + MONO, t)
    t = re.sub(r'font-family="[^"]*"', 'font-family="' + MONO.replace('"', "'") + '"', t)
    (OUT / f"{name}.svg").write_text(t, encoding="utf-8")
    print("wrote", name)


def boot(f, *a, B=2000, seed=0):
    r = np.random.default_rng(seed); n = len(a[0]); v = []
    for _ in range(B):
        i = r.integers(0, n, n); v.append(f(*[x[i] for x in a]))
    return np.percentile(v, [2.5, 97.5])


# 1. PJM queue: what happened to requests submitted 2008-2017, and how long the survivors took
q = J(PQ)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
s = q["submitted_2008_2017"]
vals = [100 * s["share_requests_in_service"], 100 * s["share_requests_withdrawn"], 100 * (1 - s["share_requests_in_service"] - s["share_requests_withdrawn"])]
bars(ax[0], [0, 1, 2], vals, 0, 0.55)
for x, v in zip([0, 1, 2], vals):
    ax[0].text(x, v + 2, f"{v:.0f}%", ha="center")
ax[0].set_xticks([0, 1, 2], ["in service", "withdrew", "other"]); ax[0].set_ylabel("% of requests")
ax[0].set_title(f"PJM requests submitted 2008-2017 (n = {s['n']:,})", fontsize=9.5)
yrs = {int(k): v for k, v in q["years_to_in_service_median_by_submit_year"].items() if int(k) >= 2003}
ax[1].plot(list(yrs), list(yrs.values()), color=K, lw=1.2, marker="x", ms=6)
ax[1].set_xlabel("year submitted"); ax[1].xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True)); ax[1].set_ylabel("median years to service")
ax[1].set_title("survivors: time from request to service", fontsize=9.5)
save(fig, "f_pjm")

# 2. Engine vs independent solver: worst voltage difference per grid (log)
names = dict(case30="IEEE 30", case118="IEEE 118", case_ACTIVSg200="Illinois 200", case300="IEEE 300",
             case_ACTIVSg500="SC 500", case_ACTIVSg2000="Texas 2000")
fig, ax = plt.subplots(figsize=(9, 3.3))
labels, n_all = [], []
for i, c in enumerate(names):
    d = J(GE / f"validate_pypower_{c}.json"); w = []; n = 0
    for v in d["seasons"].values():
        for x in v.values():
            n += x["compared"]
            if x["max_dv"]:
                w.append(x["max_dv"]["1.0"])
    ax.plot([i] * len(w), w, "x", color=K, ms=6)
    labels.append(f"{names[c]}\n{n:,} cases"); n_all.append(n)
ax.set_yscale("log"); ax.set_ylim(1e-16, 1e-6)
ax.axhline(1e-10, color=K, lw=0.8, ls="--"); ax.text(5.45, 1.4e-10, "1e-10 pu", ha="right", va="bottom", fontsize=8.5)
ax.set_xticks(range(len(labels)), labels, fontsize=8.5)
ax.set_ylabel("worst |V difference| (pu)")
ax.set_title(f"grid-engine vs PYPOWER (MATPOWER port): every season and outage set, {sum(n_all):,} cases; each x = one season x set", fontsize=9)
save(fig, "f_validation")

# 3. DC vs AC: share of AC-insecure cases the linear check calls secure
fig, ax = plt.subplots(figsize=(9, 3.3))
rows = []
for c in ["case300", "case_ACTIVSg2000"]:
    d = J(GE / f"validate_{c}.json")["B_dc_vs_ac"]
    for s in ["summer_peak", "winter_peak"]:
        for k in ["P1", "P7", "N2"]:
            x = d[s].get(k)
            if x and x["n"] - x["ac_secure"] >= 5:
                rows.append((f"{names[c]}\n{s.split('_')[0]} {k}", x["n"] - x["ac_secure"], x["dc_secure_ac_insecure"]))
xs = np.arange(len(rows))
bars(ax, xs - 0.2, [r[1] for r in rows], 0, label="AC insecure")
bars(ax, xs + 0.2, [r[2] for r in rows], 1, label="of those, DC says secure")
for x, r in zip(xs, rows):
    ax.text(x + 0.2, r[2] + 1, f"{100 * r[2] / r[1]:.0f}%", ha="center", fontsize=8)
ax.set_xticks(xs, [r[0] for r in rows], fontsize=8); ax.set_ylabel("outage cases"); ax.legend(loc="upper right")
ax.set_title("the linear (DC) check misses many unsafe outages, mostly voltage problems it cannot see", fontsize=9.5)
save(fig, "f_dc_vs_ac")

# 4. Speed
fig, ax = plt.subplots(figsize=(9, 3.2))
cs = ["case118", "case300", "case_ACTIVSg2000"]
pg = [J(GE / f"bench_{c}.json")["seasons"]["summer_peak"]["P1"]["ms_per_case"] for c in cs]
pd_ = [J(GE / f"bench_{c}.json")["pandapower_loop"]["ms_per_case"] for c in cs]
xs = np.arange(3)
bars(ax, xs - 0.2, pd_, 1, label="pandapower loop")
bars(ax, xs + 0.2, pg, 0, label="Power Grid Model batch")
ax.set_yscale("log"); ax.set_ylim(0.5, 3000); ax.set_xticks(xs, [names[c] for c in cs]); ax.set_ylabel("ms per outage case"); ax.legend(fontsize=8, loc="upper left", ncol=2)
for x, a_, b_ in zip(xs, pd_, pg):
    ax.text(x + 0.2, b_ * 1.3, f"{a_ / b_:.0f}x faster", ha="center", fontsize=8.5)
save(fig, "f_speed")

# 5. Capacity lost to outages, per season (IEEE 118)
C = J(GE / "capacity_case118.json"); CQ = J(GE / "capacity_case118_qlim.json")
fig, ax = plt.subplots(1, 2, figsize=(9, 3.3), sharey=True)
seas = ["summer_peak", "winter_peak", "light_load"]
for a, kind, title in zip(ax, ["gen", "load"], ["new generation", "new load (e.g. a data center)"]):
    for j, (R, lab) in enumerate([(C, "reactive limits off"), (CQ, "reactive limits on")]):
        med, lo, hi = [], [], []
        for s in seas:
            m = [x for x in R["map"] if x["kind"] == kind and x["season"] == s]
            n0 = np.array([x["N0"]["mw"] for x in m]); p1 = np.array([x["P1"]["mw"] for x in m]); ok = n0 > 1e-6
            loss = 100 * (1 - p1[ok] / n0[ok]); b = boot(np.median, loss)
            med.append(np.median(loss)); lo.append(np.median(loss) - b[0]); hi.append(b[1] - np.median(loss))
        bars(a, np.arange(3) + (j - 0.5) * 0.38, med, j, label=lab, err=[lo, hi])
    a.set_xticks(range(3), ["summer peak", "winter peak", "light load"]); a.set_title(title, fontsize=9.5)
ax[0].set_ylabel("median % of a bus's room lost\nto single outages (IEEE 118)"); ax[1].legend(fontsize=8)
save(fig, "f_capacity_seasons")

# 6. Cluster decisions (IEEE 118)
fig, ax = plt.subplots(figsize=(9, 3.3))
for j, cond in enumerate(["P1", "P1+P7"]):
    r = [x[cond] for x in C["clusters"]]
    fa = sum(x["fits_alone_mw"] for x in r); fc = sum(x["queue"]["mw"] for x in r)
    lf = sum(x["largest_first"]["mw"] for x in r); bs = sum(x["cluster"]["mw"] for x in r)
    bars(ax, np.arange(4) + (j - 0.5) * 0.38, [fa, fc, lf, bs], j, label="single outages (P1)" if cond == "P1" else "plus common-tower doubles (P7)")
ax.set_xticks(range(4), ["'fits alone' (sum)", "first come", "largest first", "best subset (exact)"])
ax.set_ylabel("total MW over 90 clusters"); ax.legend(fontsize=8)
ax.set_title("deciding as a cluster: same requests, every answer AC-checked", fontsize=9.5)
save(fig, "f_clusters")

# 7. Linear decisions vs AC truth
B = J(GE / "baselines_case118.json")
fig, ax = plt.subplots(figsize=(9, 3.2))
vals, errs, labs = [], [], []
for cond in ["P1", "P1+P7"]:
    r = [x[cond] for x in B["clusters"]]; k = sum(not x["dc_pick_ac_secure"] for x in r); n = len(r)
    vals.append(100 * k / n); labs.append(f"90 clusters\n{cond}")
s5 = J(CC / "s5v2_certify_case118.json"); vals.append(100 * s5["n_insecure"] / s5["n"]); labs.append(f"{s5['n']:,} clusters\nP1")
bars(ax, range(3), vals, 1, 0.5)
for x, v in enumerate(vals):
    ax.text(x, v + 0.6, f"{v:.1f}%", ha="center")
ax.set_xticks(range(3), labs); ax.set_ylabel("% of linear picks\nthat fail full AC"); ax.set_ylim(0, max(vals) * 1.3)
save(fig, "f_dc_pick")

# 8. Ways to make room
O = J(GE / "options_case118.json"); plain = np.array([x["plain"]["mw"] for x in O["clusters"]])
lab = dict(ras_gen_0="trip generation after an outage", partial="connect at partial size", flex_load_0="flexible load (drops to 0)",
           flex_load_50="flexible load (keeps 50%)", storage_25="battery at load (25%)", switch="open one line")
fig, ax = plt.subplots(figsize=(9, 3.3))
keys = [k for k in lab if k in O["summary"]["options"]]
g = []; e = []
for k in keys:
    mw = np.array([x["options"][k]["mw"] for x in O["clusters"]]); v = mw.sum() - plain.sum(); b = boot(lambda a, c: a.sum() - c.sum(), mw, plain)
    g.append(v); e.append([v - b[0], b[1] - v])
y = np.arange(len(keys))
ax.barh(y, g, 0.55, fill=False, edgecolor=K, hatch="////", xerr=np.array(e).T, error_kw=dict(ecolor=K, capsize=3, lw=0.9))
ax.set_yticks(y, [lab[k] for k in keys]); ax.invert_yaxis(); ax.set_xlabel(f"extra MW over the best plain subset ({O['summary']['plain_mw']:,.0f} MW), 90 clusters, IEEE 118")
save(fig, "f_options")

# 9. PJM timelines by fuel
T = J(GE / "timelines_pjm.json")["service"]["by_fuel"]
f = sorted([(k, v) for k, v in T.items() if not v.get("small_sample") and v["n"] >= 30], key=lambda kv: kv[1]["median"])
fig, ax = plt.subplots(figsize=(9, 3.2))
for i, (k, v) in enumerate(f):
    ax.plot([v["p25"], v["p75"]], [i, i], color=K, lw=1.2); ax.plot(v["median"], i, "x", color=K, ms=8, mew=1.6)
ax.set_yticks(range(len(f)), [f"{k} (n={v['n']})" for k, v in f]); ax.set_xlabel("years from queue entry to operation (x = median, line = 25th to 75th percentile)")
save(fig, "f_timelines")

# 10. Certify or defer: AC-insecure share by score quintile, and work per decision
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
qd = s5["insecure_rate_by_score_quintile"]
for j, (key, lab2) in enumerate([("dc", "DC margin"), ("ac_k10", "screened AC (10 worst outages)")]):
    if key in qd:
        r = [100 * b["rate"] for b in qd[key]]
        ax[0].plot(range(1, len(r) + 1), r, color=K, lw=1.2, ls="-" if j else "--", marker="x", ms=6, label=lab2)
ax[0].set_xticks(range(1, 6)); ax[0].set_xlabel("score quintile (1 = lowest margin)"); ax[0].set_ylabel("% of picks that fail full AC"); ax[0].legend(fontsize=8)
m = s5["main_split"]
ks = [k for k in ["dc", "ac_k5", "ac_k10", "ac_k20"] if k in m]
cert = [100 * m[k]["0.05"]["certified_share"] for k in ks]; sol = [m[k]["0.05"]["ac_solves_per_decision"] for k in ks]
bars(ax[1], np.arange(len(ks)) - 0.2, cert, 0, label="% certified (eps 5%)")
ax2 = ax[1].twinx(); ax2.spines["right"].set_visible(True)
ax2.plot(np.arange(len(ks)) + 0.2, sol, "x", color=K, ms=8, mew=1.6, label="AC solves per decision")
ax2.axhline(s5["full_check_solves"], color=K, ls=":", lw=0.9); ax2.set_ylabel("AC solves per decision (x)")
ax[1].set_xticks(range(len(ks)), ["DC margin", "AC top 5", "AC top 10", "AC top 20"]); ax[1].set_ylabel("% certified (bars)")
save(fig, "f_certify")

# 11. AI layer: error of the learned AC correction
fig, ax = plt.subplots(figsize=(9, 3.2))
rows = {"case30": {"DC (no model)": 0.399, }, }
txt = (CS / "RESULTS.md").read_text(encoding="utf-8")
res = {}
for case in ["case30", "case118"]:
    seg = txt[txt.index(f"### {case}\n"):]
    seg = seg[:seg.index("Joint feasibility")]
    d = {}
    for line in seg.splitlines():
        p = [c.strip() for c in line.strip("|").split("|")]
        if len(p) >= 2 and p[0] in ("DC (z = 0)", "deepsets", "settf", "opgraph"):
            d[p[0]] = float(p[1])
    res[case] = d
mods = ["DC (z = 0)", "deepsets", "settf", "opgraph"]; disp = ["linear (DC)", "DeepSets", "Set Transformer", "operator graph"]
for j, case in enumerate(["case30", "case118"]):
    bars(ax, np.arange(4) + (j - 0.5) * 0.38, [res[case][m_] for m_ in mods], j, label=names[case])
ax.set_xticks(range(4), disp); ax.set_ylabel("test RMSE of log(AC/DC capacity)"); ax.legend(fontsize=8)
save(fig, "f_ai")
