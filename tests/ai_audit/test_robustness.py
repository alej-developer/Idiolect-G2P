"""
Auditoría Dimensión 3: Robustez y Estabilidad ante Entradas Adversariales.
Valida que el motor de inferencia bayesiana y la gramática MaxEnt manejen
graciosamente entradas vacías, malformadas, extremas y en idiomas incorrectos
sin producir excepciones no controladas ni resultados inválidos.

AI Audit Dimension 3: Robustness and Stability under Adversarial Inputs.
"""

import math
import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    IdiolectProfileResult,
    profile_idiolect_from_poem,
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def profiler() -> BayesianIdiolectProfiler:
    return BayesianIdiolectProfiler()


# ---------------------------------------------------------------------------
# Tests de Entradas Vacías y Degeneradas
# ---------------------------------------------------------------------------

class TestEntradasVaciasYDegeneradas:
    """Verifica comportamiento estable ante poemas vacíos, mínimos o sin contenido útil."""

    def test_poema_vacio_no_lanza_excepcion(self, profiler: BayesianIdiolectProfiler) -> None:
        """Un string vacío no debe lanzar excepción; debe retornar resultado degradado."""
        resultado = profiler.profile_poem("")
        assert isinstance(resultado, IdiolectProfileResult)
        assert resultado.predicted_dialect_code is not None

    def test_poema_solo_espacios_y_newlines(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto compuesto solo de whitespace no debe causar crash."""
        resultado = profiler.profile_poem("   \n\n  \t  \n   ")
        assert isinstance(resultado, IdiolectProfileResult)

    def test_poema_un_solo_verso(self, profiler: BayesianIdiolectProfiler) -> None:
        """Un verso aislado sin par de rima debe generar resultado válido."""
        resultado = profiler.profile_poem("En la caza del amanecer")
        assert isinstance(resultado, IdiolectProfileResult)
        suma = sum(dp.posterior_probability for dp in resultado.dialect_probabilities)
        assert abs(suma - 1.0) < 1e-5

    def test_poema_una_sola_palabra(self, profiler: BayesianIdiolectProfiler) -> None:
        """Una sola palabra aislada debe generar resultado válido sin crash."""
        resultado = profiler.profile_poem("casa")
        assert isinstance(resultado, IdiolectProfileResult)
        assert resultado.predicted_dialect_code is not None


# ---------------------------------------------------------------------------
# Tests de Entradas con Caracteres Especiales
# ---------------------------------------------------------------------------

class TestEntradasConCaracteresEspeciales:
    """Verifica manejo de puntuación, números, emojis y caracteres no alfabéticos."""

    def test_solo_puntuacion_y_numeros(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto sin letras (solo signos y números) no debe causar crash."""
        resultado = profiler.profile_poem("123 456! @#$ %^& *() 789...")
        assert isinstance(resultado, IdiolectProfileResult)

    def test_emojis_y_caracteres_unicode_raros(self, profiler: BayesianIdiolectProfiler) -> None:
        """Emojis y caracteres Unicode exóticos no deben causar excepción."""
        texto = "🎭 La máscara 🎶 del poeta 🌙 canta 🎭"
        resultado = profiler.profile_poem(texto)
        assert isinstance(resultado, IdiolectProfileResult)

    def test_mezcla_de_cero_width_y_control_chars(self, profiler: BayesianIdiolectProfiler) -> None:
        """Caracteres de ancho cero y de control intercalados no causan crash."""
        texto = "Ca\u200Bsa\u200C del \uFEFFpo\u200Deta"
        resultado = profiler.profile_poem(texto)
        assert isinstance(resultado, IdiolectProfileResult)


# ---------------------------------------------------------------------------
# Tests de Poemas Extremadamente Largos
# ---------------------------------------------------------------------------

class TestPoemasExtremos:
    """Verifica que el sistema maneje poemas largos sin degradación catastrófica."""

    def test_poema_500_versos_sin_timeout(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Un poema de ~500 versos debe completar la inferencia sin timeout.
        El límite temporal depende del hardware, aquí solo verificamos
        que no haya crash ni resultados inválidos.
        """
        estrofa = """
        En este dulce abrazo
        yo sigo cada paso
        unido por el lazo
        en este nuevo caso
        """
        poema_largo = estrofa * 125  # ~500 versos
        resultado = profiler.profile_poem(poema_largo)

        assert isinstance(resultado, IdiolectProfileResult)
        suma = sum(dp.posterior_probability for dp in resultado.dialect_probabilities)
        assert abs(suma - 1.0) < 1e-4
        for dp in resultado.dialect_probabilities:
            assert math.isfinite(dp.posterior_probability)


# ---------------------------------------------------------------------------
# Tests de Idiomas Incorrectos
# ---------------------------------------------------------------------------

class TestIdiomasIncorrectos:
    """Verifica que texto en otros idiomas no cause crash y genere baja confianza."""

    def test_texto_en_ingles_no_causa_crash(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto en inglés debe procesarse sin excepción."""
        texto_ingles = """
        Shall I compare thee to a summer's day?
        Thou art more lovely and more temperate.
        Rough winds do shake the darling buds of May,
        And summer's lease hath all too short a date.
        """
        resultado = profiler.profile_poem(texto_ingles)
        assert isinstance(resultado, IdiolectProfileResult)
        assert resultado.predicted_dialect_code is not None

    def test_texto_en_frances_no_causa_crash(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto en francés debe procesarse sin excepción."""
        texto_frances = """
        Je suis le ténébreux, le veuf, l'inconsolé,
        Le prince d'Aquitaine à la tour abolie.
        Ma seule étoile est morte, et mon luth constellé
        Porte le soleil noir de la Mélancolie.
        """
        resultado = profiler.profile_poem(texto_frances)
        assert isinstance(resultado, IdiolectProfileResult)


# ---------------------------------------------------------------------------
# Tests de Perturbación de Caracteres
# ---------------------------------------------------------------------------

class TestPerturbacionDeCaracteres:
    """Verifica degradación suave ante perturbaciones ortográficas."""

    def test_swap_de_caracteres_no_causa_crash(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto con letras intercambiadas no debe causar crash."""
        texto_perturbado = """
        En eset dulce abrzao
        yo sgoi cdaa psao
        undio por el laoz
        en eset nueov caos
        """
        resultado = profiler.profile_poem(texto_perturbado)
        assert isinstance(resultado, IdiolectProfileResult)
        suma = sum(dp.posterior_probability for dp in resultado.dialect_probabilities)
        assert abs(suma - 1.0) < 1e-5

    def test_texto_con_repeticiones_extremas(self, profiler: BayesianIdiolectProfiler) -> None:
        """Texto con la misma palabra repetida muchas veces no causa crash."""
        texto_repetido = "casa " * 200
        resultado = profiler.profile_poem(texto_repetido)
        assert isinstance(resultado, IdiolectProfileResult)

    def test_texto_con_lineas_muy_largas(self, profiler: BayesianIdiolectProfiler) -> None:
        """Una línea de texto extremadamente larga (sin saltos) no causa crash."""
        texto_largo = "En la caza del amanecer bajo el sol de la mañana " * 50
        resultado = profiler.profile_poem(texto_largo)
        assert isinstance(resultado, IdiolectProfileResult)
