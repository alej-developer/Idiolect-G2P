"""Pruebas del dashboard: tras un éxito, un fallo no debe dejar datos viejos como vigentes.

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
HARNESS = Path(__file__).with_name("fallo_tras_exito_harness.js")
MSG_ESCANSION = "No se pudo completar el análisis métrico. Inténtalo de nuevo."

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


@pytest.mark.parametrize("escenario", ["http500", "network"])
def test_escansion_exito_y_luego_fallo_retira_la_tabla(escenario: str) -> None:
    r = _ejecutar(escenario)
    assert "Un verso" in r["exito"]["tabla"]
    assert r["exito"]["insignia"] == "1 Versos Analizados"
    assert "Un verso" not in r["tabla"]
    assert MSG_ESCANSION in r["tabla"]
    assert r["insignia"] == "Sin resultado"
    assert r["forma"] == "—" and r["esquema"] == "—"


@pytest.mark.parametrize("escenario", ["http500", "network"])
def test_fallo_de_inferencia_reinicia_el_audio_del_perfilador(escenario: str) -> None:
    audio = _ejecutar(escenario)["audio"]
    assert audio["estado"] == "Listo"
    assert audio["karaoke"] == ""
    assert audio["karaoke_display"] == "none"
    assert "src" in audio["reproductor_removidos"]
    assert audio["reproductor_pausado"] is True
    # Sin manejadores, el evento "pause" del navegador no reescribe la insignia.
    assert audio["manejadores_retirados"] is True


@pytest.mark.parametrize("escenario", ["http500", "network"])
def test_fallo_de_sintesis_muestra_aviso_en_la_insignia(escenario: str) -> None:
    assert _ejecutar(escenario)["estado_sintesis"] == "No se pudo sintetizar el audio"
