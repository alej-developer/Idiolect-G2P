// Ejecuta idiolect_g2p/web/app.js con un DOM mínimo simulado y reproduce
// "Inferencia Inversa" bajo un escenario de red. Imprime el estado final en JSON.
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
    appendChild(c) { this.children.push(c); this.innerHTML += '<child/>'; return c; },
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

const GOOD = {
  predicted_dialect_name: 'Mexicano Central', predicted_dialect_code: 'MX_CENTRAL',
  confidence_score: 0.5,
  dialect_ranking: [{ name: 'Mexicano Central', region: 'Mesoamérica', posterior_probability: 0.5, phonetic_distance: 0.1 }],
  maxent_constraints: [],
};
const TRANSCRIBE = { transcriptions: [{ syllabified_ipa: 'a' }] };

const calls = [];
async function fetchStub(url) {
  calls.push(url);
  if (url.includes('profile-idiolect')) {
    if (scenario === 'network') throw new TypeError('Failed to fetch');
    if (scenario === 'http500') return { ok: false, status: 500, json: async () => ({}) };
    if (scenario === 'badjson') return { ok: true, status: 200, json: async () => { throw new SyntaxError('Unexpected token'); } };
    if (scenario === 'emptyranking') return { ok: true, status: 200, json: async () => ({ dialect_ranking: [] }) };
    return { ok: true, status: 200, json: async () => GOOD };
  }
  return { ok: true, status: 200, json: async () => TRANSCRIBE };
}

const sandbox = {
  document, fetch: fetchStub, console: { log() {}, error() {} },
  localStorage: { getItem: () => null, setItem() {} },
  window: {}, setTimeout, clearTimeout, requestAnimationFrame: (f) => f(),
  Promise, JSON, Math, parseInt, Array, Number,
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

(async () => {
  for (const fn of domListeners) fn();
  document.getElementById('texto-manuscrito').value = 'Una mariposa\nUna luminosa';
  // Estado previo que un error no debe dejar visible como resultado vigente.
  document.getElementById('veredicto-dialecto').textContent = 'Resultado previo';
  document.getElementById('metrica-confianza').textContent = 'Confianza: 77.0%';
  await document.getElementById('btn-ejecutar-inferencia').fire('click');
  const g = (id) => document.getElementById(id);
  process.stdout.write(JSON.stringify({
    nombre: g('veredicto-dialecto').textContent,
    region: g('veredicto-region').textContent,
    confianza: g('metrica-confianza').textContent,
    error_texto: g('inferencia-error').textContent,
    error_oculto: g('inferencia-error').hidden,
    boton: g('btn-ejecutar-inferencia').textContent,
    lista: g('distribucion-lista').innerHTML,
    afi: g('consola-afi').textContent,
  }));
})();
