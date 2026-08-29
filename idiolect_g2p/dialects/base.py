"""
Clase base y representacion del continuo de isoglosas dialectales.
Base class and continuous isogloss vector representation for Spanish dialects.

Basado en:
- Lipski, J. M. (1994). Latin American Spanish.
- Alvar, M. (1996). Manual de dialectologia hispanica.
- Hualde, J. I. (2014). The sounds of Spanish.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any
from ..core.phonetics import Phoneme, get_phoneme
from ..core.syllabifier import ProsodicWord, Syllable


class DialectRegion(Enum):
    """Macrorregiones geograficas y diacronicas del mundo hispanohablante."""
    NORTH_AMERICA = "Norteamérica"
    CENTRAL_AMERICA = "Centroamérica"
    CARIBBEAN = "El Caribe"
    ANDINE = "Región Andina"
    SOUTHERN_CONE = "Cono Sur / Rioplatense"
    CHILE = "Chile"
    IBERIAN = "Iberoamérica / España Peninsular e Insular"
    DIACHRONIC = "Variantes Diacrónicas e Históricas"


@dataclass(frozen=True)
class IsoglossVector:
    """
    Vector continuo de parametros e isoglosas fonologicas: theta in [0.0, 1.0]^K.
    Permite modelar idiolectos hibridos y zonas de transicion dialectal.
    """
    seseo: float = 1.0                # 1.0 = Seseo pleno (/s/), 0.0 = Distincion (/θ/ vs /s/)
    aspiration_s: float = 0.0         # 1.0 = Aspiracion/elision total de /s/ en coda ([h]/[∅])
    lambdacism: float = 0.0           # 1.0 = Neutralizacion /ɾ/ -> [l] en coda (puelto)
    rhotacism: float = 0.0            # 1.0 = Neutralizacion /l/ -> [ɾ] en coda (arto)
    gemination: float = 0.0           # 1.0 = Asimilacion/geminacion consonantica (kanne)
    rehilamiento_voiced: float = 0.0  # 1.0 = Zheismo /ʝ/ -> [ʒ] (calle -> ka.ʒe)
    rehilamiento_voiceless: float = 0.0 # 1.0 = Sheismo /ʝ/ -> [ʃ] (calle -> ka.ʃe)
    lleismo: float = 0.0              # 1.0 = Distincion estricta lateral palatal /ʎ/ vs /ʝ/
    assibilation_r: float = 0.0       # 1.0 = Asibilacion vibrante /r/ -> [ř] / [ʐ] / [t͡ʂ]
    vowel_opening: float = 0.0        # 1.0 = Desdoblamiento vocalico fonologico ([ɛ, ɔ, æ])
    velar_nasal: float = 0.0          # 1.0 = Velarizacion de /n/ final de palabra a [ŋ]
    vocalic_reduction: float = 0.0    # 1.0 = Vocales caedizas o debilitadas (mexicano)
    glottal_j: float = 0.0            # 1.0 = Realizacion aspirada [h] de 'j' (en lugar de [x]/[χ])
    affricate_tl: float = 0.0         # 1.0 = Articulacion africada [t͡ɬ] de 'tl'
    diachronic_sibilants: float = 0.0 # 1.0 = Sistema medieval/clasico de 6 sibilantes
    initial_f_aspiration: float = 0.0 # 1.0 = Retencion de [h] procedente de F- latina

    def to_dict(self) -> Dict[str, float]:
        """Convierte el vector de isoglosas en un diccionario."""
        return {
            "seseo": self.seseo,
            "aspiration_s": self.aspiration_s,
            "lambdacism": self.lambdacism,
            "rhotacism": self.rhotacism,
            "gemination": self.gemination,
            "rehilamiento_voiced": self.rehilamiento_voiced,
            "rehilamiento_voiceless": self.rehilamiento_voiceless,
            "lleismo": self.lleismo,
            "assibilation_r": self.assibilation_r,
            "vowel_opening": self.vowel_opening,
            "velar_nasal": self.velar_nasal,
            "vocalic_reduction": self.vocalic_reduction,
            "glottal_j": self.glottal_j,
            "affricate_tl": self.affricate_tl,
            "diachronic_sibilants": self.diachronic_sibilants,
            "initial_f_aspiration": self.initial_f_aspiration,
        }


class Dialect(ABC):
    """
    Clase abstracta base para perfiles dialectales del espanol.
    Aplica el patron Strategy para transformar secuencias fonemicas en representaciones
    alofonicas contextuales segun las leyes fonotacticas de cada region.
    """

    def __init__(
        self,
        code: str,
        name: str,
        region: DialectRegion,
        description: str,
        isogloss_vector: Optional[IsoglossVector] = None,
        active_rules_description: Optional[List[str]] = None,
    ) -> None:
        self.code = code
        self.name = name
        self.region = region
        self.description = description
        self.isogloss_vector = isogloss_vector or IsoglossVector()
        self.active_rules_description = active_rules_description or []

    @abstractmethod
    def apply_allophonic_rules(
        self,
        word: ProsodicWord,
        base_phonemes: List[List[str]]
    ) -> List[List[str]]:
        """
        Aplica las transformaciones alofonicas contextuales propias del dialecto
        a la lista de fonemas segmentados por silaba.

        :param word: Objeto ProsodicWord con la estructura silabica y acento.
        :param base_phonemes: Lista de silabas, donde cada silaba es una lista de simbolos AFI.
        :return: Lista de silabas transformadas alofonicamente en simbolos AFI.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializacion estructurada del dialecto para la API."""
        return {
            "code": self.code,
            "name": self.name,
            "region": self.region.value,
            "description": self.description,
            "isogloss_vector": self.isogloss_vector.to_dict(),
            "active_rules": self.active_rules_description,
        }
