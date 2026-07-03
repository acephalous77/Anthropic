#!/usr/bin/env python3
"""KITS -- eight hand-composed, interlocking song kits. Every note chosen.

The lesson of the review: generated note-choices make plausible wallpaper,
not usable music. So these are WRITTEN, not generated -- the way the three
foundation pieces were. What makes each kit usable:

  * a RECOGNIZABLE beat: a real idiom stated exactly, with a hand-written
    fill bar (A A A B) -- not rotated Euclidean chance
  * a bass line WRITTEN AGAINST the kick (locks its accents) and against
    the chord changes
  * a lead melody with a memorable shape -- chosen intervals, a rhythmic
    motto, real phrase endings, silence between phrases
  * chords voiced by hand with smooth movement
  * everything on one explicit progression, so any subset of parts works

The groove engine is used ONLY for feel polish (micro-timing + swing);
velocities are hand-written. Drums use MC-707 pads 36-51. Loops are 4 bars,
seamless, hit on beat 1.

    python kits.py    ->  output/kits/<NN_Name_Key_bpm>/{drums,bass,lead,chords,arp,full}.mid
"""

import os
import random
import shutil

import groove as G
import humanize
import midiwriter
from midiwriter import Event
from songcraft import anchor

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "kits")
PPQ = midiwriter.PPQ
STEP = PPQ // 4

_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
       "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def N(name):
    """'F#2' -> MIDI number (C4 = 60)."""
    pc = name[:-1]
    return (int(name[-1]) + 1) * 12 + _PC[pc]


def bars_to_events(bars, channel, bar_steps=16):
    """bars: list of [(step, dur, 'Note', vel), ...] per bar -> Events."""
    ev = []
    for bi, bar in enumerate(bars):
        for (s, d, note, v) in bar:
            ev.append(Event((bi * bar_steps + s) * STEP, d * STEP,
                            N(note) if isinstance(note, str) else note, v, channel))
    return ev


def drum_bars(bars, bar_steps=16):
    """bars: list of {note: [(step, vel), ...]} per bar -> channel-10 Events."""
    ev = []
    for bi, bar in enumerate(bars):
        for note, hits in bar.items():
            for (s, v) in hits:
                ev.append(Event((bi * bar_steps + s) * STEP, STEP, note, v, 9))
    return ev


def H(*pairs):
    """hits helper: H(0,106, 8,96) -> [(0,106), (8,96)]"""
    return list(zip(pairs[::2], pairs[1::2]))


# =============================================================================
# THE KITS -- every note below is deliberate.
# =============================================================================

def kit_nightpulse():
    """Fever Ray territory: a dark half-time throb in F minor, 68 bpm.
    The bass is an 8th-note pulse that dips to Eb and climbs home through Db;
    the lead is an icy descending hook that states itself, then answers one
    step higher and lands long on the root."""
    A = {36: H(0, 110, 8, 98, 14, 72),          # kick throb + soft pickup
         41: H(3, 88, 11, 84),                   # low tom answers the kick
         37: H(4, 66, 12, 62),                   # rim keeps the frame
         44: H(0, 56, 2, 40, 4, 52, 6, 40, 8, 54, 10, 40, 12, 52, 14, 42),
         46: H(12, 78)}                          # one open hat exhale
    B = {36: H(0, 110, 8, 96),
         41: H(3, 86, 10, 84, 12, 90),
         45: H(11, 88, 13, 92),
         48: H(14, 94, 15, 98),                  # tom fill climbs into the loop
         44: H(0, 56, 4, 50, 8, 54),
         37: H(4, 64)}
    drums = [A, A, A, B]

    P = lambda s, v: (s, 2, "F1", v)             # the pulse cell
    bass = [
        [P(0, 98), P(2, 74), P(4, 88), P(6, 74), P(8, 96), P(10, 74), P(12, 86), P(14, 76)],
        [P(0, 98), P(2, 74), P(4, 88), P(6, 74), P(8, 94), P(10, 72),
         (12, 2, "Eb1", 86), (14, 2, "Eb1", 78)],
        [P(0, 98), P(2, 74), P(4, 88), P(6, 74), P(8, 96), P(10, 74), P(12, 86), P(14, 76)],
        [P(0, 98), P(2, 74), P(4, 86), P(6, 72),
         (8, 2, "Db1", 88), (10, 2, "Db1", 78), (12, 2, "Eb1", 90), (14, 2, "Eb1", 82)],
    ]
    lead = [
        [(0, 2, "C5", 102), (2, 2, "Ab4", 92), (4, 4, "F4", 96),
         (10, 2, "G4", 88), (12, 2, "Ab4", 90), (14, 2, "G4", 86)],
        [(0, 6, "F4", 94), (10, 2, "Eb4", 84), (12, 4, "F4", 90)],
        [(0, 2, "C5", 100), (2, 2, "Ab4", 90), (4, 4, "Bb4", 96),
         (10, 2, "Ab4", 88), (12, 2, "G4", 86), (14, 2, "Eb4", 84)],
        [(0, 10, "F4", 96)],                     # the long landing, then breath
    ]
    chords = [
        [(0, 16, "C3", 58), (0, 16, "F3", 56), (0, 16, "Ab3", 54)],   # Fm
        [(0, 16, "C3", 56), (0, 16, "F3", 54), (0, 16, "Ab3", 52)],
        [(0, 16, "Db3", 58), (0, 16, "F3", 56), (0, 16, "Ab3", 54)],  # Db (VI)
        [(0, 16, "Eb3", 58), (0, 16, "G3", 56), (0, 16, "Bb3", 54)],  # Eb (VII)
    ]
    return dict(name="Nightpulse", key="Fm", bpm=68, feel="ritual", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=38, lead=81, chords=89, arp=None))


