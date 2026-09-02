"""
Motor de inferencia bayesiana para desambiguacion fonologica dialectal inversa.
Bayesian inference engine for inverse dialectal phonological disambiguation.

Formalizacion matematica:
  D_opt, theta_opt = argmax P(D, theta | T, R)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

from ..meter.verse_analyzer import PoemAnalysis, Stanza, Verse, analyze_poem
from ..meter.phonetic_distance import RhymeMatch, evaluate_rhyme_pair
from ..dialects.base import Dialect, IsoglossVector
from ..dialects.registry import GLOBAL_DIALECT_REGISTRY, DialectRegistry
from ..core.transducer import G2PTransducer, TransductionResult
from ..core.phonetics import get_phoneme


@dataclass(frozen=True)
class DialectProbability:
    """Probabilidad a posteriori y evaluacion de un dialecto especifico."""
    dialect_code: str
    dialect_name: str
    region: str
    posterior_probability: float        # P(D | T, R) in [0.0, 1.0]
    log_likelihood: float
    total_phonetic_distance: float
    perfect_rhymes_count: int
    total_evaluated_pairs: int


@dataclass(frozen=True)
class IdiolectProfileResult:
    """Resultado completo de la perfilacion forense e inferencia del idiolecto."""
    predicted_dialect_code: str
    predicted_dialect_name: str
    confidence_score: float              # Probabilidad del dialecto ganador [0.0, 1.0]
    estimated_isogloss_vector: Dict[str, float]  # Vector continuo theta
    dialect_probabilities: List[DialectProbability]
    poem_analysis: PoemAnalysis
    evaluated_rhyme_matches: List[RhymeMatch]
    optimal_transcriptions: List[TransductionResult]


def _extract_vowel_nucleus_skeleton(rhyme_str: str) -> str:
    """Extrae unicamente el esqueleto de vocales del segmento rimante."""
    vowels = "aeiouáéíóúü"
    clean_vowels = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
        "a": "a", "e": "e", "i": "i", "o": "o", "u": "u"
    }
    return "".join(clean_vowels[c] for c in rhyme_str.lower() if c in vowels)


class BayesianIdiolectProfiler:
    """
    Infiere el dialecto e idiolecto optimo de un autor mediante la evaluacion
    multi-hipotesis de las restricciones de rima bajo el continuo dialectal hispanico.
    """

    def __init__(
        self,
        registry: Optional[DialectRegistry] = None,
        lambda_sensitivity: float = 16.0
    ) -> None:
        self.registry = registry or GLOBAL_DIALECT_REGISTRY
        self.lambda_sensitivity = lambda_sensitivity

    def _extract_rhyming_pairs(self, poem: PoemAnalysis) -> List[Tuple[Verse, Verse]]:
        """
        Extrae los pares de versos candidatos a rima en cada estrofa basandose en:
        1. Etiquetas metricas estructurales compartidas.
        2. Coincidencia del esqueleto de vocales tonicas y post-tonicas (asonancia base).
        3. Emparejamiento por esquemas clasicos (AABB, ABBA, ABAB, tiradas).
        """
        pairs: List[Tuple[Verse, Verse]] = []
        seen_pairs = set()

        for stanza in poem.stanzas:
            verses = stanza.verses
            n = len(verses)

            # 1. Comparar todos los versos dentro de la estrofa que comparten el mismo esqueleto vocalico
            for i in range(n):
                skel_i = _extract_vowel_nucleus_skeleton(verses[i].rhyme_segment_orthographic)
                for j in range(i + 1, n):
                    skel_j = _extract_vowel_nucleus_skeleton(verses[j].rhyme_segment_orthographic)
                    # Si comparten el mismo esqueleto vocalico (ej. a-o, e-o, a), son candidatos a rima
                    if skel_i == skel_j and skel_i != "":
                        pair_key = (verses[i].verse_number, verses[j].verse_number)
                        if pair_key not in seen_pairs:
                            pairs.append((verses[i], verses[j]))
                            seen_pairs.add(pair_key)

            # 2. Si no hay pares con esqueleto identico, comparar versos pares o esquemas clasicos
            if not pairs and n >= 2:
                for i in range(0, n - 1):
                    pair_key = (verses[i].verse_number, verses[i + 1].verse_number)
                    if pair_key not in seen_pairs:
                        pairs.append((verses[i], verses[i + 1]))
                        seen_pairs.add(pair_key)

        # Si aún no hay pares y hay más de un verso en todo el poema
        if not pairs and len(poem.all_verses) >= 2:
            for i in range(len(poem.all_verses) - 1):
                pairs.append((poem.all_verses[i], poem.all_verses[i + 1]))

        return pairs

    def profile_poem(
        self,
        poem_text: str,
        century_prior: Optional[int] = None
    ) -> IdiolectProfileResult:
        """
        Ejecuta la inferencia bayesiana completa sobre el texto poético.
        """
        poem_analysis = analyze_poem(poem_text)
        rhyming_pairs = self._extract_rhyming_pairs(poem_analysis)
        dialects = self.registry.list_all()

        transducer = G2PTransducer()
        from .maxent_grammar import MaxEntGrammar
        maxent_engine = MaxEntGrammar()

        dialect_evaluations: List[Dict[str, Any]] = []
        raw_log_likelihoods: List[float] = []

        for dialect in dialects:
            total_dist = 0.0
            perfect_count = 0
            evaluated_matches: List[RhymeMatch] = []
            maxent_weights = maxent_engine.calibrate_weights_from_isoglosses(dialect.isogloss_vector.to_dict())
            total_harmony_penalty = 0.0

            for v1, v2 in rhyming_pairs:
                match = evaluate_rhyme_pair(v1, v2, dialect=dialect, transducer=transducer)
                evaluated_matches.append(match)
                total_dist += match.phonetic_distance
                if match.is_perfect_consonant:
                    perfect_count += 1

                # Evaluar coherencia fonológica de la rima con la gramática MaxEnt del dialecto
                # Si una realización superficial en la rima es altamente disonante para el dialecto,
                # la armonía H(y) aporta una penalización probabilística suave.
                r1_phones = match.rhyme_phones_1
                r2_phones = match.rhyme_phones_2
                ctx_r = {
                    "coda_phones": [p for p in (r1_phones + r2_phones) if p in ("s", "s̺", "z", "h", "l", "ɾ")],
                    "all_phones": r1_phones + r2_phones,
                    "underlying_phones": r1_phones,
                    "surface_phones": r2_phones
                }
                cands = maxent_engine.evaluate_candidates(
                    underlying_seq="".join(r1_phones),
                    candidates=[("".join(r2_phones), ctx_r)],
                    weights_override=maxent_weights
                )
                if cands:
                    # Contribución MaxEnt calibrada como modulador continuo suave
                    total_harmony_penalty += cands[0].harmony * 0.005

            # Verosimilitud P(R | AFI(T, D)) = exp(-lambda * total_distance - harmony_penalty)
            multiplier = 1.2 if poem_analysis.is_consonant_expected else 0.9
            log_lik = -self.lambda_sensitivity * multiplier * total_dist - total_harmony_penalty


            # Modulador de Prior Diacronico
            if century_prior is not None:
                if century_prior in (16, 17) and dialect.code == "DIACHRONIC_GOLDEN_AGE":
                    log_lik += 2.0
                elif century_prior in (12, 13, 14, 15) and dialect.code == "DIACHRONIC_MEDIEVAL":
                    log_lik += 2.5
                elif century_prior >= 19 and "DIACHRONIC" in dialect.code:
                    log_lik -= 3.0

            raw_log_likelihoods.append(log_lik)
            dialect_evaluations.append({
                "dialect": dialect,
                "total_distance": total_dist,
                "perfect_count": perfect_count,
                "total_pairs": len(rhyming_pairs),
                "matches": evaluated_matches,
                "log_lik": log_lik
            })


        # Normalizacion Log-Sum-Exp
        max_log_lik = max(raw_log_likelihoods) if raw_log_likelihoods else 0.0
        exp_vals = [math.exp(ll - max_log_lik) for ll in raw_log_likelihoods]
        sum_exp = sum(exp_vals) if sum(exp_vals) > 0.0 else 1.0
        posteriors = [ev / sum_exp for ev in exp_vals]

        prob_results: List[DialectProbability] = []
        for deval, post_prob in zip(dialect_evaluations, posteriors):
            d_obj: Dialect = deval["dialect"]
            prob_results.append(DialectProbability(
                dialect_code=d_obj.code,
                dialect_name=d_obj.name,
                region=d_obj.region.value,
                posterior_probability=post_prob,
                log_likelihood=deval["log_lik"],
                total_phonetic_distance=deval["total_distance"],
                perfect_rhymes_count=deval["perfect_count"],
                total_evaluated_pairs=deval["total_pairs"]
            ))

        prob_results.sort(key=lambda dp: dp.posterior_probability, reverse=True)

        best_dialect_prob = prob_results[0]
        best_dialect = self.registry.get(best_dialect_prob.dialect_code) or dialects[0]

        # Estimacion de isoglosas continuas ponderadas
        theta_estimated: Dict[str, float] = {}
        first_iso_dict = dialects[0].isogloss_vector.to_dict()
        for iso_key in first_iso_dict.keys():
            weighted_iso_val = sum(
                dp.posterior_probability * (self.registry.get(dp.dialect_code).isogloss_vector.to_dict()[iso_key])
                for dp in prob_results
                if self.registry.get(dp.dialect_code) is not None
            )
            theta_estimated[iso_key] = round(weighted_iso_val, 4)

        # Transcripcion optima bajo el dialecto ganador
        optimal_transcriptions = [
            transducer.transcribe_word(w.original_text, dialect=best_dialect)
            for v in poem_analysis.all_verses
            for w in v.prosodic_words
        ]

        best_matches = next(
            deval["matches"] for deval in dialect_evaluations if deval["dialect"].code == best_dialect.code
        )

        return IdiolectProfileResult(
            predicted_dialect_code=best_dialect.code,
            predicted_dialect_name=best_dialect.name,
            confidence_score=best_dialect_prob.posterior_probability,
            estimated_isogloss_vector=theta_estimated,
            dialect_probabilities=prob_results,
            poem_analysis=poem_analysis,
            evaluated_rhyme_matches=best_matches,
            optimal_transcriptions=optimal_transcriptions
        )


def profile_idiolect_from_poem(
    poem_text: str,
    century_prior: Optional[int] = None
) -> IdiolectProfileResult:
    """Funcion auxiliar para perfilar un poema de forma directa."""
    profiler = BayesianIdiolectProfiler()
    return profiler.profile_poem(poem_text, century_prior=century_prior)
