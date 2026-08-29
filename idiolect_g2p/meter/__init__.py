"""
Modulo de metrica versal, escansion y analisis fonologico de rimas.
Metrical scansion and phonological rhyme analysis module.
"""

from .verse_analyzer import (
    StanzaType,
    Verse,
    Stanza,
    PoemAnalysis,
    analyze_verse,
    analyze_poem,
)
from .phonetic_distance import (
    RhymeType,
    RhymeMatch,
    evaluate_rhyme_pair,
    compute_rhyme_phonetic_distance,
)

__all__ = [
    "StanzaType",
    "Verse",
    "Stanza",
    "PoemAnalysis",
    "analyze_verse",
    "analyze_poem",
    "RhymeType",
    "RhymeMatch",
    "evaluate_rhyme_pair",
    "compute_rhyme_phonetic_distance",
]
