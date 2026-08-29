"""
Pruebas unitarias para la inferencia bayesiana y perfilacion forense de idiolectos.
Unit tests for Bayesian inference and forensic idiolect profiling.
"""

import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    profile_idiolect_from_poem,
)
from idiolect_g2p.inference.forensic_explainer import (
    generate_forensic_explanation,
)


def test_bayesian_inference_seseo_poem() -> None:
    """
    Verifica que un poema con rimas cruzadas entre 'z' y 's' (abrazo/paso/lazo/caso)
    sea clasificado con menor distancia fonetica y mayor verosimilitud en dialectos seseantes
    que en la norma con distincion peninsular.
    """
    poem_seseo = """
    En este dulce abrazo
    yo sigo cada paso
    unido por el lazo
    en este nuevo caso
    """
    profiler = BayesianIdiolectProfiler()
    result = profiler.profile_poem(poem_seseo)

    # Verificar que el dialecto ganador sea seseante
    assert result.estimated_isogloss_vector["seseo"] > 0.80

    # Comprobar probabilidades
    prob_dict = {dp.dialect_code: dp.posterior_probability for dp in result.dialect_probabilities}
    assert "MX_CENTRAL" in prob_dict
    assert "ES_PENINSULAR" in prob_dict

    # Dialectos seseantes deben tener probabilidad mayor que Peninsular Distincion
    assert prob_dict["MX_CENTRAL"] > prob_dict["ES_PENINSULAR"]


def test_bayesian_inference_lambdacist_poem() -> None:
    """
    Verifica que un poema con rima puerto/muelto y sol/amor (lambdacismo caribeno)
    identifique el dialecto Caribeño Lambdacista con maxima verosimilitud.
    """
    poem_lambdacist = """
    Llegó la barca al puerto
    con el marinero muelto
    bajo la luz del sol
    buscando su gran amor
    """
    profiler = BayesianIdiolectProfiler()
    result = profiler.profile_poem(poem_lambdacist)

    # El dialecto ganador debe ser Caribeño Lambdacista
    assert result.predicted_dialect_code == "CARIBBEAN_LAMBDACIST"
    assert result.confidence_score > 0.10
    assert result.estimated_isogloss_vector["lambdacism"] > 0.10


def test_forensic_report_generation() -> None:
    """Verifica la generacion del dictamen pericial forense."""
    poem = """
    No me diste ningún abrazo
    cuando apresuré mi paso
    """
    result = profile_idiolect_from_poem(poem)
    report = generate_forensic_explanation(result, case_id="CASE-FORENSIC-TEST")

    assert report.case_identifier == "CASE-FORENSIC-TEST"
    assert report.confidence_percentage > 0.0
    assert len(report.discriminant_evidences) >= 1
    assert "Seseo" in report.discriminant_evidences[0].phonetic_phenomenon
    assert len(report.dialect_ranking) > 0
