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



def kit_duskwire():
    """In Rainbows territory: E minor, 100. The interlocking 8th-note arpeggio
    IS the song (Em-C-G-D with common tones held between chords); the lead
    floats long hymn tones above it; bass approaches each new root by step."""
    A = {36: H(0, 102, 8, 94, 10, 88),
         38: H(4, 92, 12, 94),
         42: H(0, 58, 2, 50, 4, 56, 6, 50, 8, 58, 10, 50, 12, 56, 14, 52)}
    B = {36: H(0, 102, 8, 94, 10, 86, 14, 78),
         38: H(4, 92, 12, 92, 15, 64),
         48: H(13, 82),
         42: H(0, 58, 4, 56, 8, 58, 12, 56)}
    drums = [A, A, A, B]
    bass = [
        [(0, 4, "E2", 96), (6, 2, "E2", 78), (8, 4, "E2", 90), (14, 2, "D2", 80)],
        [(0, 4, "C2", 96), (6, 2, "C2", 78), (8, 4, "C2", 90), (14, 2, "B1", 80)],
        [(0, 4, "G2", 96), (6, 2, "G2", 78), (8, 4, "G2", 90), (14, 2, "F#2", 80)],
        [(0, 4, "D2", 96), (6, 2, "D2", 78), (8, 2, "A2", 84), (10, 2, "F#2", 82),
         (12, 4, "D2", 90)],
    ]
    lead = [
        [(0, 8, "B4", 88), (10, 4, "G4", 84)],
        [(0, 8, "C5", 90), (12, 4, "B4", 84)],
        [(0, 6, "B4", 86), (8, 8, "D5", 92)],
        [(0, 4, "A4", 88), (4, 4, "F#4", 84), (8, 8, "E4", 90)],
    ]
    chords = [
        [(0, 16, "E3", 48), (0, 16, "G3", 46), (0, 16, "B3", 44)],
        [(0, 16, "E3", 48), (0, 16, "G3", 46), (0, 16, "C4", 44)],
        [(0, 16, "D3", 48), (0, 16, "G3", 46), (0, 16, "B3", 44)],
        [(0, 16, "D3", 48), (0, 16, "F#3", 46), (0, 16, "A3", 44)],
    ]
    def bar_arp(n1, n2, n3, n4):
        seq = [n1, n2, n3, n4, n3, n2, n1, n3]
        return [(i * 2, 2, seq[i], 72 + (10 if i in (0, 4) else 0)) for i in range(8)]
    arp = [bar_arp("E4", "B4", "G4", "E5"), bar_arp("E4", "C5", "G4", "E5"),
           bar_arp("D4", "B4", "G4", "D5"), bar_arp("D4", "A4", "F#4", "D5")]
    return dict(name="Duskwire", key="Em", bpm=100, feel="laidback", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=arp,
                progs=dict(bass=33, lead=89, chords=48, arp=27))


def kit_autoglide():
    """Krautrock motorik: C mixolydian, 120. The bass is a relentless 8th-note
    C that finally admits the flat-7 (Bb) in bar 3 -- the one-chord jam that
    breathes; terse repeated lead figure, organ held underneath."""
    A = {36: H(0, 106, 4, 100, 8, 104, 12, 100),
         38: H(4, 94, 12, 96),
         42: H(0, 60, 2, 48, 4, 58, 6, 48, 8, 60, 10, 48, 12, 58, 14, 48)}
    B = {36: H(0, 106, 4, 100, 8, 104, 12, 98),
         38: H(4, 94, 12, 94, 14, 78),
         42: H(0, 60, 4, 58, 8, 60, 12, 58), 46: H(14, 82)}
    drums = [A, A, A, B]
    def drive(root):
        return [(i * 2, 2, root, 92 if i % 4 == 0 else 78) for i in range(8)]
    bass = [drive("C2"), drive("C2"),
            drive("Bb1"),
            [(0, 2, "F2", 92), (2, 2, "F2", 78), (4, 2, "F2", 84), (6, 2, "F2", 78),
             (8, 2, "G2", 92), (10, 2, "G2", 78), (12, 2, "G2", 86), (14, 2, "G2", 80)]]
    lead = [
        [(0, 2, "G4", 92), (4, 2, "E4", 88), (8, 2, "G4", 90), (12, 2, "A4", 86)],
        [(0, 2, "G4", 90), (4, 2, "E4", 86), (8, 2, "G4", 88), (12, 2, "E4", 84)],
        [(0, 2, "F4", 92), (4, 2, "D4", 88), (8, 2, "F4", 90), (12, 2, "G4", 86)],
        [(0, 2, "A4", 90), (4, 2, "F4", 88), (8, 4, "G4", 92)],
    ]
    chords = [
        [(0, 16, "G3", 52), (0, 16, "C4", 50), (0, 16, "E4", 48)],
        [(0, 16, "G3", 50), (0, 16, "C4", 48), (0, 16, "E4", 46)],
        [(0, 16, "F3", 52), (0, 16, "Bb3", 50), (0, 16, "D4", 48)],
        [(0, 8, "F3", 52), (0, 8, "A3", 50), (0, 8, "C4", 48),
         (8, 8, "G3", 52), (8, 8, "B3", 50), (8, 8, "D4", 48)],
    ]
    return dict(name="Autoglide", key="Cmix", bpm=120, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=33, lead=80, chords=16, arp=None))


