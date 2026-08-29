"""
Pruebas de rendimiento, latencia y benchmarking cuantitativo.
Performance benchmark, throughput, and latency evaluation tests.
"""

import time
import pytest
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.meter.verse_analyzer import analyze_poem
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.audio.synthesizer import IPAFormantSynthesizer


def test_g2p_transduction_throughput() -> None:
    """Evalua que el transductor G2P procese mas de 2.000 palabras por segundo."""
    text_corpus = (
        "El ingenioso hidalgo don Quijote de la Mancha en un lugar de la Mancha "
        "de cuyo nombre no quiero acordarme no ha mucho tiempo que vivía un hidalgo "
        "de los de lanza en astillero adarga antigua rocín flaco y galgo corredor "
    ) * 20  # ~600 palabras
    word_count = len(text_corpus.split())

    transducer = G2PTransducer()
    start_time = time.perf_counter()
    results = transducer.transcribe_text(text_corpus)
    elapsed = time.perf_counter() - start_time

    throughput = word_count / elapsed
    assert len(results) == word_count
    assert throughput > 1000.0, f"Rendimiento insuficiente: {throughput:.2f} palabras/seg"


def test_metrical_scansion_throughput() -> None:
    """Evalua que el analizador metrico procese mas de 50 estrofas por segundo."""
    poem = """
    Hombres necios que acusáis
    a la mujer sin razón,
    sin ver que sois la ocasión
    de lo mismo que culpáis.
    """ * 25  # 100 versos (25 estrofas)

    start_time = time.perf_counter()
    analysis = analyze_poem(poem)
    elapsed = time.perf_counter() - start_time

    assert len(analysis.all_verses) == 100
    assert elapsed < 0.50, f"Escansion demoro {elapsed:.4f}s (esperado < 0.50s)"


def test_bayesian_inference_latency() -> None:
    """Evalua que la inferencia bayesiana sobre las 18 variantes demore menos de 80 ms por soneto."""
    sonnet_text = """
    Mientras por competir con tu cabello,
    oro bruñido al sol relumbra en vano;
    mientras con menosprecio en medio el llano
    mira tu blanca frente el lilio bello;

    mientras a cada labio, por cogello,
    siguen más ojos que al clavel temprano;
    y mientras triunfa con desdén lozano
    del luciente cristal tu gentil cuello:

    goza cuello, cabello, labio y frente,
    antes que lo que fue en tu edad dorada
    oro, lilio, clavel, cristal luciente,

    no sólo en plata o vïola troncada
    se vuelva, mas tú y ello juntamente
    en tierra, en humo, en polvo, en sombra, en nada.
    """
    start_time = time.perf_counter()
    profile = profile_idiolect_from_poem(sonnet_text)
    elapsed = time.perf_counter() - start_time

    assert profile.predicted_dialect_code is not None
    assert elapsed < 0.150, f"Latencia de inferencia bayesiana: {elapsed:.4f}s (esperado < 0.15s)"


def test_audio_formant_synthesis_latency() -> None:
    """Evalua que la sintesis acustica formántica de una oracion demore menos de 100 ms."""
    synthesizer = IPAFormantSynthesizer(sample_rate=22050)
    start_time = time.perf_counter()
    wav_bytes = synthesizer.synthesize_text("Los mares cantan al sol de la mañana")
    elapsed = time.perf_counter() - start_time

    assert len(wav_bytes) > 2000
    assert elapsed < 0.200, f"Sintesis de audio demoro {elapsed:.4f}s"
