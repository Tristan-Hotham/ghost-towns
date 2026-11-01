"""Step 1. Clean the Wikidata extract and England's deserted medieval villages.

Wikidata: one row per item (first point, all classes, first dissolved year). Each item gets a scope:
  ghost    at least one class from the ghost-town family (ghost town, abandoned village, deserted medieval village,
           former village, abandoned hamlet, mining community and a few more: GHOST below), or a weaker class such as
           'former settlement' when the item has no ancient or archaeological class;
  ancient  otherwise, a class for an ancient or archaeological settlement (ancient city, polis, Roman city, oppidum...);
  dropped  everything else. Almost all of these are the 2,456 living municipalities of Mexico, which reach the query
           through a faulty subclass link in Wikidata, plus a handful of museums, castles and living towns.
Country, continent and first-level region come from Natural Earth by point in polygon (nearest country within 25 km for
points just offshore), so former states and empires in the Wikidata country field are replaced by today's country.
England's deserted medieval villages (DMV) and hamlets (DMH) come from the companion study's lost_villages.csv.
Run: python3 code/01_clean.py
"""
import os, sys, re, subprocess, collections
import pandas as pd, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

GHOST = {"ghost town", "abandoned village", "deserted medieval village", "former village", "abandoned hamlet",
         "mining community", "former town", "pit village", "ghost towns in Italy"}
# weaker classes: count as ghost towns only when the item has no ancient or archaeological class
GHOST_WEAK = {"former settlement", "former place", "destroyed settlement", "depopulated Palestinian village", "submerged settlement"}
ANCIENT = {"ancient city", "polis", "Roman city", "oppidum", "dava", "iberian settlement", "vicus", "Roman colony",
           "municipium", "castro", "Ancient Greek archaeological site", "burgus", "castrum", "hillfort",
           "Roman archaeological site", "tell", "city-state", "Greek colony", "celtiberian town", "emporium", "kokufu",
           "Gallo-Roman city", "colonia augusta", "Bronze Age settlement", "lost city", "archaeological site", "ruins",
           "roman ruins", "Celtic archaeological site", "settlement site", "mutatio", "mansio", "City-kingdom of Cyprus",
           "hieron", "Byzantine city", "destroyed city", "Maya site in Mexico", "ancient port", "Carthaginian archaeological site",
           "Ancient Egyptian archaeological site", "archaeological site in Greece", "civitas stipendaria", "Civitas foederata",
           "proto-city", "cave city", "underground city", "Samian Ware Discovery Site", "ancient Roman structure",
           "archaeological park", "zona arqueológica", "type site", "organized archaeological site", "titular see",
           "biblical place", "deme", "town of Rus'", "Genoese colonies", "medieval city", "fortified town", "burh",
           "promontory fort", "German promontory fort", "circular rampart", "castle", "fortress", "fortification"}
NAME_FIX = {"United States of America": "United States", "Republic of Serbia": "Serbia", "United Republic of Tanzania": "Tanzania",
            "The Bahamas": "Bahamas", "Czechia": "Czech Republic", "eSwatini": "Eswatini", "Macedonia": "North Macedonia"}


def wd_clean():
    d = pd.read_csv(f"{RAW}/wikidata_ghost.tsv", sep="\t", dtype=str)
    d.columns = [c.lstrip("?") for c in d.columns]
    for c in ("bL", "cL", "clsL", "desc"):
        d[c] = d[c].str.strip().str.replace(r'@en$', "", regex=True).str.replace(r'^"|"$', "", regex=True)
    d["qid"] = d.b.str.extract(r"(Q\d+)>")[0]
    xy = d.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
    d["lon"], d["lat"] = xy[0], xy[1]

    def year(s):
        if not isinstance(s, str): return None
        m = re.match(r"^(-?\d{1,4})-", s)
        return int(m.group(1)) if m else None
    d["y"] = d.end.map(year)
    rows = []; nocoord = []
    for q, g in d.groupby("qid", sort=False):
        cls = sorted(set(g.clsL.dropna()))
        lab = g.bL.dropna().iloc[0] if g.bL.notna().any() else None
        ys = [int(v) for v in g.y.dropna()]
        gp = g[g.lat.notna()]
        if gp.empty:                                   # coordinate given only as 'unknown value'
            nocoord.append(q); continue
        rows.append({"qid": q, "name": lab, "sitelinks": int(g.sl.iloc[0]), "lat": round(gp.lat.iloc[0], 5), "lon": round(gp.lon.iloc[0], 5),
                     "wd_country": "; ".join(sorted(set(g.cL.dropna()))), "classes": cls, "desc": g.desc.dropna().iloc[0] if g.desc.notna().any() else None,
                     "dissolved": min(ys) if ys else None, "dissolved_unknown": bool(g.end.fillna("").str.contains("genid").any())})
    W = pd.DataFrame(rows)
    W["scope"] = ["ghost" if set(c) & GHOST or (set(c) & GHOST_WEAK and not set(c) & ANCIENT) else "ancient" if set(c) & ANCIENT
                  else "dropped" for c in W.classes]
    W["mexico_muni"] = [c == ["municipality of Mexico"] for c in W.classes]
    W.attrs["nocoord"] = nocoord
    return W, d


