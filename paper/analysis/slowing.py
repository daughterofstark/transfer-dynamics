import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import importlib.util,sys,json,ctypes,subprocess,time
import numpy as np
from scipy.special import roots_legendre
from scipy.optimize import minimize,brentq
from scipy.integrate import quad
R=Path(__file__).resolve().parent
import fitting as agefit
import six_utils as m
import shlex
NAMES=m.NAMES.copy();NAMES[1]='training_decay_scale'
SCALE=m.SCALE;BOUNDS=m.BOUNDS
STARTS=[[.006,.008,4,1.5,-.5,.0005],[.003,.002,4,2,-.4,.002],[.015,.03,5,1,-.4,.0003]]
LIB=R/'build'/('slowing.dylib' if sys.platform=='darwin' else 'slowing.so')
if not LIB.exists() or LIB.stat().st_mtime<(R/'slowing_objective.c').stat().st_mtime:
    subprocess.run(shlex.split(os.environ.get('CC','cc'))+shlex.split(os.environ.get('CFLAGS',''))+['-O3','-shared','-fPIC',str(R/'slowing_objective.c'),'-o',str(LIB),'-lm'],check=True)
lib=ctypes.CDLL(str(LIB));lib.objective.argtypes=[ctypes.c_int]*3+[m.fa]*2+[m.ia]+[m.fa]*8+[ctypes.c_int]+[m.fa]*3;lib.objective.restype=ctypes.c_double

def quadrature(n=24):
    x,w=roots_legendre(n);v=(x+1)*9-14;u=np.exp(v);weight=w*9*u*np.exp(-u);weight/=weight.sum()
    return np.ascontiguousarray(u),np.ascontiguousarray(weight)

def vector(r):return np.array([r['parameters'][k] for k in NAMES])

def maintenance(x,target):
    kg,k,A,*_=x
    if target<=0:return 0.
    if target>=1:return None
    lam=-np.log1p(-k)
    def fraction(g):return quad(lambda u:np.exp(-u)*np.exp(-lam*u)*g/(1-np.exp(-lam*u)*(1-g)),0,50,epsabs=1e-11,epsrel=1e-10,limit=100)[0]
    if fraction(1.)<target:return None
    g=brentq(lambda g:fraction(g)-target,1e-12,1.,xtol=1e-14)
    return float(np.log1p(-g)/np.log1p(-kg))

def derived(x):
    kg,k,A,q,beta,kr=x
    r=dict(isolated_input_half_life_days=float(1/-np.log1p(-k)),retest_half_life_days=m.half(kr),age_ratio_per20=float(np.exp(beta)))
    for pct in [70,80,90]:r[f'dose_{pct}_games_day']=maintenance(x,pct/100)
    r['dose_3GI_games_day']=maintenance(x,3/A) if A>3 else None
    return r

class Objective:
    def __init__(self,a,w,nodes=24,reference=None,single=False,profile=True):
        self.a=a;self.w=np.ascontiguousarray(w,dtype=float)
        self.reference=agefit.reference(a,w) if reference is None else np.array(reference)
        aa=(a['age']-50)/20;self.b=np.ascontiguousarray((a['GI0']-(self.reference[0]+self.reference[1]*aa+self.reference[2]*aa*aa))/15)
        self.u,self.weights=(np.ones(1),np.ones(1)) if single else quadrature(nodes)
        self.pred=np.full_like(a['Y'],np.nan);self.eta=np.zeros(1);self.rates=None;self.profile=profile
    def __call__(self,x):
        a=self.a;g=np.zeros(6);n,j=a['Y'].shape
        loss=lib.objective(n,j,len(self.u),self.u,self.weights,a['ptr'],a['dt'],a['plays'],a['D'],a['Y'],a['age'],self.w,self.b,np.ascontiguousarray(x,dtype=float),int(self.profile),g,self.pred,self.eta)
        self.pred+=self.eta[0]*self.b[:,None]
        return loss,g

def fit(a,w,starts=None,nodes=24):
    o=Objective(a,w,nodes=nodes);starts=STARTS if starts is None else starts;records=[];begin=time.monotonic()
    bounds=[(lo/sc,None if hi is None else hi/sc) for (lo,hi),sc in zip(BOUNDS,SCALE)]
    def fun(z):v,g=o(z*SCALE);return v,g*SCALE
    for start in starts:
        z=np.array(start)/SCALE
        for retry in range(3):
            opt=minimize(fun,z,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':400,'maxls':70,'maxcor':20,'ftol':1e-13 if retry==0 else 1e-14,'gtol':1e-8});z=opt.x;x=z*SCALE;v,g=o(x)
            if opt.success and m.active_gradient(x,g)<1e-5:break
        stationarity=None
        accepted=bool((opt.success and m.active_gradient(x,g)<1e-4) or stationarity and stationarity['passed'])
        hits=[NAMES[j] for j,(lo,hi) in enumerate(BOUNDS) if x[j]-lo<1e-8 or hi is not None and hi-x[j]<1e-8]
        r=dict(parameters=dict(zip(NAMES,map(float,x))),wmse=float(v),gradient=m.active_gradient(x,g),stationarity=stationarity,accepted=accepted,bound_hits=hits,baseline_GI_coefficient_per15=float(o.eta[0]),reference_coefficients=o.reference.tolist(),nodes=nodes,elapsed_seconds=time.monotonic()-begin)
        records.append(r);print('Start completed',len(records),'loss',v,'gradient',r['gradient'],'accepted',accepted,'seconds',round(r['elapsed_seconds']),flush=True)
    good=[r for r in records if r['accepted']];assert good,records
    best=min(good,key=lambda r:r['wmse']);best['starts']=[{k:r[k] for k in ['wmse','gradient','accepted','bound_hits']} for r in records];x=vector(best);v,g=o(x);ok=w>0
    loss=float(np.average(np.nanmean((a['Y'][ok]-o.pred[ok])**2,axis=1),weights=w[ok]));assert abs(loss-v)<1e-8
    best.update(model='hyperbolic_training7',outcome_parameters=7,reference_parameters=3,reference_refit=True,derived=derived(x),loss_audit_error=abs(loss-v));return best

def predict(a,r,nodes=None):
    o=Objective(a,np.ones(len(a['age'])),nodes=r['nodes'] if nodes is None else nodes,reference=r['reference_coefficients'],profile=False);o(vector(r))
    return o.pred+r['baseline_GI_coefficient_per15']*o.b[:,None]

def python_raw(a,x,nodes=24):
    u,w=quadrature(nodes);kg,k,A,q50,beta,kr=x;out=np.full_like(a['Y'],np.nan);lam=-np.log1p(-k)*u
    for i in range(len(a['age'])):
        z=np.zeros(nodes);rt=0;q=q50*np.exp(beta*(a['age'][i]-50)/20)
        for j in range(4):
            if not np.isfinite(a['Y'][i,j]):continue
            rt=(rt+q)*(1-kr)**a['D'][i,j]
            start,end=a['ptr'][i,j]
            for p,d in zip(a['plays'][start:end],a['dt'][start:end]):
                g=-np.expm1(p*np.log1p(-kg))
                z=(z+g*(1-z))*np.exp(-lam*d)
            out[i,j]=A*(w@z)+rt
    return out
