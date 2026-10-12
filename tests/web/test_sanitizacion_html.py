"""Pruebas del dashboard: el texto del API o del usuario no debe interpretarse como HTML.

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
HARNESS = Path(__file__).with_name("sanitizacion_harness.js")
ESCAPADO = "&lt;img src=x onerror=alert(1)&gt;"

pytestmark = pytest.mark.skipif(NODE is None, reason="Node no está disponible")


@pytest.fixture(scope="module")
def html() -> dict[str, Any]:
    assert NODE is not None
    proc = subprocess.run(
        [NODE, str(HARNESS)], capture_output=True, text=True, timeout=30, check=True
    )
    resultado: dict[str, Any] = json.loads(proc.stdout)
    return resultado


@pytest.mark.parametrize("panel", ["ranking", "maxent", "junturas", "escansion"])
def test_el_texto_hostil_se_escapa(html: dict[str, Any], panel: str) -> None:
    contenido = html[panel]
    assert ESCAPADO in contenido
    assert "<img" not in contenido
