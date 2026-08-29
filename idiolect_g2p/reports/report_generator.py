"""
Generador de informes periciales, cientificos y de divulgacion en multiples formatos.
Multi-format scientific, forensic, and dissemination report generator.

Soporta:
1. LaTeX (.tex) con paquete TIPA y booktabs.
2. BibTeX (.bib) para citacion academica.
3. TEI-XML (.xml) bajo el estandar TEI-Verse para humanidades digitales.
4. CSV (.csv) para analisis cuantitativo en R/Python.
5. HTML (.html) cientifico autocontenido con graficos SVG y estilos de impresion.
6. Markdown (.md) reproducible.
7. JSON (.json) estructurado e interoperable.
8. Texto Plano (.txt) formal pericial.
"""

from __future__ import annotations
import json
import csv
import io
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..inference.bayesian_profiler import IdiolectProfileResult, DialectProbability
from ..inference.forensic_explainer import generate_forensic_explanation, ForensicReport


class ReportFormat(Enum):
    """Formatos de exportacion cientifica y divulgativa soportados."""
    LATEX = "latex"
    BIBTEX = "bibtex"
    TEI_XML = "tei_xml"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    TXT = "txt"


def generate_latex_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un informe cientifico compilable en LaTeX con paquetes TIPA y booktabs."""
    forensic = generate_forensic_explanation(profile, case_id=case_id)
    top_dp = profile.dialect_probabilities[0]

    rows_latex = []
    for dp in profile.dialect_probabilities[:8]:
        p_pct = dp.posterior_probability * 100.0
        clean_code = dp.dialect_code.replace('_', r'\_')
        rows_latex.append(
            f"{clean_code} & {dp.dialect_name} & {dp.region} & "
            f"{dp.total_phonetic_distance:.3f} & {p_pct:.2f}\\% \\\\"
        )
    table_rows = "\n".join(rows_latex)

    evidences_latex = []
    for ev in forensic.discriminant_evidences:
        evidences_latex.append(
            f"\\item \\textbf{{Versos {ev.verse_1_num} y {ev.verse_2_num}}} ('{ev.word_1}' / '{ev.word_2}'): "
            f"{ev.impact_description}"
        )
    evidences_body = "\n".join(evidences_latex) if evidences_latex else "\\item No se detectaron anomalías métricas conflictivas."
    consonant_expected_str = "Sí" if profile.poem_analysis.is_consonant_expected else "No (Asonante/Libre)"

    return f"""% Informe Cientifico Generado por Idiolect-G2P
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[spanish]{{babel}}
\\usepackage{{amsmath,amssymb}}
\\usepackage{{booktabs}}
\\usepackage{{geometry}}
\\usepackage{{tipa}}
\\usepackage{{hyperref}}
\\geometry{{margin=2.5cm}}

