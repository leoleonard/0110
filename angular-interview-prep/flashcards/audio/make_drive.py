"""Render the flashcard deck as ~2 hours of MP3 audio for driving.

Each card: question (voice A) -> 6 s silence to answer out loud -> soft tone -> answer (voice B).
Tracks are grouped by theme, weak areas first.
"""
import json, re, sys, time
from pathlib import Path
import numpy as np
import lameenc
from kokoro_onnx import Kokoro

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
CARDS = json.loads(Path("/home/user/0110/angular-interview-prep/flashcards/cards.json").read_text())

TRACKS = [
    ("01-weak-areas-part-1", "Weak areas, part one", ["Change detection", "Event loop", "RxJS"]),
    ("02-weak-areas-part-2", "Weak areas, part two", ["Dependency injection", "State management", "REST & HTTP", "Answer technique"]),
    ("03-angular-core", "Angular core", ["Versions", "Signals", "Components & templates", "Routing & templates", "Forms"]),
    ("04-angular-platform", "Angular platform, testing and security", ["HTTP, SSR & testing", "Testing", "Build & tooling", "Security", "Errors & monitoring"]),
    ("05-web-fundamentals", "JavaScript, TypeScript and the browser", ["JavaScript", "TypeScript", "CSS & rendering", "HTML & styles", "Accessibility", "Web platform", "i18n"]),
    ("06-engineering-and-product", "Engineering practice and product", ["Component library", "Architecture", "Patterns & quality", "Git & CI", "Agile", "Product & stakeholders"]),
]
covered = {t for _, _, ts in TRACKS for t in ts}
missing = {c["topic"] for c in CARDS} - covered
assert not missing, f"topics not in any track: {missing}"

SR = 24000
Q_VOICE, A_VOICE, HOST_VOICE = "am_michael", "af_heart", "af_heart"
THINK_S, GAP_S = 6.0, 1.6

# Words the voice would otherwise mangle.
SAY = [
    (r"\bRxJS\b", "R X J S"), (r"\bNgRx\b", "N G R X"), (r"\bngrx\b", "N G R X"),
    (r"\bJSON\b", "jason"), (r"\bnpm\b", "N P M"), (r"\bnpm ci\b", "N P M C I"),
    (r"\bI/O\b", "I O"), (r"\bUI\b", "U I"), (r"\bUX\b", "U X"), (r"\bCI/CD\b", "C I C D"),
    (r"\bES(\d{4})\b", r"E S \1"), (r"\bES8\b", "E S 8"), (r"\bSPA\b", "S P A"),
    (r"\bng-content\b", "N G content"), (r"\bng-packagr\b", "N G packager"), (r"\bng update\b", "N G update"),
    (r"\bng add\b", "N G add"), (r"\bng generate\b", "N G generate"), (r"\bng-deep\b", "N G deep"),
    (r"\bngCspNonce\b", "N G C S P nonce"), (r"\bngOnChanges\b", "N G on changes"), (r"\bngOnInit\b", "N G on init"),
    (r"\bngDoCheck\b", "N G do check"), (r"\bngOnDestroy\b", "N G on destroy"),
    (r"\bngAfter(\w+)", lambda m: "N G after " + split_camel(m.group(1))),
    (r"\bngIf\b", "N G if"), (r"\bngFor\b", "N G for"), (r"\bngSwitch\b", "N G switch"),
    (r"\bngTemplateOutlet\b", "N G template outlet"), (r"\bNgOptimizedImage\b", "N G optimized image"),
    (r"\bNgComponentOutlet\b", "N G component outlet"), (r"\bNG_VALUE_ACCESSOR\b", "N G value accessor"),
    (r"\bCSP_NONCE\b", "C S P nonce"), (r"\bXSRF-TOKEN\b", "X S R F token"), (r"\bX-XSRF-TOKEN\b", "X X S R F token"),
    (r"\bDTOs\b", "D T Os"), (r"\bADRs\b", "A D Rs"), (r"\bSLAs\b", "S L As"), (r"\bRTL\b", "R T L"),
    (r"\bCDK\b", "C D K"), (r"\bSSR\b", "S S R"), (r"\bLCP\b", "L C P"), (r"\bINP\b", "I N P"),
    (r"\bCLS\b", "C L S"), (r"\bFID\b", "F I D"), (r"\bCSSOM\b", "C S S O M"), (r"\bDOM\b", "dom"),
    (r"\bGPU\b", "G P U"), (r"\bWIP\b", "work in progress"), (r"\bPKCE\b", "pixie"), (r"\bXSS\b", "X S S"),
    (r"\bCSRF\b", "C S R F"), (r"\bETag\b", "E tag"), (r"\bOpenAPI\b", "Open A P I"), (r"\bAPI\b", "A P I"),
    (r"\bAPIs\b", "A P Is"), (r"\bHTTP\b", "H T T P"), (r"\bHTML\b", "H T M L"), (r"\bCSS\b", "C S S"),
    (r"\bURL\b", "U R L"), (r"\bIDs?\b", "I D"), (r"\bid\b", "I D"), (r"\bids\b", "I Ds"), (r"\bDI\b", "D I"),
    (r"\bA/B\b", "A B"), (r"\bWCAG\b", "W cag"), (r"\bARIA\b", "aria"), (r"\bNVDA\b", "N V D A"),
    (r"\bDORA\b", "dora"), (r"\bRFCs?\b", "R F C"), (r"\bSVG\b", "S V G"), (r"\bRTL\b", "R T L"),
    (r"\bvs\b", "versus"), (r"\be\.g\.", "for example"),
]

