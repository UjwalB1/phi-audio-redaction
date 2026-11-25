import json

PAD = 0.1
CLIPS = ["test1", "test2", "test3"]

def merge(ranges):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out

total_caught = total_items = 0

for clip in CLIPS:
    with open(f"{clip}_hits.json", encoding="utf-8") as f:
        hits = json.load(f)
    with open(f"{clip}_ground_truth.json", encoding="utf-8") as f:
        truth = json.load(f)

    muted = merge([(h["start"] - PAD, h["end"] + PAD) for h in hits])

    def covered(start, end):
        span, got = end - start, 0.0
        for a, b in muted:
            lo, hi = max(start, a), min(end, b)
            if hi > lo:
                got += hi - lo
        return min(got / span, 1.0)

    caught = 0
    print(f"\n=== {clip} ===")
    print(f"{'#':<3}{'identifier':<18}{'silenced':>9}   result")
    for t in truth:
        frac = covered(t["start"], t["end"])
        ok = frac >= 0.999
        caught += ok
        print(f"{t['id']:<3}{t['label']:<18}{frac*100:8.1f}%   "
              f"{'caught' if ok else 'MISSED'}")
    print(f"{clip}: {caught}/{len(truth)}")
    total_caught += caught
    total_items += len(truth)

print(f"\nOverall: {total_caught}/{total_items} = "
      f"{total_caught/total_items*100:.1f}%")