def kit_veilfire():
    """Dark synth-pop: B minor, 112, Bm-G-D-A. The 16th-note syncopated bass
    with octave flicks is the engine; chord stabs live on the off-8ths; the
    lead hangs on the 2nd in bar 4 so the loop resolves itself."""
    A = {36: H(0, 108, 8, 100),
         38: H(4, 100, 12, 102), 39: H(4, 70, 12, 72),
         42: H(2, 54, 6, 54, 10, 54, 14, 54), 44: H(15, 40)}
    B = {36: H(0, 108, 8, 100, 10, 84),
         38: H(4, 100, 12, 100, 15, 58), 39: H(4, 70, 12, 72),
         42: H(2, 54, 6, 54, 10, 54), 46: H(14, 82)}
    drums = [A, A, A, B]
    def dmbass(r, hi):
        return [(0, 1, r, 100), (2, 1, r, 80), (3, 1, hi, 72), (4, 1, r, 92),
                (6, 1, r, 80), (8, 1, r, 96), (10, 1, hi, 74), (11, 1, r, 80),
                (12, 1, r, 90), (14, 1, r, 82)]
    bass = [dmbass("B1", "B2"), dmbass("G1", "G2"), dmbass("D2", "D3"), dmbass("A1", "A2")]
    lead = [
        [(0, 2, "D5", 96), (2, 2, "C#5", 90), (4, 4, "B4", 92), (10, 2, "F#4", 86),
         (12, 4, "B4", 90)],
        [(0, 2, "B4", 92), (2, 2, "A4", 88), (4, 4, "G4", 90), (10, 2, "D5", 92),
         (12, 4, "B4", 88)],
        [(0, 2, "A4", 90), (2, 2, "F#4", 86), (4, 4, "D4", 88), (10, 2, "F#4", 84),
         (12, 4, "A4", 90)],
        [(0, 2, "C#5", 94), (2, 2, "E5", 98), (4, 4, "C#5", 92), (8, 8, "B4", 90)],
    ]
    def stabs(n1, n2, n3):
        out = []
        for s in (2, 6, 10, 14):
            out += [(s, 1, n1, 68), (s, 1, n2, 64), (s, 1, n3, 60)]
        return out
    chords = [stabs("F#3", "B3", "D4"), stabs("G3", "B3", "D4"),
              stabs("F#3", "A3", "D4"), stabs("E3", "A3", "C#4")]
    return dict(name="Veilfire", key="Bm", bpm=112, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=38, lead=81, chords=90, arp=None))


def kit_palefen():
    """The Cure territory: D minor, 96, Dm-Bb-F-C. Floor tom drives under
    straight 16th hats; a watery two-octave arp; the lead speaks one falling
    line, waits a bar, answers, and waits again."""
    A = {36: H(0, 104, 8, 98),
         38: H(4, 94, 12, 96),
         41: H(0, 60, 8, 58),
         42: H(0, 54, 1, 38, 2, 50, 3, 38, 4, 54, 5, 38, 6, 50, 7, 38,
               8, 54, 9, 38, 10, 50, 11, 38, 12, 54, 13, 38, 14, 50, 15, 40)}
    B = {36: H(0, 104, 8, 96),
         38: H(4, 94, 12, 94),
         41: H(0, 60, 8, 58, 12, 70, 14, 74), 43: H(13, 72, 15, 78),
         42: H(0, 54, 4, 54, 8, 54, 12, 54)}
    drums = [A, A, A, B]
    def pedal(r, approach):
        notes = [(i * 2, 2, r, 88 if i % 4 == 0 else 76) for i in range(7)]
        return notes + [(14, 2, approach, 78)]
    bass = [pedal("D2", "C2"), pedal("Bb1", "C2"), pedal("F2", "E2"), pedal("C2", "C2")]
    lead = [
        [(0, 4, "A4", 92), (4, 2, "G4", 88), (6, 2, "F4", 86), (8, 8, "E4", 90)],
        [],
        [(0, 4, "C5", 92), (4, 2, "A4", 88), (6, 2, "G4", 86), (8, 8, "A4", 90)],
        [],
    ]
    chords = [
        [(0, 16, "D3", 50), (0, 16, "F3", 48), (0, 16, "A3", 46)],
        [(0, 16, "D3", 50), (0, 16, "F3", 48), (0, 16, "Bb3", 46)],
        [(0, 16, "C3", 50), (0, 16, "F3", 48), (0, 16, "A3", 46)],
        [(0, 16, "C3", 50), (0, 16, "E3", 48), (0, 16, "G3", 46)],
    ]
    def bar_arp(n1, n2, n3, n4):
        seq = [n1, n2, n3, n4, n3, n2, n1, n3]
        return [(i * 2, 2, seq[i], 62 + (8 if i == 0 else 0)) for i in range(8)]
    arp = [bar_arp("D4", "F4", "A4", "D5"), bar_arp("D4", "F4", "Bb4", "D5"),
           bar_arp("C4", "F4", "A4", "C5"), bar_arp("C4", "E4", "G4", "C5")]
    return dict(name="Palefen", key="Dm", bpm=96, feel="laidback", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=arp,
                progs=dict(bass=34, lead=89, chords=50, arp=27))


