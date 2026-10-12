// Ejecuta idiolect_g2p/web/app.js con un DOM mínimo simulado y reproduce la inferencia,
// las junturas y la escansión con texto hostil (HTML) en las respuestas del API. Imprime el HTML resultante en JSON.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scenario = process.argv[2];
const appPath = path.join(__dirname, '..', '..', 'idiolect_g2p', 'web', 'app.js');
const code = fs.readFileSync(appPath, 'utf-8');

function makeElement(id) {
  const listeners = {};
  const el = {
    id, textContent: '', innerHTML: '', value: '', hidden: false, checked: true,
    style: {}, dataset: {}, children: [],
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
    appendChild(c) { this.children.push(c); this.innerHTML += c.innerHTML || '<child/>'; return c; },
    setAttribute() {}, removeAttribute() {}, getAttribute: () => null,
    querySelector: () => null, querySelectorAll: () => [],
    animate: () => ({ finished: Promise.resolve(), cancel() {} }),
    fire(ev) { return Promise.all((listeners[ev] || []).map((fn) => fn({ preventDefault() {} }))); },
  };
  return el;
}

const elements = {};
const domListeners = [];
const document = {
  documentElement: makeElement('html'),
  getElementById(id) { return (elements[id] = elements[id] || makeElement(id)); },
  querySelectorAll: () => [],
  querySelector: () => null,
  createElement: (tag) => makeElement(tag),
  addEventListener(ev, fn) { if (ev === 'DOMContentLoaded') domListeners.push(fn); },
};

const XSS = '<img src=x onerror=alert(1)>';

const PERFIL = {
  predicted_dialect_name: 'Dialecto', predicted_dialect_code: 'X', confidence_score: 0.5,
  dialect_ranking: [{ name: XSS, region: 'R', posterior_probability: 0.5, phonetic_distance: 0.1 }],
  maxent_constraints: [{ name: XSS, description: XSS, is_markedness: true, weight: 1.5 }],
};
const TRANSCRIBE = {
  transcriptions: [{ syllabified_ipa: 'a' }], full_ipa_text: 'a',
  sandhi_junctures: [{
    process_type: 'x', description: XSS, input_left_coda: XSS, input_right_onset: XSS, output_phoneme: XSS,
  }],
};
const POEMA = {
  total_verses: 1, detected_stanza_type: 'x', global_rhyme_scheme: 'A',
  stanzas: [{ verses: [{
    verse_number: 1, raw_text: XSS, metrical_syllables: 8, sinalefas_count: 0,
    final_stress_compensation: 0, rhyme_segment: XSS,
  }] }],
};

async function fetchStub(url) {
  let data = TRANSCRIBE;
  if (url.includes('profile-idiolect')) data = PERFIL;
  if (url.includes('analyze-poem')) data = POEMA;
  return { ok: true, status: 200, json: async () => data };
}

const sandbox = {
  document, fetch: fetchStub, console: { log() {}, error() {} },
  localStorage: { getItem: () => null, setItem() {} },
  window: {}, setTimeout, clearTimeout, requestAnimationFrame: (f) => f(),
  Promise, JSON, Math, parseInt, parseFloat, Array, Number, String, Blob: function Blob() {},
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

(async () => {
  for (const fn of domListeners) fn();
  const g = (id) => document.getElementById(id);
  g('texto-manuscrito').value = 'Aquí\nallí';
  g('meter-poem-input').value = 'Un verso';
  await g('btn-ejecutar-inferencia').fire('click');
  await g('btn-run-scansion').fire('click');
  process.stdout.write(JSON.stringify({
    ranking: g('distribucion-lista').innerHTML,
    maxent: g('maxent-constraints-container').innerHTML,
    junturas: g('contenedor-junturas-badges').innerHTML,
    escansion: g('meter-table-body').innerHTML,
  }));
})();