def kit_glasskid():
    """Kid A territory: C minor, 120. The bass plays the kick's exact rhythm
    (that lock is the groove); the lead is a displaced four-note cell --
    C Eb D G -- that shifts one 16th late every other bar and comes back."""
    A = {36: H(0, 112, 3, 88, 8, 104, 11, 88),
         39: H(12, 96),
         44: H(6, 50, 10, 46),
         37: H(5, 36, 13, 34)}                   # glitch ticks, nearly silent
    B = {36: H(0, 112, 3, 88, 8, 102, 11, 86, 12, 78, 14, 92),
         39: H(12, 94, 15, 80),
         40: H(14, 70),
         44: H(6, 48)}
    drums = [A, A, A, B]

    bass = [
        [(0, 3, "C2", 100), (3, 2, "C2", 82), (8, 3, "C2", 96), (11, 2, "C2", 82)],
        [(0, 3, "C2", 100), (3, 2, "C2", 82), (8, 3, "C2", 94), (11, 2, "Eb2", 86)],
        [(0, 3, "C2", 100), (3, 2, "C2", 82), (8, 3, "C2", 96), (11, 2, "C2", 82)],
        [(0, 3, "C2", 98), (3, 2, "C2", 82), (8, 2, "Bb1", 90), (10, 2, "Bb1", 80),
         (12, 4, "G1", 94)],                     # the descent that resets the loop
    ]
    cell = [(0, 1, "C5", 98), (2, 1, "Eb5", 92), (4, 1, "D5", 90), (6, 2, "G4", 94)]
    lead = [
        cell + [(10, 1, "G4", 70), (12, 1, "C5", 74)],
        [(s + 1, d, n, v) for (s, d, n, v) in cell],          # displaced a 16th
        cell + [(10, 1, "G4", 70), (12, 1, "C5", 74)],
        cell + [(8, 1, "Bb4", 88), (10, 1, "F5", 92), (12, 4, "C5", 96)],
    ]
    chords = [
        [(2, 2, "Eb4", 72), (2, 2, "G4", 68), (2, 2, "Bb4", 64),
         (10, 2, "Eb4", 66), (10, 2, "G4", 62), (10, 2, "Bb4", 58)],   # Cm7 stabs
        [(2, 2, "C4", 72), (2, 2, "Eb4", 68), (2, 2, "Ab4", 64),
         (10, 2, "C4", 66), (10, 2, "Eb4", 62), (10, 2, "Ab4", 58)],   # Ab
        [(2, 2, "Eb4", 72), (2, 2, "G4", 68), (2, 2, "Bb4", 64),
         (10, 2, "Eb4", 66), (10, 2, "G4", 62), (10, 2, "Bb4", 58)],
        [(2, 2, "D4", 72), (2, 2, "F4", 68), (2, 2, "Bb4", 64),
         (10, 2, "D4", 66), (10, 2, "F4", 62), (10, 2, "Bb4", 58)],    # Bb
    ]
    return dict(name="Glasskid", key="Cm", bpm=120, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=38, lead=80, chords=95, arp=None))