def geo_assign(lat, lon):
    A = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
    polys = [shape(f["geometry"]) for f in A]
    tree = STRtree(polys)
    S = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
    keep = [f for f in S if f["properties"]["admin"] in ("United States of America", "United Kingdom", "Canada", "Australia", "Russia")]
    spolys = [shape(f["geometry"]) for f in keep]; stree = STRtree(spolys)
    out = []
    for la, lo in zip(lat, lon):
        p = Point(lo, la); c = None
        for i in tree.query(p, predicate="intersects"):
            c = A[int(i)]["properties"]; break
        off = False
        if c is None:
            i = tree.nearest(p)
            if polys[int(i)].distance(p) < 0.25:
                c = A[int(i)]["properties"]; off = True
        st = None; unit = None
        if c is not None and c["ADMIN"] in ("United States of America", "United Kingdom", "Canada", "Australia", "Russia"):
            hit = [int(i) for i in stree.query(p, predicate="intersects")]
            if not hit:
                j = int(stree.nearest(p)); hit = [j] if spolys[j].distance(p) < 0.25 else []
            if hit:
                pr = keep[hit[0]]["properties"]; st = pr["name"]; unit = pr.get("geonunit")
        if c is None:
            out.append((None, None, None, None, False)); continue
        name = NAME_FIX.get(c["ADMIN"], c["ADMIN"])
        cont = CONTINENT_FIX.get(name, c["CONTINENT"])
        if cont == "Seven seas (open ocean)": cont = "Africa" if name in ("Mauritius", "Seychelles") else "Asia" if name in ("Maldives",) else cont
        out.append((name, cont, st, unit, off))
    return out


def dmv_clean():
    if not os.path.exists(f"{LV}/data/lost_villages.csv"):
        os.makedirs(os.path.dirname(LV), exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", LV_REPO, LV], check=True)
    V = pd.read_csv(f"{LV}/data/lost_villages.csv")
    V = V[V.site_type.isin(["DMV", "DMH"])].copy()
    V["cause_mentions"] = [", ".join(k for k, c in (("enclosure or pasture", r.mentions_enclosure), ("emparking", r.mentions_park),
                                                   ("plague", r.mentions_plague), ("monastic landholder", r.mentions_monastic),
                                                   ("sea or flooding", r.mentions_water)) if c is True or c == 1 or c == "True")
                           for r in V.itertuples()]
    keep = ["id", "name", "site_type", "county", "county_now", "parish_modern", "lat", "lon", "depop_text", "depop_start", "depop_end",
            "depop_period", "cause_mentions", "scheduled_status", "full_record"]
    return V[keep].reset_index(drop=True)


if __name__ == "__main__":
    W, raw = wd_clean()
    nc = W.attrs["nocoord"]
    G = geo_assign(W.lat.values, W.lon.values)
    W["country"], W["continent"], W["region"], W["uk_nation"], W["offshore"] = zip(*G)
    # where Natural Earth finds no country (open sea, Antarctica), keep a modern Wikidata country if there is one
    W["country"] = W.country.fillna(W.wd_country.str.split("; ").str[0])
    V = dmv_clean()
    print(W.scope.value_counts().to_dict(), "mexico munis", int(W.mexico_muni.sum()), "| dmv", len(V))
    jsave({"wd": W.to_dict("records"), "dmv": V.where(V.notna(), None).to_dict("records"),
           "raw_rows": len(raw), "raw_items": int(raw.qid.nunique()),
           "nocoord": nc}, f"{WORK}/clean.json")
