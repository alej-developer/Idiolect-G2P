"""
Motor de transduccion determinista de grafemas a fonemas (G2P) para espanol.
Rule-based deterministic Grapheme-to-Phoneme (G2P) transducer for Spanish.

Implementa un pipeline en dos fases:
1. Transduccion fonemica base a partir de la estructura prosodica y silabica.
2. Derivacion alofonica contextual parametrizada por el dialecto activo.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Final, Any, TYPE_CHECKING
import re
import copy


from .phonetics import Phoneme, get_phoneme
from .syllabifier import ProsodicWord, Syllable, syllabify_word, syllabify_text

if TYPE_CHECKING:
    from ..dialects.base import Dialect


@dataclass(frozen=True)
class TransductionResult:
    """Resultado estructurado de la transduccion G2P de una palabra o texto."""
    original_text: str
    ipa_transcription: str
    syllabified_ipa: str
    prosodic_word: ProsodicWord
    syllable_phonemes: List[List[str]]
    dialect_code: str
    dialect_name: str


class G2PTransducer:
    """
    Transductor fonetico multi-dialectal basado en reglas fonotacticas deterministas.
    """

    def __init__(self, default_dialect: Optional[Dialect] = None) -> None:
        self.default_dialect = default_dialect

    def _transcribe_nucleus(self, nucleus: str) -> List[str]:
        """Convierte la cadena ortografica del nucleo en sus simbolos AFI."""
        phonemes: List[str] = []
        n = len(nucleus)
        i = 0
        while i < n:
            c = nucleus[i].lower()
            # Vocales simples
            if c in ("a", "á", "à"):
                phonemes.append("a")
            elif c in ("e", "é", "è"):
                phonemes.append("e")
            elif c in ("o", "ó", "ò"):
                phonemes.append("o")
            elif c in ("i", "í"):
                # Si forma parte de un diptongo creciente en posicion inicial
                if i == 0 and n > 1 and nucleus[i + 1].lower() in "aeoáéó":
                    phonemes.append("j")
                # Si forma parte de un diptongo decreciente en posicion final
                elif i > 0 and nucleus[i - 1].lower() in "aeoáéó":
                    phonemes.append("j")
                else:
                    phonemes.append("i")
            elif c in ("u", "ú", "ü"):
                # Si forma parte de un diptongo creciente inicial (ej. cu-an-do)
                if i == 0 and n > 1 and nucleus[i + 1].lower() in "aeoáéó":
                    phonemes.append("w")
                # Si forma parte de diptongo decreciente (ej. au-to)
                elif i > 0 and nucleus[i - 1].lower() in "aeoáéó":
                    phonemes.append("w")
                else:
                    phonemes.append("u")
            elif c == "y":
                # 'y' como núcleo o semivocal (ej. 'rey', 'muy', 'y')
                if n == 1:
                    phonemes.append("i")
                else:
                    phonemes.append("j")
            i += 1
        return phonemes

    def _transcribe_onset(self, onset: str, nucleus: str, is_word_initial: bool) -> List[str]:
        """Convierte el ataque silabico ortografico a simbolos fonemicos base."""
        if not onset:
            return []

        ons = onset.lower()
        first_nuc = nucleus[0].lower() if nucleus else ""
        phonemes: List[str] = []

        # Casos especiales de digrafos y grupos
        if ons == "ch":
            return ["t͡ʃ"]
        if ons == "ll":
            return ["ʝ"]  # Base yeista; los dialectos lleistas lo reescriben a [ʎ]
        if ons == "rr":
            return ["r"]
        if ons == "qu":
            return ["k"]
        if ons == "gu":
            # Si va seguido de e, i (sin dieresis) -> /g/
            if first_nuc in ("e", "é", "i", "í"):
                return ["g"]
            return ["g", "w"]
        if ons == "gü":
            return ["g", "w"]
        if ons == "tl":
            return ["t͡ɬ"]

        i = 0
        n = len(ons)
        while i < n:
            c = ons[i]
            # Grafia 's'
            if c == "s":
                phonemes.append("s")
            # Grafias con 'c'
            elif c == "c":
                if i + 1 < n and ons[i + 1] == "h":
                    phonemes.append("t͡ʃ")
                    i += 2
                    continue
                if first_nuc in ("e", "é", "i", "í") and i == n - 1:
                    phonemes.append("s")  # Base seseante; el dialecto peninsular lo reescribe a /θ/
                else:
                    phonemes.append("k")
            # Grafias con 'z'
            elif c == "z":
                phonemes.append("s")  # Base seseante; peninsular reescribe a /θ/
            # Grafias con 'g'
            elif c == "g":
                if i + 1 < n and ons[i + 1] == "u" and first_nuc in ("e", "é", "i", "í"):
                    phonemes.append("g")
                    i += 2
                    continue
                if first_nuc in ("e", "é", "i", "í") and i == n - 1:
                    phonemes.append("x")
                else:
                    phonemes.append("g")
            # Grafias con 'j'
            elif c == "j":
                phonemes.append("x")
            # Grafia 'h' (muda en espanol moderno, aspirada en diacronico)
            elif c == "h":
                pass
            # Grafias 'b', 'v' (homofonas en espanol)
            elif c in ("b", "v"):
                phonemes.append("b")
            # Grafia 'r'
            elif c == "r":
                if is_word_initial and i == 0:
                    phonemes.append("r")  # /r/ multiple a inicio de palabra
                else:
                    phonemes.append("ɾ")
            # Grafia 'y' en ataque
            elif c == "y":
                phonemes.append("ʝ")
            # Grafia 'x'
            elif c == "x":
                if is_word_initial:
                    phonemes.append("s")
                else:
                    phonemes.extend(["k", "s"])
            # Grafias directas: p, t, k, d, f, m, n, ñ, l
            elif c == "p":
                phonemes.append("p")
            elif c == "t":
                phonemes.append("t")
            elif c == "k":
                phonemes.append("k")
            elif c == "d":
                phonemes.append("d")
            elif c == "f":
                phonemes.append("f")
            elif c == "m":
                phonemes.append("m")
            elif c == "n":
                phonemes.append("n")
            elif c == "ñ":
                phonemes.append("ɲ")
            elif c == "l":
                phonemes.append("l")
            elif c == "w":
                phonemes.append("w")
            i += 1

        return phonemes

    def _transcribe_coda(self, coda: str) -> List[str]:
        """Convierte la coda silabica ortografica a fonemas base."""
        if not coda:
            return []

        cod = coda.lower()
        phonemes: List[str] = []
        i = 0
        n = len(cod)

        while i < n:
            c = cod[i]
            if c == "s":
                phonemes.append("s")
            elif c == "z":
                phonemes.append("s")
            elif c == "r":
                phonemes.append("ɾ")
            elif c == "l":
                phonemes.append("l")
            elif c == "n":
                phonemes.append("n")
            elif c == "m":
                phonemes.append("m")
            elif c == "d":
                phonemes.append("d")
            elif c in ("b", "v"):
                phonemes.append("b")
            elif c in ("c", "k"):
                phonemes.append("k")
            elif c == "p":
                phonemes.append("p")
            elif c == "t":
                phonemes.append("t")
            elif c == "g":
                phonemes.append("g")
            elif c == "x":
                phonemes.extend(["k", "s"])
            elif c == "j":
                phonemes.append("x")
            i += 1

        return phonemes

    def transcribe_word(
        self,
        word: str,
        dialect: Optional[Dialect] = None
    ) -> TransductionResult:
        """
        Transcribe una palabra ortografica a su representacion fonetica AFI
        segun las restricciones prosodicas y alofonicas del dialecto activo.
        """
        active_dialect = dialect or self.default_dialect
        pword = syllabify_word(word)

        # Fase 1: Generacion fonemica base silaba a silaba
        base_syllable_phonemes: List[List[str]] = []
        for idx, syll in enumerate(pword.syllables):
            is_initial = (idx == 0)
            ons_p = self._transcribe_onset(syll.onset, syll.nucleus, is_initial)
            nuc_p = self._transcribe_nucleus(syll.nucleus)
            cod_p = self._transcribe_coda(syll.coda)
            base_syllable_phonemes.append(ons_p + nuc_p + cod_p)

        # Fase 2: Aplicacion de reglas alofonicas dialectales
        if active_dialect is not None:
            derived_syllables = active_dialect.apply_allophonic_rules(pword, base_syllable_phonemes)
            dialect_code = active_dialect.code
            dialect_name = active_dialect.name
        else:
            derived_syllables = base_syllable_phonemes
            dialect_code = "STD"
            dialect_name = "Estándar Fonémico Base"

        # Fase 3: Construccion de la cadena AFI con fronteras silabicas y acento prosodico
        ipa_syllables_str: List[str] = []
        for idx, syl_phones in enumerate(derived_syllables):
            syl_str = "".join(syl_phones)
            if idx == pword.stressed_syllable_index:
                ipa_syllables_str.append(f"ˈ{syl_str}")
            else:
                ipa_syllables_str.append(syl_str)

        syllabified_ipa = ".".join(ipa_syllables_str)
        # Limpieza de duplicacion de acento con punto
        syllabified_ipa = syllabified_ipa.replace(".ˈ", "ˈ")
        ipa_full = f"/{syllabified_ipa}/"

        return TransductionResult(
            original_text=word,
            ipa_transcription=ipa_full,
            syllabified_ipa=syllabified_ipa,
            prosodic_word=pword,
            syllable_phonemes=derived_syllables,
            dialect_code=dialect_code,
            dialect_name=dialect_name
        )

    def transcribe_text(
        self,
        text: str,
        dialect: Optional[Dialect] = None
    ) -> List[TransductionResult]:
        """Transcribe una oracion o verso completo palabra por palabra."""
        words = re.findall(r"\b[\wáéíóúüàèòñ]+\b", text, flags=re.IGNORECASE)
        return [self.transcribe_word(w, dialect) for w in words]

    def transcribe_connected_text(
        self,
        text: str,
        dialect: Optional[Dialect] = None,
        apply_sandhi: bool = True
    ) -> Tuple[List[TransductionResult], str, List[Any]]:
        """
        Transcribe una oración o verso continuo aplicando opcionalmente fonotaxis
        post-léxica de sandhi (reencadenamiento silábico y resonorización de frontera).

        Returns:
            Tuple con (resultados individuales, cadena AFI conectada, lista de junturas de sandhi).
        """
        from .sandhi import SandhiEngine

        word_results = self.transcribe_text(text, dialect=dialect)
        if not word_results:
            return [], "", []

        if not apply_sandhi or len(word_results) < 2:
            connected_ipa = " ".join(r.syllabified_ipa for r in word_results)
            return word_results, connected_ipa, []

        engine = SandhiEngine()
        words_syllables = [copy.deepcopy(r.syllable_phonemes) for r in word_results]
        stresses = [r.prosodic_word.stressed_syllable_index for r in word_results]

        isogloss_dict = dialect.isogloss_vector.to_dict() if dialect else None
        modified_syllables, junctures = engine.apply_sandhi(words_syllables, isogloss_vector=isogloss_dict)
        connected_ipa = engine.format_connected_ipa(modified_syllables, stresses=stresses)

        return word_results, connected_ipa, junctures

