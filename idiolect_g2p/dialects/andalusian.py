"""
Dialectos Andaluces: Andaluz Occidental y Andaluz Oriental (Desdoblamiento Vocalico).
Andalusian Spanish dialects: Western Andalusian and Eastern Andalusian (Vocalic Split/Opening).

Basado en:
- Herrero de Haro, A., & Hajek, J. (2022). Illustrations of the IPA: Eastern Andalusian Spanish. JIPA 52(1).
- Alvar, M. (1996). Manual de dialectologia hispanica: El espanol de Espana.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class WesternAndalusianDialect(Dialect):
    """
    Espanol Andaluz Occidental (Sevilla, Huelva, Cadiz):
    - Seseo o Ceceo generalizado (/s/ o /θ/).
    - Aspiracion y elision sistematica de /s/ implosiva (/s/ -> [h] / [∅]).
    - Yeismo generalizado (/ʝ/).
    - Fricativa glotal [h] para 'j'.
    - Neutralizacion ocasional de liquidas en coda.
    """

    def __init__(self) -> None:
        super().__init__(
            code="ANDALUSIAN_WESTERN",
            name="Andaluz Occidental",
            region=DialectRegion.IBERIAN,
            description="Variedad andaluza occidental con seseo/ceceo, aspiración/elisión de /s/ en coda y 'j' glotal [h].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=1.0,
                lambdacism=0.3,
                rhotacism=0.3,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.6,
                vocalic_reduction=0.0,
                glottal_j=1.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Seseo / Ceceo fonologico.",
                "Aspiracion de /s/ en coda (/s/ -> [h]).",
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


class EasternAndalusianDialect(Dialect):
    """
    Espanol Andaluz Oriental (Granada, Almeria, Jaen, Cordoba oriental, Murcia sur):
    - **Desdoblamiento y abertura vocalica fonologica**: La perdida o aspiracion de /s/ final
      provoca la apertura sistematica de las vocales previas (/a, e, o/ -> [æ, ɛ, ɔ]).
    - Distincion fonematica entre singular y plural basada exclusivamente en la abertura vocalica.
    - Seseo o distincion segun la subzona.
    """

    def __init__(self) -> None:
        super().__init__(
            code="ANDALUSIAN_EASTERN",
            name="Andaluz Oriental (Abertura Vocálica)",
            region=DialectRegion.IBERIAN,
            description="Variedad con desdoblamiento y abertura vocálica fonológica ([æ, ɛ, ɔ]) ante la elisión/aspiración de /s/.",
            isogloss_vector=IsoglossVector(
                seseo=0.8,
                aspiration_s=1.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=1.0,
                velar_nasal=0.5,
                vocalic_reduction=0.0,
                glottal_j=1.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Desdoblamiento vocalico: apertura fonologica de /a/ -> [æ], /e/ -> [ɛ], /o/ -> [ɔ] ante coda con /s/.",
                "Aspiracion y elision de /s/ implosiva (/s/ -> [h] o [∅]).",
                "Pronunciacion glotal [h] de 'j'."
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
            has_coda_s = "s" in syll.coda.lower() or "z" in syll.coda.lower()

            for phone_idx, p in enumerate(phones):
                new_p = p
                is_in_coda = (phone_idx >= coda_start_idx)

                # Abertura vocalica provocada por /s/ en la misma silaba
                if has_coda_s:
                    if p == "a":
                        new_p = "æ"
                    elif p == "e":
                        new_p = "ɛ"
                    elif p == "o":
                        new_p = "ɔ"

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
