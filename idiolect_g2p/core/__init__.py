"""
Modulo central de analisis fonetico, silabificacion y transduccion G2P.
Core phonetics, syllabification, and G2P transduction module.
"""

from .phonetics import (
    Phoneme,
    PhonemeType,
    PlaceOfArticulation,
    MannerOfArticulation,
    Phonation,
    VowelHeight,
    VowelBackness,
    VowelRounding,
    PhonologicalFeatures,
    PHONEME_INVENTORY,
    get_phoneme,
    compute_phonetic_distance,
)
from .syllabifier import (
    Syllable,
    ProsodicWord,
    SyllableNucleus,
    StressType,
    syllabify_word,
    syllabify_text,
)
from .transducer import (
    G2PTransducer,
    TransductionResult,
)

__all__ = [
    "Phoneme",
    "PhonemeType",
    "PlaceOfArticulation",
    "MannerOfArticulation",
    "Phonation",
    "VowelHeight",
    "VowelBackness",
    "VowelRounding",
    "PhonologicalFeatures",
    "PHONEME_INVENTORY",
    "get_phoneme",
    "compute_phonetic_distance",
    "Syllable",
    "ProsodicWord",
    "SyllableNucleus",
    "StressType",
    "syllabify_word",
    "syllabify_text",
    "G2PTransducer",
    "TransductionResult",
]
