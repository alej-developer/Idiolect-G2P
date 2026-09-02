"""
Gramática Fonológica de Máxima Entropía (MaxEnt) y Optimidad Estocástica para Idiolect-G2P.
Maximum Entropy (MaxEnt) and Stochastic Optimality Theory Grammar for Idiolect-G2P.

Basado en:
- Boersma, P., & Hayes, B. (2001). Empirical tests of the Gradual Learning Algorithm.
  Linguistic Inquiry, 32(1), 45-86.
- Goldrick, M. (2007). Lexical representation and speech production.
  Language and Linguistics Compass, 1(5), 444-460.
- Hayes, B., & Wilson, C. (2008). A maximum entropy model of phonotactics and phonotactic learning.
  Linguistic Inquiry, 39(3), 379-440.
- Clements, G. N., & Hume, E. V. (1995). The internal organization of speech sounds.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Callable
import math

from ..core.phonetics import Phoneme, get_phoneme, compute_phonetic_distance


@dataclass
class Constraint:
    """
    Restricción fonológica formal en la teoría MaxEnt/OT.
    """
    name: str
    description: str
    is_markedness: bool              # True: Marcación, False: Fidelidad (Faithfulness)
    evaluator: Callable[[str, str, Dict[str, Any]], int] # Retorna el número de violaciones en el candidato


@dataclass
class MaxEntCandidate:
    """
    Candidato superficial evaluado por la gramática MaxEnt.
    """
    surface_form: str
    violations: Dict[str, int]       # Nombre de restricción -> Conteo de violaciones
    harmony: float = 0.0             # H(y) = \sum w_k * C_k(x, y)
    probability: float = 0.0         # P(y | x) = exp(-H(y)) / Z(x)


class MaxEntGrammar:
    """
    Gramática fonológica probabilística de Máxima Entropía.
    Modela la variación dialectal e idiolectal como pesos continuos sobre restricciones.
    """

    def __init__(self, constraint_weights: Optional[Dict[str, float]] = None):
        self.constraints: List[Constraint] = self._init_constraints()
        # Pesos por defecto (pueden ser modulados por el vector de isoglosas)
        self.weights: Dict[str, float] = constraint_weights or self._default_weights()

    def _init_constraints(self) -> List[Constraint]:
        """Inicializa la familia de restricciones fonológicas universales para el español."""
        c_list: List[Constraint] = []

        # ---------------------------------------------------------------------
        # 1. RESTRICCIONES DE MARCACIÓN (*M)
        # ---------------------------------------------------------------------
        def eval_coda_s(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # Penaliza sibilante en posición de coda (favorece aspiración [h] o elisión)
            coda_phones = ctx.get("coda_phones", [])
            return sum(1 for p in coda_phones if p in ("s", "s̺", "z"))

        c_list.append(Constraint(
            name="*CODA[s]",
            description="Prohíbe sibilantes alveolares en posición de coda silábica (marca de aspiración).",
            is_markedness=True,
            evaluator=eval_coda_s
        ))

        def eval_voiceless_before_sonorant(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # Penaliza obstruyente sorda ante consonante sonora (favorece resonorización de sandhi)
            violations = 0
            phones = ctx.get("all_phones", [])
            sonorants = {"m", "n", "ɲ", "ŋ", "l", "ʎ", "ɾ", "r", "b", "d", "g", "v", "z", "ʒ"}
            for i in range(len(phones) - 1):
                if phones[i] in ("s", "s̺", "θ") and phones[i + 1] in sonorants:
                    violations += 1
            return violations

        c_list.append(Constraint(
            name="*VOICELESS-BEFORE-SONORANT",
            description="Prohíbe sibilantes o interdentales sordas ante consonantes sonoras (induce sandhi sonoro).",
            is_markedness=True,
            evaluator=eval_voiceless_before_sonorant
        ))

        def eval_coda_liquid(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # Penaliza líquidas en coda (favorece lambdacismo / rotacismo)
            coda_phones = ctx.get("coda_phones", [])
            return sum(1 for p in coda_phones if p in ("ɾ", "l"))

        c_list.append(Constraint(
            name="*CODA[Liquid]",
            description="Prohíbe líquidas en posición de coda silábica (induce neutralización líquida).",
            is_markedness=True,
            evaluator=eval_coda_liquid
        ))

        def eval_onset_empty(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # ONSET: Sílabas deben tener ataque (favorece reencadenamiento interpalabra)
            has_empty_onset = ctx.get("has_vowel_initial_onset", False)
            return 1 if has_empty_onset else 0

        c_list.append(Constraint(
            name="ONSET",
            description="Las sílabas deben tener un constituyente de ataque (favorece reencadenamiento).",
            is_markedness=True,
            evaluator=eval_onset_empty
        ))

        # ---------------------------------------------------------------------
        # 2. RESTRICCIONES DE FIDELIDAD (FAITHFULNESS)
        # ---------------------------------------------------------------------
        def eval_ident_voice(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # IDENT-IO(Voice): Preservar el valor del rasgo [sonoro] subyacente
            und_phones = ctx.get("underlying_phones", [])
            sur_phones = ctx.get("surface_phones", [])
            v = 0
            for u, s in zip(und_phones, sur_phones):
                p_u = get_phoneme(u)
                p_s = get_phoneme(s)
                if p_u.features.voice != p_s.features.voice:
                    v += 1
            return v

        c_list.append(Constraint(
            name="IDENT(Voice)",
            description="El valor del rasgo [sonoro] en superficie debe ser idéntico al subyacente.",
            is_markedness=False,
            evaluator=eval_ident_voice
        ))

        def eval_ident_place(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # IDENT-IO(Place): Preservar el punto de articulación (e.g. lambdacismo viola IDENT[Place])
            und_phones = ctx.get("underlying_phones", [])
            sur_phones = ctx.get("surface_phones", [])
            v = 0
            for u, s in zip(und_phones, sur_phones):
                p_u = get_phoneme(u)
                p_s = get_phoneme(s)
                if (p_u.place != p_s.place) or (p_u.features.coronal != p_s.features.coronal):
                    v += 1
            return v

        c_list.append(Constraint(
            name="IDENT(Place)",
            description="El punto de articulación debe conservarse fiel al input subyacente.",
            is_markedness=False,
            evaluator=eval_ident_place
        ))

        def eval_max_c(underlying: str, surface: str, ctx: Dict[str, Any]) -> int:
            # MAX-IO(C): No elidir consonantes subyacentes
            len_u = len(ctx.get("underlying_phones", []))
            len_s = len(ctx.get("surface_phones", []))
            return max(0, len_u - len_s)

        c_list.append(Constraint(
            name="MAX(C)",
            description="Toda consonante subyacente debe tener un correlato en superficie (prohíbe elisión).",
            is_markedness=False,
            evaluator=eval_max_c
        ))

        return c_list

    def _default_weights(self) -> Dict[str, float]:
        """Pesos neutrales equilibrados."""
        return {
            "*CODA[s]": 1.5,
            "*VOICELESS-BEFORE-SONORANT": 2.5,
            "*CODA[Liquid]": 0.8,
            "ONSET": 2.0,
            "IDENT(Voice)": 2.0,
            "IDENT(Place)": 3.0,
            "MAX(C)": 4.0
        }

    def calibrate_weights_from_isoglosses(self, isogloss_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Calibra los pesos MaxEnt a partir de un vector continuo de isoglosas dialectales.
        Por ejemplo, una alta tasa de aspiración eleva el peso de *CODA[s] y reduce MAX(C).
        """
        w = dict(self._default_weights())
        asp = isogloss_dict.get("aspiration_s", 0.0)
        lam = isogloss_dict.get("lambdacism", 0.0)
        rho = isogloss_dict.get("rhotacism", 0.0)

        # Aspiración: eleva la penalización a sibilantes en coda y relaja fidelidad
        w["*CODA[s]"] = 1.0 + 5.0 * asp
        w["*VOICELESS-BEFORE-SONORANT"] = 2.0 + 3.0 * (1.0 - asp) # Resonorización activa en dialectos no aspirantes
        w["MAX(C)"] = max(0.5, 4.0 - 2.5 * asp)

        # Lambdacismo / Rotacismo
        w["*CODA[Liquid]"] = 0.5 + 4.0 * max(lam, rho)
        w["IDENT(Place)"] = max(0.8, 3.5 - 2.0 * max(lam, rho))

        return w

    def evaluate_candidates(
        self,
        underlying_seq: str,
        candidates: List[Tuple[str, Dict[str, Any]]],
        weights_override: Optional[Dict[str, float]] = None
    ) -> List[MaxEntCandidate]:
        """
        Evalúa un conjunto de candidatos fonéticos superficiales calculando su armonía H(y)
        y distribución de probabilidad de Gibbs P(y | x).

        Args:
            underlying_seq: Forma subyacente abstracta.
            candidates: Lista de tuplas (superficie_str, contexto_evaluacion_dict).
            weights_override: Pesos opcionales específicos del dialecto.

        Returns:
            Lista de MaxEntCandidate ordenados por probabilidad decreciente.
        """
        if not candidates:
            return []

        w = weights_override or self.weights
        eval_candidates: List[MaxEntCandidate] = []

        for surface_str, ctx in candidates:
            violations: Dict[str, int] = {}
            harmony = 0.0

            for c in self.constraints:
                viol_count = c.evaluator(underlying_seq, surface_str, ctx)
                violations[c.name] = viol_count
                constraint_weight = w.get(c.name, 1.0)
                harmony += constraint_weight * viol_count

            eval_candidates.append(MaxEntCandidate(
                surface_form=surface_str,
                violations=violations,
                harmony=harmony,
                probability=0.0
            ))

        # Cálculo de función de partición Z(x) = \sum exp(-H(y))
        # Uso de truco numérico para estabilidad: exp(-H + H_min)
        min_harmony = min(cand.harmony for cand in eval_candidates)
        unnormalized_probs = [math.exp(-(cand.harmony - min_harmony)) for cand in eval_candidates]
        total_z = sum(unnormalized_probs)

        for cand, prob in zip(eval_candidates, unnormalized_probs):
            cand.probability = prob / total_z if total_z > 0 else (1.0 / len(eval_candidates))

        eval_candidates.sort(key=lambda c: c.probability, reverse=True)
        return eval_candidates
