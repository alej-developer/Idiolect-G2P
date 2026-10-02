"""
Sintetizador acustico formántico determinista en Python puro.
Deterministic formant acoustic synthesizer in pure Python for IPA sequences.

Genera tramas PCM lineales a 16-bits mono (22.050 Hz) empaquetadas en formato WAV canónico.

Arquitectura (Klatt, 1980; Klatt & Klatt, 1990):
- Fuente glotal de Rosenberg continua en fase durante todo el enunciado.
- Cascada de resonadores formánticos F1-F4 con ganancia unitaria en continua
  y caracteristica de radiacion labial (+6 dB/octava).
- Rama paralela de ruido de friccion con filtro pasabanda de pico constante.
- Parametros por tramas de 2,5 ms suavizados sin desfase, que modelan la
  coarticulacion y eliminan los chasquidos en las fronteras entre segmentos.
- Prosodia: declinacion de F0, prominencia tonica, alargamiento final de frase,
  pausas segun la puntuacion y velocidad de habla ajustable.
- Masterizacion perceptiva: intensidad intrinseca por clase de sonido,
  filtro antizumbido, normalizacion de sonoridad RMS y techo de pico.
"""

from __future__ import annotations
import cmath
import io
import math
import random
import struct
import wave
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .acoustic_features import (
    AFFRICATES,
    TAPS,
    TRILLS,
    VOICED_STOPS,
    VOICELESS_STOPS,
    VOWELS,
    IPA_ACOUSTIC_TABLE,
    AcousticParameters,
    get_acoustic_parameters,
    get_relative_intensity_db,
)
from ..core.transducer import G2PTransducer
from ..dialects.base import Dialect


_MULTI_CHAR_SYMBOLS: Tuple[str, ...] = ("t͡ʃ", "t͡ʂ", "t͡ɬ", "s̺", "e̥", "o̥", "ts", "dz")

FRAME_MS = 2.5
REFERENCE_F0_HZ = 118.0
MIN_SPEECH_RATE = 0.5
MAX_SPEECH_RATE = 2.0

# Pausas a velocidad 1.0 (ms): juntura de palabra, coma/punto y coma, punto/fin de verso.
_PAUSE_MS: Dict[str, float] = {"word": 35.0, "minor": 260.0, "major": 480.0, "question": 480.0}
_LEAD_IN_MS = 60.0
_TAIL_MS = 180.0

# Escalado temporal de la tabla acustica hacia un tempo moderado (~4 silabas/s).
_VOWEL_TEMPO = 1.03
_CONSONANT_TEMPO = 0.86

# Sonoridad de referencia para voz hablada (~ -16 LUFS, AES TD1004).
_TARGET_RMS_DBFS = -16.0
_PEAK_CEILING = 0.89  # -1 dBFS

_MINOR_PUNCTUATION = frozenset(",;:—–()«»\"¿¡")
_MAJOR_PUNCTUATION = frozenset(".!…\n")

_GLOTTAL_TABLE_SIZE = 256
_NOISE_TABLE_SIZE = 1 << 15


def _build_glottal_table(size: int) -> List[float]:
    """Ciclo glotal de Rosenberg (apertura suave, cierre abrupto) sin componente continua."""
    table: List[float] = []
    for n in range(size):
        t = n / size
        if t < 0.60:
            g = 0.5 * (1.0 - math.cos(math.pi * t / 0.60))
        elif t < 0.85:
            g = math.cos(math.pi * (t - 0.60) / 0.50)
        else:
            g = 0.0
        table.append(g)
    mean = sum(table) / size
    return [g - mean for g in table]


_GLOTTAL_TABLE: List[float] = _build_glottal_table(_GLOTTAL_TABLE_SIZE)
_NOISE_RNG = random.Random(42)
_NOISE_TABLE: List[float] = [_NOISE_RNG.uniform(-1.0, 1.0) for _ in range(_NOISE_TABLE_SIZE)]

