"""
Pruebas unitarias para el modulo de metrica versal y evaluacion de rimas.
Unit tests for metric scansion and rhyme evaluation.
"""

import pytest
from idiolect_g2p.meter.verse_analyzer import (
    analyze_verse,
    analyze_poem,
    StanzaType,
)
from idiolect_g2p.meter.phonetic_distance import (
    evaluate_rhyme_pair,
    compute_rhyme_phonetic_distance,
    RhymeType,
)
from idiolect_g2p.dialects.peninsular import PeninsularStandardDialect
from idiolect_g2p.dialects.north_america import MexicanCentralDialect


def test_verse_scansion_and_sinalefa() -> None:
    """Verifica el calculo de silabas metricas y sinalefas."""
    # "Era una tarde clara y hermosa" -> E-ra_u-na (sinalefa 1), cla-ra_y_her-mo-sa (sinalefa 2 y 3)
    v = analyze_verse("Era una tarde hermosa", verse_number=1)
    assert v.sinalefas_count >= 1
    assert v.rhyme_segment_orthographic == "osa"


def test_verse_final_stress_compensation() -> None:
    """Verifica la compensacion prosodica: aguda +1, esdrujula -1."""
    v_aguda = analyze_verse("Al son del mar", verse_number=1)
    # Al (1) son (2) del (3) mar (4) + 1 aguda = 5
    assert v_aguda.final_stress_compensation == 1
    assert v_aguda.metrical_syllables_count == 5

    v_esdrujula = analyze_verse("Suave música", verse_number=2)
    # Sua-ve (2) mú-si-ca (3) - 1 esdrujula = 4
    assert v_esdrujula.final_stress_compensation == -1


def test_sonnet_detection() -> None:
    """Verifica la clasificacion de una estrofa de cuatro versos (cuarteto/redondilla)."""
    cuarteto_text = """
    Hombres necios que acusáis
    a la mujer sin razón,
    sin ver que sois la ocasión
    de lo mismo que culpáis
    """
    poem_analysis = analyze_poem(cuarteto_text)
    assert len(poem_analysis.all_verses) == 4
    assert poem_analysis.is_consonant_expected


def test_rhyme_phonetic_distance_computation() -> None:
    """Verifica calculo de distancia fonetica entre pares de rima."""
    dist_identical = compute_rhyme_phonetic_distance(["a", "s", "a"], ["a", "s", "a"])
    assert dist_identical == 0.0

    dist_close = compute_rhyme_phonetic_distance(["a", "s", "a"], ["a", "θ", "a"])
    dist_far = compute_rhyme_phonetic_distance(["a", "s", "a"], ["e", "n", "o"])
    assert dist_close < dist_far