def split_camel(word: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", word)

def speakable(text: str) -> str:
    for pat, rep in SAY:
        text = re.sub(pat, rep, text)
    # split remaining camelCase / PascalCase identifiers: markForCheck -> mark For Check
    text = re.sub(r"\b[a-zA-Z]+[a-z][A-Z][A-Za-z]*\b", lambda m: split_camel(m.group(0)), text)
    for pat, rep in [(r"\bHttp\b", "H T T P"), (r"\bXhr\b", "X H R"), (r"\bAA\b", "double A"),
                     (r"\bUrl\b", "U R L"), (r"\bCva\b", "C V A"), (r"\bDOM\b", "dom")]:
        text = re.sub(pat, rep, text)
    return text

kokoro = Kokoro(str(HERE / "kokoro.onnx"), str(HERE / "voices.bin"))

def tts(text: str, voice: str, speed: float = 1.0) -> np.ndarray:
    audio, sr = kokoro.create(speakable(text), voice=voice, speed=speed, lang="en-us")
    assert sr == SR
    return audio.astype(np.float32)

def silence(sec: float) -> np.ndarray:
    return np.zeros(int(SR * sec), dtype=np.float32)

def tone(freqs=(660, 880), dur=0.12, vol=0.12) -> np.ndarray:
    parts = []
    for f in freqs:
        t = np.arange(int(SR * dur)) / SR
        env = np.minimum(1, np.minimum(t, dur - t) / 0.02)
        parts.append(vol * env * np.sin(2 * np.pi * f * t))
    return np.concatenate(parts).astype(np.float32)

def encode(audio: np.ndarray, path: Path, title: str, track_no: int):
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(56); enc.set_in_sample_rate(SR); enc.set_channels(1); enc.set_quality(2)
    path.write_bytes(enc.encode(pcm) + enc.flush())

summary = []
start_all = time.time()
for n, (slug, title, topics) in enumerate(TRACKS, 1):
    cards = [c for t in topics for c in CARDS if c["topic"] == t]
    pieces = [tts(f"Track {n}. {title}. {len(cards)} cards. After each question you get a few seconds to answer out loud, then you'll hear the answer.", HOST_VOICE), silence(1.2)]
    for t in topics:
        group = [c for c in CARDS if c["topic"] == t]
        pieces += [tone((523, 784), 0.15, 0.1), tts(f"Topic: {t.replace('&', 'and')}.", HOST_VOICE), silence(0.9)]
        for c in group:
            pieces += [tts(c["q"], Q_VOICE), silence(THINK_S), tone(), silence(0.25),
                       tts(c["a"], A_VOICE, 1.03), silence(GAP_S)]
        print(f"  {slug}: {t} done ({time.time()-start_all:.0f}s elapsed)", flush=True)
    pieces += [silence(0.8), tts(f"End of track {n}.", HOST_VOICE), silence(1.0)]
    audio = np.concatenate(pieces)
    path = OUT / f"{slug}.mp3"
    encode(audio, path, title, n)
    mins = len(audio) / SR / 60
    summary.append({"file": path.name, "title": title, "topics": topics, "cards": len(cards), "minutes": round(mins, 1),
                    "mb": round(path.stat().st_size / 1e6, 1)})
    print(f"TRACK {n} {path.name}: {mins:.1f} min, {path.stat().st_size/1e6:.1f} MB", flush=True)

(OUT / "tracks.json").write_text(json.dumps(summary, indent=2))
print("TOTAL minutes", round(sum(s["minutes"] for s in summary), 1), "compute s", round(time.time() - start_all))
