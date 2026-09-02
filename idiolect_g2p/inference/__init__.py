"""
Modulo de inferencia bayesiana inversa y perfilacion forense de idiolectos.
Inverse Bayesian inference and forensic idiolect profiling module.
"""

from .bayesian_profiler import (
    DialectProbability,
    IdiolectProfileResult,
    BayesianIdiolectProfiler,
    profile_idiolect_from_poem,
)
from .forensic_explainer import (
    DiscriminantEvidence,
    ForensicReport,
    generate_forensic_explanation,
)
from .maxent_grammar import (
    Constraint,
    MaxEntCandidate,
    MaxEntGrammar,
)

__all__ = [
    "DialectProbability",
    "IdiolectProfileResult",
    "BayesianIdiolectProfiler",
    "profile_idiolect_from_poem",
    "DiscriminantEvidence",
    "ForensicReport",
    "generate_forensic_explanation",
    "Constraint",
    "MaxEntCandidate",
    "MaxEntGrammar",
]

