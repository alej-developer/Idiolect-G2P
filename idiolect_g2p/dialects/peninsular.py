"""
Dialecto Castellano Peninsular Septentrional y Central.
Castilian Northern and Central Peninsular Spanish dialect.

Basado en:
- Martinez-Celdran, E., Fernandez-Planas, A. M., & Carrera-Sabate, J. (2003). Illustrations of the IPA: Castilian Spanish. JIPA 33(2).
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


class PeninsularStandardDialect(Dialect):
    """
    Espanol peninsular septentrional/central normativo:
    - Distincion fonologica estricta: /θ/ (c ante e/i, z) vs /s̺/ (s apicoalveolar).
    - Alofonos aproximantes intervocalicos: [β, ð, ɣ].
    - Fricativa uvular/velar sorda [χ] / [x] para 'j' y 'g+e/i'.
    - Conservacion tensa de consonantes en coda silabica.
    - Neutralizacion de /d/ final a interdental [θ] en registro central (Madrid -> ma.ˈðɾiθ).
    """

    def __init__(self) -> None:
        super().__init__(
            code="ES_PENINSULAR",
            name="Castellano Peninsular Septentrional/Central",
            region=DialectRegion.IBERIAN,
            description="Variedad peninsular estandar con distincion fonologica /θ/ y /s̺/, alofonos aproximantes y /x/ uvular/velar.",
            isogloss_vector=IsoglossVector(
                seseo=0.0,
                aspiration_s=0.0,
                lambdacism=0.0,
                rhotacism=0.0,
                gemination=0.0,
                rehilamiento_voiced=0.0,
                rehilamiento_voiceless=0.0,
                lleismo=0.5,  # Tradicionalmente lleista, actualmente yeista en zonas urbanas
                assibilation_r=0.0,
                vowel_opening=0.0,
                velar_nasal=0.0,
                vocalic_reduction=0.0,
                glottal_j=0.0,
                affricate_tl=0.0,
            ),
            active_rules_description=[
                "Distincion fonologica entre /θ/ ('c', 'z') y /s̺/ ('s').",
                "Articulacion apicoalveolar de /s/ [s̺].",
                "Espirantizacion aproximante de oclusivas sonoras intervocálicas [β, ð, ɣ].",
                "Fricativa velar/uvular sorda [χ] para 'j' y 'g' ante 'e, i'.",
                "Conservacion de consonantes en coda sin aspiracion."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []
        raw_word = word.normalized_text

        # Localizar posiciones de 'c+e/i' y 'z' en el texto original para distinguir /θ/ de /s/
        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            ons_text = syll.onset.lower()
            cod_text = syll.coda.lower()
            nuc_text = syll.nucleus.lower()

            for phone_idx, p in enumerate(phones):
                new_p = p

                # 1. Distincion /θ/ vs /s/: Si la grafia era 'z' o 'c' ante e/i -> /θ/
                if p == "s":
                    if "z" in ons_text or "z" in cod_text or ("c" in ons_text and any(v in nuc_text for v in "eiéí")):
                        new_p = "θ"
                    else:
                        new_p = "s̺"  # S apicoalveolar peninsular

                # 2. Espirantizacion aproximante intervocálica
                elif p == "b" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "β"
                elif p == "d" and (syl_idx > 0 or phone_idx > 0):
                    # Si es 'd' final de palabra en posicion de coda
                    if syl_idx == len(word.syllables) - 1 and phone_idx == len(phones) - 1 and cod_text == "d":
                        new_p = "θ"  # /d/ final relajada a [θ] (Madrid -> ma.ˈðɾiθ)
                    else:
                        new_p = "ð"
                elif p == "g" and (syl_idx > 0 or phone_idx > 0):
                    new_p = "ɣ"

                # 3. Fricativa velar/uvular [χ]
                elif p == "x":
                    new_p = "χ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result
