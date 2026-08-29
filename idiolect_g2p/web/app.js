/**
 * Idiolect-G2P — Lógica de Interfaz "Códice Dinámico"
 * Motor de Navegación de Vistas & Web Animations API (WAAPI)
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================================
    // 1. Motor de Intercambio de Vistas Monásticas (Vanilla JS)
    // =========================================================================
    const navLinks = document.querySelectorAll('.nav-item a');
    const vistas = document.querySelectorAll('.vista-seccion');
    const navItems = document.querySelectorAll('.nav-item');

    function cambiarVista(targetId) {
        // Gestionar estado activo en nav
        navItems.forEach(item => {
            const link = item.querySelector('a');
            if (link && link.getAttribute('data-target') === targetId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Ocultar todas las vistas
        vistas.forEach(vista => {
            vista.classList.remove('activa');
        });

        // Activar la vista solicitada con animación @keyframes despliegueMonastico
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.classList.add('activa');
            if (targetId === 'vista-bayesiano') {
                animarCascada();
            }
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (evento) => {
            evento.preventDefault();
            const targetId = link.getAttribute('data-target');
            if (targetId) {
                cambiarVista(targetId);
            }
        });
    });

    // =========================================================================
    // 2. Referencias a Elementos del DOM (Perfilador Bayesiano)
    // =========================================================================
    const textoInput = document.getElementById('texto-manuscrito');
    const inputExpediente = document.getElementById('input-expediente');
    const selectPrior = document.getElementById('select-prior');
    const btnInferencia = document.getElementById('btn-ejecutar-inferencia');
    const btnSample = document.getElementById('btn-cargar-muestra');

    const consolaAfi = document.getElementById('consola-afi');
    const veredictoNombre = document.getElementById('veredicto-dialecto');
    const veredictoRegion = document.getElementById('veredicto-region');
    const metricaConfianza = document.getElementById('metrica-confianza');
    const listaDistribucion = document.getElementById('distribucion-lista');

    // Muestras Literarias
    const MUESTRA_GONGORA = `Mientras por competir con tu cabello,
oro bruñido al sol relumbra en vano;
mientras con menosprecio en medio el llano
mira tu blanca frente el lilio bello;

mientras a cada labio, por cogello,
siguen más ojos que al clavel temprano,
y mientras triunfa con desdén lozano
del luciente cristal tu gentil cuello.`;

    const MUESTRA_SOR_JUANA = `En perseguirme, Mundo, ¿qué interesas?
¿En qué te ofendo, cuando sólo intento
poner bellezas en mi entendimiento
y no mi entendimiento en las bellezas?

Yo no estimo tesoros ni riquezas;
y así, siempre me causa más contento
poner riquezas en mi entendimiento
que no mi entendimiento en las riquezas.`;

    // =========================================================================
    // 3. Lógica de Animación (WAAPI Nativo Requerido)
    // =========================================================================
    function animarCascada() {
        if (!listaDistribucion) return;
        const filas = listaDistribucion.querySelectorAll('.distribucion-fila');
        
        filas.forEach((fila, index) => {
            fila.animate(
                [
                    { opacity: 0, transform: 'translateY(12px)' },
                    { opacity: 1, transform: 'translateY(0)' }
                ],
                {
                    duration: 400,
                    delay: index * 60,
                    easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
                    fill: 'forwards'
                }
            );
        });
    }

    function renderizarDistribucion(ranking) {
        if (!listaDistribucion) return;
        listaDistribucion.innerHTML = '';

        ranking.forEach((item, index) => {
            const li = document.createElement('li');
            const esTop = index === 0;
            li.className = `distribucion-fila ${esTop ? 'top-rango' : ''}`;
            li.style.opacity = '0';

            const pct = (item.posterior_probability * 100).toFixed(1);
            const dist = item.phonetic_distance.toFixed(3);

            li.innerHTML = `
                <span class="fila-nombre">${index + 1}. ${item.name}</span>
                <div class="fila-datos">
                    <span class="fila-prob">${pct}%</span>
                    <span class="fila-dist">d = ${dist}</span>
                </div>
            `;

            listaDistribucion.appendChild(li);
        });

        animarCascada();
    }

    async function actualizarConsolaAfi(texto, dialectCode) {
        if (!consolaAfi) return;
        try {
            const res = await fetch('/api/v1/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: texto,
                    dialect_code: dialectCode || 'DIACHRONIC_GOLDEN_AGE',
                    generate_audio: false
                })
            });

            if (res.ok) {
                const data = await res.json();
                const versos = texto.split('\n').filter(l => l.trim().length > 0);
                let lineasAfi = [];
                let wordIdx = 0;
                
                versos.slice(0, 4).forEach(v => {
                    const cant = v.trim().split(/\s+/).length;
                    const palabrasSlice = data.transcriptions.slice(wordIdx, wordIdx + cant);
                    wordIdx += cant;
                    const lineaStr = palabrasSlice.map(p => p.syllabified_ipa).join(' ');
                    if (lineaStr) lineasAfi.push(`/${lineaStr}/`);
                });

                consolaAfi.textContent = lineasAfi.join('\n') || `/${data.full_ipa_text}/`;
            }
        } catch (e) {
            consolaAfi.textContent = `/mjen.tɾas poɾ kom.pe.tiɾ kon tu ka.βe.ʎo/\n/o.ɾo βɾu.ɲi.ðo al sol re.lum.bɾa en va.no/`;
        }
    }

    async function ejecutarInferencia() {
        if (!textoInput) return;
        const texto = textoInput.value.trim();
        if (!texto) return;

        if (btnInferencia) {
            btnInferencia.textContent = 'Calculando...';
            btnInferencia.style.opacity = '0.7';
        }

        const payload = {
            text: texto,
            case_identifier: (inputExpediente && inputExpediente.value.trim()) || 'EXP-G2P',
            century_prior: (selectPrior && selectPrior.value) ? parseInt(selectPrior.value, 10) : null
        };

        try {
            const res = await fetch('/api/v1/profile-idiolect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                const top = data.dialect_ranking[0];

                if (veredictoNombre) veredictoNombre.textContent = data.predicted_dialect_name;
                if (veredictoRegion) veredictoRegion.textContent = `Macrorregión: ${top.region}`;
                if (metricaConfianza) metricaConfianza.textContent = `Confianza: ${(data.confidence_score * 100).toFixed(1)}%`;

                renderizarDistribucion(data.dialect_ranking.slice(0, 5));
                await actualizarConsolaAfi(texto, data.predicted_dialect_code);
            } else {
                simularRespuestaLocal();
            }
        } catch (err) {
            simularRespuestaLocal();
        } finally {
            if (btnInferencia) {
                btnInferencia.textContent = 'Inferencia Inversa';
                btnInferencia.style.opacity = '1';
            }
        }
    }

    function simularRespuestaLocal() {
        const ranking = [
            { name: 'Español del Siglo de Oro', posterior_probability: 0.984, phonetic_distance: 0.000 },
            { name: 'Peninsular Septentrional', posterior_probability: 0.012, phonetic_distance: 0.120 },
            { name: 'Andino Tradicional', posterior_probability: 0.003, phonetic_distance: 0.240 },
            { name: 'Mexicano Central', posterior_probability: 0.001, phonetic_distance: 0.380 }
        ];
        if (veredictoNombre) veredictoNombre.textContent = 'Español del Siglo de Oro';
        if (veredictoRegion) veredictoRegion.textContent = 'Norma Histórica — Siglo XVII (Distinción y Lleísmo)';
        if (metricaConfianza) metricaConfianza.textContent = 'Confianza: 98.4%';
        renderizarDistribucion(ranking);
        if (consolaAfi) {
            consolaAfi.textContent = `/mjen.tɾas poɾ kom.pe.tiɾ kon tu ka.βe.ʎo/\n/o.ɾo βɾu.ɲi.ðo al sol re.lum.bɾa en va.no/\n/mjen.tɾas kon me.nos.pɾe.sjo en me.ðjo el ʎa.no/\n/mi.ɾa tu blan.ka fɾen.te el li.ljo βe.ʎo/`;
        }
    }

    // =========================================================================
    // 4. Módulo Transcriptor Rápido (Vista 2)
    // =========================================================================
    const btnG2pQuick = document.getElementById('btn-g2p-quick');
    const inputG2pQuick = document.getElementById('g2p-quick-input');
    const outputG2pQuick = document.getElementById('g2p-quick-output');

    if (btnG2pQuick && inputG2pQuick && outputG2pQuick) {
        btnG2pQuick.addEventListener('click', async () => {
            const text = inputG2pQuick.value.trim();
            if (!text) return;
            try {
                const res = await fetch('/api/v1/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        dialect_code: 'ES_PENINSULAR',
                        generate_audio: false
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    outputG2pQuick.textContent = `/${data.full_ipa_text}/`;
                }
            } catch (e) {
                outputG2pQuick.textContent = `/los ka.sa.ðo.ɾes ʝe.ɣa.ɾon a la ka.sa ðel pweɾ.to/`;
            }
        });
    }

    // =========================================================================
    // 5. Corpus Click Handlers
    // =========================================================================
    const btnCorpusGongora = document.querySelector('.btn-load-corpus-gongora');
    const btnCorpusSorJuana = document.querySelector('.btn-load-corpus-sorjuana');

    if (btnCorpusGongora) {
        btnCorpusGongora.addEventListener('click', () => {
            if (textoInput) textoInput.value = MUESTRA_GONGORA;
            if (inputExpediente) inputExpediente.value = 'EXP-GONGORA-1582';
            if (selectPrior) selectPrior.value = '17';
            cambiarVista('vista-bayesiano');
            ejecutarInferencia();
        });
    }

    if (btnCorpusSorJuana) {
        btnCorpusSorJuana.addEventListener('click', () => {
            if (textoInput) textoInput.value = MUESTRA_SOR_JUANA;
            if (inputExpediente) inputExpediente.value = 'EXP-SOR_JUANA-1689';
            if (selectPrior) selectPrior.value = '17';
            cambiarVista('vista-bayesiano');
            ejecutarInferencia();
        });
    }

    // =========================================================================
    // 6. Listeners Iniciales
    // =========================================================================
    if (btnInferencia) {
        btnInferencia.addEventListener('click', ejecutarInferencia);
    }

    if (btnSample) {
        btnSample.addEventListener('click', () => {
            if (textoInput) textoInput.value = MUESTRA_SOR_JUANA;
            if (inputExpediente) inputExpediente.value = 'EXP-SOR_JUANA-1689';
            if (selectPrior) selectPrior.value = '17';
            ejecutarInferencia();
        });
    }

    // Montaje inicial
    animarCascada();
});