def kit_hillrunner():
    """Kate Bush territory: A minor gallop at 108 over i-VI-VII-v (Am F G Em).
    The lead leaps a fifth and walks back down -- the yearning shape -- and
    the balearic arp keeps the sky moving."""
    A = {36: H(0, 108, 8, 100),
         43: H(3, 86, 4, 78, 11, 86, 12, 78),    # the gallop
         38: H(4, 98, 12, 100),
         44: H(2, 44, 6, 44, 10, 44, 14, 44)}
    B = {36: H(0, 108, 8, 98),
         43: H(3, 86, 4, 78),
         38: H(4, 98, 12, 100),
         45: H(11, 84), 48: H(13, 88, 14, 92, 15, 96),
         44: H(2, 44, 6, 44)}
    drums = [A, A, A, B]

    def bar_bass(r, f):
        return [(0, 2, r, 98), (2, 2, r, 80), (4, 2, f, 88), (6, 2, r, 80),
                (8, 2, r, 96), (10, 2, r, 78), (12, 2, f, 88), (14, 2, r, 82)]
    bass = [bar_bass("A1", "E2"), bar_bass("F2", "C3"),
            bar_bass("G2", "D3"), bar_bass("E2", "B2")]

    lead = [
        [(0, 2, "A4", 94), (2, 4, "E5", 104), (6, 2, "D5", 92), (8, 2, "C5", 90),
         (10, 2, "B4", 88), (12, 4, "A4", 92)],
        [(0, 2, "A4", 90), (2, 4, "C5", 98), (6, 2, "B4", 86), (8, 4, "A4", 90),
         (12, 4, "G4", 86)],
        [(0, 2, "B4", 92), (2, 4, "D5", 100), (6, 2, "C5", 88), (8, 4, "B4", 90),
         (12, 4, "G4", 84)],
        [(0, 2, "G4", 88), (2, 4, "B4", 96), (6, 2, "A4", 86), (8, 8, "E4", 90)],
    ]
    chords = [
        [(0, 8, "A3", 64), (0, 8, "C4", 60), (0, 8, "E4", 56),
         (8, 8, "A3", 56), (8, 8, "C4", 52), (8, 8, "E4", 48)],
        [(0, 8, "F3", 64), (0, 8, "A3", 60), (0, 8, "C4", 56),
         (8, 8, "F3", 56), (8, 8, "A3", 52), (8, 8, "C4", 48)],
        [(0, 8, "G3", 64), (0, 8, "B3", 60), (0, 8, "D4", 56),
         (8, 8, "G3", 56), (8, 8, "B3", 52), (8, 8, "D4", 48)],
        [(0, 8, "E3", 64), (0, 8, "G3", 60), (0, 8, "B3", 56),
         (8, 8, "E3", 56), (8, 8, "G3", 52), (8, 8, "B3", 48)],
    ]
    def bar_arp(t1, t2, t3, t4):
        seq = [t1, t2, t3, t4, t3, t2, t1, t2]
        return [(i * 2, 2, seq[i], 58 + (6 if i == 0 else 0)) for i in range(8)]
    arp = [bar_arp("A4", "C5", "E5", "A5"), bar_arp("A4", "C5", "F5", "A5"),
           bar_arp("B4", "D5", "G5", "B5"), bar_arp("B4", "E5", "G5", "B5")]
    return dict(name="Hillrunner", key="Am", bpm=108, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=arp,
                progs=dict(bass=38, lead=81, chords=50, arp=11))