_GLOTTAL_HARMONICS: List[complex] = []
_CALIBRATION_CACHE: Dict[Tuple[int, str], Tuple[float, float]] = {}


def _resonator_coeffs(freq: float, bandwidth: float, sample_rate: int) -> Tuple[float, float, float]:
    """Coeficientes (A, B, C) del resonador de Klatt con ganancia unitaria en continua."""
    freq = min(max(freq, 50.0), 0.45 * sample_rate)
    bandwidth = max(bandwidth, 20.0)
    r = math.exp(-math.pi * bandwidth / sample_rate)
    c = -r * r
    b = 2.0 * r * math.cos(2.0 * math.pi * freq / sample_rate)
    return 1.0 - b - c, b, c


def _bandpass_coeffs(center_freq: float, bandwidth: float, sample_rate: int) -> Tuple[float, float, float]:
    """Coeficientes (b0, a1, a2) de un pasabanda de pico 0 dB (RBJ) normalizados por a0."""
    center_freq = min(max(center_freq, 100.0), 0.45 * sample_rate)
    bandwidth = max(bandwidth, 100.0)
    w0 = 2.0 * math.pi * center_freq / sample_rate
    alpha = math.sin(w0) * bandwidth / (2.0 * center_freq)
    a0 = 1.0 + alpha
    return alpha / a0, -2.0 * math.cos(w0) / a0, (1.0 - alpha) / a0


