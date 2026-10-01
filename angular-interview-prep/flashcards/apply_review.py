"""Apply fact-check corrections (review_*.json) to cards.py.

Usage: python3 apply_review.py review_A.json review_B.json ...
Each review entry: {"q": original question, "verdict": "fix", "new_q"?: str, "new_a": str}.
Notes ("verdict": "note") are printed for a human decision and not applied.
"""
import json, sys
from pathlib import Path

here = Path(__file__).parent
src = (here / "cards.py").read_text()
fixed = notes = 0
for f in sys.argv[1:]:
    for e in json.loads(Path(f).read_text()):
        if "lesson_index" in e:
            continue
        if e.get("verdict") != "fix":
            notes += 1
            print(f"NOTE [{Path(f).name}] {e['q'][:70]}\n      {e.get('why', '')}\n")
            continue
        q_lit = json.dumps(e["q"], ensure_ascii=False)
        if q_lit not in src:
            print(f"!! question not found, skipped: {e['q'][:80]}")
            continue
        start = src.index(q_lit)
        a_start = src.index('"', start + len(q_lit))   # opening quote of the answer
        a_end = src.index('"),', a_start)               # closing quote of the answer
        old_a = json.loads(src[a_start:a_end + 1])
        new_a = e.get("new_a", old_a)
        new_q = e.get("new_q") or e["q"]
        src = (src[:start] + json.dumps(new_q, ensure_ascii=False) + src[start + len(q_lit):a_start]
               + json.dumps(new_a, ensure_ascii=False) + src[a_end + 1:])
        fixed += 1
(here / "cards.py").write_text(src)
print(f"applied {fixed} fixes, {notes} notes for review")
