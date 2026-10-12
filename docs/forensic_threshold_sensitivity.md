# Sensibilidad del umbral de evidencias forenses (0.01)

Una evidencia discriminante se emite cuando, para un rasgo presente en el
segmento rimante, la diferencia de distancia fonetica media entre las hipotesis
con y sin el rasgo supera `0.01` y favorece a la hipotesis principal.

## Metodo

`scripts/forensic_threshold_sensitivity.py` recorre 33 textos (los 17 poemas de
`corpus_examples.json` mas pares minimos de control) y reune 70 observaciones
par x rasgo donde el rasgo esta en el segmento rimante.

## Resultados

Los deltas forman una distribucion continua, sin hueco natural:

- Seseo: 0.0 (x7), 0.003 (x3), 0.01, 0.01, 0.012, 0.013, 0.015, 0.025, 0.03, 0.037 (x3), 0.055.
- Palatales: muchos 0.0, luego 0.004-0.009, 0.026, 0.033.
- Liquidas: mayoria 0.0, luego 0.001-0.009 y 0.015-0.053.

| Umbral | Evidencias emitidas |
|---|---|
| 0.0 | 26 |
| 0.001 | 24 |
| 0.005 | 21 |
| 0.01 | 15 |
| 0.02 | 11 |
| 0.05 | 2 |

Un delta de 0.003 es lo que produce un unico dialecto atipico de 18 (por
ejemplo el medieval con dz). El umbral 0.01 es por tanto un suelo de ruido
frente a valores atipicos aislados, **no un optimo validado**: es una decision
de diseno. Un contraste basado en la mediana seria mas robusto frente a
atipicos; no esta implementado.

## Limitacion: yeismo

No se ha podido construir un control positivo de yeismo. El transductor
renderiza la `y` intervocalica como [j], no [ʝ]. Las hipotesis yeista (ʝ vs j,
distancia 0.06) y lleista (ʎ vs j, 0.058) difieren ~0.002, ruido. El perfilador
elige dialectos lleistas para pares ll/y (valla/playa, halla/haya, pollo/poyo) y
en oxitonos como calló/cayó el segmento rimante es solo [o]. Con el umbral
actual no se emite evidencia de yeismo, lo cual es correcto para ruido, pero la
ruta positiva sigue sin verificar. `test_yeismo_no_emite_evidencia_sin_contraste_real`
fija este comportamiento. Corregirlo requiere cambiar el transductor, fuera de
este PR.
