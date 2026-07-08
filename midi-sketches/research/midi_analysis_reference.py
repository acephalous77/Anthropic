#!/usr/bin/env python3
"""
midi_analysis.py — measurement instrument for a generative MIDI toolkit.

The transcription pipeline gave us, for free, a battery of feature extractors.
Pointed at GENERATED MIDI instead of transcribed audio, they become an
objective function: generate -> measure -> tune, instead of tuning diversity
by ear. This module is that instrument.

Core idea for the diversity/entropy problem:
  • Within a track  -> pitch-class entropy, IOI entropy, tonal clarity, density.
  • Across N tracks -> pairwise distance in feature space. If your generated
    tracks cluster tightly, they will sound samey; `diversity_report` surfaces
    the collapse and names the near-duplicate pairs.

HONEST CAVEAT (read this): statistical distance is a NECESSARY-NOT-SUFFICIENT
proxy. Two tracks can share an identical pitch-class histogram and still sound
completely different (order, register, rhythm). Treat these numbers as a
diagnostic and a tunable target, never as ground truth for "these sound
different." Optimizing the proxy too hard is Goodhart's law waiting to happen.

Notes format: a list of (pitch:int, start:float, end:float, velocity:int).
Helpers to load from pretty_midi / .mid are at the bottom (lazy import).

Deps: numpy (core). pretty_midi only for the .mid loaders.
"""

from __future__ import annotations
import numpy as np

# Krumhansl–Kessler tonal-hierarchy profiles (shared with the transcriber).
_KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                      2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                      2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_PC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

Note = tuple  # (pitch, start, end, velocity)

# ───────────────────────── primitives ─────────────────────────

def _norm(dist: np.ndarray) -> np.ndarray:
    d = np.asarray(dist, dtype=float)
    s = d.sum()
    return d / s if s > 0 else d


def normalized_entropy(dist: np.ndarray) -> float:
    """Shannon entropy scaled to [0,1] (1 = uniform, 0 = single spike)."""
    p = _norm(dist)
    nz = p[p > 0]
    if nz.size <= 1:
        return 0.0
    h = -np.sum(nz * np.log2(nz))
    return float(h / np.log2(len(p)))


