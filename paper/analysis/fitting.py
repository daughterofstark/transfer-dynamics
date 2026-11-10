"""Frozen matched comparison and standalone reproduction of the adopted model."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[k]='1'
from pathlib import Path
import json, time, argparse, hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np
import model as m
R=Path(__file__).resolve().parent
REFERENCE=R.parent/'reference'
SEEDS=R.parent/'specification/bootstrap_seeds.json'

def save(name,x):
    p=Path(os.environ.get('CT_OUTPUT',str(R.parents[1]/'outputs')))/name
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp')
    t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.replace(p)

def reference(a,w):
    t=(a['age']-50)/20;z=np.column_stack([np.ones(len(t)),t,t*t])
    return np.linalg.solve(z.T@(w[:,None]*z),z.T@(w*a['GI0']))

def center(a,c):
    t=(a['age']-50)/20;b=a.copy()
    b['GI0']=np.ascontiguousarray(100+a['GI0']-(c[0]+c[1]*t+c[2]*t*t))
    return b

def fitted(a,w,kind,starts=None):
    c=reference(a,w);b=center(a,c)
    r=m.fit(b,w,starts=starts,fixed={6:0.} if kind=='constant7' else {})
    r['reference_coefficients']=c.tolist()
    r['outcome_parameter_count']=7 if kind=='constant7' else 8
    r['reference_nuisance_coefficients']=3
    obj=m.Objective(b,w);loss,_=obj(m.vector(r));ok=w>0
    loss2=np.average(np.nanmean((obj.pred[ok]-a['Y'][ok])**2,axis=1),weights=w[ok])
    assert abs(loss-loss2)<1e-8
    r['independent_loss_error']=float(abs(loss-loss2))
    return r

def predict(a,r):
    b=center(a,r['reference_coefficients']);n,j=a['Y'].shape
    out=np.full_like(a['Y'],np.nan);grad=np.zeros(7);eta=np.zeros(1)
    z=np.ascontiguousarray((b['GI0']-100)/15)
    # C writes raw predictions; its profiled eta is ignored here.
    # mode=1 selects observed daily timing, not profiling behavior.
    m.lib.objective(n,j,a['ptr'],a['dt'],a['plays'],a['P'],a['D'],a['Y'],a['age'],np.ones(n),z,m.vector(r),1,grad,out,eta)
    return out+r['baseline_GI_coefficient_per15']*z[:,None]

def starts():
    return [[.006,.005,4.,1.6,-.5,.0006,0.],
            [.004,.002,4.,2.,-.4,.002,.15],
            [.003,.0005,4.,2.,.3,.005,.5]]

def folds(n):
    return np.random.default_rng(291029).integers(0,5,n)
