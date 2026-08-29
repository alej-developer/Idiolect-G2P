"""
Generador de explicaciones y dictamenes periciales en linguistica forense.
Forensic linguistics explanation and expert report generator.

Basado en:
- Coulthard, M., & Johnson, A. (2007). An introduction to forensic linguistics.
- French, P., & Watt, D. (2018). The Oxford handbook of forensic phonetics.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from .bayesian_profiler import IdiolectProfileResult, DialectProbability
from ..meter.phonetic_distance import RhymeMatch, RhymeType


@dataclass(frozen=True)
class DiscriminantEvidence:
    """Evidencia fonologica clave que discrimina entre hipotesis dialectales."""
    verse_1_num: int
    verse_2_num: int
    word_1: str
    word_2: str
    ipa_1: str
    ipa_2: str
    phonetic_phenomenon: str
    impact_description: str
    discriminating_power: float        # Puntuacion de impacto discriminatorio [0.0 - 1.0]


@dataclass(frozen=True)
class ForensicReport:
    """Dictamen pericial y reporte de perfilacion sociolinguistica e idiolectal."""
    case_identifier: str
    primary_hypothesis: str
    confidence_percentage: float
    isogloss_summary: Dict[str, float]
    discriminant_evidences: List[DiscriminantEvidence]
    dialect_ranking: List[Tuple[str, str, float]]  # [(code, name, posterior_prob)]
    sociolinguistic_conclusion: str


def generate_forensic_explanation(
    profile_result: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> ForensicReport:
    """
    Sintetiza un dictamen pericial forense detallado a partir de los resultados
    de la inferencia bayesiana y las restricciones fonotacticas observadas.
    """
    discriminant_evidences: List[DiscriminantEvidence] = []
    matches = profile_result.evaluated_rhyme_matches

    for match in matches:
        w1 = match.word_1_text.lower()
        w2 = match.word_2_text.lower()

        # 1. Deteccion de discriminacion por Seseo vs Distincion (/s/ vs /θ/)
        if (("z" in w1 or "z" in w2) or ("c" in w1 and any(v in w1 for v in "eiéí")) or ("c" in w2 and any(v in w2 for v in "eiéí"))) and ("s" in w1 or "s" in w2):
            phenomenon = "Neutralizacion sibilante (Seseo /s/ vs Distincion /θ/)"
            impact = (
                f"El par de rima '{match.word_1_text}' / '{match.word_2_text}' solo alcanza consonancia "
                f"perfecta bajo dialectos con seseo (/s/). En variantes con distincion peninsular (/θ/), "
                f"se genera una penalizacion metrica por discrepancia fonemica."
            )
            discriminant_evidences.append(DiscriminantEvidence(
                verse_1_num=match.verse_1_index,
                verse_2_num=match.verse_2_index,
                word_1=match.word_1_text,
                word_2=match.word_2_text,
                ipa_1=match.ipa_1,
                ipa_2=match.ipa_2,
                phonetic_phenomenon=phenomenon,
                impact_description=impact,
                discriminating_power=0.95
            ))

        # 2. Deteccion de discriminacion por Lambdacismo (/ɾ/ -> [l])
        elif ("r" in w1 and "l" in w2) or ("l" in w1 and "r" in w2):
            phenomenon = "Neutralizacion de liquidas en coda (Lambdacismo /ɾ/ -> [l] o Rotacismo /l/ -> [ɾ])"
            impact = (
                f"El par '{match.word_1_text}' / '{match.word_2_text}' constituye una evidencia determinante "
                f"de neutralizacion de liquidas en posicion de coda, caracteristica diagnostica del macro-dialecto caribeno."
            )
            discriminant_evidences.append(DiscriminantEvidence(
                verse_1_num=match.verse_1_index,
                verse_2_num=match.verse_2_index,
                word_1=match.word_1_text,
                word_2=match.word_2_text,
                ipa_1=match.ipa_1,
                ipa_2=match.ipa_2,
                phonetic_phenomenon=phenomenon,
                impact_description=impact,
                discriminating_power=0.98
            ))

        # 3. Deteccion de discriminacion por Yeismo vs Lleismo (/ʝ/ vs /ʎ/)
        elif ("ll" in w1 and "y" in w2) or ("y" in w1 and "ll" in w2):
            phenomenon = "Desfonologizacion palatal (Yeismo /ʝ/ vs Lleismo tradicional /ʎ/)"
            impact = (
                f"La rima entre '{match.word_1_text}' y '{match.word_2_text}' confirma que el autor no distingue "
                f"el fonema lateral palatal /ʎ/ del fricativo /ʝ/, descartando dialectos lleistas conservadores."
            )
            discriminant_evidences.append(DiscriminantEvidence(
                verse_1_num=match.verse_1_index,
                verse_2_num=match.verse_2_index,
                word_1=match.word_1_text,
                word_2=match.word_2_text,
                ipa_1=match.ipa_1,
                ipa_2=match.ipa_2,
                phonetic_phenomenon=phenomenon,
                impact_description=impact,
                discriminating_power=0.85
            ))

    # Redaccion de conclusiones sociolinguisticas formales
    best_dp = profile_result.dialect_probabilities[0]
    conf = best_dp.posterior_probability * 100.0

    conclusion = (
        f"El analisis de restricciones fonologicas inversas concluye que el texto presenta "
        f"una probabilidad a posteriori del {conf:.2f}% de haber sido compuesto bajo el sistema "
        f"fonotactico de '{best_dp.dialect_name}' (Region: {best_dp.region}). "
        f"Se han identificado {len(discriminant_evidences)} evidencias metrico-foneticas discriminantes "
        f"que maximizan la regularidad de la rima bajo esta hipotesis dialectal."
    )

    ranking = [
        (dp.dialect_code, dp.dialect_name, dp.posterior_probability)
        for dp in profile_result.dialect_probabilities[:5]
    ]

    return ForensicReport(
        case_identifier=case_id,
        primary_hypothesis=best_dp.dialect_name,
        confidence_percentage=conf,
        isogloss_summary=profile_result.estimated_isogloss_vector,
        discriminant_evidences=discriminant_evidences,
        dialect_ranking=ranking,
        sociolinguistic_conclusion=conclusion
    )
