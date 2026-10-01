# Audio revision tracks

Scripts that turn `../cards.json` into about 2¼ hours of MP3 audio for listening while driving or walking.

- `make_drive.py` renders tracks 01–06: every card as question, then 6 seconds of quiet to answer out loud, a chime, then the answer.
- `make_cd.py` renders track 00: a spoken change detection lesson followed by all change detection cards.

They use the offline Kokoro TTS model (`pip install kokoro-onnx soundfile lameenc`, plus `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the kokoro-onnx GitHub releases placed next to the scripts). The MP3s aren't committed because of their size. Regenerate them after editing the cards.