def kit_redloam():
    """Gothic blues stomp in 12/8: E minor, 54. Kick on 1 and 3, snare on 2
    and 4, triplet ticks between; the lead is minor pentatonic with the flat
    five leaned on hard; Em-Em-Am-B7, the oldest dark-blues turnaround."""
    A = {36: H(0, 112, 12, 104),
         38: H(6, 102, 18, 104),
         44: H(0, 46, 2, 36, 4, 40, 6, 46, 8, 36, 10, 40, 12, 46, 14, 36,
               16, 40, 18, 46, 20, 36, 22, 40),
         41: H(22, 68)}
    B = {36: H(0, 112, 12, 102),
         38: H(6, 102, 18, 100),
         44: H(0, 46, 6, 44, 12, 46),
         41: H(18, 82, 20, 86), 45: H(21, 84, 22, 88, 23, 92)}
    drums = [A, A, A, B]
    bass = [
        [(0, 6, "E1", 100), (6, 4, "G1", 84), (10, 2, "A1", 86), (12, 6, "E1", 96),
         (18, 4, "G1", 86), (22, 2, "A1", 88)],
        [(0, 6, "E1", 100), (6, 4, "G1", 84), (10, 2, "A1", 86), (12, 6, "E1", 94),
         (18, 6, "B1", 88)],
        [(0, 6, "A1", 98), (6, 6, "C2", 86), (12, 6, "A1", 94), (18, 6, "G1", 86)],
        [(0, 6, "B1", 98), (6, 6, "A1", 86), (12, 6, "B1", 92), (18, 6, "D#2", 88)],
    ]
    lead = [
        [(0, 4, "E4", 94), (4, 2, "G4", 90), (6, 6, "A4", 92), (12, 4, "Bb4", 98),
         (16, 2, "A4", 88), (18, 6, "G4", 90)],
        [(0, 10, "E4", 92)],
        [(0, 4, "A4", 94), (4, 2, "C5", 96), (6, 6, "A4", 90), (12, 12, "G4", 88)],
        [(0, 4, "F#4", 90), (4, 2, "A4", 88), (6, 6, "D#4", 92), (12, 12, "E4", 94)],
    ]
    chords = [
        [(0, 12, "E3", 54), (0, 12, "G3", 52), (0, 12, "B3", 50),
         (12, 12, "E3", 48), (12, 12, "G3", 46), (12, 12, "B3", 44)],
        [(0, 12, "E3", 54), (0, 12, "G3", 52), (0, 12, "B3", 50),
         (12, 12, "E3", 48), (12, 12, "G3", 46), (12, 12, "B3", 44)],
        [(0, 12, "E3", 54), (0, 12, "A3", 52), (0, 12, "C4", 50),
         (12, 12, "E3", 48), (12, 12, "A3", 46), (12, 12, "C4", 44)],
        [(0, 12, "D#3", 54), (0, 12, "F#3", 52), (0, 12, "B3", 50),
         (12, 12, "D#3", 48), (12, 12, "A3", 46), (12, 12, "B3", 44)],
    ]
    return dict(name="Redloam", key="Em", bpm=54, feel="ritual", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                bar_steps=24, meter=(12, 8),
                progs=dict(bass=32, lead=25, chords=16, arp=None))


