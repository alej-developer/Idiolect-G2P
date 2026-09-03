"""
Auditoría Dimensión 5: Fairness y Sesgo Dialectal.
Valida que el sistema no tenga sesgos implícitos hacia o contra dialectos
específicos, que la cobertura de priors sea uniforme ante evidencia ambigua,
y que el corpus de validación balanceado sea clasificado correctamente.

AI Audit Dimension 5: Dialect Fairness and Bias Auditing.
"""

import math
import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    IdiolectProfileResult,
    profile_idiolect_from_poem,
)
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def profiler() -> BayesianIdiolectProfiler:
    return BayesianIdiolectProfiler()


@pytest.fixture
def todos_los_dialectos():
    """Lista de todos los códigos de dialectos registrados."""
    return [d.code for d in GLOBAL_DIALECT_REGISTRY.list_all()]


# ---------------------------------------------------------------------------
# Corpus de poemas con señal dialectal diagnóstica
# ---------------------------------------------------------------------------

# Cada poema está diseñado para contener rasgos fonológicos diagnósticos
# del dialecto indicado (seseo, lambdacismo, etc.)
CORPUS_DIALECTAL = {
    "MX_CENTRAL": """
    La caza en la llanura empieza
    cuando el sol muestra su belleza
    mientras corre con gran destreza
    buscando siempre la certeza
    """,
    "CARIBBEAN_LAMBDACIST": """
    Llegó la barca al puerto
    con el marinero muelto
    bajo la luz del sol
    buscando su gran amor
    """,
    "ES_PENINSULAR": """
    La caza por el bosque suena
    mientras el lazo se encadena
    el cielo azul de plena luna
    ilumina toda la duna
    """,
}


# ---------------------------------------------------------------------------
# Tests de Cobertura Uniforme de Priors
# ---------------------------------------------------------------------------

class TestCoberturaUniformePriors:
    """Verifica que ningún dialecto tenga ventaja implícita ante evidencia nula."""

    def test_priors_implicitos_no_dominados(
        self, profiler: BayesianIdiolectProfiler, todos_los_dialectos: list
    ) -> None:
        """
        Con un poema genérico sin señal dialectal fuerte, ningún dialecto
        debería acaparar más del 50% de la posterior. Esto verifica que
        no hay un prior implícito dominante.
        """
        poema_neutro = """
        Las flores en el campo se abren
        los pájaros al cielo cantan
        las nubes lentas se esparcen
        mientras las aguas se levantan
        """
        resultado = profiler.profile_poem(poema_neutro)

        for dp in resultado.dialect_probabilities:
            assert dp.posterior_probability < 0.50, (
                f"Dialecto {dp.dialect_code} domina con P={dp.posterior_probability:.4f} "
                f"ante evidencia neutra (umbral: < 0.50)"
            )

    def test_todos_los_dialectos_representados(
        self, profiler: BayesianIdiolectProfiler, todos_los_dialectos: list
    ) -> None:
        """
        La inferencia debe evaluar todos los dialectos registrados.
        Ningún dialecto debe ser excluido del ranking.
        """
        resultado = profiler.profile_poem("La casa del poeta en la plaza del pueblo")
        dialectos_evaluados = {dp.dialect_code for dp in resultado.dialect_probabilities}

        for codigo in todos_los_dialectos:
            assert codigo in dialectos_evaluados, (
                f"Dialecto {codigo} excluido de la evaluación"
            )


# ---------------------------------------------------------------------------
# Tests de No-Discriminación de Dialectos Minoritarios
# ---------------------------------------------------------------------------

