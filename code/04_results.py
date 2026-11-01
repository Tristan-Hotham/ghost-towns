"""Step 4. Every number used anywhere (page, paper, blog, collage, post) goes into data/results.json; the page's point
data go to data/points.json and summaries to data/by_country.csv and data/us_states.csv.
Run: python3 code/04_results.py
"""
import os, sys, collections, math
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

J = jload(f"{WORK}/classified.json"); C0 = jload(f"{WORK}/clean.json")
W = pd.DataFrame(J["W"]); V = pd.DataFrame(J["V"]); E = J["E"]; H = J["H"]
G = W[(W.scope == "ghost") & ~W.dup_dmv].copy()          # Wikidata ghost towns and abandoned villages
A = W[W.scope == "ancient"].copy()
D = W[W.scope == "dropped"]
EL = [e for e in E if e["kind"] != "note"]
R = {}
R["raw_rows"] = C0["raw_rows"]; R["raw_items"] = C0["raw_items"]; R["n_nocoord"] = len(C0["nocoord"])
R["n_ghost"] = len(G); R["n_ancient"] = len(A); R["n_dropped"] = len(D); R["n_mexico"] = int(W.mexico_muni.sum())
R["n_dropped_other"] = R["n_dropped"] - R["n_mexico"]; R["n_dup"] = int(W.dup_dmv.sum())
R["n_dmv"] = len(V); R["n_dmv_dmv"] = int((V.site_type == "DMV").sum()); R["n_dmh"] = int((V.site_type == "DMH").sum())
R["n_map"] = R["n_ghost"] + R["n_dmv"]                     # abandoned settlements (not ancient) on the map
R["n_hand"] = len(H); R["n_wiki"] = len(EL); R["n_wiki_notes"] = len(E) - len(EL)
R["n_wiki_matched"] = J["nmatch"]; R["n_article_matched"] = J["nart"]
R["n_ghost_nolabel"] = int(G.name.isna().sum())
R["n_points_total"] = R["n_ghost"] + R["n_dmv"] + R["n_ancient"] + R["n_hand"]

# ---------- bias: who dominates ----------
cty = G.country.value_counts()
R["n_countries_ghost"] = int(G.country.nunique())
R["us_n"] = int(cty.get("United States", 0)); R["us_share_wd"] = R["us_n"] / R["n_ghost"]
R["ca_n"] = int(cty.get("Canada", 0)); R["gr_n"] = int(cty.get("Greece", 0)); R["au_n"] = int(cty.get("Australia", 0))
R["uk_wd_n"] = int(cty.get("United Kingdom", 0))
R["dmv_share_map"] = R["n_dmv"] / R["n_map"]
R["us_dmv_share_map"] = (R["us_n"] + R["n_dmv"]) / R["n_map"]
R["top_countries"] = [{"country": c, "n": int(n)} for c, n in cty.head(15).items()]
R["n_countries_1to9"] = int(((cty >= 1) & (cty < 10)).sum())
R["africa_n"] = int((G.continent == "Africa").sum()); R["asia_n"] = int((G.continent == "Asia").sum())
R["sam_n"] = int((G.continent == "South America").sum())
R["afasam"] = R["africa_n"] + R["asia_n"] + R["sam_n"]
anc = A.country.value_counts()
R["anc_top"] = [{"country": c, "n": int(n)} for c, n in anc.head(6).items()]
R["anc_tr_gr_share"] = (anc.get("Turkey", 0) + anc.get("Greece", 0)) / len(A)

# ---------- reasons ----------
def rcount(s):
    c = s.value_counts()
    return {k: int(c.get(k, 0)) for k in RKEYS}