def kit_lowgold():
    """Boom-bap head-nod in D dorian, 84, swung. Bass leaves real space and
    touches the dorian B-natural in the turnaround; the lead is a pentatonic
    call that asks in bar 1, answers in bar 2, and rests low in bar 4."""
    A = {36: H(0, 108, 7, 92, 10, 96),
         38: H(4, 102, 12, 104),
         37: H(7, 34, 15, 32),                   # ghost hand
         42: H(0, 62, 2, 46, 4, 58, 6, 46, 8, 60, 10, 46, 12, 58, 14, 48)}
    B = {36: H(0, 108, 7, 92, 10, 94, 13, 84),
         38: H(4, 102, 12, 102),
         45: H(14, 86, 15, 90),
         42: H(0, 62, 4, 58, 8, 60, 12, 58)}
    drums = [A, A, A, B]

    bass = [
        [(0, 3, "D2", 100), (4, 2, "D2", 80), (7, 2, "F2", 88), (10, 3, "C2", 90),
         (14, 2, "D2", 82)],
        [(0, 3, "D2", 98), (4, 2, "F2", 84), (7, 2, "G2", 88), (10, 2, "A2", 90),
         (12, 4, "A1", 86)],
        [(0, 3, "D2", 100), (4, 2, "D2", 80), (7, 2, "F2", 88), (10, 3, "C2", 90),
         (14, 2, "D2", 82)],
        [(0, 3, "D2", 98), (4, 2, "C2", 86), (6, 2, "B1", 84), (8, 4, "A1", 92),
         (12, 4, "D2", 90)],
    ]
    lead = [
        [(0, 2, "F4", 92), (2, 2, "G4", 90), (4, 4, "A4", 96)],
        [(0, 2, "C5", 94), (2, 2, "A4", 88), (4, 2, "G4", 86), (6, 4, "F4", 90)],
        [(0, 2, "F4", 90), (2, 2, "G4", 88), (4, 4, "A4", 94), (10, 2, "C5", 92),
         (12, 2, "D5", 96)],
        [(0, 6, "D4", 90)],
    ]
    chords = [
        [(0, 14, "D3", 60), (0, 14, "F3", 56), (0, 14, "A3", 54), (0, 14, "E4", 50),
         (10, 2, "F3", 46), (10, 2, "A3", 44)],                         # Dm9 + stab
        [(0, 14, "D3", 58), (0, 14, "F3", 54), (0, 14, "A3", 52), (0, 14, "E4", 48)],
        [(0, 14, "G3", 60), (0, 14, "B3", 56), (0, 14, "F4", 52),
         (10, 2, "B3", 46), (10, 2, "F4", 44)],                         # G7
        [(0, 14, "D3", 58), (0, 14, "F3", 54), (0, 14, "A3", 52), (0, 14, "E4", 48)],
    ]
    return dict(name="Lowgold", key="Ddor", bpm=84, feel="laidback", swing=True,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=33, lead=11, chords=4, arp=None))


def kit_seaglass():
    """Dream-pop doo-wop: C major, 92, I-vi-IV-V. The oldest progression
    there is, because it works. Stepwise sing-song lead that lands on
    thirds; root-5-6-5 bass; music-box arp."""
    A = {36: H(0, 104, 4, 92, 8, 100, 12, 92),
         38: H(4, 96, 12, 98),
         44: H(2, 46, 6, 46, 10, 46, 14, 46)}
    B = {36: H(0, 104, 4, 92, 8, 100),
         38: H(4, 96, 12, 82, 13, 86, 14, 90, 15, 94),   # snare build into the top
         44: H(2, 46, 6, 46, 10, 46)}
    drums = [A, A, A, B]

    def bar_bass(r, f, s):
        return [(0, 2, r, 96), (4, 2, f, 84), (8, 2, s, 88), (12, 2, f, 82)]
    bass = [bar_bass("C2", "G2", "A2"), bar_bass("A1", "E2", "G2"),
            bar_bass("F2", "C3", "D3"), bar_bass("G2", "D3", "E3")]

    lead = [
        [(0, 2, "E5", 94), (2, 2, "D5", 90), (4, 4, "C5", 92), (8, 2, "D5", 88),
         (10, 2, "E5", 90), (12, 4, "G5", 96)],
        [(0, 4, "E5", 94), (4, 2, "C5", 88), (6, 2, "B4", 86), (8, 8, "A4", 90)],
        [(0, 2, "A4", 88), (2, 2, "C5", 92), (4, 4, "F5", 94), (8, 2, "E5", 90),
         (10, 2, "D5", 88), (12, 4, "C5", 90)],
        [(0, 2, "D5", 92), (2, 2, "E5", 94), (4, 4, "D5", 96), (8, 6, "B4", 88)],
    ]
    chords = [
        [(0, 8, "G3", 62), (0, 8, "C4", 58), (0, 8, "E4", 54),
         (8, 8, "G3", 54), (8, 8, "C4", 50), (8, 8, "E4", 46)],
        [(0, 8, "A3", 62), (0, 8, "C4", 58), (0, 8, "E4", 54),
         (8, 8, "A3", 54), (8, 8, "C4", 50), (8, 8, "E4", 46)],
        [(0, 8, "A3", 62), (0, 8, "C4", 58), (0, 8, "F4", 54),
         (8, 8, "A3", 54), (8, 8, "C4", 50), (8, 8, "F4", 46)],
        [(0, 8, "G3", 62), (0, 8, "B3", 58), (0, 8, "D4", 54),
         (8, 8, "G3", 54), (8, 8, "B3", 50), (8, 8, "D4", 46)],
    ]
    def bar_arp(t1, t2, t3, t4):
        seq = [t1, t2, t3, t4, t3, t2, t1, t3]
        return [(i * 2, 2, seq[i], 54) for i in range(8)]
    arp = [bar_arp("C4", "E4", "G4", "C5"), bar_arp("A3", "C4", "E4", "A4"),
           bar_arp("A3", "C4", "F4", "A4"), bar_arp("B3", "D4", "G4", "B4")]
    return dict(name="Seaglass", key="Cmaj", bpm=92, feel="laidback", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=arp,
                progs=dict(bass=33, lead=5, chords=89, arp=10))


