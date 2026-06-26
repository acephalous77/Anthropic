// ui.js — wires all modules to the DOM. Owns no musical logic.

import { MidiEngine } from './midi.js';
import { ClockEngine } from './clock.js';
import { EuclideanEngine } from './euclidean.js';
import { LFOEngine } from './lfo.js';
import {
  HarmonyEngine,
  CHORD_QUALITIES,
  NOTE_NAMES,
  chordName,
  midiNoteName,
} from './harmony.js';

// Module evaluated successfully → ES modules loaded. This clears the file://
// fallback notice. Set synchronously at top level, independent of async MIDI
// init (which may hang waiting on a permission prompt).
window.__hwBooted = true;

const STATE_KEY = 'hw_v2_state';
const STATE_VERSION = 2;

// ---- Engine instances ----
const midi = new MidiEngine();
const clock = new ClockEngine(midi);
const euclid = new EuclideanEngine(clock, midi);
const lfo = new LFOEngine(clock, midi);
const harmony = new HarmonyEngine(clock, midi);

const $ = (id) => document.getElementById(id);

// =====================================================================
//  PERSISTENCE
// =====================================================================

let saveTimer = null;
function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(saveState, 500);
}

function saveState() {
  const state = {
    version: STATE_VERSION,
    clock: {
      bpm: clock.bpm,
      subdivision: clock.subdivision,
      mode: clock.mode,
    },
    midi: {
      outputPortId: midi.getOutputPortId(),
      clockInputPortId: midi.getClockInputPortId(),
      keyboardInputPortId: midi.getKeyboardInputPortId(),
    },
    euclidean: { voices: euclid.getVoices() },
    lfo: { lfos: lfo.getLFOs() },
    harmony: {
      channel: harmony.channel,
      voiceCount: harmony.voiceCount,
      octave: harmony.octave,
      inversion: harmony.inversion,
      mode: harmony.mode,
      followChannel: harmony.followChannel,
      progression: harmony.getProgression(),
      runningStepIndex: harmony._stepIndex,
    },
  };
  try {
    localStorage.setItem(STATE_KEY, JSON.stringify(state));
  } catch (e) {
    /* storage full / unavailable — ignore silently */
  }
}

function loadState() {
  let raw;
  try {
    raw = localStorage.getItem(STATE_KEY);
  } catch (e) {
    return null;
  }
  if (!raw) return null;
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return null;
  }
  // Version mismatch → discard stale state, start fresh.
  if (!parsed || parsed.version !== STATE_VERSION) {
    try { localStorage.removeItem(STATE_KEY); } catch (e) {}
    return null;
  }
  return parsed;
}

// =====================================================================
//  MIDI + STATUS
// =====================================================================

const statusDot = $('statusDot');
const statusText = $('statusText');
let activityTimer = null;

function setStatus(kind, text) {
  statusDot.classList.remove('ok', 'err', 'act');
  if (kind) statusDot.classList.add(kind);
  if (text != null) statusText.textContent = text;
}

midi.onActivity(() => {
  statusDot.classList.add('act');
  if (activityTimer) clearTimeout(activityTimer);
  activityTimer = setTimeout(() => statusDot.classList.remove('act'), 80);
});

function fillPortSelect(sel, ports, currentId) {
  sel.innerHTML = '<option value="">— none —</option>';
  ports.forEach((p) => {
    const o = document.createElement('option');
    o.value = p.id; o.textContent = p.name;
    if (p.id === currentId) o.selected = true;
    sel.appendChild(o);
  });
}

function populatePorts() {
  const outs = midi.getOutputPorts();
  const ins = midi.getInputPorts();
  fillPortSelect($('outPort'), outs, midi.getOutputPortId());
  fillPortSelect($('clockInPort'), ins, midi.getClockInputPortId());
  fillPortSelect($('keysInPort'), ins, midi.getKeyboardInputPortId());
}

async function initMidi() {
  try {
    await midi.init();
    setStatus('ok', 'MIDI ready');
    populatePorts();
    midi.onStateChange(() => {
      populatePorts();
    });
  } catch (e) {
    setStatus('err', 'No Web MIDI');
    $('supportBanner').classList.add('show');
  }
}

// =====================================================================
//  TRANSPORT / CLOCK WIRING
// =====================================================================