R["reasons"] = [{"key": k, "label": RLAB[k], "full": RFULL[k], "colour": RCOL[k]} for k in RKEYS]
R["wd_reason"] = rcount(G.reason)
R["wd_known"] = R["n_ghost"] - R["wd_reason"]["unknown"]; R["wd_known_share"] = R["wd_known"] / R["n_ghost"]
R["wd_conf"] = {k: int((G.confidence == k).sum()) for k in ("high", "medium", "low", "none")}
R["wd_known_hm"] = R["wd_conf"]["high"] + R["wd_conf"]["medium"]
R["wd_mining_low"] = int(((G.reason == "mining") & (G.confidence == "low")).sum())
R["wd_from_list"] = int(G.rule.fillna("").str.startswith("Wikipedia list").sum())
R["wd_from_article"] = int(G.rule.fillna("").str.startswith("Ghost town article").sum())
R["wd_from_desc"] = int(G.rule.fillna("").str.startswith("Wikidata description").sum())
R["wd_from_zone"] = int(G.rule.fillna("").str.contains("exclusion zone").sum())
R["wd_from_class"] = int(G.rule.fillna("").str.startswith("Wikidata class").sum())
R["anc_known"] = int((A.reason != "unknown").sum())
R["wiki_reason"] = rcount(pd.Series([e["reason"] for e in EL]))
R["wiki_known"] = R["n_wiki"] - R["wiki_reason"]["unknown"]; R["wiki_known_share"] = R["wiki_known"] / R["n_wiki"]
kn = {k: v for k, v in R["wiki_reason"].items() if k != "unknown"}
R["wiki_reason_share"] = {k: v / R["wiki_known"] for k, v in kn.items()}
R["wiki_top_reason"] = max(kn, key=kn.get)
R["wiki_rank"] = sorted(kn, key=lambda k: -kn[k])
R["wiki_from_group"] = sum(e["reason_from"] == "group sentence" for e in EL)
R["wiki_countries"] = len({e["country_ne"] for e in EL})
# by continent (Wikipedia list)
CONT = ["Europe", "Asia", "Africa", "North America", "South America", "Oceania", "Antarctica and sub-Antarctic islands"]
R["wiki_by_cont"] = []
for c in CONT:
    es = [e for e in EL if e["continent"] == c]
    rc = collections.Counter(e["reason"] for e in es)
    known = len(es) - rc.get("unknown", 0)
    top = max([k for k in RKEYS if k != "unknown"], key=lambda k: rc.get(k, 0)) if known else None
    R["wiki_by_cont"].append({"continent": c, "label": "Antarctica" if c.startswith("Antarctica") else c, "n": len(es), "known": known,
                              "by": {k: rc.get(k, 0) for k in RKEYS}, "top": top, "top_n": rc.get(top, 0) if top else 0})
BC = {b["continent"]: b for b in R["wiki_by_cont"]}
R["wiki_oc_mining"] = BC["Oceania"]["by"]["mining"]; R["wiki_oc_n"] = BC["Oceania"]["n"]
R["wiki_eu_n"] = BC["Europe"]["n"]
R["wiki_eu_war"] = BC["Europe"]["by"]["war"]; R["wiki_eu_res"] = BC["Europe"]["by"]["reservoir"]
R["wiki_eu_nuc"] = BC["Europe"]["by"]["nuclear"]
R["wiki_af_mining"] = BC["Africa"]["by"]["mining"]; R["wiki_af_n"] = BC["Africa"]["n"]
R["wiki_mx_res"] = sum(1 for e in EL if e["country"] == "Mexico" and e["reason"] == "reservoir")
R["wiki_mx_mining"] = sum(1 for e in EL if e["country"] == "Mexico" and e["reason"] == "mining")
R["wiki_mx_n"] = sum(1 for e in EL if e["country"] == "Mexico")
R["wiki_uk_n"] = sum(1 for e in EL if e["country"] == "United Kingdom")
R["wiki_uk_war"] = sum(1 for e in EL if e["country"] == "United Kingdom" and e["reason"] == "war")
R["wiki_uk_res"] = sum(1 for e in EL if e["country"] == "United Kingdom" and e["reason"] == "reservoir")
R["wiki_uk_dis"] = sum(1 for e in EL if e["country"] == "United Kingdom" and e["reason"] == "disaster")
R["wiki_au_n"] = sum(1 for e in EL if e["country"] == "Australia")
R["wiki_au_mining"] = sum(1 for e in EL if e["country"] == "Australia" and e["reason"] == "mining")
R["wiki_ua_war"] = sum(1 for e in EL if e["country"] == "Ukraine" and e["reason"] == "war")
R["wiki_ua_nuc"] = sum(1 for e in EL if e["country"] == "Ukraine" and e["reason"] == "nuclear")

