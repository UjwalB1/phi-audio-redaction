# Findings

## Run 1 — 2026-11-22 — Turning audio into text
Whisper base model on CPU. 40 second phone recording, 9 identifiers
planted on purpose.

### Whisper skipped 8 seconds
Nothing at all between 21.42s and 29.22s. What got skipped: "Her
daughter Priya is the contact, number is 519-555-0182." It then
stitched "Her daughter" straight onto "lives over on Erie Street"
like the middle never happened.

So a name and a phone number never made it into the text. Nothing
further down the program can find what isn't there, and they don't
get bleeped either.

Still need to listen back and check the phone number is actually
audible at that point. If it is, that's the model's fault and not my
recording's.

### Unusual names came out wrong
"Okonkwo" turned into two pieces, "O" then "'Conquo". "Halvorsen"
became "Halvorson".

Everyday words were fine. It only tripped on unusual names, which is
unfortunate given that's exactly what a patient's name usually is.

One name can also land across more than one piece of text, each with
its own timestamp. My code has to deal with that when it mutes.

### The MRN came out as one long chunk
I read "four four seven one nine eight two" and Whisper wrote it as a
single item, "4471982", running 9.98s to 13.50s. 3.5 seconds in one
piece when most words are under half a second.

---

## Run 2 — 2026-11-23 — Finding the identifiers in the text
spaCy en_core_web_sm over the transcript from Run 1.

### 6 of 9 caught
Caught: date of birth, MRN, admission date, doctor's name, hospital,
street.

Missed: patient's surname, daughter's name, phone number.

### Half a name is no name
spaCy tagged "Margaret O '" as a person and stopped. "Conquo" wasn't
in the flagged text.

Bleeping half a name leaks the name, and the surname is the half that
identifies someone. So a partial catch counts as a miss. No half
marks.

It did get muted in the end, but only by accident. The flagged text
included the apostrophe, and that apostrophe is the first character
of the "'Conquo" token, so my code pulled the whole word in when it
worked out the time range. One character earlier and the surname
would have stayed audible.

### Two of the three misses happened before my detector ran
The daughter's name and the phone number were never in the text at
all, because of the 8 second gap. No detector could have found them.
That failure sits in the speech-to-text step, which is a different
problem from the detector missing something that was right in front
of it.

### Getting the label wrong didn't matter
spaCy called the MRN "4471982" a DATE. Wrong, but it still flagged
it, and flagging is all I need. For redaction I don't care what
something gets called, only whether it got picked up.

That was luck though. A number spaCy decides isn't a date sails
straight through, so the MRN needs its own pattern instead of
depending on this.

### Four false alarms, no harm done
It flagged "12" from "bed 12", the word "MRN" itself, "Emerg", and
"the morning".

None of that is patient information. Bleeping it makes the recording
slightly less useful and hurts nobody. I'd rather over-bleep than
under-bleep.

### A decision I had to make
spaCy flags plain numbers as CARDINAL, which is how "bed 12" got
picked up. I'm not acting on CARDINAL. Bed numbers, doses and lab
values aren't identifiers, and bleeping all of them would wreck what
makes the recording useful in the first place, for no privacy gain.

The cost is that an identifying number in some format I haven't
thought of could slip through.

---

## Run 3 — 2026-11-23 — Muting the audio
Muted all 10 flagged ranges with 100ms padding either side. Output:
test1_redacted.wav.

### Listened back
Silent as intended: patient name, date of birth, record number,
admission date, doctor's name, hospital, street.

Still audible as intended: "bed 12", the chest pain, the lab results,
the plan. None of that identifies anyone.

### The phone number is still in the output
"Her daughter Priya is the contact, number is 519-555-0182" plays
back untouched in the redacted file.

As far as the program's concerned nothing went wrong. It muted every
range it was handed and reported success. Those identifiers just were
never in the text it was working from.

A tool that fails obviously is safer than one that fails like this
one, where it slips under the radar.

---

## Run 4 — 2026-11-24 — Scoring it
Wrote down when each of the 9 identifiers was actually spoken, then
checked whether those seconds ended up silent.

### Why I scored by time and not by text
The obvious approach is checking whether the tool flagged the text
"Okonkwo". That falls apart immediately, since Whisper wrote
"'Conquo" and the two don't match. I'd be measuring Whisper's
spelling rather than whether my tool removed anything.

What I care about is simpler. The name was spoken between 3.82 and
5.18 seconds. Is that stretch silent now? Doesn't matter what
anything got called or spelled.

Seven of the nine times I could read off the transcript. The other
two, the daughter's name and the phone number, I found by ear,
because they're inside the gap Whisper skipped.

### Results

| # | Identifier         | Silenced | Result |
|---|--------------------|----------|--------|
| 1 | patient name       | 100%     | caught |
| 2 | date of birth      | 100%     | caught |
| 3 | MRN                | 100%     | caught |
| 4 | admission date     | 100%     | caught |
| 5 | physician name     | 100%     | caught |
| 6 | hospital           | 100%     | caught |
| 7 | family member name | 0%       | missed |
| 8 | phone number       | 0%       | missed |
| 9 | address            | 100%     | caught |

7 of 9, so 77.8%.

Caught only counts if the whole thing went silent. Same rule as
before, no half marks.

### Run 2's count was wrong
I said 6 of 9 in Run 2, going off the list of things spaCy flagged.
Scoring by time says 7. The surname did end up silenced even though
the flagged text looked like it stopped short, because of that
apostrophe overlap.

Counting what a model flagged isn't the same as measuring what
actually happened to the audio. Worth remembering.

### Where the failures actually are
9 identifiers spoken. 7 made it into the transcript. All 7 of those
got caught and silenced. Nothing that reached the detector got past
it.

Both failures happened earlier, on words that were never written
down.

Two numbers, and they say different things:

- End to end, 7 of 9.
- Of what it could actually see, 7 of 7.

That changes what I'd fix next. Looking at 77.8% on its own I'd have
gone and swapped the name detector for something better. Pointless.
Every remaining failure is upstream, so it's a bigger Whisper model
or a second pass over the audio, and nothing downstream will move the
number at all.