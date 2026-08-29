/**
 * Idiolect-G2P — Aplicacion Frontend Cientifica
 * Interaccion con la API REST, renderizado reactivo y sintesis acustica.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Estado global de la aplicacion
    const state = {
        dialects: [],
        corpus: [],
        currentAudioBase64: null,
        selectedReportFormat: 'markdown',
        lastProfileResult: null,
        currentTheme: localStorage.getItem('idiolect_theme') || 'dark'
    };

    // =========================================================================
    // 1. GESTION DE TEMA (CLARO / OSCURO)
    // =========================================================================
    document.documentElement.setAttribute('data-theme', state.currentTheme);
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            state.currentTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', state.currentTheme);
            localStorage.setItem('idiolect_theme', state.currentTheme);
        });
    }

    // =========================================================================
    // 2. NAVEGACION POR PESTANAS
    // =========================================================================
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');

    function switchTab(tabId) {
        tabButtons.forEach(btn => {
            const isActive = btn.getAttribute('data-tab') === tabId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
        tabPanels.forEach(panel => {
            panel.classList.toggle('active', panel.id === tabId);
        });
    }

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // =========================================================================
    // 3. CARGA DEL CATALOGO DE DIALECTOS
    // =========================================================================
    async function loadDialects() {
        try {
            const res = await fetch('/api/v1/dialects');
            if (!res.ok) throw new Error('No se pudo cargar el catalogo');
            state.dialects = await res.json();

            // Poblar dropdown en Transcriptor
            const selectEl = document.getElementById('transcribe-dialect-select');
            if (selectEl) {
                selectEl.innerHTML = state.dialects.map(d => 
                    `<option value="${d.code}">${d.name} (${d.region})</option>`
                ).join('');
            }

            // Poblar tabla de Catalogo
            renderDialectsCatalog(state.dialects);
        } catch (err) {
            console.error('Error al inicializar dialectos:', err);
            const statusBadge = document.getElementById('api-status-badge');
            if (statusBadge) {
                statusBadge.textContent = 'API Desconectada';
                statusBadge.className = 'badge badge-rose';
            }
        }
    }

    function renderDialectsCatalog(dialectsList) {
        const tbody = document.getElementById('dialects-catalog-body');
        if (!tbody) return;

        const countBadge = document.getElementById('dialects-count-badge');
        if (countBadge) countBadge.textContent = `${dialectsList.length} Variantes`;

        tbody.innerHTML = dialectsList.map(d => {
            const iso = d.isogloss_vector || {};
            return `
                <tr>
                    <td><code>${d.code}</code></td>
                    <td><strong>${d.name}</strong></td>
                    <td><span class="badge badge-indigo">${d.region}</span></td>
                    <td style="font-size: 0.85rem; color: var(--text-secondary); max-width: 300px;">${d.description}</td>
                    <td><strong>${((iso.seseo || 0) * 100).toFixed(0)}%</strong></td>
                    <td>${((iso.aspiration_s || 0) * 100).toFixed(0)}%</td>
                    <td>${((iso.lambdacism || 0) * 100).toFixed(0)}%</td>
                    <td>${((iso.lleismo || 0) * 100).toFixed(0)}%</td>
                </tr>
            `;
        }).join('');
    }

    // Buscador interactivo en catalogo
    const dialectSearch = document.getElementById('dialects-search-input');
    if (dialectSearch) {
        dialectSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = state.dialects.filter(d => 
                d.name.toLowerCase().includes(query) ||
                d.code.toLowerCase().includes(query) ||
                d.region.toLowerCase().includes(query) ||
                d.description.toLowerCase().includes(query)
            );
            renderDialectsCatalog(filtered);
        });
    }

    // =========================================================================
    // 4. CARGA DEL CORPUS DE EJEMPLOS HISTORICOS
    // =========================================================================
    async function loadCorpus() {
        try {
            const res = await fetch('/static/corpus_examples.json');
            if (!res.ok) return;
            state.corpus = await res.json();

            const container = document.getElementById('corpus-cards-container');
            if (!container) return;

            container.innerHTML = state.corpus.map(item => `
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h3 style="font-family: var(--font-heading); font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--text-primary);">
                            ${item.title}
                        </h3>
                        <div style="font-size: 0.8rem; color: var(--accent-indigo); font-weight: 600; margin-bottom: 0.75rem;">
                            Autor: ${item.author} | Siglo ${item.century}
                        </div>
                        <pre style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); white-space: pre-wrap; margin-bottom: 1rem; max-height: 120px; overflow-y: auto;">${item.text}</pre>
                    </div>
                    <button class="btn btn-primary btn-sm btn-load-corpus-item" data-id="${item.id}">
                        Cargar en Perfilador Bayesiano
                    </button>
                </div>
            `).join('');

            // Asignar eventos de carga
            document.querySelectorAll('.btn-load-corpus-item').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    const found = state.corpus.find(c => c.id === id);
                    if (found) {
                        const profilerText = document.getElementById('profiler-text-input');
                        const profilerCase = document.getElementById('profiler-case-id');
                        const profilerCentury = document.getElementById('profiler-century-select');

                        if (profilerText) profilerText.value = found.text;
                        if (profilerCase) profilerCase.value = `CASE-${found.id.toUpperCase()}`;
                        if (profilerCentury) profilerCentury.value = found.century ? found.century.toString() : '';

                        switchTab('tab-profiler');
                        runProfiling();
                    }
                });
            });
        } catch (err) {
            console.warn('No se pudo cargar corpus_examples.json:', err);
        }
    }

    // =========================================================================
    // 5. PERFILADOR IDIOLECTAL BAYESIANO
    // =========================================================================
    const btnRunProfiling = document.getElementById('btn-run-profiling');
    if (btnRunProfiling) {
        btnRunProfiling.addEventListener('click', runProfiling);
    }

    async function runProfiling() {
        const textInput = document.getElementById('profiler-text-input');
        const caseIdInput = document.getElementById('profiler-case-id');
        const centurySelect = document.getElementById('profiler-century-select');

        if (!textInput || !textInput.value.trim()) {
            alert('Por favor, ingrese un texto poético para analizar.');
            return;
        }

        const payload = {
            text: textInput.value.trim(),
            case_identifier: (caseIdInput && caseIdInput.value.trim()) ? caseIdInput.value.trim() : 'CASE-G2P-001',
            century_prior: centurySelect && centurySelect.value ? parseInt(centurySelect.value, 10) : null
        };

        const predNameEl = document.getElementById('profiler-predicted-name');
        const confBadge = document.getElementById('profiler-confidence-badge');
        const rankingContainer = document.getElementById('profiler-ranking-bars');
        const evidencesContainer = document.getElementById('profiler-evidences-container');

        if (predNameEl) predNameEl.textContent = 'Calculando verosimilitudes...';

        try {
            const res = await fetch('/api/v1/profile-idiolect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Error en la inferencia');
            }

            const data = await res.json();
            state.lastProfileResult = data;

            // 1. Mostrar prediccion principal
            if (predNameEl) predNameEl.textContent = data.predicted_dialect_name;
            const regionEl = document.getElementById('profiler-predicted-region');
            const topRanking = data.dialect_ranking[0];
            if (regionEl && topRanking) regionEl.textContent = `Macrorregión: ${topRanking.region}`;

            const confPct = (data.confidence_score * 100).toFixed(1);
            if (confBadge) confBadge.textContent = `Confianza: ${confPct}%`;

            // 2. Renderizar barras de probabilidad
            if (rankingContainer) {
                rankingContainer.innerHTML = data.dialect_ranking.slice(0, 7).map((dr, idx) => {
                    const pct = (dr.posterior_probability * 100).toFixed(1);
                    const isTop = idx === 0;
                    return `
                        <div class="prob-bar-container">
                            <div class="prob-bar-header">
                                <span>${dr.name}</span>
                                <span>${pct}% (d=${dr.phonetic_distance.toFixed(3)})</span>
                            </div>
                            <div class="prob-bar-track">
                                <div class="prob-bar-fill ${isTop ? 'highlight' : ''}" style="width: ${pct}%;"></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            // 3. Renderizar evidencias discriminantes
            if (evidencesContainer) {
                if (data.discriminant_evidences && data.discriminant_evidences.length > 0) {
                    evidencesContainer.innerHTML = data.discriminant_evidences.map(ev => `
                        <div class="evidence-card">
                            <div class="evidence-header">
                                <span>Versos ${ev.verse_1} y ${ev.verse_2} ('${ev.word_1}' / '${ev.word_2}')</span>
                                <span class="badge badge-amber">${ev.phenomenon.split('(')[0]}</span>
                            </div>
                            <div class="evidence-body">${ev.description}</div>
                        </div>
                    `).join('');
                } else {
                    evidencesContainer.innerHTML = `
                        <div style="font-size: 0.85rem; color: var(--text-muted); padding: 0.5rem 0;">
                            No se detectaron divergencias de rima anómalas. Todas las hipótesis dialectales evaluadas mantienen regularidad estructural.
                        </div>
                    `;
                }
            }

        } catch (err) {
            console.error('Error en inferencia bayesiana:', err);
            alert(`Error al ejecutar inferencia: ${err.message}`);
            if (predNameEl) predNameEl.textContent = 'Error en el cálculo';
        }
    }

    // =========================================================================
    // 6. TRANSCRIPTOR G2P & SINTESIS AFI
    // =========================================================================
    const btnRunTranscribe = document.getElementById('btn-run-transcribe');
    const btnSynthesizeAudio = document.getElementById('btn-synthesize-audio');
    const btnReplayAudio = document.getElementById('btn-replay-audio');

    if (btnRunTranscribe) {
        btnRunTranscribe.addEventListener('click', () => runTranscribe(false));
    }
    if (btnSynthesizeAudio) {
        btnSynthesizeAudio.addEventListener('click', () => runTranscribe(true));
    }
    if (btnReplayAudio) {
        btnReplayAudio.addEventListener('click', () => {
            if (state.currentAudioBase64 && window.ipaAudioEngine) {
                window.ipaAudioEngine.playBase64Wav(state.currentAudioBase64);
            }
        });
    }

    async function runTranscribe(generateAudio = false) {
        const textInput = document.getElementById('transcribe-text-input');
        const dialectSelect = document.getElementById('transcribe-dialect-select');
        const fullIpaEl = document.getElementById('transcribe-full-ipa');
        const syllablesContainer = document.getElementById('transcribe-syllables-container');
        const wordCountBadge = document.getElementById('transcribe-word-count-badge');
        const audioStatus = document.getElementById('audio-playback-status');

        if (!textInput || !textInput.value.trim()) return;

        const payload = {
            text: textInput.value.trim(),
            dialect_code: dialectSelect ? dialectSelect.value : 'ES_PENINSULAR',
            generate_audio: generateAudio
        };

        if (fullIpaEl) fullIpaEl.textContent = '/transcribiendo.../';
        if (generateAudio && audioStatus) audioStatus.textContent = 'Sintetizando audio formántico...';

        try {
            const res = await fetch('/api/v1/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Error al transcribir');
            const data = await res.json();

            if (fullIpaEl) fullIpaEl.textContent = `/${data.full_ipa_text}/`;
            if (wordCountBadge) wordCountBadge.textContent = `${data.total_words} Palabras`;

            // Renderizar píldoras silábicas
            if (syllablesContainer) {
                syllablesContainer.innerHTML = data.transcriptions.map(word => {
                    const sylPills = word.syllables.map((s, sIdx) => {
                        const isStressed = sIdx === word.stress_index;
                        return `
                            <span class="syllable-pill ${isStressed ? 'stressed' : ''}">
                                <span>${s}</span>
                                <span class="syllable-tag">${isStressed ? 'Tónica' : 'Átona'}</span>
                            </span>
                        `;
                    }).join('');

                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; background: rgba(15, 23, 42, 0.4); padding: 0.4rem; border-radius: var(--radius-sm); margin: 0.2rem;">
                            <div style="display: flex;">${sylPills}</div>
                            <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-blue); margin-top: 0.2rem;">/${word.syllabified_ipa}/</div>
                        </div>
                    `;
                }).join('');
            }

            // Reproduccion de Audio
            if (data.audio_base64) {
                state.currentAudioBase64 = data.audio_base64;
                if (btnReplayAudio) btnReplayAudio.style.display = 'inline-flex';
                if (audioStatus) audioStatus.textContent = 'Reproduciendo síntesis formántica AFI...';
                if (window.ipaAudioEngine) {
                    await window.ipaAudioEngine.playBase64Wav(data.audio_base64);
                    if (audioStatus) audioStatus.textContent = 'Reproducción finalizada.';
                }
            }

        } catch (err) {
            console.error('Error al transcribir:', err);
            if (fullIpaEl) fullIpaEl.textContent = '/error en transcripción/';
        }
    }

    // =========================================================================
    // 7. ESCANSION METRICA VERSAL
    // =========================================================================
    const btnRunScansion = document.getElementById('btn-run-scansion');
    if (btnRunScansion) {
        btnRunScansion.addEventListener('click', runScansion);
    }

    async function runScansion() {
        const poemInput = document.getElementById('meter-poem-input');
        const typeBadge = document.getElementById('meter-stanza-type-badge');
        const schemeDisplay = document.getElementById('meter-scheme-display');
        const consonantDisplay = document.getElementById('meter-consonant-display');
        const tableBody = document.getElementById('meter-table-body');

        if (!poemInput || !poemInput.value.trim()) return;

        try {
            const res = await fetch('/api/v1/analyze-poem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ poem_text: poemInput.value.trim() })
            });

            if (!res.ok) throw new Error('Error al escanear métrica');
            const data = await res.json();

            if (typeBadge) typeBadge.textContent = data.detected_stanza_type;
            if (schemeDisplay) schemeDisplay.textContent = data.global_rhyme_scheme || 'Libre';
            if (consonantDisplay) {
                consonantDisplay.textContent = data.is_consonant_expected ? 'Exigida (Clásica)' : 'Asonante / Libre';
                consonantDisplay.style.color = data.is_consonant_expected ? 'var(--accent-emerald)' : 'var(--text-secondary)';
            }

            if (tableBody) {
                const allVerses = data.stanzas.flatMap(s => s.verses);
                tableBody.innerHTML = allVerses.map(v => `
                    <tr>
                        <td><strong>${v.verse_number}</strong></td>
                        <td style="font-family: var(--font-heading); font-size: 0.95rem;">${v.raw_text}</td>
                        <td><span class="badge badge-blue">${v.metrical_syllables}</span></td>
                        <td>${v.sinalefas_count}</td>
                        <td>${v.final_stress_compensation > 0 ? `+${v.final_stress_compensation}` : v.final_stress_compensation}</td>
                        <td><code style="color: var(--accent-amber); font-weight: bold;">-${v.rhyme_segment}</code></td>
                    </tr>
                `).join('');
            }

        } catch (err) {
            console.error('Error al escanear métrica:', err);
        }
    }

    // =========================================================================
    // 8. GENERADOR DE INFORMES MULTI-FORMATO
    // =========================================================================
    const formatButtons = document.querySelectorAll('.btn-format-select');
    formatButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            formatButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedReportFormat = btn.getAttribute('data-format');
            const badge = document.getElementById('report-format-badge');
            if (badge) badge.textContent = btn.textContent.split(' ')[0];
        });
    });

    const btnGenerateReport = document.getElementById('btn-generate-selected-report');
    const btnDownloadReport = document.getElementById('btn-download-report');

    let currentReportContent = '';
    let currentReportFilename = 'report.txt';
    let currentReportMime = 'text/plain';

    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', generateReportPreview);
    }
    if (btnDownloadReport) {
        btnDownloadReport.addEventListener('click', () => {
            if (!currentReportContent) {
                alert('Genere primero la vista previa del informe.');
                return;
            }
            const blob = new Blob([currentReportContent], { type: currentReportMime });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentReportFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    async function generateReportPreview() {
        const profilerText = document.getElementById('profiler-text-input');
        const caseIdInput = document.getElementById('profiler-case-id');
        const centurySelect = document.getElementById('profiler-century-select');
        const previewBox = document.getElementById('report-preview-box');

        const text = (profilerText && profilerText.value.trim()) ? profilerText.value.trim() : 'En este dulce abrazo yo sigo cada paso';
        const caseId = (caseIdInput && caseIdInput.value.trim()) ? caseIdInput.value.trim() : 'CASE-G2P-001';
        const century = (centurySelect && centurySelect.value) ? parseInt(centurySelect.value, 10) : null;

        if (previewBox) previewBox.textContent = '// Generando dictamen formal...';

        try {
            const res = await fetch('/api/v1/generate-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    format_type: state.selectedReportFormat,
                    case_identifier: caseId,
                    century_prior: century
                })
            });

            if (!res.ok) throw new Error('Error al generar informe');
            const data = await res.json();

            currentReportContent = data.content;
            currentReportFilename = data.filename;
            currentReportMime = data.mime_type;

            if (previewBox) {
                previewBox.textContent = data.content;
            }

        } catch (err) {
            console.error('Error al generar informe:', err);
            if (previewBox) previewBox.textContent = `// Error al generar reporte: ${err.message}`;
        }
    }

    // Inicializacion inicial
    await loadDialects();
    await loadCorpus();
});
