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

---

## Run 5 — 2026-11-25 — Two more recordings
One clip wasn't enough to claim anything, so I recorded two more.

test2 is a deliberately common name (John Smith) plus an email, a
postal code and a health card number. test3 is a hyphenated name, a
date read out as digits, a second phone number and a policy number.

Ran all three through the same pipeline.

### test1 came out identical on the re-run
Same transcript, same ten ranges, same timestamps to the hundredth of
a second. Whisper didn't drift. Good, because a redaction tool giving
you different output on the same file twice would be a problem on its
own.

### Scores
test1: 7 of 9
test2: 6 of 9
test3: 4 of 10

17 of 28 overall, so 60.7%.

### Broken down by what kind of identifier it is

| Type | Caught |
|------|--------|
| Names (patient, physician, next of kin) | 7 of 8 |
| Dates | 4 of 6 |
| Places and organisations | 3 of 6 |
| Structured strings (phone, email, postal code, policy no., MRN, health card) | 2 of 6 |

The bottom row is the real story, and even those two were flukes.
spaCy labelled the MRN and the health card number as DATE. It wasn't
recognising them as identifiers, it guessed wrong in a way that
happened to work out.

Makes sense when you think about what NER is for. It's trained to
spot names, places, organisations and dates. There's no entity type
for "email address" or "postal code", so it has nowhere to put them
and they sail straight through.

### Three different kinds of failure, not one
Of the 11 misses:

Two were transcription failures. test1's family member name and phone
number, never written down, so nothing downstream had a chance.

Three were partial coverage. The identifier was there and spaCy
flagged part of it. "Riverside Drive" without the "31" in front.
"DU" without the "hotel". "Campus" without the "Met". Each one leaves
enough behind to be useless as redaction.

Six were flat misses. Postal code, email, phone number, policy
number, the date of birth read as digits, and "the third".

They need completely different fixes, which is why lumping them into
one percentage hides more than it shows.

### I got Run 4 wrong
In Run 4 I said detection was fine at 7 of 7 and the only problem was
upstream in Whisper. Three clips says that's backwards. Only 2 of the
11 misses are Whisper's fault. The other 9 are detection.

test1 happened to be mostly names and dates, which is the one thing
NER actually does well. I measured the easy case and drew a general
conclusion from it.

### So what would actually move the number
Not a better NER model. Regex for the structured stuff, since a phone
number or a postal code has a shape you can just match. And widening
flagged spans out to sensible boundaries so a street number comes
along with its street name.

Both of those are maybe an hour, and between them they'd cover 9 of
the 11 misses.

### Something I had wrong about the rules
I planted "72 years old" as an identifier. Turns out HIPAA Safe Harbor
only counts ages of 90 and over, because a very high age narrows down
who someone could be. So 72 probably shouldn't have been on the list
at all.

Leaving it in since it's scored, but worth knowing I was working off
an assumption rather than the actual rules.

### The best demo is still test3's phone number
In test1 the phone number vanished because Whisper never wrote it
down. In test3 Whisper got "226 -555 -9417" perfectly and spaCy
ignored it.

Same identifier but two separate reasons it ended up in a
file I'd have called de-identified.

---

## Run 6 — 2026-11-25 — Adding regex
Run 5 said the gap was structured identifiers, so I wrote patterns
for them. New file patterns.py with five: phone numbers, any run of
four or more digits, a letter stuck to a number like "H -44291",
Canadian postal codes, and emails in the spoken form Whisper gives
you ("c .newin at gmail .com").

Also added a rule in run.py: if a bare number sits right before
something spaCy flagged, pull it in. Meant to fix "31 Riverside
Drive" losing its street number.

### 17 of 28 became 23 of 28

| Type | Before | After |
|------|--------|-------|
| Names | 7 of 8 | 7 of 8 |
| Dates | 4 of 6 | 5 of 6 |
| Places and organisations | 3 of 6 | 4 of 6 |
| Structured strings | 2 of 7 | 6 of 7 |
| Age | 1 of 1 | 1 of 1 |
| Total | 17 of 28 | 23 of 28 |

60.7% to 82.1%.

test2 went 6 of 9 to 9 of 9. The postal code, the email and the
address all came good.

The one structured identifier still missing is test1's phone number,
which was never transcribed. No pattern can match text that isn't
there.

### Run 5 said the fix was regex, and it was
Nice to have guessed right for once. Every structured identifier that
made it into a transcript now gets caught. Nothing else moved much,
which is what you'd want, since the patterns were only ever aimed at
one thing.

### The number rule works but it's sloppy
It fixed the address, but it fires on numbers that have nothing to do
with what follows them.

In test2 "John Smith" now starts at 2.42 instead of 3.36, because
"Bed 4" sits in front of it and the "4" got dragged along. Same in
test3 where "Fatima Aura Shid" picked up the "11" from "Rum 11", and
in test1 where the MRN span swallowed "1958".

All harmless since it only means bleeping a bed number nobody cares
about. But the address got fixed by a rule that's firing on things it
wasn't written for, and that's worth admitting rather than calling it
a clean win.

### What's left
Five misses.

Two are test1's dropout, the family member name and the phone number.
Nothing I do downstream touches those.

Three are places and one vague date, all in test3. "hotel DU" where
only "DU" got flagged. "Met Campus" not flagged at all, and that 17%
on it is just padding bleeding over from "next Tuesday" sitting next
to it. And "the third" as a date, which spaCy ignored.

Different shape of problem than what I started with. These need
better place recognition or a second model, not patterns.

### A guess from Run 1 that turned out wrong
Back in Run 1 I figured the long string of digits was what made
Whisper drop that 8 second chunk.

Doesn't hold. test2 has a nine digit health card number transcribed
perfectly and test3 has the whole phone number transcribed perfectly.

So the dropout happened once in three recordings and I still don't
know why. Which is a weaker claim than I'd have liked, but "this can
happen and nothing warns you" is still bad news for a tool whose
whole job is not leaving things behind.