function wireTransport() {
  $('outPort').addEventListener('change', (e) => {
    // Release notes before swapping ports to avoid orphans.
    panic();
    midi.setOutputPort(e.target.value);
    scheduleSave();
  });
  $('clockInPort').addEventListener('change', (e) => {
    midi.setClockInputPort(e.target.value);
    scheduleSave();
  });
  $('keysInPort').addEventListener('change', (e) => {
    midi.setKeyboardInputPort(e.target.value);
    scheduleSave();
  });

  const bpmInput = $('bpm');
  bpmInput.addEventListener('change', () => {
    clock.setBPM(parseFloat(bpmInput.value) || 120);
    bpmInput.value = clock.bpm;
    scheduleSave();
  });

  $('tap').addEventListener('click', () => {
    const bpm = clock.tapTempo();
    bpmInput.value = Math.round(bpm);
    scheduleSave();
  });

  $('subdivision').addEventListener('change', (e) => {
    clock.setSubdivision(e.target.value);
    scheduleSave();
  });

  $('clockMode').querySelectorAll('button').forEach((btn) => {
    btn.addEventListener('click', () => {
      $('clockMode').querySelectorAll('button').forEach((b) => b.classList.remove('on'));
      btn.classList.add('on');
      const mode = btn.dataset.mode;
      // Releasing notes before a clock-mode switch avoids orphaned noteOns.
      panic();
      clock.setMode(mode);
      bpmInput.disabled = mode === 'slave';
      $('tap').disabled = mode === 'slave';
      scheduleSave();
    });
  });

  $('start').addEventListener('click', () => {
    euclid.resetSteps();
    clock.start();
    if (clock.mode === 'internal') midi.rt(0xfa); // send MIDI start downstream
  });

  $('stop').addEventListener('click', stopAll);
  $('panic').addEventListener('click', panic);

  // Reflect slave-derived BPM in the input.
  clock.onBPMChange((bpm) => {
    if (clock.mode === 'slave') bpmInput.value = Math.round(bpm);
  });
}

function stopAll() {
  clock.stop();
  if (clock.mode === 'internal') midi.rt(0xfc);
  euclid.releaseAll();
  harmony.stopProgression();
  midi.allNotesOff();
}

function panic() {
  euclid.releaseAll();
  harmony.releaseAll();
  midi.allNotesOff();
  midi.allSoundOff();
}

// Flush all notes if the page is closed/reloaded mid-playback so the 707/VT-4
// are never left with hanging notes.
window.addEventListener('beforeunload', () => {
  euclid.releaseAll();
  harmony.releaseAll();
  midi.allNotesOff();
});

// =====================================================================
//  EUCLIDEAN UI
// =====================================================================

const voiceGrid = $('voiceGrid');
const MAX_VOICES = 8;
const voiceEls = new Map(); // id -> { el, canvas, currentStep }

function defaultVoiceConfig(n) {
  return {
    label: 'Voice ' + n,
    steps: 8, pulses: 3, offset: 0,
    mode: 'note', channel: 1, note: 36, velocity: 100,
    noteLength: '1/16', ccNumber: 80, ccHigh: 127, ccLow: 0,
    probability: 1.0, active: true,
  };
}

