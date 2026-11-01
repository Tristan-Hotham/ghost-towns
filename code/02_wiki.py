"""Step 2. Parse Wikipedia's 'List of ghost towns by country' into one entry per place, with its continent, country,
the text written about it (and the sentence that introduces its group, when a list is introduced by one, such as
'After the Chernobyl nuclear disaster in 1986, hundreds of settlements ... were evacuated, including:'), the article
it links to, a reason from the rules in reasons.py, and a year of abandonment where the text gives one.
Navigation boxes, galleries, tables and 'See also' sections are skipped. The United States and Canada have their own
lists on Wikipedia, so their sections here hold only a pointer and give no entries.
Run: python3 code/02_wiki.py
"""
import os, sys, re, collections
from bs4 import BeautifulSoup, NavigableString, Tag
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from reasons import classify, text_reasons

NOTE = re.compile(r"^(Most|Many|Some|These|There|In |After|During|Several|A number|Numerous|Other|All |Since|Around|Following|As )")
STOP = {"See also", "References", "External links", "Further reading", "Bibliography", "Notes"}
ABANDON = re.compile(r"abandon|desert|evacuat|destroy|flooded|submerged|demolish|depopulat|\bleft\b|cleared|swept|washed|"
                     r"closed|evicted|declin|emptied|razed|burn|expelled|relocat|last (permanent )?(resident|inhabitant)|"
                     r"ceased|vacated|disappear|\blost\b|ruin|sacked", re.I)
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])s?\b")
CENT = re.compile(r"\b(early |mid-?|late )?(1[0-9]|20|[2-9])(st|nd|rd|th)[ -]century", re.I)


