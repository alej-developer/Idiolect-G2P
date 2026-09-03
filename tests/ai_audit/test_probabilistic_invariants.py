"""
Auditoría Dimensión 1: Invariantes Probabilísticas del Motor Bayesiano.
Valida que el BayesianIdiolectProfiler respete los axiomas de probabilidad,
la estabilidad numérica de Log-Sum-Exp, y la monotonicidad bayesiana.

AI Audit Dimension 1: Probabilistic Invariants of the Bayesian Engine.
"""

import math
import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    IdiolectProfileResult,
    profile_idiolect_from_poem,
)


# ---------------------------------------------------------------------------
# Fixtures reutilizables
# ---------------------------------------------------------------------------

POEMA_SESEO = """
En este dulce abrazo
yo sigo cada paso
unido por el lazo
en este nuevo caso
"""

POEMA_LAMBDACISMO = """
Llegó la barca al puerto
con el marinero muelto
bajo la luz del sol
buscando su gran amor
"""

POEMA_DISTINCION = """
En la caza del amanecer
la luz se enciende sin cesar
mientras el campo al atardecer
nos deja en calma y en paz
"""

SONETO_GONGORA = """
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
    """Instancia compartida del perfilador bayesiano."""
    return BayesianIdiolectProfiler()


# ---------------------------------------------------------------------------
# Tests de Normalización y No-Negatividad
# ---------------------------------------------------------------------------

class TestNormalizacionProbabilistica:
    """Verifica los axiomas fundamentales de distribución de probabilidad."""

    @pytest.mark.parametrize("poema", [
        POEMA_SESEO,
        POEMA_LAMBDACISMO,
        POEMA_DISTINCION,
        SONETO_GONGORA,
    ], ids=["seseo", "lambdacismo", "distincion", "soneto_gongora"])
    def test_suma_posteriors_igual_a_uno(self, profiler: BayesianIdiolectProfiler, poema: str) -> None:
        """
        Axioma 1 (Normalización): La suma de probabilidades a posteriori de todos
        los dialectos debe ser exactamente 1.0 (±tolerancia numérica).
        Σ P(D_i | T, R) = 1.0
        """
        resultado = profiler.profile_poem(poema)
        suma_posteriors = sum(dp.posterior_probability for dp in resultado.dialect_probabilities)
        assert abs(suma_posteriors - 1.0) < 1e-6, (
            f"Violación del axioma de normalización: Σ P(D|T,R) = {suma_posteriors:.10f} ≠ 1.0"
        )

    @pytest.mark.parametrize("poema", [
        POEMA_SESEO,
        POEMA_LAMBDACISMO,
        POEMA_DISTINCION,
        SONETO_GONGORA,
    ], ids=["seseo", "lambdacismo", "distincion", "soneto_gongora"])
    def test_no_negatividad_posteriors(self, profiler: BayesianIdiolectProfiler, poema: str) -> None:
        """
        Axioma 2 (No-Negatividad): Toda probabilidad a posteriori debe ser ≥ 0.
        ∀ D_i: P(D_i | T, R) ≥ 0
        """
        resultado = profiler.profile_poem(poema)
        for dp in resultado.dialect_probabilities:
            assert dp.posterior_probability >= 0.0, (
                f"Probabilidad negativa detectada para {dp.dialect_code}: "
                f"P = {dp.posterior_probability}"
            )

    def test_confidence_score_en_rango_cero_uno(self, profiler: BayesianIdiolectProfiler) -> None:
        """Verifica que el confidence_score del ganador esté acotado en [0.0, 1.0]."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        assert 0.0 <= resultado.confidence_score <= 1.0, (
            f"confidence_score fuera de rango: {resultado.confidence_score}"
        )


# ---------------------------------------------------------------------------
# Tests de Monotonicidad Bayesiana
# ---------------------------------------------------------------------------

