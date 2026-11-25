import sys, os, json
import whisper, spacy
from pydub import AudioSegment
import patterns

audio_path = sys.argv[1]
base = os.path.splitext(audio_path)[0]

# transcribe 
model = whisper.load_model("base")
result = model.transcribe(audio_path, word_timestamps=True)
words = [{"text": w["word"].strip(), "start": w["start"], "end": w["end"]}
         for seg in result["segments"] for w in seg["words"]]
with open(f"{base}_transcript.json", "w", encoding="utf-8") as f:
    json.dump(words, f, indent=2)

# detect
nlp = spacy.load("en_core_web_sm")
text, spans = "", []
for i, w in enumerate(words):
    if text:
        text += " "
    s = len(text)
    text += w["text"]
    spans.append((s, len(text), i))

doc = nlp(text)
# Ignoring CARDINAL so bed numbers and doses don't get bleeped
ACT_ON = {"PERSON", "DATE", "TIME", "GPE", "LOC", "FAC", "ORG", "NORP"}

def words_covering(start_char, end_char):
    return [i for (a, b, i) in spans if a < end_char and b > start_char]

hits = []

for ent in doc.ents:
    if ent.label_ not in ACT_ON:
        continue
    covered = words_covering(ent.start_char, ent.end_char)
    if not covered:
        continue
    # grab a bare number sitting just before so street numbers come along
    first = covered[0]
    if first > 0 and words[first - 1]["text"].strip(".,").isdigit():
        covered.insert(0, first - 1)
    hits.append({"text": ent.text, "label": ent.label_,
                 "start": words[covered[0]]["start"],
                 "end": words[covered[-1]]["end"]})

for label, s, e in patterns.find(text):
    covered = words_covering(s, e)
    if covered:
        hits.append({"text": text[s:e], "label": label,
                     "start": words[covered[0]]["start"],
                     "end": words[covered[-1]]["end"]})

with open(f"{base}_hits.json", "w", encoding="utf-8") as f:
    json.dump(hits, f, indent=2)

# mute 
PAD_MS = 100
audio = AudioSegment.from_file(audio_path)
for h in hits:
    s = max(0, int(h["start"] * 1000) - PAD_MS)
    e = min(len(audio), int(h["end"] * 1000) + PAD_MS)
    audio = audio[:s] + AudioSegment.silent(duration=e - s) + audio[e:]
audio.export(f"{base}_redacted.wav", format="wav")

print(text, "\n")
for h in hits:
    print(f"{h['start']:6.2f} - {h['end']:6.2f}  {h['label']:12} {h['text']}")
print(f"\n{len(hits)} ranges muted -> {base}_redacted.wav")