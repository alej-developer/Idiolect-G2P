// Ejecuta idiolect_g2p/web/app.js con un DOM mínimo simulado y reproduce "Inferencia Inversa", la escansión y el audio del perfilador en secuencia: primero con éxito y
// luego con fallo del API. Imprime el estado final en JSON.
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
    setAttribute() {}, removeAttribute(n) { this.removidos = (this.removidos || []).concat(n); },
    pause() { this.pausado = true; }, load() { this.recargado = true; }, getAttribute: () => null,
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

let fallar = false;
const PERFIL = {
  predicted_dialect_name: 'Dialecto', predicted_dialect_code: 'X', confidence_score: 0.5,
  dialect_ranking: [{ name: 'Dialecto', region: 'R', posterior_probability: 0.5, phonetic_distance: 0.1 }],
  maxent_constraints: [],
};
const TRANSCRIBE = { transcriptions: [{ syllabified_ipa: 'a' }], full_ipa_text: 'a', sandhi_junctures: [] };
const POEMA = {
  total_verses: 1, detected_stanza_type: 'Soneto', global_rhyme_scheme: 'A',
  stanzas: [{ verses: [{
    verse_number: 1, raw_text: 'Un verso', metrical_syllables: 8, sinalefas_count: 0,
    final_stress_compensation: 0, rhyme_segment: 'o',
  }] }],
};

async function fetchStub(url) {
  if (fallar) {
    if (scenario === 'network') throw new TypeError('Failed to fetch');
    return { ok: false, status: 500, json: async () => ({}) };
  }
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
  // Primera pasada con éxito.
  await g('btn-ejecutar-inferencia').fire('click');
  await g('btn-run-scansion').fire('click');
  const exito = {
    insignia: g('meter-total-verses-badge').textContent,
    tabla: g('meter-table-body').innerHTML,
  };
  // Estado de audio del resultado anterior.
  const reproductor = g('audio-player-perfilador');
  reproductor.onpause = () => {};
  reproductor.ontimeupdate = () => {};
  g('audio-status-perfilador').textContent = 'Reproduciendo';
  g('manuscrito-sincronizado-perfilador').innerHTML = '<span>palabra</span>';
  g('manuscrito-sincronizado-perfilador').style.display = 'block';
  // Segunda pasada con fallo.
  fallar = true;
  await g('btn-ejecutar-inferencia').fire('click');
  await g('btn-run-scansion').fire('click');
  const afterAudio = {
    estado: g('audio-status-perfilador').textContent,
    karaoke: g('manuscrito-sincronizado-perfilador').innerHTML,
    karaoke_display: g('manuscrito-sincronizado-perfilador').style.display,
    reproductor_removidos: g('audio-player-perfilador').removidos || [],
    reproductor_pausado: g('audio-player-perfilador').pausado === true,
    manejadores_retirados: reproductor.onpause === null && reproductor.ontimeupdate === null,
  };
  // Fallo de la síntesis de audio.
  g('audio-status-perfilador').textContent = 'Sintetizando formantes...';
  await g('btn-reproducir-perfilador').fire('click');
  process.stdout.write(JSON.stringify({
    exito,
    insignia: g('meter-total-verses-badge').textContent,
    forma: g('meter-form-display').textContent,
    esquema: g('meter-scheme-display').textContent,
    tabla: g('meter-table-body').innerHTML,
    audio: afterAudio,
    estado_sintesis: g('audio-status-perfilador').textContent,
  }));
})();
