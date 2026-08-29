"""
Dialectos de Centroamerica: General y Costarricense.
Central American Spanish dialects: General and Costa Rican.

Basado en:
- Quesada Pacheco, M. A. (2000). El espanol de America Central.
- Lipski, J. M. (1994). Latin American Spanish.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class CentralAmericanGeneralDialect(Dialect):
    """
    Espanol Centroamericano General (Guatemala, El Salvador, Honduras, Nicaragua, Panama):
    - Seseo universal (/s/).
    - Aspiracion sistematica de /s/ en coda silabica ([h]).
    - Velarizacion de /n/ en posicion final de palabra ([ŋ]).
    - 'j' pronunciada como fricativa glotal o velar suave [h].
    """

    def __init__(self) -> None:
        super().__init__(
            code="CENTRAL_AMERICA_STD",
            name="Centroamericano General",
            region=DialectRegion.CENTRAL_AMERICA,
            description="Variedad centroamericana con seseo, aspiración de /s/ en coda [h] y velarización de nasal final [ŋ].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.9,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=1.0,
                vocalic_reduction=0.0,
                glottal_j=0.9,
                affricate_tl=0.2,
            ),
            active_rules_description=[
                "Seseo universal (/s/).",
                "Aspiracion de /s/ en coda silabica (/s/ -> [h]).",
                "Velarizacion de /n/ final de palabra a [ŋ].",
                "Fricativa glotal [h] para 'j'."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []
        num_sylls = len(word.syllables)

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            cod_len = len(syll.coda)
            num_phones = len(phones)
            coda_start_idx = num_phones - cod_len if cod_len > 0 else num_phones

            for phone_idx, p in enumerate(phones):
                new_p = p
                is_in_coda = (phone_idx >= coda_start_idx)

                if is_in_coda and p == "s":
                    new_p = "h"
                elif is_in_coda and p == "n" and syl_idx == num_sylls - 1:
                    new_p = "ŋ"
                elif p == "x":
                    new_p = "h"
                elif p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result


class CostaRicanDialect(Dialect):
    """
    Espanol Costarricense:
    - Seseo universal (/s/).
    - **Rhotacismo / Asibilacion retrofleja**: /r/ multiple y /ɾ/ simple se realizan como fricativas/aproximantes retroflejas [ʐ] o [ɻ].
    - Grupo /tr/ articulado como africada retrofleja sorda [t͡ʂ].
    - Velarizacion de /n/ final [ŋ].
    """

    def __init__(self) -> None:
        super().__init__(
            code="COSTA_RICAN",
            name="Costarricense (Asibilado)",
            region=DialectRegion.CENTRAL_AMERICA,
            description="Variedad costarricense con asibilación de vibrantes a retrofleja [ʐ], grupo /tr/ como [t͡ʂ] y seseo.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.5,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=1.0,
                vowel_opening=0.0,
                velar_nasal=0.9,
                vocalic_reduction=0.0,
                glottal_j=0.7,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Asibilacion retrofleja de vibrante multiple /r/ -> [ʐ].",
                "Grupo /tr/ articulado como africada retrofleja [t͡ʂ].",
                "Velarizacion de /n/ final a [ŋ].",
                "Seseo universal (/s/)."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []
        num_sylls = len(word.syllables)

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            cod_len = len(syll.coda)
            num_phones = len(phones)
            coda_start_idx = num_phones - cod_len if cod_len > 0 else num_phones

            i = 0
            n = len(phones)
            while i < n:
                p = phones[i]
                is_in_coda = (i >= coda_start_idx)

                # Grupo /tr/
                if p == "t" and i + 1 < n and phones[i + 1] in ("ɾ", "r"):
                    transformed_phones.append("t͡ʂ")
                    i += 2
                    continue

                # /r/ multiple a retrofleja [ʐ]
                if p == "r":
                    transformed_phones.append("ʐ")
                elif is_in_coda and p == "n" and syl_idx == num_sylls - 1:
                    transformed_phones.append("ŋ")
                elif is_in_coda and p == "s":
                    transformed_phones.append("h")
                elif p == "x":
                    transformed_phones.append("h")
                elif p == "b" and (syl_idx > 0 or i > 0):
                    transformed_phones.append("β")
                elif p == "d" and (syl_idx > 0 or i > 0):
                    transformed_phones.append("ð")
                elif p == "g" and (syl_idx > 0 or i > 0):
                    transformed_phones.append("ɣ")
                else:
                    transformed_phones.append(p)
                i += 1

            result.append(transformed_phones)

        return result
