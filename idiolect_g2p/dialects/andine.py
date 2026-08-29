"""
Dialectos de la Region Andina: Andino Tradicional (Lleista) y Andino Asibilado.
Andean Spanish dialects: Traditional (Lleísta) and Assibilated.

Basado en:
- Caravedo, R. (1990). La lengua espanola en el Peru.
- Perez Silva, J. I. (2008). Estudios de variacion fonetica andina.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class AndeanTraditionalDialect(Dialect):
    """
    Espanol Andino Tradicional (Tierras altas de Peru, Bolivia, Ecuador, Colombia):
    - Seseo universal (/s/).
    - Conservacion fonemica estricta de la distincion /ʎ/ ('ll') vs /ʝ/ ('y') (**Lleismo**).
    - Conservacion y tension de consonantes en coda silabica (sin aspiracion de /s/).
    - Oclusivas tensas.
    """

    def __init__(self) -> None:
        super().__init__(
            code="ANDINE_TRADITIONAL",
            name="Andino Tradicional (Lleísta)",
            region=DialectRegion.ANDINE,
            description="Variedad andina conservadora con seseo, distincion fonemica lateral /ʎ/ ('ll') y /s/ tensa en coda sin aspirar.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=1.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Lleismo sistematico: preservacion de la lateral palatal sonora /ʎ/ para la grafia 'll'.",
                "Seseo universal (/s/).",
                "Conservacion plena y tensa de /s/ en coda silabica sin aspiracion.",
                "Espirantizacion suave [β, ð, ɣ]."
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
            ons_text = syll.onset.lower()

            for phone_idx, p in enumerate(phones):
                new_p = p

                # Lleismo: si el ataque correspondia a 'll', se asigna /ʎ/
                if p == "ʝ" and "ll" in ons_text:
                    new_p = "ʎ"
                elif p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result


class AndeanAssibilatedDialect(Dialect):
    """
    Espanol Andino Asibilado (Zonas andinas de Colombia, Ecuador, Bolivia y NOA argentino):
    - Seseo universal (/s/).
    - **Asibilacion de vibrantes**: /r/ multiple se realiza como fricativa alveolar asibilada [ř] o retrofleja [ʐ].
    - Grupo 'tr' articulado como africada retrofleja sorda [t͡ʂ] (*tres* -> [t͡ʂes]).
    - Lleismo o yeismo segun la subzona.
    """

    def __init__(self) -> None:
        super().__init__(
            code="ANDINE_ASSIBILATED",
            name="Andino Asibilado",
            region=DialectRegion.ANDINE,
            description="Variedad andina con asibilación de vibrante múltiple [ř] y grupo /tr/ como africada retrofleja [t͡ʂ].",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.5,
                assibilation_r=1.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Asibilacion de la vibrante multiple /r/ -> [ř] (fricativa alveolar asibilada).",
                "Articulacion africada del grupo /tr/ -> [t͡ʂ].",
                "Seseo universal (/s/).",
                "Conservacion de consonantes en coda."
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
            ons_text = syll.onset.lower()

            i = 0
            n = len(phones)
            while i < n:
                p = phones[i]

                # Asibilacion de /tr/ -> [t͡ʂ]
                if p == "t" and i + 1 < n and phones[i + 1] in ("ɾ", "r"):
                    transformed_phones.append("t͡ʂ")
                    i += 2
                    continue

                # Asibilacion de /r/ multiple
                if p == "r":
                    transformed_phones.append("ř")
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
