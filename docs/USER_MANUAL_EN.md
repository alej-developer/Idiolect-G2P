# Pedagogical User Manual — Idiolect-G2P

**Comprehensive Guide to Installation, Operation, and Practical Use Cases**  
*Framework for Inverse Dialectal and Diachronic Phonological Disambiguation*

---

## 1. Introduction

**Idiolect-G2P** is a computational linguistics platform designed to solve the inverse phonological disambiguation problem: from a text in Spanish (particularly poetic, historical, or forensic corpora), the system examines rhyme and phonotactic constraints to probabilistically infer the author's dialect ($\hat{D}$) and continuous isogloss vector ($\hat{\boldsymbol{\theta}}$), producing International Phonetic Alphabet (IPA) transcriptions and synthesizing corresponding formant acoustic audio.

---

## 2. Requirements & Installation

### 2.1. System Requirements
- **Python:** Version 3.10 or higher (tested on Python 3.11).
- **Operating System:** Windows, Linux, or macOS.
- **Web Browser:** Modern Chrome, Firefox, Safari, or Edge.

### 2.2. Dependency Installation
Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/alejandro/idiolect-g2p.git
cd idiolect-g2p

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Running the Test Suite

To validate the entire system across phonology, metrical scansion, Bayesian inference, report generation, cybersecurity, and performance benchmarks:

```bash
python -m pytest -v tests/
```

All 54 unit and integration tests should complete with a `passed` status.

---

## 4. Launching the Server and Web Dashboard

To launch the FastAPI backend microservice and interactive scientific dashboard:

```bash
uvicorn idiolect_g2p.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
- **Interactive Scientific Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger / OpenAPI Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. Dashboard User Guide

### 5.1. Module 1: Bayesian Idiolect Profiler
1. Select the **Bayesian Idiolect Profiler** tab.
2. Enter or paste the poetic verse into the text area.
3. (Optional) Choose a **Diachronic Prior** century if the historical period is known.
4. Click **Run Bayesian Inference**.
5. The interface will render:
   - The **Maximum Likelihood Dialect (D̂)**.
   - The **Posterior Confidence Level (%)**.
   - The visual ranking of dialectal probabilities $P(D \mid T, R)$.
   - The **Discriminant Phonological Evidence** (e.g. seseo, lambdacism, or yeísmo markers).

### 5.2. Module 2: G2P Transducer & IPA Acoustic Synthesis
1. Select the **G2P Transcriber & IPA Synthesis** tab.
2. Choose the dialectal variety (e.g., *Caribbean Lambdacist*, *Rioplatense Sheísta*, *Central Mexican*).
3. Type a word or sentence in standard Spanish orthography.
4. Click **Transcribe to IPA** to inspect syllabification and prosodic stress.
5. Click **Listen to Pronunciation** to trigger real-time formant acoustic audio playback via the Web Audio API engine.

### 5.3. Module 3: Metrical Scansion & Rhyme Extraction
1. Select the **Metrical Scansion** tab.
2. Paste stanzas into the input box.
3. Click **Scan Meter & Rhymes**.
4. The output table details grammatical syllables, synalephas, stress compensation (+1, 0, -1), and rhyme codas for each verse.

### 5.4. Module 4: Multi-Format Report Generator
1. Select the **Multi-Format Reports** tab.
2. Select your desired output format:
   - **Markdown (.md)**: Reproducible technical documentation.
   - **LaTeX (.tex)**: Academic camera-ready papers with TIPA and booktabs.
   - **BibTeX (.bib)**: Formal bibliographic citation entry.
   - **TEI-Verse XML (.xml)**: Digital Humanities TEI standard.
   - **Interactive HTML (.html)**: Self-contained printable expert report with embedded SVG charts.
   - **CSV (.csv)**: Tabular matrix for statistical analysis in R or Pandas.
   - **JSON (.json)**: Structured interoperable data.
   - **Plain Text (.txt)**: Formal ASCII forensic report.
3. Click **Generate Preview** and then **Download File**.

### 5.5. Module 5: Preloaded Historical Corpus
1. Select the **Corpus Examples** tab.
2. Browse historical works by Sor Juana Inés de la Cruz, Luis de Góngora, Nicolás Guillén, José Hernández, and test forensic cases.
3. Click **Load into Bayesian Profiler** to instantly populate the text and execute the analysis.

---

## 6. Python API Usage

```python
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.reports.report_generator import generate_report, ReportFormat

poem_text = """
En este dulce abrazo
yo sigo cada paso
unido por el lazo
en este nuevo caso
"""

# Run Bayesian profiling
result = profile_idiolect_from_poem(poem_text)
print(f"Predicted dialect: {result.predicted_dialect_name}")
print(f"Confidence score: {result.confidence_score * 100:.2f}%")
print(f"Estimated seseo rate: {result.estimated_isogloss_vector['seseo']}")

# Export LaTeX report
latex_content = generate_report(result, format_type=ReportFormat.LATEX, case_id="CASE-2026-EN")
print(latex_content[:300])
```