function addVoiceUI(config) {
  if (euclid.voices.size >= MAX_VOICES) return null;
  const id = euclid.addVoice(config || defaultVoiceConfig(euclid.voices.size + 1));
  const v = euclid.voices.get(id);

  const el = document.createElement('div');
  el.className = 'voice open';
  el.dataset.id = id;
  el.innerHTML = `
    <div class="voice-top">
      <canvas width="120" height="120" style="width:60px;height:60px"></canvas>
      <div class="vmeta">
        <div class="vlabel"></div>
        <div class="vinfo"></div>
      </div>
      <button class="amber-btn vtoggle" title="active">●</button>
      <button class="vremove" title="remove">✕</button>
    </div>
    <div class="voice-body">
      <div class="field full">
        <label>Label</label>
        <input type="text" class="f-label" />
      </div>
      <div class="field">
        <label>Steps <span class="val f-steps-v"></span></label>
        <input type="range" class="f-steps" min="8" max="32" />
      </div>
      <div class="field">
        <label>Pulses <span class="val f-pulses-v"></span></label>
        <input type="range" class="f-pulses" min="1" max="32" />
      </div>
      <div class="field">
        <label>Offset <span class="val f-offset-v"></span></label>
        <input type="range" class="f-offset" min="0" max="31" />
      </div>
      <div class="field">
        <label>Probability <span class="val f-prob-v"></span></label>
        <input type="range" class="f-prob" min="0" max="100" />
      </div>
      <div class="field">
        <label>Mode</label>
        <select class="f-mode">
          <option value="note">note</option>
          <option value="cc">cc</option>
        </select>
      </div>
      <div class="field">
        <label>Channel</label>
        <select class="f-channel"></select>
      </div>
      <div class="field note-only">
        <label>Note <span class="val f-note-v"></span></label>
        <input type="range" class="f-note" min="0" max="127" />
      </div>
      <div class="field note-only">
        <label>Velocity <span class="val f-vel-v"></span></label>
        <input type="range" class="f-vel" min="1" max="127" />
      </div>
      <div class="field note-only">
        <label>Note length</label>
        <select class="f-notelen">
          <option value="1/16">1/16</option>
          <option value="1/8">1/8</option>
          <option value="1/4">1/4</option>
          <option value="gate">gate</option>
        </select>
      </div>
      <div class="field cc-only">
        <label>CC number <span class="val f-cc-v"></span></label>
        <input type="range" class="f-cc" min="0" max="127" />
      </div>
      <div class="field cc-only">
        <label>CC high <span class="val f-cchigh-v"></span></label>
        <input type="range" class="f-cchigh" min="0" max="127" />
      </div>
      <div class="field cc-only">
        <label>CC low <span class="val f-cclow-v"></span></label>
        <input type="range" class="f-cclow" min="0" max="127" />
      </div>
    </div>
  `;
  voiceGrid.appendChild(el);

  // Channel options.
  const chSel = el.querySelector('.f-channel');
  for (let c = 1; c <= 16; c++) {
    const o = document.createElement('option');
    o.value = c; o.textContent = c; chSel.appendChild(o);
  }

  const canvas = el.querySelector('canvas');
  const rec = { el, canvas, currentStep: -1, firedStep: -1 };
  voiceEls.set(id, rec);

  // --- bind fields to engine ---
  const set = (partial) => { euclid.updateVoice(id, partial); refreshVoiceMeta(id); drawRing(id); scheduleSave(); };

  el.querySelector('.f-label').value = v.label;
  el.querySelector('.f-label').addEventListener('input', (e) => set({ label: e.target.value }));

  const stepsR = el.querySelector('.f-steps');
  const pulsesR = el.querySelector('.f-pulses');
  const offsetR = el.querySelector('.f-offset');
  stepsR.value = v.steps; pulsesR.value = v.pulses; offsetR.value = v.offset;

  const syncStepLimits = () => {
    const steps = parseInt(stepsR.value, 10);
    pulsesR.max = steps;
    offsetR.max = steps - 1;
    if (parseInt(pulsesR.value, 10) > steps) pulsesR.value = steps;
    if (parseInt(offsetR.value, 10) > steps - 1) offsetR.value = steps - 1;
  };
  syncStepLimits();

  stepsR.addEventListener('input', () => { syncStepLimits(); set({ steps: +stepsR.value, pulses: +pulsesR.value, offset: +offsetR.value }); });
  pulsesR.addEventListener('input', () => set({ pulses: +pulsesR.value }));
  offsetR.addEventListener('input', () => set({ offset: +offsetR.value }));

  const probR = el.querySelector('.f-prob');
  probR.value = Math.round(v.probability * 100);
  probR.addEventListener('input', () => set({ probability: (+probR.value) / 100 }));

  const modeSel = el.querySelector('.f-mode');
  modeSel.value = v.mode;
  const applyModeVisibility = () => {
    const isNote = modeSel.value === 'note';
    el.querySelectorAll('.note-only').forEach((n) => n.style.display = isNote ? '' : 'none');
    el.querySelectorAll('.cc-only').forEach((n) => n.style.display = isNote ? 'none' : '');
  };
  modeSel.addEventListener('change', () => { set({ mode: modeSel.value }); applyModeVisibility(); });

  chSel.value = v.channel;
  chSel.addEventListener('change', () => set({ channel: +chSel.value }));

  const noteR = el.querySelector('.f-note'); noteR.value = v.note;
  noteR.addEventListener('input', () => set({ note: +noteR.value }));
  const velR = el.querySelector('.f-vel'); velR.value = v.velocity;
  velR.addEventListener('input', () => set({ velocity: +velR.value }));
  const noteLenSel = el.querySelector('.f-notelen'); noteLenSel.value = v.noteLength;
  noteLenSel.addEventListener('change', () => set({ noteLength: noteLenSel.value }));

  const ccR = el.querySelector('.f-cc'); ccR.value = v.ccNumber;
  ccR.addEventListener('input', () => set({ ccNumber: +ccR.value }));
  const cchighR = el.querySelector('.f-cchigh'); cchighR.value = v.ccHigh;
  cchighR.addEventListener('input', () => set({ ccHigh: +cchighR.value }));
  const cclowR = el.querySelector('.f-cclow'); cclowR.value = v.ccLow;
  cclowR.addEventListener('input', () => set({ ccLow: +cclowR.value }));

  el.querySelector('.vtoggle').addEventListener('click', (e) => {
    e.stopPropagation();
    const newState = !euclid.voices.get(id).active;
    euclid.setActive(id, newState);
    el.classList.toggle('inactive', !newState);
    scheduleSave();
  });

  el.querySelector('.vremove').addEventListener('click', (e) => {
    e.stopPropagation();
    euclid.removeVoice(id);
    el.remove();
    voiceEls.delete(id);
    updateAddVoiceBtn();
    scheduleSave();
  });

  el.querySelector('.voice-top').addEventListener('click', () => el.classList.toggle('open'));

  // step event → visual feedback
  euclid.onStep(id, (info) => {
    const r = voiceEls.get(id);
    if (!r) return;
    r.currentStep = info.step;
    if (info.fired) r.firedStep = info.step;
    drawRing(id);
  });

  applyModeVisibility();
  el.classList.toggle('inactive', !v.active);
  refreshVoiceMeta(id);
  drawRing(id);
  updateAddVoiceBtn();
  return id;
}

