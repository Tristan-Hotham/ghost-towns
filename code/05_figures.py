"""Step 5. Figures for the paper (release/paper/f_*.png), the blog (release/blog/b_*.png) and the social card (header.png).
Run: python3 code/05_figures.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *

J, R, P = load()
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
RK = RKEYS
src = np.array([p[5] for p in P]); rea = np.array([p[3] for p in P])
lat = np.array([p[1] for p in P]); lon = np.array([p[2] for p in P])
X, Y = proj(lon, lat)


def both(fig, name, dpi=200):
    fig.savefig(f"{PAP}/f_{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    fig.savefig(f"{BLOG}/b_{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def legend_row(fig, y, keys=RK, x0=.04, fs=9.5, full=True):
    x = x0
    for k in keys:
        fig.patches.append(plt.Circle((x + .006, y), .0055, transform=fig.transFigure, fc=RCOL[k], ec="none"))
        t = fig.text(x + .016, y, RFULL[k] if full else RLAB[k], fontsize=fs, va="center", color=FG, family=SER)
        fig.canvas.draw(); bb = t.get_window_extent(); x = fig.transFigure.inverted().transform((bb.x1, 0))[0] + .022
    return x


# ---------- 1. world map ----------
def world(ax, s_unk=2.2, s_k=10, s_dmv=1.6):
    poly = outline(ax, fc=SEA, ec="#C2CCCE", lw=.8, lat_min=-58, lat_max=84)
    draw_land(ax)
    ax.add_collection(LineCollection(borders_world(), colors=BORDER, linewidths=.3, zorder=1.2))
    m = (src == 0) & (rea == RK.index("unknown")); ax.scatter(X[m], Y[m], s=s_unk, c=RCOL["unknown"], lw=0, alpha=.8, zorder=3)
    m = src == 1; ax.scatter(X[m], Y[m], s=s_dmv, c=RCOL["medieval"], lw=0, alpha=.85, zorder=3.1)
    for k in RK[:-1]:
        m = (src == 0) & (rea == RK.index(k)); ax.scatter(X[m], Y[m], s=s_k, c=RCOL[k], lw=.3, edgecolors=PAPER, zorder=4)
        m = (src == 3) & (rea == RK.index(k)); ax.scatter(X[m], Y[m], s=s_k * 1.6, c=RCOL[k], lw=.9, edgecolors=FG, zorder=4.5)
    x0, x1 = poly[:, 0].min(), poly[:, 0].max(); y0, y1 = poly[:, 1].min(), poly[:, 1].max()
    ax.set_xlim(x0 - 1e5, x1 + 1e5); ax.set_ylim(y0 - 1e5, y1 + 1e5); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 6.9), facecolor=BG)
ax = fig.add_axes([.01, .1, .98, .88]); ax.set_facecolor(BG); world(ax)
legend_row(fig, .07, RK[:4], x0=.03); legend_row(fig, .03, RK[4:], x0=.03)
both(fig, "world")

# ---------- 2. sources by country ----------
rows = [(c["country"], c["n"], c["by"]) for c in R["by_country_top"]]
rows.insert(1, ("England (Beresford)", R["n_dmv"], {**{k: 0 for k in RK}, "medieval": R["n_dmv"]}))
rows = rows[:13]
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
yy = np.arange(len(rows))[::-1]
for y_, (c, n, by) in zip(yy, rows):
    left = 0
    for k in RK[:-1] + ["unknown"]:
        v = by.get(k, 0)
        if v: ax.barh(y_, v, left=left, color=RCOL[k], height=.72); left += v
    ax.text(n + 25, y_, f"{n:,}", va="center", fontsize=10, color=FG)
ax.set_yticks(yy); ax.set_yticklabels([r[0] for r in rows], fontsize=10.5)
style(ax); ax.set_xlim(0, max(r[1] for r in rows) * 1.12)
ax.set_xlabel("Abandoned settlements (Wikidata ghost towns, and England's deserted medieval villages)", fontsize=10, color=MUT)
fig.subplots_adjust(left=.2, right=.97, top=.9, bottom=.2)
fig.text(.2, .955, "Where the record is: the United States and England dominate", fontproperties=DISPB, fontsize=15, color=FG, va="top")
legend_row(fig, .06, RK[:4], x0=.03, fs=9, full=False); legend_row(fig, .025, RK[4:], x0=.03, fs=9, full=False)
both(fig, "countries")

# ---------- 3. reasons by continent, Wikipedia list ----------
B = [b for b in R["wiki_by_cont"] if b["n"]]
fig, ax = plt.subplots(figsize=(10, 5.4), facecolor=BG); ax.set_facecolor(BG)
yy = np.arange(len(B))[::-1]
for y_, b in zip(yy, B):
    left = 0
    for k in RK:
        v = b["by"][k] / b["n"]
        if v: ax.barh(y_, v, left=left, color=RCOL[k], height=.7, alpha=.55 if k == "unknown" else 1); left += v
    ax.text(1.01, y_, f"{b['n']}", va="center", fontsize=10, color=FG)
ax.set_yticks(yy); ax.set_yticklabels([b["label"] for b in B], fontsize=10.5)
ax.set_xlim(0, 1.06); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
style(ax); ax.text(1.01, len(B) - .35, "places", fontsize=9, color=MUT)
fig.subplots_adjust(left=.17, right=.95, top=.86, bottom=.22)
fig.text(.17, .95, "Why places were abandoned, by continent", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.17, .9, "Share of entries in Wikipedia's 'List of ghost towns by country' by the reason its text gives", fontsize=9.5, color=MUT, va="top")
legend_row(fig, .085, RK[:4], x0=.03, fs=9, full=False); legend_row(fig, .04, RK[4:], x0=.03, fs=9, full=False)
both(fig, "continents")

# ---------- 4. US states ----------
S = sorted(R["us_west_states"], key=lambda s: -s["n"])
top = R["us_top_states"]
import pandas as pd
UST = pd.read_csv(f"{DATA}/us_states.csv").head(20)
fig, ax = plt.subplots(figsize=(10, 6.4), facecolor=BG); ax.set_facecolor(BG)
yy = np.arange(len(UST))[::-1]
for y_, r in zip(yy, UST.itertuples()):
    ax.barh(y_, r.ghost_towns, color="#C9C3B6" if not r.west else "#8E8676", height=.72)
    ax.barh(y_, r.mining, color=RCOL["mining"], height=.72)
    ax.text(r.ghost_towns + 3, y_, f"{r.ghost_towns}" + (f"  ({r.mining} mining)" if r.mining else ""), va="center", fontsize=9.5, color=FG)
ax.set_yticks(yy); ax.set_yticklabels([s + (" *" if w else "") for s, w in zip(UST.state, UST.west)], fontsize=10)
style(ax); ax.set_xlim(0, UST.ghost_towns.max() * 1.25)
fig.subplots_adjust(left=.17, right=.96, top=.88, bottom=.1)
fig.text(.17, .955, "Wikidata's ghost towns by US state", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.17, .91, "Darker bars and *: the 11 western states. Amber: tied to mining (text, class or a mining word in the name)", fontsize=9.3, color=MUT, va="top")
both(fig, "us_states")

# ---------- 5. England ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8), facecolor=BG, gridspec_kw={"width_ratios": [1.1, 1]})
for a in (a1, a2): a.set_facecolor(BG)
per = R["dmv_periods"]
a1.bar(range(len(per)), [p["n"] for p in per], color=RCOL["medieval"], width=.7)
for i, p in enumerate(per): a1.text(i, p["n"] + 2, p["n"], ha="center", fontsize=10, color=FG)
a1.set_xticks(range(len(per))); a1.set_xticklabels([p["period"].replace(" to ", "\nto ").replace(" onwards", "\nonwards") for p in per], fontsize=9)
style(a1, axis="y"); a1.set_title(f"Presumed date of desertion ({R['dmv_dated']} dated sites)", fontsize=10.5, color=FG, loc="left")
cs = R["dmv_counties"][:10]
a2.barh(range(len(cs))[::-1], [c["n"] for c in cs], color=RCOL["medieval"], height=.7)
for i, c in zip(range(len(cs))[::-1], cs): a2.text(c["n"] + 4, i, c["n"], va="center", fontsize=9.5, color=FG)
a2.set_yticks(range(len(cs))[::-1]); a2.set_yticklabels([c["county"] for c in cs], fontsize=9.5)
style(a2); a2.set_title("Sites by historic county", fontsize=10.5, color=FG, loc="left"); a2.set_xlim(0, cs[0]["n"] * 1.18)
fig.subplots_adjust(left=.06, right=.97, top=.8, bottom=.17, wspace=.45)
fig.text(.06, .96, f"England's {R['n_dmv']:,} deserted medieval villages and hamlets", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.06, .9, "Beresford's Lost Villages gazetteer (University of Hull), as cleaned for 'The Villages That Vanished'", fontsize=9.5, color=MUT, va="top")
both(fig, "england")

# ---------- 6. post-Soviet ----------
PS = R["ps_wiki_by_country"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.9), facecolor=BG, gridspec_kw={"width_ratios": [1.15, 1]})
for a in (a1, a2): a.set_facecolor(BG)
yy = np.arange(len(PS))[::-1]
for y_, c in zip(yy, PS):
    left = 0
    for k in RK:
        v = c["by"].get(k, 0)
        if v: a1.barh(y_, v, left=left, color=RCOL[k], height=.7, alpha=.55 if k == "unknown" else 1); left += v
a1.set_yticks(yy); a1.set_yticklabels([c["country"] for c in PS], fontsize=9.5); style(a1)
a1.set_title(f"Wikipedia's list: {R['ps_wiki_n']} places, by reason", fontsize=10.5, color=FG, loc="left")
W2 = R["ps_wd_by_country"]
a2.barh(range(len(W2))[::-1], [c["n"] for c in W2], color=RCOL["unknown"], height=.7)
for i, c in zip(range(len(W2))[::-1], W2): a2.text(c["n"] + .5, i, c["n"], va="center", fontsize=9.5)
a2.set_yticks(range(len(W2))[::-1]); a2.set_yticklabels([c["country"] for c in W2], fontsize=9.5); style(a2)
a2.set_title(f"Wikidata: {R['ps_wd_n']} ghost towns ({R['ps_wd_n'] - R['ps_wd_reason']['unknown']} with a reason)", fontsize=10.5, color=FG, loc="left")
fig.subplots_adjust(left=.12, right=.97, top=.8, bottom=.2, wspace=.4)
fig.text(.03, .96, "Soviet and post-Soviet abandonment", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.03, .9, "The 15 former Soviet republics in the two sources", fontsize=9.5, color=MUT, va="top")
legend_row(fig, .06, RK, x0=.03, fs=8.6, full=False)
both(fig, "soviet")

# ---------- 7. when ----------
TL = [t for t in R["timeline_century"] if 1000 <= t["century"] <= 2000]
TD = R["timeline_decade"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.9), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.25]})
for a in (a1, a2): a.set_facecolor(BG)
xs = np.arange(len(TL))
bot = np.zeros(len(TL))
v = np.array([t["dmv"] for t in TL]); a1.bar(xs, v, bottom=bot, color=RCOL["medieval"], width=.75, alpha=.55, hatch="///", ec=PAPER, lw=0); bot += v
for k in RK:
    v = np.array([t["wiki"][k] + t["wd"][k] for t in TL])
    a1.bar(xs, v, bottom=bot, color=RCOL[k], width=.75); bot += v
a1.set_xticks(xs); a1.set_xticklabels([f"{t['century']}s" for t in TL], rotation=90, fontsize=8.5); style(a1, axis="y")
a1.set_title("By century (hatched: England's dated deserted villages)", fontsize=10, color=FG, loc="left")
xs = np.arange(len(TD)); bot = np.zeros(len(TD))
for k in RK:
    v = np.array([t["wiki"][k] + t["wd"][k] for t in TD])
    a2.bar(xs, v, bottom=bot, color=RCOL[k], width=.75); bot += v
a2.set_xticks(xs); a2.set_xticklabels([f"{t['decade']}s" for t in TD], rotation=90, fontsize=8.5); style(a2, axis="y")
from matplotlib.ticker import MaxNLocator
a2.yaxis.set_major_locator(MaxNLocator(integer=True)); a1.yaxis.set_major_locator(MaxNLocator(integer=True))
a2.set_title("Since 1840, by decade (Wikipedia list and Wikidata dates)", fontsize=10, color=FG, loc="left")
fig.subplots_adjust(left=.05, right=.98, top=.8, bottom=.27, wspace=.18)
fig.text(.05, .96, "When places were abandoned, where the record says", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.05, .9, f"{R['wiki_dated']} Wikipedia list entries with a year, {R['wd_dated']} Wikidata dissolution dates, {R['dmv_dated']} dated English deserted villages",
         fontsize=9.5, color=MUT, va="top")
legend_row(fig, .035, RK, x0=.05, fs=8.6, full=False)
both(fig, "when")

# ---------- 8. how often the record says why ----------
fig, ax = plt.subplots(figsize=(10, 3.6), facecolor=BG); ax.set_facecolor(BG)
rowsK = [("Wikidata ghost towns", R["n_ghost"], R["wd_known_hm"], R["wd_mining_low"]),
         ("Wikipedia's list", R["n_wiki"], R["wiki_known"], 0),
         ("England's deserted villages", R["n_dmv"], R["n_dmv"], 0)]
for i, (lab, n, k, low) in enumerate(rowsK[::-1]):
    ax.barh(i, 1, color=RULE, height=.6)
    ax.barh(i, (k) / n, color=FG, height=.6)
    if low: ax.barh(i, low / n, left=k / n, color=MUT, height=.6)
    ax.text(1.02, i, f"{(k + low) / n * 100:.0f}% of {n:,}", va="center", fontsize=10)
ax.set_yticks(range(3)); ax.set_yticklabels([r[0] for r in rowsK[::-1]], fontsize=10.5)
ax.set_xlim(0, 1.2); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0%", "50%", "100%"]); style(ax)
fig.subplots_adjust(left=.25, right=.93, top=.75, bottom=.15)
fig.text(.25, .95, "How often the record says why", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.25, .86, "Share with a reason. Wikidata: dark from text or class, grey from a mining word in the name", fontsize=9.3, color=MUT, va="top")
fig.savefig(f"{PAP}/f_known.png", dpi=200, facecolor=BG); plt.close(fig)

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), facecolor=BG)
ax = fig.add_axes([.32, .04, .67, .9]); ax.set_facecolor(BG); world(ax, s_unk=2.5, s_k=12, s_dmv=1.8)
fig.text(.035, .9, "Ghost\ntowns\nof the\nworld", fontproperties=DISP, fontsize=50, color=FG, va="top", linespacing=.92)
fig.text(.037, .28, f"{R['n_map']:,} abandoned settlements,\ncoloured by why they emptied.\nOnly {R['wd_known_share'] * 100:.0f}% of Wikidata's ghost\ntowns say why.",
         fontsize=12.5, color=FG, va="top", family=SER, linespacing=1.3)
fig.text(.037, .045, "maps.tristanhotham.com/ghost-towns", fontsize=10, color=MUT, va="bottom")
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
print("figures done")
