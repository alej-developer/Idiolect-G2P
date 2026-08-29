"""
Pruebas unitarias para el modulo de fonetica y rasgos distintivos.
Unit tests for phonetics and distinctive features module.
"""

import pytest
from idiolect_g2p.core.phonetics import (
    Phoneme,
    PhonemeType,
    PlaceOfArticulation,
    MannerOfArticulation,
    Phonation,
    PHONEME_INVENTORY,
    get_phoneme,
    compute_phonetic_distance,
)


def test_phoneme_inventory_integrity() -> None:
    """Verifica que el inventario contenga los fonemas canonicos del espanol."""
    essential_symbols = ["a", "e", "i", "o", "u", "p", "t", "k", "b", "d", "g", "s", "θ", "x", "m", "n", "ɲ", "l", "ʎ", "ɾ", "r"]
    for s in essential_symbols:
        assert s in PHONEME_INVENTORY, f"El fonema {s} debe estar presente en el inventario global."
        p = get_phoneme(s)
        assert p.symbol == s


def test_phonetic_distance_identity() -> None:
    """La distancia fonetica entre un fonema y si mismo debe ser 0.0."""
    for symbol in ["a", "s", "p", "θ", "l", "ɾ"]:
        p = get_phoneme(symbol)
        assert compute_phonetic_distance(p, p) == 0.0


def test_phonetic_distance_symmetry() -> None:
    """La distancia fonetica debe ser simetrica: d(A, B) == d(B, A)."""
    pairs = [("s", "θ"), ("l", "ɾ"), ("p", "b"), ("a", "e"), ("s", "p")]
    for s1, s2 in pairs:
        p1 = get_phoneme(s1)
        p2 = get_phoneme(s2)
        dist1 = compute_phonetic_distance(p1, p2)
        dist2 = compute_phonetic_distance(p2, p1)
        assert pytest.approx(dist1, 0.0001) == dist2


def test_phonetic_distance_hierarchy() -> None:
    """
    Verifica que fonemas cercanamente emparentados tengan menor distancia
    que fonemas completamente disimiles.
    """
    p_s = get_phoneme("s")
    p_theta = get_phoneme("θ")
    p_a = get_phoneme("a")

    dist_s_theta = compute_phonetic_distance(p_s, p_theta)
    dist_s_a = compute_phonetic_distance(p_s, p_a)

    # La distancia entre /s/ y /θ/ (ambas fricativas coronales) debe ser significativamente menor que entre /s/ y /a/
    assert dist_s_theta < dist_s_a
    assert dist_s_theta < 0.25
    assert dist_s_a > 0.40
