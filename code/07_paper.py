"""Step 7. Paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_Ghost_Towns_of_the_World.tex
and compile it with xelatex (figures from step 5 in release/paper/). The DOI keeps the publisher's 10.5281/zenodo.23857616 placeholder.
Run: python3 code/07_paper.py
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Ghost_Towns_of_the_World"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def sub(m):
    k = m.group(1)
    if k == "DOI":
        return m.group(0)
    v = get(R, k); f = m.group(3)
    if f == "pct": return f"{round(v * 100)}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f in (None, "raw"): return tex(v)
    return fmt(v, f)


src = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
out = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", sub, src)
out = re.sub(r'(^|[\s(])"', r"\1``", out, flags=re.M).replace('"', "''")      # typographic quotes
out = re.sub(r"(^|[\s(])'", r"\1`", out, flags=re.M)
assert not re.search(r"\{\{[A-Za-z_]", out.replace("10.5281/zenodo.23857616", ""))
body = re.sub(r"(?m)^%.*$", "", out)
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in body, bad
assert "--" not in body
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
pdf = f"{OUT}/{NAME}.pdf"
assert os.path.exists(pdf), r.stdout[-3000:]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
print(NAME, n, "pages")
assert 8 <= n <= 15, n
for ext in ("aux", "log", "out", "bbl", "blg"):
    if os.path.exists(f"{OUT}/{NAME}.{ext}"):
        os.remove(f"{OUT}/{NAME}.{ext}")
