# Guía de Contribución Científica / Scientific Contribution Guidelines

¡Gracias por su interés en contribuir a **Idiolect-G2P**! Este proyecto se rige por principios de **rigor científico, reproducibilidad experimental y código abierto de alta calidad**. Damos la bienvenida a contribuciones de lingüistas, fonólogos, dialectólogos, ingenieros de NLP y humanistas digitales.

---

## 1. Áreas Principales de Contribución

1. **Ampliación Dialectal y Diacrónica**:
   - Nuevas variantes regionales (e.g., variedades patagónicas, dialectos judeoespañoles / ladino, español filipino).
   - Variedades históricas (e.g., español renacentista del siglo XVI, judeoespañol medieval).
2. **Refinamiento Fonotáctico y Alófonos**:
   - Nuevos procesos de sandhi externo o asimilación segmental.
   - Calibración empírica de frecuencias formánticas $(F_0, F_1, F_2, F_3)$ en [`idiolect_g2p/core/phonetics.py`](idiolect_g2p/core/phonetics.py).
3. **Gramática Estocástica (MaxEnt / Stochastic OT)**:
   - Formulación de nuevas restricciones universales de marcación o fidelidad en [`idiolect_g2p/inference/maxent_grammar.py`](idiolect_g2p/inference/maxent_grammar.py).
4. **Métrica y Versificación**:
   - Mejoras en la detección de encabalgamientos, compensaciones prosódicas o esquemas estróficos complejos en [`idiolect_g2p/meter/`](idiolect_g2p/meter/).

---

## 2. Protocolo para Agregar una Nueva Variante Dialectal

Para incorporar una nueva variedad dialectal o diacrónica al catálogo oficial:

1. **Crear el módulo dialectal**:
   - Cree un archivo descriptivo en `idiolect_g2p/dialects/` (por ejemplo, `ladino.py`).
   - Herédese de la clase base `Dialect` en [`idiolect_g2p/dialects/base.py`](idiolect_g2p/dialects/base.py).
2. **Definir el vector continuo de isoglosas $\boldsymbol{\theta}$**:
   - Cada dimensión del `IsoglossVector` debe estar documentada y justificada con fuentes bibliográficas académicas (e.g., Alvar, Lipski, Penny, RAE-ASALE).
3. **Implementar reglas alofónicas**:
   - Sobrescribir el método `apply_allophonic_rules(self, word, syllables)`.
4. **Registrar en el catálogo global**:
   - Instanciar e incluir la variante en `_register_default_dialects` dentro de [`idiolect_g2p/dialects/registry.py`](idiolect_g2p/dialects/registry.py).
5. **Añadir pruebas unitarias**:
   - Crear una prueba en `tests/test_dialects.py` verificando pares mínimos y alófonos distintivos.

---

## 3. Estándares de Calidad y Estilo de Código

Todo código propuesto debe adherirse a los siguientes estándares:

- **Python 3.9+**: Sintaxis moderna con anotaciones de tipo exhaustivas (`typing`, `from __future__ import annotations`).
- **Formato PEP 8**: Indentación de 4 espacios, nombres en snake_case para funciones y variables, PascalCase para clases.
- **Documentación Bilingüe**: Docstrings formales en español y/o inglés detallando el fundamento teórico o bibliográfico del algoritmo.
- **Sin Dependencias Pesadas Innecesarias**: Idiolect-G2P prioriza la síntesis y procesamiento en Python puro con dependencias mínimas (FastAPI, Pydantic, Pytest).

---

## 4. Flujo de Trabajo de Git (Git Workflow)

1. **Bifurcar (Fork)** el repositorio en GitHub.
2. **Crear una rama temática** con nombre descriptivo:
   ```bash
   git checkout -b feat/dialecto-ladino
   # o
   git checkout -b fix/asimilacion-sandhi-nasal
   ```
3. **Ejecutar la suite de pruebas localmente**:
   ```bash
   pytest -v
   ```
   *Ningún Pull Request será aprobado si la suite de pruebas (69 tests actuales) no pasa al 100%.*
4. **Hacer commits semánticos con mensajes en español**:
   ```bash
   git commit -m "feat(dialects): incorporar variedad judeoespanola con lleismo conservador"
   ```
5. **Enviar el Pull Request** referenciando el issue o debate metodológico pertinente.

---

## 5. Revisión por Pares (Peer-Review) de Pull Requests

Cada contribución será sometida a una revisión técnica y académica:
- **Verificación computacional**: Pases de tests unitarios, benchmarks de rendimiento temporal (< 100 ms) y verificación de ciberseguridad.
- **Verificación filológica**: Revisión de las citas bibliográficas que fundamentan el comportamiento fonológico o la métrica versal propuesta.

Para dudas conceptuales o discusiones filológicas, abra un *GitHub Discussion* o un *Issue* con la plantilla correspondiente.
