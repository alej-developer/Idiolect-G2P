# Sensibilidad del umbral de evidencias forenses (0.01)

Una evidencia discriminante se emite cuando, para un rasgo presente en el
segmento rimante, la diferencia de distancia fonética media entre las hipótesis
con y sin el rasgo supera `0.01` y favorece a la hipótesis principal.

## Método

`scripts/forensic_threshold_sensitivity.py` recorre 33 textos (los 17 poemas de
`corpus_examples.json` más pares mínimos de control) y reúne 70 observaciones
par x rasgo donde el rasgo está en el segmento rimante.

## Resultados

Los deltas forman una distribución continua, sin hueco natural:

- Seseo: 0.0 (x7), 0.003 (x3), 0.01, 0.01, 0.012, 0.013, 0.015, 0.025, 0.03, 0.037 (x3), 0.055.
- Palatales: muchos 0.0, luego 0.004-0.009, 0.026, 0.033.
- Líquidas: mayoría 0.0, luego 0.001-0.009 y 0.015-0.053.

| Umbral | Evidencias emitidas |
|---|---|
| 0.0 | 26 |
| 0.001 | 24 |
| 0.005 | 21 |
| 0.01 | 15 |
| 0.02 | 11 |
| 0.05 | 2 |

Un delta de 0.003 es lo que produce un único dialecto atípico de 18 (por
ejemplo el medieval con dz). El umbral 0.01 es por tanto un suelo de ruido
frente a valores atípicos aislados, **no un óptimo validado**: es una decisión
de diseño. Un contraste basado en la mediana sería más robusto frente a
atípicos; no está implementado.

## Limitación: yeísmo

No se ha podido construir un control positivo de yeísmo. El transductor
renderiza la `y` intervocálica como [j], no [ʝ]. La hipótesis yeísta (ʝ vs j,
distancia 0.06) y la lleísta (ʎ vs j, 0.058) difieren ~0.002, ruido. El perfilador
elige dialectos lleístas para pares ll/y (valla/playa, halla/haya, pollo/poyo) y
en oxítonos como calló/cayó el segmento rimante es solo [o]. Con el umbral
actual no se emite evidencia de yeísmo, lo cual es correcto para ruido, pero la
ruta positiva sigue sin verificar. `test_yeismo_no_emite_evidencia_sin_contraste_real`
fija este comportamiento. Corregirlo requiere cambiar el transductor, fuera de
este PR.

## Prueba de robustez adicional (`scripts/forensic_threshold_permutation.py`)

Sobre las mismas 70 observaciones se comparó el criterio actual (diferencia de
medias >= 0.01) con otras alternativas. Se cuentan solo evidencias que favorecen
a la hipótesis principal.

| Criterio | Evidencias |
|---|---|
| media >= 0.01 (actual) | 15 |
| mediana >= 0.01 | 16 |
| media y mediana >= 0.01 | 13 |
| media >= 0.01 y estable al quitar cualquier dialecto (jackknife) | 15 |
| permutación p < 0.05 | 10 (9 coinciden con el criterio actual) |
| permutación p < 0.01 | 7 (todas coinciden con el criterio actual) |

Lectura honesta:

- Mediana y jackknife no mejoran de forma clara el criterio de la media: los 15
  casos actuales ya son estables al quitar cualquier dialecto, y la mediana solo
  mueve 2-3 casos en ambos sentidos.
- Hay observaciones con delta >= 0.01 que el azar iguala con facilidad (p > 0.1,
  dos de las 15 evidencias actuales tienen delta 0.010 y 0.015 con p = 0.12 y 0.10). Con solo 2-7 valores de
  distancia distintos entre 18 dialectos, la media tiene poca potencia.
- Los p-valores son descriptivos: los dialectos no son intercambiables.
- No emerge un umbral defendible con respaldo estadístico propio. 0.01 se
  mantiene como suelo de ruido pragmático, y el código no se cambia: ninguna
  alternativa probada lo mejora claramente. La evidencia emitida debe leerse
  como indicio, no como prueba.