def kit_ironveil():
    """Dark techno / EBM: A minor, 126. Octave 16th bass pump under a
    four-note stab riff (A C B E) that everyone remembers after one loop."""
    A = {36: H(0, 112, 4, 104, 8, 106, 12, 104),
         46: H(2, 84, 6, 84, 10, 84, 14, 84),
         39: H(4, 90, 12, 92),
         37: H(3, 30, 7, 30, 11, 30, 15, 30)}
    B = {36: H(0, 112, 4, 104, 8, 106, 12, 102, 14, 96),
         46: H(2, 84, 6, 84, 10, 84, 15, 88),
         39: H(4, 90, 12, 92, 13, 84),
         37: H(3, 30, 11, 30)}
    drums = [A, A, A, B]

    def pump_bar(last4=None):
        bar = []
        for s in range(16):
            if last4 and s >= 12:
                break
            note = "A1" if s % 2 == 0 else "A2"
            vel = 100 if s % 4 == 0 else (80 if s % 2 == 0 else 66)
            bar.append((s, 1, note, vel))
        if last4:
            bar += last4
        return bar
    bass = [pump_bar(), pump_bar(), pump_bar(),
            pump_bar(last4=[(12, 1, "G1", 98), (13, 1, "G2", 68),
                            (14, 1, "B1", 98), (15, 1, "B2", 68)])]

    riff = [(0, 1, "A3", 100), (2, 1, "C4", 92), (4, 1, "B3", 90), (6, 2, "E4", 102)]
    lead = [
        riff + [(10, 1, "E4", 84), (12, 1, "D4", 88), (14, 1, "C4", 90)],
        riff + [(10, 1, "E4", 84), (12, 1, "D4", 88), (14, 1, "C4", 90)],
        riff + [(10, 1, "E4", 84), (12, 1, "D4", 88), (14, 1, "C4", 90)],
        riff + [(8, 1, "G4", 96), (10, 1, "E4", 90), (12, 1, "D4", 88), (14, 1, "B3", 86)],
    ]
    chords = [[(0, 16, "A2", 50), (0, 16, "E3", 46)]] * 4      # bare-fifth drone
    return dict(name="Ironveil", key="Am", bpm=126, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=38, lead=81, chords=95, arp=None))