function refreshVoiceMeta(id) {
  const rec = voiceEls.get(id);
  const v = euclid.voices.get(id);
  if (!rec || !v) return;
  const el = rec.el;
  el.querySelector('.vlabel').textContent = v.label;
  const tgt = v.mode === 'note' ? `note ${midiNoteName(v.note)}` : `CC ${v.ccNumber}`;
  el.querySelector('.vinfo').textContent = `E(${v.pulses},${v.steps}) · ch${v.channel} · ${tgt}`;
  // value labels
  const setv = (cls, val) => { const n = el.querySelector(cls); if (n) n.textContent = val; };
  setv('.f-steps-v', v.steps);
  setv('.f-pulses-v', v.pulses);
  setv('.f-offset-v', v.offset);
  setv('.f-prob-v', Math.round(v.probability * 100) + '%');
  setv('.f-note-v', midiNoteName(v.note));
  setv('.f-vel-v', v.velocity);
  setv('.f-cc-v', v.ccNumber);
  setv('.f-cchigh-v', v.ccHigh);
  setv('.f-cclow-v', v.ccLow);
}

function drawRing(id) {
  const rec = voiceEls.get(id);
  const v = euclid.voices.get(id);
  if (!rec || !v) return;
  const ctx = rec.canvas.getContext('2d');
  const W = rec.canvas.width, H = rec.canvas.height;
  ctx.clearRect(0, 0, W, H);
  const cx = W / 2, cy = H / 2, R = W / 2 - 16;
  const pattern = v._pattern;
  const n = pattern.length;
  const amber = '#e0a44a';
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2 - Math.PI / 2;
    const x = cx + Math.cos(ang) * R;
    const y = cy + Math.sin(ang) * R;
    const active = pattern[i];
    let r = active ? 7 : 4;
    let fill = active ? amber : '#352d40';
    if (i === rec.currentStep) {
      fill = '#7ee081';
      r = active ? 9 : 6;
    }
    if (i === rec.firedStep && i === rec.currentStep) {
      fill = '#ffffff';
    }
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    if (active && i !== rec.currentStep) {
      ctx.strokeStyle = amber;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }
  // decay fired highlight
  if (rec.firedStep !== -1 && rec.firedStep !== rec.currentStep) rec.firedStep = -1;
}

function updateAddVoiceBtn() {
  $('addVoice').disabled = euclid.voices.size >= MAX_VOICES;
}

// =====================================================================
//  LFO UI
// =====================================================================

const lfoGrid = $('lfoGrid');
const MAX_LFOS = 4;
const lfoEls = new Map();
const LFO_SHAPES = ['sine', 'triangle', 'sawtooth', 'ramp', 'square', 'random', 's&h'];
const LFO_RATES = ['4/1', '2/1', '1/1', '1/2', '1/4', '1/8', '1/16', '1/4t', '1/8t'];

function defaultLfoConfig(n) {
  return {
    label: 'LFO ' + n, shape: 'sine', rate: '1/4',
    depth: 64, center: 64, channel: 1, ccNumber: 80, phase: 0, active: true,
  };
}

