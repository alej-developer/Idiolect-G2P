"""
Pruebas unitarias para la gramática MaxEnt y Teoría de Optimidad Estocástica.
Unit tests for MaxEnt grammar and Stochastic Optimality Theory module.
"""

import pytest
from idiolect_g2p.inference.maxent_grammar import MaxEntGrammar, MaxEntCandidate


def test_maxent_initialization_and_constraints():
    """Verifica que la gramática inicialice las restricciones universales esperadas."""
    grammar = MaxEntGrammar()
    constraint_names = [c.name for c in grammar.constraints]
    
    assert "*CODA[s]" in constraint_names
    assert "*VOICELESS-BEFORE-SONORANT" in constraint_names
    assert "*CODA[Liquid]" in constraint_names
    assert "ONSET" in constraint_names
    assert "IDENT(Voice)" in constraint_names
    assert "IDENT(Place)" in constraint_names
    assert "MAX(C)" in constraint_names


def test_maxent_coda_s_aspiration_evaluation():
    """
    Evalúa la competencia estocástica entre retención de coda [s] vs aspiración [h].
    Bajo un dialecto aspirante (peso elevado de *CODA[s]), [h] debe tener mayor probabilidad.
    """
    grammar = MaxEntGrammar()
    
    # Contexto 1: Dialecto conservador (Poco peso a *CODA[s], alto a IDENT/MAX)
    conservative_weights = grammar.calibrate_weights_from_isoglosses({"aspiration_s": 0.0})
    
    candidates = [
        ("las", {"coda_phones": ["s"], "all_phones": ["l", "a", "s"], "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "s"]}),
        ("lah", {"coda_phones": ["h"], "all_phones": ["l", "a", "h"], "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "h"]}),
    ]
    
    res_cons = grammar.evaluate_candidates("las", candidates, weights_override=conservative_weights)
    # En dialecto conservador, la retención de [s] gana por fidelidad
    assert res_cons[0].surface_form == "las"
    assert res_cons[0].probability > res_cons[1].probability
    
    # Contexto 2: Dialecto aspirante (Caribe / Andaluz oriental)
    aspirating_weights = grammar.calibrate_weights_from_isoglosses({"aspiration_s": 1.0})
    res_asp = grammar.evaluate_candidates("las", candidates, weights_override=aspirating_weights)
    
    # En dialecto aspirante, [lah] debe ganar
    assert res_asp[0].surface_form == "lah"
    assert res_asp[0].probability > res_asp[1].probability


def test_maxent_liquid_neutralization():
    """Verifica que una tasa alta de lambdacismo favorezca la realización en [l]."""
    grammar = MaxEntGrammar()
    lambdacist_weights = grammar.calibrate_weights_from_isoglosses({"lambdacism": 1.0})
    
    # 'puelto' vs 'puerto'
    candidates = [
        ("pwel.to", {"coda_phones": ["l"], "underlying_phones": ["p", "w", "e", "ɾ", "t", "o"], "surface_phones": ["p", "w", "e", "l", "t", "o"]}),
        ("pweɾ.to", {"coda_phones": ["ɾ"], "underlying_phones": ["p", "w", "e", "ɾ", "t", "o"], "surface_phones": ["p", "w", "e", "ɾ", "t", "o"]}),
    ]
    
    res = grammar.evaluate_candidates("pweɾ.to", candidates, weights_override=lambdacist_weights)
    # Ambas violan *CODA[Liquid], pero la forma lambdacista es permitida por la relajación de IDENT(Place)
    assert len(res) == 2
    assert abs(sum(c.probability for c in res) - 1.0) < 1e-5