def js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen–Shannon divergence in bits, in [0,1] for two distributions."""
    p, q = _norm(p), _norm(q)
    m = 0.5 * (p + q)
    def _h(x):
        nz = x[x > 0]
        return -np.sum(nz * np.log2(nz)) if nz.size else 0.0
    return float(_h(m) - 0.5 * (_h(p) + _h(q)))


# ───────────────────────── per-track features ─────────────────────────

def pitch_class_histogram(notes: list[Note], weight_by_duration: bool = True) -> np.ndarray:
    h = np.zeros(12)
    for pitch, start, end, _vel in notes:
        w = max(end - start, 1e-3) if weight_by_duration else 1.0
        h[int(pitch) % 12] += w
    return h


def tonal_clarity(notes: list[Note]) -> tuple[int, str, float]:
    """K–K key estimate from the SYMBOLIC pitch-class histogram (cleaner than
    audio chroma — we have exact notes). corr ≈ how tonally focused the material
    is; low corr on a part that should be tonal is a red flag."""
    h = pitch_class_histogram(notes)
    if h.sum() <= 0:
        return 0, "minor", 0.0
    c = h - h.mean()
    best = (0, "minor", -2.0)
    for mode, prof in (("major", _KK_MAJOR), ("minor", _KK_MINOR)):
        p = prof - prof.mean()
        for tonic in range(12):
            rp = np.roll(p, tonic)
            den = np.linalg.norm(c) * np.linalg.norm(rp)
            corr = float(np.dot(c, rp) / den) if den else 0.0
            if corr > best[2]:
                best = (tonic, mode, corr)
    return best


def ioi_histogram(notes: list[Note], bins: int = 16, max_ioi: float = 2.0) -> np.ndarray:
    """Histogram of inter-onset intervals (rhythmic-variety proxy)."""
    starts = sorted(s for _p, s, _e, _v in notes)
    iois = np.diff(starts)
    iois = iois[(iois > 0) & (iois <= max_ioi)]
    if iois.size == 0:
        return np.zeros(bins)
    hist, _ = np.histogram(iois, bins=bins, range=(0, max_ioi))
    return hist.astype(float)


def grid_position_histogram(notes: list[Note], bpm: float, subdivision: int = 4,
                            phase: float = 0.0) -> np.ndarray:
    """Where onsets fall within the metric grid (placement variety)."""
    if bpm <= 0:
        return np.zeros(subdivision)
    step = 60.0 / bpm / subdivision
    h = np.zeros(subdivision)
    for _p, s, _e, _v in notes:
        slot = int(round((s - phase) / step)) % subdivision
        h[slot] += 1
    return h


def track_features(notes: list[Note], bpm: float | None = None) -> dict:
    if not notes:
        return {"n_notes": 0, "empty": True}
    pitches = [int(p) for p, *_ in notes]
    starts = [s for _p, s, *_ in notes]
    span = max(starts) - min(starts)
    tonic, mode, corr = tonal_clarity(notes)
    feats = {
        "n_notes": len(notes),
        "unique_pitches": len(set(pitches)),
        "pitch_min": min(pitches),
        "pitch_max": max(pitches),
        "pitch_span": max(pitches) - min(pitches),
        "pc_entropy": normalized_entropy(pitch_class_histogram(notes)),
        "ioi_entropy": normalized_entropy(ioi_histogram(notes)),
        "note_density": len(notes) / span if span > 0 else 0.0,
        "key": f"{_PC[tonic]} {mode}",
        "tonal_clarity": corr,
        "_pc_hist": pitch_class_histogram(notes),
        "_ioi_hist": ioi_histogram(notes),
    }
    if bpm:
        feats["grid_entropy"] = normalized_entropy(
            grid_position_histogram(notes, bpm))
    return feats


# ───────────────────────── cross-track diversity ─────────────────────────

def diversity_report(tracks: dict[str, list[Note]], bpm: float | None = None,
                     similar_threshold: float = 0.1) -> dict:
    """Feature every track, then measure how DIFFERENT they are from each other.
    Higher mean pairwise distance = more diverse output. The min pair is your
    collapse risk. `similar_threshold` flags near-duplicate pairs (JSD units)."""
    names = list(tracks)
    feats = {n: track_features(tracks[n], bpm) for n in names}
    valid = [n for n in names if feats[n].get("n_notes", 0) > 0]

    # scalar feature matrix, z-scored across the set for a fair Euclidean
    keys = ["pc_entropy", "ioi_entropy", "note_density", "pitch_span",
            "unique_pitches", "tonal_clarity"]
    M = np.array([[feats[n][k] for k in keys] for n in valid], dtype=float)
    mu, sd = M.mean(0), M.std(0)
    Z = (M - mu) / np.where(sd > 0, sd, 1.0)

    pairs = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            tonal = js_divergence(feats[valid[i]]["_pc_hist"],
                                  feats[valid[j]]["_pc_hist"])
            rhythm = js_divergence(feats[valid[i]]["_ioi_hist"],
                                   feats[valid[j]]["_ioi_hist"])
            scalar = float(np.linalg.norm(Z[i] - Z[j]))
            pairs.append({"a": valid[i], "b": valid[j], "tonal_jsd": tonal,
                          "rhythm_jsd": rhythm, "scalar_dist": scalar})

    def _stat(field):
        vals = [p[field] for p in pairs]
        return {"mean": float(np.mean(vals)) if vals else 0.0,
                "min": float(np.min(vals)) if vals else 0.0}

    near_dupes = sorted([p for p in pairs if p["tonal_jsd"] < similar_threshold],
                        key=lambda p: p["tonal_jsd"])
    return {
        "per_track": {n: {k: v for k, v in feats[n].items()
                          if not k.startswith("_")} for n in names},
        "tonal_diversity": _stat("tonal_jsd"),
        "rhythmic_diversity": _stat("rhythm_jsd"),
        "scalar_diversity": _stat("scalar_dist"),
        "near_duplicate_pairs": near_dupes,
        "n_tracks": len(valid),
    }


def print_report(rep: dict) -> None:
    print(f"tracks analyzed: {rep['n_tracks']}")
    print(f"tonal diversity  (JSD)  mean={rep['tonal_diversity']['mean']:.3f} "
          f"min={rep['tonal_diversity']['min']:.3f}")
    print(f"rhythm diversity (JSD)  mean={rep['rhythmic_diversity']['mean']:.3f} "
          f"min={rep['rhythmic_diversity']['min']:.3f}")
    print(f"scalar diversity (z)    mean={rep['scalar_diversity']['mean']:.3f} "
          f"min={rep['scalar_diversity']['min']:.3f}")
    if rep["near_duplicate_pairs"]:
        print("⚠ near-duplicate pairs (tonally):")
        for p in rep["near_duplicate_pairs"]:
            print(f"   {p['a']}  ≈  {p['b']}  (JSD {p['tonal_jsd']:.3f})")
    else:
        print("no near-duplicate pairs under threshold")


# ───────────────────────── loaders (lazy pretty_midi) ─────────────────────────

def notes_from_pretty_midi(pm, include_drums: bool = False) -> list[Note]:
    out = []
    for inst in pm.instruments:
        if inst.is_drum and not include_drums:
            continue
        for n in inst.notes:
            out.append((n.pitch, n.start, n.end, n.velocity))
    return out


def notes_from_midi_file(path: str, include_drums: bool = False) -> list[Note]:
    import pretty_midi
    return notes_from_pretty_midi(pretty_midi.PrettyMIDI(path), include_drums)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:  # quick CLI: analyze a folder of .mid as a set
        from pathlib import Path
        files = sorted(Path(sys.argv[1]).glob("*.mid"))
        tracks = {f.stem: notes_from_midi_file(str(f)) for f in files}
        print_report(diversity_report(tracks))