function addLfoUI(config) {
  if (lfo.lfos.size >= MAX_LFOS) return null;
  const id = lfo.addLFO(config || defaultLfoConfig(lfo.lfos.size + 1));
  const l = lfo.lfos.get(id);

  const el = document.createElement('div');
  el.className = 'lfo';
  el.dataset.id = id;
  el.innerHTML = `
    <div class="lfo-head">
      <span class="llabel"></span>
      <span class="spacer" style="flex:1"></span>
      <button class="teal-btn ltoggle" title="active">●</button>
      <button class="lremove" title="remove">✕</button>
    </div>
    <canvas width="360" height="80"></canvas>
    <div class="lfo-body">
      <div class="field full">
        <label>Label</label>
        <input type="text" class="lf-label" />
      </div>
      <div class="field">
        <label>Shape</label>
        <select class="lf-shape"></select>
      </div>
      <div class="field">
        <label>Rate</label>
        <select class="lf-rate"></select>
      </div>
      <div class="field">
        <label>Depth <span class="val lf-depth-v"></span></label>
        <input type="range" class="lf-depth" min="0" max="127" />
      </div>
      <div class="field">
        <label>Center <span class="val lf-center-v"></span></label>
        <input type="range" class="lf-center" min="0" max="127" />
      </div>
      <div class="field">
        <label>Channel</label>
        <select class="lf-channel"></select>
      </div>
      <div class="field">
        <label>CC <span class="val lf-cc-v"></span></label>
        <input type="range" class="lf-cc" min="0" max="127" />
      </div>
    </div>
  `;
  lfoGrid.appendChild(el);

  const shapeSel = el.querySelector('.lf-shape');
  LFO_SHAPES.forEach((s) => { const o = document.createElement('option'); o.value = s; o.textContent = s; shapeSel.appendChild(o); });
  const rateSel = el.querySelector('.lf-rate');
  LFO_RATES.forEach((r) => { const o = document.createElement('option'); o.value = r; o.textContent = r; rateSel.appendChild(o); });
  const chSel = el.querySelector('.lf-channel');
  for (let c = 1; c <= 16; c++) { const o = document.createElement('option'); o.value = c; o.textContent = c; chSel.appendChild(o); }

  const canvas = el.querySelector('canvas');
  lfoEls.set(id, { el, canvas });

  const set = (partial) => { lfo.updateLFO(id, partial); refreshLfoMeta(id); scheduleSave(); };

  el.querySelector('.lf-label').value = l.label;
  el.querySelector('.lf-label').addEventListener('input', (e) => set({ label: e.target.value }));
  shapeSel.value = l.shape; shapeSel.addEventListener('change', () => set({ shape: shapeSel.value }));
  rateSel.value = l.rate; rateSel.addEventListener('change', () => set({ rate: rateSel.value }));
  const depthR = el.querySelector('.lf-depth'); depthR.value = l.depth;
  depthR.addEventListener('input', () => set({ depth: +depthR.value }));
  const centerR = el.querySelector('.lf-center'); centerR.value = l.center;
  centerR.addEventListener('input', () => set({ center: +centerR.value }));
  chSel.value = l.channel; chSel.addEventListener('change', () => set({ channel: +chSel.value }));
  const ccR = el.querySelector('.lf-cc'); ccR.value = l.ccNumber;
  ccR.addEventListener('input', () => set({ ccNumber: +ccR.value }));

  el.querySelector('.ltoggle').addEventListener('click', () => {
    const ns = !lfo.lfos.get(id).active;
    lfo.setActive(id, ns);
    el.classList.toggle('inactive', !ns);
    scheduleSave();
  });
  el.querySelector('.lremove').addEventListener('click', () => {
    lfo.removeLFO(id); el.remove(); lfoEls.delete(id); updateAddLfoBtn(); scheduleSave();
  });

  el.classList.toggle('inactive', !l.active);
  refreshLfoMeta(id);
  updateAddLfoBtn();
  return id;
}

function refreshLfoMeta(id) {
  const rec = lfoEls.get(id);
  const l = lfo.lfos.get(id);
  if (!rec || !l) return;
  rec.el.querySelector('.llabel').textContent = l.label;
  const setv = (cls, val) => { const n = rec.el.querySelector(cls); if (n) n.textContent = val; };
  setv('.lf-depth-v', l.depth);
  setv('.lf-center-v', l.center);
  setv('.lf-cc-v', l.ccNumber);
}

function drawLfoWave(id) {
  const rec = lfoEls.get(id);
  const l = lfo.lfos.get(id);
  if (!rec || !l) return;
  const ctx = rec.canvas.getContext('2d');
  const W = rec.canvas.width, H = rec.canvas.height;
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = '#4ec5c1';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let x = 0; x <= W; x++) {
    const pos = x / W;
    const v = LFOEngine.previewShape(l.shape, pos);
    const y = H - v * (H - 6) - 3;
    if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Position cursor based on current live value mapped back to 0..1.
  if (clock.isRunning() && l.active) {
    const cur = lfo.getCurrentValue(id);
    // Map cursor X by phase position derived from the clock tick.
    const pos = lfoCursorPos(l);
    const cx = pos * W;
    ctx.strokeStyle = 'rgba(126,224,129,0.9)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx, 0); ctx.lineTo(cx, H);
    ctx.stroke();
    // Live value label
    ctx.fillStyle = '#8a8194';
    ctx.font = '10px IBM Plex Mono, monospace';
    ctx.fillText(String(cur), 4, 12);
  }
}

