# Ghost towns of the world

Where places were abandoned, and why: a world map of 5,448 abandoned settlements in open data (3,374 Wikidata ghost towns and abandoned villages, and England's 2,074 deserted medieval villages and hamlets), each coloured by why it was abandoned (mining, war, disaster, reservoirs, nuclear accidents, medieval desertion, economic decline, or not recorded), with 4,249 ancient cities and sites as a separate layer.

Interactive page: https://maps.tristanhotham.com/ghost-towns/
Paper: https://doi.org/10.5281/zenodo.23857616
Blog post: https://blog.tristanhotham.com/2026/10/31/ghost-towns/
Sister study: [The Villages That Vanished](https://tristan-hotham.github.io/lost-villages/) (England's deserted medieval villages)

## Headline results

- The record is lopsided. 2,700 of Wikidata's 3,374 ghost towns (80%) are in the United States, 91% of them with a formulaic one-line description. With England's 2,074 deserted medieval villages added, England is 38% of the map and the two countries together 88%. Africa, Asia and South America hold 34 Wikidata ghost towns between them.
- The record rarely says why. Only 165 Wikidata ghost towns (4.9%) yield a reason, 61 of them from a mining word in the name alone. Wikipedia's 'List of ghost towns by country' gives a reason for 300 of its 492 places (61%).
- Where Wikipedia gives a reason, mining and resource booms lead (81), then war or military use (55) and natural disasters (54), economic decline (50), reservoirs (27) and nuclear accidents (24). Mining dominates Oceania (41 of 69) and Africa; war leads in Europe.
- The American West: 1,053 ghost towns in the 11 western states, 65 tied to mining (6.2%, against 0.9% elsewhere), but 47 of those only by name. Texas (335) and Missouri (289) have the most.
- England: of 270 dated deserted villages, 17% were deserted in 1348 to 1449 and 59% in 1450 to 1699, the age of enclosure.
- Soviet and after: 23 of Wikipedia's places in Ukraine and Belarus were evacuated after Chernobyl; 7 Ukrainian towns emptied by fighting since 2022. Wikidata has 62 post-Soviet ghost towns, 10 with a reason.
- When: 85% of dated Wikipedia entries were abandoned after 1900; the busiest decade is the 2010s.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; loads `data/points.json` and `data/us_states.json`). |
| `header.png` | Social card, 1200 x 630. |
| `data/ghost_towns.csv` | 3,374 Wikidata ghost towns and 4,249 ancient sites (column `scope`): Wikidata ID, name, country, continent, region, point, reason, confidence, the rule that gave it, all reasons matched, dissolution year, classes, description, whether a Wikipedia list entry was matched. CC BY 4.0. |
| `data/england_dmv.csv` | England's 2,074 deserted medieval villages and hamlets from Beresford's gazetteer, with county, parish, point, presumed depopulation and causes mentioned. CC BY-NC-SA 4.0. |
| `data/wikipedia_list_entries.csv` | Every entry of Wikipedia's 'List of ghost towns by country' with its text, reason, year and Wikidata match. CC BY-SA 4.0. |
| `data/wikipedia_list_handplaced.csv` | 44 well-known list entries placed by hand (approximate positions). CC BY-SA 4.0. |
| `data/by_country.csv`, `data/us_states.csv` | Counts by country and reason, and by US state with mining and density. CC BY 4.0. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/us_states.json` | Page data. |
| `code/` | Scripts, run in order (below), the reason rules (`reasons.py`), hand-placed positions (`handplaced.py`) and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Places: Wikidata items with coordinates that are instances of ghost town (Q74047), abandoned village (Q15661340) or deserted medieval village (Q1952852), or a subclass. Kept as ghost towns if a class is in the ghost town family (or 'former settlement' without an ancient class); ancient cities and archaeological sites go to a separate layer; 2,456 living Mexican municipalities (a faulty subclass link) and 42 other living places are dropped. Country and region from Natural Earth.
- England: deserted villages and hamlets from Beresford's Lost Villages (University of Hull), as cleaned for The Villages That Vanished.
- Reasons: keyword rules (`code/reasons.py`) on the place's Wikipedia list entry (with the sentence introducing its group), a linked sentence in Wikipedia's 'Ghost town' article, and the Wikidata description; a fixed order picks the main reason when several match (nuclear, war, disaster, reservoir, mining, medieval, economic). Chernobyl (45 km) and Fukushima (30 km) zones count as nuclear. Confidence: high (stated in words, or a zone), medium (Wikidata class), low (mining word in the name).
- Hand-placed: 44 famous list entries missing from the Wikidata extract, at approximate positions, shown on the map but not counted.
- Dates: Wikidata dissolution dates; for list entries, the first year or century after a word of abandonment; England's presumed dates at the middle of each range.
- Caveats: the map shows what has been recorded, not everywhere abandoned; reasons come from simple word rules on short texts; the mining West rests mostly on names; Wikipedia's list is a selection; hand-placed positions are approximate.

## How to rerun

Needs Python 3 with pandas, shapely, pyproj, beautifulsoup4, lxml, matplotlib, fontTools and Pillow, xelatex and pdftotext, and Playwright for the QA step. Raw inputs are read in place from `/home/claude/newdata/raw8/ghosttowns/` and Natural Earth from `/home/claude/newdata/raw/geo/` (set in `code/common.py`); the England data are cloned from https://github.com/Tristan-Hotham/lost-villages. Intermediate files go to `/home/claude/work/ghost-towns` (set `GHOST_WORK` to change).

```
python3 code/01_clean.py        # Wikidata items, scope, countries; England's deserted villages
python3 code/02_wiki.py         # Wikipedia list entries and article sentences
python3 code/03_classify.py     # reasons, matching, data files
python3 code/04_results.py      # results.json and page data
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_build_site.py   # index.html
python3 code/07_paper.py        # paper PDF
python3 code/08_readme.py       # README and LICENSE
python3 code/09_release.py      # blog post, Zenodo files, Reddit post
python3 reddit/collage.py       # collage
python3 code/10_qa.py           # browser and text checks
```

## Sources and licences

- Wikidata (https://www.wikidata.org/), via QLever. CC0.
- Beresford's Lost Villages, University of Hull (https://dmv.wordpress.hull.ac.uk/), from M. Beresford and J. Hurst's gazetteer, via https://github.com/Tristan-Hotham/lost-villages. CC BY-NC-SA 4.0.
- English Wikipedia: 'List of ghost towns by country' and 'Ghost town'. CC BY-SA 4.0.
- Natural Earth (public domain).
- Base map tiles on the page: © Esri.

Licences here: code MIT (see `LICENSE`); text and figures CC BY-NC-SA 4.0 (they include England's deserted villages); data files as in the table above.

## Citation

Hotham, T. (2026) Ghost towns of the world: where places were abandoned, and why, in Wikidata, Wikipedia and England's deserted medieval villages. Zenodo. https://doi.org/10.5281/zenodo.23857616

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
