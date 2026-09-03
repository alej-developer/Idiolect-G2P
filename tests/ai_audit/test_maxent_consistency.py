"""
Auditoría Dimensión 2: Consistencia de la Gramática MaxEnt y Distribución de Gibbs.
Valida que la gramática fonológica estocástica respete las propiedades formales
de la distribución de Gibbs, la monotonicidad armonía-probabilidad, la sensibilidad
a pesos, y la convergencia a distribución uniforme bajo pesos degenerados.

AI Audit Dimension 2: MaxEnt Grammar Consistency and Gibbs Distribution Properties.
"""

import math
import pytest
from idiolect_g2p.inference.maxent_grammar import MaxEntGrammar, MaxEntCandidate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gramatica() -> MaxEntGrammar:
    """Instancia compartida de la gramática MaxEnt."""
    return MaxEntGrammar()


def _crear_candidatos_coda_s():
    """Candidatos estándar para el contexto de aspiración de /s/ en coda."""
    return [
        ("las", {
            "coda_phones": ["s"], "all_phones": ["l", "a", "s"],
            "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "s"]
        }),
        ("lah", {
            "coda_phones": ["h"], "all_phones": ["l", "a", "h"],
            "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "h"]
        }),
    ]


# ---------------------------------------------------------------------------
# Tests de Distribución de Gibbs Bien Formada
# ---------------------------------------------------------------------------