\\title{{\\textbf{{Dictamen Fonol\\'ogico e Inferencia Dialectal Inversa}}\\\\ \\large Caso / Identificador: \\texttt{{{case_id}}}}}
\\author{{Sistema Computacional \\textsc{{Idiolect-G2P}}}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
El presente informe documenta la inferencia bayesiana del idiolecto y la variante dialectal del texto analizado, calculada a partir de las restricciones fonot\\'acticas y los esquemas de rima. La hip\\'otesis fonol\\'ogica de m\\'axima verosimilitud corresponde a \\textbf{{{top_dp.dialect_name}}} con una probabilidad a posteriori del \\textbf{{{forensic.confidence_percentage:.2f}\\%}}.
\\end{{abstract}}

\\section{{Resumen de Par\\'ametros y Resultados}}
\\begin{{itemize}}
    \\item \\textbf{{Variante Inferida ($\\hat{{D}}$):}} {top_dp.dialect_name} ({top_dp.region})
    \\item \\textbf{{Nivel de Confianza:}} {forensic.confidence_percentage:.2f}\\%
    \\item \\textbf{{Molde Estr\\'ofico Detectado:}} {profile.poem_analysis.detected_stanza_type.value}
    \\item \\textbf{{Rima Consonante Esperada:}} {consonant_expected_str}
\\end{{itemize}}

\\section{{Distribuci\\'on Posterior de Probabilidad Dialectal}}
A continuaci\\'on se detalla la verosimilitud fonol\\'ogica calculada sobre el espacio de hip\\'otesis:

\\begin{{table}}[h!]
\\centering
\\small
\\begin{{tabular}}{{lllrr}}
\\toprule
\\textbf{{C\\'odigo}} & \\textbf{{Variante Dialectal}} & \\textbf{{Macrorregi\\'on}} & \\textbf{{Dist. Fon.}} & \\textbf{{$P(D \\mid T, R)$}} \\\\
\\midrule
{table_rows}
\\bottomrule
\\end{{tabular}}
\\caption{{Evaluaci\\'on probabil\\'istica de macro-dialectos bajo la geometr\\'ia de rasgos de Clements \\& Hume.}}
\\end{{table}}

\\section{{Evidencias Fonol\\'ogicas Discriminantes}}
\\begin{{itemize}}
{evidences_body}
\\end{{itemize}}

\\section{{Conclusi\\'on Socioling\\\"u\\'istica Forense}}
{forensic.sociolinguistic_conclusion}

\\end{{document}}
"""


def generate_bibtex_entry(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera una ficha BibTeX formal con metadatos del analisis."""
    top_dp = profile.dialect_probabilities[0]
    year = datetime.now().year
    clean_id = case_id.lower().replace('-', '_')
    pct = top_dp.posterior_probability * 100.0
    return f"""@misc{{{clean_id}_{year},
  author       = {{Idiolect-G2P Computational Linguistics System}},
  title        = {{Phonological Disambiguation and Dialectal Inference Report: {case_id}}},
  year         = {{{year}}},
  howpublished = {{Software and Expert Analysis Report}},
  note         = {{Predicted Dialect: {top_dp.dialect_name} ({top_dp.dialect_code}), Confidence: {pct:.2f}\\%}},
  url          = {{https://github.com/alejandro/idiolect-g2p}}
}}
"""


def generate_tei_xml_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un archivo TEI-Verse XML interoperable para humanidades digitales."""
    top_dp = profile.dialect_probabilities[0]

    stanzas_xml = []
    for s in profile.poem_analysis.stanzas:
        verses_xml = []
        for v in s.verses:
            verses_xml.append(
                f'        <l n="{v.verse_number}" met="{v.metrical_syllables_count}" rhyme="{v.rhyme_segment_orthographic}">{v.raw_text}</l>'
            )
        v_body = "\n".join(verses_xml)
        stanzas_xml.append(
            f'      <lg n="{s.stanza_number}" type="{s.stanza_type.name}" rhymeScheme="{s.rhyme_pattern}">\n{v_body}\n      </lg>'
        )
    poem_body = "\n".join(stanzas_xml)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Analisis Metrico y Transduccion Fonologica: {case_id}</title>
        <author>Idiolect-G2P</author>
      </titleStmt>
      <publicationStmt>
        <p>Generado automaticamente por Idiolect-G2P Framework</p>
      </publicationStmt>
      <sourceDesc>
        <p>Inferencia dialectal sobre texto poetico</p>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage>
        <language ident="es" dialect="{top_dp.dialect_code}">{top_dp.dialect_name}</language>
      </langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="poem" subtype="{profile.poem_analysis.detected_stanza_type.name}">
{poem_body}
      </div>
    </body>
  </text>
</TEI>
"""


def generate_csv_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera una matriz tabular CSV para analisis estadistico en R o Pandas."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "case_id",
        "dialect_code",
        "dialect_name",
        "region",
        "posterior_probability",
        "log_likelihood",
        "total_phonetic_distance",
        "perfect_rhymes_count",
        "total_evaluated_pairs"
    ])

    for dp in profile.dialect_probabilities:
        writer.writerow([
            case_id,
            dp.dialect_code,
            dp.dialect_name,
            dp.region,
            f"{dp.posterior_probability:.6f}",
            f"{dp.log_likelihood:.4f}",
            f"{dp.total_phonetic_distance:.4f}",
            dp.perfect_rhymes_count,
            dp.total_evaluated_pairs
        ])

    return output.getvalue()


def generate_html_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un informe HTML interactivo y reproducible con estilos formales de impresion."""
    forensic = generate_forensic_explanation(profile, case_id=case_id)
    top_dp = profile.dialect_probabilities[0]

    svg_bars = []
    y_pos = 20
    for dp in profile.dialect_probabilities[:6]:
        pct = dp.posterior_probability * 100.0
        bar_width = int(pct * 3.5)
        d_name_sub = dp.dialect_name[:24]
        svg_bars.append(
            f'<text x="10" y="{y_pos + 12}" font-family="sans-serif" font-size="12" fill="#2d3748">{d_name_sub}</text>'
            f'<rect x="220" y="{y_pos}" width="{max(2, bar_width)}" height="16" fill="#2b6cb0" rx="3" />'
            f'<text x="{230 + max(2, bar_width)}" y="{y_pos + 12}" font-family="sans-serif" font-size="11" fill="#4a5568">{pct:.2f}%</text>'
        )
        y_pos += 26
    svg_chart = f'<svg width="100%" height="{y_pos + 10}" viewBox="0 0 650 {y_pos + 10}">\n' + "\n".join(svg_bars) + "\n</svg>"

    table_rows = []
    for dp in profile.dialect_probabilities:
        pct = dp.posterior_probability * 100.0
        table_rows.append(
            f"<tr>"
            f"<td><code>{dp.dialect_code}</code></td>"
            f"<td><strong>{dp.dialect_name}</strong></td>"
            f"<td>{dp.region}</td>"
            f"<td>{dp.total_phonetic_distance:.3f}</td>"
            f"<td><strong>{pct:.2f}%</strong></td>"
            f"</tr>"
        )
    rows_html = "\n".join(table_rows)

    evidences_html = []
    for ev in forensic.discriminant_evidences:
        evidences_html.append(
            f'<li class="evidence-item">'
            f'<strong>Versos {ev.verse_1_num} y {ev.verse_2_num}</strong> (<em>{ev.word_1}</em> / <em>{ev.word_2}</em>)<br/>'
            f'<span class="badge">{ev.phonetic_phenomenon}</span><br/>'
            f'<p>{ev.impact_description}</p>'
            f'</li>'
        )
    ev_html = "\n".join(evidences_html) if evidences_html else "<li>No se observaron divergencias anómalas.</li>"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Dictamen Pericial Fonológico - {case_id}</title>
    <style>
        body {{ font-family: 'Times New Roman', Times, serif; color: #1a202c; line-height: 1.6; max-width: 850px; margin: 40px auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2d3748; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
        .header-box {{ background: #f7fafc; border: 1px solid #cbd5e0; padding: 20px; border-radius: 6px; margin-bottom: 25px; }}
        .badge {{ display: inline-block; background: #edf2f7; color: #2b6cb0; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; margin: 4px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #cbd5e0; padding: 8px 12px; text-align: left; font-size: 0.95em; }}
        th {{ background: #edf2f7; }}
        .chart-box {{ background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .evidence-item {{ margin-bottom: 15px; }}
        @media print {{
            body {{ max-width: 100%; margin: 0; padding: 15mm; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header-box">
        <h1>Dictamen Pericial de Lingüística Forense y Fonética</h1>
        <p><strong>Identificador de Análisis:</strong> <code>{case_id}</code> | <strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Variante Dialectal Inferida:</strong> <span class="badge" style="font-size: 1.1em; background: #ebf8ff;">{top_dp.dialect_name}</span></p>
        <p><strong>Nivel de Confianza Posterior:</strong> <strong>{forensic.confidence_percentage:.2f}%</strong></p>
        <p><strong>Estructura Métrica:</strong> {profile.poem_analysis.detected_stanza_type.value}</p>
    </div>

    <h2>1. Distribución Posterior de Probabilidades Dialectales P(D | T, R)</h2>
    <div class="chart-box">
        {svg_chart}
    </div>

    <table>
        <thead>
            <tr>
                <th>Código</th>
                <th>Variante Dialectal</th>
                <th>Región</th>
                <th>Distancia Fonética</th>
                <th>Probabilidad</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <h2>2. Evidencias Fonológicas y Rimas Discriminantes</h2>
    <ul>
        {ev_html}
    </ul>

    <h2>3. Dictamen y Conclusiones Sociolingüísticas</h2>
    <p>{forensic.sociolinguistic_conclusion}</p>

    <hr style="margin-top: 40px;"/>
    <p style="font-size: 0.85em; color: #718096; text-align: center;">Generado por Idiolect-G2P — Framework de Desambiguación Fonológica Dialectal y Diacrónica Inversa.</p>
</body>
</html>
"""


def generate_markdown_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un informe en formato Markdown estructurado."""
    forensic = generate_forensic_explanation(profile, case_id=case_id)
    top_dp = profile.dialect_probabilities[0]

    table_rows = []
    for dp in profile.dialect_probabilities:
        pct = dp.posterior_probability * 100.0
        table_rows.append(
            f"| `{dp.dialect_code}` | **{dp.dialect_name}** | {dp.region} | {dp.total_phonetic_distance:.3f} | **{pct:.2f}%** |"
        )
    md_table = "\n".join(table_rows)

    evidences_md = []
    for ev in forensic.discriminant_evidences:
        evidences_md.append(
            f"- **Versos {ev.verse_1_num} y {ev.verse_2_num}** (`{ev.word_1}` / `{ev.word_2}`):\n"
            f"  - *Fenómeno:* {ev.phonetic_phenomenon}\n"
            f"  - *Impacto:* {ev.impact_description}"
        )
    ev_md = "\n".join(evidences_md) if evidences_md else "- No se detectaron rimas divergentes o anómalas."

    return f"""# Dictamen Fonológico e Inferencia Dialectal Inversa

**Identificador de Caso:** `{case_id}`  
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Software:** Idiolect-G2P Framework v1.0.0  

---

## 1. Resumen Ejecutivo
- **Variante Óptima Inferida (\\hat{{D}}):** {top_dp.dialect_name} ({top_dp.region})
- **Nivel de Confianza Posterior:** {forensic.confidence_percentage:.2f}%
- **Régimen Estrófico:** {profile.poem_analysis.detected_stanza_type.value}
- **Esquema de Rima Global:** `{profile.poem_analysis.global_rhyme_scheme}`

---

## 2. Matriz de Probabilidades Dialectales P(D | T, R)

| Código | Variante Dialectal | Región | Distancia Fonética | Probabilidad |
| :--- | :--- | :--- | :--- | :--- |
{md_table}

---

## 3. Evidencias Fonológicas Discriminantes
{ev_md}

---

## 4. Conclusión Sociolingüística y Pericial
{forensic.sociolinguistic_conclusion}
"""


def generate_json_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un informe completo estructurado en formato JSON."""
    forensic = generate_forensic_explanation(profile, case_id=case_id)

    data = {
        "case_id": case_id,
        "timestamp": datetime.now().isoformat(),
        "predicted_dialect": {
            "code": profile.predicted_dialect_code,
            "name": profile.predicted_dialect_name,
            "confidence_score": profile.confidence_score,
        },
        "isogloss_vector": profile.estimated_isogloss_vector,
        "poem_analysis": {
            "stanza_type": profile.poem_analysis.detected_stanza_type.name,
            "rhyme_scheme": profile.poem_analysis.global_rhyme_scheme,
            "is_consonant_expected": profile.poem_analysis.is_consonant_expected,
            "total_verses": len(profile.poem_analysis.all_verses),
        },
        "dialect_probabilities": [
            {
                "code": dp.dialect_code,
                "name": dp.dialect_name,
                "region": dp.region,
                "posterior_probability": dp.posterior_probability,
                "log_likelihood": dp.log_likelihood,
                "total_phonetic_distance": dp.total_phonetic_distance,
                "perfect_rhymes_count": dp.perfect_rhymes_count,
            }
            for dp in profile.dialect_probabilities
        ],
        "discriminant_evidences": [
            {
                "verse_1": ev.verse_1_num,
                "verse_2": ev.verse_2_num,
                "word_1": ev.word_1,
                "word_2": ev.word_2,
                "phenomenon": ev.phonetic_phenomenon,
                "description": ev.impact_description,
                "power": ev.discriminating_power,
            }
            for ev in forensic.discriminant_evidences
        ],
        "sociolinguistic_conclusion": forensic.sociolinguistic_conclusion,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_txt_report(
    profile: IdiolectProfileResult,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Genera un dictamen formal en texto plano con tablas ASCII."""
    forensic = generate_forensic_explanation(profile, case_id=case_id)
    top_dp = profile.dialect_probabilities[0]

    lines = [
        "=" * 78,
        f"DICTAMEN DE LINGUISTICA FORENSE Y PERFILACION IDIOLECTAL",
        f"Identificador: {case_id}  |  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 78,
        "",
        f"1. RESULTADO PRINCIPAL:",
        f"   Variante Predicha: {top_dp.dialect_name} ({top_dp.dialect_code})",
        f"   Macrorregion:      {top_dp.region}",
        f"   Nivel de Confianza: {forensic.confidence_percentage:.2f}%",
        f"   Regimen Estrofico: {profile.poem_analysis.detected_stanza_type.value}",
        "",
        f"2. RANKING DE PROBABILIDAD DIALECTAL:",
        f"   {'-'*70}",
        f"   {'CODIGO':<22} | {'VARIANTE':<28} | {'PROB':<10}",
        f"   {'-'*70}",
    ]

    for dp in profile.dialect_probabilities[:8]:
        p_pct = f"{dp.posterior_probability * 100.0:.2f}%"
        d_name_sub = dp.dialect_name[:28]
        lines.append(f"   {dp.dialect_code:<22} | {d_name_sub:<28} | {p_pct:<10}")

    lines.extend([
        f"   {'-'*70}",
        "",
        f"3. EVIDENCIAS DISCRIMINANTES:",
    ])

    if forensic.discriminant_evidences:
        for idx, ev in enumerate(forensic.discriminant_evidences, start=1):
            lines.append(f"   [{idx}] Versos {ev.verse_1_num} y {ev.verse_2_num} ('{ev.word_1}' / '{ev.word_2}')")
            lines.append(f"       Fenomeno: {ev.phonetic_phenomenon}")
            lines.append(f"       Impacto:  {ev.impact_description}")
    else:
        lines.append("   No se detectaron rimas anomalas.")

    lines.extend([
        "",
        f"4. CONCLUSION PERICIAL:",
        f"   {forensic.sociolinguistic_conclusion}",
        "=" * 78,
    ])

    return "\n".join(lines)


def generate_report(
    profile: IdiolectProfileResult,
    format_type: ReportFormat = ReportFormat.MARKDOWN,
    case_id: str = "CASE-G2P-001"
) -> str:
    """Punto de entrada unificado para generar el informe en el formato solicitado."""
    if format_type == ReportFormat.LATEX:
        return generate_latex_report(profile, case_id=case_id)
    elif format_type == ReportFormat.BIBTEX:
        return generate_bibtex_entry(profile, case_id=case_id)
    elif format_type == ReportFormat.TEI_XML:
        return generate_tei_xml_report(profile, case_id=case_id)
    elif format_type == ReportFormat.CSV:
        return generate_csv_report(profile, case_id=case_id)
    elif format_type == ReportFormat.HTML:
        return generate_html_report(profile, case_id=case_id)
    elif format_type == ReportFormat.JSON:
        return generate_json_report(profile, case_id=case_id)
    elif format_type == ReportFormat.TXT:
        return generate_txt_report(profile, case_id=case_id)
    else:
        return generate_markdown_report(profile, case_id=case_id)
