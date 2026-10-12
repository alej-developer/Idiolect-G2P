// Ejecuta idiolect_g2p/web/app.js con un DOM mínimo simulado y reproduce la consola AFI
// del perfilador y el transcriptor rápido bajo un escenario de red. Imprime el estado final en JSON.
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

const TRANSCRIBE = {
  transcriptions: [{ syllabified_ipa: 'a.ki' }], full_ipa_text: 'a.ki', sandhi_junctures: [],
};

async function fetchStub() {
  if (scenario.endsWith('network')) throw new TypeError('Failed to fetch');
  if (scenario.endsWith('http500')) return { ok: false, status: 500, json: async () => ({}) };
  return { ok: true, status: 200, json: async () => TRANSCRIBE };
}

const sandbox = {
  document, fetch: fetchStub, console: { log() {}, error() {} },
  localStorage: { getItem: () => null, setItem() {} },
  window: {}, setTimeout, clearTimeout, requestAnimationFrame: (f) => f(),
  Promise, JSON, Math, parseInt, parseFloat, Array, Number, Blob: function Blob() {},
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

(async () => {
  for (const fn of domListeners) fn();
  const g = (id) => document.getElementById(id);
  g('texto-manuscrito').value = 'Aquí\nallí';
  g('g2p-quick-input').value = 'Los cazadores';
  g('consola-afi').textContent = 'Resultado previo AFI';
  g('g2p-quick-output').textContent = 'Resultado previo G2P';
  await g('check-sandhi-bayesiano').fire('change');
  await g('btn-g2p-quick').fire('click');
  process.stdout.write(JSON.stringify({
    afi: g('consola-afi').textContent,
    g2p: g('g2p-quick-output').textContent,
    juntura_display: g('panel-junturas-sandhi').style.display || '',
  }));
})();
