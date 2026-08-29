"""
Metrica de distancia fonologica ponderada y evaluador de rimas.
Weighted phonological distance metric and rhyme evaluator.

Basado en:
- Clements, G. N., & Hume, E. V. (1995). The internal organization of speech sounds.
- Plechac, P. (2021). Versification and authorship attribution.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple, Dict, Optional, Final

from ..core.phonetics import Phoneme, get_phoneme, compute_phonetic_distance
from ..core.syllabifier import ProsodicWord, Syllable
from ..core.transducer import G2PTransducer, TransductionResult
from ..dialects.base import Dialect
from .verse_analyzer import Verse


class RhymeType(Enum):
    """Clasificacion cualitativa de la concordancia de rima."""
    CONSONANT = "Rima Consonante Perfecta"
    ASSONANT = "Rima Asonante"
    IMPERFECT_FORCED = "Rima Forzada / Alofonica"
    DEFECTIVE = "Sin Rima / Divergente"


@dataclass(frozen=True)
class RhymeMatch:
    """Evaluacion fonologica del par de rima entre dos versos bajo un dialecto."""
    verse_1_index: int
    verse_2_index: int
    word_1_text: str
    word_2_text: str
    ipa_1: str
    ipa_2: str
    rhyme_phones_1: List[str]
    rhyme_phones_2: List[str]
    phonetic_distance: float
    rhyme_type: RhymeType
    is_perfect_consonant: bool
    is_discriminant_pair: bool
    linguistic_explanation: str


def _extract_phonetic_rhyme_segment(
    trans_res: TransductionResult
) -> List[str]:
    """
    Extrae la lista de fonemas AFI del segmento de rima (a partir del nucleo tonico).
    """
    pword = trans_res.prosodic_word
    stressed_idx = pword.stressed_syllable_index
    syll_phonemes = trans_res.syllable_phonemes

    if not syll_phonemes or stressed_idx >= len(syll_phonemes):
        return []

    # Obtener los fonemas de la silaba tonica a partir de la primera vocal
    stressed_phones = syll_phonemes[stressed_idx]
    tonic_start_idx = 0

    # Localizar la primera vocal en la silaba tonica
    for idx, p_sym in enumerate(stressed_phones):
        p_obj = get_phoneme(p_sym)
        if p_obj.is_vowel():
            tonic_start_idx = idx
            break

    rhyme_phones = list(stressed_phones[tonic_start_idx:])

    # Anadir todos los fonemas de las silabas post-tonicas
    for post_idx in range(stressed_idx + 1, len(syll_phonemes)):
        rhyme_phones.extend(syll_phonemes[post_idx])

    return rhyme_phones


def compute_rhyme_phonetic_distance(
    phones1: List[str],
    phones2: List[str]
) -> float:
    """
    Calcula la distancia fonologica de Levenshtein ponderada por la Geometria de Rasgos
    de Clements & Hume (1995) entre dos secuencias de fonemas rimantes.
    """
    if phones1 == phones2:
        return 0.0

    len1, len2 = len(phones1), len(phones2)
    if len1 == 0:
        return float(len2)
    if len2 == 0:
        return float(len1)

    # Matriz de programacion dinamica
    dp = [[0.0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = float(i) * 0.8  # Coste de insercion/borrado
    for j in range(len2 + 1):
        dp[0][j] = float(j) * 0.8

    for i in range(1, len1 + 1):
        p1 = get_phoneme(phones1[i - 1])
        for j in range(1, len2 + 1):
            p2 = get_phoneme(phones2[j - 1])

            # Coste de sustitucion basado en la distancia por rasgos articulatorios
            sub_cost = compute_phonetic_distance(p1, p2)

            dp[i][j] = min(
                dp[i - 1][j] + 0.8,              # Borrado
                dp[i][j - 1] + 0.8,              # Insercion
                dp[i - 1][j - 1] + sub_cost     # Sustitucion ponderada
            )

    # Normalizar por la longitud maxima de la secuencia
    max_len = max(len1, len2)
    return dp[len1][len2] / max_len


def evaluate_rhyme_pair(
    v1: Verse,
    v2: Verse,
    dialect: Dialect,
    transducer: Optional[G2PTransducer] = None
) -> RhymeMatch:
    """
    Evalua cuantitativa y cualitativamente la rima entre dos versos
    bajo las reglas alofonicas del dialecto especificado.
    """
    trans = transducer or G2PTransducer(default_dialect=dialect)

    res1 = trans.transcribe_word(v1.last_word.original_text, dialect=dialect)
    res2 = trans.transcribe_word(v2.last_word.original_text, dialect=dialect)

    r_phones1 = _extract_phonetic_rhyme_segment(res1)
    r_phones2 = _extract_phonetic_rhyme_segment(res2)

    dist = compute_rhyme_phonetic_distance(r_phones1, r_phones2)

    # Clasificacion del tipo de rima segun la distancia fonologica
    if dist < 0.001:
        rhyme_t = RhymeType.CONSONANT
        is_perfect = True
        explanation = f"Rima consonante perfecta bajo {dialect.name} (distancia fonética = 0.00)."
    elif dist < 0.20:
        rhyme_t = RhymeType.IMPERFECT_FORCED
        is_perfect = False
        explanation = f"Rima alofónica o forzada bajo {dialect.name} (distancia = {dist:.2f})."
    else:
        # Verificar si coinciden las vocales (asonancia)
        vowels1 = [p for p in r_phones1 if get_phoneme(p).is_vowel()]
        vowels2 = [p for p in r_phones2 if get_phoneme(p).is_vowel()]
        if vowels1 == vowels2:
            rhyme_t = RhymeType.ASSONANT
            is_perfect = False
            explanation = f"Rima asonante legítima (núcleos vocálicos idénticos: {''.join(vowels1)})."
        else:
            rhyme_t = RhymeType.DEFECTIVE
            is_perfect = False
            explanation = f"Divergencia fonética significativa (distancia = {dist:.2f})."

    # Determinar si es un par discriminante clave (ej. seseo casa/caza, lambdacismo puerto/muelto)
    is_discriminant = False
    w1_lower = v1.last_word.normalized_text
    w2_lower = v2.last_word.normalized_text

    if ("z" in w1_lower or "z" in w2_lower) and ("s" in w1_lower or "s" in w2_lower):
        is_discriminant = True
    elif ("r" in w1_lower or "r" in w2_lower) and ("l" in w1_lower or "l" in w2_lower):
        is_discriminant = True
    elif ("ll" in w1_lower or "ll" in w2_lower) and ("y" in w1_lower or "y" in w2_lower):
        is_discriminant = True

    return RhymeMatch(
        verse_1_index=v1.verse_number,
        verse_2_index=v2.verse_number,
        word_1_text=v1.last_word.original_text,
        word_2_text=v2.last_word.original_text,
        ipa_1=res1.syllabified_ipa,
        ipa_2=res2.syllabified_ipa,
        rhyme_phones_1=r_phones1,
        rhyme_phones_2=r_phones2,
        phonetic_distance=dist,
        rhyme_type=rhyme_t,
        is_perfect_consonant=is_perfect,
        is_discriminant_pair=is_discriminant,
        linguistic_explanation=explanation
    )
