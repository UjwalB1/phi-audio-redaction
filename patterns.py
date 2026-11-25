import re

# stuff spacy has no entity type for
# written for what whisper actually spits out, not clean text

PATTERNS = [
    # "226 -555 -9417"
    ("phone", r"\b\d{3}\s*-?\s*\d{3}\s*-?\s*\d{4}\b"),

    # record numbers, health cards, years, policy numbers
    # broad on purpose, lab values and bed numbers are 1-3 digits
    ("long number", r"\d{4,}"),

    # "H -44291"
    ("id with prefix", r"\b[A-Z]\s*-?\s*\d{3,}"),

    # N9A 6T3 came out as M9A63 so this stays loose
    ("postal code", r"\b[A-Z]\d[A-Z]\s*\d[A-Z0-9]{0,2}\b"),

    # "c .newin at gmail .com", the @ turns into the word at
    ("email", r"\S+\s*\.?\S*\s+at\s+\w+\s*\.\s*(?:com|ca|org|net|edu)"),
]


def find(text):
    out = []
    for label, pat in PATTERNS:
        for m in re.finditer(pat, text):
            out.append((label, m.start(), m.end()))
    return out