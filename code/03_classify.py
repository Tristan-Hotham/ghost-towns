"""Step 3. Give every place a reason and a confidence (rules in reasons.py), match Wikipedia list entries to Wikidata
items, and write the clean data files.

Matching: a Wikipedia entry matches a Wikidata item (ghost or ancient scope) when their names agree after removing
accents, case, brackets and anything after a comma, and the Natural Earth country of the item is the entry's country.
Only unique matches are used. The matched entry's text then counts as evidence for the item's reason.
England: Wikidata ghost-town items within 2 km of a Beresford site with the same name are dropped as duplicates.
Run: python3 code/03_classify.py
"""
import os, sys, re, unicodedata, collections
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from reasons import classify, km

J = jload(f"{WORK}/clean.json"); E = jload(f"{WORK}/wiki_list.json")
W = pd.DataFrame(J["wd"]); V = pd.DataFrame(J["dmv"])


def norm(s):
    if not isinstance(s, str): return ""
    s = re.sub(r"\s*\(.*?\)", "", s).split(",")[0]
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


ALIAS = {"Cyprus": ["Cyprus", "Northern Cyprus"], "Norway": ["Norway"], "Palestine": ["Palestine", "Israel"],
         "Georgia": ["Georgia"], "Morocco": ["Morocco", "Western Sahara"]}
WIKI_CTY = {"Russian Federation": "Russia", "Republic of Ireland": "Ireland", "Ivory Coast": "Ivory Coast",
            "Czech Republic": "Czech Republic", "West Bank": "Palestine", "Gaza Strip": "Palestine"}
# 1. match
W["key"] = W.name.map(norm)
idx = collections.defaultdict(list)
for i, r in W[W.scope != "dropped"].iterrows():
    idx[(r.key, r.country)].append(i)
W["wiki_i"] = None
nmatch = 0
for j, e in enumerate(E):
    e["qid"] = None
    if e["kind"] == "note":
        continue
    cty = WIKI_CTY.get(e["subregion"], WIKI_CTY.get(e["country"], e["country"]))
    for nm in (e["link"], e["name"]):
        hits = [h for c in ALIAS.get(cty, [cty]) for h in idx.get((norm(nm), c), [])]
        if len(hits) == 1:
            i = hits[0]
            if W.at[i, "wiki_i"] is None:
                W.at[i, "wiki_i"] = j; e["qid"] = W.at[i, "qid"]; nmatch += 1
            break

# 1b. sentences of the 'Ghost town' article that link to a place: unique name match among ghost-scope items, and for
# titles of the form 'Place, State' the Natural Earth region (state or province) must agree
A = jload(f"{WORK}/article_mentions.json")
gidx = collections.defaultdict(list)
for i, r in W[W.scope == "ghost"].iterrows():
    gidx[r.key].append(i)
W["article"] = None; nart = 0
BIG = set(W.country.dropna()) | set(W.region.dropna())          # links to countries, states and provinces are not places
for a in A:
    parts = [p.strip() for p in re.sub(r"\s*\(.*?\)", "", a["title"]).split(",")]
    if len(parts) == 1 and parts[0] in BIG:
        continue
    hits = gidx.get(norm(parts[0]), [])
    if len(parts) > 1:
        hits = [i for i in hits if W.at[i, "region"] == parts[1] or W.at[i, "country"] == parts[1]]
    if len(hits) == 1 and W.at[hits[0], "article"] is None:
        W.at[hits[0], "article"] = a["sentence"]; nart += 1

# 2. classify Wikidata items
res = []
for r in W.itertuples():
    if r.scope == "dropped":
        res.append(("", "", "", [])); continue
    wt = None
    if r.wiki_i is not None:
        e = E[int(r.wiki_i)]; wt = (e["text"] + " " + e["context"]).strip()
    res.append(classify(desc=r.desc, wiki=wt, classes=r.classes, label=r.name or "", lat=r.lat, lon=r.lon, article=r.article))
W["reason"], W["confidence"], W["rule"], W["reasons_all"] = zip(*res)

