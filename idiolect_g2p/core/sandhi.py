"""
Módulo de Fonotaxis Post-léxica y Sandhi Externo para Idiolect-G2P.
Post-lexical Phonotactics and External Sandhi Module.

Basado en:
- Hualde, J. I. (2014). Los sonidos del español: Spanish phonetics and phonology.
  Cambridge University Press. (Capítulo 6: La estructura silábica; Capítulo 13: Procesos postléxicos).
- Quilis, A. (1993). Tratado de fonología y fonética españolas. Gredos.
- Martínez Celdrán, E., & Fernández Planas, A. M. (2007). Manual de fonética española. Ariel.
- Clements, G. N., & Hume, E. V. (1995). The internal organization of speech sounds.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
import copy

from .phonetics import Phoneme, get_phoneme
from .syllabifier import ProsodicWord, Syllable


class JunctureProcessType(Enum):
    """Tipos formales de procesos fonotácticos en frontera de juntura (sandhi)."""
    RESYLLABIFICATION = "resyllabification"    # Coda_w1 + Núcleo_w2 -> Ataque_w2 (e.g. las alas -> [la.ˈsa.las])
    VOICING_ASSIMILATION = "voicing_assimilation" # Asimilación de sonoridad (e.g. los mismos -> [loz ˈmiz.mos])
    VOCALIC_COALESCENCE = "vocalic_coalescence"   # Fusión/sinalefa interpalabra (e.g. de este -> [de‿este])
    NASAL_ASSIMILATION = "nasal_assimilation"     # Asimilación de punto de /n/ ante C inicial
    NO_CHANGE = "no_change"


@dataclass
class SandhiJuncture:
    """
    Registro formal de un evento fonotáctico en frontera de palabra (sandhi externo).
    """
    word_index_left: int
    word_index_right: int
    process_type: JunctureProcessType
    input_left_coda: str
    input_right_onset: str
    output_phoneme: str
    description: str
    isogloss_condition: Optional[str] = None


@dataclass
class ConnectedSpeechResult:
    """
    Resultado de la evaluación fonotáctica de una frase o verso en habla continua.
    """
    raw_text: str
    words: List[str]
    word_syllables: List[List[List[str]]] # [palabra][silaba][fonemas]
    connected_ipa: str                    # Transcripción unificada con marcas de sandhi
    junctures: List[SandhiJuncture] = field(default_factory=list)


class SandhiEngine:
    """
    Motor fonotáctico post-léxico para español.
    Evalúa y aplica procesos de sandhi externo en secuencias adyacentes de palabras.
    """

    # Consonantes sonoras que inducen asimilación regresiva de sonoridad en coda
    SONORANT_OR_VOICED_ONSET = {
        "m", "n", "ɲ", "ŋ",  # Nasales
        "l", "ʎ",            # Laterales
        "ɾ", "r", "ř", "ʐ",  # Vibrantes
        "b", "β", "d", "ð", "g", "ɣ", # Oclusivas / Aproximantes sonoras
        "ʝ", "ʒ", "w", "j"   # Fricativas / Aproximantes sonoras
    }

    # Vocales y semivocales
    VOWEL_PHONEMES = {"a", "e", "i", "o", "u", "á", "é", "í", "ó", "ú", "j", "w", "æ", "ɛ", "ɔ"}

    def __init__(self, enable_resyllabification: bool = True, enable_voicing: bool = True):
        self.enable_resyllabification = enable_resyllabification
        self.enable_voicing = enable_voicing

    def apply_sandhi(
        self,
        words_syllables: List[List[List[str]]],
        isogloss_vector: Optional[Dict[str, float]] = None
    ) -> Tuple[List[List[List[str]]], List[SandhiJuncture]]:
        """
        Aplica los procesos de sandhi interpalabra a una lista estructurada de palabras fonéticas.
        
        Args:
            words_syllables: Lista de palabras, cada una con su lista de sílabas y fonemas AFI.
            isogloss_vector: Vector de isoglosas activo para modular aspiración vs resonorización.

        Returns:
            Tuple con (palabras modificadas, lista de junturas detectadas).
        """
        if not words_syllables or len(words_syllables) < 2:
            return words_syllables, []

        modified: List[List[List[str]]] = [
            [list(syl) for syl in word] for word in words_syllables
        ]
        junctures: List[SandhiJuncture] = []

        isoglosses = isogloss_vector or {}
        aspiration_rate = isoglosses.get("aspiration_s", 0.0)

        for w_idx in range(len(modified) - 1):
            left_word = modified[w_idx]
            right_word = modified[w_idx + 1]

            if not left_word or not right_word:
                continue

            last_syl_left = left_word[-1]
            first_syl_right = right_word[0]

            if not last_syl_left or not first_syl_right:
                continue

            # Identificar último fonema de W_left y primer fonema de W_right
            left_coda_phone = last_syl_left[-1]
            right_onset_phone = first_syl_right[0]

            # -------------------------------------------------------------
            # 1. REENCADENAMIENTO SILÁBICO (Resyllabification)
            # Coda consonántica ante vocal inicial de palabra siguiente:
            # e.g., /las/ + /a.las/ -> [la] + [sa.las]
            # -------------------------------------------------------------
            if self.enable_resyllabification and (right_onset_phone in self.VOWEL_PHONEMES):
                # La coda de W_left es consonante (no vocal)
                if left_coda_phone not in self.VOWEL_PHONEMES:
                    out_phone = left_coda_phone
                    if left_coda_phone == "h" and aspiration_rate < 0.9:
                        # Re-fonologización conservadora en ataque intervocálico
                        out_phone = "s"

                    # Transferir coda a ataque de la sílaba siguiente
                    popped_coda = last_syl_left.pop()
                    first_syl_right.insert(0, out_phone)

                    junctures.append(SandhiJuncture(
                        word_index_left=w_idx,
                        word_index_right=w_idx + 1,
                        process_type=JunctureProcessType.RESYLLABIFICATION,
                        input_left_coda=popped_coda,
                        input_right_onset=right_onset_phone,
                        output_phoneme=out_phone,
                        description=f"Reencadenamiento de coda '{popped_coda}' como ataque ante vocal inicial '{right_onset_phone}'."
                    ))
                    continue

            # -------------------------------------------------------------
            # 2. ASIMILACIÓN REGRESIVA DE SONORIDAD (Voicing Assimilation)
            # Sibilante /s/ o interdental /θ/ en coda ante consonante sonora:
            # e.g., /los/ + /mis.mos/ -> [loz] + [mis.mos] (o [loh] si aspira)
            # -------------------------------------------------------------
            if self.enable_voicing and (right_onset_phone in self.SONORANT_OR_VOICED_ONSET):
                if left_coda_phone in ("s", "s̺"):
                    if aspiration_rate >= 0.6:
                        if left_coda_phone != "h":
                            last_syl_left[-1] = "h"
                            junctures.append(SandhiJuncture(
                                word_index_left=w_idx,
                                word_index_right=w_idx + 1,
                                process_type=JunctureProcessType.VOICING_ASSIMILATION,
                                input_left_coda=left_coda_phone,
                                input_right_onset=right_onset_phone,
                                output_phoneme="h",
                                description=f"Aspiración de sibilante en frontera ante consonante sonora '{right_onset_phone}'.",
                                isogloss_condition="aspiration_s"
                            ))
                    else:
                        last_syl_left[-1] = "z"
                        junctures.append(SandhiJuncture(
                            word_index_left=w_idx,
                            word_index_right=w_idx + 1,
                            process_type=JunctureProcessType.VOICING_ASSIMILATION,
                            input_left_coda=left_coda_phone,
                            input_right_onset=right_onset_phone,
                            output_phoneme="z",
                            description=f"Resonorización asimilativa de sibilante /s/ -> [z] ante '{right_onset_phone}'."
                        ))
                    continue

                elif left_coda_phone == "θ":
                    last_syl_left[-1] = "ð"
                    junctures.append(SandhiJuncture(
                        word_index_left=w_idx,
                        word_index_right=w_idx + 1,
                        process_type=JunctureProcessType.VOICING_ASSIMILATION,
                        input_left_coda="θ",
                        input_right_onset=right_onset_phone,
                        output_phoneme="ð",
                        description=f"Resonorización asimilativa de interdental /θ/ -> [ð] ante '{right_onset_phone}'."
                    ))
                    continue

            # -------------------------------------------------------------
            # 3. ASIMILACIÓN HOMORGÁNICA DE NASAL EN FRONTERA
            # /n/ ante consonante adopta el punto de articulación
            # -------------------------------------------------------------
            if left_coda_phone == "n":
                if right_onset_phone in ("p", "b", "β", "m"):
                    last_syl_left[-1] = "m"
                    junctures.append(SandhiJuncture(
                        word_index_left=w_idx,
                        word_index_right=w_idx + 1,
                        process_type=JunctureProcessType.NASAL_ASSIMILATION,
                        input_left_coda="n",
                        input_right_onset=right_onset_phone,
                        output_phoneme="m",
                        description=f"Asimilación homorgánica de nasal alveolar /n/ -> bilabial [m] ante '{right_onset_phone}'."
                    ))
                elif right_onset_phone in ("k", "g", "ɣ", "x"):
                    last_syl_left[-1] = "ŋ"
                    junctures.append(SandhiJuncture(
                        word_index_left=w_idx,
                        word_index_right=w_idx + 1,
                        process_type=JunctureProcessType.NASAL_ASSIMILATION,
                        input_left_coda="n",
                        input_right_onset=right_onset_phone,
                        output_phoneme="ŋ",
                        description=f"Asimilación homorgánica de nasal /n/ -> velar [ŋ] ante '{right_onset_phone}'."
                    ))

        return modified, junctures

    def format_connected_ipa(
        self,
        words_syllables: List[List[List[str]]],
        stresses: Optional[List[int]] = None
    ) -> str:
        """
        Formatea las palabras procesadas en una cadena AFI de habla continua,
        marcando separadores silábicos '.' y espacios de frontera ' '.
        """
        word_strs: List[str] = []
        for w_idx, word in enumerate(words_syllables):
            syl_strs: List[str] = []
            stress_pos = stresses[w_idx] if stresses and w_idx < len(stresses) else -1

            for s_idx, syl in enumerate(word):
                phone_str = "".join(syl)
                if s_idx == stress_pos:
                    syl_strs.append(f"ˈ{phone_str}")
                else:
                    syl_strs.append(phone_str)

            word_ipa = ".".join(syl_strs).replace(".ˈ", "ˈ")
            word_strs.append(word_ipa)

        return " ".join(word_strs)
