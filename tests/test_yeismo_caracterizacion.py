"""Tratamiento de 'y' y 'll' en el silabeador y el transductor (ver #28).

'y' ante vocal es consonante de ataque ([ʝ] en dialectos yeístas); 'y' final tras vocal
(rey, hoy, muy) y la conjunción 'y' siguen siendo vocálicas.
"""

from __future__ import annotations

import pytest

from idiolect_g2p.core.syllabifier import syllabify_word
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY

T = G2PTransducer()


def _ipa(palabra: str, codigo: str = "ES_PENINSULAR") -> str:
    dialecto = GLOBAL_DIALECT_REGISTRY.get(codigo)
    assert dialecto is not None
    resultado = T.transcribe_word(palabra, dialecto)
    return str(resultado.syllabified_ipa)


@pytest.mark.parametrize(
    ("palabra", "esperado"),
    [("valla", "ˈba.ʝa"), ("calle", "ˈka.ʝe"), ("rey", None), ("muy", None), ("hoy", None)],
)
def test_ll_y_diptongos_con_y_final(palabra: str, esperado: str | None) -> None:
    ipa = _ipa(palabra)
    if esperado is not None:
        assert ipa == esperado
    else:
        assert "j" in ipa  # 'y' final tras vocal es semivocal: no debe cambiar


@pytest.mark.parametrize(
    ("palabra", "esperado"),
    [
        ("playa", "ˈpla.ʝa"),
        ("mayo", "ˈma.ʝo"),
        ("haya", "ˈa.ʝa"),
        ("yo", "ˈʝo"),
        ("ayer", "aˈʝeɾ"),
        ("leyó", "leˈʝo"),
        ("inyectar", "in.ʝekˈtaɾ"),
    ],
)
def test_y_ante_vocal_es_ataque_yeista(palabra: str, esperado: str) -> None:
    assert _ipa(palabra) == esperado


@pytest.mark.parametrize(("palabra", "esperado"), [("playa", "pla-ya"), ("huyó", "hu-yó"), ("rey", "rey")])
def test_silabeo_de_y(palabra: str, esperado: str) -> None:
    assert syllabify_word(palabra).hyphenated == esperado


def test_conjuncion_y_sigue_siendo_vocal() -> None:
    assert _ipa("y") == "ˈi"
