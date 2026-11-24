# Findings

## Run 1 — 2026-11-22 — Turning audio into text
Whisper base model, running on CPU. Audio: test1.m4a, 40 seconds,
recorded on a phone, with 9 identifiers I planted on purpose.

### Whisper skipped 8 seconds of the recording
Between 21.42s and 29.22s it wrote down nothing at all. The part it
skipped was: "Her daughter Priya is the contact, number is
519-555-0182." It then joined "Her daughter" straight onto "lives
over on Erie Street" as if the middle never happened.

So a name and a phone number never made it into the text. If they
aren't in the text, nothing later in my program can find them, and
they never get bleeped out of the audio.

Still need to listen back to the original recording at that point. If
the phone number is clearly audible there, the fault is the model's
and not the recording's.

### It got the unusual names wrong
"Okonkwo" came out as two separate pieces: "O" then "'Conquo".
"Halvorsen" came out as "Halvorson".
Everyday words were fine. It only struggled with unusual names,
which is exactly the kind of word a patient's name usually is.

This also means one name can be split across more than one piece of
text, each with its own timestamp. My code has to handle that when
it mutes things.

### The MRN came out as one long chunk
I read out "four four seven one nine eight two" and Whisper wrote it
as a single item, "4471982", stretching from 9.98s to 13.50s. That's
3.5 seconds in one piece, while most words are under half a second.

---

## Run 2 — 2026-11-23 — Finding the identifiers in the text
spaCy en_core_web_sm, run over the transcript from Run 1.

### Score: 6 of 9 caught
Caught: the date of birth, the MRN, the admission date, the doctor's
name, the hospital, the street.

Missed: the patient's surname, the daughter's name, the phone number.

### A half-caught name would be a missed name
spaCy tagged "Margaret O '" as a person and stopped there. "Conquo"
was not in the flagged text.

A half-bleeped name is a leaked name, and the surname identifies
someone more strongly than the first name does, so I score a partial
catch as a miss.

It did get muted in the end, but by accident. The flagged text
included the apostrophe, and that apostrophe is the first character
of the "'Conquo" token, so my code pulled the whole word in when it
worked out the time range. Had spaCy stopped one character earlier,
the surname would have stayed audible.

### Two of the three misses happened before my detector ran
The daughter's name and the phone number were never in the text,
because of the 8-second gap from Run 1. No detector could have found
them. The failure was upstream, in the speech-to-text step, and it is
a different problem from the detector missing something that was
there.

### Getting the label wrong didn't matter
spaCy tagged the MRN "4471982" as a DATE. That's wrong, but it still
flagged it, which is all I need. For redaction I only care whether
something got flagged, not what it was called.

It got caught by luck rather than by design though. A number that
spaCy decides isn't a date would sail straight through, so the MRN
needs its own pattern rather than depending on this.

### Four false alarms, and they cost nothing
It flagged "12" (from "bed 12"), the word "MRN" itself, "Emerg", and
"the morning".

None of these are patient information. Bleeping them makes the
recording slightly less useful and harms nobody. I would rather
over-bleep than under-bleep.

### A decision I had to make
spaCy flags plain numbers as CARDINAL, which is how "bed 12" got
picked up. I am choosing not to act on CARDINAL. Bed numbers, doses
and lab values are not patient identifiers, and bleeping all of them
would wreck the clinical usefulness of the recording for no privacy
gain.

The cost of that choice is that a stray identifying number in an
unrecognised format could slip through.

---

## Run 3 — 2026-11-23 — Muting the audio
Muted all 10 flagged ranges with 100ms of padding either side.
Output: test1_redacted.wav.

### Listened back to check
Silent as intended: the patient's name, date of birth, record number,
admission date, the doctor's name, the hospital, the street.

Still audible as intended: "bed 12", the chest pain, the lab results,
the plan. None of that identifies anyone.

### The phone number is still in the output
"Her daughter Priya is the contact, number is 519-555-0182" plays
back untouched in the redacted file.

Nothing went wrong from the program's point of view. It muted every
range it was given and reported success. The identifiers were simply
never in the text it was working from.

A tool that fails obviously is safer than one that fails like this one where it can go under the radar in a way.