"""
Registro y catalogo central de dialectos del espanol.
Central dialect registry and catalog for pan-Hispanic and diachronic varieties.
"""

from __future__ import annotations
from typing import Dict, List, Optional
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


class DialectRegistry:
    """Catalogo centralizado e inmutable de todos los dialectos soportados."""

    def __init__(self) -> None:
        self._dialects: Dict[str, Dialect] = {}
        self._register_default_dialects()

    def _register_default_dialects(self) -> None:
        dialects_to_register: List[Dialect] = [
            # Iberoamérica
            PeninsularStandardDialect(),
            WesternAndalusianDialect(),
            EasternAndalusianDialect(),
            CanarianDialect(),
            # Norteamérica
            MexicanCentralDialect(),
            MexicanNorthernChicanoDialect(),
            # Centroamérica
            CentralAmericanGeneralDialect(),
            CostaRicanDialect(),
            # El Caribe
            CaribbeanStandardDialect(),
            CaribbeanLambdacistDialect(),
            CaribbeanRhotacistDialect(),
            # Región Andina
            AndeanTraditionalDialect(),
            AndeanAssibilatedDialect(),
            # Cono Sur
            RioplatenseZheistDialect(),
            RioplatenseSheistDialect(),
            ChileanDialect(),
            # Diacrónicos
            GoldenAgeDialect(),
            MedievalSpanishDialect(),
        ]
        for d in dialects_to_register:
            self._dialects[d.code] = d

    def get(self, code: str) -> Optional[Dialect]:
        """Obtiene un dialecto por su codigo unico."""
        return self._dialects.get(code.upper())

    def get_or_default(self, code: Optional[str] = None) -> Dialect:
        """Obtiene un dialecto o retorna el estandar peninsular si no existe."""
        if code and code.upper() in self._dialects:
            return self._dialects[code.upper()]
        return self._dialects["ES_PENINSULAR"]

    def list_all(self) -> List[Dialect]:
        """Retorna la lista de todos los dialectos disponibles."""
        return list(self._dialects.values())

    def list_by_region(self, region: DialectRegion) -> List[Dialect]:
        """Filtra dialectos por su macrorregion geografica o diacronica."""
        return [d for d in self._dialects.values() if d.region == region]

    def register_custom(self, dialect: Dialect) -> None:
        """Registra un dialecto personalizado en tiempo de ejecucion."""
        self._dialects[dialect.code] = dialect


# Instancia singleton del registro global
GLOBAL_DIALECT_REGISTRY: DialectRegistry = DialectRegistry()
