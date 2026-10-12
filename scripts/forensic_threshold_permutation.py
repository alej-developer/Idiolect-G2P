"""Contraste por media, mediana, jackknife y permutacion sobre las 18 hipotesis dialectales.

Uso: ``PYTHONPATH=. python scripts/forensic_threshold_permutation.py``
La permutacion reasigna al azar que dialectos cuentan como 'con rasgo' (mismo tamano de
grupo) y mide cuan a menudo el azar iguala el contraste observado. Es descriptiva: los
dialectos no son intercambiables (estan correlacionados).
"""
import json
import random
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from idiolect_g2p.core.transducer import G2PTransducer
from idiolect_g2p.dialects.registry import GLOBAL_DIALECT_REGISTRY as R
from idiolect_g2p.inference import forensic_explainer as fe
from idiolect_g2p.inference.bayesian_profiler import profile_idiolect_from_poem
from idiolect_g2p.meter.phonetic_distance import evaluate_rhyme_pair
import forensic_threshold_sensitivity as S  # noqa: E402
random.seed(1)
T=G2PTransducer(); D=R.list_all()
rows=[]
texts=[e["text"] for e in json.loads(S.CORPUS.read_text(encoding="utf-8"))]+S.CONTROLES
for t in texts:
    pr=profile_idiolect_from_poem(t); prim=R.get(pr.predicted_dialect_code)
    vs={v.verse_number:v for v in pr.poem_analysis.all_verses}
    for p in pr.evaluated_rhyme_matches:
        v1,v2=vs.get(p.verse_1_index),vs.get(p.verse_2_index)
        if not v1 or not v2: continue
        ms=[evaluate_rhyme_pair(v1,v2,dialect=d,transducer=T) for d in D]
        dist=[m.phonetic_distance for m in ms]
        ph={x for m in ms for x in m.rhyme_phones_1+m.rhyme_phones_2}
        for f in fe._FEATURES:
            flag=[f.has_feature(d) for d in D]
            if not (ph&f.relevant_phones) or all(flag) or not any(flag): continue
            w=[x for x,g in zip(dist,flag) if g]; o=[x for x,g in zip(dist,flag) if not g]
            dm=st.mean(w)-st.mean(o); dmed=st.median(w)-st.median(o)
            # jackknife
            jk=[]
            for i in range(len(dist)):
                w2=[x for j,(x,g) in enumerate(zip(dist,flag)) if g and j!=i]; o2=[x for j,(x,g) in enumerate(zip(dist,flag)) if not g and j!=i]
                if w2 and o2: jk.append(st.mean(w2)-st.mean(o2))
            same=all((x>0)==(dm>0) and x!=0 for x in jk) if dm!=0 else False
            jkmin=min(abs(x) for x in jk) if same else 0.0
            # permutation p
            k=sum(flag); n=0;N=2000
            for _ in range(N):
                idx=set(random.sample(range(len(dist)),k))
                a=[dist[i] for i in idx]; b=[dist[i] for i in range(len(dist)) if i not in idx]
                if abs(st.mean(a)-st.mean(b))>=abs(dm)-1e-12: n+=1
            prim_has=f.has_feature(prim); fav=(dm<0) if prim_has else (dm>0)
            rows.append((f.phenomenon.split(" (")[0],t.replace("\n"," / ")[:30],round(dm,4),round(dmed,4),round(jkmin,4),(n+1)/(N+1),fav,len(set(round(x,6) for x in dist))))
print(len(rows))
def cnt(f): return sum(1 for r in rows if r[6] and f(r))
print("mean>=.01",cnt(lambda r:abs(r[2])>=.01))
print("median>=.01",cnt(lambda r:abs(r[3])>=.01))
print("mean>=.01 & median>=.01",cnt(lambda r:abs(r[2])>=.01 and abs(r[3])>=.01))
print("jackknife-stable (all LOO same sign) & mean>=.01",cnt(lambda r:r[4]>0 and abs(r[2])>=.01))
print("jackknife min>=.005",cnt(lambda r:r[4]>=.005))
for a in (.05,.01):
    print("perm p<",a,cnt(lambda r:r[5]<a), "with mean>=.01",cnt(lambda r:r[5]<a and abs(r[2])>=.01))
print("perm p<.05 & median>=.005 & jk>0",cnt(lambda r:r[5]<.05 and abs(r[3])>=.005 and r[4]>0))
print("all-obs mean<.01 but p<.05:",sum(1 for r in rows if abs(r[2])<.01 and r[5]<.05))