def kit_chromehall():
    """Synthwave: G minor, 100, Gm-Eb-Bb-F. Octave 8th bass under a big
    long-note saw hook; the chords pulse on the off-8ths like a sidechain."""
    A = {36: H(0, 106, 8, 96, 10, 90),
         38: H(4, 102, 12, 104),
         42: H(2, 56, 6, 56, 10, 56, 14, 56), 46: H(14, 80)}
    B = {36: H(0, 106, 8, 96),
         38: H(4, 102, 12, 78, 13, 84, 14, 90, 15, 96),
         42: H(2, 56, 6, 56, 10, 56)}
    drums = [A, A, A, B]
    def oct8(lo, hi):
        return [(i * 2, 2, lo if i % 2 == 0 else hi, 96 if i % 4 == 0 else 70)
                for i in range(8)]
    bass = [oct8("G1", "G2"), oct8("Eb1", "Eb2"), oct8("Bb1", "Bb2"), oct8("F1", "F2")]
    lead = [
        [(0, 6, "G4", 98), (6, 2, "F4", 88), (8, 8, "Bb4", 96)],
        [(0, 6, "Eb5", 100), (6, 2, "D5", 90), (8, 8, "Bb4", 92)],
        [(0, 6, "D5", 98), (6, 2, "C5", 88), (8, 8, "Bb4", 94)],
        [(0, 6, "A4", 96), (6, 2, "C5", 92), (8, 8, "G4", 90)],
    ]
    def pulse(n1, n2, n3):
        out = []
        for s in (2, 6, 10, 14):
            out += [(s, 2, n1, 62), (s, 2, n2, 58), (s, 2, n3, 54)]
        return out
    chords = [pulse("G3", "Bb3", "D4"), pulse("G3", "Bb3", "Eb4"),
              pulse("F3", "Bb3", "D4"), pulse("F3", "A3", "C4")]
    return dict(name="Chromehall", key="Gm", bpm=100, feel="pushing", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=38, lead=81, chords=90, arp=None))


def kit_thornfield():
    """Dark stomp in E phrygian, 92: the F-natural against E is the whole
    drama. Toms answer the kick; the lead states E-F, peaks on G in bar 3,
    and lands low; the bass leans on the pedal and walks B back home."""
    A = {36: H(0, 110, 8, 100),
         41: H(3, 84, 11, 86), 45: H(6, 82, 14, 84),
         37: H(4, 68, 12, 70),
         44: H(0, 48, 2, 40, 4, 46, 6, 40, 8, 48, 10, 40, 12, 46, 14, 42)}
    B = {36: H(0, 110, 8, 98),
         41: H(3, 84, 12, 84), 45: H(6, 80, 13, 88), 48: H(10, 84, 14, 92, 15, 96),
         37: H(4, 66),
         44: H(0, 48, 4, 46, 8, 48)}
    drums = [A, A, A, B]
    bass = [
        [(0, 4, "E2", 98), (6, 2, "E2", 80), (8, 4, "E2", 94), (14, 2, "E2", 78)],
        [(0, 4, "F2", 96), (6, 2, "E2", 78), (8, 4, "F2", 92), (14, 2, "F2", 80)],
        [(0, 4, "E2", 98), (6, 2, "E2", 80), (8, 4, "E2", 94), (14, 2, "E2", 78)],
        [(0, 4, "D2", 96), (8, 2, "D2", 84), (10, 2, "C2", 82), (12, 4, "B1", 90)],
    ]
    lead = [
        [(0, 2, "E5", 100), (2, 2, "F5", 96), (4, 4, "E5", 94), (10, 2, "D5", 88),
         (12, 4, "B4", 90)],
        [(0, 2, "F5", 98), (2, 2, "E5", 92), (4, 4, "C5", 94), (8, 8, "A4", 90)],
        [(0, 2, "E5", 98), (2, 2, "F5", 94), (4, 4, "G5", 100), (10, 2, "F5", 90),
         (12, 4, "E5", 92)],
        [(0, 12, "E4", 92)],
    ]
    chords = [
        [(0, 8, "E3", 54), (0, 8, "G3", 52), (0, 8, "B3", 50),
         (8, 8, "E3", 48), (8, 8, "G3", 46), (8, 8, "B3", 44)],
        [(0, 8, "F3", 54), (0, 8, "A3", 52), (0, 8, "C4", 50),
         (8, 8, "F3", 48), (8, 8, "A3", 46), (8, 8, "C4", 44)],
        [(0, 8, "E3", 54), (0, 8, "G3", 52), (0, 8, "B3", 50),
         (8, 8, "E3", 48), (8, 8, "G3", 46), (8, 8, "B3", 44)],
        [(0, 8, "D3", 54), (0, 8, "F3", 52), (0, 8, "A3", 50),
         (8, 8, "D3", 48), (8, 8, "F3", 46), (8, 8, "A3", 44)],
    ]
    return dict(name="Thornfield", key="Ephr", bpm=92, feel="ritual", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=42, lead=48, chords=48, arp=None))


