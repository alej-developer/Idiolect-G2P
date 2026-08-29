"""
Pruebas unitarias para el modulo de sintesis acustica basada en AFI.
Unit tests for the IPA-based acoustic synthesizer.
"""

import io
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
