"""Pruebas del dashboard: un fallo de transcripción no debe mostrar IPA inventada.

Ejecuta ``idiolect_g2p/web/app.js`` en Node con un DOM mínimo simulado.
Se omiten si Node no está instalado.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

NODE = shutil.which("node")
HARNESS = Path(__file__).with_name("transcripcion_harness.js")
WEB = Path(__file__).resolve().parents[2] / "idiolect_g2p" / "web"
MSG_AFI = "No se pudo obtener la transcripción AFI. Inténtalo de nuevo."
MSG_G2P = "No se pudo completar la transcripción. Inténtalo de nuevo."
IPA_FIJA = ("mjen.tɾas", "ka.θa.ˈðo.ɾes")

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


def test_no_quedan_transcripciones_ipa_fijas_en_el_codigo() -> None:
    for archivo in ("app.js", "index.html"):
        texto = (WEB / archivo).read_text(encoding="utf-8")
        for fija in IPA_FIJA:
            assert fija not in texto, f"{fija} sigue en {archivo}"


def test_html_inicial_sin_resultados_inventados() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "Confianza: 98.4%" not in html
    assert not re.search(r"1\. Español del Siglo de Oro", html)


@pytest.mark.parametrize("escenario", ["http500", "network"])
def test_fallo_muestra_aviso_y_retira_el_resultado_previo(escenario: str) -> None:
    r = _ejecutar(escenario)
    assert r["afi"] == MSG_AFI
    assert r["g2p"] == MSG_G2P
    for fija in IPA_FIJA:
        assert fija not in r["afi"] and fija not in r["g2p"]
    assert r["juntura_display"] == "none"


def test_exito_muestra_la_transcripcion_real() -> None:
    r = _ejecutar("ok")
    assert r["afi"] == "/a.ki/"
    assert r["g2p"] == "/a.ki/"
