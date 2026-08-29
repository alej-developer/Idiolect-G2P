"""
Modelado fonologico, rasgos distintivos y matriz de distancias foneticas.
Phonological modeling, distinctive features, and phonetic distance metrics.

Basado en:
- Chomsky, N., & Halle, M. (1968). The sound pattern of English.
- Clements, G. N., & Hume, E. V. (1995). The internal organization of speech sounds.
- Martinez Celdran, E., & Fernandez Planas, A. M. (2007). Manual de fonetica espanola.
- International Phonetic Association (1999). Handbook of the IPA.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, Tuple, List, Final
import math


class PhonemeType(Enum):
    """Categoria taxonomica fundamental del fonema o alofono."""
    VOWEL = auto()
    CONSONANT = auto()
    GLIDE = auto()
    SUPRASEGMENTAL = auto()


class PlaceOfArticulation(Enum):
    """Punto de articulacion segun la Asociacion Fonetica Internacional."""
    NONE = auto()
    BILABIAL = auto()
    LABIODENTAL = auto()
    INTERDENTAL = auto()
    DENTAL = auto()
    ALVEOLAR = auto()
    POSTALVEOLAR = auto()
    RETROFLEX = auto()
    ALVEOLOPALATAL = auto()
    PALATAL = auto()
    VELAR = auto()
    UVULAR = auto()
    GLOTTAL = auto()


class MannerOfArticulation(Enum):
    """Modo de articulacion segun la Asociacion Fonetica Internacional."""
    NONE = auto()
    OCCLUSIVE = auto()
    FRICATIVE = auto()
    APPROXIMANT = auto()
    AFFRICATE = auto()
    NASAL = auto()
    TAP_FLAP = auto()
    TRILL = auto()
    LATERAL_APPROXIMANT = auto()
    LATERAL_FRICATIVE = auto()
    LATERAL_AFFRICATE = auto()


class Phonation(Enum):
    """Estado glotico y sonoridad."""
    VOICELESS = auto()
    VOICED = auto()


class VowelHeight(Enum):
    """Apertura o altura de la cavidad oral en vocales."""
    NONE = auto()
    CLOSE = auto()         # Cerrada / Alta
    NEAR_CLOSE = auto()    # Semicerrada
    CLOSE_MID = auto()     # Media cerrada
    OPEN_MID = auto()      # Media abierta
    NEAR_OPEN = auto()     # Semiabierta
    OPEN = auto()          # Abierta / Baja


class VowelBackness(Enum):
    """Posicion anteroposterior del dorso lingual."""
    NONE = auto()
    FRONT = auto()         # Anterior
    CENTRAL = auto()       # Central
    BACK = auto()          # Posterior


class VowelRounding(Enum):
    """Redondeamiento o labializacion vocálica."""
    NONE = auto()
    UNROUNDED = auto()
    ROUNDED = auto()


@dataclass(frozen=True)
class PhonologicalFeatures:
    """
    Sistema de rasgos distintivos binarios basados en Chomsky & Halle (1968)
    y la Geometria de Rasgos de Clements & Hume (1995).
    """
    # Nodo Raiz (Root Node)
    syllabic: bool = False
    consonantal: bool = True
    sonorant: bool = False

    # Modo (Manner Node)
    continuant: bool = False
    delayed_release: bool = False
    nasal: bool = False
    lateral: bool = False
    strident: bool = False

    # Laringeo (Laryngeal Node)
    voice: bool = False
    spread_glottis: bool = False  # Para aspiradas [h]
    constricted_glottis: bool = False

    # Cavidad Oral y Punto (Place Node)
    labial: bool = False
    coronal: bool = False
    anterior: bool = False
    distributed: bool = False
    dorsal: bool = False
    high: bool = False
    low: bool = False
    back: bool = False
    tense: bool = False

    def to_vector(self) -> List[float]:
        """Convierte los rasgos en un vector binario normalizado."""
        return [
            1.0 if self.syllabic else 0.0,
            1.0 if self.consonantal else 0.0,
            1.0 if self.sonorant else 0.0,
            1.0 if self.continuant else 0.0,
            1.0 if self.delayed_release else 0.0,
            1.0 if self.nasal else 0.0,
            1.0 if self.lateral else 0.0,
            1.0 if self.strident else 0.0,
            1.0 if self.voice else 0.0,
            1.0 if self.spread_glottis else 0.0,
            1.0 if self.constricted_glottis else 0.0,
            1.0 if self.labial else 0.0,
            1.0 if self.coronal else 0.0,
            1.0 if self.anterior else 0.0,
            1.0 if self.distributed else 0.0,
            1.0 if self.dorsal else 0.0,
            1.0 if self.high else 0.0,
            1.0 if self.low else 0.0,
            1.0 if self.back else 0.0,
            1.0 if self.tense else 0.0,
        ]


# Ponderacion jerarquica de rasgos segun Clements & Hume (1995)
FEATURE_WEIGHTS: Final[List[float]] = [
    1.2,  # syllabic (critico para distincion vocal/consonante)
    1.0,  # consonantal
    0.9,  # sonorant
    0.8,  # continuant
    0.7,  # delayed_release
    0.9,  # nasal
    0.8,  # lateral
    0.7,  # strident
    0.6,  # voice (menor peso en ciertas neutralizaciones de rima)
    0.7,  # spread_glottis
    0.6,  # constricted_glottis
    0.8,  # labial
    0.8,  # coronal
    0.6,  # anterior
    0.5,  # distributed
    0.8,  # dorsal
    0.7,  # high
    0.7,  # low
    0.7,  # back
    0.5,  # tense
]


@dataclass(frozen=True)
class Phoneme:
    """
    Representacion inmutable de un fonema o alofono en el estandar AFI.
    Incluye rasgos articulatorios y parametros acusticos formánticos para sintesis.
    """
    symbol: str
    name: str
    phoneme_type: PhonemeType
    place: PlaceOfArticulation = PlaceOfArticulation.NONE
    manner: MannerOfArticulation = MannerOfArticulation.NONE
    phonation: Phonation = Phonation.VOICELESS
    vowel_height: VowelHeight = VowelHeight.NONE
    vowel_backness: VowelBackness = VowelBackness.NONE
    vowel_rounding: VowelRounding = VowelRounding.NONE
    features: PhonologicalFeatures = field(default_factory=PhonologicalFeatures)

    # Parametros acusticos para sintesis formantica (valores medios de referencia en Hz)
    f1: float = 0.0
    f2: float = 0.0
    f3: float = 0.0
    f4: float = 3500.0
    bandwidth1: float = 80.0
    bandwidth2: float = 100.0
    bandwidth3: float = 120.0
    noise_level: float = 0.0      # Nivel de ruido fricativo/explosion [0.0 - 1.0]
    typical_duration_ms: float = 100.0

    def is_vowel(self) -> bool:
        """Determina si la entidad es una vocal o nucleo silabico."""
        return self.phoneme_type == PhonemeType.VOWEL

    def is_consonant(self) -> bool:
        """Determina si la entidad es una consonante."""
        return self.phoneme_type == PhonemeType.CONSONANT

    def is_glide(self) -> bool:
        """Determina si la entidad es una semivocal o semiconsonante."""
        return self.phoneme_type == PhonemeType.GLIDE


def _create_phoneme_inventory() -> Dict[str, Phoneme]:
    """
    Construye el inventario integral de fonemas y alofonos del espanol panhispanico
    y diacronico con sus rasgos distintivos y parametros acusticos formánticos.
    """
    inv: Dict[str, Phoneme] = {}

    def add(p: Phoneme) -> None:
        inv[p.symbol] = p

    # -------------------------------------------------------------------------
    # VOCALES CANONICAS Y ALOFONICAS
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="a",
        name="Vocal abierta central no redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.OPEN,
        vowel_backness=VowelBackness.CENTRAL,
        vowel_rounding=VowelRounding.UNROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, low=True, tense=True),
        f1=800.0, f2=1400.0, f3=2600.0, typical_duration_ms=130.0
    ))
    add(Phoneme(
        symbol="e",
        name="Vocal media anterior no redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.CLOSE_MID,
        vowel_backness=VowelBackness.FRONT,
        vowel_rounding=VowelRounding.UNROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, tense=True),
        f1=500.0, f2=1900.0, f3=2600.0, typical_duration_ms=110.0
    ))
    add(Phoneme(
        symbol="i",
        name="Vocal cerrada anterior no redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.CLOSE,
        vowel_backness=VowelBackness.FRONT,
        vowel_rounding=VowelRounding.UNROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, high=True, tense=True),
        f1=300.0, f2=2300.0, f3=3000.0, typical_duration_ms=90.0
    ))
    add(Phoneme(
        symbol="o",
        name="Vocal media posterior redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.CLOSE_MID,
        vowel_backness=VowelBackness.BACK,
        vowel_rounding=VowelRounding.ROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, back=True, labial=True, tense=True),
        f1=500.0, f2=1000.0, f3=2500.0, typical_duration_ms=110.0
    ))
    add(Phoneme(
        symbol="u",
        name="Vocal cerrada posterior redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.CLOSE,
        vowel_backness=VowelBackness.BACK,
        vowel_rounding=VowelRounding.ROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, high=True, back=True, labial=True, tense=True),
        f1=300.0, f2=800.0, f3=2400.0, typical_duration_ms=90.0
    ))

    # Vocales abiertas alofonicas (Andaluz Oriental / desdoblamiento vocálico)
    add(Phoneme(
        symbol="ɛ",
        name="Vocal semiabierta anterior no redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.OPEN_MID,
        vowel_backness=VowelBackness.FRONT,
        vowel_rounding=VowelRounding.UNROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, low=False, tense=False),
        f1=580.0, f2=1780.0, f3=2550.0, typical_duration_ms=135.0
    ))
    add(Phoneme(
        symbol="ɔ",
        name="Vocal semiabierta posterior redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.OPEN_MID,
        vowel_backness=VowelBackness.BACK,
        vowel_rounding=VowelRounding.ROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, back=True, labial=True, tense=False),
        f1=580.0, f2=920.0, f3=2450.0, typical_duration_ms=135.0
    ))
    add(Phoneme(
        symbol="æ",
        name="Vocal casi abierta anterior no redondeada",
        phoneme_type=PhonemeType.VOWEL,
        vowel_height=VowelHeight.NEAR_OPEN,
        vowel_backness=VowelBackness.FRONT,
        vowel_rounding=VowelRounding.UNROUNDED,
        features=PhonologicalFeatures(syllabic=True, consonantal=False, sonorant=True, continuant=True, voice=True, low=True, tense=False),
        f1=750.0, f2=1600.0, f3=2600.0, typical_duration_ms=145.0
    ))

    # Semivocales / Glides
    add(Phoneme(
        symbol="j",
        name="Aproximante palatal / semivocal anterior",
        phoneme_type=PhonemeType.GLIDE,
        place=PlaceOfArticulation.PALATAL,
        manner=MannerOfArticulation.APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(syllabic=False, consonantal=False, sonorant=True, continuant=True, voice=True, high=True),
        f1=300.0, f2=2250.0, f3=2900.0, typical_duration_ms=60.0
    ))
    add(Phoneme(
        symbol="w",
        name="Aproximante labiovelar / semivocal posterior",
        phoneme_type=PhonemeType.GLIDE,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(syllabic=False, consonantal=False, sonorant=True, continuant=True, voice=True, high=True, back=True, labial=True),
        f1=300.0, f2=750.0, f3=2300.0, typical_duration_ms=60.0
    ))

    # -------------------------------------------------------------------------
    # CONSONANTES OCLUSIVAS Y APROXIMANTES
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="p",
        name="Oclusiva bilabial sorda",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.BILABIAL,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, labial=True, voice=False),
        noise_level=0.7, typical_duration_ms=80.0
    ))
    add(Phoneme(
        symbol="b",
        name="Oclusiva bilabial sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.BILABIAL,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, labial=True, voice=True),
        f1=200.0, f2=900.0, f3=2200.0, noise_level=0.3, typical_duration_ms=70.0
    ))
    add(Phoneme(
        symbol="β",
        name="Aproximante bilabial sonora (alofono espirantizado)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.BILABIAL,
        manner=MannerOfArticulation.APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, continuant=True, labial=True, voice=True),
        f1=300.0, f2=1000.0, f3=2300.0, noise_level=0.1, typical_duration_ms=60.0
    ))
    add(Phoneme(
        symbol="t",
        name="Oclusiva dental sorda",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.DENTAL,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, coronal=True, anterior=True, distributed=True, voice=False),
        noise_level=0.8, typical_duration_ms=85.0
    ))
    add(Phoneme(
        symbol="d",
        name="Oclusiva dental sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.DENTAL,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, coronal=True, anterior=True, distributed=True, voice=True),
        f1=200.0, f2=1600.0, f3=2600.0, noise_level=0.3, typical_duration_ms=75.0
    ))
    add(Phoneme(
        symbol="ð",
        name="Aproximante/fricativa dental sonora (alofono espirantizado)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.DENTAL,
        manner=MannerOfArticulation.APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, continuant=True, coronal=True, anterior=True, distributed=True, voice=True),
        f1=350.0, f2=1500.0, f3=2500.0, noise_level=0.2, typical_duration_ms=60.0
    ))
    add(Phoneme(
        symbol="k",
        name="Oclusiva velar sorda",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, dorsal=True, high=True, back=True, voice=False),
        noise_level=0.85, typical_duration_ms=90.0
    ))
    add(Phoneme(
        symbol="g",
        name="Oclusiva velar sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.OCCLUSIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, dorsal=True, high=True, back=True, voice=True),
        f1=200.0, f2=1800.0, f3=2400.0, noise_level=0.3, typical_duration_ms=75.0
    ))
    add(Phoneme(
        symbol="ɣ",
        name="Aproximante velar sonora (alofono espirantizado)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, continuant=True, dorsal=True, high=True, back=True, voice=True),
        f1=350.0, f2=1700.0, f3=2400.0, noise_level=0.2, typical_duration_ms=60.0
    ))

    # -------------------------------------------------------------------------
    # CONSONANTES FRICATIVAS Y SIBILANTES
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="f",
        name="Fricativa labiodental sorda",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.LABIODENTAL,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, labial=True, strident=True, voice=False),
        noise_level=0.6, typical_duration_ms=100.0
    ))
    add(Phoneme(
        symbol="θ",
        name="Fricativa interdental sorda (distincion peninsular)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.INTERDENTAL,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=True, distributed=True, strident=False, voice=False),
        noise_level=0.5, typical_duration_ms=100.0
    ))
    add(Phoneme(
        symbol="s",
        name="Fricativa alveolar sorda predorsal (seseo / hispanoamerica)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=True, strident=True, voice=False),
        noise_level=0.9, typical_duration_ms=110.0
    ))
    add(Phoneme(
        symbol="s̺",
        name="Fricativa apicoalveolar sorda (peninsular septentrional)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=True, distributed=False, strident=True, voice=False),
        noise_level=0.95, typical_duration_ms=115.0
    ))
    add(Phoneme(
        symbol="z",
        name="Fricativa alveolar sonora (alofono preconsonantico o medieval)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=True, strident=True, voice=True),
        f1=250.0, f2=1600.0, f3=2600.0, noise_level=0.7, typical_duration_ms=90.0
    ))
    add(Phoneme(
        symbol="ʃ",
        name="Fricativa postalveolar sorda (sheismo rioplatense / medieval)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.POSTALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=False, distributed=True, strident=True, voice=False),
        noise_level=0.9, typical_duration_ms=110.0
    ))
    add(Phoneme(
        symbol="ʒ",
        name="Fricativa postalveolar sonora (zheismo rioplatense / medieval)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.POSTALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=False, distributed=True, strident=True, voice=True),
        f1=250.0, f2=1800.0, f3=2700.0, noise_level=0.75, typical_duration_ms=95.0
    ))
    add(Phoneme(
        symbol="x",
        name="Fricativa velar sorda",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, dorsal=True, high=True, back=True, voice=False),
        noise_level=0.8, typical_duration_ms=105.0
    ))
    add(Phoneme(
        symbol="χ",
        name="Fricativa uvular sorda (peninsular enfatica)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.UVULAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, dorsal=True, low=False, back=True, voice=False),
        noise_level=0.85, typical_duration_ms=110.0
    ))
    add(Phoneme(
        symbol="h",
        name="Fricativa glotal sorda (aspiracion caribena, canaria, andaluza, diacronica)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.GLOTTAL,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=False, sonorant=False, continuant=True, spread_glottis=True, voice=False),
        noise_level=0.4, typical_duration_ms=70.0
    ))
    add(Phoneme(
        symbol="ç",
        name="Fricativa palatal sorda (alofono chileno ante vocal anterior)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.PALATAL,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=False, dorsal=True, high=True, voice=False),
        noise_level=0.75, typical_duration_ms=100.0
    ))

    # -------------------------------------------------------------------------
    # AFRICADAS Y GRUPOS ESPECIALES
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="t͡ʃ",
        name="Africada postalveolar sorda ('ch')",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.POSTALVEOLAR,
        manner=MannerOfArticulation.AFFRICATE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, delayed_release=True, coronal=True, anterior=False, distributed=True, strident=True, voice=False),
        noise_level=0.85, typical_duration_ms=120.0
    ))
    add(Phoneme(
        symbol="t͡ɬ",
        name="Africada alveolar lateral sorda (mexicano / sustrato nahuatl)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.LATERAL_AFFRICATE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, delayed_release=True, lateral=True, coronal=True, anterior=True, voice=False),
        noise_level=0.8, typical_duration_ms=115.0
    ))
    add(Phoneme(
        symbol="t͡ʂ",
        name="Africada retrofleja sorda (alofono /tr/ andino, chileno, costarricense)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.RETROFLEX,
        manner=MannerOfArticulation.AFFRICATE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, delayed_release=True, coronal=True, anterior=False, strident=True, voice=False),
        noise_level=0.85, typical_duration_ms=120.0
    ))
    add(Phoneme(
        symbol="ts",
        name="Africada alveolar sorda (sibilante medieval 'ç')",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.AFFRICATE,
        phonation=Phonation.VOICELESS,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, delayed_release=True, coronal=True, anterior=True, strident=True, voice=False),
        noise_level=0.85, typical_duration_ms=115.0
    ))
    add(Phoneme(
        symbol="dz",
        name="Africada alveolar sonora (sibilante medieval 'z')",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.AFFRICATE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, delayed_release=True, coronal=True, anterior=True, strident=True, voice=True),
        f1=250.0, f2=1600.0, f3=2600.0, noise_level=0.7, typical_duration_ms=105.0
    ))

    # -------------------------------------------------------------------------
    # NASALES
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="m",
        name="Nasal bilabial sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.BILABIAL,
        manner=MannerOfArticulation.NASAL,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, nasal=True, labial=True, voice=True),
        f1=250.0, f2=1000.0, f3=2200.0, typical_duration_ms=90.0
    ))
    add(Phoneme(
        symbol="n",
        name="Nasal alveolar sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.NASAL,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, nasal=True, coronal=True, anterior=True, voice=True),
        f1=250.0, f2=1500.0, f3=2500.0, typical_duration_ms=85.0
    ))
    add(Phoneme(
        symbol="ɲ",
        name="Nasal palatal sonora ('ñ')",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.PALATAL,
        manner=MannerOfArticulation.NASAL,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, nasal=True, coronal=False, dorsal=True, high=True, voice=True),
        f1=250.0, f2=2100.0, f3=2800.0, typical_duration_ms=100.0
    ))
    add(Phoneme(
        symbol="ŋ",
        name="Nasal velar sonora (velarizacion final caribena y centroamericana)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.VELAR,
        manner=MannerOfArticulation.NASAL,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, nasal=True, dorsal=True, high=True, back=True, voice=True),
        f1=250.0, f2=1800.0, f3=2400.0, typical_duration_ms=85.0
    ))

    # -------------------------------------------------------------------------
    # LIQUIDAS: LATERALES Y VIBRANTES
    # -------------------------------------------------------------------------
    add(Phoneme(
        symbol="l",
        name="Lateral alveolar sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.LATERAL_APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, continuant=True, lateral=True, coronal=True, anterior=True, voice=True),
        f1=350.0, f2=1300.0, f3=2700.0, typical_duration_ms=80.0
    ))
    add(Phoneme(
        symbol="ʎ",
        name="Lateral palatal sonora (lleismo andino, peninsular tradicional, diacronico)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.PALATAL,
        manner=MannerOfArticulation.LATERAL_APPROXIMANT,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, continuant=True, lateral=True, dorsal=True, high=True, voice=True),
        f1=300.0, f2=2000.0, f3=2900.0, typical_duration_ms=95.0
    ))
    add(Phoneme(
        symbol="ʝ",
        name="Fricativa/aproximante palatal sonora (yeismo estandar)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.PALATAL,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, dorsal=True, high=True, voice=True),
        f1=280.0, f2=2100.0, f3=2850.0, noise_level=0.4, typical_duration_ms=85.0
    ))
    add(Phoneme(
        symbol="ɾ",
        name="Vibrante simple alveolar sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.TAP_FLAP,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, coronal=True, anterior=True, voice=True),
        f1=350.0, f2=1500.0, f3=2500.0, typical_duration_ms=25.0
    ))
    add(Phoneme(
        symbol="r",
        name="Vibrante multiple alveolar sonora",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.TRILL,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=True, coronal=True, anterior=True, tense=True, voice=True),
        f1=350.0, f2=1500.0, f3=2500.0, typical_duration_ms=90.0
    ))
    add(Phoneme(
        symbol="ř",
        name="Vibrante asibilada alveolar sonora (andino / costarricense)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.ALVEOLAR,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=True, strident=True, voice=True),
        f1=300.0, f2=1600.0, f3=2600.0, noise_level=0.6, typical_duration_ms=85.0
    ))
    add(Phoneme(
        symbol="ʐ",
        name="Fricativa retrofleja sonora (asibilacion /r/ costarricense)",
        phoneme_type=PhonemeType.CONSONANT,
        place=PlaceOfArticulation.RETROFLEX,
        manner=MannerOfArticulation.FRICATIVE,
        phonation=Phonation.VOICED,
        features=PhonologicalFeatures(consonantal=True, sonorant=False, continuant=True, coronal=True, anterior=False, strident=True, voice=True),
        f1=300.0, f2=1700.0, f3=2650.0, noise_level=0.65, typical_duration_ms=85.0
    ))

    # Suprasegmentales y separadores
    add(Phoneme(
        symbol="ˈ",
        name="Acento prosodico primario",
        phoneme_type=PhonemeType.SUPRASEGMENTAL,
        features=PhonologicalFeatures(syllabic=False, consonantal=False),
        typical_duration_ms=0.0
    ))
    add(Phoneme(
        symbol=".",
        name="Frontera silabica",
        phoneme_type=PhonemeType.SUPRASEGMENTAL,
        features=PhonologicalFeatures(syllabic=False, consonantal=False),
        typical_duration_ms=0.0
    ))

    return inv


# Inventario global inmutable precalculado
PHONEME_INVENTORY: Final[Dict[str, Phoneme]] = _create_phoneme_inventory()


def get_phoneme(symbol: str) -> Phoneme:
    """
    Recupera un fonema del inventario por su simbolo AFI.
    Si el simbolo no se encuentra, genera un fonema generico conservando el simbolo.
    """
    if symbol in PHONEME_INVENTORY:
        return PHONEME_INVENTORY[symbol]

    # Fonema de contingencia para simbolos exoticos
    return Phoneme(
        symbol=symbol,
        name=f"Fonema AFI no categorizado ({symbol})",
        phoneme_type=PhonemeType.CONSONANT,
        features=PhonologicalFeatures()
    )


def compute_phonetic_distance(p1: Phoneme, p2: Phoneme) -> float:
    """
    Calcula la distancia fonetica normalizada [0.0, 1.0] entre dos fonemas
    utilizando la Geometria de Rasgos de Clements & Hume (1995).

    Distancia = 0.0: Identidad fonologica absoluta.
    Distancia cercana a 0.0: Alófonos o fonemas estrechamente emparentados (ej. [s] y [θ], [l] y [ɾ]).
    Distancia cercana a 1.0: Fonemas opuestos en modo, punto y sonoridad (ej. [p] y [a]).
    """
    if p1.symbol == p2.symbol:
        return 0.0

    # Separadores o acentos tienen distancia binaria
    if p1.phoneme_type == PhonemeType.SUPRASEGMENTAL or p2.phoneme_type == PhonemeType.SUPRASEGMENTAL:
        return 0.0 if p1.symbol == p2.symbol else 1.0

    vec1 = p1.features.to_vector()
    vec2 = p2.features.to_vector()

    weighted_diff = 0.0
    total_weight = sum(FEATURE_WEIGHTS)

    for v1, v2, w in zip(vec1, vec2, FEATURE_WEIGHTS):
        weighted_diff += w * abs(v1 - v2)

    base_dist = weighted_diff / total_weight

    # Modulador adicional por distancia formántica en vocales
    if p1.is_vowel() and p2.is_vowel():
        f1_diff = abs(p1.f1 - p2.f1) / 1000.0
        f2_diff = abs(p2.f2 - p2.f2) / 2500.0
        formant_penalty = 0.3 * (f1_diff + f2_diff)
        return min(1.0, 0.7 * base_dist + formant_penalty)

    return min(1.0, base_dist)
