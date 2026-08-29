/**
 * Idiolect-G2P — Scriptorium Monástico & Filología Computacional
 * Estética: Cuero Envejecido, Pigmentos Minerales Mates y Tinta Ferrogálica
 */

document.addEventListener('DOMContentLoaded', async () => {
    // =========================================================================
    // Estado Global de la Aplicación
    // =========================================================================
    const state = {
        dialects: [],
        corpus: [],
        currentAudioBase64: null,
        selectedReportFormat: 'markdown',
        lastProfileResult: null,
        currentTheme: localStorage.getItem('idiolect_theme') || 'dark'
    };

    // =========================================================================
    // 1. Sistema de Notificaciones Toast Editorial
    // =========================================================================
    function showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type === 'error' ? 'toast-error' : type === 'success' ? 'toast-success' : ''}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(8px)';
            toast.style.transition = 'all 0.25s ease';
            setTimeout(() => toast.remove(), 250);
        }, 3200);
    }

    // =========================================================================
    // 2. Gestión de Tema (Scriptorium / Pergamino)
    // =========================================================================
    document.documentElement.setAttribute('data-theme', state.currentTheme);
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            state.currentTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', state.currentTheme);
            localStorage.setItem('idiolect_theme', state.currentTheme);
            themeToggleBtn.textContent = state.currentTheme === 'dark' ? 'Modo Pergamino' : 'Modo Scriptorium';
            showToast(`Activado ${state.currentTheme === 'dark' ? 'Scriptorium Nocturno' : 'Pergamino Diurno'}.`);
        });
        themeToggleBtn.textContent = state.currentTheme === 'dark' ? 'Modo Pergamino' : 'Modo Scriptorium';
    }

    // =========================================================================
    // 3. Navegación Editorial por Pestañas (Pura Tipografía)
    // =========================================================================
    const navLinks = document.querySelectorAll('.nav-link');
    const tabPanels = document.querySelectorAll('.tab-panel');

    function switchTab(tabId) {
        navLinks.forEach(btn => {
            const isActive = btn.getAttribute('data-tab') === tabId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
            if (isActive) {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        });
        tabPanels.forEach(panel => {
            panel.classList.toggle('active', panel.id === tabId);
        });
    }

    navLinks.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // =========================================================================
    // 4. Catálogo de Variantes Dialectales
    // =========================================================================
    async function loadDialects() {
        try {
            const res = await fetch('/api/v1/dialects');
            if (!res.ok) throw new Error('No se pudo cargar el catálogo de dialectos.');
            state.dialects = await res.json();

            // Actualizar selector en módulo G2P
            const selectEl = document.getElementById('transcribe-dialect-select');
            if (selectEl) {
                selectEl.innerHTML = state.dialects.map(d => 
                    `<option value="${d.code}">${d.name} — [${d.region}]</option>`
                ).join('');
            }

            // Renderizar tabla de catálogo
            renderDialectsCatalog(state.dialects);
        } catch (err) {
            console.error('Error al inicializar dialectos:', err);
            const statusBadge = document.getElementById('api-status-badge');
            if (statusBadge) {
                statusBadge.innerHTML = '<span class="status-dot" style="background: var(--accent-iron-oxide);"></span> Desconectada';
                statusBadge.style.color = 'var(--accent-iron-oxide)';
            }
            showToast('No se pudo conectar con el catálogo de la API.', 'error');
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
                    <td><code style="font-family: var(--font-mono); font-size: 0.78rem;">${d.code}</code></td>
                    <td><strong style="font-family: var(--font-serif); font-size: 1rem;">${d.name}</strong></td>
                    <td><span style="font-family: var(--font-mono); font-size: 0.76rem; color: var(--accent-lapis); font-weight: 600;">${d.region}</span></td>
                    <td style="font-family: var(--font-serif); font-size: 0.9rem; color: var(--text-secondary); max-width: 280px;">${d.description}</td>
                    <td style="font-family: var(--font-mono); font-size: 0.82rem;"><strong>${((iso.seseo || 0) * 100).toFixed(0)}%</strong></td>
                    <td style="font-family: var(--font-mono); font-size: 0.82rem;">${((iso.aspiration_s || 0) * 100).toFixed(0)}%</td>
                    <td style="font-family: var(--font-mono); font-size: 0.82rem;">${((iso.lambdacism || 0) * 100).toFixed(0)}%</td>
                    <td style="font-family: var(--font-mono); font-size: 0.82rem;">${((iso.lleismo || 0) * 100).toFixed(0)}%</td>
                </tr>
            `;
        }).join('');
    }

    const dialectSearch = document.getElementById('dialects-search-input');
    if (dialectSearch) {
        dialectSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
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
    // 5. Corpus de Casos Históricos y Periciales Documentados
    // =========================================================================
    async function loadCorpus() {
        try {
            const res = await fetch('/static/corpus_examples.json');
            if (!res.ok) return;
            state.corpus = await res.json();

            const container = document.getElementById('corpus-cards-container');
            if (!container) return;

            container.innerHTML = state.corpus.map(item => `
                <div style="background: var(--bg-panel); border: 1px solid var(--border-divider); border-radius: var(--radius-sharp); padding: 1.35rem; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h3 style="font-family: var(--font-heading); font-size: 1.25rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                            ${item.title}
                        </h3>
                        <div style="font-family: var(--font-mono); font-size: 0.76rem; color: var(--accent-iron-oxide); font-weight: 600; margin-bottom: 0.75rem;">
                            ${item.author} — Siglo ${item.century || 'N/A'}
                        </div>
                        <div style="font-family: var(--font-serif); font-size: 0.98rem; line-height: 1.6; background: var(--bg-lab); padding: 0.85rem 1rem; border: 1px solid var(--border-divider); border-radius: var(--radius-sharp); color: var(--text-secondary); white-space: pre-wrap; margin-bottom: 1rem; max-height: 140px; overflow-y: auto;">${item.text}</div>
                    </div>
                    <button class="btn-editorial btn-subtle btn-load-corpus-item" data-id="${item.id}" style="width: 100%; font-size: 0.82rem;">
                        Cargar en Perfilador Bayesiano
                    </button>
                </div>
            `).join('');

            document.querySelectorAll('.btn-load-corpus-item').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    const found = state.corpus.find(c => c.id === id);
                    if (found) {
                        const profilerText = document.getElementById('profiler-text-input');
                        const profilerCase = document.getElementById('profiler-case-id');
                        const profilerCentury = document.getElementById('profiler-century-select');

                        if (profilerText) profilerText.value = found.text;
                        if (profilerCase) profilerCase.value = `EXP-${found.id.toUpperCase()}`;
                        if (profilerCentury) profilerCentury.value = found.century ? found.century.toString() : '';

                        switchTab('tab-profiler');
                        runProfiling();
                        showToast(`Manuscrito de ${found.author} cargado.`);
                    }
                });
            });
        } catch (err) {
            console.warn('No se pudo cargar corpus_examples.json:', err);
        }
    }

    // =========================================================================
    // 6. Perfilador Idiolectal Bayesiano & Lingüística Forense
    // =========================================================================
    const btnRunProfiling = document.getElementById('btn-run-profiling');
    const btnLoadSampleProfiler = document.getElementById('btn-load-sample-profiler');

    if (btnRunProfiling) {
        btnRunProfiling.addEventListener('click', runProfiling);
    }

    if (btnLoadSampleProfiler) {
        btnLoadSampleProfiler.addEventListener('click', () => {
            if (state.corpus.length > 0) {
                const sample = state.corpus[0];
                const textInput = document.getElementById('profiler-text-input');
                const caseId = document.getElementById('profiler-case-id');
                const century = document.getElementById('profiler-century-select');
                if (textInput) textInput.value = sample.text;
                if (caseId) caseId.value = `EXP-${sample.id.toUpperCase()}`;
                if (century) century.value = sample.century ? sample.century.toString() : '';
                showToast(`Cargado soneto de ${sample.author}`);
            }
        });
    }

    async function runProfiling() {
        const textInput = document.getElementById('profiler-text-input');
        const caseIdInput = document.getElementById('profiler-case-id');
        const centurySelect = document.getElementById('profiler-century-select');

        if (!textInput || !textInput.value.trim()) {
            showToast('Por favor, ingrese un texto poético para analizar.', 'error');
            return;
        }

        const payload = {
            text: textInput.value.trim(),
            case_identifier: (caseIdInput && caseIdInput.value.trim()) ? caseIdInput.value.trim() : 'EXP-G2P-001',
            century_prior: centurySelect && centurySelect.value ? parseInt(centurySelect.value, 10) : null
        };

        const predNameEl = document.getElementById('profiler-predicted-name');
        const confBadge = document.getElementById('profiler-confidence-badge');
        const indexContainer = document.getElementById('posterior-index-container');
        const evidencesContainer = document.getElementById('profiler-evidences-container');

        if (predNameEl) predNameEl.textContent = 'Calculando verosimilitudes bayesianas...';

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

            // 1. Mostrar predicción principal
            if (predNameEl) predNameEl.textContent = data.predicted_dialect_name;
            const regionEl = document.getElementById('profiler-predicted-region');
            const topRanking = data.dialect_ranking[0];
            if (regionEl && topRanking) regionEl.textContent = `Macrorregión: ${topRanking.region}`;

            const confPct = (data.confidence_score * 100).toFixed(1);
            if (confBadge) confBadge.textContent = `Confianza: ${confPct}%`;

            // 2. Renderizar lista estilo índice de libro antiguo
            if (indexContainer) {
                indexContainer.innerHTML = data.dialect_ranking.slice(0, 7).map((dr, idx) => {
                    const pct = (dr.posterior_probability * 100).toFixed(1);
                    const isTop = idx === 0;
                    return `
                        <div class="posterior-index-row ${isTop ? 'top-hypothesis' : ''}">
                            <span class="hyp-name">${idx + 1}. ${dr.name}</span>
                            <div class="hyp-data">
                                <span class="hyp-pct">${pct}%</span>
                                <span class="hyp-dist">d = ${dr.phonetic_distance.toFixed(3)}</span>
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
                                <span class="evidence-phenomenon">${ev.phenomenon.split('(')[0]}</span>
                            </div>
                            <div class="evidence-body">${ev.description}</div>
                        </div>
                    `).join('');
                } else {
                    evidencesContainer.innerHTML = `
                        <div style="font-family: var(--font-serif); font-size: 0.95rem; color: var(--text-muted); padding: 0.5rem 0; font-style: italic;">
                            No se detectaron divergencias fonéticas anómalas. Todas las hipótesis dialectales evaluadas mantienen regularidad estructural.
                        </div>
                    `;
                }
            }

            showToast('Inferencia filológica calculada exitosamente.', 'success');

        } catch (err) {
            console.error('Error en inferencia:', err);
            showToast(`Error al ejecutar inferencia: ${err.message}`, 'error');
            if (predNameEl) predNameEl.textContent = 'Error en el cálculo';
        }
    }

    // =========================================================================
    // 7. Transcriptor G2P & Síntesis Acústica AFI
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

            // Renderizar fichas silábicas limpias
            if (syllablesContainer) {
                syllablesContainer.innerHTML = data.transcriptions.map(word => {
                    const sylBadges = word.syllables.map((s, sIdx) => {
                        const isStressed = sIdx === word.stress_index;
                        return `
                            <span class="syllable-chip ${isStressed ? 'stressed' : ''}">
                                <span>${s}</span>
                                <span class="syllable-type">${isStressed ? 'Tónica' : 'Átona'}</span>
                            </span>
                        `;
                    }).join('');

                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; margin: 0.25rem;">
                            <div style="display: flex; gap: 0.25rem;">${sylBadges}</div>
                            <div style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-iron-oxide); margin-top: 0.25rem;">/${word.syllabified_ipa}/</div>
                        </div>
                    `;
                }).join('');
            }

            // Reproducción de Audio
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
            showToast('Error en la transducción fonética.', 'error');
        }
    }

    // =========================================================================
    // 8. Escansión Métrica Versal
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
                consonantDisplay.style.color = data.is_consonant_expected ? 'var(--accent-verdigris)' : 'var(--text-secondary)';
            }

            if (tableBody) {
                const allVerses = data.stanzas.flatMap(s => s.verses);
                tableBody.innerHTML = allVerses.map(v => `
                    <tr>
                        <td><strong style="font-family: var(--font-mono); font-size: 0.82rem;">${v.verse_number}</strong></td>
                        <td style="font-family: var(--font-serif); font-size: 1.08rem;">${v.raw_text}</td>
                        <td><span class="confidence-metric">${v.metrical_syllables}</span></td>
                        <td style="font-family: var(--font-mono);">${v.sinalefas_count}</td>
                        <td style="font-family: var(--font-mono);">${v.final_stress_compensation > 0 ? `+${v.final_stress_compensation}` : v.final_stress_compensation}</td>
                        <td><code style="font-family: var(--font-mono); color: var(--accent-iron-oxide); font-weight: 600;">-${v.rhyme_segment}</code></td>
                    </tr>
                `).join('');
            }

            showToast('Escansión métrica completada.', 'success');

        } catch (err) {
            console.error('Error al escanear métrica:', err);
            showToast('Error al analizar la métrica versal.', 'error');
        }
    }

    // =========================================================================
    // 9. Generador de Informes Multi-Formato
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
    let currentReportFilename = 'dictamen.txt';
    let currentReportMime = 'text/plain';

    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', generateReportPreview);
    }
    if (btnDownloadReport) {
        btnDownloadReport.addEventListener('click', () => {
            if (!currentReportContent) {
                showToast('Genere primero la vista previa del informe.', 'error');
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
            showToast(`Archivo ${currentReportFilename} descargado.`);
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

        if (previewBox) previewBox.textContent = '// Generando dictamen pericial formal...';

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
            showToast(`Informe en formato ${data.format.toUpperCase()} generado.`);

        } catch (err) {
            console.error('Error al generar informe:', err);
            if (previewBox) previewBox.textContent = `// Error al generar reporte: ${err.message}`;
            showToast('Error al generar el informe.', 'error');
        }
    }

    // Inicialización al arrancar
    await loadDialects();
    await loadCorpus();
});
