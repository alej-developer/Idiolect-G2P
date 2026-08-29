"""
Modulo de sintesis acustica y modelado formántico basado en el AFI.
Acoustic synthesis and formant modeling module based on the IPA.
"""

from .acoustic_features import (
    AcousticParameters,
    get_acoustic_parameters,
    IPA_ACOUSTIC_TABLE,
)
from .synthesizer import (
    IPAFormantSynthesizer,
    synthesize_ipa_to_wav,
)

__all__ = [
    "AcousticParameters",
    "get_acoustic_parameters",
    "IPA_ACOUSTIC_TABLE",
    "IPAFormantSynthesizer",
    "synthesize_ipa_to_wav",
]