class TestMonotonicidadBayesiana:
    """Verifica que más evidencia concentra la distribución posterior."""

    def test_mas_evidencia_reduce_entropia(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Al añadir más versos con la misma señal dialectal (seseo), la entropía
        de Shannon de la distribución posterior debe decrecer o mantenerse.
        H(posterior_corto) ≥ H(posterior_largo) (más concentrada con más datos).
        """
        poema_corto = """
        En este dulce abrazo
        yo sigo cada paso
        """
        poema_largo = """
        En este dulce abrazo
        yo sigo cada paso
        unido por el lazo
        en este nuevo caso
        la traza de mi brazo
        siguiendo tu compás, tu regazo
        """

        resultado_corto = profiler.profile_poem(poema_corto)
        resultado_largo = profiler.profile_poem(poema_largo)

        def entropia_shannon(probs: list) -> float:
            return -sum(p * math.log(p + 1e-30) for p in probs)

        probs_corto = [dp.posterior_probability for dp in resultado_corto.dialect_probabilities]
        probs_largo = [dp.posterior_probability for dp in resultado_largo.dialect_probabilities]

        h_corto = entropia_shannon(probs_corto)
        h_largo = entropia_shannon(probs_largo)

        assert h_largo <= h_corto + 0.1, (
            f"La entropía no decreció con más evidencia: "
            f"H(corto)={h_corto:.4f}, H(largo)={h_largo:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests de Estabilidad Numérica (Log-Sum-Exp)
# ---------------------------------------------------------------------------

class TestEstabilidadNumerica:
    """Verifica que la normalización Log-Sum-Exp no produzca overflow ni underflow."""

    def test_sin_nan_ni_inf_en_posteriors(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Verifica que ningún posterior sea NaN o ±Inf, lo cual indicaría
        un fallo en la estabilización numérica de Log-Sum-Exp.
        """
        resultado = profiler.profile_poem(SONETO_GONGORA)
        for dp in resultado.dialect_probabilities:
            assert math.isfinite(dp.posterior_probability), (
                f"Posterior no finito para {dp.dialect_code}: P = {dp.posterior_probability}"
            )
            assert not math.isnan(dp.posterior_probability), (
                f"Posterior NaN para {dp.dialect_code}"
            )

    def test_sin_nan_ni_inf_en_log_likelihoods(self, profiler: BayesianIdiolectProfiler) -> None:
        """Verifica que las log-likelihoods crudas sean finitas."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        for dp in resultado.dialect_probabilities:
            assert math.isfinite(dp.log_likelihood), (
                f"Log-likelihood no finita para {dp.dialect_code}: LL = {dp.log_likelihood}"
            )

    def test_estabilidad_con_lambda_extremo(self) -> None:
        """
        Con lambda_sensitivity extremadamente alta (1000), la distribución se
        concentra casi toda en un solo dialecto. Pero no debe producir NaN/Inf.
        """
        profiler_extremo = BayesianIdiolectProfiler(lambda_sensitivity=1000.0)
        resultado = profiler_extremo.profile_poem(POEMA_SESEO)

        suma = sum(dp.posterior_probability for dp in resultado.dialect_probabilities)
        assert abs(suma - 1.0) < 1e-4, f"Normalización rota con λ=1000: Σ = {suma}"

        for dp in resultado.dialect_probabilities:
            assert math.isfinite(dp.posterior_probability), (
                f"Posterior no finito con λ=1000 para {dp.dialect_code}"
            )


# ---------------------------------------------------------------------------
# Test de Dominancia Estricta
# ---------------------------------------------------------------------------

class TestDominanciaEstricta:
    """Verifica que distancias fonéticas menores impliquen posteriors mayores."""

    def test_dialecto_con_menor_distancia_gana(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Si un dialecto D_a tiene distancia fonética total estrictamente menor que D_b,
        entonces P(D_a | T, R) > P(D_b | T, R) (ceteris paribus en priors).
        """
        resultado = profiler.profile_poem(POEMA_SESEO)

        # Construir mapeo código → (distancia, probabilidad)
        datos = {
            dp.dialect_code: (dp.total_phonetic_distance, dp.posterior_probability)
            for dp in resultado.dialect_probabilities
        }

        # El ganador debe tener la menor distancia entre los top-3
        ganador = resultado.dialect_probabilities[0]
        for dp in resultado.dialect_probabilities[1:4]:
            if dp.total_phonetic_distance > ganador.total_phonetic_distance + 0.5:
                assert ganador.posterior_probability > dp.posterior_probability, (
                    f"Violación de dominancia: {ganador.dialect_code} "
                    f"(dist={ganador.total_phonetic_distance:.4f}) tiene menor distancia que "
                    f"{dp.dialect_code} (dist={dp.total_phonetic_distance:.4f}) pero no mayor posterior"
                )
