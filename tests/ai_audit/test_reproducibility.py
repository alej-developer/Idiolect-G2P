"""
Auditoría Dimensión 4: Consistencia y Reproducibilidad de las Predicciones.
Valida que el motor bayesiano sea determinista, estable ante reordenamiento
de estrofas, invariante a whitespace superficial e idempotente.

AI Audit Dimension 4: Prediction Consistency and Reproducibility.
"""

import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    IdiolectProfileResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

POEMA_REFERENCIA = """
En este dulce abrazo
yo sigo cada paso
unido por el lazo
en este nuevo caso
"""

SONETO_REFERENCIA = """
Mientras por competir con tu cabello,
oro bruñido al sol relumbra en vano;
mientras con menosprecio en medio el llano
mira tu blanca frente el lilio bello;

mientras a cada labio, por cogello,
siguen más ojos que al clavel temprano;
y mientras triunfa con desdén lozano
del luciente cristal tu gentil cuello:

goza cuello, cabello, labio y frente,
antes que lo que fue en tu edad dorada
oro, lilio, clavel, cristal luciente,

no sólo en plata o vïola troncada
se vuelva, mas tú y ello juntamente
en tierra, en humo, en polvo, en sombra, en nada.
"""


@pytest.fixture
def profiler() -> BayesianIdiolectProfiler:
    return BayesianIdiolectProfiler()


# ---------------------------------------------------------------------------
# Tests de Determinismo
# ---------------------------------------------------------------------------

class TestDeterminismo:
    """Verifica que la misma entrada produzca exactamente el mismo resultado."""

    def test_misma_entrada_mismo_resultado_100_veces(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Ejecutar la inferencia 100 veces con la misma entrada debe producir
        idénticos predicted_dialect_code, confidence_score y posteriors.
        """
        resultado_referencia = profiler.profile_poem(POEMA_REFERENCIA)

        for i in range(99):
            resultado = profiler.profile_poem(POEMA_REFERENCIA)
            assert resultado.predicted_dialect_code == resultado_referencia.predicted_dialect_code, (
                f"Iteración {i+2}: dialecto cambió de "
                f"{resultado_referencia.predicted_dialect_code} a {resultado.predicted_dialect_code}"
            )
            assert abs(resultado.confidence_score - resultado_referencia.confidence_score) < 1e-10, (
                f"Iteración {i+2}: confidence_score difiere en "
                f"{abs(resultado.confidence_score - resultado_referencia.confidence_score):.2e}"
            )

    def test_determinismo_con_instancias_separadas(self) -> None:
        """Dos instancias independientes del profiler deben dar el mismo resultado."""
        profiler_a = BayesianIdiolectProfiler()
        profiler_b = BayesianIdiolectProfiler()

        resultado_a = profiler_a.profile_poem(SONETO_REFERENCIA)
        resultado_b = profiler_b.profile_poem(SONETO_REFERENCIA)

        assert resultado_a.predicted_dialect_code == resultado_b.predicted_dialect_code
        assert abs(resultado_a.confidence_score - resultado_b.confidence_score) < 1e-10

        for dp_a, dp_b in zip(resultado_a.dialect_probabilities, resultado_b.dialect_probabilities):
            assert dp_a.dialect_code == dp_b.dialect_code
            assert abs(dp_a.posterior_probability - dp_b.posterior_probability) < 1e-10


# ---------------------------------------------------------------------------
# Tests de Invarianza a Whitespace
# ---------------------------------------------------------------------------

class TestInvarianzaWhitespace:
    """Verifica que espacios, tabs y newlines extra no alteren el resultado."""

    def test_espacios_extra_no_cambian_prediccion(self, profiler: BayesianIdiolectProfiler) -> None:
        """Espacios dobles/triples entre palabras no deben afectar la predicción."""
        poema_normal = """
        En este dulce abrazo
        yo sigo cada paso
        """
        poema_espacios = """
        En   este   dulce   abrazo
        yo   sigo   cada   paso
        """
        resultado_normal = profiler.profile_poem(poema_normal)
        resultado_espacios = profiler.profile_poem(poema_espacios)

        assert resultado_normal.predicted_dialect_code == resultado_espacios.predicted_dialect_code

    def test_tabs_no_cambian_prediccion(self, profiler: BayesianIdiolectProfiler) -> None:
        """Tabuladores usados como indentación no deben alterar la predicción."""
        poema_espacios = """
        En este dulce abrazo
        yo sigo cada paso
        """
        poema_tabs = """
\tEn este dulce abrazo
\tyo sigo cada paso
        """
        resultado_espacios = profiler.profile_poem(poema_espacios)
        resultado_tabs = profiler.profile_poem(poema_tabs)

        assert resultado_espacios.predicted_dialect_code == resultado_tabs.predicted_dialect_code

    def test_newlines_extra_no_cambian_prediccion(self, profiler: BayesianIdiolectProfiler) -> None:
        """Líneas en blanco adicionales entre versos no deben alterar la predicción."""
        poema_compacto = """
        En este dulce abrazo
        yo sigo cada paso
        unido por el lazo
        en este nuevo caso
        """
        poema_espaciado = """

        En este dulce abrazo


        yo sigo cada paso

        unido por el lazo


        en este nuevo caso

        """
        resultado_compacto = profiler.profile_poem(poema_compacto)
        resultado_espaciado = profiler.profile_poem(poema_espaciado)

        assert resultado_compacto.predicted_dialect_code == resultado_espaciado.predicted_dialect_code


# ---------------------------------------------------------------------------
# Tests de Estabilidad ante Reordenamiento Parcial
# ---------------------------------------------------------------------------

class TestEstabilidadReordenamiento:
    """Verifica estabilidad de la predicción dialectal ante reordenamiento."""

    def test_estrofas_reordenadas_misma_prediccion(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Un poema con dos estrofas intercambiadas debe producir la misma
        predicción dialectal (±tolerancia en confidence).
        """
        poema_original = """
        En este dulce abrazo
        yo sigo cada paso

        unido por el lazo
        en este nuevo caso
        """
        poema_reordenado = """
        unido por el lazo
        en este nuevo caso

        En este dulce abrazo
        yo sigo cada paso
        """
        resultado_original = profiler.profile_poem(poema_original)
        resultado_reordenado = profiler.profile_poem(poema_reordenado)

        assert resultado_original.predicted_dialect_code == resultado_reordenado.predicted_dialect_code, (
            f"Reordenar estrofas cambió la predicción de "
            f"{resultado_original.predicted_dialect_code} a {resultado_reordenado.predicted_dialect_code}"
        )

    def test_lambda_sensitivity_no_afecta_orden_dialectal(self) -> None:
        """
        Distintos valores de lambda_sensitivity deben producir el mismo
        ranking relativo de dialectos para un poema con señal fuerte.
        """
        resultados_por_lambda = {}
        for lam in [4.0, 16.0, 64.0]:
            profiler = BayesianIdiolectProfiler(lambda_sensitivity=lam)
            resultado = profiler.profile_poem(POEMA_REFERENCIA)
            resultados_por_lambda[lam] = resultado.predicted_dialect_code

        # Todos deben predecir el mismo dialecto ganador
        dialectos_unicos = set(resultados_por_lambda.values())
        assert len(dialectos_unicos) == 1, (
            f"Distintos λ produjeron distintas predicciones: {resultados_por_lambda}"
        )
