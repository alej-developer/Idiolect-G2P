"""
Dialectos Diacronicos e Historicos: Espanol del Siglo de Oro y Espanol Medieval.
Diachronic and Historical Spanish dialects: Golden Age Spanish and Medieval Spanish.

Basado en:
- Penny, R. (2002). A history of the Spanish language.
- Lapesa, R. (1981). Historia de la lengua espanola.
"""

from __future__ import annotations
from typing import List
from .base import Dialect, DialectRegion, IsoglossVector
from ..core.syllabifier import ProsodicWord, Syllable


# Lista canonica de terminos con 'h-' procedente etimologicamente de 'f-' latina
HISTORICAL_F_LATIN_WORDS = frozenset([
    "hacer", "hace", "hacen", "hacia", "hizo", "hecho", "haciendo",
    "hablar", "habla", "hablan", "hablo", "hablado", "hablando",
    "hijo", "hija", "hijos", "hijas",
    "hoja", "hojas",
    "hondo", "honda", "hondos", "hondas", "hondura",
    "humo", "humos",
    "hambre", "hambriento",
    "hierro", "fierro",
    "herir", "herida", "herido",
    "hervir", "hirviendo",
    "huir", "huye", "huyen", "huida",
    "horca", "horcón",
    "horno", "hornear",
    "harina",
    "halcon", "halcón",
    "hebra",
    "hechizo", "hechicera",
    "hospedar",
    "heder", "hedor",
    "hurto", "hurtar", "hurta",
    "huso"
])


class GoldenAgeDialect(Dialect):
    """
    Espanol Clasico / Siglo de Oro (Siglos XVI y XVII - Garcilaso, Lope de Vega, Gongora, Quevedo, Sor Juana):
    - **Retencion de la aspirada [h]** en palabras con 'h-' etimologica de F- latina (*hacer* -> [ha.ˈseɾ] / [ha.ˈθeɾ]).
    - Lleismo sistematico (/ʎ/ para 'll').
    - Distincion o seseo segun el origen del autor.
    - Conservacion plena de consonantes en coda.
    """

    def __init__(self) -> None:
        super().__init__(
            code="DIACHRONIC_GOLDEN_AGE",
            name="Español del Siglo de Oro (Clásico)",
            region=DialectRegion.DIACHRONIC,
            description="Variedad clásica de los siglos XVI-XVII con retención de aspiración [h] < F- latina, lleísmo estricto /ʎ/ y sibilantes.",
            isogloss_vector=IsoglossVector(
                seseo=0.5,
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
                diachronic_sibilants=0.6,
                initial_f_aspiration=1.0,
            ),
            active_rules_description=[
                "Retencion de la aspirada glotal [h] en grafemas 'h-' derivados de la F- inicial latina (hacer -> [ha.ˈseɾ]).",
                "Lleismo estricto: pronunciacion lateral palatal sonora /ʎ/ para 'll'.",
                "Fricativa velar sorda [x] para 'j' / 'g+e,i'.",
                "Conservacion rigurosa de consonantes en coda silabica."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []
        norm_word = word.normalized_text

        # Verificar si la palabra procede de F- latina
        has_f_latina = any(norm_word.startswith(stem) or stem.startswith(norm_word) for stem in HISTORICAL_F_LATIN_WORDS)

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            ons_text = syll.onset.lower()

            # Si es la primera sílaba y la palabra tiene 'h-' procedente de F- latina
            if syl_idx == 0 and has_f_latina and norm_word.startswith("h"):
                transformed_phones.append("h")

            for phone_idx, p in enumerate(phones):
                new_p = p

                # Lleismo
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


class MedievalSpanishDialect(Dialect):
    """
    Espanol Medieval (Siglos XII - XV - Cantar de Mio Cid, Gonzalo de Berceo, Arcipreste de Hita):
    - **Sistema de 6 sibilantes medievales**:
      - /ts/ (grafia 'ç')
      - /dz/ (grafia 'z')
      - /s̺/ (grafia 'ss' e inicio 's-')
      - /z̺/ (grafia 's' intervocalica)
      - /ʃ/ (grafia 'x')
      - /ʒ/ (grafia 'j' / 'g+e,i')
    - Lleismo /ʎ/.
    - Retencion de [f-] o [h-].
    """

    def __init__(self) -> None:
        super().__init__(
            code="DIACHRONIC_MEDIEVAL",
            name="Español Medieval (6 Sibilantes)",
            region=DialectRegion.DIACHRONIC,
            description="Sistema fonológico medieval con seis sibilantes (/ts, dz, s̺, z̺, ʃ, ʒ/), lleísmo y retención de F-.",
            isogloss_vector=IsoglossVector(
                seseo=0.0,
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
                diachronic_sibilants=1.0,
                initial_f_aspiration=1.0,
            ),
            active_rules_description=[
                "Sistema de seis sibilantes medievales: /ts/ (ç), /dz/ (z), /s̺/ (ss), /z̺/ (s), /ʃ/ (x), /ʒ/ (j, g).",
                "Lleismo estricto /ʎ/.",
                "Oclusivas sonoras intervocálicas sin relajación plena."
            ]
        )

    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        result: List[List[str]] = []
        raw_word = word.normalized_text

        for syl_idx, (syll, phones) in enumerate(zip(word.syllables, base_phonemes)):
            transformed_phones: List[str] = []
            ons_text = syll.onset.lower()
            cod_text = syll.coda.lower()

            for phone_idx, p in enumerate(phones):
                new_p = p

                # 1. Grafia 'z' -> africada alveolar sonora /dz/
                if "z" in ons_text or "z" in cod_text:
                    if p == "s":
                        new_p = "dz"
                # 2. Grafia 'c' ante e/i o 'ç' -> africada alveolar sorda /ts/
                elif ("c" in ons_text or "ç" in ons_text) and p == "s":
                    new_p = "ts"
                # 3. Grafia 'x' -> fricativa postalveolar sorda /ʃ/ (ej. Quixote -> ki.ˈʃo.te)
                elif "x" in ons_text or "x" in cod_text:
                    if p in ("x", "k", "s"):
                        new_p = "ʃ"
                # 4. Grafia 'j' o 'g+e/i' -> fricativa postalveolar sonora /ʒ/ (ej. muger -> mu.ˈʒeɾ)
                elif ("j" in ons_text or "g" in ons_text) and p == "x":
                    new_p = "ʒ"
                # 5. Lleismo
                elif p == "ʝ" and "ll" in ons_text:
                    new_p = "ʎ"

                transformed_phones.append(new_p)
            result.append(transformed_phones)

        return result