def clean(t):
    t = re.sub(r"\[\s*(\d+|[a-z]|citation needed|note \d+|when\?|which\?)\s*\]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def year_of(text):
    """Year of abandonment: the first year (or century, as its middle) at or after the first abandonment word;
    failing that, none. Returns (year, how)."""
    m = ABANDON.search(text)
    if not m:
        return None, None
    tail = text[m.start():]
    cands = []
    for y in YEAR.finditer(tail):
        cands.append((y.start(), int(y.group(1)) + (5 if y.group(0).endswith("s") else 0), "year"))
    for c in CENT.finditer(tail):
        n = int(c.group(2)); q = (c.group(1) or "").strip().lower()
        base = (n - 1) * 100
        y = base + (20 if q == "early" else 80 if q == "late" else 50)
        cands.append((c.start(), y, "century"))
    cands = [c for c in cands if c[1] <= YEAR_NOW]
    if not cands:
        return None, None
    c = min(cands)
    return c[1], c[2]


def parse(path):
    h = jload(path)["html"]
    soup = BeautifulSoup(h, "lxml")
    root = soup.select_one(".mw-parser-output") or soup
    for bad in root.select("style, table, .navbox, .gallery, .thumb, figure, .reflist, sup.reference, .hatnote, .mw-editsection, .sidebar, .metadata"):
        bad.decompose()
    path_ = ["", "", ""]; out = []; last_p = ""; stop = False
    for el in root.find_all(["h2", "h3", "h4", "p", "ul"], recursive=True):
        if el.name in ("h2", "h3", "h4"):
            lv = int(el.name[1]) - 2; t = clean(el.get_text())
            path_[lv] = t
            for k in range(lv + 1, 3): path_[k] = ""
            stop = path_[0] in STOP; last_p = ""
            continue
        if stop or not path_[0] or not path_[1]:
            continue
        if el.name == "ul" and el.find_parent("ul"):
            continue                                  # nested lists are read with their parent item
        if el.name == "p":
            t = clean(el.get_text())
            if not t:
                continue
            if NOTE.match(t):
                a = el.find("a", href=re.compile(r"^/wiki/[^:]+$"))
                out.append({"continent": path_[0], "country": path_[1], "subregion": path_[2], "text": t, "context": "",
                            "link": a.get("title") if a else None, "kind": "note"})
                last_p = t                            # a general sentence introduces the list that follows it
                continue
            if t.endswith(":") or re.search(r"(including|include|following|such as|these are|listed below|below)[^.]*[:.]?$", t, re.I) and len(t) < 600:
                last_p = t
                continue
            last_p = ""
            a = el.find("a", href=re.compile(r"^/wiki/[^:]+$"))
            out.append({"continent": path_[0], "country": path_[1], "subregion": path_[2], "text": t, "context": "",
                        "link": a.get("title") if a else None, "kind": "paragraph"})
            continue
        for li in el.find_all("li", recursive=False):
            t = clean(li.get_text(" "))
            if not t or len(t) < 3:
                continue
            a = li.find("a", href=re.compile(r"^/wiki/[^:]+$"))
            first_a = a.get("title") if a and t.lower().startswith(a.get_text().strip().lower()[:6]) else None
            out.append({"continent": path_[0], "country": path_[1], "subregion": path_[2], "text": t, "context": last_p,
                        "link": first_a or (a.get("title") if a else None), "kind": "list item"})
        last_p = ""
    return out


def lead_name(t, link=None):
    """The place's own name: the linked article if the text starts with it, else the start of the text up to the first
    comma, bracket or verb (after dropping openings such as 'The small town of')."""
    t = re.sub(r"^(the )?([\w -]{0,40}?\b)?(town|city|village|settlement|island|hamlet|port|resort) of ", "", t, flags=re.I)
    if link:
        base = re.sub(r"\s*\(.*\)$", "", link).split(",")[0]
        if t.lower().startswith(base.lower()):
            return base
    m = re.match(r"^(.{2,60}?)(\s*\(|,| is | was | were | has | had | in the | on the | near |: | - | – )", t + " is ")
    return m.group(1).strip(" .") if m else t[:60]


def article_mentions(path):
    """Sentences of the 'Ghost town' article that link to a place, keyed by the linked article's title."""
    soup = BeautifulSoup(jload(path)["html"], "lxml")
    root = soup.select_one(".mw-parser-output") or soup
    for bad in root.select("style, table, .navbox, .reflist, sup.reference, .hatnote, .mw-editsection, .sidebar, .metadata, figure, .thumb, .gallery"):
        bad.decompose()
    out = {}; sec = ""
    for el in root.find_all(["h2", "h3", "h4", "p", "li"]):
        if el.name[0] == "h":
            sec = clean(el.get_text()); continue
        if sec in STOP or (el.name == "li" and el.find_parent(class_=re.compile("toc"))):
            continue
        txt = clean(el.get_text(" "))
        for a in el.find_all("a", href=re.compile(r"^/wiki/[^:]+$")):
            t = a.get("title"); at = a.get_text().strip()
            if not t or not at:
                continue
            i = txt.find(at)
            if i < 0:
                continue
            s0 = txt.rfind(". ", 0, i); s0 = 0 if s0 < 0 else s0 + 2; s1 = txt.find(". ", i); s1 = len(txt) if s1 < 0 else s1 + 1
            out.setdefault(t, {"title": t, "anchor": at, "section": sec, "sentence": txt[s0:s1].strip()})
    return list(out.values())


if __name__ == "__main__":
    jsave(article_mentions(f"{RAW}/wiki_Ghost_town.json"), f"{WORK}/article_mentions.json")
    E = parse(f"{RAW}/wiki_List_of_ghost_towns.json")
    for e in E:
        r, conf, rule, allr = classify(wiki=(e["text"] + " " + e["context"]).strip())
        e["reason"], e["reason_rule"], e["reasons_all"] = r, rule, allr
        e["reason_from"] = "own text" if text_reasons(e["text"]) else ("group sentence" if r != "unknown" else "")
        y, how = year_of(e["text"])
        if y is None and e["context"]:
            y, how = year_of(e["context"])
        e["year"], e["year_how"] = y, how
        e["name"] = lead_name(e["text"], e["link"])

        e["country_norm"] = {"Russian Federation": "Russia", "Republic of Ireland": "Ireland", "Palestine": "Palestine"}.get(e["country"], e["country"])
    c = collections.Counter(e["reason"] for e in E)
    print(len(E), "entries;", dict(c), "; with a year", sum(e["year"] is not None for e in E))
    print(collections.Counter(e["continent"] for e in E))
    jsave(E, f"{WORK}/wiki_list.json")
