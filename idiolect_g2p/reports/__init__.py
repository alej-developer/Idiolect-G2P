"""
Modulo de generacion y exportacion de informes cientificos y de divulgacion.
Scientific and dissemination multi-format report generator module.
"""

from .report_generator import (
    ReportFormat,
    generate_report,
    generate_latex_report,
    generate_tei_xml_report,
    generate_bibtex_entry,
    generate_csv_report,
    generate_html_report,
    generate_markdown_report,
    generate_json_report,
    generate_txt_report,
)

__all__ = [
    "ReportFormat",
    "generate_report",
    "generate_latex_report",
    "generate_tei_xml_report",
    "generate_bibtex_entry",
    "generate_csv_report",
    "generate_html_report",
    "generate_markdown_report",
    "generate_json_report",
    "generate_txt_report",
]