# 3. England duplicates with Beresford
dup = []
eng = W[(W.scope == "ghost") & (W.uk_nation == "England")]
for i, r in eng.iterrows():
    for v in V.itertuples():
        if km(r.lat, r.lon, v.lat, v.lon) < 2 and norm(v.name) == r.key:
            dup.append(i); break
W["dup_dmv"] = W.index.isin(dup)

# 4. DMVs: medieval by definition (Beresford's gazetteer of deserted medieval villages and hamlets)
V["reason"] = "medieval"; V["confidence"] = "high"; V["rule"] = "Beresford's gazetteer of deserted medieval villages"

# 5. Wikipedia entries: country normalised for counting
for e in E:
    e["country_ne"] = WIKI_CTY.get(e["subregion"], WIKI_CTY.get(e["country"], e["country"]))

# 6. hand-placed list entries (see handplaced.py): not counted in any Wikidata total
from handplaced import HAND
H = []
for e in E:
    k = (e["country"], e["name"])
    if k in HAND and not e["qid"] and e["kind"] != "note":
        la, lo = HAND[k]
        H.append({"name": e["name"], "country": e["country_ne"], "lat": la, "lon": lo, "reason": e["reason"], "rule": e["reason_rule"],
                  "year": e["year"], "text": e["text"], "context": e["context"], "link": e["link"]})
assert len(H) == len(HAND), sorted(set(HAND) - {(h["country"] if False else None) for h in H})
pd.DataFrame(H).map(dash).to_csv(f"{DATA}/wikipedia_list_handplaced.csv", index=False)

# ---------- write data files ----------
out = W[W.scope != "dropped"].copy()
out["name_out"] = out.name.fillna("(no English label)")
cols = {"qid": "wikidata", "name_out": "name", "scope": "scope", "country": "country", "continent": "continent", "region": "region",
        "lat": "lat", "lon": "lon", "reason": "reason", "confidence": "confidence", "rule": "reason_rule", "reasons_all": "reasons_all",
        "dissolved": "dissolved_year", "classes": "wikidata_classes", "desc": "wikidata_description", "wd_country": "wikidata_country",
        "sitelinks": "sitelinks", "dup_dmv": "duplicate_of_beresford"}
D = out[list(cols)].rename(columns=cols)
D["reasons_all"] = D.reasons_all.map(lambda a: "; ".join(a))
D["wikidata_classes"] = D.wikidata_classes.map(lambda a: "; ".join(a))
D["wikipedia_list_entry"] = out.wiki_i.map(lambda i: "yes" if i is not None else "")
D = D.sort_values(["scope", "country", "name"], key=lambda s: s.str.lower() if s.dtype == object else s)
D.map(dash).to_csv(f"{DATA}/ghost_towns.csv", index=False)
Vo = V.rename(columns={"site_type": "type", "county": "historic_county", "depop_text": "presumed_depopulation",
                       "depop_start": "depop_start_year", "depop_end": "depop_end_year"})
Vo.to_csv(f"{DATA}/england_dmv.csv", index=False)
Eo = pd.DataFrame([{"continent": e["continent"], "list_section": e["country"], "subsection": e["subregion"], "country": e["country_ne"],
                    "name": e["name"], "linked_article": e["link"], "kind": e["kind"], "reason": e["reason"], "reason_rule": e["reason_rule"] or "",
                    "reason_from": e["reason_from"], "year": e["year"], "year_from": e["year_how"] or "", "wikidata_match": e["qid"] or "",
                    "text": e["text"], "group_sentence": e["context"]} for e in E])
Eo.map(dash).to_csv(f"{DATA}/wikipedia_list_entries.csv", index=False)
jsave({"W": W.drop(columns=["key"]).to_dict("records"), "V": V.where(V.notna(), None).to_dict("records"), "E": E, "nmatch": nmatch,
       "nart": nart, "H": H},
      f"{WORK}/classified.json")
g = W[(W.scope == "ghost") & ~W.dup_dmv]
print("article", nart, "| hand", len(H), "| matched", nmatch, "| dup", len(dup), "| ghost", len(g), g.reason.value_counts().to_dict(), g.confidence.value_counts().to_dict())
a = W[W.scope == "ancient"]; print("ancient", len(a), a.reason.value_counts().to_dict())