class TestDistribucionGibbsBienFormada:
    """Verifica que P(y|x) sea una distribución de probabilidad válida."""

    def test_suma_probabilidades_igual_a_uno(self, gramatica: MaxEntGrammar) -> None:
        """Σ P(y_i | x) = 1.0 para todo conjunto de candidatos."""
        candidatos = _crear_candidatos_coda_s()
        resultados = gramatica.evaluate_candidates("las", candidatos)
        suma = sum(c.probability for c in resultados)
        assert abs(suma - 1.0) < 1e-6, f"Σ P(y|x) = {suma:.10f} ≠ 1.0"

    def test_probabilidades_en_rango_cero_uno(self, gramatica: MaxEntGrammar) -> None:
        """∀ y: P(y|x) ∈ [0.0, 1.0]."""
        candidatos = _crear_candidatos_coda_s()
        resultados = gramatica.evaluate_candidates("las", candidatos)
        for c in resultados:
            assert 0.0 <= c.probability <= 1.0, (
                f"P({c.surface_form}|x) = {c.probability} fuera de [0,1]"
            )

    def test_probabilidades_finitas_sin_nan(self, gramatica: MaxEntGrammar) -> None:
        """Todas las probabilidades y armonías deben ser valores finitos."""
        candidatos = _crear_candidatos_coda_s()
        resultados = gramatica.evaluate_candidates("las", candidatos)
        for c in resultados:
            assert math.isfinite(c.probability), f"P({c.surface_form}) no finita"
            assert math.isfinite(c.harmony), f"H({c.surface_form}) no finita"

    def test_normalizacion_con_multiples_candidatos(self, gramatica: MaxEntGrammar) -> None:
        """Σ P(y|x) = 1.0 con un conjunto expandido de 4 candidatos."""
        candidatos = [
            ("las", {"coda_phones": ["s"], "all_phones": ["l", "a", "s"],
                     "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "s"]}),
            ("lah", {"coda_phones": ["h"], "all_phones": ["l", "a", "h"],
                     "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "h"]}),
            ("la", {"coda_phones": [], "all_phones": ["l", "a"],
                    "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a"]}),
            ("laz", {"coda_phones": ["z"], "all_phones": ["l", "a", "z"],
                     "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "z"]}),
        ]
        resultados = gramatica.evaluate_candidates("las", candidatos)
        suma = sum(c.probability for c in resultados)
        assert abs(suma - 1.0) < 1e-6, f"Σ P(y|x) = {suma:.10f} con 4 candidatos"


# ---------------------------------------------------------------------------
# Tests de Monotonicidad Armonía ↔ Probabilidad
# ---------------------------------------------------------------------------

class TestMonotonicidadArmoniaProbabilidad:
    """Verifica que menor armonía H(y) implique mayor probabilidad P(y|x)."""

    def test_menor_armonia_mayor_probabilidad(self, gramatica: MaxEntGrammar) -> None:
        """
        Para cualesquiera dos candidatos y_a, y_b:
        H(y_a) < H(y_b) ⟹ P(y_a|x) > P(y_b|x)
        """
        candidatos = _crear_candidatos_coda_s()
        resultados = gramatica.evaluate_candidates("las", candidatos)

        # Los resultados vienen ordenados por probabilidad decreciente
        for i in range(len(resultados) - 1):
            for j in range(i + 1, len(resultados)):
                if resultados[i].harmony < resultados[j].harmony:
                    assert resultados[i].probability >= resultados[j].probability, (
                        f"Violación de monotonicidad: H({resultados[i].surface_form})="
                        f"{resultados[i].harmony:.4f} < H({resultados[j].surface_form})="
                        f"{resultados[j].harmony:.4f} pero "
                        f"P({resultados[i].surface_form})={resultados[i].probability:.6f} < "
                        f"P({resultados[j].surface_form})={resultados[j].probability:.6f}"
                    )

    def test_orden_por_probabilidad_coherente(self, gramatica: MaxEntGrammar) -> None:
        """La lista devuelta debe estar ordenada de mayor a menor probabilidad."""
        candidatos = _crear_candidatos_coda_s()
        resultados = gramatica.evaluate_candidates("las", candidatos)
        for i in range(len(resultados) - 1):
            assert resultados[i].probability >= resultados[i + 1].probability, (
                f"Resultados desordenados en posición {i}: "
                f"P[{i}]={resultados[i].probability:.6f} < P[{i+1}]={resultados[i+1].probability:.6f}"
            )


# ---------------------------------------------------------------------------
# Tests de Sensibilidad a Pesos
# ---------------------------------------------------------------------------

class TestSensibilidadAPesos:
    """Verifica que cambios en los pesos alteren las probabilidades coherentemente."""

    def test_peso_coda_s_favorece_aspiracion(self, gramatica: MaxEntGrammar) -> None:
        """
        Elevar el peso de *CODA[s] debe incrementar la probabilidad de 'lah'
        respecto a 'las'.
        """
        candidatos = _crear_candidatos_coda_s()

        # Pesos conservadores (bajo *CODA[s])
        pesos_bajos = dict(gramatica.weights)
        pesos_bajos["*CODA[s]"] = 0.1
        res_bajo = gramatica.evaluate_candidates("las", candidatos, weights_override=pesos_bajos)
        p_lah_bajo = next(c.probability for c in res_bajo if c.surface_form == "lah")

        # Pesos aspirantes (alto *CODA[s])
        pesos_altos = dict(gramatica.weights)
        pesos_altos["*CODA[s]"] = 10.0
        res_alto = gramatica.evaluate_candidates("las", candidatos, weights_override=pesos_altos)
        p_lah_alto = next(c.probability for c in res_alto if c.surface_form == "lah")

        assert p_lah_alto > p_lah_bajo, (
            f"Elevar *CODA[s] no favoreció aspiración: "
            f"P(lah|bajo)={p_lah_bajo:.4f}, P(lah|alto)={p_lah_alto:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests de Degeneración (Convergencia a Uniforme)
# ---------------------------------------------------------------------------

class TestDegeneracionUniforme:
    """Verifica que pesos uniformes producen distribución cercana a uniforme."""

    def test_pesos_cero_producen_distribucion_uniforme(self, gramatica: MaxEntGrammar) -> None:
        """
        Con todos los pesos en 0.0, H(y) = 0 para todo candidato, por lo que
        P(y|x) = 1/N (distribución uniforme).
        """
        candidatos = _crear_candidatos_coda_s()
        pesos_cero = {c.name: 0.0 for c in gramatica.constraints}
        resultados = gramatica.evaluate_candidates("las", candidatos, weights_override=pesos_cero)

        n = len(resultados)
        prob_esperada = 1.0 / n
        for c in resultados:
            assert abs(c.probability - prob_esperada) < 1e-6, (
                f"Con pesos cero, P({c.surface_form}) = {c.probability:.6f} ≠ {prob_esperada:.6f}"
            )

    def test_candidato_unico_probabilidad_uno(self, gramatica: MaxEntGrammar) -> None:
        """Un único candidato debe tener probabilidad exactamente 1.0."""
        candidato_unico = [
            ("las", {"coda_phones": ["s"], "all_phones": ["l", "a", "s"],
                     "underlying_phones": ["l", "a", "s"], "surface_phones": ["l", "a", "s"]}),
        ]
        resultados = gramatica.evaluate_candidates("las", candidato_unico)
        assert len(resultados) == 1
        assert abs(resultados[0].probability - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Tests de Calibración Isoglosa → Peso
# ---------------------------------------------------------------------------

class TestCalibracionIsoglosaPeso:
    """Verifica que el mapping isoglosa → peso sea monotónico y acotado."""

    def test_aspiracion_creciente_eleva_peso_coda_s(self, gramatica: MaxEntGrammar) -> None:
        """
        aspiration_s ↑ ⟹ w(*CODA[s]) ↑
        """
        w_bajo = gramatica.calibrate_weights_from_isoglosses({"aspiration_s": 0.0})
        w_medio = gramatica.calibrate_weights_from_isoglosses({"aspiration_s": 0.5})
        w_alto = gramatica.calibrate_weights_from_isoglosses({"aspiration_s": 1.0})

        assert w_bajo["*CODA[s]"] <= w_medio["*CODA[s]"] <= w_alto["*CODA[s]"], (
            f"No monotónico: w(0.0)={w_bajo['*CODA[s]']:.2f}, "
            f"w(0.5)={w_medio['*CODA[s]']:.2f}, w(1.0)={w_alto['*CODA[s]']:.2f}"
        )

    def test_pesos_calibrados_no_negativos(self, gramatica: MaxEntGrammar) -> None:
        """Todos los pesos calibrados deben ser ≥ 0."""
        for asp in [0.0, 0.25, 0.5, 0.75, 1.0]:
            pesos = gramatica.calibrate_weights_from_isoglosses({
                "aspiration_s": asp,
                "lambdacism": asp * 0.5,
                "rhotacism": asp * 0.3,
            })
            for nombre, peso in pesos.items():
                assert peso >= 0.0, (
                    f"Peso negativo: {nombre} = {peso:.4f} con aspiration_s={asp}"
                )

    def test_lista_candidatos_vacia_retorna_vacia(self, gramatica: MaxEntGrammar) -> None:
        """evaluate_candidates con lista vacía debe retornar lista vacía sin error."""
        resultados = gramatica.evaluate_candidates("las", [])
        assert resultados == []
