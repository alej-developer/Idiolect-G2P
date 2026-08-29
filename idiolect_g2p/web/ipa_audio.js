/**
 * Motor de reproduccion y sintesis acustica en navegador mediante Web Audio API.
 * Web Audio API playback and client-side formant generator.
 */

class IPAAudioEngine {
    constructor() {
        this.audioCtx = null;
        this.currentSource = null;
    }

    initContext() {
        if (!this.audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        }
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    }

    /**
     * Reproduce un flujo binario WAV empaquetado en Base64.
     * @param {string} base64Wav 
     * @returns {Promise<void>}
     */
    async playBase64Wav(base64Wav) {
        this.initContext();
        this.stop();

        try {
            const binaryStr = atob(base64Wav);
            const len = binaryStr.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryStr.charCodeAt(i);
            }

            const audioBuffer = await this.audioCtx.decodeAudioData(bytes.buffer);
            const source = this.audioCtx.createBufferSource();
            source.buffer = audioBuffer;

            const gainNode = this.audioCtx.createGain();
            gainNode.gain.setValueAtTime(0.9, this.audioCtx.currentTime);

            source.connect(gainNode);
            gainNode.connect(this.audioCtx.destination);

            this.currentSource = source;
            source.start(0);

            return new Promise((resolve) => {
                source.onended = () => {
                    this.currentSource = null;
                    resolve();
                };
            });
        } catch (err) {
            console.error('Error al decodificar audio WAV:', err);
            throw err;
        }
    }

    /**
     * Detiene la reproduccion activa.
     */
    stop() {
        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch (e) {
                // Ignore if already stopped
            }
            this.currentSource = null;
        }
    }
}

window.ipaAudioEngine = new IPAAudioEngine();
