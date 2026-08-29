"""
Parametros formánticos y acusticos de fonemas y alofonos en el estandar AFI.
Formant and acoustic parameters of phonemes and allophones in the IPA standard.

Basado en:
- Martinez Celdran, E., & Fernandez Planas, A. M. (2007). Manual de fonetica espanola.
- Quilis, A. (1993). Tratado de fonologia y fonetica espanolas.
- Klatt, D. H. (1980). Software for a cascade/parallel formant synthesizer. JASA.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Final, Optional


@dataclass(frozen=True)
class AcousticParameters:
    """Parametros de resonancia acustica para un simbolo fonetico AFI."""
    symbol: str
    f0_hz: float = 120.0             # Frecuencia fundamental glotal media (Hz)
    f1_hz: float = 500.0             # Primer formante (apertura mandibular)
    f2_hz: float = 1500.0            # Segundo formante (posicion lingual anteroposterior)
    f3_hz: float = 2500.0            # Tercer formante (cavidad faringea / redondeamiento)
    f4_hz: float = 3500.0            # Cuarto formante
    bw1_hz: float = 80.0             # Ancho de banda F1
    bw2_hz: float = 100.0            # Ancho de banda F2
    bw3_hz: float = 120.0            # Ancho de banda F3
    voicing_amplitude: float = 1.0   # Amplitud de la fuente sonora periodica glotal [0.0, 1.0]
    noise_amplitude: float = 0.0     # Amplitud de la fuente de ruido de friccion [0.0, 1.0]
    noise_center_freq: float = 0.0   # Frecuencia central del filtro de ruido (Hz)
    noise_bandwidth: float = 1000.0  # Ancho de banda del ruido
    duration_ms: float = 100.0       # Duracion temporal intrinseca media (ms)
    attack_ms: float = 15.0          # Tiempo de ataque envolvente (ms)
    decay_ms: float = 20.0           # Tiempo de decaimiento envolvente (ms)


def _build_acoustic_table() -> Dict[str, AcousticParameters]:
    """Construye la tabla acustica formántica de referencia para sintesis fonetica."""
    table: Dict[str, AcousticParameters] = {}

    def add(p: AcousticParameters) -> None:
        table[p.symbol] = p

    # -------------------------------------------------------------------------
    # VOCALES CANONICAS (Frecuencias F1, F2, F3 tipicas del espanol)
    # -------------------------------------------------------------------------
    add(AcousticParameters(symbol="a", f1_hz=800.0, f2_hz=1400.0, f3_hz=2600.0, voicing_amplitude=1.0, duration_ms=130.0))
    add(AcousticParameters(symbol="e", f1_hz=500.0, f2_hz=1900.0, f3_hz=2600.0, voicing_amplitude=1.0, duration_ms=110.0))
    add(AcousticParameters(symbol="i", f1_hz=300.0, f2_hz=2300.0, f3_hz=3000.0, voicing_amplitude=1.0, duration_ms=95.0))
    add(AcousticParameters(symbol="o", f1_hz=500.0, f2_hz=1000.0, f3_hz=2500.0, voicing_amplitude=1.0, duration_ms=110.0))
    add(AcousticParameters(symbol="u", f1_hz=300.0, f2_hz=800.0, f3_hz=2400.0, voicing_amplitude=1.0, duration_ms=95.0))

    # Vocales abiertas / alofonicas (Andalucia oriental)
    add(AcousticParameters(symbol="ɛ", f1_hz=580.0, f2_hz=1780.0, f3_hz=2550.0, voicing_amplitude=1.0, duration_ms=140.0))
    add(AcousticParameters(symbol="ɔ", f1_hz=580.0, f2_hz=920.0, f3_hz=2450.0, voicing_amplitude=1.0, duration_ms=140.0))
    add(AcousticParameters(symbol="æ", f1_hz=750.0, f2_hz=1600.0, f3_hz=2600.0, voicing_amplitude=1.0, duration_ms=145.0))

    # Vocales ensordecidas / caedizas (Mexico)
    add(AcousticParameters(symbol="e̥", f1_hz=500.0, f2_hz=1900.0, f3_hz=2600.0, voicing_amplitude=0.2, noise_amplitude=0.3, noise_center_freq=2500.0, duration_ms=60.0))
    add(AcousticParameters(symbol="o̥", f1_hz=500.0, f2_hz=1000.0, f3_hz=2500.0, voicing_amplitude=0.2, noise_amplitude=0.3, noise_center_freq=2000.0, duration_ms=60.0))

    # Semivocales / Glides
    add(AcousticParameters(symbol="j", f1_hz=300.0, f2_hz=2250.0, f3_hz=2900.0, voicing_amplitude=0.9, duration_ms=60.0))
    add(AcousticParameters(symbol="w", f1_hz=300.0, f2_hz=750.0, f3_hz=2300.0, voicing_amplitude=0.9, duration_ms=60.0))

    # -------------------------------------------------------------------------
    # FRICATIVAS (Ruido filtrado en banda y formantes de transicion)
    # -------------------------------------------------------------------------
    # Seseante alveolar [s]
    add(AcousticParameters(symbol="s", f1_hz=350.0, f2_hz=1600.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.9, noise_center_freq=5500.0, noise_bandwidth=2000.0, duration_ms=110.0))
    # Apicoalveolar peninsular [s̺] (centro de ruido mas agudo)
    add(AcousticParameters(symbol="s̺", f1_hz=350.0, f2_hz=1600.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.95, noise_center_freq=6200.0, noise_bandwidth=1800.0, duration_ms=115.0))
    # Interdental peninsular [θ] (ruido plano difuso y de menor energia)
    add(AcousticParameters(symbol="θ", f1_hz=350.0, f2_hz=1500.0, f3_hz=2600.0, voicing_amplitude=0.0, noise_amplitude=0.5, noise_center_freq=4500.0, noise_bandwidth=3000.0, duration_ms=105.0))
    # Fricativa postalveolar sorda [ʃ] (sheismo rioplatense / medieval: energia en 2.5-4 kHz)
    add(AcousticParameters(symbol="ʃ", f1_hz=350.0, f2_hz=1800.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.9, noise_center_freq=3500.0, noise_bandwidth=1500.0, duration_ms=115.0))
    # Fricativa postalveolar sonora [ʒ] (zheismo rioplatense)
    add(AcousticParameters(symbol="ʒ", f1_hz=300.0, f2_hz=1800.0, f3_hz=2700.0, voicing_amplitude=0.6, noise_amplitude=0.7, noise_center_freq=3500.0, noise_bandwidth=1500.0, duration_ms=100.0))
    # Fricativa alveolar sonora [z]
    add(AcousticParameters(symbol="z", f1_hz=300.0, f2_hz=1600.0, f3_hz=2600.0, voicing_amplitude=0.6, noise_amplitude=0.7, noise_center_freq=5500.0, noise_bandwidth=2000.0, duration_ms=90.0))
    # Fricativa labiodental [f]
    add(AcousticParameters(symbol="f", f1_hz=300.0, f2_hz=1200.0, f3_hz=2400.0, voicing_amplitude=0.0, noise_amplitude=0.6, noise_center_freq=4000.0, noise_bandwidth=2500.0, duration_ms=100.0))
    # Fricativa velar sorda [x]
    add(AcousticParameters(symbol="x", f1_hz=400.0, f2_hz=1500.0, f3_hz=2400.0, voicing_amplitude=0.0, noise_amplitude=0.8, noise_center_freq=2200.0, noise_bandwidth=1200.0, duration_ms=105.0))
    # Fricativa uvular sorda [χ] (peninsular enfatica)
    add(AcousticParameters(symbol="χ", f1_hz=450.0, f2_hz=1300.0, f3_hz=2300.0, voicing_amplitude=0.0, noise_amplitude=0.85, noise_center_freq=1800.0, noise_bandwidth=1000.0, duration_ms=110.0))
    # Fricativa glotal [h] (aspiracion caribena, canaria, andaluza, diacronica)
    add(AcousticParameters(symbol="h", f1_hz=600.0, f2_hz=1400.0, f3_hz=2500.0, voicing_amplitude=0.0, noise_amplitude=0.5, noise_center_freq=1500.0, noise_bandwidth=2000.0, duration_ms=75.0))
    # Fricativa palatal [ç] (chileno)
    add(AcousticParameters(symbol="ç", f1_hz=350.0, f2_hz=2100.0, f3_hz=2900.0, voicing_amplitude=0.0, noise_amplitude=0.75, noise_center_freq=3200.0, noise_bandwidth=1400.0, duration_ms=100.0))

    # -------------------------------------------------------------------------
    # AFRICADAS
    # -------------------------------------------------------------------------
    add(AcousticParameters(symbol="t͡ʃ", f1_hz=300.0, f2_hz=1800.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.85, noise_center_freq=3500.0, noise_bandwidth=1500.0, duration_ms=120.0, attack_ms=30.0))
    add(AcousticParameters(symbol="t͡ʂ", f1_hz=300.0, f2_hz=1600.0, f3_hz=2500.0, voicing_amplitude=0.0, noise_amplitude=0.8, noise_center_freq=2800.0, noise_bandwidth=1400.0, duration_ms=120.0, attack_ms=30.0))
    add(AcousticParameters(symbol="t͡ɬ", f1_hz=350.0, f2_hz=1400.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.75, noise_center_freq=4500.0, noise_bandwidth=2000.0, duration_ms=115.0, attack_ms=25.0))
    add(AcousticParameters(symbol="ts", f1_hz=350.0, f2_hz=1600.0, f3_hz=2700.0, voicing_amplitude=0.0, noise_amplitude=0.85, noise_center_freq=5500.0, noise_bandwidth=2000.0, duration_ms=115.0, attack_ms=25.0))
    add(AcousticParameters(symbol="dz", f1_hz=300.0, f2_hz=1600.0, f3_hz=2600.0, voicing_amplitude=0.5, noise_amplitude=0.7, noise_center_freq=5000.0, noise_bandwidth=2000.0, duration_ms=105.0, attack_ms=25.0))

    # -------------------------------------------------------------------------
    # OCLUSIVAS Y APROXIMANTES
    # -------------------------------------------------------------------------
    add(AcousticParameters(symbol="p", f1_hz=200.0, f2_hz=1000.0, f3_hz=2200.0, voicing_amplitude=0.0, noise_amplitude=0.7, noise_center_freq=1200.0, duration_ms=75.0, attack_ms=10.0))
    add(AcousticParameters(symbol="b", f1_hz=200.0, f2_hz=1000.0, f3_hz=2200.0, voicing_amplitude=0.6, noise_amplitude=0.3, noise_center_freq=1200.0, duration_ms=65.0))
    add(AcousticParameters(symbol="β", f1_hz=300.0, f2_hz=1000.0, f3_hz=2300.0, voicing_amplitude=0.8, noise_amplitude=0.1, duration_ms=55.0))

    add(AcousticParameters(symbol="t", f1_hz=250.0, f2_hz=1700.0, f3_hz=2600.0, voicing_amplitude=0.0, noise_amplitude=0.8, noise_center_freq=4000.0, duration_ms=75.0, attack_ms=10.0))
    add(AcousticParameters(symbol="d", f1_hz=250.0, f2_hz=1600.0, f3_hz=2600.0, voicing_amplitude=0.6, noise_amplitude=0.3, noise_center_freq=3500.0, duration_ms=65.0))
    add(AcousticParameters(symbol="ð", f1_hz=350.0, f2_hz=1500.0, f3_hz=2500.0, voicing_amplitude=0.8, noise_amplitude=0.15, duration_ms=55.0))

    add(AcousticParameters(symbol="k", f1_hz=300.0, f2_hz=1800.0, f3_hz=2400.0, voicing_amplitude=0.0, noise_amplitude=0.85, noise_center_freq=2200.0, duration_ms=85.0, attack_ms=10.0))
    add(AcousticParameters(symbol="g", f1_hz=250.0, f2_hz=1800.0, f3_hz=2400.0, voicing_amplitude=0.6, noise_amplitude=0.3, noise_center_freq=2000.0, duration_ms=70.0))
    add(AcousticParameters(symbol="ɣ", f1_hz=350.0, f2_hz=1700.0, f3_hz=2400.0, voicing_amplitude=0.8, noise_amplitude=0.15, duration_ms=55.0))
    add(AcousticParameters(symbol="c", f1_hz=300.0, f2_hz=2200.0, f3_hz=2900.0, voicing_amplitude=0.0, noise_amplitude=0.8, noise_center_freq=3000.0, duration_ms=80.0))
    add(AcousticParameters(symbol="ɟ", f1_hz=280.0, f2_hz=2200.0, f3_hz=2900.0, voicing_amplitude=0.6, noise_amplitude=0.3, noise_center_freq=2800.0, duration_ms=70.0))

    # -------------------------------------------------------------------------
    # NASALES
    # -------------------------------------------------------------------------
    add(AcousticParameters(symbol="m", f1_hz=250.0, f2_hz=1000.0, f3_hz=2200.0, bw1_hz=150.0, voicing_amplitude=0.8, duration_ms=85.0))
    add(AcousticParameters(symbol="n", f1_hz=250.0, f2_hz=1500.0, f3_hz=2500.0, bw1_hz=150.0, voicing_amplitude=0.8, duration_ms=80.0))
    add(AcousticParameters(symbol="ɲ", f1_hz=250.0, f2_hz=2100.0, f3_hz=2800.0, bw1_hz=160.0, voicing_amplitude=0.8, duration_ms=95.0))
    add(AcousticParameters(symbol="ŋ", f1_hz=250.0, f2_hz=1800.0, f3_hz=2400.0, bw1_hz=160.0, voicing_amplitude=0.8, duration_ms=80.0))

    # -------------------------------------------------------------------------
    # LIQUIDAS Y APROXIMANTES
    # -------------------------------------------------------------------------
    add(AcousticParameters(symbol="l", f1_hz=350.0, f2_hz=1300.0, f3_hz=2700.0, voicing_amplitude=0.9, duration_ms=75.0))
    add(AcousticParameters(symbol="ʎ", f1_hz=300.0, f2_hz=2000.0, f3_hz=2900.0, voicing_amplitude=0.9, duration_ms=90.0))
    add(AcousticParameters(symbol="ʝ", f1_hz=280.0, f2_hz=2100.0, f3_hz=2850.0, voicing_amplitude=0.7, noise_amplitude=0.3, noise_center_freq=3000.0, duration_ms=80.0))
    add(AcousticParameters(symbol="ɾ", f1_hz=350.0, f2_hz=1500.0, f3_hz=2500.0, voicing_amplitude=0.85, duration_ms=30.0))
    add(AcousticParameters(symbol="r", f1_hz=350.0, f2_hz=1500.0, f3_hz=2500.0, voicing_amplitude=0.85, duration_ms=90.0))
    add(AcousticParameters(symbol="ř", f1_hz=300.0, f2_hz=1600.0, f3_hz=2600.0, voicing_amplitude=0.6, noise_amplitude=0.6, noise_center_freq=4500.0, duration_ms=85.0))
    add(AcousticParameters(symbol="ʐ", f1_hz=300.0, f2_hz=1700.0, f3_hz=2650.0, voicing_amplitude=0.6, noise_amplitude=0.6, noise_center_freq=3800.0, duration_ms=85.0))

    return table


IPA_ACOUSTIC_TABLE: Final[Dict[str, AcousticParameters]] = _build_acoustic_table()


def get_acoustic_parameters(symbol: str) -> AcousticParameters:
    """Recupera los parametros acusticos formánticos de un simbolo AFI."""
    if symbol in IPA_ACOUSTIC_TABLE:
        return IPA_ACOUSTIC_TABLE[symbol]
    # Contingencia para fonemas neutros o no catalogados
    return AcousticParameters(symbol=symbol)
