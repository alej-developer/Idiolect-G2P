---
name: Reporte de Discrepancia Fonética / Bug Report
about: Reportar un error en la silabificación, transcripción AFI o inferencia dialectal
title: "[BUG]: "
labels: ["bug", "fonologia"]
assignees: ''

---

## 1. Descripción de la Discrepancia
Una descripción concisa de cuál es el comportamiento fonético anómalo o error en la transducción.

## 2. Entrada Ortográfica y Contexto
- **Palabra o Verso de Entrada:** (e.g., `los mismos`)
- **Variedad Dialectal Seleccionada:** (e.g., `ES_PENINSULAR`, `CARIBBEAN_LAMBDACIST`)
- **Ajustes de Sandhi:** (Activado / Desactivado)

## 3. Comportamiento Observado vs. Comportamiento Esperado
- **AFI Producido por Idiolect-G2P:** (e.g., `[los ˈmis.mos]`)
- **AFI Esperado según la Fonotaxis:** (e.g., `[loz ˈmiz.mos]`)

## 4. Fundamentación Filológica / Bibliográfica
Cite las fuentes lingüísticas que respaldan la realización esperada (e.g., *Hualde, 2014; Quilis, 1993; RAE-ASALE, 2011*).

## 5. Entorno y Reproducción
- Versión de Python: (e.g., 3.11)
- Sistema Operativo: (Windows, Linux, macOS)
