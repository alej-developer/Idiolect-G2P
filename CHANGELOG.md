# Registro de Cambios e Historial de Versiones (CHANGELOG)

Todas las modificaciones notables realizadas en el proyecto **Idiolect-G2P** serán documentadas cronológicamente en este archivo.
El formato se fundamenta en las directrices de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y se adhiere a las directrices de [Versionado Semántico](https://semver.org/lang/es/).

---

## [1.2.0] - 2026-09-04

### Correcciones de Compatibilidad y Estabilidad
- **Eliminación de Deprecaciones de Starlette**: Migración del import `starlette.testclient.TestClient` al módulo canónico `fastapi.testclient.TestClient` en los módulos de pruebas de ciberseguridad (`test_advanced_security.py`, `test_security.py`), eliminando la advertencia `StarletteDeprecationWarning`.
- **Actualización del Código de Estado HTTP 413**: Transición del identificador obsoleto `HTTP_413_REQUEST_ENTITY_TOO_LARGE` al estándar vigente `HTTP_413_CONTENT_TOO_LARGE` conforme a la especificación HTTP actualizada en `idiolect_g2p/api/main.py`.
- **Corrección de Import Faltante**: Incorporación del tipo `Optional` al módulo de rutas `idiolect_g2p/api/routes.py`, resolviendo un `NameError` latente en la ruta de transcripción con síntesis de audio deshabilitada.

### Infraestructura de Integración Continua
- **Pipeline CI/CD Matricial**: Creación del flujo de trabajo `.github/workflows/ci.yml` con ejecución automatizada de la suite de pruebas sobre una matriz de Python 3.10, 3.11 y 3.12 en Ubuntu, incluyendo reporte de cobertura de código mediante `pytest-cov` y verificación de integridad de importaciones del paquete.

### Gobernanza de Tipado y Empaquetado
- **Marcador PEP 561**: Creación del archivo `idiolect_g2p/py.typed` para que verificadores de tipos estáticos (mypy, pyright) reconozcan el paquete como completamente tipado.
- **Sincronización de Versión 1.2.0**: Actualización coherente del número de versión en `idiolect_g2p/__init__.py`, `pyproject.toml`, la instancia `FastAPI` y el endpoint `/health`.

### Documentación y Metadatos
- **Actualización de Insignias Dinámicas**: Corrección del badge de tests en `README.md` de 69/69 a **147/147 tests aprobados (100%)**, reflejando la cobertura real del proyecto incluyendo las 7 dimensiones de auditoría de IA.
- **Actualización de BibTeX**: Versión de citación científica actualizada a 1.2.0.
- **Ampliación de `.gitignore`**: Incorporación de patrones para notebooks Jupyter (`.ipynb_checkpoints`), artefactos de sistema operativo (`Thumbs.db`, `Desktop.ini`) y variables de entorno locales.

---

## [1.1.0] - 2026-09-02

### Infraestructura y Operaciones DevOps
- **Flujo de Trabajo de Automatización de Proyectos**: Se crea el archivo `.github/workflows/project-automation.yml` para vincular automáticamente incidencias (Issues) y solicitudes de extracción (Pull Requests) al tablero de GitHub Projects del usuario.
- **Gestión Automatizada de Estados**: Configurada la incorporación inmediata de tarjetas en eventos de apertura (`opened`) y la transición automática hacia la columna de completado (`Done`) ante cierres de incidencias o fusiones de solicitudes de extracción (`closed`).
- **Gobernanza de Ciberseguridad y Credenciales**:
  - Implementación del principio de mínimo privilegio en el bloque de permisos (`permissions: issues: write, pull-requests: write, contents: read`).
  - Prohibición absoluta de exposición de credenciales en el código fuente y empleo exclusivo de secretos cifrados del repositorio mediante `${{ secrets.PROJECT_PAT }}`.
- **Estructuración y Población del Tablero de Proyectos**:
  - Creación y cierre de 10 incidencias históricas representativas del backend fonológico, seguridad de API y síntesis acústica (Issues #1 a #10).
  - Publicación de 5 incidencias estratégicas de roadmap futuro orientadas a optimización concurrente, dialectología de contacto y estilometría forense (Issues #11 a #15).
  - Creación del documento `PROJECT_DESCRIPTION.md` optimizado para SEO para la presentación pública del tablero.


---

## [1.0.0] - 2026-09-02

### Gobernanza y Publicación Científica
- **Identidad Académica**: Creación de `CITATION.cff` (v1.2.0) con metadatos formales para citación bibliográfica en BibTeX y gestores documentales.
- **Licencia de Código Abierto**: Incorporación formal del archivo `LICENSE` bajo los términos de la Licencia MIT.
- **Protocolos Comunitarios**: Creación de la guía de contribución `CONTRIBUTING.md` y el código de conducta `CODE_OF_CONDUCT.md` adaptado del Contributor Covenant v2.1.
- **Revisión por Pares**: Incorporación de plantillas de incidencias (`bug_report.md`, `feature_dialect.md`) y plantilla de solicitud de extracción (`PULL_REQUEST_TEMPLATE.md`).
- **Documentación Académica**: Actualización simétrica bilingüe en `docs/SCIENTIFIC_PAPER_ES.md` y `docs/SCIENTIFIC_PAPER_EN.md` con normativas APA 7.ª edición.
- **Portal Principal**: Actualización del archivo `README.md` con insignias dinámicas de estado, diagrama arquitectónico con componentes estocásticos y fragmento BibTeX.

### Fonología Computacional y Modelado Lingüístico
- **Motor de Sandhi Externo**: Implementación de reencadenamiento silábico interpalabra y asimilaciones de sonoridad y homorganicidad nasal en `idiolect_g2p/core/sandhi.py`.
- **Gramática de Máxima Entropía (MaxEnt)**: Integración del evaluador armónico estocástico continuo en `idiolect_g2p/inference/maxent_grammar.py`.
- **Inferencia Bayesiana Híbrida**: Ponderación conjunta de la geometría de rasgos de Clements y Hume con la penalización armónica MaxEnt en `idiolect_g2p/inference/bayesian_profiler.py`.
- **Interfaz Web Interactiva**: Controles de sandhi post-léxico y tablero dinámico de pesos MaxEnt en el panel de control del Scriptorium.
