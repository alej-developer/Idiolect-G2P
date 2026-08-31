"""
Pruebas avanzadas de ciberseguridad, traversal, homoglifos unicode y sanitizacion de entradas.
Advanced cybersecurity tests: path traversal, unicode homoglyph/zero-width attacks, and tampering.
"""

import pytest
from starlette.testclient import TestClient
from idiolect_g2p.api.main import app
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.core.syllabifier import syllabify_text
from idiolect_g2p.meter.verse_analyzer import analyze_poem
from idiolect_g2p.reports.report_generator import ReportFormat, generate_report


@pytest.fixture
def client():
    """Fixture del cliente de pruebas HTTP."""
    return TestClient(app)


def test_path_traversal_and_arbitrary_file_access_resistance(client: TestClient) -> None:
    """Verifica que intentos de path traversal no accedan a ficheros del sistema ni filtren rutas."""
    malicious_paths = [
        "../../../../etc/passwd",
        "..\\..\\..\\windows\\win.ini",
        "....//....//....//etc/shadow",
        "..%2F..%2F..%2Fetc%2Fpasswd"
    ]
    for path in malicious_paths:
        # Peticion contra endpoint de dialecto con path malicioso
        res_dialect = client.get(f"/api/v1/dialects?region={path}")
        assert res_dialect.status_code in (200, 404, 422)

        # Peticion contra generador de reportes con formato traversal
        res_report = client.post("/api/v1/generate-report", json={
            "format": path,
            "poem_text": "Caza en la llanura",
            "predicted_dialect_code": "ES_PENINSULAR"
        })
        assert res_report.status_code in (400, 422)


def test_unicode_homoglyphs_and_zero_width_sanitization() -> None:
    """Verifica que homoglifos cirilicos, caracteres invisibles y bytes nulos sean manejados sin fallo."""
    # Mezcla de caracteres latinos con cirilicos visualmente identicos (a -> \u0430, e -> \u0435, o -> \u043e)
    # y caracteres de ancho cero (\u200B, \u200C, \u200D, \uFEFF)
    hostile_unicode = "C\u0430z\u0430 \u200B\u200Cy \uFEFFc\u0430s\u0430 \u202Een el pu\u0435rt\u043e"
    transducer = G2PTransducer()
    results = transducer.transcribe_text(hostile_unicode)
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r.ipa_transcription, str)
        assert isinstance(r.syllabified_ipa, str)

    # Analisis metrico con caracteres invisibles
    poem_analysis = analyze_poem(hostile_unicode)
    assert isinstance(poem_analysis.stanzas, list)
    assert len(poem_analysis.stanzas) >= 1


def test_invalid_json_and_parameter_tampering_rejection(client: TestClient) -> None:
    """Verifica que datos con tipos corruptos o estructuras malformadas sean rechazados con HTTP 422."""
    tampered_payloads = [
        {"text": 12345, "dialect_code": True},
        {"text": None, "generate_audio": "NOT_A_BOOLEAN"},
        {"poem_text": [], "predicted_dialect_code": 9999},
        {"ipa_sequence": {"nested": "value"}, "sample_rate": "invalid_rate"}
    ]
    for payload in tampered_payloads:
        res = client.post("/api/v1/transcribe", json=payload)
        assert res.status_code == 422
        # Verificar que no se filtre informacion de rutas locales o trazas internas en el detalle del error
        assert "Traceback" not in res.text
        assert "C:\\Users\\" not in res.text


def test_report_format_injection_safety() -> None:
    """Verifica que el generador de reportes rechace formatos no soportados sin ejecutar codigo."""
    with pytest.raises((ValueError, KeyError)):
        generate_report(
            format_type=ReportFormat("INVALID_FORMAT_OR_EVAL"),
            poem_text="En tanto que de rosa y azucena",
            analysis_data={"confidence": 0.95}
        )
