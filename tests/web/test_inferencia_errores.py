"""Pruebas del dashboard: un fallo de la API no debe mostrar resultados simulados.

Ejecuta ``idiolect_g2p/web/app.js`` en Node con un DOM mínimo simulado.
Se omiten si Node no está instalado.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

NODE = shutil.which("node")
HARNESS = Path(__file__).with_name("inference_harness.js")
APP_JS = Path(__file__).resolve().parents[2] / "idiolect_g2p" / "web" / "app.js"
MENSAJE_ERROR = "No se pudo completar la inferencia. Inténtalo de nuevo"
VALORES_SIMULADOS = ("Siglo de Oro", "98.4")

pytestmark = pytest.mark.skipif(NODE is None, reason="Node no está disponible")


def _ejecutar(escenario: str) -> dict[str, Any]:
    assert NODE is not None
    proc = subprocess.run(
        [NODE, str(HARNESS), escenario],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    resultado: dict[str, Any] = json.loads(proc.stdout)
    return resultado


def test_la_simulacion_local_ya_no_existe() -> None:
    assert "simularRespuestaLocal" not in APP_JS.read_text(encoding="utf-8")


@pytest.mark.parametrize("escenario", ["http500", "network", "badjson", "emptyranking"])
def test_error_muestra_aviso_y_no_resultados_simulados(escenario: str) -> None:
    r = _ejecutar(escenario)
    assert r["error_texto"] == MENSAJE_ERROR
    assert r["error_oculto"] is False
    for valor in VALORES_SIMULADOS:
        assert valor not in r["nombre"]
        assert valor not in r["confianza"]
        assert valor not in r["afi"]
    # El resultado previo se retira en lugar de dejarse como si fuera vigente.
    assert r["nombre"] != "Resultado previo"
    assert r["confianza"] == "Confianza: —"
    assert r["lista"] == ""
    assert r["afi"] == ""
    # El botón vuelve a estar disponible para reintentar.
    assert r["boton"] == "Inferencia Inversa"


def test_exito_muestra_resultado_real_sin_aviso() -> None:
    r = _ejecutar("ok")
    assert r["nombre"] == "Mexicano Central"
    assert r["confianza"] == "Confianza: 50.0%"
    assert r["error_texto"] == ""
    assert r["error_oculto"] is True
    assert r["boton"] == "Inferencia Inversa"
