"""
Pruebas unitarias para el generador de informes multi-formato.
Unit tests for the multi-format report generator.
"""

import json
import pytest
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.reports.report_generator import (
    ReportFormat,
    generate_report,
    generate_latex_report,
    generate_bibtex_entry,
    generate_tei_xml_report,
    generate_csv_report,
    generate_html_report,
    generate_markdown_report,
    generate_json_report,
    generate_txt_report,
)


@pytest.fixture
def sample_profile():
    """Genera un perfil de prueba a partir de un poema seseante."""
    poem = """
    En este dulce abrazo
    yo sigo cada paso
    unido por el lazo
    en este nuevo caso
    """
    return profile_idiolect_from_poem(poem)


def test_latex_report_generation(sample_profile) -> None:
    """Verifica generacion de documento LaTeX compilable."""
    latex_doc = generate_latex_report(sample_profile, case_id="CASE-TEST-01")
    assert "\\documentclass" in latex_doc
    assert "\\begin{document}" in latex_doc
    assert "\\end{document}" in latex_doc
    assert "CASE-TEST-01" in latex_doc
    assert "booktabs" in latex_doc


def test_bibtex_entry_generation(sample_profile) -> None:
    """Verifica generacion de ficha BibTeX."""
    bibtex_entry = generate_bibtex_entry(sample_profile, case_id="CASE-TEST-01")
    assert "@misc{" in bibtex_entry
    assert "Idiolect-G2P" in bibtex_entry


def test_tei_xml_generation(sample_profile) -> None:
    """Verifica generacion de archivo TEI-Verse XML."""
    xml_doc = generate_tei_xml_report(sample_profile, case_id="CASE-TEST-01")
    assert "<?xml" in xml_doc
    assert "<TEI" in xml_doc
    assert "</TEI>" in xml_doc
    assert "<lg" in xml_doc
    assert "<l n=" in xml_doc


def test_csv_report_generation(sample_profile) -> None:
    """Verifica generacion de tabla CSV cuantitativa."""
    csv_doc = generate_csv_report(sample_profile, case_id="CASE-TEST-01")
    lines = csv_doc.strip().splitlines()
    assert len(lines) >= 15
    assert "case_id,dialect_code,dialect_name" in lines[0]


def test_html_report_generation(sample_profile) -> None:
    """Verifica generacion de informe HTML con SVG embebido."""
    html_doc = generate_html_report(sample_profile, case_id="CASE-TEST-01")
    assert "<!DOCTYPE html>" in html_doc
    assert "<svg" in html_doc
    assert "<table>" in html_doc
    assert "@media print" in html_doc


def test_markdown_and_json_generation(sample_profile) -> None:
    """Verifica generacion de formatos Markdown y JSON estructurado."""
    md_doc = generate_markdown_report(sample_profile, case_id="CASE-TEST-01")
    assert "# Dictamen Fonológico" in md_doc

    json_doc = generate_json_report(sample_profile, case_id="CASE-TEST-01")
    data = json.loads(json_doc)
    assert data["case_id"] == "CASE-TEST-01"
    assert "predicted_dialect" in data
    assert "dialect_probabilities" in data


def test_unified_generate_report_dispatcher(sample_profile) -> None:
    """Verifica el despachador unificado generate_report."""
    for fmt in ReportFormat:
        res = generate_report(sample_profile, format_type=fmt, case_id="DISPATCHER-TEST")
        assert len(res) > 50
