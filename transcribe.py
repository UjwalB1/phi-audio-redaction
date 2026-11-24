import whisper
import json

model = whisper.load_model("base")
result = model.transcribe("test1.m4a", word_timestamps=True)

words = []
for seg in result["segments"]:
    for w in seg["words"]:
        words.append({
            "text": w["word"].strip(),
            "start": w["start"],
            "end": w["end"],
        })

with open("transcript.json", "w", encoding="utf-8") as f:
    json.dump(words, f, indent=2)

print(f"Saved {len(words)} words to transcript.json\n")
print(" ".join(w["text"] for w in words))