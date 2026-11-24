import whisper

model = whisper.load_model("base")
r = model.transcribe("test1.m4a", word_timestamps=True)

for seg in r["segments"]:
    for w in seg["words"]:
        print(f"{w['start']:6.2f} - {w['end']:6.2f}  {w['word']}")