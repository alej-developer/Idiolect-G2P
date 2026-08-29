# Manual Didáctico de Usuario — Idiolect-G2P

**Guía Integral de Instalación, Operación y Casos de Uso Prácticos**  
*Framework de Desambiguación Fonológica Dialectal y Diacrónica Inversa*

---

## 1. Introducción al Framework

**Idiolect-G2P** es una plataforma de lingüística computacional diseñada para resolver la desambiguación fonológica inversa: a partir de un texto en español (especialmente textos poéticos, históricos o periciales), el sistema analiza las restricciones de rima y fonotaxis para deducir probabilísticamente el dialecto del autor ($\hat{D}$) y su vector continuo de isoglosas ($\hat{\boldsymbol{\theta}}$), generando la transcripción en el Alfabeto Fonético Internacional (AFI) y sintetizando el audio acústico correspondiente.

---

## 2. Requisitos e Instalación

### 2.1. Requisitos del Sistema
- **Python:** Versión 3.10 o superior (probado en Python 3.11).
- **Sistema Operativo:** Windows, Linux o macOS.
- **Navegador Web:** Chrome, Firefox, Safari o Edge moderno.

### 2.2. Instalación de Dependencias
Clone el repositorio y cree un entorno virtual:

```bash
git clone https://github.com/alejandro/idiolect-g2p.git
cd idiolect-g2p

# Crear y activar entorno virtual
python -m venv venv
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 3. Ejecución de la Suite de Pruebas

Para validar el funcionamiento completo de todos los módulos fonológicos, métricos, inferenciales, de reportes, seguridad y benchmarking:

```bash
python -m pytest -v tests/
```

Todas las 54 pruebas unitarias e integradas deben concluir con estado `passed`.

---

## 4. Inicio del Servidor y Acceso a la Interfaz Web

Para iniciar el microservicio backend FastAPI y el panel web interactivo:

```bash
uvicorn idiolect_g2p.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Abra su navegador web e ingrese a:
- **Panel Web Científico:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación Interactiva Swagger / OpenAPI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Documentación Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. Guía de Uso del Panel Web por Módulos

### 5.1. Módulo 1: Perfilador Idiolectal Bayesiano
1. Ingrese a la pestaña **Perfilador Idiolectal Bayesiano**.
2. Escriba o pegue el poema o texto de análisis en el cuadro de texto.
3. (Opcional) Seleccione un **Prior Diacrónico** si conoce el siglo aproximado del texto.
4. Haga clic en **Ejecutar Inferencia Bayesiana**.
5. El sistema mostrará:
   - La **Variante Óptima de Máxima Verosimilitud (D̂)**.
   - El **Nivel de Confianza Posterior (%)**.
   - El ranking gráfico de probabilidades dialectales $P(D \mid T, R)$.
   - Las **Evidencias Fonológicas Discriminantes** (por ejemplo, pares que evidencian seseo, lambdacismo o yeísmo).

### 5.2. Módulo 2: Transcriptor G2P & Síntesis Acústica AFI
1. Ingrese a la pestaña **Transcriptor G2P & Síntesis AFI**.
2. Seleccione la variante dialectal deseada (ej. *Caribeño Lambdacista*, *Rioplatense Sheísta*, *Mexicano Central*).
3. Ingrese una oración o palabra en español.
4. Haga clic en **Transcribir a AFI** para ver la segmentación silábica y el acento léxico.
5. Haga clic en **Escuchar Pronunciación** para reproducir la síntesis formántica acústica generada por el motor Web Audio API.

### 5.3. Módulo 3: Escansión Métrica y Rimas
1. Ingrese a la pestaña **Escansión Métrica**.
2. Pegue una o varias estrofas.
3. Pulse **Escanear Métrica y Rimas**.
4. La tabla detallará el número de sílabas gramaticales, sinalefas detectadas, compensación por acento final (+1, 0, -1) y el segmento rimante de cada verso.

### 5.4. Módulo 4: Generador de Informes Multi-Formato
1. Ingrese a la pestaña **Informes Multi-Formato**.
2. Seleccione el formato deseado:
   - **Markdown (.md)**: Documentación reproducible.
   - **LaTeX (.tex)**: Publicaciones académicas con paquetes TIPA y booktabs.
   - **BibTeX (.bib)**: Citas bibliográficas estandarizadas.
   - **TEI-Verse XML (.xml)**: Estándar para Humanidades Digitales.
   - **HTML Interactivo (.html)**: Dictamen imprimible con gráficos SVG.
   - **CSV (.csv)**: Matriz tabular cuantitativa.
   - **JSON (.json)**: Integración interoperable con otras APIs.
   - **Texto Plano (.txt)**: Dictamen pericial formal.
3. Pulse **Generar Vista Previa** y posteriormente **Descargar Archivo**.

### 5.5. Módulo 5: Corpus de Ejemplos Pre-cargados
1. Ingrese a la pestaña **Corpus de Ejemplos**.
2. Explore textos de Sor Juana Inés de la Cruz, Luis de Góngora, Nicolás Guillén, José Hernández y casos periciales de prueba.
3. Pulse **Cargar en Perfilador Bayesiano** para transferir automáticamente el texto y ejecutar el peritaje.

---

## 6. Uso Mediante Código Python

```python
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.reports.report_generator import generate_report, ReportFormat

# 1. Definir texto poético
poema = """
En este dulce abrazo
yo sigo cada paso
unido por el lazo
en este nuevo caso
"""

# 2. Ejecutar inferencia bayesiana
resultado = profile_idiolect_from_poem(poema)
print(f"Dialecto predicho: {resultado.predicted_dialect_name}")
print(f"Confianza: {resultado.confidence_score * 100:.2f}%")
print(f"Tasa estimada de seseo: {resultado.estimated_isogloss_vector['seseo']}")

# 3. Generar dictamen en LaTeX
informe_latex = generate_report(resultado, format_type=ReportFormat.LATEX, case_id="EXP-2026-01")
print(informe_latex[:300])
```

---

## 7. Preguntas Frecuentes y Solución de Problemas

- **¿Por qué un verso agudo suma una sílaba métrica?**  
  Conforme a la regla de paroxitonía del verso hispánico (Quilis, 1993), el acento en la última sílaba genera un tiempo acústico equivalente a una sílaba suplementaria (+1).
- **¿Cómo se calculan las distancias fonéticas?**  
  Se computa la distancia de Levenshtein ponderada sobre la jerarquía de rasgos de Clements y Hume (1995), asignando menores penalizaciones a pares homorgánicos o alófonos que a discrepancias mayores de modo o punto de articulación.
