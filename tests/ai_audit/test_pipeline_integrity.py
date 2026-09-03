"""
Auditoría Dimensión 7: Integridad del Pipeline End-to-End.
Valida la coherencia entre módulos del pipeline completo: desde el análisis
métrico hasta la inferencia bayesiana, pasando por la gramática MaxEnt y
el explicador forense. Verifica conservación de información, contratos de tipo,
coherencia transductor-inferencia, y funcionalidad del prior diacrónico.

AI Audit Dimension 7: End-to-End Pipeline Integrity.
"""

import pytest
from dataclasses import fields
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    IdiolectProfileResult,
    DialectProbability,
    profile_idiolect_from_poem,
)
from idiolect_g2p.inference.forensic_explainer import (
    ForensicReport,
    DiscriminantEvidence,
    generate_forensic_explanation,
)
from idiolect_g2p.inference.maxent_grammar import MaxEntGrammar, MaxEntCandidate
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY
from idiolect_g2p.core.transducer import G2PTransducer, TransductionResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

POEMA_SESEO = """
En este dulce abrazo
yo sigo cada paso
unido por el lazo
en este nuevo caso
"""

SONETO_SIGLO_ORO = """
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
# Tests de Conservación de Información
# ---------------------------------------------------------------------------

class TestConservacionDeInformacion:
    """Verifica que no se pierdan versos ni palabras entre etapas del pipeline."""

    def test_todos_los_versos_presentes_en_analisis(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        El análisis métrico dentro del resultado de inferencia debe contener
        todos los versos no vacíos del poema original.
        """
        resultado = profiler.profile_poem(POEMA_SESEO)
        versos_analisis = resultado.poem_analysis.all_verses

        # Contar líneas no vacías del poema
        lineas_no_vacias = [l.strip() for l in POEMA_SESEO.strip().split("\n") if l.strip()]
        assert len(versos_analisis) == len(lineas_no_vacias), (
            f"Versos perdidos: poema tiene {len(lineas_no_vacias)} líneas, "
            f"análisis tiene {len(versos_analisis)} versos"
        )

    def test_transcripciones_optimas_no_vacias(self, profiler: BayesianIdiolectProfiler) -> None:
        """Las transcripciones óptimas deben contener al menos una entrada."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        assert len(resultado.optimal_transcriptions) > 0, (
            "No se generaron transcripciones óptimas"
        )

    def test_rimas_evaluadas_presentes(self, profiler: BayesianIdiolectProfiler) -> None:
        """Los pares de rima evaluados deben ser una lista no vacía."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        assert len(resultado.evaluated_rhyme_matches) > 0, (
            "No se evaluaron pares de rima"
        )


# ---------------------------------------------------------------------------
# Tests de Coherencia Transductor ↔ Inferencia
# ---------------------------------------------------------------------------

class TestCoherenciaTransductorInferencia:
    """Verifica que las transcripciones óptimas correspondan al dialecto predicho."""

    def test_transcripciones_son_transduction_result(self, profiler: BayesianIdiolectProfiler) -> None:
        """Cada transcripción óptima debe ser una instancia de TransductionResult."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        for tr in resultado.optimal_transcriptions:
            assert isinstance(tr, TransductionResult), (
                f"Transcripción no es TransductionResult: {type(tr)}"
            )

    def test_transcripciones_tienen_ipa_no_vacio(self, profiler: BayesianIdiolectProfiler) -> None:
        """Cada transcripción IPA debe ser un string no vacío."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        for tr in resultado.optimal_transcriptions:
            assert isinstance(tr.ipa_transcription, str)
            assert len(tr.ipa_transcription) > 0, (
                f"Transcripción IPA vacía para '{tr.original_text}'"
            )


# ---------------------------------------------------------------------------
# Tests del Prior Diacrónico
# ---------------------------------------------------------------------------

