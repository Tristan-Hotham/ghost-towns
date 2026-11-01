"""Step 6. Build index.html from code/page_template.html and code/fullscreen_snippet.html. Every number in the text is a
{{path|format}} token filled from data/results.json; facts stated in words are checked by the asserts below (they cover
the page, paper, blog and collage). 10.5281/zenodo.23857616 and https://blog.tristanhotham.com/2026/10/31/ghost-towns/ are left for the publisher.
Run: python3 code/06_build_site.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from reasons import PAT, ORDER, CLASS_REASON, ZONES

R = jload(f"{DATA}/results.json")
P = jload(f"{DATA}/points.json")["p"]
NM = {}
for p in P:
    NM.setdefault(p[0], []).append(p)

# ---------- facts stated in words ----------
assert R["by_country_top"][0]["country"] == "United States" and R["by_country_top"][1]["country"] == "Canada"
assert [c["country"] for c in R["by_country_top"][2:4]] == ["Greece", "Australia"]
assert R["n_dmv"] < R["us_n"] and R["n_dmv"] > R["ca_n"]                     # England second after the US
assert R["ca_nl"] > R["ca_n"] / 2
assert R["wiki_rank"][0] == "mining" and R["wiki_reason"]["war"] >= R["wiki_reason"]["disaster"] > R["wiki_reason"]["economic"] > R["wiki_reason"]["reservoir"] > R["wiki_reason"]["nuclear"] > R["wiki_reason"]["medieval"]
BC = {b["continent"]: b for b in R["wiki_by_cont"]}
assert BC["Oceania"]["top"] == "mining" and BC["Africa"]["top"] == "mining" and BC["Europe"]["top"] == "war"
assert R["wiki_au_mining"] > R["wiki_au_n"] / 2
assert R["us_nv"] == max(s["n"] for s in R["us_west_states"])
assert [s["state"] for s in R["us_top_states"][:2]] == ["Texas", "Missouri"]
assert R["bodie_ca_reason"] == ["unknown"] and R["rhyolite_reason"] == ["unknown"]
assert {"Galena", "Quartz Mountain", "Borax"} <= set(R["west_low_names"])
assert abs(R["us_west_dens"] - R["us_rest_dens"]) / R["us_rest_dens"] < .1         # "about as many"
assert R["us_west_mining_low"] > R["us_west_mining_hm"]                              # "mostly an inference from names"
assert [c["county"] for c in R["dmv_counties"][:3]] == ["Yorkshire", "Lincolnshire", "Northumberland"]
assert R["dmv_causes"]["enclosure_or_pasture"] > R["dmv_causes"]["emparking"] > R["dmv_causes"]["plague"]
assert R["dmv_1450_1699"] > .5 and R["dmv_plague_period"] < .2
assert R["ru_wd_n"] > R["by_wd_n"] == R["ps_wd_by_country"][1]["n"]
assert [w["decade"] for w in R["wiki_peak_decades"][:3]] == [2010, 1980, 1950]
assert R["wiki_dated_since1900_share"] > .8
for n, k in (("Plymouth", "disaster"), ("Kolmanskop", "mining"), ("Centralia", "disaster"), ("Varosha", "war"), ("Craco", "disaster"), ("Times Beach", "disaster")):
    assert R["examples"][n]["reason"] == k, n
txt = {}
for p in P:
    if p[5] in (0, 3): txt[p[0]] = txt.get(p[0], "") + " " + (p[12] + " " + p[11] + " " + p[10]).lower()
for e in jload(f"{WORK}/classified.json")["E"]:
    txt[e["name"]] = txt.get(e["name"], "") + " " + (e["text"] + " " + e["context"]).lower()
for n, w in (("Plymouth", "volcano"), ("Kolmanskop", "diamond"), ("Centralia", "mine fire"), ("Varosha", "1974"), ("Craco", "landslide"),
             ("Times Beach", "dioxin"), ("Khalmer-Yu", "1995"), ("Butugychag", "uranium"), ("Pyramiden", "soviet")):
    assert w in txt[n], (n, w)
for n in ("Pripyat", "Oradour-sur-Glane", "Hashima Island", "Tyneham", "Kadykchan", "Soledar", "Marinka", "Popasna"):
    assert n in NM, n
assert R["ua_2022_wiki"] >= 3 and "Mologa" in NM

# rules table for the page
RULES = [[k, RLAB[k] + (" (Chernobyl within 45 km, Fukushima within 30 km)" if k == "nuclear" else ""), PAT[k].replace("\\b", "").replace("\\", "")] for k in ORDER]
RULES += [["unknown", "From a Wikidata class (medium)", "; ".join(f"{c}: {RLAB[v].lower()}" for c, v in CLASS_REASON.items())],
          ["mining", "From the name (low)", "gold, silver, copper, mine, lode, placer, bonanza, quartz, galena, nugget, coal and other mining words"]]


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J_ = lambda o: json.dumps(dash(o), ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J_(R)).replace("/*RULES*/", J_(RULES))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    visible_text_ok(vis, "page")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