# ---------- by country table ----------
rows = []
for c, n in cty.items():
    s = G[G.country == c]
    rows.append({"country": c, "continent": s.continent.iloc[0], "wikidata_ghost_towns": int(n), **{f"reason_{k}": int((s.reason == k).sum()) for k in RKEYS},
                 "wikidata_ancient": int(anc.get(c, 0)), "wikipedia_list_entries": sum(1 for e in EL if e["country_ne"] == c),
                 "england_dmv": R["n_dmv"] if c == "United Kingdom" else 0})
BYC = pd.DataFrame(rows)
BYC.to_csv(f"{DATA}/by_country.csv", index=False)
R["by_country_top"] = [{"country": r.country, "n": int(r.wikidata_ghost_towns), "dmv": int(r.england_dmv),
                        "by": {k: int(getattr(r, f"reason_{k}")) for k in RKEYS}} for r in BYC.head(12).itertuples()]

# ---------- United States ----------
US = G[G.country == "United States"]
st = US.region.value_counts()
R["us_states_n"] = int(US.region.nunique())
R["us_top_states"] = [{"state": s, "n": int(n), "west": s in US_WEST, "mining": int(((US.region == s) & (US.reason == "mining")).sum())} for s, n in st.head(12).items()]
west = US[US.region.isin(US_WEST)]; rest = US[~US.region.isin(US_WEST)]
R["us_west_n"] = len(west); R["us_west_share"] = len(west) / len(US)
R["us_west_mining"] = int((west.reason == "mining").sum()); R["us_rest_mining"] = int((rest.reason == "mining").sum())
R["us_west_mining_share"] = R["us_west_mining"] / len(west); R["us_rest_mining_share"] = R["us_rest_mining"] / len(rest)
R["us_west_mining_hm"] = int(((west.reason == "mining") & west.confidence.isin(["high", "medium"])).sum())
R["us_west_mining_low"] = int(((west.reason == "mining") & (west.confidence == "low")).sum())
R["us_west_known"] = int((west.reason != "unknown").sum())
R["us_west_mining_of_known"] = R["us_west_mining"] / max(1, R["us_west_known"])
R["us_rest_known"] = int((rest.reason != "unknown").sum())
R["ca_nl"] = int(((G.country == "Canada") & (G.region == "Newfoundland and Labrador")).sum())
R["us_desc_formula"] = int(US.desc.fillna("").str.match(r"^(ghost town|human settlement|unincorporated community|place|abandoned village|former settlement|census-designated place) in ", case=False).sum())
R["us_desc_formula_share"] = R["us_desc_formula"] / len(US)
R["us_tx_mo"] = int(st.get("Texas", 0) + st.get("Missouri", 0))
R["us_tx"] = int(st.get("Texas", 0)); R["us_mo"] = int(st.get("Missouri", 0)); R["us_nv"] = int(st.get("Nevada", 0))
# area density for western states
S1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
from shapely.geometry import shape
from pyproj import Geod
geod = Geod(ellps="WGS84")
area = {}
for f in S1:
    p = f["properties"]
    if p["admin"] == "United States of America":
        g = shape(f["geometry"]); a = abs(geod.geometry_area_perimeter(g)[0]) / 1e6; area[p["name"]] = a
rows = []
for s in sorted(set(US.region.dropna())):
    u = US[US.region == s]
    rows.append({"state": s, "west": s in US_WEST, "ghost_towns": len(u), "mining": int((u.reason == "mining").sum()),
                 "mining_high_or_medium": int(((u.reason == "mining") & u.confidence.isin(["high", "medium"])).sum()),
                 "per_10000_km2": round(len(u) / area[s] * 1e4, 2) if s in area else None})
