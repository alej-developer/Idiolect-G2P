"""
Pruebas unitarias para el módulo de fonotaxis post-léxica y sandhi externo.
Unit tests for post-lexical phonotactics and sandhi module.
"""

import pytest
from idiolect_g2p.core.sandhi import SandhiEngine, JunctureProcessType
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY


def test_sandhi_resyllabification_basic():
    """Verifica el reencadenamiento silábico interpalabra: Coda + Núcleo -> Ataque."""
    engine = SandhiEngine(enable_resyllabification=True, enable_voicing=False)
    
    # "las" [l, a, s] + "alas" [a, l, a, s]
    words_syllables = [
        [["l", "a", "s"]],              # 'las'
        [["a"], ["l", "a", "s"]]        # 'a-las'
    ]
    
    modified, junctures = engine.apply_sandhi(words_syllables)
    
    assert len(junctures) == 1
    assert junctures[0].process_type == JunctureProcessType.RESYLLABIFICATION
    assert junctures[0].input_left_coda == "s"
    assert junctures[0].output_phoneme == "s"
    
    # La coda de 'las' debe haber desaparecido: [l, a]
    assert modified[0][-1] == ["l", "a"]
    # El ataque de la primera sílaba de 'alas' ahora contiene 's': [s, a]
    assert modified[1][0] == ["s", "a"]


def test_sandhi_voicing_assimilation_s_to_z():
    """Verifica la resonorización asimilativa de sibilante ante consonante sonora: /s/ -> [z]."""
    engine = SandhiEngine(enable_resyllabification=True, enable_voicing=True)
    
    # "los" [l, o, s] + "mismos" [m, i, z, m, o, s]
    words_syllables = [
        [["l", "o", "s"]],
        [["m", "i", "s"], ["m", "o", "s"]]
    ]
    
    # Dialecto peninsular estándar (sin aspiración de coda)
    modified, junctures = engine.apply_sandhi(words_syllables, isogloss_vector={"aspiration_s": 0.0})
    
    assert len(junctures) == 1
    assert junctures[0].process_type == JunctureProcessType.VOICING_ASSIMILATION
    assert junctures[0].output_phoneme == "z"
    assert modified[0][-1][-1] == "z"


def test_sandhi_voicing_assimilation_with_aspiration():
    """Verifica que en un dialecto aspirante (e.g. Caribeño) la sibilante ante sonora se realice como [h]."""
    engine = SandhiEngine(enable_resyllabification=True, enable_voicing=True)
    
    words_syllables = [
        [["l", "o", "s"]],
        [["m", "i", "s"], ["m", "o", "s"]]
    ]
    
    modified, junctures = engine.apply_sandhi(words_syllables, isogloss_vector={"aspiration_s": 1.0})
    
    assert len(junctures) == 1
    assert junctures[0].output_phoneme == "h"
    assert modified[0][-1][-1] == "h"


def test_sandhi_nasal_assimilation_homorganic():
    """Verifica asimilación de /n/ en frontera ante bilabial [p] y velar [k]."""
    engine = SandhiEngine()
    
    # "un" [u, n] + "beso" [b, e, s, o] -> [u, m] + [b, e, s, o]
    w1 = [[["u", "n"]], [["b", "e"], ["s", "o"]]]
    mod1, junct1 = engine.apply_sandhi(w1)
    assert len(junct1) == 1
    assert junct1[0].process_type == JunctureProcessType.NASAL_ASSIMILATION
    assert junct1[0].output_phoneme == "m"
    assert mod1[0][-1][-1] == "m"

    # "con" [k, o, n] + "cariño" [k, a...] -> [k, o, ŋ]
    w2 = [[["k", "o", "n"]], [["k", "a"], ["ɾ", "i"], ["ɲ", "o"]]]
    mod2, junct2 = engine.apply_sandhi(w2)
    assert len(junct2) == 1
    assert junct2[0].output_phoneme == "ŋ"
    assert mod2[0][-1][-1] == "ŋ"


def test_sandhi_format_connected_ipa():
    """Verifica el formateo en cadena unificada con acentos prosódicos."""
    engine = SandhiEngine()
    words_syllables = [
        [["l", "o", "z"]],
        [["m", "i", "z"], ["m", "o", "s"]]
    ]
    stresses = [0, 0] # Primera sílaba tónica
    connected_str = engine.format_connected_ipa(words_syllables, stresses)
    assert connected_str == "ˈloz ˈmiz.mos"
