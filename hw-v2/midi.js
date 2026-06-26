// midi.js — MIDI plumbing: port management, send helpers, activity flash.
// Web MIDI API only. No SysEx. No backend.

const NOTE_ON = 0x90;
const NOTE_OFF = 0x80;
const CONTROL_CHANGE = 0xb0;
const PROGRAM_CHANGE = 0xc0;

// Clamp a value into a valid MIDI 7-bit range.
function clamp7(v) {
  v = Math.round(v);
  if (v < 0) return 0;
  if (v > 127) return 127;
  return v;
}

// Channel is exposed to callers as 1-16; on the wire it is 0-15.
function chNibble(ch) {
  const c = Math.round(ch) - 1;
  if (c < 0) return 0;
  if (c > 15) return 15;
  return c;
}

export class MidiEngine {
  constructor() {
    this.access = null;
    this.output = null;
    this.input = null;
    this._stateCallbacks = [];
    this._messageCallbacks = [];
    this._activityCallbacks = [];
    this._available = false;
  }

  // Request access and populate ports. Returns true on success.
  async init() {
    if (!navigator.requestMIDIAccess) {
      this._available = false;
      const err = new Error('Web MIDI API not available in this browser.');
      err.code = 'NO_WEB_MIDI';
      throw err;
    }
    // sysex:false is a hard constraint of the project.
    this.access = await navigator.requestMIDIAccess({ sysex: false });
    this._available = true;
    this.access.onstatechange = (e) => {
      this._stateCallbacks.forEach((cb) => cb(e));
    };
    return true;
  }

  isAvailable() {
    return this._available;
  }

  onStateChange(callback) {
    this._stateCallbacks.push(callback);
  }

  // --- Port enumeration ---

  getOutputPorts() {
    if (!this.access) return [];
    const out = [];
    this.access.outputs.forEach((p) => out.push({ id: p.id, name: p.name }));
    return out;
  }

  getInputPorts() {
    if (!this.access) return [];
    const out = [];
    this.access.inputs.forEach((p) => out.push({ id: p.id, name: p.name }));
    return out;
  }

  setOutputPort(id) {
    if (!this.access) return;
    this.output = id ? this.access.outputs.get(id) || null : null;
  }

  setInputPort(id) {
    if (!this.access) return;
    // Detach previous input handler.
    if (this.input) this.input.onmidimessage = null;
    this.input = id ? this.access.inputs.get(id) || null : null;
    if (this.input) {
      this.input.onmidimessage = (msg) => {
        this._messageCallbacks.forEach((cb) => cb(msg.data, msg.timeStamp));
      };
    }
  }

  getOutputPortId() {
    return this.output ? this.output.id : null;
  }

  getInputPortId() {
    return this.input ? this.input.id : null;
  }

  // --- Raw input handler (for clock slave) ---
  onMidiMessage(callback) {
    this._messageCallbacks.push(callback);
  }

  // --- Activity flash registration ---
  onActivity(callback) {
    this._activityCallbacks.push(callback);
  }

  _flash(direction) {
    this._activityCallbacks.forEach((cb) => cb(direction));
  }

  // --- Send helpers ---

  send(bytes) {
    if (!this.output) return false;
    this.output.send(bytes);
    this._flash('out');
    return true;
  }

  noteOn(ch, note, vel) {
    this.send([NOTE_ON | chNibble(ch), clamp7(note), clamp7(vel)]);
  }

  noteOff(ch, note) {
    this.send([NOTE_OFF | chNibble(ch), clamp7(note), 0]);
  }

  cc(ch, number, value) {
    this.send([CONTROL_CHANGE | chNibble(ch), clamp7(number), clamp7(value)]);
  }

  pc(ch, program) {
    this.send([PROGRAM_CHANGE | chNibble(ch), clamp7(program)]);
  }

  // Realtime bytes: 0xF8 clock, 0xFA start, 0xFB continue, 0xFC stop.
  rt(byte) {
    this.send([byte]);
  }

  // Panic helpers — used on stop, mode switch, port change.
  allNotesOff() {
    for (let ch = 1; ch <= 16; ch++) this.cc(ch, 123, 0);
  }

  allSoundOff() {
    for (let ch = 1; ch <= 16; ch++) this.cc(ch, 120, 0);
  }
}
