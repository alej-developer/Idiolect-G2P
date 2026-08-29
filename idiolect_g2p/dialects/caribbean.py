"""
Dialectos de El Caribe: Estandar, Lambdacista, Rotacista y Geminador.
Caribbean Spanish dialects: Standard, Lambdacist, Rhotacist, and Geminating.

Basado en:
- Guitart, J. M. (1978). Organizacion fonologica del espanol de Cuba.
- Chela-Flores, G. (1982). Las teorias fonologicas y la sincronia caribena.
- Lipski, J. M. (1994). Latin American Spanish.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class CaribbeanStandardDialect(Dialect):
    """
    Espanol Caribeno General / Estandar (Cuba, Venezuela, Republica Dominicana, Puerto Rico):
    - Seseo universal (/s/).
    - Aspiracion sistematica de /s/ en coda silabica ([h]) y elision ante pausa.
    - Velarizacion sistematica de /n/ en posicion final de palabra ([ŋ]).
    - Articulacion de 'j' como fricativa glotal sorda [h] (en lugar de [x]/[χ]).
    - Debilitamiento y caida frecuente de /d/ intervocalica (-ado -> [ao]).
    """

    def __init__(self) -> None:
        super().__init__(
            code="CARIBBEAN_STD",
            name="Caribeño General / Estándar",
            region=DialectRegion.CARIBBEAN,
            description="Variedad caribeña con seseo, aspiración de /s/ en coda [h], velarización de nasal final [ŋ] y 'j' glotal [h].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=1.0,
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
                glottal_j=1.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Seseo universal (/s/).",
                "Aspiracion de /s/ en posicion de coda silabica (/s/ -> [h]).",
                "Velarizacion de nasal final de palabra (/n/ -> [ŋ]).",
                "Pronunciacion de 'j' como fricativa glotal [h].",
                "Espirantizacion y debilitamiento de oclusivas intervocalicas [β, ð, ɣ]."
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

                # 1. Aspiracion de /s/ en coda
                if is_in_coda and p == "s":
                    new_p = "h"

                # 2. Velarizacion de /n/ en posicion final de palabra
                elif is_in_coda and p == "n" and syl_idx == num_sylls - 1:
                    new_p = "ŋ"

                # 3. 'j' glotal
                elif p == "x":
                    new_p = "h"

                # 4. Espirantizacion intervocalica
                elif p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    # Debilitamiento intervocalico
                    new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result


class CaribbeanLambdacistDialect(Dialect):
    """
    Espanol Caribeno Lambdacista (Puerto Rico, Republica Dominicana, zonas costeras):
    - Todos los rasgos caribenos estandar.
    - Neutralizacion de liquidas: **Lambdacismo** (/ɾ/ -> [l] en posicion de coda silabica).
    - Permite rimas dialectales consonantes perfectas: puerto/muelto, amor/sol, mar/sal.
    """

    def __init__(self) -> None:
        super().__init__(
            code="CARIBBEAN_LAMBDACIST",
            name="Caribeño Lambdacista (Lateralizante)",
            region=DialectRegion.CARIBBEAN,
            description="Variedad caribeña con lambdacismo sistemático (/ɾ/ -> [l] en coda), aspiración de /s/ y velarización de nasal final.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=1.0,
                lambdacism=1.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=1.0,
                vocalic_reduction=0.0,
                glottal_j=1.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Lambdacismo sistematico: conversion de vibrante simple en coda a lateral alveolar (/ɾ/ -> [l]).",
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

                # Lambdacismo en coda: /ɾ/ -> [l]
                if is_in_coda and p == "ɾ":
                    new_p = "l"
                elif is_in_coda and p == "s":
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


class CaribbeanRhotacistDialect(Dialect):
    """
    Espanol Caribeno Rotacista:
    - Neutralizacion de liquidas: **Rotacismo** (/l/ -> [ɾ] en posicion de coda: alto -> [ˈaɾ.to]).
    """

    def __init__(self) -> None:
        super().__init__(
            code="CARIBBEAN_RHOTACIST",
            name="Caribeño Rotacista",
            region=DialectRegion.CARIBBEAN,
            description="Variedad caribeña con rotacismo (/l/ -> [ɾ] en coda), aspiración de /s/ y velarización nasal.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=1.0,
                lambdacism=0.0,
                rhotacism=1.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=1.0,
                vocalic_reduction=0.0,
                glottal_j=1.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Rotacismo en coda: conversion de lateral a vibrante simple (/l/ -> [ɾ]).",
                "Aspiracion de /s/ en coda [h].",
                "Velarizacion nasal final [ŋ]."
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

                if is_in_coda and p == "l":
                    new_p = "ɾ"
                elif is_in_coda and p == "s":
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