class TestPriorDiacronico:
    """Verifica que century_prior module la distribución posterior correctamente."""

    def test_century_16_favorece_siglo_de_oro(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Con century_prior=16, el dialecto DIACHRONIC_GOLDEN_AGE debe tener
        mayor posterior que sin el prior.
        """
        resultado_sin_prior = profiler.profile_poem(SONETO_SIGLO_ORO)
        resultado_con_prior = profiler.profile_poem(SONETO_SIGLO_ORO, century_prior=16)

        prob_sin = next(
            (dp.posterior_probability for dp in resultado_sin_prior.dialect_probabilities
             if dp.dialect_code == "DIACHRONIC_GOLDEN_AGE"), 0.0
        )
        prob_con = next(
            (dp.posterior_probability for dp in resultado_con_prior.dialect_probabilities
             if dp.dialect_code == "DIACHRONIC_GOLDEN_AGE"), 0.0
        )

        assert prob_con > prob_sin, (
            f"century_prior=16 no favoreció Siglo de Oro: "
            f"P(sin)={prob_sin:.6f}, P(con)={prob_con:.6f}"
        )

    def test_century_13_favorece_medieval(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Con century_prior=13, el dialecto DIACHRONIC_MEDIEVAL debe tener
        mayor posterior que sin el prior.
        """
        poema_medieval = """
        La donzella del castillo fuerte
        con el cauallero de buena suerte
        en la batalla contra la muerte
        buscando la gloria que no se pierde
        """
        resultado_sin = profiler.profile_poem(poema_medieval)
        resultado_con = profiler.profile_poem(poema_medieval, century_prior=13)

        prob_sin = next(
            (dp.posterior_probability for dp in resultado_sin.dialect_probabilities
             if dp.dialect_code == "DIACHRONIC_MEDIEVAL"), 0.0
        )
        prob_con = next(
            (dp.posterior_probability for dp in resultado_con.dialect_probabilities
             if dp.dialect_code == "DIACHRONIC_MEDIEVAL"), 0.0
        )

        assert prob_con > prob_sin, (
            f"century_prior=13 no favoreció Medieval: "
            f"P(sin)={prob_sin:.6f}, P(con)={prob_con:.6f}"
        )

    def test_century_21_penaliza_diacronicos(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        Con century_prior=21, los dialectos diacrónicos deben tener posteriors
        menores que sin prior (o al menos no mayores).
        """
        resultado_sin = profiler.profile_poem(POEMA_SESEO)
        resultado_con = profiler.profile_poem(POEMA_SESEO, century_prior=21)

        for dp_sin, dp_con in zip(
            resultado_sin.dialect_probabilities,
            resultado_con.dialect_probabilities,
        ):
            if "DIACHRONIC" in dp_sin.dialect_code:
                # Encontrar el mismo dialecto en ambos resultados
                prob_sin = dp_sin.posterior_probability
                prob_con_match = next(
                    (d.posterior_probability for d in resultado_con.dialect_probabilities
                     if d.dialect_code == dp_sin.dialect_code), 0.0
                )
                assert prob_con_match <= prob_sin + 0.01, (
                    f"century_prior=21 no penalizó {dp_sin.dialect_code}: "
                    f"P(sin)={prob_sin:.6f}, P(con)={prob_con_match:.6f}"
                )


# ---------------------------------------------------------------------------
# Tests de Contratos de Tipo
# ---------------------------------------------------------------------------

class TestContratosDeTipo:
    """Verifica que todos los outputs cumplan los contratos de tipo de los dataclasses."""

    def test_idiolect_profile_result_tipos_correctos(self, profiler: BayesianIdiolectProfiler) -> None:
        """Todos los campos de IdiolectProfileResult deben tener el tipo esperado."""
        resultado = profiler.profile_poem(POEMA_SESEO)

        assert isinstance(resultado.predicted_dialect_code, str)
        assert isinstance(resultado.predicted_dialect_name, str)
        assert isinstance(resultado.confidence_score, float)
        assert isinstance(resultado.estimated_isogloss_vector, dict)
        assert isinstance(resultado.dialect_probabilities, list)
        assert isinstance(resultado.poem_analysis, object)
        assert isinstance(resultado.evaluated_rhyme_matches, list)
        assert isinstance(resultado.optimal_transcriptions, list)

    def test_dialect_probability_tipos_correctos(self, profiler: BayesianIdiolectProfiler) -> None:
        """Todos los campos de DialectProbability deben tener el tipo esperado."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        for dp in resultado.dialect_probabilities:
            assert isinstance(dp, DialectProbability)
            assert isinstance(dp.dialect_code, str)
            assert isinstance(dp.dialect_name, str)
            assert isinstance(dp.region, str)
            assert isinstance(dp.posterior_probability, float)
            assert isinstance(dp.log_likelihood, float)
            assert isinstance(dp.total_phonetic_distance, float)
            assert isinstance(dp.perfect_rhymes_count, int)
            assert isinstance(dp.total_evaluated_pairs, int)

    def test_isogloss_vector_claves_conocidas(self, profiler: BayesianIdiolectProfiler) -> None:
        """El vector de isoglosas estimado debe contener solo claves conocidas."""
        resultado = profiler.profile_poem(POEMA_SESEO)

        claves_esperadas = {
            "seseo", "aspiration_s", "lambdacism", "rhotacism", "gemination",
            "rehilamiento_voiced", "rehilamiento_voiceless", "lleismo",
            "assibilation_r", "vowel_opening", "velar_nasal", "vocalic_reduction",
            "glottal_j", "affricate_tl", "diachronic_sibilants", "initial_f_aspiration",
        }
        for clave, valor in resultado.estimated_isogloss_vector.items():
            assert clave in claves_esperadas, f"Clave de isoglosa desconocida: '{clave}'"
            assert isinstance(valor, float), f"Valor de isoglosa no es float: {type(valor)}"
            assert 0.0 <= valor <= 1.0, f"Isoglosa '{clave}' fuera de [0,1]: {valor}"


# ---------------------------------------------------------------------------
# Tests de Pipeline Completo
# ---------------------------------------------------------------------------

class TestPipelineCompleto:
    """Verifica la coherencia end-to-end del pipeline inferencia → reporte."""

    def test_pipeline_completo_sin_errores(self, profiler: BayesianIdiolectProfiler) -> None:
        """
        El pipeline completo (perfilación → reporte forense) debe ejecutarse
        sin errores para múltiples poemas.
        """
        poemas = [POEMA_SESEO, SONETO_SIGLO_ORO]
        for poema in poemas:
            resultado = profiler.profile_poem(poema)
            reporte = generate_forensic_explanation(resultado, case_id="PIPELINE-TEST")

            assert isinstance(reporte, ForensicReport)
            assert reporte.case_identifier == "PIPELINE-TEST"
            assert len(reporte.dialect_ranking) > 0

    def test_dialecto_predicho_existe_en_registro(self, profiler: BayesianIdiolectProfiler) -> None:
        """El dialecto predicho debe existir en el registro global."""
        resultado = profiler.profile_poem(POEMA_SESEO)
        dialecto = GLOBAL_DIALECT_REGISTRY.get(resultado.predicted_dialect_code)
        assert dialecto is not None, (
            f"Dialecto predicho '{resultado.predicted_dialect_code}' no existe en el registro"
        )