def _glottal_harmonics() -> List[complex]:
    if not _GLOTTAL_HARMONICS:
        n_size = _GLOTTAL_TABLE_SIZE
        for k in range(1, n_size // 2):
            acc = 0j
            for n, g in enumerate(_GLOTTAL_TABLE):
                acc += g * cmath.exp(-2j * math.pi * k * n / n_size)
            _GLOTTAL_HARMONICS.append(acc / n_size)
    return _GLOTTAL_HARMONICS


def _calibration_gains(params: AcousticParameters, sample_rate: int) -> Tuple[float, float]:
    """
    Ganancias que llevan las ramas sonora y de ruido de un simbolo a RMS unitario,
    calculadas analiticamente a partir de la respuesta en frecuencia de los filtros.
    """
    key = (sample_rate, params.symbol)
    cached = _CALIBRATION_CACHE.get(key)
    if cached is not None:
        return cached

    voice_gain = 0.0
    if params.voicing_amplitude > 0.0 and params.f1_hz > 0.0:
        resonators = [
            _resonator_coeffs(f, bw, sample_rate)
            for f, bw in (
                (params.f1_hz, params.bw1_hz),
                (params.f2_hz, params.bw2_hz),
                (params.f3_hz, params.bw3_hz),
                (params.f4_hz, 250.0),
            )
        ]
        power = 0.0
        for k, coef in enumerate(_glottal_harmonics(), start=1):
            freq = k * REFERENCE_F0_HZ
            if freq >= 0.5 * sample_rate:
                break
            z1 = cmath.exp(-2j * math.pi * freq / sample_rate)
            h = 1.0 - z1
            for a, b, c in resonators:
                h *= a / (1.0 - b * z1 - c * z1 * z1)
            power += 2.0 * abs(coef) ** 2 * abs(h) ** 2
        voice_gain = 1.0 / math.sqrt(power) if power > 0.0 else 0.0

    noise_gain = 0.0
    if params.noise_amplitude > 0.0 and params.noise_center_freq > 0.0:
        b0, a1, a2 = _bandpass_coeffs(params.noise_center_freq, params.noise_bandwidth, sample_rate)
        points = 256
        acc = 0.0
        for i in range(points):
            z1 = cmath.exp(-1j * math.pi * (i + 0.5) / points)
            h = b0 * (1.0 - z1 * z1) / (1.0 + a1 * z1 + a2 * z1 * z1)
            acc += abs(h) ** 2
        power = acc / points / 3.0  # varianza del ruido uniforme [-1, 1]
        noise_gain = 1.0 / math.sqrt(power) if power > 0.0 else 0.0

    _CALIBRATION_CACHE[key] = (voice_gain, noise_gain)
    return voice_gain, noise_gain


def _smooth(track: Sequence[float], tau_ms: float) -> List[float]:
    """Suavizado exponencial de ida y vuelta (sin desfase) de una pista de parametros."""
    if not track:
        return []
    alpha = 1.0 - math.exp(-FRAME_MS / tau_ms)
    out = list(track)
    for i in range(1, len(out)):
        out[i] = out[i - 1] + alpha * (out[i] - out[i - 1])
    for i in range(len(out) - 2, -1, -1):
        out[i] = out[i + 1] + alpha * (out[i] - out[i + 1])
    return out


def _boundaries_from_text(text: str, words: Sequence[str]) -> List[str]:
    """Clasifica la frontera prosodica tras cada palabra segun la puntuacion del texto original."""
    spans: List[Optional[Tuple[int, int]]] = []
    cursor = 0
    for w in words:
        idx = text.find(w, cursor) if w else -1
        if idx < 0:
            spans.append(None)
            continue
        spans.append((idx, idx + len(w)))
        cursor = idx + len(w)

    boundaries: List[str] = []
    for i, span in enumerate(spans):
        if span is None:
            boundaries.append("word")
            continue
        next_start = len(text)
        for later in spans[i + 1:]:
            if later is not None:
                next_start = later[0]
                break
        gap = text[span[1]:next_start]
        if "?" in gap:
            boundaries.append("question")
        elif any(ch in _MAJOR_PUNCTUATION for ch in gap):
            boundaries.append("major")
        elif any(ch in _MINOR_PUNCTUATION for ch in gap):
            boundaries.append("minor")
        else:
            boundaries.append("word")
    return boundaries


@dataclass
class _Phone:
    symbol: str
    params: AcousticParameters
    stressed: bool
    syllable: int
    long: bool = False


@dataclass
class _Segment:
    params: Optional[AcousticParameters]
    frames: int
    stressed: bool = False
    phrase_final: bool = False
    boundary: str = "word"


def _parse_ipa_word(ipa: str) -> List[_Phone]:
    """Segmenta una palabra AFI en fonos con su silaba y acento."""
    phones: List[_Phone] = []
    syllable = 0
    stressed = False
    i = 0
    n = len(ipa)
    while i < n:
        ch = ipa[i]
        if ch in ("ˈ", "ˌ", "."):
            if phones and phones[-1].syllable == syllable:
                syllable += 1
            stressed = ch == "ˈ"
            i += 1
            continue
        if ch == "ː":
            if phones:
                phones[-1].long = True
            i += 1
            continue

        sym = next((m for m in _MULTI_CHAR_SYMBOLS if ipa.startswith(m, i)), ch)
        i += len(sym)
        if 0x0300 <= ord(sym[0]) <= 0x036F or sym in ("ʰ", "ʲ", "ʷ", "ˀ"):
            # Diacritico suelto: se agrega al fono previo si existe en la tabla
            if phones:
                combined = phones[-1].symbol + sym
                if combined in IPA_ACOUSTIC_TABLE:
                    phones[-1].symbol = combined
                    phones[-1].params = get_acoustic_parameters(combined)
            continue
        phones.append(_Phone(sym, get_acoustic_parameters(sym), stressed, syllable))
    return phones


class IPAFormantSynthesizer:
    """
    Sintetizador formántico determinista basado estrictamente en la cadena de simbolos AFI.
    Permite auditar acusticamente las diferencias sutiles entre variantes dialectales
    (ej. distincion [s] vs [θ], aspiracion [h], lambdacismo [l], sheismo [ʃ], etc.).

    `speech_rate` regula el tempo: 1.0 es una lectura moderada (~4 silabas/s),
    0.75 una diccion pausada y 1.25 un habla fluida.
    """

    def __init__(self, sample_rate: int = 22050, speech_rate: float = 1.0) -> None:
        if speech_rate <= 0.0:
            raise ValueError("speech_rate debe ser positivo.")
        self.sample_rate = sample_rate
        self.speech_rate = min(max(speech_rate, MIN_SPEECH_RATE), MAX_SPEECH_RATE)
        self.frame_samples = max(1, int(round(sample_rate * FRAME_MS / 1000.0)))

    # ------------------------------------------------------------------
    # Planificacion temporal y prosodica
    # ------------------------------------------------------------------
    def _ms_to_frames(self, ms: float) -> int:
        return max(1, int(round(ms * self.sample_rate / (1000.0 * self.frame_samples))))

    def _phone_duration_ms(self, phone: _Phone, phrase_final: bool) -> float:
        p = phone.params
        rate = self.speech_rate
        if phone.symbol in VOWELS:
            dur = p.duration_ms * _VOWEL_TEMPO
            if phone.stressed:
                dur *= 1.25
            if phrase_final:
                dur *= 1.35
            dur /= rate
            minimum = 40.0
        else:
            dur = p.duration_ms * _CONSONANT_TEMPO
            if phone.stressed:
                dur *= 1.08
            if phrase_final:
                dur *= 1.15
            # Las consonantes se comprimen menos que las vocales al acelerar
            dur /= rate ** 0.6
            minimum = 20.0 if phone.symbol in TAPS else 35.0
        if phone.long:
            dur *= 1.6
        return max(minimum, dur)

    def _plan_segments(self, words: Sequence[Tuple[str, str]]) -> Tuple[List[_Segment], List[Tuple[int, int]]]:
        """
        Convierte palabras AFI con su frontera posterior en segmentos temporizados.
        Devuelve los segmentos y el intervalo de tramas [inicio, fin) de cada palabra.
        """
        segments: List[_Segment] = []
        word_spans: List[Tuple[int, int]] = []
        frame_cursor = 0

        for idx, (ipa, boundary) in enumerate(words):
            phones = _parse_ipa_word(ipa.strip("/[] "))
            is_last_word = idx == len(words) - 1
            ends_phrase = boundary != "word" or is_last_word
            last_syllable = phones[-1].syllable if phones else -1

            start = frame_cursor
            for ph in phones:
                final = ends_phrase and ph.syllable == last_syllable
                frames = self._ms_to_frames(self._phone_duration_ms(ph, final))
                segments.append(_Segment(ph.params, frames, ph.stressed, final, boundary))
                frame_cursor += frames
            word_spans.append((start, frame_cursor))

            if not is_last_word:
                pause_ms = _PAUSE_MS.get(boundary, _PAUSE_MS["word"]) / self.speech_rate ** 1.25
                frames = self._ms_to_frames(pause_ms)
                segments.append(_Segment(None, frames, boundary=boundary))
                frame_cursor += frames

        return segments, word_spans

    def _build_tracks(self, segments: Sequence[_Segment]) -> Dict[str, List[float]]:
        """Genera las pistas de parametros por trama (formantes, F0, amplitudes)."""
        sr = self.sample_rate
        names = ("f1", "f2", "f3", "f4", "b1", "b2", "b3", "nf", "nb")
        targets: Dict[str, List[Optional[float]]] = {k: [] for k in names}
        av: List[float] = []
        an: List[float] = []
        f0: List[float] = []

        # Contorno de F0 por frase: declinacion, prominencia tonica y tonema final
        phrase_frames = 0
        phrase: List[Tuple[_Segment, int]] = []

        def flush_phrase(final_boundary: str) -> None:
            nonlocal phrase_frames
            total = max(1, phrase_frames)
            pos = 0
            final_total = sum(s.frames for s, _ in phrase if s.phrase_final) or 1
            final_pos = 0
            for seg, _ in phrase:
                for _k in range(seg.frames):
                    rel = pos / total
                    value = REFERENCE_F0_HZ * (1.07 - 0.14 * rel)
                    if seg.params is not None:
                        value *= seg.params.f0_hz / 120.0 if seg.params.f0_hz > 0.0 else 1.0
                        if seg.stressed:
                            value *= 1.10
                        if seg.phrase_final:
                            t = final_pos / final_total
                            if final_boundary == "question":
                                value *= 1.0 + 0.32 * t
                            elif final_boundary == "minor":
                                value *= 1.0 + 0.06 * t
                            else:
                                value *= 1.0 - 0.14 * t
                            final_pos += 1
                    f0.append(value)
                    pos += 1
            phrase.clear()
            phrase_frames = 0

        for seg in segments:
            if seg.params is None and seg.boundary != "word":
                flush_phrase(seg.boundary)
                f0.extend([f0[-1] if f0 else REFERENCE_F0_HZ] * seg.frames)
            else:
                phrase.append((seg, seg.frames))
                phrase_frames += seg.frames
        if phrase:
            last_boundary = next((s.boundary for s, _ in reversed(phrase) if s.params is not None), "major")
            flush_phrase("question" if last_boundary == "question" else "major")

        for seg in segments:
            p = seg.params
            n = seg.frames
            if p is None:
                for k in names:
                    targets[k].extend([None] * n)
                av.extend([0.0] * n)
                an.extend([0.0] * n)
                continue

            values = (p.f1_hz, p.f2_hz, p.f3_hz, p.f4_hz, p.bw1_hz, p.bw2_hz, p.bw3_hz,
                      p.noise_center_freq if p.noise_center_freq > 0.0 else 3000.0,
                      p.noise_bandwidth)
            for k, v in zip(names, values):
                targets[k].extend([v] * n)

            level = 10.0 ** (get_relative_intensity_db(p.symbol) / 20.0)
            gv, gn = _calibration_gains(p, sr)
            va = p.voicing_amplitude if p.f1_hz > 0.0 else 0.0
            na = p.noise_amplitude if p.noise_center_freq > 0.0 else 0.0
            norm = math.sqrt(va * va + na * na) or 1.0
            voice = level * va * gv / norm
            noise = level * na * gn / norm

            seg_av, seg_an = self._articulation_pattern(p.symbol, n, voice, noise)
            av.extend(seg_av)
            an.extend(seg_an)

        tracks: Dict[str, List[float]] = {}
        for k in names:
            tracks[k] = self._fill_gaps(targets[k])
        tracks["f1"] = _smooth(tracks["f1"], 12.0)
        tracks["f2"] = _smooth(tracks["f2"], 14.0)
        tracks["f3"] = _smooth(tracks["f3"], 14.0)
        tracks["f4"] = _smooth(tracks["f4"], 14.0)
        for k in ("b1", "b2", "b3"):
            tracks[k] = _smooth(tracks[k], 12.0)
        tracks["nf"] = _smooth(tracks["nf"], 4.0)
        tracks["nb"] = _smooth(tracks["nb"], 4.0)
        tracks["f0"] = _smooth(f0, 30.0)
        tracks["av"] = _smooth(av, 3.0)
        tracks["an"] = _smooth(an, 2.5)
        return tracks

    @staticmethod
    def _fill_gaps(track: List[Optional[float]]) -> List[float]:
        """Las pausas mantienen la postura articulatoria vecina (sin barridos espurios)."""
        out: List[float] = []
        last: Optional[float] = next((v for v in track if v is not None), 500.0)
        for v in track:
            if v is not None:
                last = v
            out.append(last if last is not None else 500.0)
        return out

    @staticmethod
    def _articulation_pattern(symbol: str, n: int, voice: float, noise: float) -> Tuple[List[float], List[float]]:
        """Estructura interna del segmento: oclusion + explosion, vibraciones, etc."""
        if symbol in VOICELESS_STOPS:
            closure = int(n * 0.60)
            burst = n - closure
            av = [0.0] * n
            an = [0.0] * closure + [
                noise * (1.0 if i < 4 else max(0.2, 1.0 - (i - 4) / max(1, burst - 4)))
                for i in range(burst)
            ]
            return av, an
        if symbol in VOICED_STOPS:
            closure = int(n * 0.65)
            release = n - closure
            av = [voice * 0.35] * closure + [voice] * release
            an = [0.0] * closure + [noise * max(0.0, 1.0 - i / max(1, release)) for i in range(release)]
            return av, an
        if symbol in AFFRICATES:
            closure = int(n * 0.35)
            bar = 0.35 if voice > 0.0 else 0.0
            av = [voice * bar] * closure + [voice] * (n - closure)
            an = [0.0] * closure + [noise] * (n - closure)
            return av, an
        if symbol in TAPS:
            lo, hi = int(n * 0.30), int(n * 0.75)
            av = [voice * (0.3 if lo <= i < hi else 1.0) for i in range(n)]
            return av, [noise] * n
        if symbol in TRILLS:
            cycles = max(2, round(n * FRAME_MS / 28.0))
            av = [voice * (0.3 + 0.7 * (0.5 + 0.5 * math.cos(2.0 * math.pi * cycles * i / n))) for i in range(n)]
            return av, [noise] * n
        return [voice] * n, [noise] * n

    # ------------------------------------------------------------------
    # Renderizado de la señal
    # ------------------------------------------------------------------
    def _render(self, tracks: Dict[str, List[float]]) -> List[float]:
        sr = self.sample_rate
        fs = self.frame_samples
        n_frames = len(tracks["av"])
        out: List[float] = []
        table = _GLOTTAL_TABLE
        table_size = _GLOTTAL_TABLE_SIZE
        noise_table = _NOISE_TABLE
        noise_mask = _NOISE_TABLE_SIZE - 1

        phase = 0.0
        noise_idx = 0
        r1a = r1b = r2a = r2b = r3a = r3b = r4a = r4b = 0.0
        prev_voice = 0.0
        nx1 = nx2 = ny1 = ny2 = 0.0
        frame_sec = fs / sr

        for f in range(n_frames):
            av0 = tracks["av"][f]
            an0 = tracks["an"][f]
            av1 = tracks["av"][f + 1] if f + 1 < n_frames else av0
            an1 = tracks["an"][f + 1] if f + 1 < n_frames else an0
            t = f * frame_sec
            flutter = 1.0 + 0.006 * (math.sin(2 * math.pi * 12.7 * t) + math.sin(2 * math.pi * 7.1 * t)
                                     + math.sin(2 * math.pi * 4.7 * t)) / 3.0
            inc = tracks["f0"][f] * flutter * table_size / sr

            voiced = av0 > 1e-6 or av1 > 1e-6
            noisy = an0 > 1e-6 or an1 > 1e-6
            if not voiced and not noisy:
                phase = (phase + inc * fs) % table_size
                noise_idx = (noise_idx + fs) & noise_mask
                r1a = r1b = r2a = r2b = r3a = r3b = r4a = r4b = 0.0
                prev_voice = 0.0
                nx1 = nx2 = ny1 = ny2 = 0.0
                out.extend([0.0] * fs)
                continue

            a1, b1, c1 = _resonator_coeffs(tracks["f1"][f], tracks["b1"][f], sr)
            a2, b2, c2 = _resonator_coeffs(tracks["f2"][f], tracks["b2"][f], sr)
            a3, b3, c3 = _resonator_coeffs(tracks["f3"][f], tracks["b3"][f], sr)
            a4, b4, c4 = _resonator_coeffs(tracks["f4"][f], 250.0, sr)
            nb0, na1, na2 = _bandpass_coeffs(tracks["nf"][f], tracks["nb"][f], sr)
            dav = (av1 - av0) / fs
            dan = (an1 - an0) / fs
            amp_v = av0
            amp_n = an0

            for _ in range(fs):
                sample = 0.0
                if voiced:
                    g = table[int(phase)]
                    phase += inc
                    if phase >= table_size:
                        phase -= table_size
                    y = a1 * g + b1 * r1a + c1 * r1b
                    r1b = r1a
                    r1a = y
                    y = a2 * y + b2 * r2a + c2 * r2b
                    r2b = r2a
                    r2a = y
                    y = a3 * y + b3 * r3a + c3 * r3b
                    r3b = r3a
                    r3a = y
                    y = a4 * y + b4 * r4a + c4 * r4b
                    r4b = r4a
                    r4a = y
                    sample = amp_v * (y - prev_voice)
                    prev_voice = y
                    amp_v += dav
                else:
                    phase += inc
                    if phase >= table_size:
                        phase -= table_size
                if noisy:
                    x = noise_table[noise_idx]
                    noise_idx = (noise_idx + 1) & noise_mask
                    yn = nb0 * (x - nx2) - na1 * ny1 - na2 * ny2
                    nx2 = nx1
                    nx1 = x
                    ny2 = ny1
                    ny1 = yn
                    sample += amp_n * yn
                    amp_n += dan
                else:
                    noise_idx = (noise_idx + 1) & noise_mask
                out.append(sample)

            if not voiced:
                r1a = r1b = r2a = r2b = r3a = r3b = r4a = r4b = 0.0
                prev_voice = 0.0
            if not noisy:
                nx1 = nx2 = ny1 = ny2 = 0.0

        return out

    def _master(self, samples: List[float]) -> List[float]:
        """
        Masterizacion perceptiva: filtro antizumbido a 60 Hz, normalizacion de la
        sonoridad del habla activa a -16 dBFS RMS y techo de pico a -1 dBFS.
        """
        sr = self.sample_rate
        lead = [0.0] * int(_LEAD_IN_MS * sr / 1000.0)
        tail = [0.0] * int(_TAIL_MS * sr / 1000.0)
        if not samples:
            return lead + tail

        r = math.exp(-2.0 * math.pi * 60.0 / sr)
        x1 = y1 = 0.0
        filtered: List[float] = []
        for x in samples:
            y1 = x - x1 + r * y1
            x1 = x
            filtered.append(y1)

        block = max(1, int(0.020 * sr))
        powers = [
            sum(v * v for v in filtered[i:i + block]) / len(filtered[i:i + block])
            for i in range(0, len(filtered), block)
        ]
        loudest = max(powers) if powers else 0.0
        active = [p for p in powers if p > loudest * 0.01]
        peak = max(abs(v) for v in filtered)
        if not active or peak <= 0.0:
            return lead + filtered + tail

        active_rms = math.sqrt(sum(active) / len(active))
        gain = (10.0 ** (_TARGET_RMS_DBFS / 20.0)) / active_rms
        gain = min(gain, _PEAK_CEILING / peak)
        return lead + [v * gain for v in filtered] + tail

    def _synthesize_words(self, words: Sequence[Tuple[str, str]]) -> Tuple[List[float], List[Tuple[int, int]]]:
        segments, spans = self._plan_segments(words)
        samples = self._master(self._render(self._build_tracks(segments)))
        lead = int(_LEAD_IN_MS * self.sample_rate / 1000.0)
        sample_spans = [(lead + s * self.frame_samples, lead + e * self.frame_samples) for s, e in spans]
        return samples, sample_spans

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------
    def synthesize_ipa_string(
        self,
        ipa_str: str,
        is_stressed_word: bool = False
    ) -> List[float]:
        """
        Parsea una cadena en notacion AFI (con marcas de acento ˈ, puntos silabicos,
        espacios entre palabras y barras prosodicas | ‖) y genera el arreglo continuo
        de muestras PCM normalizadas.
        """
        clean_ipa = ipa_str.strip("/[] ")
        if not clean_ipa:
            return [0.0] * int(0.05 * self.sample_rate)
        if is_stressed_word and "ˈ" not in clean_ipa:
            clean_ipa = "ˈ" + clean_ipa

        words: List[Tuple[str, str]] = []
        token = ""
        for ch in clean_ipa + " ":
            if ch in (" ", "-", "_", "|", "‖"):
                if token:
                    words.append((token, "word"))
                    token = ""
                if words and ch in ("|", "‖"):
                    words[-1] = (words[-1][0], "minor" if ch == "|" else "major")
            else:
                token += ch
        if not words:
            return [0.0] * int(0.05 * self.sample_rate)

        samples, _ = self._synthesize_words(words)
        return samples

    def to_wav_bytes(self, samples: List[float]) -> bytes:
        """
        Empaqueta un arreglo de muestras continuas [-1.0, 1.0] en un flujo binario WAV
        canónico PCM a 16-bits mono (22.050 Hz) sin almacenamiento en disco.
        """
        if not samples:
            samples = [0.0] * 100

        # Normalizacion de pico para evitar clipping
        max_val = max(abs(s) for s in samples) if samples else 1.0
        norm_factor = 0.90 / max_val if max_val > 0.90 else 1.0

        byte_io = io.BytesIO()
        with wave.open(byte_io, "wb") as wav_file:
            wav_file.setnchannels(1)       # Mono
            wav_file.setsampwidth(2)      # 16-bit PCM (2 bytes por muestra)
            wav_file.setframerate(self.sample_rate)

            raw_frames = bytearray()
            for s in samples:
                val = int(round(max(-1.0, min(1.0, s * norm_factor)) * 32767.0))
                raw_frames.extend(struct.pack("<h", val))

            wav_file.writeframes(raw_frames)

        return byte_io.getvalue()

    def synthesize_word(
        self,
        word: str,
        dialect: Optional[Dialect] = None
    ) -> bytes:
        """Transcribe una palabra y genera directamente su audio WAV."""
        transducer = G2PTransducer(default_dialect=dialect)
        result = transducer.transcribe_word(word, dialect=dialect)
        samples = self.synthesize_ipa_string(result.syllabified_ipa)
        return self.to_wav_bytes(samples)

    def synthesize_text(
        self,
        text: str,
        dialect: Optional[Dialect] = None
    ) -> bytes:
        """Transcribe un verso u oracion completa y genera su audio WAV continuo."""
        wav_bytes, _ = self.synthesize_text_with_timings(text, dialect=dialect)
        return wav_bytes

    def synthesize_text_with_timings(
        self,
        text: str,
        dialect: Optional[Dialect] = None
    ) -> Tuple[bytes, List[dict]]:
        """
        Transcribe un texto verso a verso, genera el audio continuo WAV
        y computa las marcas temporales exactas (start_time, end_time) para cada palabra.
        Las pausas y la entonacion se derivan de la puntuacion y los saltos de verso.
        """
        transducer = G2PTransducer(default_dialect=dialect)
        results = transducer.transcribe_text(text, dialect=dialect)
        if not results:
            return self.to_wav_bytes([]), []

        boundaries = _boundaries_from_text(text, [r.prosodic_word.original_text for r in results])
        words = [(r.syllabified_ipa, b) for r, b in zip(results, boundaries)]
        samples, spans = self._synthesize_words(words)

        word_timings: List[dict] = []
        for r, (start, end) in zip(results, spans):
            word_timings.append({
                "word": r.prosodic_word.original_text,
                "normalized_word": r.prosodic_word.normalized_text,
                "ipa": r.syllabified_ipa,
                "start_time": round(start / self.sample_rate, 3),
                "end_time": round(end / self.sample_rate, 3)
            })

        return self.to_wav_bytes(samples), word_timings


def synthesize_ipa_to_wav(
    ipa_sequence: str,
    sample_rate: int = 22050,
    speech_rate: float = 1.0
) -> bytes:
    """Funcion auxiliar directa para sintetizar cualquier cadena AFI a WAV."""
    synthesizer = IPAFormantSynthesizer(sample_rate=sample_rate, speech_rate=speech_rate)
    samples = synthesizer.synthesize_ipa_string(ipa_sequence)
    return synthesizer.to_wav_bytes(samples)
