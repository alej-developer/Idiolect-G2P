"""
Pruebas de integración para la Fase 2: transductor continuo con sandhi e inferencia MaxEnt.
Integration tests for Phase 2: connected transducer with sandhi and MaxEnt inference.
"""

import pytest
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.inference.bayesian_profiler import BayesianIdiolectProfiler
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY


def test_transducer_transcribe_connected_text_with_sandhi():
    """Verifica que transcribe_connected_text aplique sandhi e identifique junturas."""
    transducer = G2PTransducer()
    peninsular = GLOBAL_DIALECT_REGISTRY.get("ES_PENINSULAR")
    
    # "los mismos" -> en habla continua con sandhi la coda de 'los' se resuena a [z] ante [m]
    words, connected_ipa, junctures = transducer.transcribe_connected_text(
        text="los mismos",
        dialect=peninsular,
        apply_sandhi=True
    )
    
    assert len(words) == 2
    assert len(junctures) >= 1
    assert junctures[0].output_phoneme == "z"
    assert "z" in connected_ipa


def test_transducer_transcribe_connected_text_without_sandhi():
    """Verifica que si apply_sandhi=False no se modifiquen las fronteras."""
    transducer = G2PTransducer()
    peninsular = GLOBAL_DIALECT_REGISTRY.get("ES_PENINSULAR")
    
    words, connected_ipa, junctures = transducer.transcribe_connected_text(
        text="los mismos",
        dialect=peninsular,
        apply_sandhi=False
    )
    
    assert len(words) == 2
    assert len(junctures) == 0
    assert "loz" not in connected_ipa