UST = pd.DataFrame(rows).sort_values("ghost_towns", ascending=False)
UST.to_csv(f"{DATA}/us_states.csv", index=False)
jsave([{"state": r.state, "n": int(r.ghost_towns), "mining": int(r.mining), "west": bool(r.west)} for r in UST.itertuples()], f"{DATA}/us_states.json")
R["bodie_ca_reason"] = G[(G.name == "Bodie") & (G.region == "California")].reason.tolist()
R["rhyolite_reason"] = G[(G.name == "Rhyolite") & (G.region == "Nevada")].reason.tolist()
R["west_low_names"] = sorted(set(G[(G.region.isin(US_WEST)) & (G.country == "United States") & (G.confidence == "low")].name))
R["us_west_states"] = [{"state": r.state, "n": int(r.ghost_towns), "mining": int(r.mining), "dens": r.per_10000_km2} for r in UST[UST.west].itertuples()]
R["us_west_dens"] = len(west) / sum(area[s] for s in US_WEST) * 1e4
R["us_rest_dens"] = len(rest[rest.region.isin(area) & ~rest.region.isin(["Alaska", "Hawaii"])]) / sum(a for s, a in area.items() if s not in US_WEST + ["Alaska", "Hawaii"]) * 1e4
R["us_dens_top"] = UST.sort_values("per_10000_km2", ascending=False).head(3).state.tolist()
R["us_names"] = {"bodie": "Bodie" in set(west.name), "rhyolite": "Rhyolite" in set(west.name)}

# ---------- England ----------
cc = V.county.value_counts()
R["dmv_counties"] = [{"county": c, "n": int(n)} for c, n in cc.head(10).items()]
R["dmv_n_counties"] = int(V.county.nunique())
R["dmv_top3"] = int(cc.head(3).sum()); R["dmv_top3_share"] = R["dmv_top3"] / len(V)
R["dmv_yorks"] = int(cc.get("Yorkshire", 0)); R["dmv_lincs"] = int(cc.get("Lincolnshire", 0)); R["dmv_nland"] = int(cc.get("Northumberland", 0))
per = V.depop_period.value_counts()
PER = ["Before 1348", "1348 to 1449", "1450 to 1549", "1550 to 1699", "1700 onwards"]
R["dmv_periods"] = [{"period": p, "n": int(per.get(p, 0))} for p in PER]
R["dmv_dated"] = int(sum(per.get(p, 0) for p in PER)); R["dmv_undated"] = len(V) - R["dmv_dated"]
R["dmv_full_record"] = int(V.full_record.fillna(False).astype(bool).sum())
cm = collections.Counter(x.strip() for s in V.cause_mentions.fillna("") for x in s.split(",") if x.strip())
R["dmv_causes"] = {k.replace(" ", "_"): int(v) for k, v in cm.items()}
R["dmv_with_desc_text"] = int(V.full_record.fillna(False).astype(bool).sum())
dm = V[V.depop_period.isin(PER)]
R["dmv_mid"] = [int((a + b) / 2) for a, b in zip(dm.depop_start, dm.depop_end)]
R["dmv_mid_median"] = int(np.median(R["dmv_mid"]))
R["dmv_1450_1699"] = (per.get("1450 to 1549", 0) + per.get("1550 to 1699", 0)) / R["dmv_dated"]
R["dmv_plague_period"] = per.get("1348 to 1449", 0) / R["dmv_dated"]
R["eng_wd_ghost"] = int(((G.uk_nation == "England")).sum())
R["dmv_vs_rest_world_wd"] = R["n_dmv"] / (R["n_ghost"] - R["us_n"])

# ---------- Soviet and post-Soviet ----------
PS = G[G.country.isin(POST_SOVIET)]
R["ps_wd_n"] = len(PS); R["ps_wd_by_country"] = [{"country": c, "n": int(n)} for c, n in PS.country.value_counts().items()]
R["ps_wd_reason"] = rcount(PS.reason); R["ps_wd_known"] = len(PS) - R["ps_wd_reason"]["unknown"]
R["ps_wd_nolabel"] = int(PS.name.isna().sum())
psE = [e for e in EL if e["country_ne"] in POST_SOVIET]
R["ps_wiki_n"] = len(psE); R["ps_wiki_reason"] = rcount(pd.Series([e["reason"] for e in psE]))
R["ps_wiki_countries"] = len({e["country_ne"] for e in psE})
R["ps_wiki_soviet_word"] = sum(1 for e in psE if "soviet" in (e["text"] + e["context"]).lower())
R["ps_wiki_by_country"] = [{"country": c, "n": n, "by": dict(collections.Counter(e["reason"] for e in psE if e["country_ne"] == c))}
                           for c, n in collections.Counter(e["country_ne"] for e in psE).most_common()]
