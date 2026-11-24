import json
import spacy

nlp = spacy.load("en_core_web_sm")

with open("transcript.json", encoding="utf-8") as f:
    words = json.load(f)

# Glue words into one string, remembering where each one landed
text = ""
spans = []                      # (char_start, char_end, word_index)
for i, w in enumerate(words):
    if text:
        text += " "
    start = len(text)
    text += w["text"]
    spans.append((start, len(text), i))

doc = nlp(text)

# Ignoring CARDINAL so bed numbers and doses don't get bleeped
ACT_ON = {"PERSON", "DATE", "TIME", "GPE", "LOC", "FAC", "ORG", "NORP"}

hits = []
for ent in doc.ents:
    if ent.label_ not in ACT_ON:
        continue
    covered = [i for (s, e, i) in spans
               if s < ent.end_char and e > ent.start_char]
    if not covered:
        continue
    hits.append({
        "text": ent.text,
        "label": ent.label_,
        "start": words[covered[0]]["start"],
        "end": words[covered[-1]]["end"],
    })

for h in hits:
    print(f"{h['start']:6.2f} - {h['end']:6.2f}  {h['label']:8} {h['text']}")

with open("hits.json", "w", encoding="utf-8") as f:
    json.dump(hits, f, indent=2)

print(f"\n{len(hits)} ranges to mute, saved to hits.json")