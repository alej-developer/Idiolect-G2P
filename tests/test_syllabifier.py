"""
Pruebas unitarias para el silabificador fonotactico y analizador prosodico.
Unit tests for the phonotactic syllabifier and prosodic stress analyzer.
"""

import pytest
from idiolect_g2p.core.syllabifier import (
    syllabify_word,
    syllabify_text,
    StressType,
    SyllableNucleus,
)


def test_basic_syllabification() -> None:
    """Verifica silabificacion de palabras regulares."""
    w1 = syllabify_word("casa")
    assert w1.hyphenated == "ca-sa"
    assert w1.stress_type == StressType.PAROXYTONE
    assert w1.stressed_syllable.raw_text == "ca"

    w2 = syllabify_word("cantar")
    assert w2.hyphenated == "can-tar"
    assert w2.stress_type == StressType.OXYTONE
    assert w2.stressed_syllable.raw_text == "tar"

    w3 = syllabify_word("música")
    assert w3.hyphenated == "mú-si-ca"
    assert w3.stress_type == StressType.PROPAROXYTONE
    assert w3.stressed_syllable.raw_text == "mú"


def test_diphthongs_and_hiatuses() -> None:
    """Verifica diptongos e hiatos acentuales y formales."""
    # Diptongo creciente
    w_viaje = syllabify_word("viaje")
    assert w_viaje.hyphenated == "via-je"

    # Diptongo decreciente
    w_causa = syllabify_word("causa")
    assert w_causa.hyphenated == "cau-sa"

    # Hiato acentual (tilde disolvente)
    w_pais = syllabify_word("país")
    assert w_pais.hyphenated == "pa-ís"
    assert len(w_pais.syllables) == 2
    assert w_pais.stress_type == StressType.OXYTONE

    w_rio = syllabify_word("río")
    assert w_rio.hyphenated == "rí-o"
    assert len(w_rio.syllables) == 2

    # Hiato formal entre vocales abiertas
    w_teatro = syllabify_word("teatro")
    assert w_teatro.hyphenated == "te-a-tro"
    assert len(w_teatro.syllables) == 3

    w_poema = syllabify_word("poema")
    assert w_poema.hyphenated == "po-e-ma"
    assert len(w_poema.syllables) == 3


def test_consonant_clusters() -> None:
    """Verifica division de ataques complejos e inseparables."""
    w_pr = syllabify_word("precio")
    assert w_pr.hyphenated == "pre-cio"

    w_trans = syllabify_word("transporte")
    assert w_trans.hyphenated == "trans-por-te"

    w_const = syllabify_word("construir")
    assert w_const.hyphenated == "cons-truir"


def test_monosyllables() -> None:
    """Verifica clasificacion de monosilabos."""
    for word in ["pan", "sol", "mar", "él", "fe", "ya"]:
        w = syllabify_word(word)
        assert w.is_monosyllable
        assert w.stress_type == StressType.MONOSYLLABLE
