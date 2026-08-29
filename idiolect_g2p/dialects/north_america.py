"""
Dialectos de Norteamerica: Mexicano Central / Altiplano y Mexicano Norteno / Chicano.
North American Spanish dialects: Central Mexican (Highland) and Northern Mexican / Chicano.

Basado en:
- Avelino, H. (2018). Illustrations of the IPA: Mexico City Spanish. JIPA 48(2).
- Lipski, J. M. (1994). Latin American Spanish.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class MexicanCentralDialect(Dialect):
    """
    Espanol Mexicano Central / Altiplano:
    - Seseo universal (/s/ predorsal).
    - Articulacion plena y muy tensa de consonantes en coda (resistencia a la aspiracion de /s/).
    - Debilitamiento o ensordecimiento de vocales atonas en contacto con /s/ ('vocales caedizas').
    - Articulacion africada alveolar lateral sorda [t͡ɬ] para el grupo 'tl' (sustrato nahuatl).
    - Yeismo estandar /ʝ/.
    - Fricativa velar sorda [x] suave.
    """

    def __init__(self) -> None:
        super().__init__(
            code="MX_CENTRAL",
            name="Mexicano Central / Altiplano",
            region=DialectRegion.NORTH_AMERICA,
            description="Variedad de tierras altas con seseo, fuerte tension consonantica en coda, vocales caedizas y /tl/ africada [t͡ɬ].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.8,
                glottal_j=0.0,
                affricate_tl=1.0,
            ),
            active_rules_description=[
                "Seseo fonologico universal (/s/ predorsal para 's', 'c', 'z').",
                "Conservacion y maxima tension de consonantes en coda silabica.",
                "Articulacion africada alveolar lateral sorda [t͡ɬ] para el grupo 'tl'.",
                "Debilitamiento alofonico de vocales atonas en contacto con sibilantes.",
                "Yeismo estandar [ʝ] / [j]."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            is_stressed = syll.stressed

            for phone_idx, p in enumerate(phones):
                new_p = p

                # Espirantizacion suave
                if p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                # Vocales caedizas: debilita vocales átonas /e/, /o/ en contacto con /s/
                elif not is_stressed and p in ("e", "o"):
                    if "s" in phones or (syl_idx > 0 and "s" in base_phonemes[syl_idx - 1]):
                        new_p = f"{p}̥"  # Vocal ensordecida / debilitada en AFI

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result


class MexicanNorthernChicanoDialect(Dialect):
    """
    Espanol Mexicano Norteno / Suroeste de EE.UU. / Chicano:
    - Seseo universal (/s/).
    - Fricativizacion o desoclusion de 'ch' (/t͡ʃ/ -> [ʃ]).
    - Conservacion tensa de consonantes en coda.
    """

    def __init__(self) -> None:
        super().__init__(
            code="MX_NORTH_CHICANO",
            name="Mexicano Norteño / Chicano",
            region=DialectRegion.NORTH_AMERICA,
            description="Variedad del norte de Mexico y suroeste de EE.UU. con seseo y fricativizacion de /t͡ʃ/ a [ʃ].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.2,
                glottal_j=0.0,
                affricate_tl=0.5,
            ),
            active_rules_description=[
                "Seseo fonologico universal (/s/).",
                "Fricativizacion de la africada /t͡ʃ/ ('ch') a fricativa postalveolar [ʃ].",
                "Conservacion de consonantes en coda.",
                "Espirantizacion aproximante intervocálica [β, ð, ɣ]."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []

            for phone_idx, p in enumerate(phones):
                new_p = p

                # Fricativizacion de 'ch'
                if p == "t͡ʃ":
                    new_p = "ʃ"
                elif p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result
