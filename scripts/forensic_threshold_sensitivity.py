"""Sensibilidad del umbral de contraste de las evidencias forenses.

Para cada par de rima de un corpus (los poemas de ``corpus_examples.json`` mas
pares minimos de control) calcula, por rasgo, la diferencia de distancia media
entre las hipotesis con y sin el rasgo, solo cuando el rasgo aparece en el
segmento rimante. Imprime la distribucion y cuantas evidencias se emitirian con
distintos umbrales.

Uso: ``python scripts/forensic_threshold_sensitivity.py``
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY
from idiolect_g2p.inference import forensic_explainer as fe
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.meter.phonetic_distance import evaluate_rhyme_pair

CORPUS = Path(__file__).resolve().parents[1] / "idiolect_g2p" / "web" / "corpus_examples.json"
CONTROLES = [
    "El abrazo\nel paso", "El lazo\nel caso", "La casa\nla caza", "El puerto\nel muelto",
    "El mar\nel sal", "La valla\nla playa", "El pollo\nel poyo", "La cena\nla seda",
    "La mariposa\nla luminosa", "La calle\nel valle", "La rosa\nla hermosa", "El cielo\nel suelo",
    "El arte\nel alce", "La cerca\nla sierra", "La luz\nla cruz", "El mes\nel pez",
]
THRESHOLDS = (0.0, 0.001, 0.005, 0.01, 0.02, 0.05)


def contrastes(texto: str) -> List[Tuple[str, float, bool]]:
    """Devuelve (rasgo, |delta|, favorece_a_la_hipotesis_principal) por par y rasgo."""
    perfil = profile_idiolect_from_poem(texto)
    primaria = GLOBAL_DIALECT_REGISTRY.get(perfil.predicted_dialect_code)
    versos = {v.verse_number: v for v in perfil.poem_analysis.all_verses}
    transductor = G2PTransducer()
    salida: List[Tuple[str, float, bool]] = []
    if primaria is None:
        return salida
    for par in perfil.evaluated_rhyme_matches:
        v1, v2 = versos.get(par.verse_1_index), versos.get(par.verse_2_index)
        if v1 is None or v2 is None:
            continue
        for rasgo in fe._FEATURES:
            con, sin = [], []
            for d in GLOBAL_DIALECT_REGISTRY.list_all():
                m = evaluate_rhyme_pair(v1, v2, dialect=d, transducer=transductor)
                (con if rasgo.has_feature(d) else sin).append(m)
            fonemas = {p for m in con + sin for p in m.rhyme_phones_1 + m.rhyme_phones_2}
            if not con or not sin or not (fonemas & rasgo.relevant_phones):
                continue
            mc = sum(m.phonetic_distance for m in con) / len(con)
            ms = sum(m.phonetic_distance for m in sin) / len(sin)
            tiene = rasgo.has_feature(primaria)
            favorece = (mc < ms) if tiene else (ms < mc)
            salida.append((rasgo.phenomenon.split(" (")[0], abs(mc - ms), favorece))
    return salida


def main() -> None:
    textos = [e["text"] for e in json.loads(CORPUS.read_text(encoding="utf-8"))] + CONTROLES
    filas: List[Tuple[str, float, bool]] = []
    for t in textos:
        filas.extend(contrastes(t))
    por_rasgo: Dict[str, List[float]] = defaultdict(list)
    for rasgo, delta, _ in filas:
        por_rasgo[rasgo].append(delta)
    print(f"Textos: {len(textos)}  |  observaciones (par x rasgo con el rasgo en la rima): {len(filas)}")
    for rasgo, vals in por_rasgo.items():
        vals_ord = sorted(vals)
        print(f"\n{rasgo}: n={len(vals)}")
        print("  deltas ordenados:", [round(v, 3) for v in vals_ord])
    print("\nEvidencias emitidas segun umbral (solo si favorece a la hipotesis principal):")
    for u in THRESHOLDS:
        n = sum(1 for _, d, fav in filas if fav and d >= max(u, 1e-12) and d > u - 1e-12)
        print(f"  umbral {u:<6}: {n}")


if __name__ == "__main__":
    main()
