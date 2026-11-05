"""Selected longitudinal-change comparison; profiles baseline and two drift terms."""
from pathlib import Path
import os,sys,ctypes,subprocess,shlex
import numpy as np
import model as m
import fitting
R=Path(__file__).resolve().parent
LIB=m.BUILD/('drift.dylib' if sys.platform=='darwin' else 'drift.so')
if not LIB.exists() or LIB.stat().st_mtime<(R/'drift_objective.c').stat().st_mtime:
    subprocess.run(shlex.split(os.environ.get('CC','cc'))+shlex.split(os.environ.get('CFLAGS',''))+['-O3','-shared','-fPIC',str(R/'drift_objective.c'),'-o',str(LIB),'-lm'],check=True)
lib=ctypes.CDLL(str(LIB));lib.objective.argtypes=[ctypes.c_int,ctypes.c_int,m.ia]+[m.fa]*10+[ctypes.c_int,m.fa,m.fa,m.fa];lib.objective.restype=ctypes.c_double
def design(a,reference,drift=True):
    t=(a['age']-50)/20;mu=reference[0]+reference[1]*t+reference[2]*t*t
    T=np.cumsum(np.nan_to_num(a['D']),axis=1)/365.25
    X=np.zeros((*a['Y'].shape,3));X[:,:,0]=(a['GI0']-mu)[:,None]/15
    if drift:X[:,:,1]=T;X[:,:,2]=t[:,None]*T+T*T/40
    return np.ascontiguousarray(X)

class Objective:
    def __init__(self,a,w,reference=None,drift=True):
        self.a=a;self.w=np.ascontiguousarray(w,dtype=float)
        self.reference=fitting.reference(a,w) if reference is None else np.array(reference)
        self.X=design(a,self.reference,drift)
        valid=np.isfinite(a['Y']);weights=self.w[:,None]*valid/valid.sum(1)[:,None]
        gram=np.einsum('ij,ijk,ijl->kl',weights,self.X,self.X)
        self.M=np.zeros((3,3));size=3 if drift else 1;self.M[:size,:size]=np.linalg.inv(gram[:size,:size]);self.M=np.ascontiguousarray(self.M)
        self.pred=np.full_like(a['Y'],np.nan);self.eta=np.zeros(3)
    def __call__(self,x):
        a=self.a;n,j=a['Y'].shape;g=np.zeros(6)
        value=lib.objective(n,j,a['ptr'],a['dt'],a['plays'],a['P'],a['D'],a['Y'],a['age'],self.w,self.X,self.M,np.ascontiguousarray(x,dtype=float),1,g,self.pred,self.eta)
        self.pred+=self.X@self.eta
        return value,np.r_[g,0.]

def fitted(a,w,starts):
    previous=m.Objective;m.Objective=Objective
    try:r=m.fit(a,w,starts=starts,fixed={6:0.})
    finally:m.Objective=previous
    o=Objective(a,w);v,g=o(m.vector(r));ok=w>0
    loss=float(np.average(np.nanmean((a['Y'][ok]-o.pred[ok])**2,axis=1),weights=w[ok]))
    pg=m.active_gradient(m.vector(r),g,fixed={6:0.})
    boundary=None
    assert abs(v-loss)<1e-8 and (pg<1e-4 or boundary and boundary['passed'])
    r.update(model='age_baseline_drift9',outcome_parameter_count=9,baseline_reference_parameter_count=3,reference_coefficients=o.reference.tolist(),baseline_GI_coefficient_per15=float(o.eta[0]),drift_GI_per_year_age50=float(o.eta[1]),drift_GI_per_year_per20years=float(o.eta[2]),reference_refit=True,linear_coefficients=o.eta.tolist(),audit=dict(loss_error=abs(v-loss),gradient=pg,boundary=boundary))
    for age in [30,50,70,85]:r['derived'][f'drift_GI_per_year_age{age}']=float(o.eta[1]+o.eta[2]*(age-50)/20)
    return r

def predict(a,r):
    b=fitting.center(a,r['reference_coefficients']);o=m.Objective(b,np.ones(len(a['age'])))
    o(m.vector(r));raw=o.pred-o.eta[0]*o.b[:,None]
    return raw+design(a,r['reference_coefficients'])@np.array(r['linear_coefficients'])
