"""
Pruebas de integracion para la API REST FastAPI y cabeceras de seguridad.
Integration tests for FastAPI REST API and security headers.
"""

import pytest
from starlette.testclient import TestClient
from idiolect_g2p.api.main import app


@pytest.fixture
def client():
    """Cliente de pruebas para la aplicacion FastAPI."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Verifica el endpoint de salud."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Idiolect-G2P"


def test_security_headers_present(client: TestClient) -> None:
    """Verifica que las cabeceras HTTP de seguridad esten presentes en todas las respuestas."""
    response = client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in response.headers


def test_list_dialects_endpoint(client: TestClient) -> None:
    """Verifica la obtencion del catalogo completo de dialectos."""
    response = client.get("/api/v1/dialects")
    assert response.status_code == 200
    dialects = response.json()
    assert len(dialects) >= 15
    codes = [d["code"] for d in dialects]
    assert "ES_PENINSULAR" in codes
    assert "MX_CENTRAL" in codes
    assert "CARIBBEAN_STD" in codes
    assert "RIOPLATENSE_SHEIST" in codes


def test_transcribe_endpoint(client: TestClient) -> None:
    """Verifica la transcripcion fonetica G2P a traves de la API."""
    payload = {
        "text": "caza y casa",
        "dialect_code": "ES_PENINSULAR",
        "generate_audio": True
    }
    response = client.post("/api/v1/transcribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_words"] == 3
    assert "audio_base64" in data
    assert data["audio_base64"] is not None
    assert "word_timings" in data
    assert data["word_timings"] is not None
    assert data["word_timings"][0]["start_time"] >= 0.0
    assert data["word_timings"][0]["end_time"] > data["word_timings"][0]["start_time"]


def test_transcribe_endpoint_with_sandhi(client: TestClient) -> None:

    """Verifica que el endpoint /transcribe reporte sandhi y sus junturas."""
    payload = {
        "text": "los mismos",
        "dialect_code": "ES_PENINSULAR",
        "apply_sandhi": True
    }
    response = client.post("/api/v1/transcribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sandhi_applied"] is True
    assert len(data["sandhi_junctures"]) >= 1
    assert data["sandhi_junctures"][0]["output_phoneme"] == "z"



def test_syllabify_endpoint(client: TestClient) -> None:
    """Verifica la silabificacion ortografica y fonotactica."""
    response = client.post("/api/v1/syllabify", json={"text": "transcripcion computacional"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["words"]) == 2
    assert "syllables" in data["words"][0]



def test_synthesize_ipa_endpoint(client: TestClient) -> None:
    """Verifica la sintesis de audio a partir de cadena AFI."""
    payload = {
        "ipa_sequence": "ˈka.sa",
        "sample_rate": 22050
    }
    response = client.post("/api/v1/synthesize-ipa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["duration_seconds"] > 0.0
    assert len(data["audio_base64_wav"]) > 100


def test_analyze_poem_endpoint(client: TestClient) -> None:
    """Verifica el analisis metrico de un poema."""
    poem = """
    Hombres necios que acusáis
    a la mujer sin razón,
    sin ver que sois la ocasión
    de lo mismo que culpáis
    """
    response = client.post("/api/v1/analyze-poem", json={"poem_text": poem})
    assert response.status_code == 200
    data = response.json()
    assert data["total_verses"] == 4
    assert data["is_consonant_expected"] is True


def test_profile_idiolect_endpoint(client: TestClient) -> None:
    """Verifica el analisis pericial forense con restricciones MaxEnt."""
    sonnet_sample = """
    En este dulce abrazo
    yo sigo cada paso
    unido por el lazo
    en este nuevo caso
    """
    payload = {
        "text": sonnet_sample,
        "century_prior": 17,
        "case_identifier": "TEST-API-CASE"
    }
    response = client.post("/api/v1/profile-idiolect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["case_identifier"] == "TEST-API-CASE"
    assert data["confidence_score"] > 0.0
    assert len(data["dialect_ranking"]) > 0
    assert len(data["discriminant_evidences"]) >= 1
    assert len(data["maxent_constraints"]) >= 5


def test_generate_report_endpoint(client: TestClient) -> None:
    """Verifica la generacion de informes en multiples formatos."""
    poem = """
    En este dulce abrazo
    yo sigo cada paso
    unido por el lazo
    en este nuevo caso
    """
    for fmt in ["markdown", "latex", "tei_xml", "csv", "html", "json", "txt"]:
        payload = {
            "text": poem,
            "format_type": fmt,
            "case_identifier": f"REPORT-{fmt.upper()}"
        }
        response = client.post("/api/v1/generate-report", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["format_type"] == fmt
        assert len(data["content"]) > 50


def test_web_index_served(client: TestClient) -> None:
    """Verifica que la aplicacion web principal sea servida correctamente."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Idiolect-G2P" in response.text
    assert "tab-profiler" in response.text