function lfoCursorPos(l) {
  // Recompute normalized cycle position from the clock for cursor display.
  const RATE_QUARTERS = { '4/1':16,'2/1':8,'1/1':4,'1/2':2,'1/4':1,'1/8':0.5,'1/16':0.25,'1/4t':2/3,'1/8t':1/3 };
  const q = RATE_QUARTERS[l.rate] || 1;
  const ticksPerCycle = q * 24;
  const pos = clock._tick % ticksPerCycle / ticksPerCycle;
  return ((pos + l.phase) % 1 + 1) % 1;
}

function updateAddLfoBtn() {
  $('addLfo').disabled = lfo.lfos.size >= MAX_LFOS;
}

// =====================================================================
//  HARMONY UI
// =====================================================================

function wireHarmony() {
  const chSel = $('harmCh');
  for (let c = 1; c <= 16; c++) { const o = document.createElement('option'); o.value = c; o.textContent = c; chSel.appendChild(o); }
  chSel.value = harmony.channel;
  chSel.addEventListener('change', () => { harmony.setChannel(+chSel.value); scheduleSave(); });

  $('harmVoices').addEventListener('change', (e) => { harmony.setVoiceCount(+e.target.value); refreshHarmonyDisplay(); scheduleSave(); });
  $('harmOct').addEventListener('change', (e) => { harmony.setOctave(+e.target.value); refreshHarmonyDisplay(); scheduleSave(); });
  $('harmInv').addEventListener('change', (e) => { harmony.setInversion(+e.target.value); refreshHarmonyDisplay(); scheduleSave(); });

  // Keys CH selector: 0 = any (omni), 1-16 specific.
  const keysChSel = $('harmKeysCh');
  const anyOpt = document.createElement('option');
  anyOpt.value = '0'; anyOpt.textContent = 'any'; keysChSel.appendChild(anyOpt);
  for (let c = 1; c <= 16; c++) { const o = document.createElement('option'); o.value = c; o.textContent = c; keysChSel.appendChild(o); }
  keysChSel.value = harmony.followChannel;
  keysChSel.addEventListener('change', () => { harmony.setFollowChannel(+keysChSel.value); scheduleSave(); });

  $('harmMode').querySelectorAll('button').forEach((btn) => {
    btn.addEventListener('click', () => {
      applyHarmonyMode(btn.dataset.mode);
      scheduleSave();
    });
  });
  $('harmNext').style.visibility = 'hidden';
  $('harmNext').addEventListener('click', () => {
    harmony.jumpToStep(harmony._stepIndex + 1);
  });

  harmony.onFollowChordChange((c) => refreshFollowDisplay(c));

  $('progStart').addEventListener('click', () => { harmony.startProgression(); scheduleSave(); });
  $('progStop').addEventListener('click', () => { harmony.stopProgression(); refreshHarmonyDisplay(); scheduleSave(); });
  $('progReset').addEventListener('click', () => { harmony.jumpToStep(0); scheduleSave(); });

  harmony.onStepChange(() => refreshHarmonyDisplay());
  harmony.onBarsRemaining(() => refreshBarDots());

  buildProgressionGrid();
  wireStepModal();
  refreshHarmonyDisplay();
}

function buildProgressionGrid() {
  const grid = $('progGrid');
  grid.innerHTML = '';
  const prog = harmony.getProgression();
  for (let i = 0; i < 8; i++) {
    const step = prog[i];
    const cell = document.createElement('div');
    cell.className = 'prog-step' + (step ? '' : ' empty');
    cell.dataset.index = i;
    cell.innerHTML = `
      <span class="num">${i + 1}</span>
      <span class="chord">${step ? chordName(step.root, step.quality) : '–'}</span>
      <span class="bars">${step ? step.bars + 'b' : ''}</span>
    `;
    cell.addEventListener('click', () => openStepModal(i));
    grid.appendChild(cell);
  }
  highlightCurrentStep();
}

function highlightCurrentStep() {
  const cells = $('progGrid').querySelectorAll('.prog-step');
  const cur = harmony.getCurrentStep();
  const next = harmony.getNextStep();
  cells.forEach((c) => c.classList.remove('current', 'next'));
  if (harmony.isRunning() && cur) {
    const cc = cells[cur.index]; if (cc) cc.classList.add('current');
    if (next) { const nc = cells[next.index]; if (nc) nc.classList.add('next'); }
  }
}

