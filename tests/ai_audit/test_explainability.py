"""
Auditoría Dimensión 6: Explicabilidad y Trazabilidad Forense.
Valida que los dictámenes periciales generados por el ForensicExplainer sean
completos, coherentes con la predicción, no-alucinatorios, y con ranking
consistente respecto a las probabilidades a posteriori.

AI Audit Dimension 6: Explainability and Forensic Traceability.
"""

import pytest
from idiolect_g2p.inference.bayesian_profiler import (
    BayesianIdiolectProfiler,
    profile_idiolect_from_poem,
)
from idiolect_g2p.inference.forensic_explainer import (
    ForensicReport,
    DiscriminantEvidence,
    generate_forensic_explanation,
)


# ---------------------------------------------------------------------------
# Fixtures
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


@pytest.fixture
def resultado_seseo():
    return profile_idiolect_from_poem(POEMA_SESEO)


@pytest.fixture
def resultado_lambdacismo():
    return profile_idiolect_from_poem(POEMA_LAMBDACISMO)


@pytest.fixture
def reporte_seseo(resultado_seseo):
    return generate_forensic_explanation(resultado_seseo, case_id="AUDIT-SESEO-001")


@pytest.fixture
def reporte_lambdacismo(resultado_lambdacismo):
    return generate_forensic_explanation(resultado_lambdacismo, case_id="AUDIT-LAMBDA-001")


# ---------------------------------------------------------------------------
# Tests de Completitud del Reporte
# ---------------------------------------------------------------------------

class TestCompletitudReporte:
    """Verifica que todos los campos obligatorios del dictamen estén presentes."""

    def test_campos_obligatorios_presentes(self, reporte_seseo: ForensicReport) -> None:
        """Todo reporte forense debe contener case_id, hipótesis, evidencias, ranking y conclusión."""
        assert reporte_seseo.case_identifier == "AUDIT-SESEO-001"
        assert isinstance(reporte_seseo.primary_hypothesis, str)
        assert len(reporte_seseo.primary_hypothesis) > 0
        assert isinstance(reporte_seseo.confidence_percentage, float)
        assert isinstance(reporte_seseo.isogloss_summary, dict)
        assert isinstance(reporte_seseo.discriminant_evidences, list)
        assert isinstance(reporte_seseo.dialect_ranking, list)
        assert isinstance(reporte_seseo.sociolinguistic_conclusion, str)
        assert len(reporte_seseo.sociolinguistic_conclusion) > 0

    def test_ranking_no_vacio(self, reporte_seseo: ForensicReport) -> None:
        """El ranking de dialectos debe contener al menos 1 entrada."""
        assert len(reporte_seseo.dialect_ranking) >= 1

    def test_conclusion_contiene_porcentaje(self, reporte_seseo: ForensicReport) -> None:
        """La conclusión sociolingüística debe mencionar el porcentaje de confianza."""
        assert "%" in reporte_seseo.sociolinguistic_conclusion


# ---------------------------------------------------------------------------
# Tests de Coherencia Evidencia ↔ Predicción
# ---------------------------------------------------------------------------

class TestCoherenciaEvidenciaPrediccion:
    """Verifica que las evidencias discriminantes sean coherentes con la predicción."""

    def test_evidencias_seseo_coherentes(self, reporte_seseo: ForensicReport) -> None:
        """
        Si el poema contiene señal de seseo y se detectan evidencias,
        al menos una debe mencionar 'Seseo' o 'sibilante'.
        """
        if len(reporte_seseo.discriminant_evidences) > 0:
            fenomenos = [ev.phonetic_phenomenon for ev in reporte_seseo.discriminant_evidences]
            tiene_seseo = any("eseo" in f or "sibilante" in f for f in fenomenos)
            assert tiene_seseo, (
                f"Evidencias no mencionan seseo para poema seseante: {fenomenos}"
            )

    def test_evidencias_lambdacismo_coherentes(self, reporte_lambdacismo: ForensicReport) -> None:
        """
        Si el poema contiene señal de lambdacismo y se detectan evidencias,
        al menos una debe mencionar 'liquida' o 'lambdacismo'.
        """
        if len(reporte_lambdacismo.discriminant_evidences) > 0:
            fenomenos = [ev.phonetic_phenomenon.lower() for ev in reporte_lambdacismo.discriminant_evidences]
            tiene_lambda = any("líquida" in f or "liquida" in f or "lambdacismo" in f for f in fenomenos)
            assert tiene_lambda, (
                f"Evidencias no mencionan lambdacismo para poema lambdacista: {fenomenos}"
            )


# ---------------------------------------------------------------------------
# Tests de Poder Discriminante Acotado
# ---------------------------------------------------------------------------

