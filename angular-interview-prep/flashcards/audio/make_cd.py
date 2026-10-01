"""Track 00: change detection deep dive. A short spoken lesson, then all change detection cards."""
import json, time
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "make_drive.py").read_text().split("summary = []")[0]
exec(src)  # defines CARDS, tts, silence, tone, encode, OUT, SR, voices
CARDS = json.loads(Path("/home/user/0110/angular-interview-prep/flashcards/cards.json").read_text())

LESSON = [
    "Track zero. Change detection deep dive. First a short lesson, then thirty questions.",
    "Part one. What change detection is. Angular keeps a tree of component views. In each change detection cycle it walks that tree from the root down. For every view it evaluates the template bindings, compares each value with the previous one, and updates only the DOM that changed. Data flows one way, from parent to child, once per cycle. In development mode Angular runs a second, checking pass. If a value changed between the two passes, you get the error ExpressionChangedAfterItHasBeenChecked. That error means your data flow goes backwards, so fix the flow, not the symptom.",
    "Part two. Who starts a cycle. With zone.js, the zone patches timers, events, promises and HTTP. When an async task finishes, Angular runs a tick from the root. Without zone.js, in a zoneless app, which is the default since version 21, nothing is automatic. A cycle is scheduled only by a signal change that a template reads, by markForCheck, by a template or host event listener, by the async pipe, or by setInput. A plain field assigned inside setTimeout schedules nothing.",
    "Part three. Eager versus OnPush. An Eager component, which was called Default before version 22, is checked every time change detection reaches it, so whenever its parent is checked. An OnPush component is skipped, together with its whole subtree, unless it is marked dirty. That means an OnPush parent also shields its Eager children. It is marked dirty when an input reference changes, when an event fires in its template, when an async pipe emits, when a signal it reads changes, or when markForCheck is called. Since version 22, OnPush is the default.",
    "Part four. The classic bug. A parent pushes an item into an array that it passes to an OnPush child. The reference is the same, so the child is never marked dirty and shows old data. The same happens with signals: if you mutate an array and set the same reference, Object dot is sees no change. The fix is always the same: create a new array or object.",
    "Part five. The tools. markForCheck marks the component and its ancestors dirty for the next cycle. It's the normal choice. detectChanges checks this view synchronously, right now. Use it in tests, in detached views, or when you need the DOM updated immediately. detach removes a component from automatic checking, so you can render high-frequency data on your own schedule.",
    "Part six. Why signals change the picture. When a signal read in a template changes, Angular refreshes just the view that read it. OnPush ancestors are only traversed, not re-checked. So with signals you rarely need markForCheck or detectChanges at all, and zoneless just works.",
    "Part seven. How to answer in the interview. Use the chain: what happens, why, what the user sees, the fix, and how you prevent it. For example: the child doesn't update because the array was mutated, so OnPush never marked it dirty. The user sees stale data. Fix it with an immutable update or a signal. Prevent it with readonly types, signals for state, and a lint rule against mutating inputs.",
    "Now the questions. As before, answer out loud after each one.",
]

start = time.time()
pieces = []
for i, para in enumerate(LESSON):
    pieces += [tts(para, HOST_VOICE, 0.98), silence(1.4 if i else 1.0)]
pieces += [tone((523, 784), 0.15, 0.1), silence(0.8)]
cd = [c for c in CARDS if c["topic"] == "Change detection"]
for c in cd:
    pieces += [tts(c["q"], Q_VOICE), silence(THINK_S), tone(), silence(0.25), tts(c["a"], A_VOICE, 1.03), silence(GAP_S)]
pieces += [silence(0.8), tts("End of the change detection deep dive.", HOST_VOICE), silence(1.0)]
audio = np.concatenate(pieces)
path = OUT / "00-change-detection-deep-dive.mp3"
encode(audio, path, "Change detection deep dive", 0)
mins = len(audio) / SR / 60
(OUT / "track00.json").write_text(json.dumps({"file": path.name, "title": "Change detection deep dive",
    "topics": ["Spoken lesson", "Change detection"], "cards": len(cd), "minutes": round(mins, 1),
    "mb": round(path.stat().st_size / 1e6, 1)}, indent=2))
print(f"TRACK 0 {mins:.1f} min, {path.stat().st_size/1e6:.1f} MB, compute {time.time()-start:.0f}s", flush=True)
