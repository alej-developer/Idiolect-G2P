"""Regresiones: las evidencias forenses deben estar sustentadas por la rima."""

from __future__ import annotations

import pytest

from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.inference.forensic_explainer import (
    ForensicReport,
    generate_forensic_explanation,
)
from idiolect_g2p.reports.report_generator import generate_json_report


def _informe(poema: str) -> ForensicReport:
    return generate_forensic_explanation(profile_idiolect_from_poem(poema))


def test_mariposa_luminosa_no_emite_evidencia_de_liquidas() -> None:
    """Los segmentos rimantes [o, s, a] no contienen liquidas: no hay evidencia."""
    informe = _informe("Una mariposa\nUna luminosa")
    assert informe.discriminant_evidences == []
    assert "liquida" not in informe.sociolinguistic_conclusion.lower()
    assert "determinante" not in informe.sociolinguistic_conclusion.lower()


def test_cena_seda_no_afirma_consonancia_perfecta_con_seseo() -> None:
    """cena/seda es rima forzada (is_perfect_consonant False): no se afirma lo contrario."""
    resultado = profile_idiolect_from_poem("La cena\nLa seda")
    assert not any(m.is_perfect_consonant for m in resultado.evaluated_rhyme_matches)
    informe = generate_forensic_explanation(resultado)
    assert informe.discriminant_evidences == []
    assert "solo alcanza consonancia" not in informe.sociolinguistic_conclusion


def test_control_positivo_seseo() -> None:
    """Cuando la sibilante esta en la rima y cambia el resultado entre hipotesis, hay evidencia."""
    informe = _informe("En este dulce abrazo\nyo sigo cada paso")
    fenomenos = [ev.phonetic_phenomenon for ev in informe.discriminant_evidences]
    assert any("Seseo" in f for f in fenomenos)
    ev = next(e for e in informe.discriminant_evidences if "Seseo" in e.phonetic_phenomenon)
    assert ev.word_1 == "abrazo" and ev.word_2 == "paso"
    assert "Rima Consonante Perfecta" in ev.impact_description


def test_control_positivo_liquidas() -> None:
    """puerto/muelto: la liquida esta en el segmento rimante y distingue las hipotesis."""
    informe = _informe("Llegó la barca al puerto\ncon el marinero muelto")
    fenomenos = [ev.phonetic_phenomenon for ev in informe.discriminant_evidences]
    assert any("liquidas" in f for f in fenomenos)
    assert not any("Seseo" in f for f in fenomenos)


def test_evidencia_respeta_el_tipo_de_rima_calculado() -> None:
    resultado = profile_idiolect_from_poem("En este dulce abrazo\nyo sigo cada paso")
    informe = generate_forensic_explanation(resultado)
    por_par = {
        (m.word_1_text, m.word_2_text): m.rhyme_type.value for m in resultado.evaluated_rhyme_matches
    }
    for ev in informe.discriminant_evidences:
        assert por_par[(ev.word_1, ev.word_2)] in ev.impact_description


@pytest.mark.parametrize(
    "poema",
    [
        "En este dulce abrazo\nyo sigo cada paso",
        "Llegó la barca al puerto\ncon el marinero muelto",
    ],
)
def test_no_hay_puntuaciones_fijas_de_poder_discriminante(poema: str) -> None:
    informe = _informe(poema)
    assert informe.discriminant_evidences
    for ev in informe.discriminant_evidences:
        assert ev.discriminating_power is None


def test_informe_json_serializa_poder_nulo() -> None:
    import json

    resultado = profile_idiolect_from_poem("En este dulce abrazo\nyo sigo cada paso")
    datos = json.loads(generate_json_report(resultado))
    assert datos["discriminant_evidences"]
    assert all(e["power"] is None for e in datos["discriminant_evidences"])


@pytest.mark.parametrize("poema", ["La valla\nla playa", "El pollo\nel poyo"])
def test_yeismo_no_emite_evidencia_sin_contraste_real(poema: str) -> None:
    """Limitacion conocida: el transductor renderiza la 'y' intervocalica como [j].

    Las hipotesis yeista (ʝ vs j) y lleista (ʎ vs j) dan distancias casi iguales
    (diferencia ~0.002, por debajo del umbral), asi que no se debe afirmar yeismo.
    No hay control positivo de yeismo construible hasta que el transductor
    distinga [ʝ] de [j].
    """
    informe = _informe(poema)
    fenomenos = [ev.phonetic_phenomenon for ev in informe.discriminant_evidences]
    assert not any("eísmo" in f or "eismo" in f.lower() for f in fenomenos)