def kit_brightwork():
    """Dorian funk: A dorian, 116, the two-chord Am7-D9 vamp. Syncopated bass
    with octave pops, ghost-note snare hand, ninth-chord stabs off the beat,
    and a riff that saves the dorian F# for the last bar."""
    A = {36: H(0, 108, 7, 90, 10, 94),
         38: H(4, 102, 6, 32, 12, 104, 15, 30),
         42: H(0, 60, 2, 46, 4, 58, 6, 46, 8, 60, 10, 46, 12, 58, 14, 48),
         46: H(14, 80)}
    B = {36: H(0, 108, 7, 90, 10, 92, 13, 84),
         38: H(4, 102, 12, 96, 14, 84, 15, 90),
         42: H(0, 60, 4, 58, 8, 60, 12, 58)}
    drums = [A, A, A, B]
    bass = [
        [(0, 2, "A1", 100), (3, 1, "A1", 70), (4, 2, "A2", 84), (7, 2, "A1", 88),
         (10, 1, "G1", 80), (11, 1, "A1", 84), (12, 2, "C2", 86), (14, 2, "E2", 88)],
        [(0, 2, "D2", 98), (3, 1, "D2", 70), (4, 2, "D3", 82), (7, 2, "D2", 86),
         (10, 2, "C2", 82), (12, 2, "B1", 84), (14, 2, "A1", 86)],
        [(0, 2, "A1", 100), (3, 1, "A1", 70), (4, 2, "A2", 84), (7, 2, "A1", 88),
         (10, 1, "G1", 80), (11, 1, "A1", 84), (12, 2, "C2", 86), (14, 2, "E2", 88)],
        [(0, 2, "D2", 98), (4, 2, "F#2", 88), (6, 2, "A2", 90), (8, 2, "C3", 88),
         (10, 2, "B2", 86), (12, 4, "E2", 90)],
    ]
    lead = [
        [(0, 1, "E5", 96), (1, 1, "G5", 92), (2, 2, "E5", 94), (6, 2, "C5", 88),
         (8, 2, "A4", 90), (12, 2, "B4", 86), (14, 2, "C5", 88)],
        [(8, 2, "E5", 92), (10, 2, "D5", 88), (12, 4, "B4", 90)],
        [(0, 1, "E5", 96), (1, 1, "G5", 92), (2, 2, "E5", 94), (6, 2, "C5", 88),
         (8, 2, "A4", 90), (12, 2, "B4", 86), (14, 2, "C5", 88)],
        [(0, 2, "A4", 90), (2, 2, "C5", 92), (4, 2, "D5", 94), (6, 2, "E5", 96),
         (8, 6, "F#5", 98), (14, 2, "E5", 90)],
    ]
    def stabs(n1, n2, n3, extra=False):
        out = []
        for s in ((2, 10, 13) if extra else (2, 10)):
            out += [(s, 1, n1, 70), (s, 1, n2, 66), (s, 1, n3, 62)]
        return out
    chords = [stabs("G3", "C4", "E4"), stabs("F#3", "C4", "E4", extra=True),
              stabs("G3", "C4", "E4"), stabs("F#3", "C4", "E4", extra=True)]
    return dict(name="Brightwork", key="Ador", bpm=116, feel="laidback", swing=False,
                drums=drums, bass=bass, lead=lead, chords=chords, arp=None,
                progs=dict(bass=36, lead=62, chords=4, arp=None))


KIT_FNS = [kit_nightpulse, kit_glasskid, kit_hillrunner, kit_lowgold,
           kit_seaglass, kit_ironveil, kit_holloway, kit_morningvow,
           kit_duskwire, kit_autoglide, kit_veilfire, kit_palefen,
           kit_redloam, kit_chromehall, kit_thornfield, kit_brightwork]


# =============================================================================
# SECTION VARIATIONS -- four clips per part: 1_intro, 2_main, 3_lift, 4_break.
# Load a part's four clips across a 707 clip column and you have sections:
# chain 1-2-2-3-2-3-4-2 (or your own order) and the song arranges itself.
# Drum section textures are hand-specified per kit below; pitched variations
# are composed transformations (reduction / octave thickening / fragment
# isolation) -- arrangement moves, not randomness.
# =============================================================================

