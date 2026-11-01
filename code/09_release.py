"""Step 9. Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), Reddit post (reddit/post.md).
Numbers in the blog's alt text and in the post are checked against results.json here.
Run: python3 code/09_release.py
"""
import os, re, sys, zipfile, json as _json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Ghost_Towns_of_the_World"

# ---------- numbers written into alt text ----------
top = {c["country"]: c["n"] for c in R["by_country_top"]}
assert (top["United States"], R["n_dmv"], top["Canada"], top["Greece"], top["Australia"]) == (2700, 2074, 265, 101, 58)
U = {s["state"]: s["n"] for s in jload(f"{DATA}/us_states.json")}
assert (U["Texas"], U["Missouri"], U["Nevada"], U["California"], U["Utah"]) == (335, 289, 200, 146, 134)
assert [p["n"] for p in R["dmv_periods"]] == [20, 47, 62, 98, 43] and (R["dmv_yorks"], R["dmv_lincs"], R["dmv_nland"]) == (358, 220, 165)
BC = {b["continent"]: b for b in R["wiki_by_cont"]}
assert BC["Oceania"]["top"] == "mining" and BC["Africa"]["top"] == "mining" and BC["Europe"]["top"] == "war"
assert R["wiki_peak_decades"][0]["decade"] == 2010
TD = {t["decade"]: t for t in R["timeline_decade"]}
assert TD[1980]["wiki"]["nuclear"] + TD[1980]["wd"]["nuclear"] > 0
assert sum(TD[d]["wiki"]["reservoir"] + TD[d]["wd"]["reservoir"] for d in (1930, 1940, 1950, 1960)) >= 10

# ---------- blog ----------
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, used
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\})", post)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
visible_text_ok(vis, "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Ghost towns of the world: where places were abandoned, and why",
        "slug": "ghost-towns",
        "excerpt": f"I mapped {R['n_map']:,} abandoned settlements in open data and coloured each by why it emptied: mining, war, disaster, reservoirs, Chernobyl and medieval decline. {round(R['us_share_wd'] * 100)}% of Wikidata's ghost towns are American, and only {round(R['wd_known_share'] * 100)}% say why.",
        "seo_description": "A world map of ghost towns and abandoned villages coloured by why they were abandoned, and what open data does not record.",
        "tags": ["ghost towns", "abandoned places", "deserted medieval villages", "Wikidata", "maps", "data visualisation", "history", "Chernobyl"],
        "header_alt": f"Title card reading 'Ghost towns of the world' beside a world map of abandoned settlements: grey points across the United States, a magenta block over England and coloured points for mining, war, disasters, reservoirs and nuclear zones elsewhere. Text: {R['n_map']:,} abandoned settlements, coloured by why they emptied; only {round(R['wd_known_share'] * 100)}% of Wikidata's ghost towns say why."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# ---------- Zenodo ----------
Zd = f"{REL}/zenodo"; os.makedirs(Zd, exist_ok=True)
for fn in os.listdir(Zd):
    os.remove(os.path.join(Zd, fn))
os.link(f"{REL}/paper/{NAME}.pdf", f"{Zd}/{NAME}.pdf")
zp = f"{Zd}/ghost-towns_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"ghost-towns/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        z.write(os.path.join(ROOT, fn), f"ghost-towns/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", "\u201c").replace("''", "\u201d").replace("`", "\u2018")
zmeta = {"title": "Ghost Towns of the World: Where Places Were Abandoned, and Why, in Wikidata, Wikipedia and England's Deserted Medieval Villages",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE_URL}\">{PAGE_URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>.</p>"
                        "<p>Sources: Wikidata (CC0); Beresford's Lost Villages, University of Hull (CC BY-NC-SA 4.0); English Wikipedia (CC BY-SA 4.0); Natural Earth (public domain). "
                        "The paper, figures and the England table are CC BY-NC-SA 4.0; tables with Wikipedia text CC BY-SA 4.0; other data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["ghost towns", "abandoned settlements", "deserted medieval villages", "Wikidata", "Wikipedia", "mining towns", "Chernobyl", "open data bias", "data visualisation"],
         "license": "cc-by-nc-sa-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE_URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23677161", "relation": "references", "resource_type": "publication-workingpaper"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://dmv.wordpress.hull.ac.uk/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "notes": AI}
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
visible_text_ok(s, "meta")
jsave(zmeta, f"{Zd}/metadata.json", indent=2)

# ---------- Reddit post ----------
pm = f"""## Title

[OC] Ghost towns of the world: {R['n_map']:,} abandoned settlements coloured by why they were abandoned. {round(R['us_share_wd'] * 100)}% of Wikidata's ghost towns are in the US, England's deserted medieval villages are {round(R['dmv_share_map'] * 100)}% of the map, and only {round(R['wd_known_share'] * 100)}% of Wikidata's ghost towns say why they died

## Body

I mapped every ghost town, abandoned village and deserted medieval village with a position in Wikidata ({R['n_ghost']:,}, after dropping {R['n_mexico']:,} living Mexican municipalities that reach the class through a faulty link), plus England's {R['n_dmv']:,} deserted medieval villages from Beresford's gazetteer, and gave each a reason with simple, published keyword rules on Wikidata descriptions and Wikipedia text. The map turns out to show who has catalogued abandonment: {R['us_n']:,} of Wikidata's ghost towns are American and all of Africa has {R['africa_n']}. Only {R['wd_known']} Wikidata ghost towns yield a reason, {R['wd_mining_low']} of them just from a mining word in the name. Wikipedia's 'List of ghost towns by country' is more talkative: {R['wiki_known']} of {R['n_wiki']} places give a reason, led by mining ({R['wiki_reason']['mining']}), then war ({R['wiki_reason']['war']}) and disasters ({R['wiki_reason']['disaster']}), decline ({R['wiki_reason']['economic']}), reservoirs ({R['wiki_reason']['reservoir']}) and Chernobyl and Fukushima ({R['wiki_reason']['nuclear']}). In the American West, {R['us_west_mining']} of {R['us_west_n']:,} ghost towns are tied to mining, mostly by name; Bodie and Rhyolite have no reason recorded at all. {R['n_hand']} famous places missing from Wikidata's ghost town class (Pripyat, Hashima, Oradour-sur-Glane...) are placed by hand and ringed. Interactive map with filters: {PAGE_URL}

## Source comment

Sources: Wikidata (CC0), items classed as ghost town (Q74047), abandoned village (Q15661340) or deserted medieval village (Q1952852), via QLever; Beresford's Lost Villages, University of Hull (CC BY-NC-SA 4.0); English Wikipedia, 'List of ghost towns by country' and 'Ghost town' (CC BY-SA 4.0); Natural Earth. Reasons from keyword rules, in a fixed order when several match, with high, medium or low confidence; full rules in the repo.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE_URL}
Paper: https://doi.org/{{10.5281/zenodo.23857616}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/ghost-towns/}}
"""
visible_text_ok(pm, "post")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(pm)
print("blog words", words, "; figures", len(used), "; zenodo", sorted(os.listdir(Zd)), os.path.getsize(zp) // 1024, "KB zip")
