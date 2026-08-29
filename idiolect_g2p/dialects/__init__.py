"""
Modulo de variantes dialectales panhispanicas y diacronicas.
Pan-Hispanic and diachronic dialectal varieties module.
"""

from .base import Dialect, DialectRegion, IsoglossVector
from .peninsular import PeninsularStandardDialect
from .north_america import MexicanCentralDialect, MexicanNorthernChicanoDialect
from .caribbean import (
    CaribbeanStandardDialect,
    CaribbeanLambdacistDialect,
    CaribbeanRhotacistDialect,
)
from .andine import AndeanTraditionalDialect, AndeanAssibilatedDialect
from .rioplatense import RioplatenseZheistDialect, RioplatenseSheistDialect
from .chilean import ChileanDialect
from .central_america import CentralAmericanGeneralDialect, CostaRicanDialect
from .andalusian import WesternAndalusianDialect, EasternAndalusianDialect
from .canarian import CanarianDialect
from .diachronic import GoldenAgeDialect, MedievalSpanishDialect
from .registry import DialectRegistry, GLOBAL_DIALECT_REGISTRY

__all__ = [
    "Dialect",
    "DialectRegion",
    "IsoglossVector",
    "PeninsularStandardDialect",
    "MexicanCentralDialect",
    "MexicanNorthernChicanoDialect",
    "CaribbeanStandardDialect",
    "CaribbeanLambdacistDialect",
    "CaribbeanRhotacistDialect",
    "AndeanTraditionalDialect",
    "AndeanAssibilatedDialect",
    "RioplatenseZheistDialect",
    "RioplatenseSheistDialect",
    "ChileanDialect",
    "CentralAmericanGeneralDialect",
    "CostaRicanDialect",
    "WesternAndalusianDialect",
    "EasternAndalusianDialect",
    "CanarianDialect",
    "GoldenAgeDialect",
    "MedievalSpanishDialect",
    "DialectRegistry",
    "GLOBAL_DIALECT_REGISTRY",
]
