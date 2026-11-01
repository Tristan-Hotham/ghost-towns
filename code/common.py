"""Shared paths, reason categories and helpers for the ghost-towns study ("Ghost towns of the world").

Raw inputs (read in place, never copied into the repo):
  RAW  /home/claude/newdata/raw8/ghosttowns/ (fetched 2026):
         wikidata_ghost.tsv            Wikidata via QLever: items that are instances of (subclasses of) ghost town (Q74047),
                                       abandoned village (Q15661340) or deserted medieval village (Q1952852), with coordinates:
                                       item, English label, sitelinks, point, country label, class label (one row per
                                       class/point/country combination), dissolved date (P576), English description. CC0.
         wiki_List_of_ghost_towns.json English Wikipedia 'List of ghost towns by country' (parsed HTML). CC BY-SA 4.0.
         wiki_Ghost_town.json          English Wikipedia 'Ghost town' (parsed HTML). CC BY-SA 4.0.
  LV   England's deserted medieval villages, from the companion study 'The Villages That Vanished'
       (https://github.com/Tristan-Hotham/lost-villages, data/lost_villages.csv), itself built from Beresford's Lost
       Villages, University of Hull (https://dmv.wordpress.hull.ac.uk/), CC BY-NC-SA 4.0. Cloned by 01_clean.py if absent.
  GEO  Natural Earth 10m admin-0 countries and admin-1 states and provinces, 50m land (public domain).
Intermediates are written to WORK (outside the repo by default)."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("GHOST_RAW", "/home/claude/newdata/raw8/ghosttowns")
GEO = os.environ.get("GHOST_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
WORK = os.environ.get("GHOST_WORK", "/home/claude/work/ghost-towns")
LV = os.environ.get("GHOST_LV", os.path.join(WORK, "ext", "lost-villages"))
LV_REPO = "https://github.com/Tristan-Hotham/lost-villages.git"
DATA = os.path.join(ROOT, "data")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "ghost-towns"
PAGE_URL = "https://maps.tristanhotham.com/ghost-towns/"
REPO = "https://github.com/Tristan-Hotham/ghost-towns"
LV_PAGE = "https://tristan-hotham.github.io/lost-villages/"
LV_DOI = "https://doi.org/10.5281/zenodo.23677161"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
YEAR_NOW = 2026

# Reasons, in the order a place is assigned when its text matches more than one (see reasons.py).
# key, short label, full legend label, colour
REASONS = [
    ("nuclear", "Nuclear", "Nuclear accident zone (Chernobyl, Fukushima)", "#7FA80E"),
    ("war", "War", "War, conflict or military use", "#B8322A"),
    ("disaster", "Disaster", "Natural disaster, erosion or contamination", "#2B78B4"),
    ("reservoir", "Reservoir", "Flooded by a reservoir or dam", "#16A2A6"),
    ("mining", "Mining", "Mining or resource boomtown", "#D88A12"),
    ("medieval", "Medieval", "Deserted medieval village or plague", "#C04F92"),
    ("economic", "Decline", "Economic decline, depopulation or relocation", "#6D55A3"),
    ("unknown", "Unknown", "Reason not recorded", "#9AA0A4"),
]
RKEYS = [r[0] for r in REASONS]
RCOL = {r[0]: r[3] for r in REASONS}
RLAB = {r[0]: r[1] for r in REASONS}
RFULL = {r[0]: r[2] for r in REASONS}

# Former Soviet Union (as Natural Earth names them)
POST_SOVIET = ["Russia", "Ukraine", "Belarus", "Kazakhstan", "Uzbekistan", "Turkmenistan", "Kyrgyzstan", "Tajikistan",
               "Georgia", "Armenia", "Azerbaijan", "Moldova", "Estonia", "Latvia", "Lithuania"]
# The western United States: the 11 contiguous Mountain and Pacific states (Alaska and Hawaii reported separately).
US_WEST = ["Arizona", "California", "Colorado", "Idaho", "Montana", "Nevada", "New Mexico", "Oregon", "Utah",
           "Washington", "Wyoming"]

CONTINENT_FIX = {"Russia": "Europe", "Turkey": "Asia", "Cyprus": "Asia", "Georgia": "Asia", "Azerbaijan": "Asia",
                 "Armenia": "Asia", "Kazakhstan": "Asia"}


def dash(v):
    """House style: no em or en dashes, no double hyphens, in anything written to data/."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, (list, tuple)):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def _np(o):
    import numpy as np
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), default=_np)


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    raise ValueError(f)


def fill(text, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    """Replace {{path|fmt}} tokens from results.json, leaving the publisher's placeholders and IMG tokens alone."""
    def rep(m):
        k = m.group(1)
        if k in keep or k.startswith("IMG"):
            return m.group(0)
        return fmt(get(R, k), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def visible_text_ok(s, where=""):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in s, (where, bad, s[max(0, s.find(bad) - 80):s.find(bad) + 80])