class TestPoderDiscriminanteAcotado:
    """Verifica que discriminating_power esté en [0.0, 1.0] para toda evidencia."""

    @pytest.mark.parametrize("fixture_name", ["reporte_seseo", "reporte_lambdacismo"])
    def test_discriminating_power_en_rango(self, fixture_name: str, request) -> None:
        """∀ evidencia: discriminating_power ∈ [0.0, 1.0]."""
        reporte = request.getfixturevalue(fixture_name)
        for ev in reporte.discriminant_evidences:
            assert 0.0 <= ev.discriminating_power <= 1.0, (
                f"discriminating_power fuera de rango: {ev.discriminating_power} "
                f"para {ev.phonetic_phenomenon}"
            )


# ---------------------------------------------------------------------------
# Tests de No-Alucinación
# ---------------------------------------------------------------------------

class TestNoAlucinacion:
    """Verifica que las evidencias solo referencien fenómenos reales del poema."""

    def test_palabras_de_evidencias_existen_en_poema(self, reporte_seseo: ForensicReport) -> None:
        """
        Las palabras referenciadas en cada evidencia discriminante deben
        existir en el texto original del poema.
        """
        palabras_poema = set(POEMA_SESEO.lower().split())
        for ev in reporte_seseo.discriminant_evidences:
            # Las palabras de la evidencia deben poder encontrarse en el poema
            assert ev.word_1.lower() in palabras_poema or ev.word_1.lower().strip(".,;:!?") in palabras_poema, (
                f"Palabra alucinada en evidencia: '{ev.word_1}' no está en el poema"
            )
            assert ev.word_2.lower() in palabras_poema or ev.word_2.lower().strip(".,;:!?") in palabras_poema, (
                f"Palabra alucinada en evidencia: '{ev.word_2}' no está en el poema"
            )

    def test_fenomenos_son_categorias_foneticas_reales(self, reporte_seseo: ForensicReport) -> None:
        """Los fenómenos fonéticos reportados deben pertenecer a categorías conocidas."""
        fenomenos_validos = {
            "seseo", "sibilante", "lambdacismo", "rotacismo", "líquida",
            "liquida", "yeísmo", "yeismo", "palatal", "aspiración", "aspiracion",
            "neutralización", "neutralizacion", "desfonologización", "desfonologizacion"
        }
        for ev in reporte_seseo.discriminant_evidences:
            fenomeno_lower = ev.phonetic_phenomenon.lower()
            tiene_termino_valido = any(t in fenomeno_lower for t in fenomenos_validos)
            assert tiene_termino_valido, (
                f"Fenómeno desconocido: '{ev.phonetic_phenomenon}'"
            )


# ---------------------------------------------------------------------------
# Tests de Ranking Consistente
# ---------------------------------------------------------------------------

class TestRankingConsistente:
    """Verifica que el ranking del reporte coincida con el orden de posteriors."""

    def test_ranking_ordenado_por_posterior_descendente(self, resultado_seseo, reporte_seseo: ForensicReport) -> None:
        """
        El ranking de dialectos en el reporte forense debe coincidir con
        el orden de probabilidades a posteriori de la inferencia bayesiana.
        """
        # Ranking del reporte: lista de (code, name, prob)
        ranking_reporte = reporte_seseo.dialect_ranking

        # Verificar orden descendente
        for i in range(len(ranking_reporte) - 1):
            prob_actual = ranking_reporte[i][2]
            prob_siguiente = ranking_reporte[i + 1][2]
            assert prob_actual >= prob_siguiente, (
                f"Ranking desordenado: {ranking_reporte[i][0]} (P={prob_actual:.4f}) "
                f"antes de {ranking_reporte[i+1][0]} (P={prob_siguiente:.4f})"
            )

    def test_ganador_del_ranking_coincide_con_prediccion(
        self, resultado_seseo, reporte_seseo: ForensicReport
    ) -> None:
        """El primer dialecto del ranking debe ser el dialecto predicho."""
        codigo_predicho = resultado_seseo.predicted_dialect_code
        codigo_ranking_top = reporte_seseo.dialect_ranking[0][0]
        assert codigo_ranking_top == codigo_predicho, (
            f"Top del ranking ({codigo_ranking_top}) no coincide con "
            f"predicción ({codigo_predicho})"
        )

    def test_confidence_percentage_coherente(self, resultado_seseo, reporte_seseo: ForensicReport) -> None:
        """El porcentaje de confianza del reporte debe coincidir con el posterior del ganador."""
        expected_pct = resultado_seseo.dialect_probabilities[0].posterior_probability * 100.0
        assert abs(reporte_seseo.confidence_percentage - expected_pct) < 0.01, (
            f"Confianza del reporte ({reporte_seseo.confidence_percentage:.4f}%) "
            f"no coincide con posterior*100 ({expected_pct:.4f}%)"
        )
