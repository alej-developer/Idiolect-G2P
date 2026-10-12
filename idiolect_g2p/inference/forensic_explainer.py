"""
Generador de explicaciones y dictamenes periciales en linguistica forense.
Forensic linguistics explanation and expert report generator.

Basado en:
- Coulthard, M., & Johnson, A. (2007). An introduction to forensic linguistics.
- French, P., & Watt, D. (2018). The Oxford handbook of forensic phonetics.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

from .bayesian_profiler import IdiolectProfileResult, DialectProbability
from ..core.transducer import G2PTransducer
from ..dialects.base import Dialect
from ..dialects.registry import GLOBAL_DIALECT_REGISTRY, DialectRegistry
from ..meter.phonetic_distance import RhymeMatch, RhymeType, evaluate_rhyme_pair
from ..meter.verse_analyzer import Verse


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
    # Sin calculo validado todavia: se deja en None en lugar de puntuaciones fijas.
    discriminating_power: Optional[float] = None


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


@dataclass(frozen=True)
class _Feature:
    """Rasgo dialectal contrastable y los fonemas que deben aparecer en la rima."""
    phenomenon: str
    with_label: str                       # Hipotesis que presentan el rasgo
    without_label: str                    # Hipotesis que no lo presentan
    has_feature: Callable[[Dialect], bool]
    relevant_phones: FrozenSet[str]


_FEATURES: Tuple[_Feature, ...] = (
    _Feature(
        phenomenon="Neutralizacion sibilante (Seseo /s/ vs Distincion /θ/)",
        with_label="seseo",
        without_label="distincion /s/ - /θ/",
        has_feature=lambda d: d.isogloss_vector.seseo >= 0.5,
        relevant_phones=frozenset({"s", "s̺", "θ", "z", "dz", "ts"}),
    ),
    _Feature(
        phenomenon="Neutralizacion de liquidas en coda (Lambdacismo /ɾ/ -> [l] o Rotacismo /l/ -> [ɾ])",
        with_label="neutralizacion de liquidas",
        without_label="liquidas conservadas",
        has_feature=lambda d: (
            d.isogloss_vector.lambdacism >= 0.5 or d.isogloss_vector.rhotacism >= 0.5
        ),
        relevant_phones=frozenset({"l", "ɾ", "r"}),
    ),
    _Feature(
        phenomenon="Desfonologizacion palatal (Yeismo /ʝ/ vs Lleismo tradicional /ʎ/)",
        with_label="yeismo",
        without_label="lleismo",
        has_feature=lambda d: d.isogloss_vector.lleismo < 0.5,
        relevant_phones=frozenset({"ʎ", "ʝ", "ʒ", "ʃ", "j", "ɟ"}),
    ),
)

# Diferencia minima de distancia media entre grupos de hipotesis para considerar
# que el rasgo explica el par de rima.
_MIN_CONTRAST = 0.01


def _verse_index(profile_result: IdiolectProfileResult) -> Dict[int, Verse]:
    return {v.verse_number: v for v in profile_result.poem_analysis.all_verses}


def _feature_evidence(
    feature: _Feature,
    primary: Dialect,
    primary_match: RhymeMatch,
    verses: Tuple[Verse, Verse],
    dialects: List[Dialect],
    transducer: G2PTransducer,
) -> Optional[DiscriminantEvidence]:
    """
    Compara el mismo par de versos bajo las hipotesis con y sin el rasgo.
    Devuelve evidencia solo si el rasgo interviene en el segmento rimante, la
    distancia fonologica difiere entre ambos grupos y la hipotesis principal
    pertenece al grupo que explica mejor la rima.
    """
    with_group: List[RhymeMatch] = []
    without_group: List[RhymeMatch] = []
    for dialect in dialects:
        m = evaluate_rhyme_pair(verses[0], verses[1], dialect=dialect, transducer=transducer)
        (with_group if feature.has_feature(dialect) else without_group).append(m)

    if not with_group or not without_group:
        return None

    # El rasgo debe estar en el segmento rimante (no en el resto de la palabra).
    rhyme_phones = {
        p for m in with_group + without_group for p in m.rhyme_phones_1 + m.rhyme_phones_2
    }
    if not (rhyme_phones & feature.relevant_phones):
        return None

    mean_with = sum(m.phonetic_distance for m in with_group) / len(with_group)
    mean_without = sum(m.phonetic_distance for m in without_group) / len(without_group)
    if abs(mean_with - mean_without) < _MIN_CONTRAST:
        return None

    primary_has = feature.has_feature(primary)
    explains_better = mean_with < mean_without if primary_has else mean_without < mean_with
    if not explains_better:
        return None

    primary_label = feature.with_label if primary_has else feature.without_label
    other_label = feature.without_label if primary_has else feature.with_label
    mean_primary = mean_with if primary_has else mean_without
    mean_other = mean_without if primary_has else mean_with
    segmento = " ".join(primary_match.rhyme_phones_1) + " / " + " ".join(primary_match.rhyme_phones_2)

    impact = (
        f"En el segmento rimante del par '{primary_match.word_1_text}' / '{primary_match.word_2_text}' "
        f"({segmento}) interviene este rasgo. Bajo {primary.name} el par se clasifica como "
        f"'{primary_match.rhyme_type.value}' (distancia {primary_match.phonetic_distance:.3f}). "
        f"Las hipotesis con {primary_label} dan una distancia media de {mean_primary:.3f} y las de "
        f"{other_label}, {mean_other:.3f}."
    )
    return DiscriminantEvidence(
        verse_1_num=primary_match.verse_1_index,
        verse_2_num=primary_match.verse_2_index,
        word_1=primary_match.word_1_text,
        word_2=primary_match.word_2_text,
        ipa_1=primary_match.ipa_1,
        ipa_2=primary_match.ipa_2,
        phonetic_phenomenon=feature.phenomenon,
        impact_description=impact,
    )


def generate_forensic_explanation(
    profile_result: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001",
    registry: Optional[DialectRegistry] = None,
) -> ForensicReport:
    """
    Sintetiza un dictamen pericial forense detallado a partir de los resultados
    de la inferencia bayesiana y las restricciones fonotacticas observadas.

    Una evidencia dialectal solo se emite si el rasgo interviene en el segmento
    rimante y el mismo par de versos se comporta de forma distinta bajo las
    hipotesis con y sin ese rasgo. No se emiten puntuaciones de poder
    discriminante hasta definir y validar su calculo.
    """
    reg = registry or GLOBAL_DIALECT_REGISTRY
    dialects = reg.list_all()
    primary = reg.get(profile_result.predicted_dialect_code)
    verse_by_number = _verse_index(profile_result)
    transducer = G2PTransducer()

    discriminant_evidences: List[DiscriminantEvidence] = []
    if primary is not None:
        for match in profile_result.evaluated_rhyme_matches:
            v1 = verse_by_number.get(match.verse_1_index)
            v2 = verse_by_number.get(match.verse_2_index)
            if v1 is None or v2 is None:
                continue
            for feature in _FEATURES:
                evidence = _feature_evidence(
                    feature, primary, match, (v1, v2), dialects, transducer
                )
                if evidence is not None:
                    discriminant_evidences.append(evidence)

    # Redaccion de conclusiones sociolinguisticas formales
    best_dp = profile_result.dialect_probabilities[0]
    conf = best_dp.posterior_probability * 100.0

    if discriminant_evidences:
        evidence_sentence = (
            f"Se han identificado {len(discriminant_evidences)} evidencias metrico-foneticas "
            f"discriminantes: en esos pares la rima es mas regular bajo esta hipotesis dialectal "
            f"que bajo las hipotesis sin el rasgo correspondiente."
        )
    else:
        evidence_sentence = (
            "No se han identificado evidencias metrico-foneticas que distingan esta hipotesis "
            "de las alternativas: ningun rasgo dialectal explica por si solo la rima observada."
        )

    conclusion = (
        f"El analisis de restricciones fonologicas inversas concluye que el texto presenta "
        f"una probabilidad a posteriori del {conf:.2f}% de haber sido compuesto bajo el sistema "
        f"fonotactico de '{best_dp.dialect_name}' (Region: {best_dp.region}). "
        f"{evidence_sentence}"
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
