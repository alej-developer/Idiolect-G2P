"""
Dialectos Rioplatenses: Zheista (sonoro) y Sheista (sordo).
Rioplatense Spanish dialects: Zheísta (voiced [ʒ]) and Sheísta (voiceless [ʃ]).

Basado en:
- Coloma, G. (2018). Illustrations of the IPA: Argentine Spanish. JIPA 48(2).
- Lipski, J. M. (1994). Latin American Spanish.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class RioplatenseZheistDialect(Dialect):
    """
    Espanol Rioplatense Zheista (Argentina / Uruguay):
    - Seseo universal (/s/).
    - **Rehilamiento sonoro**: Yeismo con realizacion fricativa postalveolar sonora [ʒ] para 'll' e 'y'.
    - Aspiracion condicional de /s/ preconsonantica ([h] ante sordas, sonorizacion [z] ante sonoras).
    - Espirantizacion aproximante [β, ð, ɣ].
    """

    def __init__(self) -> None:
        super().__init__(
            code="RIOPLATENSE_ZHEIST",
            name="Rioplatense Zheísta [ʒ]",
            region=DialectRegion.SOUTHERN_CONE,
            description="Variedad rioplatense tradicional con rehilamiento sonoro [ʒ] para 'll' e 'y', seseo y aspiración de /s/ ante consonante.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.7,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=1.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Rehilamiento sonoro: transduccion de 'll' e 'y' a fricativa postalveolar sonora [ʒ].",
                "Seseo universal (/s/).",
                "Aspiracion de /s/ en coda silabica ante consonante sorda (/s/ -> [h]).",
                "Espirantizacion aproximante intervocálica [β, ð, ɣ]."
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

                # Rehilamiento sonoro: /ʝ/ -> [ʒ]
                if p == "ʝ":
                    new_p = "ʒ"

                # Aspiracion de /s/ en coda si no es final absoluta
                elif is_in_coda and p == "s" and syl_idx < num_sylls - 1:
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


class RioplatenseSheistDialect(Dialect):
    """
    Espanol Rioplatense Sheista (Buenos Aires contemporaneo, costa rioplatense):
    - Seseo universal (/s/).
    - **Rehilamiento ensordecido**: Yeismo con realizacion fricativa postalveolar sorda [ʃ] para 'll' e 'y'.
    - Aspiracion de /s/ preconsonantica.
    """

    def __init__(self) -> None:
        super().__init__(
            code="RIOPLATENSE_SHEIST",
            name="Rioplatense Sheísta [ʃ]",
            region=DialectRegion.SOUTHERN_CONE,
            description="Variedad rioplatense contemporánea con sheísmo ensordecido [ʃ] para 'll' e 'y' (ej. calle -> [ˈka.ʃe]).",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.7,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=1.0,
                lleismo=0.0,
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Sheismo ensordecido: transduccion de 'll' e 'y' a fricativa postalveolar sorda [ʃ].",
                "Seseo universal (/s/).",
                "Aspiracion de /s/ en coda silabica ante consonante (/s/ -> [h]).",
                "Espirantizacion aproximante [β, ð, ɣ]."
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

                # Sheismo: /ʝ/ -> [ʃ]
                if p == "ʝ":
                    new_p = "ʃ"

                elif is_in_coda and p == "s" and syl_idx < num_sylls - 1:
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