R["soviet_word_outside"] = sum(1 for e in EL if e["country_ne"] not in POST_SOVIET and "soviet" in (e["text"] + e["context"]).lower())
R["chernobyl_wiki"] = sum(1 for e in EL if e["reason"] == "nuclear" and e["country_ne"] in ("Ukraine", "Belarus"))
R["chernobyl_wd"] = int((G.rule.fillna("").str.contains("Chernobyl")).sum())
R["by_wd_n"] = int((G.country == "Belarus").sum()); R["ru_wd_n"] = int((G.country == "Russia").sum())
R["ru_yaroslavl_wiki"] = sum(1 for e in EL if e["country_ne"] == "Russia" and "Yaroslavl" in e["text"])
R["tj_n"] = sum(1 for e in EL if e["country_ne"] == "Tajikistan")
R["ua_2022_wiki"] = sum(1 for e in EL if e["country_ne"] == "Ukraine" and "2022" in e["context"] + e["text"])

# ---------- when ----------
def era(y):
    return None if y is None else int(math.floor(y / 100) * 100)
wd_d = G[G.dissolved.notna()]
R["wd_dated"] = len(wd_d); R["wd_dated_unknownval"] = int(G.dissolved_unknown.sum())
R["wd_dated_since1900"] = int((wd_d.dissolved >= 1900).sum())
R["wd_dated_min"] = int(wd_d.dissolved.min()); R["wd_dated_max"] = int(wd_d.dissolved.max())
ey = [e for e in EL if e["year"] is not None]
R["wiki_dated"] = len(ey); R["wiki_dated_since1900"] = sum(e["year"] >= 1900 for e in ey)
R["wiki_dated_since1900_share"] = R["wiki_dated_since1900"] / len(ey)
R["wiki_dated_since2000"] = sum(e["year"] >= 2000 for e in ey)
R["wiki_dated_pre1600"] = sum(e["year"] < 1600 for e in ey)
R["wiki_dated_century"] = sum(e["year_how"] == "century" for e in ey)
dec = collections.Counter(int(e["year"] // 10 * 10) for e in ey if e["year"] >= 1900)
R["wiki_peak_decades"] = [{"decade": d, "n": n} for d, n in sorted(dec.items(), key=lambda x: (-x[1], x[0]))[:4]]
# timeline: twentieth century by decade for Wikipedia list + Wikidata; by century for everything
TL = []
for c in range(-1000, 2100, 100):
    row = {"century": c, "wiki": {k: 0 for k in RKEYS}, "wd": {k: 0 for k in RKEYS}, "dmv": 0}
    for e in ey:
        if era(e["year"]) == c: row["wiki"][e["reason"]] += 1
    for r in wd_d.itertuples():
        if era(r.dissolved) == c: row["wd"][r.reason] += 1
    row["dmv"] = sum(1 for m in R["dmv_mid"] if era(m) == c)
    TL.append(row)
R["timeline_century"] = [t for t in TL if t["century"] >= 1000 and (sum(t["wiki"].values()) + sum(t["wd"].values()) + t["dmv"]) > 0 or t["century"] >= 1000 and t["century"] <= 2000]
TD = []
for d in range(1840, 2030, 10):
    row = {"decade": d, "wiki": {k: 0 for k in RKEYS}, "wd": {k: 0 for k in RKEYS}}
    for e in ey:
        if int(e["year"] // 10 * 10) == d: row["wiki"][e["reason"]] += 1
    for r in wd_d.itertuples():
        if int(r.dissolved // 10 * 10) == d: row["wd"][r.reason] += 1
    TD.append(row)
R["timeline_decade"] = TD
R["wiki_war_dated"] = [e["year"] for e in ey if e["reason"] == "war"]
R["wiki_res_dated_median"] = int(np.median([e["year"] for e in ey if e["reason"] == "reservoir"]))
R["wiki_mining_dated_median"] = int(np.median([e["year"] for e in ey if e["reason"] == "mining"]))
R["wiki_dis_dated_n"] = sum(1 for e in ey if e["reason"] == "disaster")

# ---------- examples for the page ----------
def ex(name):
    s = G[G.name == name]
    return None if s.empty else {"name": name, "country": s.country.iloc[0], "reason": s.reason.iloc[0]}
R["examples"] = {k: ex(k) for k in ("Plymouth", "Craco", "Kolmanskop", "Centralia", "Varosha", "Times Beach", "Picher", "Bodie", "Rhyolite", "Oatman")}
assert all(R["examples"].values()), R["examples"]
R["hand_names"] = [h["name"] for h in H]
R["hand_reason"] = rcount(pd.Series([h["reason"] for h in H]))

# ---------- points for the page ----------
S_ = lambda v: v if isinstance(v, str) else ""
RI = {k: i for i, k in enumerate(RKEYS)}; CI = {"high": 0, "medium": 1, "low": 2, "none": 3}
def short(s, n=170):
    if not isinstance(s, str): return ""
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."
P = []
for r in G.itertuples():
    wt = ""
    if r.wiki_i is not None and not (isinstance(r.wiki_i, float) and math.isnan(r.wiki_i)):
        wt = short(E[int(r.wiki_i)]["text"], 260)
    elif isinstance(r.article, str):
        wt = short(r.article, 260)
    P.append([S_(r.name), round(r.lat, 4), round(r.lon, 4), RI[r.reason], CI[r.confidence], 0, S_(r.country), S_(r.region),
              None if pd.isna(r.dissolved) else int(r.dissolved), r.qid, short(r.desc), S_(r.rule), wt, "; ".join(c for c in r.classes)])
for r in V.itertuples():
    P.append([r.name, round(r.lat, 4), round(r.lon, 4), RI["medieval"], 0, 1, "United Kingdom", r.county, None, int(r.id),
              f"{'Deserted medieval village' if r.site_type == 'DMV' else 'Deserted medieval hamlet'}, {r.county}" + (f"; parish {r.parish_modern}" if isinstance(r.parish_modern, str) else ""),
              "Beresford's gazetteer", (f"Presumed depopulation: {r.depop_text}" if isinstance(r.depop_text, str) and r.depop_text else "") +
              (f" Cause mentioned: {r.cause_mentions}." if r.cause_mentions else ""), r.depop_period if isinstance(r.depop_period, str) else ""])
for r in A.itertuples():
    P.append([S_(r.name), round(r.lat, 4), round(r.lon, 4), RI[r.reason], CI[r.confidence], 2, S_(r.country), S_(r.region),
              None if pd.isna(r.dissolved) else int(r.dissolved), r.qid, short(r.desc), S_(r.rule), "", "; ".join(r.classes)])
for h in H:
    P.append([h["name"], h["lat"], h["lon"], RI[h["reason"]], 0, 3, h["country"], "", h["year"], h["link"] or "", "", h["rule"] or "",
              short(h["text"], 300), ""])
jsave({"fields": ["name", "lat", "lon", "reason", "conf", "src", "country", "region", "year", "id", "desc", "rule", "wiki", "extra"], "p": P},
      f"{DATA}/points.json")
R["n_points_page"] = len(P)
import json as _j
assert "NaN" not in _j.dumps(P), "NaN in points"
assert R["n_points_page"] == R["n_points_total"]
jsave(R, f"{DATA}/results.json", indent=1)
print({k: R[k] for k in ("n_ghost", "n_ancient", "n_dropped", "n_mexico", "n_dmv", "n_map", "us_share_wd", "dmv_share_map", "wd_known", "wd_known_share",
                         "n_wiki", "wiki_known", "wiki_top_reason", "us_west_n", "us_west_share", "us_west_mining", "us_rest_mining", "ps_wd_n", "ps_wiki_n",
                         "wd_dated", "wiki_dated", "dmv_dated")})
print(R["wiki_reason"], R["wiki_rank"])
print(R["wiki_by_cont"])
print(R["us_top_states"][:6], R["us_west_dens"], R["us_rest_dens"])
print(R["ps_wd_by_country"], R["ps_wd_reason"], R["ps_wiki_reason"], R["ps_wiki_by_country"])
print(R["wiki_peak_decades"], R["dmv_periods"], R["dmv_causes"])
