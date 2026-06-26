// clock.js — clock engine: AudioContext lookahead scheduler + MIDI clock slave.
// Emits 24 ticks per quarter note (MIDI PPQ standard) in both modes.

const PPQ = 24; // MIDI pulses per quarter note.

// Subdivision -> ticks per step (relative to the 24-PPQ grid).
const SUBDIV_TICKS = {
  '1/4': 24,
  '1/8': 12,
  '1/16': 6,
  '1/32': 3,
  '1/8t': 8, // eighth triplet: 3 per quarter
  '1/16t': 4, // sixteenth triplet: 6 per quarter
};

export class ClockEngine {
  constructor(midiEngine) {
    this.midi = midiEngine;
    this.mode = 'internal';
    this.bpm = 120;
    this.beatsPerBar = 4;
    this.subdivision = '1/16';

    this._running = false;

    // Position state (zero-indexed).
    this._tick = 0; // absolute tick counter since start
    this._bar = 0;
    this._beat = 0;
    this._subdiv = 0;

    // Internal scheduler state (Chris Wilson lookahead pattern).
    this._audioCtx = null;
    this._lookahead = 25; // ms between scheduler runs
    this._scheduleAhead = 0.1; // seconds to schedule ahead
    this._nextTickTime = 0; // audio-context time of the next tick
    this._timerId = null;

    // Tap tempo.
    this._tapTimes = [];

    // Slave-mode timing.
    this._slaveTickTimes = [];
    this._slaveBPM = 120;

    // Callbacks.
    this._tickCallbacks = [];
    this._bpmCallbacks = [];

    // Bind slave handler so we can reference identity (not strictly needed but tidy).
    this._onSlaveMessage = this._onSlaveMessage.bind(this);
    if (this.midi) this.midi.onMidiMessage(this._onSlaveMessage);
  }

  // --- Configuration ---

  setMode(mode) {
    if (mode !== 'internal' && mode !== 'slave') return;
    if (mode === this.mode) return;
    const wasRunning = this._running;
    // Switch cleanly without forcing a full stop of musical state.
    if (this.mode === 'internal') this._stopInternalScheduler();
    this.mode = mode;
    // In slave mode, the incoming 0xF8 stream drives ticks. In internal mode,
    // restart the scheduler if we were running.
    if (mode === 'internal' && wasRunning) {
      this._startInternalScheduler();
    }
  }

  setBPM(bpm) {
    bpm = Math.max(40, Math.min(200, bpm));
    this.bpm = bpm;
  }

  setBeatsPerBar(n) {
    this.beatsPerBar = Math.max(1, Math.round(n));
  }

  setSubdivision(sub) {
    if (SUBDIV_TICKS[sub] != null) this.subdivision = sub;
  }

  tapTempo() {
    const now = (this._audioCtx ? this._audioCtx.currentTime : performance.now() / 1000) * 1000;
    this._tapTimes.push(now);
    // Keep only the last 4 taps.
    if (this._tapTimes.length > 4) this._tapTimes.shift();
    if (this._tapTimes.length >= 2) {
      let sum = 0;
      for (let i = 1; i < this._tapTimes.length; i++) {
        sum += this._tapTimes[i] - this._tapTimes[i - 1];
      }
      const avgMs = sum / (this._tapTimes.length - 1);
      if (avgMs > 0) {
        const bpm = 60000 / avgMs;
        this.setBPM(bpm);
        this._emitBPM(this.bpm);
      }
    }
    // If gap since last tap is large, reset the averaging window next time.
    return this.bpm;
  }

  // --- Transport ---

  start() {
    if (this._running) return;
    this._running = true;
    this._tick = 0;
    this._bar = 0;
    this._beat = 0;
    this._subdiv = 0;

    if (this.mode === 'internal') {
      this._ensureAudioCtx();
      this._nextTickTime = this._audioCtx.currentTime + 0.05;
      this._startInternalScheduler();
    } else {
      // Slave mode: reset slave timing; ticks arrive from MIDI input.
      this._slaveTickTimes = [];
    }
  }

  stop() {
    if (!this._running) return;
    this._running = false;
    this._stopInternalScheduler();
  }

  isRunning() {
    return this._running;
  }

  // --- Callbacks ---

  onTick(callback) {
    this._tickCallbacks.push(callback);
  }

  onBPMChange(callback) {
    this._bpmCallbacks.push(callback);
  }

  getCurrentBPM() {
    return this.mode === 'slave' ? this._slaveBPM : this.bpm;
  }

  getPosition() {
    return { bar: this._bar, beat: this._beat, subdiv: this._subdiv };
  }

  // --- Internal scheduler (AudioContext lookahead) ---

