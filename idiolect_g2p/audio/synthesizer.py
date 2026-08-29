"""
Sintetizador acustico formántico determinista en Python puro.
Deterministic formant acoustic synthesizer in pure Python for IPA sequences.

Genera tramas PCM lineales a 16-bits mono (22.050 Hz) empaquetadas en formato WAV canónico.
"""

from __future__ import annotations
import math
import struct
import io
import wave
import random
from typing import List, Optional, Tuple, Sequence

from .acoustic_features import AcousticParameters, get_acoustic_parameters
from ..core.syllabifier import ProsodicWord, Syllable, syllabify_word
from ..core.transducer import G2PTransducer, TransductionResult
from ..dialects.base import Dialect


class IPAFormantSynthesizer:
    """
    Sintetizador formántico determinista basado estrictamente en la cadena de simbolos AFI.
    Permite auditar acusticamente las diferencias sutiles entre variantes dialectales
    (ej. distincion [s] vs [θ], aspiracion [h], lambdacismo [l], sheismo [ʃ], etc.).
    """

    def __init__(self, sample_rate: int = 22050) -> None:
        self.sample_rate = sample_rate

    def _generate_sine(self, freq: float, num_samples: int, start_phase: float = 0.0) -> Tuple[List[float], float]:
        """Genera una onda sinusoidal pura con continuidad de fase."""
        if freq <= 0.0:
            return [0.0] * num_samples, start_phase
        samples: List[float] = []
        phase = start_phase
        phase_increment = (2.0 * math.pi * freq) / self.sample_rate
        for _ in range(num_samples):
            samples.append(math.sin(phase))
            phase += phase_increment
            if phase > 2.0 * math.pi:
                phase -= 2.0 * math.pi
        return samples, phase

    def _generate_filtered_noise(
        self,
        center_freq: float,
        bandwidth: float,
        num_samples: int,
        seed: int = 42
    ) -> List[float]:
        """
        Genera ruido blanco pseudo-aleatorio filtrado en banda simple mediante
        un filtro resonador pasabanda IIR de segundo orden.
        """
        if center_freq <= 0.0 or bandwidth <= 0.0:
            return [0.0] * num_samples

        rng = random.Random(seed)
        # Coeficientes del resonador biquad
        r = math.exp(-math.pi * (bandwidth / self.sample_rate))
        omega = 2.0 * math.pi * (center_freq / self.sample_rate)
        c = 2.0 * r * math.cos(omega)
        r2 = r * r

        y1 = 0.0
        y2 = 0.0
        output: List[float] = []

        for _ in range(num_samples):
            # Fuente de ruido blanco [-1.0, 1.0]
            x = rng.uniform(-1.0, 1.0)
            # Filtro resonador IIR
            y0 = (1.0 - r) * x + c * y1 - r2 * y2
            y2 = y1
            y1 = y0
            output.append(y0)

        return output

    def _synthesize_phone(
        self,
        params: AcousticParameters,
        is_stressed: bool = False,
        is_end_of_word: bool = False
    ) -> List[float]:
        """
        Sintetiza la trama temporal de audio correspondiente a un fonema individual
        combinando osciladores formanticos (F1, F2, F3) y componentes de friccion.
        """
        # Ajuste prosodico de duracion y frecuencia fundamental F0 para silaba tonica
        duration_factor = 1.35 if is_stressed else 1.0
        if is_end_of_word:
            duration_factor *= 1.15

        actual_duration_ms = max(25.0, params.duration_ms * duration_factor)
        num_samples = int((actual_duration_ms / 1000.0) * self.sample_rate)

        # Curva de entonacion F0 (Frecuencia Fundamental)
        base_f0 = 135.0 if is_stressed else 115.0
        f0 = params.f0_hz if params.f0_hz > 0.0 else base_f0
        if is_stressed:
            f0 *= 1.20  # Elevacion de tono en silaba tonica

        # 1. Generacion de formantes armonicos (Fuente glotal resonante)
        samples_voice = [0.0] * num_samples
        if params.voicing_amplitude > 0.0 and params.f1_hz > 0.0:
            # Sintesis aditiva calibrada de los 4 formantes principales
            s_f1, _ = self._generate_sine(params.f1_hz, num_samples)
            s_f2, _ = self._generate_sine(params.f2_hz, num_samples)
            s_f3, _ = self._generate_sine(params.f3_hz, num_samples)
            s_f4, _ = self._generate_sine(params.f4_hz, num_samples)
            s_f0, _ = self._generate_sine(f0, num_samples)

            for i in range(num_samples):
                # Ponderacion formántica con caida espectral natural (-6 dB/octava)
                v = (
                    0.40 * s_f1[i] +
                    0.30 * s_f2[i] +
                    0.20 * s_f3[i] +
                    0.10 * s_f4[i]
                )
                # Modulacion de amplitud glotal F0
                v *= (0.7 + 0.3 * s_f0[i])
                samples_voice[i] = v * params.voicing_amplitude

        # 2. Generacion de componente de ruido / friccion
        samples_noise = [0.0] * num_samples
        if params.noise_amplitude > 0.0 and params.noise_center_freq > 0.0:
            raw_noise = self._generate_filtered_noise(
                center_freq=params.noise_center_freq,
                bandwidth=params.noise_bandwidth,
                num_samples=num_samples
            )
            for i in range(num_samples):
                samples_noise[i] = raw_noise[i] * params.noise_amplitude

        # 3. Suma y aplicacion de envolvente temporal trapezoidal (Ataque y Decaimiento)
        combined: List[float] = []
        attack_samples = max(1, int((params.attack_ms / 1000.0) * self.sample_rate))
        decay_samples = max(1, int((params.decay_ms / 1000.0) * self.sample_rate))

        for i in range(num_samples):
            # Calculo de ganancia de envolvente
            env = 1.0
            if i < attack_samples:
                env = i / attack_samples
            elif i > num_samples - decay_samples:
                env = (num_samples - i) / decay_samples

            sample_val = (samples_voice[i] + samples_noise[i]) * env
            combined.append(sample_val)

        return combined

    def synthesize_ipa_string(
        self,
        ipa_str: str,
        is_stressed_word: bool = False
    ) -> List[float]:
        """
        Parsea una cadena en notacion AFI (con marcas de acento ˈ y puntos .)
        y genera el arreglo continuo de muestras PCM normalizadas.
        """
        # Limpiar barras de transcripcion fonetica
        clean_ipa = ipa_str.strip("/[] ")
        if not clean_ipa:
            return [0.0] * int(0.05 * self.sample_rate)

        # Parsear simbolos AFI y marcadores prosodicos
        # Reconocimiento de digrafos complejos y alofonos con diacriticos
        multi_char_symbols = [
            "t͡ʃ", "t͡ʂ", "t͡ɬ", "s̺", "e̥", "o̥", "ts", "dz"
        ]

        audio_samples: List[float] = []
        i = 0
        n = len(clean_ipa)
        is_current_stressed = False

        while i < n:
            char = clean_ipa[i]

            # Marcador de acento prosodico primario
            if char == "ˈ":
                is_current_stressed = True
                i += 1
                continue

            # Frontera silabica (micro-pausa o transicion de 10 ms)
            if char == ".":
                is_current_stressed = False
                audio_samples.extend([0.0] * int(0.010 * self.sample_rate))
                i += 1
                continue

            if char in (" ", "-", "_"):
                is_current_stressed = False
                audio_samples.extend([0.0] * int(0.040 * self.sample_rate))
                i += 1
                continue

            # Comprobar si coincide con un simbolo multi-caracter
            matched_symbol: Optional[str] = None
            for mcs in multi_char_symbols:
                if clean_ipa.startswith(mcs, i):
                    matched_symbol = mcs
                    break

            if matched_symbol is not None:
                sym = matched_symbol
                i += len(matched_symbol)
            else:
                sym = char
                i += 1

            params = get_acoustic_parameters(sym)
            phone_samples = self._synthesize_phone(
                params=params,
                is_stressed=is_current_stressed,
                is_end_of_word=(i >= n)
            )
            audio_samples.extend(phone_samples)

        return audio_samples

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

            # Empaquetamiento binario optimizado con struct
            raw_frames = bytearray()
            for s in samples:
                val = int(max(-1.0, min(1.0, s * norm_factor)) * 32767.0)
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
        transducer = G2PTransducer(default_dialect=dialect)
        results = transducer.transcribe_text(text, dialect=dialect)
        all_samples: List[float] = []

        for idx, r in enumerate(results):
            word_samples = self.synthesize_ipa_string(r.syllabified_ipa)
            all_samples.extend(word_samples)
            # Pausa inter-palabra de 60 ms
            if idx < len(results) - 1:
                all_samples.extend([0.0] * int(0.060 * self.sample_rate))

        return self.to_wav_bytes(all_samples)


def synthesize_ipa_to_wav(
    ipa_sequence: str,
    sample_rate: int = 22050
) -> bytes:
    """Funcion auxiliar directa para sintetizar cualquier cadena AFI a WAV."""
    synthesizer = IPAFormantSynthesizer(sample_rate=sample_rate)
    samples = synthesizer.synthesize_ipa_string(ipa_sequence)
    return synthesizer.to_wav_bytes(samples)
