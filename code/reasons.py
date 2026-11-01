"""Rules that give each place a reason for abandonment and a confidence. Every rule is a regular expression or a
distance test, written out here so anyone can check or change it.

A place can match several reasons. Its main reason is the first match in this order:
nuclear, war, disaster, reservoir, mining, medieval, economic (all matches are kept in `reasons_all`).

Confidence
  high    the reason is stated in words: the Wikidata description, the place's own entry in Wikipedia's
          'List of ghost towns by country' (including the sentence that introduces a group of places), or the sentence
          that links to it in Wikipedia's 'Ghost town' article; or the place
          lies inside a nuclear exclusion zone, or it is a deserted medieval village in Beresford's gazetteer.
  medium  the reason follows from the Wikidata class alone (for example 'mining community', 'pit village',
          'depopulated Palestinian village', 'deserted medieval village').
  low     only the place name suggests it: a mining word in the name (Gold, Silver, Copper, Mine, Lode, Placer and so on).
  none    no rule matched: reason 'unknown'.
"""
import math, re

ORDER = ["nuclear", "war", "disaster", "reservoir", "mining", "medieval", "economic"]

PAT = {
    "nuclear": r"chernobyl|chornobyl|fukushima|nuclear (disaster|accident|plant|power)|radiation|radioactiv|exclusion zone|kyshtym|mayak",
    "war": (r"\bwars?\b|wartime|battle|bomb(ed|ing|ardment)|shell(ed|ing)|\bmilitary\b|\barmy\b|soldiers|troops|invasion|invaded|"
            r"(military|enemy|foreign|german|soviet|israeli|turkish|armenian|japanese|nazi) occupation|occupied by|massacre|\bnazi|waffen|genocide|expelled|expulsion|deport|ethnic cleansing|conflict|"
            r"insurgen|guerrilla|fighting|\bsiege|artillery|firing range|training (area|ground|range|facility)|battle area|"
            r"air ?base|naval base|military base|missile|radar|sacked|sack of|"
            r"refugees?|front ?line|nakba|depopulated palestinian|population exchange|partition|airstrike|air raid|"
            r"razed|annex|forced to flee|fled the|evacuated .{0,40}(war|fighting|army)|liberation"),
    "disaster": (r"earthquake|tsunami|volcan|erupt|lava|hurricane|cyclone|typhoon|tornado|landslide|mudslide|avalanche|"
                 r"wildfire|bushfire|\bfires?\b|burn(ed|t) down|coastal erosion|eroded|erosion|swept (away|into the sea)|"
                 r"washed (away|into the sea)|into the (north )?sea|sea level|rising sea|storm|sand ?dunes?|sandstorm|"
                 r"desertification|drought|subsidence|sinkhole|mine fire|underground fire|toxic|contaminat|dioxin|pollut|"
                 r"chemical|floods?\b|flooding|flash flood|disaster"),
    "reservoir": (r"reservoir|\bdams?\b|hydro-?electric|hydro scheme|submerged|drowned|inundat|artificial lake|"
                  r"flooded (to|for|by|when|in order|so|under)|decant pond|tailings|under (the )?(water|lake)|lies (beneath|under)|beneath (the )?lake"),
    "mining": (r"\bmin(e|es|ing|ers?)\b|\bgold\b|gold ?rush|silver|copper|\bcoal\b|colliery|\btin\b|\bzinc\b|\blead\b mine|"
               r"quarr(y|ies|ying)|\bores?\b|boom ?town|\bboom\b|\brush\b|\boil\b|petroleum|uranium|diamond|nickel|"
               r"asbestos|phosphate|guano|whaling|lumber|logging|timber|sawmill|pulp mill|smelter|molybdenum|mercury|"
               r"sulphur|sulfur|salt works|saltpetre|nitrate|potash|borax|bauxite"),
    "medieval": (r"medieval|middle ages|black death|\bplague|pestilence|deserted village .{0,30}(england|yorkshire)|"
                 r"enclosure|sheep pasture|converted to pasture|emparked|1[1-5]th century"),
    "economic": (r"declin|depopulat|emigrat|railways?\b|railroads?\b|bypass|highway|closure|\bclosed\b|factory|\bmills?\b|"
                 r"industr|econom|unemploy|clearances?|cleared|evicted|eviction|resettle|relocat|\bmoved\b|abolished|"
                 r"liquidat|collective farm|kolkhoz|isolation|remote|last (permanent )?(residents?|inhabitants?)|"
                 r"population of (zero|0)|no permanent|uninhabited|airport|demolished (to|for|so)|make way|"
                 r"fishing (village|station)|company town|outcompeted|left for|harsh|lighthouse|underoccupied|"
                 r"speculat|commercial|weaken|colonial capital|capital (was )?moved|people left|youth left|aging|ageing|money shortage|poverty|big cities"),
}
RX = {k: re.compile(v, re.I) for k, v in PAT.items()}

