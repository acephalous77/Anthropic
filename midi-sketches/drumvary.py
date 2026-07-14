"""Per-clip drum variation -- the fix for the diagnosed drum-convergence bug.

The archetypes build their drum skeletons from hardcoded step grids, so every
seed of one archetype rendered the SAME beat (diversity.py measured drum_jac
~0.0 for six of them). This pass gives each clip its own drum signature --
drawn once from the clip's rng, applied consistently across all its bars so it
still grooves -- by perturbing the EXISTING voices only (never inventing a
voice name the kit can't map):

  * kick    keeps the downbeat, gains a small fixed syncopation set
  * snare   keeps its backbone, sprinkles ghost hits (per-bar probability)
  * else    ornamental voices (hats/shaker/perc) get a fixed rotation + thin

Because the choices are seeded from the clip rng, the same seed still renders
identically (reproducible), but different seeds now diverge. Structural voices
(kick downbeat, the main snare hit) are preserved so the feel survives.
"""

OFFBEATS = (3, 6, 7, 10, 11, 14)     # "e/and/a" kick syncopation candidates
GHOSTS = (2, 6, 10, 14)              # tasteful ghost-snare slots


def _hits(grid):
    return {i for i, c in enumerate(grid) if c in "xX"}


def _accents(grid):
    return {i for i, c in enumerate(grid) if c == "X"}


def _to_grid(length, hits, accents):
    return "".join("X" if i in accents else ("x" if i in hits else ".")
                   for i in range(length))


def _subset(rng, pool, k):
    k = min(k, len(pool))
    return set(rng.sample(list(pool), k)) if k else set()


def signature(rng):
    """Draw one clip's drum-variation signature from its rng."""
    return {
        "kick_extra": _subset(rng, OFFBEATS, rng.choice([0, 1, 1, 2])),
        "ghost_pool": _subset(rng, GHOSTS, rng.choice([0, 1, 2, 2])),
        "ghost_prob": rng.choice([0.0, 0.0, 0.35, 0.5, 0.6]),
        "rotate": rng.choice([0, 0, 1, 2, 3, 14]),   # 14 == shift left by 2
        "thin": rng.choice([0.0, 0.0, 0.15, 0.25]),
    }


def _is_kick(v):
    return v.lower() in ("kick", "bd", "kick2")


def _is_snare(v):
    v = v.lower()
    return ("snare" in v or v in ("clap", "rim")) and "ghost" not in v


def vary(rng, sections):
    """Mutate each bar's drum grids in place with one per-clip signature."""
    sig = signature(rng)
    for sec in sections:
        for bar in sec.get("bars", []):
            drums = bar.get("drums")
            if not drums:
                continue
            out = {}
            for voice, grid in drums.items():
                L = len(grid)
                hits, acc = _hits(grid), _accents(grid)
                if _is_kick(voice):
                    hits |= {s for s in sig["kick_extra"] if s < L}
                elif _is_snare(voice):
                    if sig["ghost_prob"] and rng.random() < sig["ghost_prob"]:
                        # ghosts land only where the backbone is silent
                        hits |= {s for s in sig["ghost_pool"] if s < L and s not in hits}
                else:  # ornamental: fixed rotation + optional thinning
                    if sig["rotate"]:
                        hits = {(i + sig["rotate"]) % L for i in hits}
                        acc = {(i + sig["rotate"]) % L for i in acc}
                    if sig["thin"]:
                        hits = {i for i in hits
                                if i in acc or rng.random() > sig["thin"]}
                out[voice] = _to_grid(L, hits, acc)
            bar["drums"] = out
    return sections
