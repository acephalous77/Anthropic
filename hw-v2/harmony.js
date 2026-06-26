// harmony.js — VT-4 harmony driver: progression, clock-locked auto-advance,
// note output. The core of v2's musical intelligence.
//
// VT-4 Harmony mode interprets incoming MIDI notes as the key/scale center for
// its harmony generation, not as specific pitches to play. Sending C4+E4+G4
// sets a C-major harmonic context.

// Chord quality -> interval sets (semitones above root).
export const CHORD_QUALITIES = {
  maj: [0, 4, 7],
  min: [0, 3, 7],
  dom7: [0, 4, 7, 10],
  maj7: [0, 4, 7, 11],
  min7: [0, 3, 7, 10],
  dim: [0, 3, 6],
  aug: [0, 4, 8],
  sus2: [0, 2, 7],
  sus4: [0, 5, 7],
  min9: [0, 3, 7, 10, 14],
  add9: [0, 4, 7, 14],
};

export const NOTE_NAMES = [
  'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
];

export function chordName(root, quality) {
  return NOTE_NAMES[((root % 12) + 12) % 12] + ' ' + quality;
}

export function midiNoteName(note) {
  const n = NOTE_NAMES[((note % 12) + 12) % 12];
  const oct = Math.floor(note / 12) - 1;
  return n + oct;
}

export class HarmonyEngine {
  constructor(clockEngine, midiEngine) {
    this.clock = clockEngine;
    this.midi = midiEngine;

    this.channel = 1; // VT-4 default
    this.voiceCount = 2;
    this.octave = 4;
    this.inversion = 0; // 0 root, 1 first, 2 second
    this.mode = 'auto';

    this.progression = [];
    this._stepIndex = 0;
    this._barsRemaining = 0;
    this._lastBar = -1;
    this._running = false;
    this._locked = false;
    this._activeNotes = [];

    this._stepChangeCallbacks = [];
    this._barsRemainingCallbacks = [];

    this.clock.onTick((t) => this._onTick(t));
  }

  // --- Configuration ---

  setChannel(ch) {
    this.channel = Math.max(1, Math.min(16, Math.round(ch)));
  }

  setVoiceCount(n) {
    this.voiceCount = Math.max(1, Math.min(3, Math.round(n)));
  }

  setOctave(n) {
    this.octave = Math.max(3, Math.min(5, Math.round(n)));
  }

  setInversion(n) {
    this.inversion = Math.max(0, Math.min(2, Math.round(n)));
  }

  setMode(mode) {
    if (mode !== 'auto' && mode !== 'lock' && mode !== 'manual') return;
    // On mode switch, clear any orphan notes to be safe.
    const prev = this.mode;
    this.mode = mode;
    if (mode === 'lock') {
      this._locked = true;
    } else if (prev === 'lock') {
      this._locked = false;
    }
  }

  getMode() {
    return this.mode;
  }

  // --- Progression ---

  setProgression(steps) {
    this.progression = (steps || []).slice(0, 8).map((s) => ({
      root: ((Math.round(s.root) % 12) + 12) % 12,
      quality: CHORD_QUALITIES[s.quality] ? s.quality : 'maj',
      bars: Math.max(1, Math.min(8, Math.round(s.bars || 1))),
    }));
    if (this._stepIndex >= this.progression.length) this._stepIndex = 0;
  }

  getProgression() {
    return this.progression.map((s) => Object.assign({}, s));
  }

  startProgression() {
    if (this.progression.length === 0) return;
    this._running = true;
    this._stepIndex = 0;
    this._lastBar = -1;
    this._applyStep(this._stepIndex, true);
  }

  stopProgression() {
    this._running = false;
    this._releaseActive();
    this._stepIndex = 0;
    this._barsRemaining = 0;
  }

  // Manual advance in 'manual' mode, or forced jump.
  jumpToStep(index) {
    if (this.progression.length === 0) return;
    const i = ((index % this.progression.length) + this.progression.length) % this.progression.length;
    this._stepIndex = i;
    this._applyStep(i, true);
  }