  _ensureAudioCtx() {
    if (!this._audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      this._audioCtx = new Ctx();
    }
    if (this._audioCtx.state === 'suspended') {
      this._audioCtx.resume();
    }
  }

  _secondsPerTick() {
    // 24 ticks per quarter note.
    return 60 / this.bpm / PPQ;
  }

  _startInternalScheduler() {
    if (this._timerId != null) return;
    const scheduler = () => {
      const ctx = this._audioCtx;
      while (this._nextTickTime < ctx.currentTime + this._scheduleAhead) {
        this._scheduleTick(this._nextTickTime);
        this._nextTickTime += this._secondsPerTick();
      }
      this._timerId = setTimeout(scheduler, this._lookahead);
    };
    scheduler();
  }

  _stopInternalScheduler() {
    if (this._timerId != null) {
      clearTimeout(this._timerId);
      this._timerId = null;
    }
  }

  // Schedule a tick to fire at a precise audio-context time. We use a
  // setTimeout aligned to the audio clock for the callback dispatch, which is
  // the standard Wilson approach: scheduling precision comes from computing
  // times against the audio clock, not from setTimeout itself.
  _scheduleTick(time) {
    const tickIndex = this._tick;
    const delayMs = Math.max(0, (time - this._audioCtx.currentTime) * 1000);
    setTimeout(() => {
      if (this.mode === 'internal' && this._running) {
        this._advanceAndEmit(tickIndex);
      }
    }, delayMs);
    this._tick++;
  }

  // --- Slave mode (MIDI clock input) ---

  _onSlaveMessage(data) {
    if (this.mode !== 'slave') return;
    const status = data[0];
    if (status === 0xfa) {
      // Start
      this._running = true;
      this._tick = 0;
      this._bar = 0;
      this._beat = 0;
      this._subdiv = 0;
      this._slaveTickTimes = [];
      return;
    }
    if (status === 0xfc) {
      // Stop
      this._running = false;
      return;
    }
    if (status === 0xfb) {
      // Continue
      this._running = true;
      return;
    }
    if (status === 0xf8) {
      // Clock tick.
      if (!this._running) this._running = true;
      this._deriveSlaveBPM();
      this._advanceAndEmit(this._tick);
      this._tick++;
    }
  }

  // Derive BPM from inter-tick timing averaged over 8 ticks, with hysteresis.
  _deriveSlaveBPM() {
    const now = performance.now();
    this._slaveTickTimes.push(now);
    if (this._slaveTickTimes.length > 9) this._slaveTickTimes.shift();
    if (this._slaveTickTimes.length >= 2) {
      const n = this._slaveTickTimes.length;
      const span = this._slaveTickTimes[n - 1] - this._slaveTickTimes[0];
      const intervals = n - 1;
      const msPerTick = span / intervals;
      if (msPerTick > 0) {
        // 24 ticks per quarter; quarter = msPerTick * 24.
        const msPerBeat = msPerTick * PPQ;
        const bpm = 60000 / msPerBeat;
        // Hysteresis: only update display BPM if it moved by > 2.
        if (Math.abs(bpm - this._slaveBPM) > 2) {
          this._slaveBPM = Math.round(bpm);
          this._emitBPM(this._slaveBPM);
        }
      }
    }
  }

  // --- Shared tick advance + emission ---

  _advanceAndEmit(tickIndex) {
    // Compute musical position from the absolute tick count.
    // bar/beat/subdiv are zero-indexed.
    const ticksPerBeat = PPQ;
    const beat = Math.floor(tickIndex / ticksPerBeat) % this.beatsPerBar;
    const bar = Math.floor(tickIndex / (ticksPerBeat * this.beatsPerBar));
    const stepTicks = SUBDIV_TICKS[this.subdivision] || 6;
    const subdiv = Math.floor(tickIndex / stepTicks);

    this._bar = bar;
    this._beat = beat;
    this._subdiv = subdiv;

    const payload = {
      tick: tickIndex,
      bar,
      beat,
      subdiv,
      bpm: this.getCurrentBPM(),
      // True only on the exact tick that begins a subdivision step — lets
      // consumers (Euclidean) advance once per musical step rather than per PPQ tick.
      isStepBoundary: tickIndex % stepTicks === 0,
      isBeatBoundary: tickIndex % ticksPerBeat === 0,
      isBarBoundary: tickIndex % (ticksPerBeat * this.beatsPerBar) === 0,
      stepIndex: Math.floor(tickIndex / stepTicks),
    };
    this._tickCallbacks.forEach((cb) => cb(payload));
  }

  _emitBPM(bpm) {
    this._bpmCallbacks.forEach((cb) => cb(bpm));
  }
}