class TestNoDiscriminacionMinoritarios:
    """Verifica que dialectos menos comunes no tengan desventaja sistemática."""

    def test_dialectos_minoritarios_no_tienen_posterior_cero(
        self, profiler: BayesianIdiolectProfiler
    ) -> None:
        """
        Dialectos minoritarios (Canario, Andino Asibilado, Rioplatense Sheísta)
        no deben tener posterior exactamente 0 en ninguna inferencia razonable.
        """
        poema = """
        En este dulce abrazo
        yo sigo cada paso
        unido por el lazo
        en este nuevo caso
        """
        resultado = profiler.profile_poem(poema)

        dialectos_minoritarios = ["CANARIAN", "ANDEAN_ASSIBILATED", "RIOPLATENSE_SHEIST"]
        for dp in resultado.dialect_probabilities:
            if dp.dialect_code in dialectos_minoritarios:
                assert dp.posterior_probability > 0.0, (
                    f"Dialecto minoritario {dp.dialect_code} tiene posterior = 0.0"
                )

    def test_dialectos_diacronicos_accesibles_con_prior(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Con century_prior=16 (Siglo de Oro), los dialectos diacrónicos deben
        ser accesibles y no quedar marginados.
        """
        poema_clasico = """
        Mientras por competir con tu cabello,
        oro bruñido al sol relumbra en vano;
        mientras con menosprecio en medio el llano
        mira tu blanca frente el lilio bello;
        """
        resultado = profiler.profile_poem(poema_clasico, century_prior=16)

        dialectos_diacronicos = {"DIACHRONIC_GOLDEN_AGE", "DIACHRONIC_MEDIEVAL"}
        posteriors_diacronicos = [
            dp.posterior_probability
            for dp in resultado.dialect_probabilities
            if dp.dialect_code in dialectos_diacronicos
        ]
        assert len(posteriors_diacronicos) > 0, "No se encontraron dialectos diacrónicos"
        assert any(p > 0.01 for p in posteriors_diacronicos), (
            f"Dialectos diacrónicos marginados con century_prior=16: {posteriors_diacronicos}"
        )


# ---------------------------------------------------------------------------
# Tests de Clasificación con Corpus Balanceado
# ---------------------------------------------------------------------------

class TestClasificacionCorpusBalanceado:
    """Verifica que poemas diagnósticos sean clasificados en el dialecto correcto."""

    @pytest.mark.parametrize("dialecto_esperado,poema", [
        ("MX_CENTRAL", CORPUS_DIALECTAL["MX_CENTRAL"]),
        ("CARIBBEAN_LAMBDACIST", CORPUS_DIALECTAL["CARIBBEAN_LAMBDACIST"]),
    ], ids=["mexicano_central", "caribeño_lambdacista"])
    def test_poema_diagnostico_clasificado_correctamente(
        self, profiler: BayesianIdiolectProfiler, dialecto_esperado: str, poema: str
    ) -> None:
        """
        Un poema diseñado con rasgos diagnósticos de un dialecto debe ser
        clasificado en ese dialecto o en uno de la misma macrorregión.
        """
        resultado = profiler.profile_poem(poema)

        # Verificar que el dialecto esperado esté entre los top-3
        top_3_codigos = [dp.dialect_code for dp in resultado.dialect_probabilities[:3]]
        assert dialecto_esperado in top_3_codigos, (
            f"Dialecto {dialecto_esperado} no está en el top-3: {top_3_codigos}"
        )


# ---------------------------------------------------------------------------
# Tests de Entropía Acotada
# ---------------------------------------------------------------------------

class TestEntropiaAcotada:
    """Verifica que la entropía de la distribución posterior esté en rango válido."""

    def test_entropia_entre_cero_y_log_n(
        self, profiler: BayesianIdiolectProfiler, todos_los_dialectos: list
    ) -> None:
        """
        La entropía de Shannon H debe estar en [0, log(N)], donde N es el
        número de dialectos. H = 0 significa certeza total, H = log(N) es
        máxima incertidumbre (uniforme).
        """
        resultado = profiler.profile_poem(CORPUS_DIALECTAL["MX_CENTRAL"])
        probs = [dp.posterior_probability for dp in resultado.dialect_probabilities]

        entropia = -sum(p * math.log(p + 1e-30) for p in probs)
        n = len(todos_los_dialectos)
        entropia_maxima = math.log(n)

        assert 0.0 <= entropia <= entropia_maxima + 0.01, (
            f"Entropía fuera de rango: H = {entropia:.4f}, "
            f"rango esperado [0, {entropia_maxima:.4f}]"
        )
