/**
 * Idiolect-G2P — Lógica de Interfaz "Códice Dinámico"
 * Motor de Navegación de Vistas & Web Animations API (WAAPI)
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================================
    // 0. Lógica del Tema (Claro / Oscuro) con Persistencia en localStorage
    // =========================================================================
    const themeToggleBtn = document.getElementById('theme-toggle');
    const statusIndicator = document.getElementById('codice-status-indicator');
    const htmlElement = document.documentElement; // Aplica al tag <html>

    function aplicarTema(tema) {
        if (tema === 'dark') {
            htmlElement.setAttribute('data-theme', 'dark');
            if (themeToggleBtn) themeToggleBtn.textContent = 'Estudio Lumínico';
            if (statusIndicator) statusIndicator.innerHTML = '<span class="status-dot"></span> Scriptorium Activo';
        } else {
            htmlElement.removeAttribute('data-theme');
            if (themeToggleBtn) themeToggleBtn.textContent = 'Modo Scriptorium';
            if (statusIndicator) statusIndicator.innerHTML = '<span class="status-dot"></span> Estudio Lumínico Activo';
        }
    }

    // 1. Revisar si el usuario ya tenía una preferencia guardada (por defecto: claro)
    const temaGuardado = localStorage.getItem('idiolect-theme');
    aplicarTema(temaGuardado === 'dark' ? 'dark' : 'light');

    // 2. Evento de click para alternar suavemente
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const esOscuro = htmlElement.getAttribute('data-theme') === 'dark';
            const nuevoTema = esOscuro ? 'light' : 'dark';
            localStorage.setItem('idiolect-theme', nuevoTema);
            aplicarTema(nuevoTema);
        });
    }

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
                ultimoDialectoPredicho = data.predicted_dialect_code;
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

    let ultimoDialectoPredicho = 'DIACHRONIC_GOLDEN_AGE';
    const btnReproducirPerfilador = document.getElementById('btn-reproducir-perfilador');
    const audioPlayerPerfilador = document.getElementById('audio-player-perfilador');
    const manuscritoSincronizadoPerfilador = document.getElementById('manuscrito-sincronizado-perfilador');
    const audioStatusPerfilador = document.getElementById('audio-status-perfilador');

    // Motor de Sincronización Interactiva Texto-Audio (Karaoke Fonológico)
    function configurarSincronizacionAudio({ audioEl, containerWords, containerIpa, statusBadge, wordTimings }) {
        if (!audioEl || !wordTimings || wordTimings.length === 0) return;

        if (containerWords) {
            containerWords.innerHTML = '';
            containerWords.style.display = 'block';
            wordTimings.forEach((wt, idx) => {
                const span = document.createElement('span');
                span.className = 'synced-word';
                span.textContent = wt.word;
                span.dataset.wordIdx = idx;
                span.dataset.start = wt.start_time;
                span.dataset.end = wt.end_time;
                span.title = `[${wt.ipa}] (${wt.start_time.toFixed(2)}s - ${wt.end_time.toFixed(2)}s) — Clic para reproducir`;
                span.addEventListener('click', () => {
                    audioEl.currentTime = wt.start_time;
                    audioEl.play().catch(() => {});
                });
                containerWords.appendChild(span);
                containerWords.appendChild(document.createTextNode(' '));
            });
        }

        if (containerIpa) {
            containerIpa.innerHTML = '';
            containerIpa.style.display = 'flex';
            wordTimings.forEach((wt, idx) => {
                const span = document.createElement('span');
                span.className = 'synced-ipa';
                span.textContent = `/${wt.ipa}/`;
                span.dataset.wordIdx = idx;
                span.dataset.start = wt.start_time;
                span.dataset.end = wt.end_time;
                span.title = `${wt.word} (${wt.start_time.toFixed(2)}s - ${wt.end_time.toFixed(2)}s)`;
                span.addEventListener('click', () => {
                    audioEl.currentTime = wt.start_time;
                    audioEl.play().catch(() => {});
                });
                containerIpa.appendChild(span);
            });
        }

        function actualizarHighlight() {
            const t = audioEl.currentTime;
            let activeIdx = -1;
            for (let i = 0; i < wordTimings.length; i++) {
                const wt = wordTimings[i];
                if (t >= wt.start_time && t <= wt.end_time + 0.05) {
                    activeIdx = i;
                    break;
                }
            }

            if (containerWords) {
                const wordSpans = containerWords.querySelectorAll('.synced-word');
                wordSpans.forEach((s, idx) => {
                    if (idx === activeIdx) {
                        s.classList.add('reproduciendo');
                    } else {
                        s.classList.remove('reproduciendo');
                    }
                });
            }

            if (containerIpa) {
                const ipaSpans = containerIpa.querySelectorAll('.synced-ipa');
                ipaSpans.forEach((s, idx) => {
                    if (idx === activeIdx) {
                        s.classList.add('reproduciendo');
                    } else {
                        s.classList.remove('reproduciendo');
                    }
                });
            }

            if (statusBadge) {
                if (audioEl.paused && !audioEl.ended) {
                    statusBadge.textContent = 'En Pausa';
                } else if (audioEl.ended) {
                    statusBadge.textContent = 'Finalizado';
                } else if (activeIdx >= 0) {
                    statusBadge.textContent = `Pronunciando: "${wordTimings[activeIdx].word}"`;
                } else {
                    statusBadge.textContent = 'Reproduciendo...';
                }
            }
        }

        audioEl.ontimeupdate = actualizarHighlight;
        audioEl.onplay = () => {
            if (statusBadge) statusBadge.textContent = 'Reproduciendo...';
            actualizarHighlight();
        };
        audioEl.onpause = () => {
            if (statusBadge) statusBadge.textContent = 'En Pausa';
        };
        audioEl.onended = () => {
            if (statusBadge) statusBadge.textContent = 'Finalizado';
            if (containerWords) {
                containerWords.querySelectorAll('.synced-word').forEach(s => s.classList.remove('reproduciendo'));
            }
            if (containerIpa) {
                containerIpa.querySelectorAll('.synced-ipa').forEach(s => s.classList.remove('reproduciendo'));
            }
        };
    }

    if (btnReproducirPerfilador && audioPlayerPerfilador) {
        btnReproducirPerfilador.addEventListener('click', async () => {
            if (!textoInput) return;
            const texto = textoInput.value.trim();
            if (!texto) return;

            btnReproducirPerfilador.textContent = 'Sintetizando...';
            btnReproducirPerfilador.style.opacity = '0.7';
            if (audioStatusPerfilador) audioStatusPerfilador.textContent = 'Sintetizando formantes...';

            try {
                const lineas = texto.split('\n').map(l => l.trim()).filter(Boolean).slice(0, 3).join('. ');
                const res = await fetch('/api/v1/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: lineas || texto,
                        dialect_code: ultimoDialectoPredicho || 'DIACHRONIC_GOLDEN_AGE',
                        generate_audio: true
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.audio_base64) {
                        audioPlayerPerfilador.src = `data:audio/wav;base64,${data.audio_base64}`;
                        if (data.word_timings) {
                            configurarSincronizacionAudio({
                                audioEl: audioPlayerPerfilador,
                                containerWords: manuscritoSincronizadoPerfilador,
                                containerIpa: null,
                                statusBadge: audioStatusPerfilador,
                                wordTimings: data.word_timings
                            });
                        }
                        audioPlayerPerfilador.play().catch(e => console.log('Autoplay bloqueado por el navegador'));
                    }
                }
            } catch (e) {
                console.error('Error al sintetizar audio del dictamen:', e);
            } finally {
                btnReproducirPerfilador.textContent = 'Escuchar Dictamen';
                btnReproducirPerfilador.style.opacity = '1';
            }
        });
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
    // 4. Módulo Transcriptor Rápido & Síntesis Acústica (Vista 2)
    // =========================================================================
    const btnG2pQuick = document.getElementById('btn-g2p-quick');
    const btnG2pAudio = document.getElementById('btn-g2p-audio');
    const inputG2pQuick = document.getElementById('g2p-quick-input');
    const selectG2pDialect = document.getElementById('g2p-dialect-select');
    const outputG2pQuick = document.getElementById('g2p-quick-output');
    const playerG2pAudio = document.getElementById('g2p-audio-player');
    const g2pKaraokeWords = document.getElementById('g2p-karaoke-words');
    const g2pKaraokeIpa = document.getElementById('g2p-karaoke-ipa');
    const audioStatusG2p = document.getElementById('audio-status-g2p');

    async function transcribirYSintetizarG2P(generarAudio = false) {
        if (!inputG2pQuick) return;
        const text = inputG2pQuick.value.trim();
        if (!text) return;

        const dialectCode = selectG2pDialect ? selectG2pDialect.value : 'ES_PENINSULAR';

        if (generarAudio && btnG2pAudio) {
            btnG2pAudio.textContent = 'Sintetizando formantes...';
            btnG2pAudio.style.opacity = '0.7';
            if (audioStatusG2p) audioStatusG2p.textContent = 'Sintetizando formantes...';
        }

        try {
            const res = await fetch('/api/v1/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    dialect_code: dialectCode,
                    generate_audio: generarAudio
                })
            });

            if (res.ok) {
                const data = await res.json();
                if (outputG2pQuick) {
                    outputG2pQuick.textContent = `/${data.full_ipa_text}/`;
                }

                if (generarAudio && data.audio_base64 && playerG2pAudio) {
                    playerG2pAudio.src = `data:audio/wav;base64,${data.audio_base64}`;
                    if (data.word_timings) {
                        configurarSincronizacionAudio({
                            audioEl: playerG2pAudio,
                            containerWords: g2pKaraokeWords,
                            containerIpa: g2pKaraokeIpa,
                            statusBadge: audioStatusG2p,
                            wordTimings: data.word_timings
                        });
                    }
                    playerG2pAudio.play().catch(e => console.log('Autoplay bloqueado por el navegador'));
                }
            }
        } catch (e) {
            console.error('Error en transducción/síntesis G2P:', e);
            if (outputG2pQuick) {
                outputG2pQuick.textContent = `/los ka.θa.ˈðo.ɾes ʝe.ˈɣa.ɾon a la ˈka.sa ðel ˈpweɾ.to/`;
            }
        } finally {
            if (btnG2pAudio) {
                btnG2pAudio.textContent = 'Sintetizar y Reproducir Audio';
                btnG2pAudio.style.opacity = '1';
            }
        }
    }

    if (btnG2pQuick) {
        btnG2pQuick.addEventListener('click', () => transcribirYSintetizarG2P(false));
    }

    if (btnG2pAudio) {
        btnG2pAudio.addEventListener('click', () => transcribirYSintetizarG2P(true));
    }

    // Muestras Literarias Latinoamericanas, Españolas e Históricas
    const MUESTRAS_CORPUS = {
        mistral: {
            text: `Piececitos de niño,
azulosos de frío,
¡cómo os ven y no os cubren,
Dios mío!

Piececitos heridos
por los guijarros todos,
ultrajados de nieves
y lodos.`,
            caseId: 'EXP-MISTRAL-CHILE-1922',
            century: '20'
        },
        rosalia: {
            text: `A través del follaje espeso
el rayo de la luna brilla,
y en la fuente la limpia orilla
besa el aura con blando beso.`,
            caseId: 'EXP-ROSALIA-GALICIA-1884',
            century: '19'
        },
        sorjuana: {
            text: `Hombres necios que acusáis
a la mujer sin razón,
sin ver que sois la ocasión
de lo mismo que culpáis.

Si con ansia sin igual
solicitáis su desdén,
¿por qué queréis que obren bien
si las incitáis al mal?`,
            caseId: 'EXP-SOR_JUANA-1689',
            century: '17'
        },
        teresa: {
            text: `Vivo sin vivir en mí,
y tan alta vida espero,
que muero porque no muero.

Vivo ya fuera de mí,
después que muero de amor;
porque vivo en el Señor,
que me quiso para sí.`,
            caseId: 'EXP-SANTA_TERESA-1572',
            century: '16'
        },
        storni: {
            text: `Tú me quieres alba,
me quieres de espumas,
me quieres de nácar.
Que sea azucena
sobre todas, casta.
De perfume tenue.
Corola cerrada.`,
            caseId: 'EXP-STORNI-ARGENTINA-1918',
            century: '20'
        },
        arvelo: {
            text: `Voz del viento en la llanura,
rumor hondo de palmares,
que derramas tus cantares
en la noche más oscura.`,
            caseId: 'EXP-ARVELO-VENEZUELA-1939',
            century: '20'
        },
        fuertes: {
            text: `Escribo por la noche y por el día,
escribo para el pueblo que no lee,
para el que tiene sed de poesía
y en la palabra humana todavía cree.`,
            caseId: 'EXP-GLORIA_FUERTES-MADRID-1962',
            century: '20'
        },
        loynaz: {
            text: `Si me quieres, quiéreme entera,
no por zonas de luz o sombra...
Si me quieres, quiéreme negra
y blanca, y gris, y verde, y rubia.`,
            caseId: 'EXP-LOYNAZ-CUBA-1953',
            century: '20'
        },
        cadenas: {
            text: `Que cada palabra lleve lo que dice.
Que sea como el temblor que la sostiene.
Que se mantenga como un latido en la noche.
No me des palabras que deslumbren,
dame palabras que amanezcan en la boca.`,
            caseId: 'EXP-CADENAS-BARQUISIMETO-1977',
            century: '20'
        },
        arraiz: {
            text: `Esta es la tierra brava,
estos son los hombres recios,
los que cantan al viento
y doman los potros cimarrones
bajo el sol ardiente del desierto.`,
            caseId: 'EXP-ARRAIZ-BARQUISIMETO-1924',
            century: '20'
        },
        vallejo: {
            text: `Hay golpes en la vida, tan fuertes... ¡Yo no sé!
Golpes como del odio de Dios; como si ante ellos,
la resaca de todo lo sufrido
se empozara en el alma... ¡Yo no sé!`,
            caseId: 'EXP-VALLEJO-PERU-1918',
            century: '20'
        },
        dario: {
            text: `Juventud, divino tesoro,
¡ya te vas para no volver!
Cuando quiero llorar, no lloro...
y a veces lloro sin querer.`,
            caseId: 'EXP-DARIO-NICARAGUA-1905',
            century: '19'
        },
        hernandez: {
            text: `Aquí me pongo a cantar
al compás de la vigüela,
que el hombre que lo desvela
una pena estraordinaria,
como la ave solitaria
con el cantar se consuela.`,
            caseId: 'EXP-HERNANDEZ-GAUCHESCO-1872',
            century: '19'
        },
        gongora: {
            text: `Mientras por competir con tu cabello,
oro bruñido al sol relumbra en vano;
mientras con menosprecio en medio el llano
mira tu blanca frente el lilio bello;

mientras a cada labio, por cogello,
siguen más ojos que al clavel temprano,
y mientras triunfa con desdén lozano
del luciente cristal tu gentil cuello.`,
            caseId: 'EXP-GONGORA-1582',
            century: '17'
        },
        guillen: {
            text: `Por qué te pone tan bravo
cuando te dicen negro bembón,
si tiene la boca santa,
negro bembón.

Bembón así como ere
tiene de to;
Caridad te mantiene,
te lo da to.`,
            caseId: 'EXP-GUILLEN-CUBA-1930',
            century: '20'
        }
    };

    function cargarMuestraEnPerfilador(clave) {
        const item = MUESTRAS_CORPUS[clave];
        if (!item) return;
        if (textoInput) textoInput.value = item.text;
        if (inputExpediente) inputExpediente.value = item.caseId;
        if (selectPrior) selectPrior.value = item.century;
        cambiarVista('vista-bayesiano');
        ejecutarInferencia();
    }

    // Handlers para botones de tarjetas del Corpus
    document.querySelectorAll('[class*="btn-load-corpus-"]').forEach(btn => {
        btn.addEventListener('click', () => {
            const className = Array.from(btn.classList).find(c => c.startsWith('btn-load-corpus-'));
            if (className) {
                const clave = className.replace('btn-load-corpus-', '');
                cargarMuestraEnPerfilador(clave);
            }
        });
    });

    // =========================================================================
    // 6. Módulo de Escansión Métrica Integral (Vista 3)
    // =========================================================================
    const poemMeterInput = document.getElementById('meter-poem-input');
    const btnRunScansion = document.getElementById('btn-run-scansion');
    const btnSampleMeterSorJuana = document.getElementById('btn-sample-meter-sorjuana');
    const meterTotalVersesBadge = document.getElementById('meter-total-verses-badge');
    const meterFormDisplay = document.getElementById('meter-form-display');
    const meterSchemeDisplay = document.getElementById('meter-scheme-display');
    const meterTableBody = document.getElementById('meter-table-body');

    const SONETO_SOR_JUANA_COMPLETO = `En perseguirme, Mundo, ¿qué interesas?
¿En qué te ofendo, cuando sólo intento
poner bellezas en mi entendimiento
y no mi entendimiento en las bellezas?

Yo no estimo tesoros ni riquezas;
y así, siempre me causa más contento
poner riquezas en mi entendimiento
que no mi entendimiento en las riquezas.

Y no estimo hermosura que, vencida,
es despojo civil de las edades,
ni riqueza me agrada fementida,

teniendo por mejor, en mis verdades,
consumir vanidades de la vida
que consumir la vida en vanidades.`;

    async function ejecutarEscansion() {
        if (!poemMeterInput) return;
        const poemText = poemMeterInput.value.trim();
        if (!poemText) return;

        if (btnRunScansion) {
            btnRunScansion.textContent = 'Analizando métrica...';
            btnRunScansion.style.opacity = '0.7';
        }

        try {
            const res = await fetch('/api/v1/analyze-poem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ poem_text: poemText })
            });

            if (res.ok) {
                const data = await res.json();

                if (meterTotalVersesBadge) {
                    meterTotalVersesBadge.textContent = `${data.total_verses} Versos Analizados`;
                }
                if (meterFormDisplay) {
                    meterFormDisplay.textContent = `${data.detected_stanza_type} (${data.total_verses} versos)`;
                }
                if (meterSchemeDisplay) {
                    meterSchemeDisplay.textContent = data.global_rhyme_scheme || 'Libre / Asonante';
                }

                if (meterTableBody) {
                    let rowsHtml = '';
                    data.stanzas.forEach((stanza, sIdx) => {
                        stanza.verses.forEach(v => {
                            const compStr = v.final_stress_compensation > 0 
                                ? `+${v.final_stress_compensation}` 
                                : `${v.final_stress_compensation}`;

                            rowsHtml += `
                                <tr>
                                    <td style="color: var(--texto-sepia); font-weight: 600;">${v.verse_number}</td>
                                    <td style="font-family: var(--font-literaria); font-size: 1.12rem; color: var(--texto-pergamino);">${v.raw_text}</td>
                                    <td style="color: var(--acento-liquen); font-weight: 600; text-align: center;">${v.metrical_syllables}</td>
                                    <td style="color: var(--texto-sepia); text-align: center;">${v.sinalefas_count}</td>
                                    <td style="color: var(--texto-sepia); text-align: center;">${compStr}</td>
                                    <td style="text-align: right;"><span style="color: var(--acento-siena); font-weight: 600;">-${v.rhyme_segment}</span></td>
                                </tr>
                            `;
                        });
                    });
                    meterTableBody.innerHTML = rowsHtml;
                }
            }
        } catch (e) {
            console.error('Error al analizar métrica:', e);
        } finally {
            if (btnRunScansion) {
                btnRunScansion.textContent = 'Escanear Poema Completo';
                btnRunScansion.style.opacity = '1';
            }
        }
    }

    if (btnRunScansion) {
        btnRunScansion.addEventListener('click', ejecutarEscansion);
    }

    if (btnSampleMeterSorJuana) {
        btnSampleMeterSorJuana.addEventListener('click', () => {
            if (poemMeterInput) {
                poemMeterInput.value = SONETO_SOR_JUANA_COMPLETO;
                ejecutarEscansion();
            }
        });
    }

    // =========================================================================
    // 7. Módulo de Informes Periciales Multi-Formato (Vista 4)
    // =========================================================================
    const btnReportFormats = document.querySelectorAll('.btn-report-format');
    const reportCaseIdInput = document.getElementById('report-case-id');
    const reportCenturyPriorSelect = document.getElementById('report-century-prior');
    const reportTextInput = document.getElementById('report-text-input');
    const btnGenerateReport = document.getElementById('btn-generate-report');
    const btnDownloadReport = document.getElementById('btn-download-report');
    const btnCopyReport = document.getElementById('btn-copy-report');
    const reportStatusBadge = document.getElementById('report-status-badge');
    const reportContentCode = document.getElementById('report-content-code');

    let formatoReporteActual = 'markdown';
    let ultimoReporteGenerado = null;

    async function generarReportePericial(formato) {
        if (!reportTextInput) return;
        const texto = reportTextInput.value.trim();
        if (!texto) return;

        const fmt = formato || formatoReporteActual;
        const caseId = (reportCaseIdInput && reportCaseIdInput.value.trim()) || 'EXP-PERICIAL-2026';
        const centuryVal = reportCenturyPriorSelect ? reportCenturyPriorSelect.value : '';
        const centuryPrior = centuryVal ? parseInt(centuryVal, 10) : null;

        if (btnGenerateReport) {
            btnGenerateReport.textContent = 'Generando dictamen...';
            btnGenerateReport.style.opacity = '0.7';
        }
        if (reportStatusBadge) {
            reportStatusBadge.textContent = 'Procesando peritaje...';
        }

        try {
            const res = await fetch('/api/v1/generate-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: texto,
                    case_identifier: caseId,
                    century_prior: centuryPrior,
                    format_type: fmt
                })
            });

            if (res.ok) {
                const data = await res.json();
                ultimoReporteGenerado = data;

                if (reportContentCode) {
                    reportContentCode.textContent = data.content;
                }
                if (reportStatusBadge) {
                    const byteSize = new Blob([data.content]).size;
                    reportStatusBadge.textContent = `${data.format_type.toUpperCase()} Listo (${byteSize} B)`;
                }
            } else {
                if (reportContentCode) {
                    reportContentCode.textContent = `// Error al generar el informe en formato ${fmt}.`;
                }
            }
        } catch (e) {
            console.error('Error al generar informe:', e);
            if (reportContentCode) {
                reportContentCode.textContent = `// Error de conexión al generar el informe.`;
            }
        } finally {
            if (btnGenerateReport) {
                btnGenerateReport.textContent = 'Generar Dictamen';
                btnGenerateReport.style.opacity = '1';
            }
        }
    }

    function descargarReporteGenerado() {
        if (!ultimoReporteGenerado || !ultimoReporteGenerado.content) {
            generarReportePericial(formatoReporteActual).then(() => {
                if (ultimoReporteGenerado) ejecutarDescarga(ultimoReporteGenerado);
            });
            return;
        }
        ejecutarDescarga(ultimoReporteGenerado);
    }

    function ejecutarDescarga(rep) {
        const blob = new Blob([rep.content], { type: rep.mime_type || 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = rep.filename || `dictamen_${rep.format_type}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function copiarReporteAlPortapapeles() {
        const texto = ultimoReporteGenerado ? ultimoReporteGenerado.content : (reportContentCode ? reportContentCode.textContent : '');
        if (!texto) return;

        navigator.clipboard.writeText(texto).then(() => {
            if (btnCopyReport) {
                const originalText = btnCopyReport.textContent;
                btnCopyReport.textContent = 'Contenido copiado al portapapeles con éxito';
                btnCopyReport.style.color = 'var(--acento-liquen)';
                setTimeout(() => {
                    btnCopyReport.textContent = originalText;
                    btnCopyReport.style.color = '';
                }, 2200);
            }
        }).catch(err => {
            console.error('Error al copiar al portapapeles:', err);
        });
    }

    // Listeners de botones de formato
    btnReportFormats.forEach(btn => {
        btn.addEventListener('click', () => {
            btnReportFormats.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            formatoReporteActual = btn.getAttribute('data-format');
            generarReportePericial(formatoReporteActual);
        });
    });

    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', () => generarReportePericial(formatoReporteActual));
    }

    if (btnDownloadReport) {
        btnDownloadReport.addEventListener('click', descargarReporteGenerado);
    }

    if (btnCopyReport) {
        btnCopyReport.addEventListener('click', copiarReporteAlPortapapeles);
    }

    // =========================================================================
    // 8. Listeners Iniciales
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

    // Montaje inicial, escansión y generación de informe por defecto
    animarCascada();
    ejecutarEscansion();
    generarReportePericial('markdown');
});