function refreshHarmonyDisplay() {
  const cur = harmony.getCurrentStep();
  const next = harmony.getNextStep();
  if (cur && harmony.progression.length) {
    $('nowChord').textContent = chordName(cur.root, cur.quality);
    const notes = harmony.getActiveNotes();
    $('nowNotes').textContent = notes.length ? notes.map(midiNoteName).join(' · ') : harmony.computeNotes(cur.root, cur.quality).map(midiNoteName).join(' · ');
  } else {
    $('nowChord').textContent = '—';
    $('nowNotes').textContent = '';
  }
  $('nextChord').textContent = next ? chordName(next.root, next.quality) : '—';
  refreshBarDots();
  highlightCurrentStep();
}

function refreshBarDots() {
  const box = $('barDots');
  // Clear all but the remaining label.
  box.querySelectorAll('.bar-dot').forEach((d) => d.remove());
  const cur = harmony.getCurrentStep();
  const label = $('barRemaining');
  if (!cur || !harmony.isRunning()) { label.textContent = ''; return; }
  const total = cur.bars;
  const remaining = harmony._barsRemaining;
  const frag = document.createDocumentFragment();
  for (let i = 0; i < total; i++) {
    const d = document.createElement('span');
    d.className = 'bar-dot' + (i < remaining ? ' filled' : '');
    frag.appendChild(d);
  }
  box.insertBefore(frag, label);
  label.textContent = `${remaining} bar${remaining === 1 ? '' : 's'} remaining`;
}

// Apply a harmony mode: update engine, button states, and panel visibility.
function applyHarmonyMode(mode) {
  $('harmMode').querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.mode === mode));
  harmony.setMode(mode);

  const isFollow = mode === 'follow';
  $('followBox').style.display = isFollow ? '' : 'none';
  $('keysChGrp').style.display = isFollow ? '' : 'none';
  // Hide progression UI in follow mode (progression is paused, not shown).
  const nowBox = document.querySelector('.now-box');
  const progControls = document.querySelector('.prog-controls');
  const progGrid = $('progGrid');
  [nowBox, progControls, progGrid].forEach((el) => { if (el) el.style.display = isFollow ? 'none' : ''; });
  $('harmNext').style.visibility = mode === 'manual' ? 'visible' : 'hidden';

  if (isFollow) refreshFollowDisplay();
  else refreshHarmonyDisplay();
}

function refreshFollowDisplay() {
  const st = harmony.getFollowState();
  if (!st) return;
  $('followHeld').textContent = st.pitchClasses.length
    ? st.pitchClasses.map((p) => NOTE_NAMES[p]).join(' · ')
    : '—';
  const det = st.detectedChord;
  const chordEl = $('followChord');
  const dot = $('followConf');
  if (det) {
    chordEl.textContent = chordName(det.root, det.quality);
    // Confidence: dim = uncertain, bright = clear (no percentage shown).
    const bright = 0.35 + 0.65 * det.confidence;
    chordEl.style.opacity = String(bright);
    dot.style.opacity = String(bright);
  } else {
    chordEl.textContent = '—';
    chordEl.style.opacity = '0.5';
    dot.style.opacity = '0.25';
  }
  const notes = harmony.getActiveNotes();
  $('followOut').textContent = notes.length ? notes.map(midiNoteName).join(' · ') : '—';
  $('followResumeHint').textContent =
    '⟳ back to AUTO resumes progression from step ' + (harmony._stepIndex + 1);
}

// ---- Step editor modal ----
let editingStepIndex = -1;
function wireStepModal() {
  const rootSel = $('stepRoot');
  NOTE_NAMES.forEach((n, i) => { const o = document.createElement('option'); o.value = i; o.textContent = n; rootSel.appendChild(o); });
  const qualSel = $('stepQuality');
  Object.keys(CHORD_QUALITIES).forEach((q) => { const o = document.createElement('option'); o.value = q; o.textContent = q; qualSel.appendChild(o); });

  $('stepCancel').addEventListener('click', closeStepModal);
  $('stepSave').addEventListener('click', () => {
    const prog = harmony._editPaddedProg || harmony.getProgression();
    const newStep = { root: +$('stepRoot').value, quality: $('stepQuality').value, bars: Math.max(1, Math.min(8, +$('stepBars').value || 1)) };
    prog[editingStepIndex] = newStep;
    harmony.setProgression(compactProgression(prog));
    buildProgressionGrid();
    refreshHarmonyDisplay();
    scheduleSave();
    closeStepModal();
  });
  $('stepClear').addEventListener('click', () => {
    const prog = harmony._editPaddedProg || harmony.getProgression();
    prog[editingStepIndex] = null;
    harmony.setProgression(compactProgression(prog));
    buildProgressionGrid();
    refreshHarmonyDisplay();
    scheduleSave();
    closeStepModal();
  });
  $('stepModal').addEventListener('click', (e) => { if (e.target === $('stepModal')) closeStepModal(); });
}

