"""
Silabificador fonotactico y asignador prosodico para el espanol.
Rule-based phonotactic syllabifier and prosodic stress analyzer for Spanish.

Basado en las normas fonotacticas de la RAE/ASALE (2011) y Quilis (1993).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional, Final
import re


class StressType(Enum):
    """Clasificacion prosodica segun la posicion de la silaba tonica."""
    OXYTONE = auto()            # Aguda (ultima silaba)
    PAROXYTONE = auto()         # Llana / Grave (penultima silaba)
    PROPAROXYTONE = auto()      # Esdrujula (antepenultima silaba)
    SUPERPROPAROXYTONE = auto() # Sobresdrujula (anterior a la antepenultima)
    MONOSYLLABLE = auto()       # Monosilabo


class SyllableNucleus(Enum):
    """Naturaleza fonologica del nucleo silabico."""
    MONOPHTHONG = auto()        # Vocal simple
    DIPHTHONG_RISING = auto()   # Diptongo creciente (cerrada + abierta)
    DIPHTHONG_FALLING = auto()  # Diptongo decreciente (abierta + cerrada)
    DIPHTHONG_HOMOGENEOUS = auto() # Diptongo homogeneo (cerrada + cerrada)
    TRIPHTHONG = auto()         # Triptongo (cerrada + abierta + cerrada)
    HIATUS = auto()             # Hiato forzoso o acentual


# Conjuntos vocalicos canónicos
OPEN_VOWELS: Final[str] = "aeoáéóàèò"
CLOSED_VOWELS: Final[str] = "iuüy"
ACCENTED_CLOSED_VOWELS: Final[str] = "íú"
ALL_ACCENTED_VOWELS: Final[str] = "áéíóú"
ALL_VOWELS: Final[str] = "aeiouáéíóúüàèòy"

# Grupos consonanticos inseparables en ataque silabico (Onset clusters)
INSEPARABLE_ONSET_CLUSTERS: Final[Tuple[str, ...]] = (
    "pr", "pl", "br", "bl", "fr", "fl", "cr", "cl", "kr", "kl", "gr", "gl", "tr", "dr", "tl"
)
DIGRAPHS: Final[Tuple[str, ...]] = ("ch", "ll", "rr", "qu", "gu")


@dataclass(frozen=True)
class Syllable:
    """Representacion inmutable de una silaba fonotactica estructurada."""
    onset: str                  # Ataque silabico (consonantes previas al nucleo)
    nucleus: str                # Nucleo silabico (vocal, diptongo o triptongo)
    coda: str                   # Coda silabica (consonantes posteriores al nucleo)
    raw_text: str               # Texto ortografico de la silaba completa
    stressed: bool = False      # Indica si porta el acento prosodico principal
    syllable_index: int = 0     # Posicion relativa en la palabra (0 a N-1)
    total_syllables: int = 1    # Cantidad total de silabas en la palabra

    @property
    def rime(self) -> str:
        """Rima estructural de la silaba (Nucleo + Coda)."""
        return f"{self.nucleus}{self.coda}"


@dataclass(frozen=True)
class ProsodicWord:
    """Representacion de una palabra analizada prosodica y silabicamente."""
    original_text: str
    normalized_text: str
    syllables: List[Syllable]
    stress_type: StressType
    stressed_syllable_index: int

    @property
    def is_monosyllable(self) -> bool:
        """Determina si la palabra consta de una unica silaba."""
        return len(self.syllables) == 1

    @property
    def stressed_syllable(self) -> Syllable:
        """Recupera la silaba portadora del acento prosodico."""
        return self.syllables[self.stressed_syllable_index]

    @property
    def hyphenated(self) -> str:
        """Representacion silabeada con guiones ortograficos."""
        return "-".join(s.raw_text for s in self.syllables)


def normalize_orthography(text: str) -> str:
    """Limpia y normaliza caracteres ortograficos manteniendo tildes."""
    text = text.strip()
    return text.lower()


def _is_vowel(char: str) -> bool:
    """Verifica si un caracter es vocalico."""
    return char.lower() in ALL_VOWELS


def _split_vowel_groups(segment: str) -> List[Tuple[str, SyllableNucleus]]:
    """
    Segmenta una secuencia contigua de vocales en sus respectivos nucleos silabicos
    (diptongos, triptongos o hiatos) aplicando las leyes fonologicas del espanol.
    """
    nuclei: List[Tuple[str, SyllableNucleus]] = []
    i = 0
    n = len(segment)

    while i < n:
        # Caso Triptongo (Cerrada + Abierta + Cerrada sin acento en cerradas)
        if i + 2 < n:
            c1, c2, c3 = segment[i], segment[i + 1], segment[i + 2]
            if (c1 in "iuüy" and c2 in "aeoáéó" and c3 in "iuüy" and
                    c1 not in ACCENTED_CLOSED_VOWELS and c3 not in ACCENTED_CLOSED_VOWELS):
                nuclei.append((segment[i:i + 3], SyllableNucleus.TRIPHTHONG))
                i += 3
                continue

        # Caso Diptongo o Hiato de 2 vocales
        if i + 1 < n:
            v1, v2 = segment[i], segment[i + 1]

            # Hiato Acentual por vocal cerrada tónica (pa-ís, rí-o, ba-úl, ca-í-da)
            if (v1 in ACCENTED_CLOSED_VOWELS and v2 in ALL_VOWELS) or (v1 in ALL_VOWELS and v2 in ACCENTED_CLOSED_VOWELS):
                nuclei.append((v1, SyllableNucleus.HIATUS))
                i += 1
                continue

            # Hiato Simple por dos vocales abiertas (te-a-tro, ca-os, po-e-ma)
            if v1 in OPEN_VOWELS and v2 in OPEN_VOWELS:
                nuclei.append((v1, SyllableNucleus.HIATUS))
                i += 1
                continue

            # Diptongo Creciente: Cerrada atona + Abierta (via-je, bue-no)
            if v1 in CLOSED_VOWELS and v2 in OPEN_VOWELS and v1 not in ACCENTED_CLOSED_VOWELS:
                nuclei.append((v1 + v2, SyllableNucleus.DIPHTHONG_RISING))
                i += 2
                continue

            # Diptongo Decreciente: Abierta + Cerrada atona (cau-sa, pei-ne, hoy)
            if v1 in OPEN_VOWELS and v2 in CLOSED_VOWELS and v2 not in ACCENTED_CLOSED_VOWELS:
                nuclei.append((v1 + v2, SyllableNucleus.DIPHTHONG_FALLING))
                i += 2
                continue

            # Diptongo Homogeneo: Dos vocales cerradas distintas (ciu-dad, cui-da-do)
            if v1 in CLOSED_VOWELS and v2 in CLOSED_VOWELS and v1 != v2 and v1 not in ACCENTED_CLOSED_VOWELS and v2 not in ACCENTED_CLOSED_VOWELS:
                nuclei.append((v1 + v2, SyllableNucleus.DIPHTHONG_HOMOGENEOUS))
                i += 2
                continue

            # Vocales identicas forman hiato (cre-er, chi-i-ta, al-ba-ha-ca)
            if v1 == v2:
                nuclei.append((v1, SyllableNucleus.HIATUS))
                i += 1
                continue

        # Vocal simple aislada (Monoptongo)
        nuclei.append((segment[i], SyllableNucleus.MONOPHTHONG))
        i += 1

    return nuclei


def _split_consonant_cluster(cluster: str) -> Tuple[str, str]:
    """
    Divide un bloque de consonantes intervocálicas entre la coda de la silaba previa
    y el ataque de la silaba siguiente segun las restricciones de sonoridad maxima.
    """
    if not cluster:
        return "", ""

    # Tratar dígrafos como una sola unidad
    for dg in DIGRAPHS:
        if cluster == dg:
            return "", cluster

    # 1 sola consonante -> Pasa integramente al ataque siguiente (V-CV)
    if len(cluster) == 1:
        return "", cluster

    # 2 consonantes
    if len(cluster) == 2:
        if cluster in INSEPARABLE_ONSET_CLUSTERS or cluster in DIGRAPHS:
            return "", cluster
        return cluster[0], cluster[1]

    # 3 consonantes
    if len(cluster) == 3:
        if cluster[1:] in INSEPARABLE_ONSET_CLUSTERS or cluster[1:] in DIGRAPHS:
            return cluster[0], cluster[1:]
        return cluster[:2], cluster[2:]

    # 4 consonantes
    if len(cluster) >= 4:
        return cluster[:2], cluster[2:]

    return "", cluster


def syllabify_word(word: str) -> ProsodicWord:
    """
    Descompone una palabra en silabas fonotacticas estructuradas (ataque, nucleo, coda)
    e infiere la posicion exacta del acento prosodico segun las normas de la RAE.
    """
    cleaned = re.sub(r"[^\wáéíóúüàèòñ]", "", word, flags=re.IGNORECASE)
    if not cleaned:
        s = Syllable(onset="", nucleus=word, coda="", raw_text=word, stressed=True, syllable_index=0, total_syllables=1)
        return ProsodicWord(original_text=word, normalized_text=word, syllables=[s], stress_type=StressType.MONOSYLLABLE, stressed_syllable_index=0)

    normalized = normalize_orthography(cleaned)

    # Pre-procesamiento de digrafos mudos: 'qu' + e/i y 'gu' + e/i (sin diéresis)
    # Protegemos temporalmente para que la 'u' muda no sea categorizada como núcleo silábico independiente
    # Usamos marcadores especiales de carácter único
    prep = normalized
    prep = re.sub(r"qu([eiéí])", r"Q\1", prep)
    prep = re.sub(r"gu([eiéí])", r"G\1", prep)

    # Identificar tramos vocalicos y consonanticos
    tokens: List[Tuple[str, bool]] = []
    cur_text = ""
    cur_is_vowel = _is_vowel(prep[0])

    for char in prep:
        is_v = _is_vowel(char)
        if is_v == cur_is_vowel:
            cur_text += char
        else:
            tokens.append((cur_text, cur_is_vowel))
            cur_text = char
            cur_is_vowel = is_v
    if cur_text:
        tokens.append((cur_text, cur_is_vowel))

    # Extraer núcleos
    all_nuclei: List[Tuple[str, SyllableNucleus]] = []
    for tok_text, is_v in tokens:
        if is_v:
            sub_nuclei = _split_vowel_groups(tok_text)
            for n_txt, n_type in sub_nuclei:
                all_nuclei.append((n_txt, n_type))

    num_syllables = len(all_nuclei)

    if num_syllables == 0:
        raw_restored = normalized
        s = Syllable(onset=raw_restored, nucleus="", coda="", raw_text=raw_restored, stressed=True, syllable_index=0, total_syllables=1)
        return ProsodicWord(original_text=word, normalized_text=normalized, syllables=[s], stress_type=StressType.MONOSYLLABLE, stressed_syllable_index=0)

    raw_syllables: List[Tuple[str, str, str]] = []

    if num_syllables == 1:
        onset_part = tokens[0][0] if not tokens[0][1] else ""
        nucleus_part = all_nuclei[0][0]
        coda_part = tokens[-1][0] if not tokens[-1][1] and len(tokens) > 1 else ""
        raw_syllables.append((onset_part, nucleus_part, coda_part))
    else:
        temp_sylls: List[dict] = [{"onset": "", "nucleus": nuc[0], "coda": ""} for nuc in all_nuclei]
        first_onset = tokens[0][0] if not tokens[0][1] else ""
        temp_sylls[0]["onset"] = first_onset

        nuc_idx = 0
        for i in range(len(tokens)):
            if tokens[i][1]:
                sub_n = _split_vowel_groups(tokens[i][0])
                for _ in range(len(sub_n) - 1):
                    nuc_idx += 1
            else:
                if i > 0 and i < len(tokens) - 1:
                    coda_prev, onset_next = _split_consonant_cluster(tokens[i][0])
                    temp_sylls[nuc_idx]["coda"] = coda_prev
                    if nuc_idx + 1 < len(temp_sylls):
                        temp_sylls[nuc_idx + 1]["onset"] = onset_next
                    nuc_idx += 1

        if not tokens[-1][1]:
            temp_sylls[-1]["coda"] = tokens[-1][0]

        for ts in temp_sylls:
            raw_syllables.append((ts["onset"], ts["nucleus"], ts["coda"]))

    # Restaurar los marcadores 'Q' -> 'qu' y 'G' -> 'gu'
    restored_syllables: List[Tuple[str, str, str]] = []
    for ons, nuc, cod in raw_syllables:
        r_ons = ons.replace("Q", "qu").replace("G", "gu")
        r_nuc = nuc.replace("Q", "qu").replace("G", "gu")
        r_cod = cod.replace("Q", "qu").replace("G", "gu")
        restored_syllables.append((r_ons, r_nuc, r_cod))

    # Acento prosodico
    accented_idx: Optional[int] = None
    for idx, (ons, nuc, cod) in enumerate(restored_syllables):
        if any(c in ALL_ACCENTED_VOWELS for c in nuc):
            accented_idx = idx
            break

    if accented_idx is None:
        if num_syllables == 1:
            accented_idx = 0
        else:
            last_char = normalized[-1]
            if last_char in "aeiou" or last_char in "ns":
                accented_idx = num_syllables - 2
            else:
                accented_idx = num_syllables - 1

    pos_from_end = num_syllables - 1 - accented_idx
    if num_syllables == 1:
        stress_type = StressType.MONOSYLLABLE
    elif pos_from_end == 0:
        stress_type = StressType.OXYTONE
    elif pos_from_end == 1:
        stress_type = StressType.PAROXYTONE
    elif pos_from_end == 2:
        stress_type = StressType.PROPAROXYTONE
    else:
        stress_type = StressType.SUPERPROPAROXYTONE

    structured_syllables: List[Syllable] = []
    for idx, (ons, nuc, cod) in enumerate(restored_syllables):
        raw_s_text = f"{ons}{nuc}{cod}"
        is_stressed = (idx == accented_idx)
        structured_syllables.append(Syllable(
            onset=ons,
            nucleus=nuc,
            coda=cod,
            raw_text=raw_s_text,
            stressed=is_stressed,
            syllable_index=idx,
            total_syllables=num_syllables
        ))

    return ProsodicWord(
        original_text=word,
        normalized_text=normalized,
        syllables=structured_syllables,
        stress_type=stress_type,
        stressed_syllable_index=accented_idx
    )


def syllabify_text(text: str) -> List[ProsodicWord]:
    """Segmenta y analiza prosodicamente todas las palabras de un texto."""
    words = re.findall(r"\b[\wáéíóúüàèòñ]+\b", text, flags=re.IGNORECASE)
    return [syllabify_word(w) for w in words]
