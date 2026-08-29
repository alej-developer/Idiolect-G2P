"""
Analizador metrico, detector de estrofas y extractor de rimas.
Metrical scansion, stanza classifier, and rhyme extractor.

Basado en:
- Navarro-Colorado, B. (2017). A metrical scansion system for Spanish sonnets. DSH.
- Gerdas, P. (2000). A logic programming approach to Spanish poetic scansion.
- Quilis, A. (1993). Metrica espanola.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Final
import re

from ..core.syllabifier import ProsodicWord, Syllable, StressType, syllabify_word, syllabify_text


class StanzaType(Enum):
    """Tipologia estrofica de la tradicion poetica hispanica."""
    SONNET = "Soneto Clásico (14 versos endecasílabos: ABBA ABBA CDE CDE)"
    DECIMA_ESPINELA = "Décima Espinela (10 versos octosílabos: abbaaccddc)"
    OCTAVA_REAL = "Octava Real (8 versos endecasílabos: ABABABCC)"
    CUARTETO = "Cuarteto (4 versos de arte mayor: ABBA)"
    REDONDILLA = "Redondilla (4 versos de arte menor: abba)"
    SERVENTESIO = "Serventesio (4 versos de arte mayor: ABAB)"
    CUARTETA = "Cuarteta (4 versos de arte menor: abab)"
    TERCETO = "Terceto Encadenado (ABA BCB CDC)"
    ROMANCE = "Romance (Tirada indefinida con rima asonante en versos pares)"
    SILVA = "Silva / Verso Libre Estructurado"
    FREE_VERSE = "Verso Libre"


@dataclass(frozen=True)
class Verse:
    """Representacion estructurada de un verso individual."""
    verse_number: int
    raw_text: str
    prosodic_words: List[ProsodicWord]
    grammatical_syllables_count: int
    metrical_syllables_count: int
    sinalefas_count: int
    final_stress_compensation: int      # +1 aguda, 0 llana, -1 esdrujula
    rhyme_segment_orthographic: str     # Segmento rimante desde la ultima vocal tonica
    last_word: ProsodicWord


@dataclass(frozen=True)
class Stanza:
    """Representacion de una estrofa poetica."""
    stanza_number: int
    stanza_type: StanzaType
    verses: List[Verse]
    rhyme_pattern: str                  # Ej: "ABBA", "abbaaccddc"


@dataclass(frozen=True)
class PoemAnalysis:
    """Analisis metrico global de un poema o corpus versal."""
    raw_text: str
    stanzas: List[Stanza]
    all_verses: List[Verse]
    detected_stanza_type: StanzaType
    global_rhyme_scheme: str
    is_consonant_expected: bool


def _extract_rhyme_segment(word: ProsodicWord) -> str:
    """
    Extrae la rima ortografica a partir de la ultima vocal tonica de la palabra final del verso.
    """
    if not word.syllables:
        return word.normalized_text

    stressed_syl_idx = word.stressed_syllable_index
    stressed_syl = word.syllables[stressed_syl_idx]

    # Localizar la vocal portadora del acento dentro del nucleo
    nuc = stressed_syl.nucleus
    accent_char_idx = 0
    accented_vowels = "áéíóú"

    for idx, char in enumerate(nuc):
        if char in accented_vowels:
            accent_char_idx = idx
            break
    else:
        # En diptongos sin tilde, la vocal abierta lleva el acento prosodico
        if len(nuc) > 1:
            for idx, char in enumerate(nuc):
                if char in "aeo":
                    accent_char_idx = idx
                    break
            else:
                # Si son dos cerradas (ui, iu), la segunda lleva el acento natural
                accent_char_idx = 1
        else:
            accent_char_idx = 0

    # Segmento rimante de la silaba tonica: desde la vocal tonica + coda
    tonic_part = nuc[accent_char_idx:] + stressed_syl.coda

    # Concatenar las silabas restantes hasta el final de la palabra
    post_tonic_parts = [s.raw_text for s in word.syllables[stressed_syl_idx + 1:]]
    return (tonic_part + "".join(post_tonic_parts)).lower()


def _compute_sinalefas(words: List[ProsodicWord]) -> int:
    """
    Calcula el numero de sinalefas entre palabras contiguas
    (fusion metrica cuando una palabra finaliza en vocal y la siguiente inicia en vocal o 'h'+vocal).
    """
    if len(words) < 2:
        return 0

    vowels = "aeiouáéíóúüàèòy"
    sinalefas = 0

    for i in range(len(words) - 1):
        w1_norm = words[i].normalized_text
        w2_norm = words[i + 1].normalized_text

        if not w1_norm or not w2_norm:
            continue

        last_char_w1 = w1_norm[-1]
        first_char_w2 = w2_norm[0]

        # Si w2 inicia con 'h', evaluar la siguiente letra
        if first_char_w2 == "h" and len(w2_norm) > 1:
            first_char_w2 = w2_norm[1]

        # Union vocal + vocal
        if last_char_w1 in vowels and first_char_w2 in vowels:
            sinalefas += 1

    return sinalefas


def analyze_verse(verse_text: str, verse_number: int = 1) -> Verse:
    """
    Analiza un verso extrayendo su estructura prosodica, conteo silabico,
    sinalefas, compensacion por acento final y segmento de rima.
    """
    clean_text = verse_text.strip()
    words = syllabify_text(clean_text)

    if not words:
        dummy_word = syllabify_word(clean_text or "a")
        return Verse(
            verse_number=verse_number,
            raw_text=verse_text,
            prosodic_words=[dummy_word],
            grammatical_syllables_count=1,
            metrical_syllables_count=1,
            sinalefas_count=0,
            final_stress_compensation=0,
            rhyme_segment_orthographic="a",
            last_word=dummy_word
        )

    # 1. Conteo silabico gramatical total
    grammatical_sylls = sum(len(w.syllables) for w in words)

    # 2. Conteo de sinalefas
    sinalefas = _compute_sinalefas(words)

    # 3. Ley del acento final (oxítonos +1, paroxítonos 0, proparoxítonos -1)
    last_w = words[-1]
    if last_w.stress_type == StressType.OXYTONE or (last_w.is_monosyllable and last_w.stressed_syllable.coda != ""):
        stress_comp = 1
    elif last_w.stress_type == StressType.PROPAROXYTONE:
        stress_comp = -1
    elif last_w.stress_type == StressType.SUPERPROPAROXYTONE:
        stress_comp = -2
    else:
        stress_comp = 0

    metrical_sylls = max(1, grammatical_sylls - sinalefas + stress_comp)
    rhyme_seg = _extract_rhyme_segment(last_w)

    return Verse(
        verse_number=verse_number,
        raw_text=clean_text,
        prosodic_words=words,
        grammatical_syllables_count=grammatical_sylls,
        metrical_syllables_count=metrical_sylls,
        sinalefas_count=sinalefas,
        final_stress_compensation=stress_comp,
        rhyme_segment_orthographic=rhyme_seg,
        last_word=last_w
    )


def _infer_rhyme_labels(verses: List[Verse]) -> List[str]:
    """
    Asigna etiquetas de rima (A, B, C...) a una lista de versos
    segun la identidad o maxima proximidad de sus segmentos de rima.
    """
    labels: List[str] = []
    seen_rhymes: Dict[str, str] = {}
    current_label_ord = ord('A')

    for v in verses:
        r_seg = v.rhyme_segment_orthographic
        # Normalizacion simple para etiquetado inicial
        r_norm = re.sub(r"[áà]", "a", r_seg)
        r_norm = re.sub(r"[éè]", "e", r_norm)
        r_norm = re.sub(r"[í]", "i", r_norm)
        r_norm = re.sub(r"[óò]", "o", r_norm)
        r_norm = re.sub(r"[úü]", "u", r_norm)

        # Buscar rima coincidente
        matched_label: Optional[str] = None
        for seen_r, lbl in seen_rhymes.items():
            if seen_r == r_norm:
                matched_label = lbl
                break

        if matched_label is not None:
            labels.append(matched_label)
        else:
            new_label = chr(current_label_ord)
            seen_rhymes[r_norm] = new_label
            labels.append(new_label)
            current_label_ord += 1

    # Ajustar mayusculas/minusculas segun arte mayor (>=9 silabas) o menor (<=8 silabas)
    adjusted_labels: List[str] = []
    for v, lbl in zip(verses, labels):
        if v.metrical_syllables_count <= 8:
            adjusted_labels.append(lbl.lower())
        else:
            adjusted_labels.append(lbl.upper())

    return adjusted_labels


def _detect_stanza_type(stanzas: List[Stanza], total_verses: int) -> StanzaType:
    """Clasifica el molde estrofico predominante del poema."""
    if total_verses == 14 and len(stanzas) in (2, 4, 1):
        return StanzaType.SONNET
    if total_verses == 10 and len(stanzas) == 1:
        return StanzaType.DECIMA_ESPINELA
    if total_verses == 8 and len(stanzas) == 1:
        return StanzaType.OCTAVA_REAL
    if total_verses == 4:
        first_s = stanzas[0]
        patt = first_s.rhyme_pattern.lower()
        if patt in ("abba", "abba."):
            return StanzaType.REDONDILLA if first_s.verses[0].metrical_syllables_count <= 8 else StanzaType.CUARTETO
        if patt in ("abab", "abab."):
            return StanzaType.CUARTETA if first_s.verses[0].metrical_syllables_count <= 8 else StanzaType.SERVENTESIO
    if total_verses >= 16 and len(stanzas) == 1:
        return StanzaType.ROMANCE

    return StanzaType.FREE_VERSE


def analyze_poem(poem_text: str) -> PoemAnalysis:
    """
    Analiza un poema completo segmentando estrofas y versos, calculando la metrica
    y deduciendo el regimen estrofico y la expectativa de rima.
    """
    raw_stanzas = re.split(r"\n\s*\n", poem_text.strip())
    analyzed_stanzas: List[Stanza] = []
    all_verses: List[Verse] = []
    verse_counter = 1

    for s_idx, s_text in enumerate(raw_stanzas, start=1):
        lines = [line.strip() for line in s_text.splitlines() if line.strip()]
        if not lines:
            continue

        stanza_verses: List[Verse] = []
        for line in lines:
            v_obj = analyze_verse(line, verse_number=verse_counter)
            stanza_verses.append(v_obj)
            all_verses.append(v_obj)
            verse_counter += 1

        rhyme_labels = _infer_rhyme_labels(stanza_verses)
        pattern_str = "".join(rhyme_labels)

        st_type = StanzaType.FREE_VERSE
        if len(stanza_verses) == 4:
            if pattern_str.lower() == "abba":
                st_type = StanzaType.REDONDILLA if stanza_verses[0].metrical_syllables_count <= 8 else StanzaType.CUARTETO
            elif pattern_str.lower() == "abab":
                st_type = StanzaType.CUARTETA if stanza_verses[0].metrical_syllables_count <= 8 else StanzaType.SERVENTESIO

        analyzed_stanzas.append(Stanza(
            stanza_number=s_idx,
            stanza_type=st_type,
            verses=stanza_verses,
            rhyme_pattern=pattern_str
        ))

    total_v = len(all_verses)
    detected_type = _detect_stanza_type(analyzed_stanzas, total_v)
    global_scheme = " - ".join(s.rhyme_pattern for s in analyzed_stanzas)

    # Sonetos, decimas, octavas reales y cuartetos exigen rima consonante perfecta
    is_consonant = detected_type in (
        StanzaType.SONNET,
        StanzaType.DECIMA_ESPINELA,
        StanzaType.OCTAVA_REAL,
        StanzaType.CUARTETO,
        StanzaType.REDONDILLA,
        StanzaType.SERVENTESIO,
        StanzaType.CUARTETA,
        StanzaType.TERCETO
    )

    return PoemAnalysis(
        raw_text=poem_text,
        stanzas=analyzed_stanzas,
        all_verses=all_verses,
        detected_stanza_type=detected_type,
        global_rhyme_scheme=global_scheme,
        is_consonant_expected=is_consonant
    )