# per-kit drum section specs:
#   intro: voices to KEEP from the main pattern (stripped opening)
#   lift_add: {note: hits} layered onto every main A bar (+ crash on bar 1)
#   brk: explicit hand-written 4-bar texture (the breakdown)
DRUM_VARS = {
    "Nightpulse": dict(
        intro=[36, 44, 37],
        lift_add={42: H(0, 58, 2, 44, 4, 54, 6, 44, 8, 56, 10, 44, 12, 54, 14, 46),
                  46: H(6, 80)},
        brk=[{41: H(0, 90, 6, 82, 11, 86), 45: H(3, 84, 13, 88), 48: H(9, 80),
              44: H(2, 42, 6, 42, 10, 42, 14, 42)}] * 3 +
            [{41: H(0, 90), 45: H(4, 86), 48: H(8, 88, 12, 92), 36: H(14, 70)}]),
    "Glasskid": dict(
        intro=[36, 44],
        lift_add={42: H(2, 58, 6, 58, 10, 58, 14, 58), 46: H(14, 86)},
        brk=[{39: H(4, 88, 12, 90), 40: H(14, 60),
              37: H(0, 40, 3, 38, 5, 36, 8, 40, 11, 38, 13, 36)}] * 3 +
            [{39: H(4, 88, 12, 90, 14, 84), 40: H(15, 70), 37: H(0, 40, 8, 40)}]),
    "Hillrunner": dict(
        intro=[36, 38, 44],
        lift_add={46: H(6, 84, 14, 86), 51: H(0, 72, 4, 70, 8, 72, 12, 70)},
        brk=[{43: H(3, 86, 4, 78, 11, 86, 12, 78), 45: H(0, 88, 8, 86),
              44: H(2, 44, 10, 44)}] * 3 +
            [{45: H(0, 88), 48: H(4, 84, 8, 88, 12, 92, 14, 96)}]),
    "Lowgold": dict(
        intro=[36, 42],
        lift_add={39: H(4, 66, 12, 68), 46: H(14, 82)},
        brk=[{37: H(0, 48, 5, 40, 7, 36, 10, 44, 15, 34),
              44: H(2, 46, 6, 46, 10, 46, 14, 46)}] * 3 +
            [{37: H(0, 48, 7, 38), 44: H(2, 46, 6, 46), 45: H(12, 80, 14, 84)}]),
    "Seaglass": dict(
        intro=[36, 44],
        lift_add={46: H(6, 80, 14, 82), 37: H(2, 40, 10, 40)},
        brk=[{36: H(0, 96, 8, 92), 46: H(12, 72),
              44: H(2, 44, 4, 40, 6, 44, 10, 44, 12, 40, 14, 44)}] * 3 +
            [{36: H(0, 96), 38: H(12, 74, 13, 78, 14, 84, 15, 90)}]),
    "Ironveil": dict(
        intro=[36, 37],
        lift_add={42: H(1, 54, 3, 54, 5, 54, 7, 54, 9, 54, 11, 54, 13, 54, 15, 54)},
        brk=[{46: H(2, 80, 6, 80, 10, 80, 14, 80), 39: H(0, 74, 4, 84, 12, 86),
              37: H(1, 30, 3, 30, 5, 30, 7, 30, 9, 30, 11, 30, 13, 30, 15, 30)}] * 3 +
            [{46: H(2, 80, 6, 80, 10, 80), 39: H(0, 74, 4, 84, 12, 86),
              40: H(8, 70, 12, 74, 14, 80)}]),
    "Holloway": dict(
        intro=[36, 42],
        lift_add={46: H(6, 76), 41: H(11, 70)},
        brk=[{38: H(8, 100), 37: H(0, 44, 5, 34, 13, 34),
              44: H(2, 46, 6, 46, 10, 46, 14, 46)}] * 3 +
            [{38: H(8, 100, 15, 58), 41: H(11, 80), 44: H(2, 46, 10, 46)}]),
    "Morningvow": dict(
        intro=[36, 44],
        lift_add={46: H(10, 74), 51: H(0, 64, 6, 62)},
        brk=[{37: H(3, 58, 9, 60), 45: H(6, 74),
              44: H(0, 44, 2, 40, 4, 42, 6, 44, 8, 40, 10, 42)}] * 3 +
            [{37: H(3, 58), 45: H(6, 76), 48: H(8, 80, 10, 86)}]),
    "Duskwire": dict(
        intro=[42, 36],
        lift_add={46: H(6, 80, 14, 82), 51: H(0, 66, 4, 64, 8, 66, 12, 64)},
        brk=[{42: H(0, 50, 2, 42, 4, 48, 6, 42, 8, 50, 10, 42, 12, 48, 14, 44),
              37: H(4, 50, 12, 50), 41: H(8, 78)}] * 3 +
            [{42: H(0, 50, 4, 48, 8, 50), 45: H(8, 82, 11, 84), 48: H(14, 88)}]),
    "Autoglide": dict(
        intro=[36, 42],
        lift_add={46: H(2, 80, 6, 80, 10, 80, 14, 80)},
        brk=[{42: H(0, 44, 1, 34, 2, 42, 3, 34, 4, 44, 5, 34, 6, 42, 7, 34,
                    8, 44, 9, 34, 10, 42, 11, 34, 12, 44, 13, 34, 14, 42, 15, 36),
              37: H(0, 52, 4, 50, 8, 52, 12, 50)}] * 3 +
            [{42: H(0, 44, 4, 42, 8, 44), 38: H(12, 68, 13, 74, 14, 80, 15, 86)}]),
    "Veilfire": dict(
        intro=[36, 42],
        lift_add={46: H(6, 82, 14, 84),
                  44: H(1, 36, 3, 36, 5, 36, 7, 36, 9, 36, 11, 36, 13, 36)},
        brk=[{39: H(0, 72, 4, 84, 12, 86),
              44: H(1, 34, 3, 34, 5, 34, 7, 34, 9, 34, 11, 34, 13, 34, 15, 34)}] * 3 +
            [{39: H(0, 72, 4, 84, 12, 86, 14, 80), 40: H(15, 66)}]),
    "Palefen": dict(
        intro=[36, 42],
        lift_add={46: H(6, 80, 14, 80)},
        brk=[{41: H(0, 70, 2, 50, 4, 64, 6, 50, 8, 68, 10, 50, 12, 64, 14, 52),
              37: H(4, 52, 12, 54)}] * 3 +
            [{41: H(0, 70, 4, 64, 8, 68), 43: H(12, 74, 14, 78)}]),
    "Redloam": dict(
        intro=[36, 44],
        lift_add={51: H(0, 68, 6, 66, 12, 68, 18, 66), 46: H(22, 78)},
        brk=[{44: H(0, 46, 2, 36, 4, 40, 6, 46, 8, 36, 10, 40, 12, 46, 14, 36,
                    16, 40, 18, 46, 20, 36, 22, 40), 37: H(6, 56, 18, 58)}] * 3 +
            [{44: H(0, 46, 6, 44, 12, 46), 37: H(6, 56),
              45: H(18, 80, 20, 84, 22, 88)}]),
    "Chromehall": dict(
        intro=[36, 42],
        lift_add={46: H(2, 78, 6, 78, 10, 78, 14, 78)},
        brk=[{39: H(0, 70, 4, 80, 12, 82),
              42: H(0, 42, 1, 34, 2, 40, 3, 34, 4, 42, 5, 34, 6, 40, 7, 34,
                    8, 42, 9, 34, 10, 40, 11, 34, 12, 42, 13, 34, 14, 40, 15, 36)}] * 3 +
            [{39: H(0, 70, 4, 80, 12, 82), 38: H(12, 70, 13, 76, 14, 82, 15, 88)}]),
    "Thornfield": dict(
        intro=[36, 44],
        lift_add={46: H(6, 82, 14, 84), 51: H(0, 68, 4, 66, 8, 68, 12, 66)},
        brk=[{41: H(0, 84, 6, 80, 11, 84), 45: H(3, 80, 14, 82),
              44: H(2, 42, 6, 42, 10, 42, 14, 42)}] * 3 +
            [{41: H(0, 84), 45: H(6, 82), 48: H(10, 84, 12, 88, 14, 92)}]),
    "Brightwork": dict(
        intro=[36, 42],
        lift_add={46: H(14, 84), 39: H(4, 72, 12, 74)},
        brk=[{38: H(0, 40, 4, 96, 6, 30, 12, 98, 15, 28),
              44: H(2, 44, 6, 44, 10, 44, 14, 44)}] * 3 +
            [{38: H(0, 40, 4, 96, 12, 96, 13, 80, 14, 86, 15, 92),
              44: H(2, 44, 6, 44)}]),
}