def kit_holloway():
    """Trip-hop: F# minor, 76, heavy swing, the huge snare on beat 3.
    Bass creeps up chromatically (B - C - C#) into the five chord; the lead
    trembles a minor second and falls home."""
    A = {36: H(0, 110, 6, 88),
         38: H(8, 108),
         42: H(0, 56, 2, 40, 4, 52, 6, 40, 8, 56, 10, 40, 12, 52, 14, 44),
         37: H(5, 32, 13, 32),
         46: H(14, 74)}
    B = {36: H(0, 110, 6, 88, 13, 82),
         38: H(8, 106, 15, 62),
         41: H(11, 84),
         42: H(0, 56, 4, 52, 8, 56, 12, 52)}
    drums = [A, A, A, B]

    bass = [
        [(0, 4, "F#1", 98), (6, 2, "A1", 86), (8, 4, "F#1", 92), (14, 2, "C#2", 84)],
        [(0, 4, "F#1", 96), (6, 2, "A1", 84), (8, 2, "B1", 88), (10, 2, "C2", 90),
         (12, 4, "C#2", 92)],
        [(0, 4, "F#1", 98), (6, 2, "A1", 86), (8, 4, "F#1", 92), (14, 2, "C#2", 84)],
        [(0, 4, "F#1", 96), (8, 2, "E2", 88), (10, 2, "D2", 86), (12, 4, "C#2", 90)],
    ]
    lead = [
        [(0, 3, "C#5", 94), (3, 1, "D5", 68), (4, 4, "C#5", 90), (10, 2, "A4", 86),
         (12, 4, "F#4", 90)],
        [(0, 3, "B4", 92), (3, 1, "C5", 66), (4, 4, "B4", 88), (10, 2, "G#4", 84),
         (12, 4, "F#4", 88)],
        [(0, 3, "C#5", 94), (3, 1, "D5", 68), (4, 4, "C#5", 90), (10, 2, "A4", 86),
         (12, 4, "F#4", 90)],
        [(0, 2, "E5", 96), (2, 2, "D5", 92), (4, 4, "C#5", 94), (8, 8, "F#4", 90)],
    ]
    chords = [
        [(0, 16, "F#3", 56), (0, 16, "A3", 52), (0, 16, "C#4", 50), (0, 16, "G#4", 44)],
        [(0, 16, "F#3", 54), (0, 16, "A3", 50), (0, 16, "C#4", 48), (0, 16, "G#4", 42)],
        [(0, 16, "D3", 56), (0, 16, "F#3", 52), (0, 16, "A3", 50), (0, 16, "C#4", 46)],
        [(0, 16, "C#3", 56), (0, 16, "F3", 52), (0, 16, "G#3", 50), (0, 16, "B3", 46)],
    ]
    return dict(name="Holloway", key="F#m", bpm=76, feel="laidback", swing=True,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=33, lead=85, chords=4, arp=None))


def kit_morningvow():
    """A 6/8 ballad in G major, 72: I-vi-IV-V under a soaring lead that
    peaks on the high G in bar 2 and settles on the leading tone so the
    loop pulls itself back to the top. Twelve steps per bar."""
    A = {36: H(0, 100, 6, 88),
         37: H(3, 62, 9, 64),
         44: H(0, 48, 2, 40, 4, 44, 6, 48, 8, 40, 10, 44)}
    B = {36: H(0, 100, 6, 88),
         37: H(3, 62),
         45: H(8, 82), 48: H(10, 86),
         44: H(0, 48, 4, 44, 8, 42)}
    drums = [A, A, A, B]

    def bar_bass(r, f):
        return [(0, 4, r, 94), (6, 3, f, 84), (9, 3, r, 86)]
    bass = [bar_bass("G2", "D3"), bar_bass("E2", "B2"),
            bar_bass("C2", "G2"), bar_bass("D2", "A2")]

    lead = [
        [(0, 2, "D5", 92), (2, 2, "E5", 94), (4, 2, "D5", 90), (6, 4, "B4", 88),
         (10, 2, "G4", 86)],
        [(0, 4, "G5", 100), (4, 2, "F#5", 92), (6, 4, "E5", 94), (10, 2, "B4", 86)],
        [(0, 2, "C5", 90), (2, 2, "D5", 92), (4, 2, "E5", 94), (6, 4, "D5", 90),
         (10, 2, "C5", 86)],
        [(0, 4, "D5", 96), (4, 2, "C5", 88), (6, 6, "B4", 92)],
    ]
    chords = [
        [(0, 12, "G3", 60), (0, 12, "B3", 56), (0, 12, "D4", 52), (6, 6, "D4", 40)],
        [(0, 12, "E3", 60), (0, 12, "G3", 56), (0, 12, "B3", 52), (6, 6, "B3", 40)],
        [(0, 12, "G3", 60), (0, 12, "C4", 56), (0, 12, "E4", 52), (6, 6, "E4", 40)],
        [(0, 12, "F#3", 60), (0, 12, "A3", 56), (0, 12, "D4", 52), (6, 6, "D4", 40)],
    ]
    def bar_arp(t1, t2, t3, t4):
        seq = [t1, t2, t3, t4, t3, t2]
        return [(i * 2, 2, seq[i], 52) for i in range(6)]
    arp = [bar_arp("G4", "B4", "D5", "G5"), bar_arp("E4", "G4", "B4", "E5"),
           bar_arp("G4", "C5", "E5", "G5"), bar_arp("F#4", "A4", "D5", "F#5")]
    return dict(name="Morningvow", key="Gmaj", bpm=72, feel="laidback", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=arp,
                bar_steps=12, meter=(6, 8),
                progs=dict(bass=32, lead=73, chords=0, arp=46))