# classes that imply a reason (medium confidence)
CLASS_REASON = {"mining community": "mining", "pit village": "mining", "mining region": "mining",
                "depopulated Palestinian village": "war", "destroyed settlement": "war",
                "deserted medieval village": "medieval", "prisoner-of-war camp": "war", "military base": "war",
                "closed city": "economic"}

NAME_MINING = re.compile(r"\b(gold|golden|silver|copper|mines?|mining|lode|placer|bonanza|eldorado|el dorado|quartz|"
                         r"\bore\b|carbonate|galena|nugget|diggings|colliery|coal|cobalt|borax|gypsum|tungsten|"
                         r"oro|plata|cobre|mineral|oil ?city|petrolia|argenta|argentine|bullion|cinnabar|garnet|"
                         r"telluride|ophir|bullfrog|chloride|leadville|zinc)\b", re.I)

# Nuclear exclusion zones: distance from the plant (km). Chernobyl: Ukraine's 30 km zone and the Polesie State
# Radioecological Reserve in Belarus, which reaches about 45 km north of the plant. Fukushima: the 20 to 30 km evacuation zone.
ZONES = {"Chernobyl": (51.3890, 30.0990, 45.0), "Fukushima": (37.4214, 141.0325, 30.0)}


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def in_zone(lat, lon):
    if lat is None:
        return None
    for name, (a, b, r) in ZONES.items():
        if km(lat, lon, a, b) <= r:
            return name
    return None


def text_reasons(txt):
    """All reasons whose pattern matches the text, in priority order, with the words that matched."""
    out = []
    if not isinstance(txt, str) or not txt:
        return out
    txt = re.sub(r"(often |also )?(called|known as|nicknamed|dubbed) (the )?[\"\u201c']?[\w ]{0,20}chernobyl", "", txt, flags=re.I)
    for k in ORDER:
        m = RX[k].search(txt)
        if m:
            if k == "disaster" and re.search(r"flood", m.group(0), re.I) and RX["reservoir"].search(txt):
                continue                                   # 'flooded to create a reservoir' is not a natural flood
            if k == "mining" and m.group(0).lower() in ("boom", "rush") and not re.search(r"gold|silver|oil|mining|land", txt, re.I):
                continue
            out.append((k, m.group(0)))
    return out


def classify(desc=None, wiki=None, classes=(), label="", lat=None, lon=None, article=None):
    """Return (reason, confidence, rule, all_reasons)."""
    z = in_zone(lat, lon)
    if z:
        return "nuclear", "high", f"inside the {z} exclusion zone", ["nuclear"]
    found = {}
    for src, txt in (("Wikipedia list", wiki), ("Ghost town article", article), ("Wikidata description", desc)):
        for k, w in text_reasons(txt):
            found.setdefault(k, (src, w))
    if found:
        ks = sorted(found, key=ORDER.index)
        src, w = found[ks[0]]
        return ks[0], "high", f"{src}: '{w.lower()}'", ks
    for c in classes:
        if c in CLASS_REASON:
            return CLASS_REASON[c], "medium", f"Wikidata class '{c}'", [CLASS_REASON[c]]
    if isinstance(label, str) and NAME_MINING.search(label):
        return "mining", "low", f"name: '{NAME_MINING.search(label).group(0).lower()}'", ["mining"]
    return "unknown", "none", "", []