def drums_variation(kit, which):
    name, spec = kit["name"], DRUM_VARS[kit["name"]]
    main = kit["drums"]
    if which == "main":
        return main
    if which == "intro":
        keep = set(spec["intro"])
        return [{n: [(s, max(1, int(v * 0.85))) for (s, v) in hits]
                 for n, hits in bar.items() if n in keep} for bar in main]
    if which == "lift":
        out = []
        for bi, bar in enumerate(main):
            nb = {n: list(h) for n, h in bar.items()}
            for n, hits in spec["lift_add"].items():
                nb.setdefault(n, [])
                nb[n] = nb[n] + list(hits)
            if bi == 0:
                nb.setdefault(49, [])
                nb[49] = nb[49] + [(0, 100)]     # the crash that opens the lift
            out.append(nb)
        return out
    return spec["brk"]


def bass_variation(bars, which, bar_steps):
    if which == "main":
        return bars
    if which == "intro":                          # root motion only, held
        return [[(0, bar_steps, b[0][2], max(1, b[0][3] - 8))] for b in bars]
    if which == "lift":                           # octave-up shadow thickens it
        out = []
        for bar in bars:
            nb = list(bar)
            for (s, d, note, v) in bar:
                nn = (N(note) if isinstance(note, str) else note) + 12
                nb.append((s, d, nn, max(1, int(v * 0.55))))
            out.append(nb)
        return out
    # break: drones on the bar roots, the written turnaround pulls back in
    return [[(0, bar_steps, b[0][2], max(1, b[0][3] - 12))] for b in bars[:3]] + [bars[3]]


def lead_variation(bars, which):
    if which == "main":
        return bars
    if which == "intro":                          # the call, then space
        return [bars[0], bars[1], [], []]
    if which == "lift":                           # octave double = chorus voice
        out = []
        for bar in bars:
            nb = list(bar)
            for (s, d, note, v) in bar:
                nn = (N(note) if isinstance(note, str) else note) + 12
                nb.append((s, d, nn, max(1, v - 24)))
            out.append(nb)
        return out
    # break: answers only, spacious -- lead with whichever answer phrase
    # starts earliest so the clip still launches on (or near) beat 1
    a, b = bars[1], bars[3]
    def first_onset(bar):
        return min((s for (s, d, n, v) in bar), default=99)
    if first_onset(b) < first_onset(a):
        a, b = b, a
    return [a, [], b, []]