KIT_FNS = [kit_nightpulse, kit_glasskid, kit_hillrunner, kit_lowgold,
           kit_seaglass, kit_ironveil, kit_holloway, kit_morningvow]


# =============================================================================
def polish(events, kit, rng):
    """Feel micro-timing only -- the velocities above are the dynamics.
    Swung kits get the classic 8th-note shuffle (off-8ths delayed), applied
    to EVERY part so bass and lead shuffle together with the hats."""
    if not events:
        return events
    ev = events
    if kit["swing"]:
        ev = humanize.swing(ev, STEP * 2,
                            swing_pct=humanize.sixteenth_swing_pct(kit["bpm"]))
    ev = G.apply_feel(ev, kit["feel"], kit["bpm"], PPQ, rng,
                      anchor_ticks=kit.get("bar_steps", 16) * STEP if ev[0].channel == 9 else None)
    return anchor(ev, STEP)


def build_kit(kit, index):
    rng = random.Random(7000 + index)
    bar_steps = kit.get("bar_steps", 16)
    meter = kit.get("meter", (4, 4))
    drums = polish(drum_bars(kit["drums"], bar_steps), kit, rng)
    bass = polish(bars_to_events(kit["bass"], 0, bar_steps), kit, rng)
    lead = polish(bars_to_events(kit["lead"], 1, bar_steps), kit, rng)
    chords = polish(bars_to_events(kit["chords"], 2, bar_steps), kit, rng)
    arp = polish(bars_to_events(kit["arp"], 3, bar_steps), kit, rng) if kit["arp"] else []

    folder = os.path.join(DEST, f"{index:02d}_{kit['name']}_{kit['key']}_{kit['bpm']}")
    os.makedirs(folder, exist_ok=True)
    bpmc, tsc = [(0, kit["bpm"])], [(0, meter)]
    pr = kit["progs"]
    stems = [("drums", drums, 9, None), ("bass", bass, 0, pr["bass"]),
             ("lead", lead, 1, pr["lead"]), ("chords", chords, 2, pr["chords"]),
             ("arp", arp, 3, pr["arp"])]
    tracks = []
    for name, evs, ch, prog in stems:
        if not evs:
            continue
        midiwriter.write_track(os.path.join(folder, f"{name}.mid"), evs, bpmc, tsc,
                               channel=ch, program=prog, track_name=f"{kit['name']}-{name}")
        tracks.append({"events": evs, "channel": ch, "program": prog, "name": name})
    midiwriter.write_combined(os.path.join(folder, "full.mid"), tracks, bpmc, tsc)
    return folder, len(tracks)


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    print("KITS -- hand-composed, every note chosen\n")
    for i, fn in enumerate(KIT_FNS, 1):
        kit = fn()
        folder, n = build_kit(kit, i)
        doc = fn.__doc__.strip().split("\n")[0]
        print(f"  {os.path.basename(folder):<28} {n} parts   {doc}")
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(__doc__ + "\nKITS:\n" + "\n".join(
            f"  {fn().get('name'):<12} {fn().get('key'):<5} {fn().get('bpm'):>3}bpm  {fn.__doc__.strip().splitlines()[0]}"
            for fn in KIT_FNS))
    print(f"\n-> {DEST}")


if __name__ == "__main__":
    main()
