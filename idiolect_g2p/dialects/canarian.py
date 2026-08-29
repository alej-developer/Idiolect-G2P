"""
Dialecto Canario.
Canarian Spanish dialect.

Basado en:
- Alvar, M. (1996). Manual de dialectologia hispanica: El espanol de Espana.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class CanarianDialect(Dialect):
    """
    Espanol Canario:
    - Seseo universal (/s/ predorsal suave).
    - Aspiracion sistematica de /s/ en coda silabica ([h]).
    - 'j' pronunciada como fricativa glotal sorda [h].
    - Yeismo generalizado.
    - Sonorizacion y debilitamiento de oclusivas intervocalicas.
    """

    def __init__(self) -> None:
        super().__init__(
            code="CANARIAN",
            name="Canario",
            region=DialectRegion.IBERIAN,
            description="Variedad canaria con seseo, aspiración de /s/ en coda [h] y 'j' glotal [h].",
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
                velar_nasal=0.4,
                vocalic_reduction=0.0,
                glottal_j=1.0,
                affricate_tl=0.8,
            ),
            active_rules_description=[
                "Seseo universal (/s/).",
                "Aspiracion de /s/ en coda silabica (/s/ -> [h]).",
                "Fricativa glotal [h] para 'j'.",
                "Espirantizacion [β, ð, ɣ]."
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
            cod_len = len(syll.coda)
            num_phones = len(phones)
            coda_start_idx = num_phones - cod_len if cod_len > 0 else num_phones

            for phone_idx, p in enumerate(phones):
                new_p = p
                is_in_coda = (phone_idx >= coda_start_idx)

                if is_in_coda and p == "s":
                    new_p = "h"
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
