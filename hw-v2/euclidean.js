// euclidean.js — Euclidean rhythm generator (Bjorklund) + probability gate.
// Each voice is an independent generator driven by the clock's step boundaries.

// Standard Bjorklund/Toussaint implementation.
// Returns bool[] of length `steps`, true = active step.
//   E(3,8)  = [1,0,0,1,0,0,1,0]
//   E(5,8)  = [1,0,1,1,0,1,1,0]
//   E(7,16) = [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0] ... (Toussaint distribution)
export function euclidean(pulses, steps) {
  steps = Math.max(1, Math.round(steps));
  pulses = Math.max(0, Math.min(Math.round(pulses), steps));
  if (pulses === 0) return new Array(steps).fill(false);
  if (pulses === steps) return new Array(steps).fill(true);

  // Bjorklund: start with `pulses` groups of [true] and `steps-pulses`
  // groups of [false], then repeatedly distribute remainders.
  let groups = [];
  for (let i = 0; i < pulses; i++) groups.push([true]);
  let remainders = [];
  for (let i = 0; i < steps - pulses; i++) remainders.push([false]);

  while (remainders.length > 1) {
    const count = Math.min(groups.length, remainders.length);
    const newGroups = [];
    for (let i = 0; i < count; i++) {
      newGroups.push(groups[i].concat(remainders[i]));
    }
    const newRemainders = [];
    if (groups.length > remainders.length) {
      for (let i = count; i < groups.length; i++) newRemainders.push(groups[i]);
    } else {
      for (let i = count; i < remainders.length; i++) newRemainders.push(remainders[i]);
    }
    groups = newGroups;
    remainders = newRemainders;
  }

  // Flatten groups then remainders.
  const out = [];
  groups.forEach((g) => g.forEach((v) => out.push(v)));
  remainders.forEach((g) => g.forEach((v) => out.push(v)));
  return out;
}

// Rotate a pattern by `offset` steps (positive = shift earlier in time).
function rotate(pattern, offset) {
  const n = pattern.length;
  if (n === 0) return pattern.slice();
  const o = ((offset % n) + n) % n;
  return pattern.slice(o).concat(pattern.slice(0, o));
}

const NOTE_LEN_STEPS = {
  '1/16': 1,
  '1/8': 2,
  '1/4': 4,
};

export class EuclideanEngine {
  constructor(clockEngine, midiEngine) {
    this.clock = clockEngine;
    this.midi = midiEngine;
    this.voices = new Map(); // id -> voice state
    this._stepCallbacks = new Map(); // id -> [callbacks]
    this._idCounter = 0;

    // Active note scheduling: track held notes per voice to send noteOff.
    // Each entry: { ch, note, offStep } scheduled by global step index.
    this._heldNotes = new Map(); // id -> { note, ch, offStep }

    this.clock.onTick((t) => this._onTick(t));
  }

  _genId() {
    this._idCounter++;
    return 'euc_' + this._idCounter;
  }

  addVoice(config = {}) {
    const id = config.id || this._genId();
    // Keep the counter ahead of any explicit id restored from saved state.
    const m = /^euc_(\d+)$/.exec(id);
    if (m) this._idCounter = Math.max(this._idCounter, parseInt(m[1], 10));
    const voice = Object.assign(
      {
        id,
        label: 'Voice',
        steps: 8,
        pulses: 3,
        offset: 0,
        mode: 'note',
        channel: 1,
        note: 36,
        velocity: 100,
        noteLength: '1/16',
        ccNumber: 80,
        ccHigh: 127,
        ccLow: 0,
        probability: 1.0,
        active: true,
      },
      config,
      { id }
    );
    voice.pulses = Math.min(voice.pulses, voice.steps);
    voice._pattern = rotate(euclidean(voice.pulses, voice.steps), voice.offset);
    voice._localStep = 0;
    this.voices.set(id, voice);
    if (!this._stepCallbacks.has(id)) this._stepCallbacks.set(id, []);
    return id;
  }

  removeVoice(id) {
    const v = this.voices.get(id);
    if (v && v.mode === 'note') this._releaseHeld(id);
    this.voices.delete(id);
    this._stepCallbacks.delete(id);
    this._heldNotes.delete(id);
  }

