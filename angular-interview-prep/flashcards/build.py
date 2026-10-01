"""Build the flashcard outputs from cards.py.

Outputs:
  cards.json              - the deck as data
  index.html              - the self-contained flashcard app (Cards + Listen modes)
  ../13-flashcards.md     - the same deck as a readable document, grouped by topic
"""
import json
from pathlib import Path

from cards import CARDS, WEAK

here = Path(__file__).parent
cards = [{"topic": t, "q": q, "a": a} for t, q, a in CARDS]

(here / "cards.json").write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n")

template = (here / "template.html").read_text()
html = (template
        .replace("/*__CARDS__*/[]", json.dumps(cards, ensure_ascii=False))
        .replace("/*__WEAK__*/[]", json.dumps(sorted(WEAK))))
(here / "index.html").write_text(html)

topics = list(dict.fromkeys(c["topic"] for c in cards))
lines = [
    "# 13 — Flashcards",
    "",
    f"> {len(cards)} cards, the same deck as the [flashcard app](flashcards/index.html). "
    "Topics marked **(weak area)** came out weakest in the mock interview, so do those first. "
    "Cover the answer, say yours out loud, then check.",
    "",
]
for t in topics:
    flag = " (weak area)" if t in WEAK else ""
    lines += [f"## {t}{flag}", ""]
    for c in (c for c in cards if c["topic"] == t):
        lines += [f"**Q: {c['q']}**", "", f"A: {c['a']}", ""]
(here.parent / "13-flashcards.md").write_text("\n".join(lines))

print(f"{len(cards)} cards, {len(topics)} topics")
