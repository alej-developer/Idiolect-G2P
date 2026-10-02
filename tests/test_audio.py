"""
Pruebas unitarias para el modulo de sintesis acustica basada en AFI.
Unit tests for the IPA-based acoustic synthesizer.
"""

import io
import math
import struct
import wave
import pytest
from idiolect_g2p.audio.synthesizer import (
    IPAFormantSynthesizer,
    synthesize_ipa_to_wav,
)
from idiolect_g2p.dialects.peninsular import PeninsularStandardDialect
from idiolect_g2p.dialects.caribbean import CaribbeanLambdacistDialect


def test_wav_header_and_structure() -> None:
    """Verifica que el flujo generado sea un archivo WAV valido a 22050 Hz, 16-bit mono."""
    wav_bytes = synthesize_ipa_to_wav("ˈka.sa", sample_rate=22050)
    assert len(wav_bytes) > 44  # Cabecera WAV minima

    # Verificar lectura de cabecera con el modulo wave estandar
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2  # 16-bit
        assert wf.getframerate() == 22050
        n_frames = wf.getnframes()
        assert n_frames > 0


def test_synthesize_word_with_dialects() -> None:
    """Verifica la sintesis de una palabra bajo diferentes variantes dialectales."""
    synth = IPAFormantSynthesizer(sample_rate=22050)

    # Peninsular
    wav_pen = synth.synthesize_word("caza", dialect=PeninsularStandardDialect())
    assert len(wav_pen) > 1000

    # Caribeño lambdacista
    wav_car = synth.synthesize_word("puerto", dialect=CaribbeanLambdacistDialect())
    assert len(wav_car) > 1000


def test_synthesize_full_sentence() -> None:
    """Verifica la sintesis continua de una oracion."""
    synth = IPAFormantSynthesizer(sample_rate=22050)
    wav_sentence = synth.synthesize_text("Los mares cantan al sol")
    assert len(wav_sentence) > 5000


def _speech_span(synth: IPAFormantSynthesizer, text: str) -> float:
    _, timings = synth.synthesize_text_with_timings(text)
    return timings[-1]["end_time"] - timings[0]["start_time"]


def test_speech_rate_controls_tempo() -> None:
    """Una velocidad menor alarga el enunciado y una mayor lo acorta."""
    text = "Los cazadores llegaron a la casa del puerto"
    slow = _speech_span(IPAFormantSynthesizer(speech_rate=0.75), text)
    moderate = _speech_span(IPAFormantSynthesizer(speech_rate=1.0), text)
    fast = _speech_span(IPAFormantSynthesizer(speech_rate=1.25), text)
    assert slow > moderate > fast

    syllables_per_second = 15 / moderate
    assert 3.5 <= syllables_per_second <= 4.8


def test_invalid_speech_rate_rejected() -> None:
    with pytest.raises(ValueError):
        IPAFormantSynthesizer(speech_rate=0.0)


def test_punctuation_inserts_prosodic_pauses() -> None:
    """La coma y el punto introducen pausas mayores que la juntura entre palabras."""
    synth = IPAFormantSynthesizer()
    _, plain = synth.synthesize_text_with_timings("hola amigo")
    _, comma = synth.synthesize_text_with_timings("hola, amigo")
    _, period = synth.synthesize_text_with_timings("hola. amigo")

    def gap(timings: list) -> float:
        return timings[1]["start_time"] - timings[0]["end_time"]

    assert gap(plain) < gap(comma) < gap(period)


def test_timings_are_monotonic_and_within_audio() -> None:
    synth = IPAFormantSynthesizer()
    wav_bytes, timings = synth.synthesize_text_with_timings("Mientras por competir con tu cabello, oro bruñido")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        total = wf.getnframes() / wf.getframerate()
    previous_end = 0.0
    for t in timings:
        assert previous_end <= t["start_time"] < t["end_time"] <= total
        previous_end = t["end_time"]


def _pcm(wav_bytes: bytes) -> list:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
    return [v / 32767.0 for v in struct.unpack(f"<{len(frames) // 2}h", frames)]


def test_no_clicks_and_comfortable_loudness() -> None:
    """Sin discontinuidades audibles, con sonoridad de voz estandar y margen de pico."""
    synth = IPAFormantSynthesizer()
    samples = _pcm(synth.synthesize_text("Los cazadores llegaron a la casa del puerto."))

    peak = max(abs(s) for s in samples)
    max_jump = max(abs(samples[i] - samples[i - 1]) for i in range(1, len(samples)))
    assert max_jump / peak < 0.5

    active = [s for s in samples if abs(s) > 1e-3]
    rms_dbfs = 20 * math.log10(math.sqrt(sum(s * s for s in active) / len(active)))
    assert -20.0 <= rms_dbfs <= -12.0
    assert max(abs(s) for s in samples) <= 0.90


def test_synthesis_is_deterministic() -> None:
    synth = IPAFormantSynthesizer()
    assert synth.synthesize_text("El sol de Alicante") == synth.synthesize_text("El sol de Alicante")
