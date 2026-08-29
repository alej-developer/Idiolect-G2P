"""
Dialecto Chileno.
Chilean Spanish dialect.

Basado en:
- Sadowsky, S., & Salamanca, G. (2011). El alofono africado [t͡s] del fonema /t͡ʃ/ en el espanol de Chile. RLA.
- Lipski, J. M. (1994). Latin American Spanish.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class ChileanDialect(Dialect):
    """
    Espanol Chileno:
    - Seseo universal (/s/).
    - **Palatalizacion de velares**: /k, g, x/ ante vocales anteriores /e, i/ se realizan como palatales [c, ɟ, ç] (*queso* -> [ˈce.so], *gente* -> [ˈçen.te]).
    - Asibilacion del grupo /tr/ a africada retrofleja [t͡ʂ].
    - Fricativizacion o relajacion de 'ch' (/t͡ʃ/ -> [ʃ]).
    - Aspiracion de /s/ en coda silabica ([h]).
    """

    def __init__(self) -> None:
        super().__init__(
            code="CHILEAN",
            name="Chileno",
            region=DialectRegion.CHILE,
            description="Variedad chilena con palatalización de velares ante vocales anteriores [c, ɟ, ç], asibilación de /tr/ [t͡ʂ] y aspiración de /s/.",
            isogloss_vector=IsoglossVector(
                seseo=1.0,
                aspiration_s=0.9,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.0,
                assibilation_r=0.8,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Palatalizacion de velares ante vocales anteriores (/k/ -> [c], /g/ -> [ɟ], /x/ -> [ç] ante e, i).",
                "Asibilacion del grupo /tr/ -> [t͡ʂ].",
                "Fricativizacion de /t͡ʃ/ -> [ʃ].",
                "Aspiracion de /s/ en coda silabica (/s/ -> [h]).",
                "Seseo universal (/s/)."
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
            nuc_text = syll.nucleus.lower()
            has_front_vowel = any(v in nuc_text for v in "eiéí")
            cod_len = len(syll.coda)
            num_phones = len(phones)
            coda_start_idx = num_phones - cod_len if cod_len > 0 else num_phones

            i = 0
            n = len(phones)
            while i < n:
                p = phones[i]
                is_in_coda = (i >= coda_start_idx)

                # Asibilacion de /tr/
                if p == "t" and i + 1 < n and phones[i + 1] in ("ɾ", "r"):
                    transformed_phones.append("t͡ʂ")
                    i += 2
                    continue

                # Palatalizacion de velares ante vocales anteriores
                if p == "k" and has_front_vowel and not is_in_coda:
                    transformed_phones.append("c")
                elif p == "g" and has_front_vowel and not is_in_coda:
                    transformed_phones.append("ɟ")
                elif p == "x" and has_front_vowel and not is_in_coda:
                    transformed_phones.append("ç")

                # Fricativizacion de /t͡ʃ/
                elif p == "t͡ʃ":
                    transformed_phones.append("ʃ")

                # Aspiracion de /s/ en coda
                elif is_in_coda and p == "s":
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