  updateVoice(id, partial) {
    const v = this.voices.get(id);
    if (!v) return;
    Object.assign(v, partial);
    if (v.pulses > v.steps) v.pulses = v.steps;
    if (v.offset >= v.steps) v.offset = ((v.offset % v.steps) + v.steps) % v.steps;
    // Recompute pattern when structural params change.
    if (
      'steps' in partial ||
      'pulses' in partial ||
      'offset' in partial
    ) {
      v._pattern = rotate(euclidean(v.pulses, v.steps), v.offset);
      if (v._localStep >= v.steps) v._localStep = 0;
    }
  }

  setActive(id, bool) {
    const v = this.voices.get(id);
    if (!v) return;
    v.active = !!bool;
    if (!bool) this._releaseHeld(id);
  }

  getPattern(id) {
    const v = this.voices.get(id);
    return v ? v._pattern.slice() : [];
  }

  onStep(id, callback) {
    if (!this._stepCallbacks.has(id)) this._stepCallbacks.set(id, []);
    this._stepCallbacks.get(id).push(callback);
  }

  getVoices() {
    return Array.from(this.voices.values()).map((v) => {
      const copy = Object.assign({}, v);
      delete copy._pattern;
      delete copy._localStep;
      return copy;
    });
  }

  // --- Clock-driven stepping ---

  _onTick(t) {
    if (!t.isStepBoundary) {
      // Still check for note-off scheduling on every step boundary only;
      // since we step on boundaries, releases are checked there too.
      return;
    }
    const globalStep = t.stepIndex;

    // First, release any held notes whose off-step has arrived.
    this._heldNotes.forEach((held, id) => {
      if (held && globalStep >= held.offStep) {
        this.midi.noteOff(held.ch, held.note);
        this._heldNotes.set(id, null);
      }
    });

    this.voices.forEach((v) => {
      const local = v._localStep % v.steps;
      const isActiveStep = v._pattern[local] === true;
      let fired = false;

      if (v.active && isActiveStep) {
        // Probability gate.
        const pass = v.probability >= 1.0 || Math.random() < v.probability;
        if (pass) {
          fired = true;
          this._fireVoice(v, globalStep);
        }
      }

      // CC low value on inactive/non-firing steps (for gate-style CC voices).
      if (v.active && v.mode === 'cc' && !fired) {
        this.midi.cc(v.channel, v.ccNumber, v.ccLow);
      }

      // Emit step event.
      const cbs = this._stepCallbacks.get(v.id);
      if (cbs && cbs.length) {
        cbs.forEach((cb) =>
          cb({ step: local, total: v.steps, fired, pattern: v._pattern })
        );
      }

      v._localStep = (v._localStep + 1) % v.steps;
    });
  }

  _fireVoice(v, globalStep) {
    if (v.mode === 'note') {
      // Release any currently held note on this voice first (mono behaviour).
      const prev = this._heldNotes.get(v.id);
      if (prev) this.midi.noteOff(prev.ch, prev.note);

      this.midi.noteOn(v.channel, v.note, v.velocity);
      if (v.noteLength === 'gate') {
        // Held until next hit — release scheduled far ahead; replaced on next fire.
        this._heldNotes.set(v.id, {
          ch: v.channel,
          note: v.note,
          offStep: globalStep + v.steps, // effectively "until next hit"
        });
      } else {
        const lenSteps = NOTE_LEN_STEPS[v.noteLength] || 1;
        this._heldNotes.set(v.id, {
          ch: v.channel,
          note: v.note,
          offStep: globalStep + lenSteps,
        });
      }
    } else if (v.mode === 'cc') {
      this.midi.cc(v.channel, v.ccNumber, v.ccHigh);
    }
  }

  _releaseHeld(id) {
    const held = this._heldNotes.get(id);
    if (held) {
      this.midi.noteOff(held.ch, held.note);
      this._heldNotes.set(id, null);
    }
  }

  // Release all held notes (used on stop / panic).
  releaseAll() {
    this._heldNotes.forEach((held) => {
      if (held) this.midi.noteOff(held.ch, held.note);
    });
    this._heldNotes.forEach((_, id) => this._heldNotes.set(id, null));
  }

  // Reset all voices' local step counters (used on transport start).
  resetSteps() {
    this.voices.forEach((v) => (v._localStep = 0));
  }
}
