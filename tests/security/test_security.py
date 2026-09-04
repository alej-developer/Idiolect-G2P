"""
Pruebas de ciberseguridad, inyeccion, ReDoS y mitigacion de ataques.
Cybersecurity, injection resistance, ReDoS, and attack mitigation tests.
"""

import pytest
from fastapi.testclient import TestClient
from idiolect_g2p.api.main import app
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.core.syllabifier import syllabify_text
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem


@pytest.fixture
def client():
    return TestClient(app)


def test_xss_and_html_injection_resilience() -> None:
    """Verifica que entradas con vectores XSS y etiquetas HTML no rompan el transductor."""
    malicious_input = "<script>alert('XSS')</script><b>Hola</b> <!-- comment -->"
    transducer = G2PTransducer()
    results = transducer.transcribe_text(malicious_input)
    assert isinstance(results, list)
    # Ninguna ejecucion o fallo por inyeccion
    for r in results:
        assert isinstance(r.syllabified_ipa, str)


def test_sql_and_command_injection_resilience() -> None:
    """Verifica resistencia frente a patrones clasicos de SQLi y command injection."""
    malicious_sql = "' OR 1=1; DROP TABLE dialects; --; $(whoami); `id`"
    pwords = syllabify_text(malicious_sql)
    assert isinstance(pwords, list)

    # Inferencia bayesiana sobre texto hostil
    profile = profile_idiolect_from_poem(malicious_sql)
    assert profile.predicted_dialect_code is not None


def test_redos_catastrophic_backtracking_protection() -> None:
    """Verifica que cadenas patologicas no provoquen congelamiento por ReDoS."""
    # Cadena con repeticiones extremas para evaluar backtracking de expresiones regulares
    pathological_string = "a" * 2000 + "!" + "b" * 2000 + "?"
    transducer = G2PTransducer()
    results = transducer.transcribe_text(pathological_string)
    assert len(results) >= 1


def test_payload_size_limit_enforcement(client: TestClient) -> None:
    """Verifica el rechazo HTTP 413 cuando el payload supera el limite estricto de 2 MB."""
    giant_payload = {"text": "A" * (2 * 1024 * 1024 + 100)}
    response = client.post("/api/v1/transcribe", json=giant_payload)
    assert response.status_code == 413
    assert "supera el limite" in response.json()["detail"]


def test_security_headers_enforcement(client: TestClient) -> None:
    """Verifica que las cabeceras HTTP de seguridad esten estrictamente configuradas."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "default-src 'self'" in headers["Content-Security-Policy"]