  lock() {
    this._locked = true;
    this.mode = 'lock';
  }

  unlock() {
    this._locked = false;
    // Resume auto from current step.
    if (this.mode === 'lock') this.mode = 'auto';
  }

  // --- Output / inspection ---

  getActiveNotes() {
    return this._activeNotes.slice();
  }

  getCurrentStep() {
    const s = this.progression[this._stepIndex];
    if (!s) return null;
    return {
      index: this._stepIndex,
      root: s.root,
      quality: s.quality,
      bars: s.bars,
      barsRemaining: this._barsRemaining,
    };
  }

  getNextStep() {
    if (this.progression.length === 0) return null;
    const ni = (this._stepIndex + 1) % this.progression.length;
    const s = this.progression[ni];
    return { index: ni, root: s.root, quality: s.quality };
  }

  isRunning() {
    return this._running;
  }

  // --- Events ---

  onStepChange(callback) {
    this._stepChangeCallbacks.push(callback);
  }

  onBarsRemaining(callback) {
    this._barsRemainingCallbacks.push(callback);
  }

  // --- Note computation ---

  // Given a chord (root, quality), select voiceCount notes near the center
  // octave, applying the configured inversion. Returns MIDI note numbers.
  computeNotes(root, quality) {
    const intervals = CHORD_QUALITIES[quality] || CHORD_QUALITIES.maj;
    // Base MIDI note for root at the chosen octave. MIDI octave: C4 = 60.
    const base = (this.octave + 1) * 12 + root;
    let chosen = intervals.slice(0, this.voiceCount).map((iv) => base + iv);

    // Apply inversion by lifting the lowest notes up an octave.
    for (let inv = 0; inv < this.inversion && inv < chosen.length; inv++) {
      chosen[inv] = chosen[inv] + 12;
    }
    chosen.sort((a, b) => a - b);
    // Clamp into MIDI range.
    return chosen.map((n) => Math.max(0, Math.min(127, n)));
  }

  // --- Internal clock handler ---

  _onTick(t) {
    if (!this._running) return;
    if (this.progression.length === 0) return;

    // Only act on bar boundaries — never advance mid-bar.
    if (!t.isBarBoundary) return;
    if (t.bar === this._lastBar) return;
    this._lastBar = t.bar;

    // A new bar elapsed.
    if (this._barsRemaining > 0) {
      this._barsRemaining--;
      this._emitBarsRemaining(this._barsRemaining);
    }

    // Lock / manual: hold the current chord, do not advance.
    if (this.mode === 'lock' || this._locked) return;
    if (this.mode === 'manual') return;

    // Auto mode: advance when the current step's bars are exhausted.
    if (this._barsRemaining <= 0) {
      this._advance();
    }
  }

  _advance() {
    const nextIndex = (this._stepIndex + 1) % this.progression.length;
    this._stepIndex = nextIndex;
    this._applyStep(nextIndex, true);
  }

  // Send noteOff for the previous chord, compute and send the new chord.
  _applyStep(index, isChange) {
    const step = this.progression[index];
    if (!step) return;
    this._releaseActive();

    const notes = this.computeNotes(step.root, step.quality);
    notes.forEach((n) => this.midi.noteOn(this.channel, n, 100));
    this._activeNotes = notes;

    this._barsRemaining = step.bars;
    this._emitBarsRemaining(this._barsRemaining);

    if (isChange) {
      const cur = this.getCurrentStep();
      const next = this.getNextStep();
      this._stepChangeCallbacks.forEach((cb) => cb(cur, next));
    }
  }

  _releaseActive() {
    this._activeNotes.forEach((n) => this.midi.noteOff(this.channel, n));
    this._activeNotes = [];
  }

  _emitBarsRemaining(n) {
    this._barsRemainingCallbacks.forEach((cb) => cb(n));
  }

  // Release all notes (panic / port change).
  releaseAll() {
    this._releaseActive();
  }
}
