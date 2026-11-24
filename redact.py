import json
from pydub import AudioSegment

audio = AudioSegment.from_file("test1.m4a")

with open("hits.json", encoding="utf-8") as f:
    hits = json.load(f)

PAD_MS = 100   # a little margin either side, timestamps aren't exact

for h in hits:
    start = max(0, int(h["start"] * 1000) - PAD_MS)
    end = min(len(audio), int(h["end"] * 1000) + PAD_MS)
    silence = AudioSegment.silent(duration=end - start)
    audio = audio[:start] + silence + audio[end:]

audio.export("test1_redacted.wav", format="wav")
print(f"Muted {len(hits)} ranges, wrote test1_redacted.wav")