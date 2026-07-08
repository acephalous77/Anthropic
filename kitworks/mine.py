#!/usr/bin/env python3
"""Mine the (now-diverse) generator for kit ideas.

The generator does NOT produce finished kits -- the kits in kits/ are
hand-authored, every note chosen, and that is why they work. This tool uses
the generator as an IDEA SOURCE: it generates a large pool of clips, then uses
the diversity metric to greedily pick the most mutually-distant handful (so you
audition variety, not fifteen cousins of one beat). Each candidate is written
as a combined preview plus drums/bass/melody stems, with an INDEX row carrying
its seed + archetype so any pick is exactly reproducible -- and then formalized
by hand into a kNN_*.py kit.

    python mine.py            # pool 66 -> pick 24 -> mine_output/
    python mine.py 40 12      # pool 40 -> pick 12

Workflow: audition mine_output/, tell me the numbers you like; I turn each into
a hand-composed kit (lifting its bones, then choosing every note deliberately).
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HERE), "midi-sketches"))

import generator            # noqa: E402
import diversity            # noqa: E402
import midiwriter           # noqa: E402

OUT = os.path.join(HERE, "mine_output")

# weight the drum skeleton and melodic shape most -- those are what makes two
# candidates feel like different songs vs. the same one
WEIGHTS = {"drum_jac": 1.3, "ngram_jac": 1.0, "pc_js": 0.8, "ioi_js": 0.7}


def _dist(fa, fb):
    d = (WEIGHTS["drum_jac"] * diversity._jaccard_distance(fa["drum"], fb["drum"])
         + WEIGHTS["ngram_jac"] * diversity._jaccard_distance(fa["trig"], fb["trig"])
         + WEIGHTS["pc_js"] * diversity._js_distance(fa["pc"], fb["pc"])
         + WEIGHTS["ioi_js"] * diversity._js_distance(fa["ioi"], fb["ioi"]))
    return d / sum(WEIGHTS.values())


def build_pool(pool_size):
    archetypes = list(generator.ARCHETYPES)
    pool = []
    i = 0
    while len(pool) < pool_size:
        arch = archetypes[i % len(archetypes)]
        seed = 20000 + i
        try:
            gen = generator.generate(seed=seed, archetype=arch)
        except RuntimeError:
            i += 1
            continue
        pool.append((gen, diversity._features(gen)))
        i += 1
    return pool


def farthest_point(pool, k):
    """Greedy max-min selection: keep picking the candidate farthest from the
    set already chosen, so the result spans the pool instead of clustering."""
    feats = [f for _, f in pool]
    n = len(pool)
    # seed with the two most distant candidates
    best = (0, 1, -1)
    for a in range(n):
        for b in range(a + 1, n):
            d = _dist(feats[a], feats[b])
            if d > best[2]:
                best = (a, b, d)
    chosen = [best[0], best[1]]
    while len(chosen) < min(k, n):
        far, far_d = None, -1
        for c in range(n):
            if c in chosen:
                continue
            nearest = min(_dist(feats[c], feats[j]) for j in chosen)
            if nearest > far_d:
                far, far_d = c, nearest
        chosen.append(far)
    return chosen


def _stems(gen):
    r = gen["result"]
    bpmc, tsc = r["bpm_changes"], r["time_sig_changes"]
    cc = gen.get("cc", {})
    return bpmc, tsc, [
        {"events": r["drums"], "channel": 9, "program": None, "name": "drums",
         "cc_events": cc.get("drums")},
        {"events": r["bass"], "channel": 0, "program": gen.get("bass_program"),
         "name": "bass", "cc_events": cc.get("bass")},
        {"events": r["melody"], "channel": 1, "program": gen.get("melody_program"),
         "name": "melody", "cc_events": cc.get("melody")},
    ]


def main(argv):
    pool_size = int(argv[0]) if len(argv) > 0 else 66
    pick = int(argv[1]) if len(argv) > 1 else 24
    if os.path.isdir(OUT):
        import shutil
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    print(f"generating pool of {pool_size}...")
    pool = build_pool(pool_size)
    print(f"selecting {pick} most mutually-distant...")
    chosen = farthest_point(pool, pick)

    rows = []
    for n, idx in enumerate(chosen, 1):
        gen, _ = pool[idx]
        r = gen["result"]
        bpmc, tsc, tracks = _stems(gen)
        tag = f"{n:02d}_{gen['archetype']}_{gen['root']}{gen['scale'][:3]}_{gen['bpm']}"
        d = os.path.join(OUT, tag)
        os.makedirs(d)
        midiwriter.write_combined(os.path.join(d, "all.mid"), tracks, bpmc, tsc)
        for t in tracks:
            if t["events"]:
                midiwriter.write_track(os.path.join(d, f"{t['name']}.mid"), t["events"],
                                       bpmc, tsc, channel=t["channel"], program=t["program"],
                                       track_name=t["name"], cc_events=t.get("cc_events"))
        rows.append({"n": n, "tag": tag, "seed": gen["seed"], "archetype": gen["archetype"],
                     "bpm": gen["bpm"], "key": f"{gen['root']} {gen['scale']}",
                     "drum_hits": len(r["drums"]), "mel_notes": len(r["melody"]),
                     "bass_notes": len(r["bass"])})
        print(f"  {tag}")

    with open(os.path.join(OUT, "INDEX.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} candidates -> {OUT}\n"
          f"audition all.mid in each; the seed+archetype in INDEX.csv "
          f"reproduces any pick for hand-authoring into a kit.")


if __name__ == "__main__":
    main(sys.argv[1:])
