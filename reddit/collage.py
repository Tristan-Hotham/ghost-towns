"""Reddit collage (r/dataisbeautiful style): a world map of abandoned settlements coloured by why they were abandoned,
with insets for the American West and England, the reasons Wikipedia's list gives, and a full legend.
Light paper background; every label sits on open sea or paper with a white halo. Writes reddit/ghost_towns_of_the_world.png.
Run: python3 reddit/collage.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figlib import *
from pyproj import Transformer

J, R, P = load()
OUT = os.path.join(ROOT, "reddit", "ghost_towns_of_the_world.png")
W_, H_ = 15.0, 12.2
fig = plt.figure(figsize=(W_, H_), facecolor=BG)
RK = RKEYS

# ---------- title ----------
fig.text(.035, .968, "Ghost towns of the world", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.036, .902, f"{R['n_map']:,} abandoned settlements in open data, coloured by why they were abandoned. "
         f"Only {R['wd_known']} of Wikidata's {R['n_ghost']:,} ghost towns ({R['wd_known_share']*100:.0f}%) say why,",
         fontsize=13.5, color=FG, va="top", family=SER)
fig.text(.036, .878, f"{R['us_share_wd']*100:.0f}% of them are in the United States, and England's {R['n_dmv']:,} deserted medieval villages "
         f"make up {R['dmv_share_map']*100:.0f}% of the map.", fontsize=13.5, color=FG, va="top", family=SER)

# ---------- world map ----------
ax = fig.add_axes([.03, .392, .94, .47]); ax.set_facecolor(BG)
poly = outline(ax, fc=SEA, ec="#C2CCCE", lw=.9, lat_min=-60, lat_max=84)
draw_land(ax, fc=LANDC, z=1)
ax.add_collection(LineCollection(borders_world(), colors=BORDER, linewidths=.35, zorder=1.2))
x0, x1 = poly[:, 0].min(), poly[:, 0].max(); y0, y1 = poly[:, 1].min(), poly[:, 1].max()
ax.set_xlim(x0 - 2e5, x1 + 2e5); ax.set_ylim(y0 - 1e5, y1 + 1.7e6); ax.set_aspect("equal"); ax.axis("off")  # paper band above the map for labels

src = np.array([p[5] for p in P]); rea = np.array([p[3] for p in P]); lat = np.array([p[1] for p in P]); lon = np.array([p[2] for p in P])
X, Y = proj(lon, lat)
unk = RK.index("unknown")
m = (src == 0) & (rea == unk)
ax.scatter(X[m], Y[m], s=3.2, c=RCOL["unknown"], lw=0, alpha=.75, zorder=3)
m = src == 1
ax.scatter(X[m], Y[m], s=2.6, c=RCOL["medieval"], lw=0, alpha=.85, zorder=3.2)
for k in RK[:-1]:
    i = RK.index(k)
    m = (src == 0) & (rea == i)
    ax.scatter(X[m], Y[m], s=16, c=RCOL[k], lw=.35, edgecolors=PAPER, zorder=4)
    m = (src == 3) & (rea == i)
    ax.scatter(X[m], Y[m], s=30, c=RCOL[k], lw=1.1, edgecolors=FG, zorder=4.5)

# callouts: name and reason, on open sea, short leaders that do not cross other labels
def pt(name):
    for p in P:
        if p[0] == name and p[5] in (0, 3):
            return p
    raise KeyError(name)

CALL = [  # name, label, words that must be in the record's text, second line, (unused), (unused), (unused)
    ("Pyramiden", "Pyramiden", "coal", "Svalbard: coal mining", 0, 0, ""),
    ("Kolmanskop", "Kolmanskop", "diamond", "Namibia: diamonds", 0, 0, ""),
    ("Plymouth", "Plymouth", "volcano", "Montserrat: volcano", 0, 0, ""),
    ("Centralia", "Centralia", "mine fire", "USA: mine fire", 0, 0, ""),
    ("Armero", "Armero", "volcanic", "Colombia: eruption", 0, 0, ""),
    ("Pripyat", "Pripyat", "", "Ukraine: Chernobyl", 0, 0, ""),
    ("Oradour-sur-Glane", "Oradour", "Waffen-SS", "France: wartime massacre", 0, 0, ""),
    ("Hashima Island", "Hashima", "coal mines", "Japan: coal mines closed", 0, 0, ""),
    ("Wittenoom", "Wittenoom", "asbestos", "Australia: asbestos mine", 0, 0, ""),
    ("Villa Epecuén", "Villa Epecuén", "flood", "Argentina: flood", 0, 0, ""),
    ("Old Adaminaby", "Old Adaminaby", "flooded by a dam", "Australia: dam flooding", 0, 0, ""),
]
# ---------- land (Natural Earth 10m countries, small islands included), buffered 25 km, for label placement ----------
from shapely.geometry import shape as _shape, Polygon as _Poly, LineString, box as sbox
from shapely.strtree import STRtree as _Tree
from shapely.prepared import prep as _prep
LAND_MARGIN = 25000
_lp = []
for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]:
    g = _shape(f["geometry"])
    for q in getattr(g, "geoms", [g]):
        a_ = np.array(q.exterior.coords)
        x_, y_ = FWD.transform(wrap(a_[:, 0]), np.clip(a_[:, 1], -89.9, 89.9))
        if np.ptp(x_) > 1.5e7:                       # a ring split by the cut at 170 W: keep both halves
            lo = wrap(a_[:, 0])
            for part in (lo < 0, lo >= 0):
                if part.sum() >= 3:
                    xx, yy = FWD.transform(lo[part], np.clip(a_[part, 1], -89.9, 89.9))
                    try: _lp.append(_Poly(np.column_stack([xx, yy])).convex_hull)
                    except Exception: pass
            continue
        try: _lp.append(_Poly(np.column_stack([x_, y_])).buffer(0))
        except Exception: pass
_tree = _Tree(_lp)
def on_land(geom):
    g = geom.buffer(LAND_MARGIN)
    return any(_lp[int(i)].intersects(g) for i in _tree.query(g))

LABELS, LEADERS, BOXES = [], [], []          # BOXES: shapely boxes (data units) of placed labels
fig.canvas.draw(); REND = fig.canvas.get_renderer()
S_ = ax.transData.transform((1, 0))[0] - ax.transData.transform((0, 0))[0]     # display px per data unit
shown_xy = np.column_stack([X, Y])[src != 2]

def size(txt, **kw):
    t = ax.text(0, 0, txt, **kw); bb = t.get_window_extent(REND); t.remove()
    return bb.width / S_, bb.height / S_

# fixed region label first
for txt, llon, llat, ha in ((f"United States\n{R['us_n']:,} ghost towns", -150, 33, "center"),):
    x, y = proj(llon, llat)
    t = ax.text(x, y, txt, ha=ha, va="center", fontsize=10.5, color=MUT, fontweight="medium", linespacing=1.15, zorder=6)
    halo(t, 3.4, SEA); LABELS.append(t)
    bb = t.get_window_extent(REND); inv = ax.transData.inverted()
    (a0, b0), (a1, b1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)]); BOXES.append(sbox(a0, b0, a1, b1))
    assert not on_land(BOXES[-1]), "US label on land"

PAD = 0.6e5
def label_boxes(lx, ly, w1, h1, w2, h2, ha):
    off = 1.2e5 if ha == "left" else -1.2e5
    x0 = lx + off if ha == "left" else lx + off - max(w1, w2)
    b1 = sbox(x0 if ha == "left" else lx + off - w1, ly + 1.0e5, (x0 + w1) if ha == "left" else lx + off, ly + 1.0e5 + h1)
    b2 = sbox(x0 if ha == "left" else lx + off - w2, ly - 0.5e5 - h2, (x0 + w2) if ha == "left" else lx + off, ly - 0.5e5)
    return b1, b2

def ok(px, py, lx, ly, b1, b2, xlim, ylim):
    whole = b1.union(b2).envelope
    if whole.bounds[0] < xlim[0] or whole.bounds[2] > xlim[1] or whole.bounds[1] < ylim[0] or whole.bounds[3] > ylim[1]:
        return False
    for b in (b1, b2):
        if on_land(b.buffer(0.6e5)): return False
        if any(b.buffer(PAD).intersects(o) for o in BOXES): return False
        bx = b.buffer(PAD).bounds
        if ((shown_xy[:, 0] > bx[0]) & (shown_xy[:, 0] < bx[2]) & (shown_xy[:, 1] > bx[1]) & (shown_xy[:, 1] < bx[3])).any(): return False
    seg = LineString([(px, py), (lx, ly)])
    if any(seg.intersects(o.buffer(PAD)) for o in BOXES): return False
    for (a, c, _) in LEADERS:
        L_ = LineString([a, c])
        if L_.intersects(b1.buffer(PAD)) or L_.intersects(b2.buffer(PAD)) or L_.crosses(seg): return False
    # the leader should not run through its own label
    if seg.intersects(b1.buffer(-1)) or seg.intersects(b2.buffer(-1)): return False
    return True

XL, YL = ax.get_xlim(), ax.get_ylim()
def crowd(px, py, lx, ly):
    """Points within 40 km of a leader line (leaders may cross data, but should cross as little as possible)."""
    a = np.array([px, py]); v = np.array([lx - px, ly - py]); L2 = max(v @ v, 1)
    t = np.clip(((shown_xy - a) @ v) / L2, 0, 1)
    d = np.hypot(*(shown_xy - (a + np.outer(t, v))).T)
    return int((d < 4e4).sum())
# Pripyat and Pyramiden: keep their labels in the Norwegian Sea, the Arctic or the paper above the map
PREFER = {"Pripyat": lambda lo, la: la > 62, "Pyramiden": lambda lo, la: la > 70, "Centralia": lambda lo, la: lo > -78 and la < 60}
outline_poly = _Poly(poly).buffer(-0.6e5)
FIRST = ["Pyramiden", "Pripyat", "Oradour-sur-Glane", "Centralia", "Wittenoom", "Old Adaminaby"]       # the crowded North Atlantic and Arctic first
order = sorted(CALL, key=lambda c: (FIRST.index(c[0]) if c[0] in FIRST else 9, -abs(pt(c[0])[1])))
for name, lab, must, why, _lon, _lat, _ha in order:
    p = pt(name)
    txt = (p[12] + " " + p[11])
    if name == "Pripyat":
        assert p[3] == RK.index("nuclear")
    else:
        assert must.lower() in txt.lower(), (name, must)
    if "wartime" in why:
        assert "World War II" in txt
    col = RCOL[RK[p[3]]]
    px, py = proj(p[2], p[1])
    w1, h1 = size(lab, fontsize=10.5, family=SER); w2, h2 = size(why, fontsize=10, family=SER, style="italic")
    best = None
    if os.environ.get("DEBUGL"): print(name, "w1 h1 w2 h2", round(w1), round(h1), round(w2), round(h2), "YL", [round(v) for v in YL], "S", S_)
    for dlon in np.arange(-70, 71, 2.5):
        for dlat in np.arange(-40, 51, 2.0):
            llon, llat = p[2] + dlon, p[1] + dlat
            if not (-58 < llat) or abs(dlon) + abs(dlat) < 4: continue
            lx, ly = proj(llon, min(llat, 84.0))
            if llat > 84: ly = ly + (llat - 84) * 1.1e5          # above the map: on the paper band
            if name in PREFER and not PREFER[name](llon, llat): continue
            if not (CUT + 2 < llon < CUT + 358): continue        # stay on the map, never across the cut at 170 W
            d = np.hypot(lx - px, ly - py) + 4e5 * crowd(px, py, lx, ly)
            if best and d >= best[0]: continue
            for ha in ("left", "right"):
                b1, b2 = label_boxes(lx, ly, w1, h1, w2, h2, ha)
                if ok(px, py, lx, ly, b1, b2, XL, YL):
                    best = (d, lx, ly, ha, b1, b2); break
    assert best, f"no sea position for {name}"
    d, lx, ly, ha, b1, b2 = best
    ax.plot([px, lx], [py, ly], color=FG, lw=.6, zorder=5, solid_capstyle="round")
    off = 1.2e5 if ha == "left" else -1.2e5
    t = ax.text(lx + off, ly + 1.0e5, lab, ha=ha, va="bottom", fontsize=10.5, color=FG, family=SER, zorder=6); halo(t, 3.2, SEA); LABELS.append(t)
    t = ax.text(lx + off, ly - 0.5e5, why, ha=ha, va="top", fontsize=10, color=col, family=SER, style="italic", zorder=6); halo(t, 3.2, SEA); LABELS.append(t)
    LEADERS.append(((px, py), (lx, ly), name)); BOXES += [b1, b2]
    ax.scatter([lx], [ly], s=6, c=FG, zorder=6)
    if os.environ.get("DEBUGL"):
        fig.canvas.draw(); bb = LABELS[-2].get_window_extent(fig.canvas.get_renderer()); iv = ax.transData.inverted()
        print("pred", [round(v/1e3) for v in b1.bounds], "real", [round(v/1e3) for v in list(iv.transform((bb.x0, bb.y0))) + list(iv.transform((bb.x1, bb.y1)))])
    print("placed", name, ha, [round(v) for v in FWD.transform(lx, ly, direction="INVERSE")])

# ---------- inset 1: the American West ----------
TW = Transformer.from_crs(4326, "+proj=aea +lat_1=34 +lat_2=46 +lat_0=40 +lon_0=-113 +datum=WGS84 +units=m", always_xy=True)
bb = (-125.5, 30.8, -101.5, 49.5)
ax2 = fig.add_axes([.035, .092, .30, .24]); ax2.set_facecolor(SEA)
polys, lines, sub = region_layers(TW, (-130, 26, -95, 52), admin1=["United States of America"])
for rings in polys: rings_patch(ax2, rings, LANDC, z=1)
ax2.add_collection(LineCollection(sub, colors=BORDER, linewidths=.6, zorder=1.3))
ax2.add_collection(LineCollection(lines, colors=COAST, linewidths=.7, zorder=1.4))
gx, gy = TW.transform(lon, lat)
inb = (lon > bb[0]) & (lon < bb[2]) & (lat > bb[1]) & (lat < bb[3]) & (src == 0)
m = inb & (rea == unk); ax2.scatter(gx[m], gy[m], s=7, c=RCOL["unknown"], lw=0, alpha=.8, zorder=3)
for k in RK[:-1]:
    m = inb & (rea == RK.index(k)); ax2.scatter(gx[m], gy[m], s=22, c=RCOL[k], lw=.4, edgecolors=PAPER, zorder=4)
cx0, cy0 = TW.transform(bb[0], bb[1]); cx1, cy1 = TW.transform(bb[2], bb[3])
xa, ya = TW.transform([-124.6, -102.0, -124.6, -102.0], [32.0, 32.0, 49.0, 49.0])
ax2.set_xlim(min(xa) - 1.2e5, max(xa) + 4e4); ax2.set_ylim(min(ya) - 3e4, max(ya) + 9e4); ax2.set_aspect("equal"); ax2.axis("off")
ax2.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax2.transAxes, fc="none", ec=RULE, lw=1.2, zorder=10))
fig.text(.035, .392, "The American West", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.035, .368, f"{R['us_west_n']:,} ghost towns in 11 states; {R['us_west_mining']} tied to mining,\n"
         f"{R['us_west_mining_low']} of them only by a mining word in the name", fontsize=9.2, color=MUT, va="top", linespacing=1.3)

# ---------- inset 2: England ----------
TE = Transformer.from_crs(4326, "EPSG:27700", always_xy=True)
ax3 = fig.add_axes([.35, .092, .2, .24]); ax3.set_facecolor(SEA)
polys, lines, sub = region_layers(TE, (-11, 49.3, 2.6, 56.6))
for rings in polys: rings_patch(ax3, rings, LANDC, z=1)
ax3.add_collection(LineCollection(lines, colors=COAST, linewidths=.6, zorder=1.4))
ex, ey = TE.transform(lon, lat)
inE = (lon > -7) & (lon < 2) & (lat > 49.8) & (lat < 56.0)
m = inE & (src == 1); ax3.scatter(ex[m], ey[m], s=4.2, c=RCOL["medieval"], lw=0, alpha=.9, zorder=3)
m = inE & (src == 0) & (rea == unk); ax3.scatter(ex[m], ey[m], s=10, c=RCOL["unknown"], lw=0, zorder=3.5)
for k in RK[:-1]:
    for sv, ss, ec, lw in ((0, 22, PAPER, .4), (3, 30, FG, 1.1)):
        m = inE & (src == sv) & (rea == RK.index(k)); ax3.scatter(ex[m], ey[m], s=ss, c=RCOL[k], lw=lw, edgecolors=ec, zorder=4)
xa, ya = TE.transform([-9.6, 2.05], [49.75, 55.9])
ax3.set_xlim(xa[0], xa[1]); ax3.set_ylim(ya[0], ya[1]); ax3.set_aspect("equal"); ax3.axis("off")
ax3.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax3.transAxes, fc="none", ec=RULE, lw=1.2, zorder=10))
fig.text(.35, .392, "England", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.35, .368, f"{R['n_dmv']:,} deserted medieval villages\nand hamlets (Beresford's gazetteer)", fontsize=9.2, color=MUT, va="top", linespacing=1.3)
t = ax3.text(.03, .03, f"Yorkshire {R['dmv_yorks']}\nLincolnshire {R['dmv_lincs']}\nNorthumberland {R['dmv_nland']}", transform=ax3.transAxes,
             fontsize=8.4, color=FG, va="bottom", ha="left", zorder=11, linespacing=1.35)
halo(t, 3, SEA)

# ---------- panel 3: reasons in Wikipedia's list ----------
ax4 = fig.add_axes([.632, .095, .075, .21]); ax4.set_facecolor(BG)
ks = [k for k in R["wiki_rank"]]
vals = [R["wiki_reason"][k] for k in ks]
yy = np.arange(len(ks))[::-1]
ax4.barh(yy, vals, color=[RCOL[k] for k in ks], height=.72)
for y_, v, k in zip(yy, vals, ks):
    ax4.text(v + 1.5, y_, f"{v}", va="center", fontsize=9.5, color=FG)
    ax4.text(-2, y_, RLAB[k], va="center", ha="right", fontsize=9.5, color=FG)
ax4.set_xlim(0, max(vals) * 1.25); ax4.set_ylim(-.6, len(ks) - .4); ax4.axis("off")
fig.text(.572, .392, "Why, per Wikipedia", fontproperties=DISPB, fontsize=15, color=FG, va="top")
fig.text(.572, .368, f"{R['wiki_known']} of {R['n_wiki']} places in its\n'List of ghost towns by\ncountry' give a reason", fontsize=9.2, color=MUT, va="top", linespacing=1.3)

# ---------- legend ----------
lx, ly = .742, .392
fig.text(lx, ly, "Why they were abandoned", fontproperties=DISPB, fontsize=13.5, color=FG, va="top")
on_map = {k: 0 for k in RK}
for p in P:
    if p[5] in (0, 1, 3): on_map[RK[p[3]]] += 1
yy = ly - .034
for k in RK:
    fig.patches.append(plt.Circle((lx + .007, yy - .007), .0052, transform=fig.transFigure, fc=RCOL[k], ec="none"))
    fig.text(lx + .047, yy, f"{on_map[k]:,}", fontsize=8.6, color=MUT, va="top", ha="right")
    fig.text(lx + .053, yy + .002, RFULL[k], fontsize=9.8, color=FG, va="top", family=SER)
    yy -= .0245
yy -= .006
fig.patches.append(plt.Circle((lx + .007, yy - .007), .0055, transform=fig.transFigure, fc=PAPER, ec=FG, lw=1.3))
fig.text(lx + .053, yy + .002, "Well-known place from Wikipedia's list,\nplaced by hand (ringed)", fontsize=10, color=FG, va="top", linespacing=1.2, family=SER)
fig.text(lx + .047, yy, f"{R['n_hand']}", fontsize=8.6, color=MUT, va="top", ha="right")
fig.text(lx, yy - .042, "Counts: places on the map. Reasons from keyword\nrules on Wikidata descriptions and Wikipedia text.",
         fontsize=7.6, color=MUT, va="top", linespacing=1.3)

# ---------- footer ----------
fig.add_artist(plt.Line2D([.035, .965], [.072, .072], transform=fig.transFigure, color=FG, lw=1))
fig.text(.035, .061, "Data: Wikidata (CC0), items classed as ghost town, abandoned village or deserted medieval village, with coordinates; "
         f"{R['n_mexico']:,} living Mexican municipalities that reach the class", fontsize=8.1, color=MUT, va="top")
fig.text(.035, .048, "through a faulty link, and ancient cities, are left off. England: Beresford's Lost Villages, University of Hull (CC BY-NC-SA 4.0). "
         "Reasons: English Wikipedia, 'List of ghost towns", fontsize=8.1, color=MUT, va="top")
fig.text(.035, .035, "by country' and 'Ghost town' (CC BY-SA 4.0). Natural Earth. Equal Earth projection.", fontsize=8.1, color=MUT, va="top")
fig.text(.035, .005, "maps.tristanhotham.com/ghost-towns", fontsize=9.5, color=FG, va="bottom", fontweight="medium")
fig.text(.965, .005, "Dr Tristan Hotham · Independent researcher · 2026", fontsize=9.5, color=FG, va="bottom", ha="right")
# ---------- checks: labels never cover data points, never overlap each other, leaders never cross other labels ----------
fig.canvas.draw()
rend = fig.canvas.get_renderer()
boxes = [(t, t.get_window_extent(rend).expanded(1.02, 1.08)) for t in LABELS]
disp = ax.transData.transform(np.column_stack([X, Y]))
shown = (src != 2)
bad = []
for t, b in boxes:
    inside = shown & (disp[:, 0] > b.x0) & (disp[:, 0] < b.x1) & (disp[:, 1] > b.y0) & (disp[:, 1] < b.y1)
    if inside.any():
        bad.append(("covers data", t.get_text(), int(inside.sum()), [P[i][0] or P[i][9] for i in np.where(inside)[0][:3]]))
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if boxes[i][1].overlaps(boxes[j][1]):
            bad.append(("overlap", boxes[i][0].get_text(), boxes[j][0].get_text()))
from shapely.geometry import LineString, box as sbox
for (a, b_, name) in LEADERS:
    seg = LineString(ax.transData.transform([a, b_]))
    for t, bb in boxes:
        if seg.intersects(sbox(bb.x0, bb.y0, bb.x1, bb.y1)) and not t.get_text().startswith(next(c[1] for c in CALL if c[0] == name)[:5]) \
                and t.get_text() not in [c[3] for c in CALL if c[0] == name]:
            bad.append(("leader crosses", name, t.get_text()))
# labels must keep 25 km clear of land, small islands included (rendered boxes, Natural Earth 10m countries)
inv = ax.transData.inverted()
for t, bb in boxes:
    (xa_, ya_), (xb_, yb_) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    if on_land(sbox(min(xa_, xb_), min(ya_, yb_), max(xa_, xb_), max(ya_, yb_))):
        bad.append(("touches land", t.get_text()))
for b in bad: print("CHECK", b)
import os as _o
if bad and not _o.environ.get("DRAFT"): raise AssertionError(bad)
fig.savefig(OUT, dpi=200, facecolor=BG)
print(OUT)
