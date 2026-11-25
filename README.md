# Audio PHI Redaction Demo

Finds protected health information in a spoken clinical handoff and
mutes it in the audio. A prototype for measuring how well
off-the-shelf models handle PHI in speech, and where they fail.

## How it works

1. Whisper transcribes the audio with a timestamp on every word
2. spaCy picks out names, dates, places and organisations, and regex
   patterns pick out phone numbers, emails, postal codes and record
   numbers
3. Flagged text gets mapped back to the seconds it was spoken
4. Those seconds are silenced

Scoring is done by time, not by text. Whisper misspells unusual names
("Okonkwo" came out "O 'Conquo"), so checking whether the tool
flagged the right string measures Whisper's spelling rather than
whether anything was actually removed. Instead each identifier's time
range is recorded by hand, and the question is whether those seconds
ended up silent.

An identifier only counts as caught if the whole range was silenced.
Half a redacted name is a leaked name.

## Results

Three recordings, 28 planted identifiers.

| Type | spaCy only | With regex |
|------|-----------|------------|
| Names | 7 of 8 | 7 of 8 |
| Dates | 4 of 6 | 5 of 6 |
| Places and organisations | 3 of 6 | 4 of 6 |
| Structured strings (phone, email, postal code, record numbers) | 2 of 7 | 6 of 7 |
| Age | 1 of 1 | 1 of 1 |
| **Total** | **17 of 28 (60.7%)** | **23 of 28 (82.1%)** |

NER alone handles names well and structured identifiers badly, which
makes sense given it has no entity type for an email address or a
postal code. The two it appeared to catch were accidents: spaCy
labelled a medical record number and a health card number as DATE.

## What it still gets wrong

Two of the five remaining misses never reached the detector. Whisper
silently skipped an 8 second stretch of the first recording
containing a name and a phone number. It raised no error, and the
tool reported success on a file that still had the phone number in
it. That same phone number was transcribed correctly in a later
recording and then ignored by spaCy, so phone numbers failed at both
stages independently.

The other three are place names where only part of the span gets
flagged ("DU" without "hotel"), or places missed entirely ("Met
Campus"), plus one vague date ("the third").

Recall matters more than precision here. A missed identifier is a
privacy breach, a false positive is a bleeped word nobody needed.
The tool over-flags on purpose.

## Running it

```
pip install openai-whisper spacy pydub
python -m spacy download en_core_web_sm
```

ffmpeg also needs to be installed and on PATH.

```
python run.py test1.m4a     # transcribe, detect, mute
python score.py             # score all three clips
```

## Files

- `run.py` is the whole pipeline
- `patterns.py` holds the regex, written against what Whisper
  actually produces rather than clean text
- `score.py` compares what got muted against the ground truth
- `testN_script.txt` is the script read aloud and the identifiers
  planted in it
- `testN_ground_truth.json` is when each identifier was spoken
- `FINDINGS.md` is the full log, including the things that turned out
  wrong

## Note on the data

All recordings are me reading invented clinical handoffs. No real
patient data was used.