def chords_variation(bars, which, bar_steps):
    if which == "main":
        return bars
    if which == "intro":                          # one held strike per bar
        out = []
        for bar in bars:
            first = min(s for (s, d, n, v) in bar)
            out.append([(first, bar_steps - first, n, max(1, v - 6))
                        for (s, d, n, v) in bar if s == first])
        return out
    if which == "lift":                           # rhythmic comp -- the 'rhythm' clip
        strikes = {16: (0, 4, 8, 12), 12: (0, 3, 6, 9), 24: (0, 6, 12, 18)}[bar_steps]
        out = []
        for bar in bars:
            first = min(s for (s, d, n, v) in bar)
            tones = [(n, v) for (s, d, n, v) in bar if s == first]
            nb = []
            for k, st in enumerate(strikes):
                for (n, v) in tones:
                    nb.append((st, 2, n, max(1, (v + 8) if k % 2 == 0 else (v - 6))))
            out.append(nb)
        return out
    out = []                                      # break: low floor, single strike
    for bar in bars:
        first = min(s for (s, d, n, v) in bar)
        out.append([(first, bar_steps - first,
                     (N(n) if isinstance(n, str) else n) - 12, max(1, v - 10))
                    for (s, d, n, v) in bar if s == first])
    return out


def arp_variation(bars, which):
    if which == "main":
        return bars
    if which == "intro":                          # half density
        return [[t for i, t in enumerate(bar) if i % 2 == 0] for bar in bars]
    if which == "lift":                           # up the octave
        return [[(s, d, (N(n) if isinstance(n, str) else n) + 12, v)
                 for (s, d, n, v) in bar] for bar in bars]
    return [[(s, d, (N(n) if isinstance(n, str) else n) - 12, max(1, v - 8))
             for i, (s, d, n, v) in enumerate(bar) if i % 2 == 0] for bar in bars]


VARIATIONS = [("1_intro", "intro"), ("2_main", "main"),
              ("3_lift", "lift"), ("4_break", "break")]


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
    bpmc, tsc = [(0, kit["bpm"])], [(0, meter)]
    pr = kit["progs"]
    folder = os.path.join(DEST, f"{index:02d}_{kit['name']}_{kit['key']}_{kit['bpm']}")

    parts = {
        "drums": (lambda w: drum_bars(drums_variation(kit, w), bar_steps), 9, None),
        "bass": (lambda w: bars_to_events(bass_variation(kit["bass"], w, bar_steps), 0, bar_steps), 0, pr["bass"]),
        "lead": (lambda w: bars_to_events(lead_variation(kit["lead"], w), 1, bar_steps), 1, pr["lead"]),
        "chords": (lambda w: bars_to_events(chords_variation(kit["chords"], w, bar_steps), 2, bar_steps), 2, pr["chords"]),
    }
    if kit["arp"]:
        parts["arp"] = (lambda w: bars_to_events(arp_variation(kit["arp"], w), 3, bar_steps), 3, pr["arp"])

    previews = {"2_main": [], "3_lift": []}
    n_files = 0
    for part, (make, ch, prog) in parts.items():
        pdir = os.path.join(folder, part)
        os.makedirs(pdir, exist_ok=True)
        for fname, which in VARIATIONS:
            evs = polish(make(which), kit, rng)
            if not evs:
                continue
            midiwriter.write_track(os.path.join(pdir, f"{fname}.mid"), evs, bpmc, tsc,
                                   channel=ch, program=prog,
                                   track_name=f"{kit['name']}-{part}-{which}")
            n_files += 1
            if fname in previews:
                previews[fname].append({"events": evs, "channel": ch, "program": prog,
                                        "name": part})
    midiwriter.write_combined(os.path.join(folder, "full_main.mid"),
                              previews["2_main"], bpmc, tsc)
    midiwriter.write_combined(os.path.join(folder, "full_lift.mid"),
                              previews["3_lift"], bpmc, tsc)
    return folder, n_files


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    print("KITS -- hand-composed; four section variations per part\n")
    total = 0
    for i, fn in enumerate(KIT_FNS, 1):
        kit = fn()
        folder, n = build_kit(kit, i)
        total += n
        print(f"  {os.path.basename(folder):<28} {n} clips + 2 previews")
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(__doc__ + """
SECTIONS: every part folder holds four clips --
  1_intro   stripped statement (root-motion bass, the call alone, held pads)
  2_main    the song as written
  3_lift    the chorus voice (crash entry, added hats/ride, octave doubles,
            chords become rhythmic comp)
  4_break   the floor drops (breakdown drums, drone bass w/ written
            turnaround, answers-only lead, low held pads)
Load a part's four clips down one MC-707 clip column; build sections by
switching columns: e.g. 1-2-2-3 / 2-3-4-2 / ... full_main.mid and
full_lift.mid are stacked previews of columns 2 and 3.
""")
    print(f"\n{total} clips -> {DEST}")


if __name__ == "__main__":
    main()
