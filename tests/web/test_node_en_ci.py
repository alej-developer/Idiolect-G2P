"""En CI, las pruebas del dashboard no deben omitirse en silencio por falta de Node."""

from __future__ import annotations

import os
import shutil

import pytest


@pytest.mark.skipif(not os.environ.get("CI"), reason="Solo se exige Node en CI")
def test_node_esta_disponible_en_ci() -> None:
    assert shutil.which("node") is not None, "Sin Node, tests/web se omitiría sin aviso"