// Remove null holes but preserve order; trailing nulls dropped.
function compactProgression(prog) {
  return prog.filter((s) => s != null);
}

function openStepModal(index) {
  editingStepIndex = index;
  const prog = harmony.getProgression();
  // Ensure array is long enough so we can edit an empty slot.
  while (prog.length <= index) prog.push(null);
  const step = prog[index];
  $('stepModalNum').textContent = index + 1;
  $('stepRoot').value = step ? step.root : 0;
  $('stepQuality').value = step ? step.quality : 'maj';
  $('stepBars').value = step ? step.bars : 2;
  // stash padded prog so save uses the right index even for empty tail slots
  harmony._editPaddedProg = prog;
  $('stepModal').classList.add('open');
}

function closeStepModal() {
  $('stepModal').classList.remove('open');
  editingStepIndex = -1;
  harmony._editPaddedProg = null;
}

// =====================================================================
//  ANIMATION LOOP (canvas redraws)
// =====================================================================

function animate() {
  voiceEls.forEach((_, id) => drawRing(id));
  lfoEls.forEach((_, id) => drawLfoWave(id));
  // Keep the follow readout live as keys are pressed/released.
  if (harmony.mode === 'follow') refreshFollowDisplay();
  requestAnimationFrame(animate);
}

// =====================================================================
//  BOOT
// =====================================================================

async function boot() {
  const state = loadState();

  wireTransport();
  wireHarmony();

  if (state) {
    // Clock
    clock.setBPM(state.clock.bpm);
    clock.setSubdivision(state.clock.subdivision);
    clock.setMode(state.clock.mode);
    $('bpm').value = state.clock.bpm;
    $('subdivision').value = state.clock.subdivision;
    $('clockMode').querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.mode === state.clock.mode));

    // Harmony config
    harmony.setChannel(state.harmony.channel);
    harmony.setVoiceCount(state.harmony.voiceCount);
    harmony.setOctave(state.harmony.octave);
    if (state.harmony.inversion != null) harmony.setInversion(state.harmony.inversion);
    if (state.harmony.followChannel != null) harmony.setFollowChannel(state.harmony.followChannel);
    harmony.setProgression(state.harmony.progression || []);
    $('harmCh').value = state.harmony.channel;
    $('harmVoices').value = state.harmony.voiceCount;
    $('harmOct').value = state.harmony.octave;
    $('harmInv').value = state.harmony.inversion || 0;
    $('harmKeysCh').value = state.harmony.followChannel || 0;
    buildProgressionGrid();
    applyHarmonyMode(state.harmony.mode || 'auto');

    // Euclidean voices
    (state.euclidean.voices || []).forEach((vc) => addVoiceUI(vc));

    // LFOs
    (state.lfo.lfos || []).forEach((lc) => addLfoUI(lc));
  } else {
    // Seed a default progression and one of each, so the UI isn't empty.
    harmony.setProgression([
      { root: 0, quality: 'min', bars: 2 },
      { root: 5, quality: 'min', bars: 2 },
      { root: 10, quality: 'maj', bars: 2 },
      { root: 3, quality: 'maj', bars: 2 },
    ]);
    buildProgressionGrid();
    refreshHarmonyDisplay();
    addVoiceUI();
    addLfoUI();
  }

  $('addVoice').addEventListener('click', () => addVoiceUI());
  $('addLfo').addEventListener('click', () => addLfoUI());

  await initMidi();

  // Restore selected ports after enumeration; auto-detect anything not saved.
  if (midi.isAvailable()) {
    const guess = midi.detectDefaultPorts();
    const sm = (state && state.midi) || {};
    const outId = sm.outputPortId || guess.out;
    const clkId = sm.clockInputPortId || guess.clockIn;
    const keysId = sm.keyboardInputPortId || guess.keysIn;
    if (outId) { midi.setOutputPort(outId); $('outPort').value = outId; }
    if (clkId) { midi.setClockInputPort(clkId); $('clockInPort').value = clkId; }
    if (keysId) { midi.setKeyboardInputPort(keysId); $('keysInPort').value = keysId; }
  }

  // Slave-mode disables BPM input.
  if (clock.mode === 'slave') { $('bpm').disabled = true; $('tap').disabled = true; }

  requestAnimationFrame(animate);
}

boot();
