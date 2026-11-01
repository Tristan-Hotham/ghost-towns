"""Shared drawing helpers for the figures, the header and the collage: fonts, colours, an Equal Earth world centred on
10 degrees E, Natural Earth land and borders, and regional projections for the insets (US West, England, Chernobyl)."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Polygon as MPoly
from pyproj import Transformer
from shapely.geometry import shape, box
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 700, "opsz": 48, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Bold.ttf")
for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FONTS, f))
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11})
BG, FG, MUT, RULE, PAPER = "#F6F3EC", "#1F1C19", "#6A645C", "#E2DCD0", "#FCFBF7"
SEA, LANDC, COAST, BORDER = "#E3EAEC", "#EAE5D9", "#C4BDAE", "#D3CCBD"
HOT = "#B8322A"
LON0 = 10.0
CUT = LON0 - 180
FWD = Transformer.from_crs(4326, f"+proj=eqearth +lon_0={LON0} +datum=WGS84 +units=m +no_defs", always_xy=True)


def wrap(lon):
    lon = np.asarray(lon, float)
    return np.where(lon < CUT, lon + 360, lon)


def proj(lon, lat, T=None):
    T = T or FWD
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    if T is FWD:
        lon = wrap(lon)
    return T.transform(lon, lat)


def _dens(coords, step=1.0, T=None):
    a = np.array(coords)
    pts = [a[0]]
    for p, q in zip(a[:-1], a[1:]):
        n = max(1, int(np.ceil(np.hypot(*(q - p)) / step)))
        for t in np.linspace(0, 1, n + 1)[1:]:
            pts.append(p + (q - p) * t)
    a = np.array(pts)
    x, y = (T or FWD).transform(a[:, 0], np.clip(a[:, 1], -89.9, 89.9))
    return np.column_stack([x, y])


_LAND = {}


def land_polys(res="50m"):
    """Natural Earth land, cut at 170 W and wrapped, as projected rings."""
    if res in _LAND:
        return _LAND[res]
    L = jload(f"{GEO}/ne_50m_land.geojson")["features"]
    g = unary_union([shape(f["geometry"]).buffer(0) for f in L])
    west = g.intersection(box(-180, -90, CUT, 90)); east = g.intersection(box(CUT, -90, 180, 90))
    g2 = unary_union([east, affinity.translate(west, 360, 0)])
    out = []
    for poly in getattr(g2, "geoms", [g2]):
        if poly.geom_type != "Polygon" or poly.area < 0.02:
            continue
        rings = [_dens(poly.exterior.coords)] + [_dens(r.coords) for r in poly.interiors]
        e = rings[0]
        if np.ptp(e[:, 0]) > 2e7 and np.ptp(e[:, 1]) < 3e5:
            continue
        out.append(rings)
    _LAND[res] = out
    return out


def rings_patch(ax, rings, fc, ec="none", lw=0, z=1):
    verts = np.concatenate(rings); codes = []
    for r in rings:
        codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 2) + [Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z))


def draw_land(ax, fc=LANDC, z=1):
    for rings in land_polys():
        rings_patch(ax, rings, fc, z=z)


_BOR = None


def borders_world():
    """Country outlines (Natural Earth 50m), split at the cut, projected."""
    global _BOR
    if _BOR is None:
        A = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
        segs = []
        for f in A:
            g = shape(f["geometry"])
            for p in getattr(g, "geoms", [g]):
                a = np.array(p.exterior.coords)
                if len(a) < 3: continue
                lo = wrap(a[:, 0]); la = np.clip(a[:, 1], -89.9, 89.9)
                br = np.where(np.abs(np.diff(lo)) > 180)[0]
                for seg in np.split(np.arange(len(lo)), br + 1):
                    if len(seg) >= 2:
                        x, y = FWD.transform(lo[seg], la[seg]); segs.append(np.column_stack([x, y]))
        _BOR = segs
    return _BOR


def outline(ax, fc=SEA, ec="#BAC6C8", lw=.8, z=0, lat_min=-90, lat_max=90):
    lat = np.linspace(lat_min, lat_max, 200)
    xl, yl = FWD.transform(np.full_like(lat, LON0 - 179.999), lat)
    xr, yr = FWD.transform(np.full_like(lat, LON0 + 179.999), lat[::-1])
    poly = np.column_stack([np.concatenate([xl, xr]), np.concatenate([yl, yr])])
    ax.add_patch(MPoly(poly, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))
    return poly


def region_layers(T, bbox, admin1=None, res="10m"):
    """Land polygons and borders for an inset, projected with T, clipped to a lon/lat bbox (w, s, e, n).
    admin1: list of Natural Earth admin names whose first-level units are outlined (e.g. US states)."""
    w, s, e, n = bbox
    B = box(w, s, e, n)
    A = jload(f"{GEO}/ne_{res}_admin_0_countries.geojson")["features"]
    polys, lines = [], []
    for f in A:
        g = shape(f["geometry"])
        if not g.intersects(B): continue
        g = g.buffer(0).intersection(B)
        for p in getattr(g, "geoms", [g]):
            if p.geom_type != "Polygon" or p.area < 1e-4: continue
            polys.append([_dens(p.exterior.coords, .1, T)] + [_dens(r.coords, .1, T) for r in p.interiors])
            lines.append(_dens(p.exterior.coords, .1, T))
    sub = []
    if admin1:
        S = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
        for f in S:
            if f["properties"]["admin"] not in admin1: continue
            g = shape(f["geometry"])
            if not g.intersects(B): continue
            for p in getattr(g, "geoms", [g]):
                if p.area < 1e-3: continue
                sub.append(_dens(p.exterior.coords, .1, T))
    return polys, lines, sub


def style(ax, grid=True, axis="x"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=10)
    if grid: ax.grid(axis=axis, color=RULE, lw=.8); ax.set_axisbelow(True)


def load():
    J = jload(f"{WORK}/classified.json"); R = jload(f"{DATA}/results.json"); P = jload(f"{DATA}/points.json")["p"]
    return J, R, P


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def halo(t, w=3, c=None):
    import matplotlib.patheffects as pe
    t.set_path_effects([pe.withStroke(linewidth=w, foreground=c or PAPER)])
    return t
