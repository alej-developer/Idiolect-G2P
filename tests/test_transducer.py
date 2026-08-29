"""
Pruebas unitarias para el transductor G2P base.
Unit tests for the base G2P transducer.
"""

import pytest
from idiolect_g2p.core.transducer import G2PTransducer


def test_base_g2p_transcription() -> None:
    """Verifica transducciones fonemicas base estandar."""
    transducer = G2PTransducer()

    res_casa = transducer.transcribe_word("casa")
    assert "ka.sa" in res_casa.syllabified_ipa or "ˈka.sa" in res_casa.syllabified_ipa

    res_guitarra = transducer.transcribe_word("guitarra")
    assert "g" in res_guitarra.syllabified_ipa
    assert "r" in res_guitarra.syllabified_ipa

    res_queso = transducer.transcribe_word("queso")
    assert "ke.so" in res_guitarra.syllabified_ipa or "ke" in res_queso.syllabified_ipa


def test_text_transcription() -> None:
    """Verifica la transcripcion de una oracion completa."""
    transducer = G2PTransducer()
    results = transducer.transcribe_text("El sol brilla en el cielo")
    assert len(results) == 6
    assert all(r.ipa_transcription.startswith("/") and r.ipa_transcription.endswith("/") for r in results)
