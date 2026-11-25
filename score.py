import json

PAD = 0.1   # must match PAD_MS in redact.py

with open("hits.json", encoding="utf-8") as f:
    hits = json.load(f)
with open("ground_truth.json", encoding="utf-8") as f:
    truth = json.load(f)

def merge(ranges):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out

# what actually got silenced, padding included
muted = merge([(h["start"] - PAD, h["end"] + PAD) for h in hits])

def covered(start, end):
    span = end - start
    got = 0.0
    for a, b in muted:
        lo, hi = max(start, a), min(end, b)
        if hi > lo:
            got += hi - lo
    return min(got / span, 1.0)

caught = 0
print(f"{'#':<3}{'identifier':<22}{'silenced':>9}   result")
for t in truth:
    frac = covered(t["start"], t["end"])
    ok = frac >= 0.999
    caught += ok
    print(f"{t['id']:<3}{t['label']:<22}{frac*100:8.1f}%   {'caught' if ok else 'MISSED'}")

print(f"\nRecall: {caught}/{len(truth)} = {caught/len(truth)*100:.1f}%")