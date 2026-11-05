"""Standalone adopted age-baseline model and nested saturating-retest comparator.

No imports from exploratory engines. Daily inputs are frozen external files.
"""
from pathlib import Path
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[key]='1'
import ctypes,subprocess,sys,time,shlex
import numpy as np
from scipy.optimize import minimize
R=Path(__file__).resolve().parent
BASE=R
BUILD=R/'build';BUILD.mkdir(exist_ok=True)
LIB=BUILD/('objective.dylib' if sys.platform=='darwin' else 'objective.so')
if not LIB.exists() or LIB.stat().st_mtime<(R/'objective.c').stat().st_mtime:
    subprocess.run(shlex.split(os.environ.get('CC','cc'))+shlex.split(os.environ.get('CFLAGS',''))+['-O3','-shared','-fPIC',str(R/'objective.c'),'-o',str(LIB),'-lm'],check=True)
lib=ctypes.CDLL(str(LIB));fa=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');ia=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')
lib.objective.argtypes=[ctypes.c_int,ctypes.c_int,ia]+[fa]*9+[ctypes.c_int,fa,fa,fa];lib.objective.restype=ctypes.c_double
NAMES=['learning_per_game','training_forgetting_per_day','game_ceiling_GI','test_increment_age50_GI','age_beta_per20','retest_forgetting_per_day','test_diminishing_fraction']
SCALE=np.array([.005,.002,4.,2.,.3,.002,.15])
BOUNDS=[(1e-6,.99),(1e-6,.99),(0.,30.),(0.,None),(-3.,3.),(1e-6,.99),(0.,.99)]

def load(path=None):
    from inputs import load_model
    return load_model(path)
def vector(r):return np.array([r['parameters'].get(k,0.) for k in NAMES])
def half(k):return float(np.log(.5)/np.log1p(-k)) if k>0 else None
def rate(h):return float(-np.expm1(np.log(.5)/h))
def derived(x):
    kg,kf,A,q,beta,kr=map(float,x[:6])
    out=dict(training_half_life_days=half(kf),retest_half_life_days=half(kr),age_ratio_per20=float(np.exp(beta)))
    for pct in [70,80,90]:
        g=kf*pct/((1-kf)*(100-pct));out[f'dose_{pct}_games_day']=float(np.log1p(-g)/np.log1p(-kg)) if g<1 else None
    for p in [1,2]:
        g=-np.expm1(p*np.log1p(-kg));out[f'GI_at_{p}_games_day']=float(A*(1-kf)*g/(kf+(1-kf)*g))
    g=kf*3/((1-kf)*(A-3)) if A>3 else np.inf;out['dose_3GI_games_day']=float(np.log1p(-g)/np.log1p(-kg)) if g<1 else None
    return out

class Objective:
    def __init__(self,a,w):
        self.a=a;self.w=np.ascontiguousarray(w,dtype=float);self.pred=np.full_like(a['Y'],np.nan);self.b=np.ascontiguousarray((a['GI0']-100)/15);self.eta=np.zeros(1)
    def __call__(self,x):
        a=self.a;grad=np.zeros(7);n,m=a['Y'].shape
        val=lib.objective(n,m,a['ptr'],a['dt'],a['plays'],a['P'],a['D'],a['Y'],a['age'],self.w,self.b,np.ascontiguousarray(x,dtype=float),1,grad,self.pred,self.eta)
        self.pred+=self.eta[0]*self.b[:,None]
        return val,grad

def active_gradient(x,g,common=False,fixed=None):
    fixed=fixed or {};g=g.copy()
    if common:g[1]+=g[5]
    active=[j for j in range(5 if common else 7) if j not in fixed]
    for j in active:
        lo,hi=BOUNDS[j]
        if x[j]-lo<1e-8:g[j]=min(g[j],0.)
        if hi is not None and hi-x[j]<1e-8:g[j]=max(g[j],0.)
    return float(max(abs(g[active]*SCALE[active])))

def fit(a,w,common=False,starts=None,fixed=None):
    fixed=fixed or {};active=[j for j in range(5 if common else 7) if j not in fixed]
    obj=Objective(a,w)
    if starts is None:starts=[[.006,.005,4.,1.6,-.5,.0006,.1],[.004,.002,4.,2.,-.4,.002,.3],[.003,.0005,4.,2.,.3,.005,0.]]
    bounds=[(BOUNDS[j][0]/SCALE[j],None if BOUNDS[j][1] is None else BOUNDS[j][1]/SCALE[j]) for j in active]
    def expand(z):
        x=np.zeros(7);x[active]=z*SCALE[active]
        for j,v in fixed.items():x[j]=v
        if common:x[5]=x[1]
        return x
    def fun(z):
        x=expand(z);v,g=obj(x)
        if common:g[1]+=g[5]
        return v,g[active]*SCALE[active]
    begin=time.monotonic();records=[]
    for start in starts:
        opt=minimize(fun,np.array(start)[active]/SCALE[active],jac=True,method='L-BFGS-B',bounds=bounds,
            options={'maxiter':500,'maxls':100,'ftol':1e-13,'gtol':1e-9})
        for retry in range(3):
            x=expand(opt.x);v,g=obj(x)
            if opt.success and active_gradient(x,g,common,fixed)<1e-5:break
            opt=minimize(fun,opt.x,jac=True,method='L-BFGS-B',bounds=bounds,
                options={'maxiter':500,'maxls':100,'maxcor':20,'ftol':1e-14,'gtol':1e-9})
        x=expand(opt.x);v,g=obj(x);hits=[];stationarity=None
        for j in active:
            lo,hi=BOUNDS[j]
            if x[j]-lo<1e-8:hits.append(NAMES[j]+'_lower')
            if hi is not None and hi-x[j]<1e-8:hits.append(NAMES[j]+'_upper')
        records.append(dict(model='constant7' if 6 in fixed else 'saturating8',parameters=dict(zip(NAMES,map(float,x))),derived=derived(x),
            wmse=float(v),success=bool(opt.success or stationarity is not None),max_scaled_projected_gradient=active_gradient(x,g,common,fixed),stationarity=stationarity,
            bound_hits=hits,fixed_parameters={NAMES[j]:v for j,v in fixed.items()},nit=int(opt.nit),message=str(opt.message)))
    good=[r for r in records if r['success'] and (r['max_scaled_projected_gradient']<1e-4 or (r['stationarity'] and r['stationarity']['passed']))]
    assert good,records
    best=min(good,key=lambda r:r['wmse']);best['starts']=[dict(wmse=r['wmse'],success=r['success'],gradient=r['max_scaled_projected_gradient'],derived=r['derived']) for r in records]
    best['elapsed_seconds']=time.monotonic()-begin
    obj(vector(best));best['baseline_GI_coefficient_per15']=float(obj.eta[0])
    return best

def reference_predict(a,x):
    kg,kf,A,q50,beta,kr,alpha=x;out=np.full_like(a['Y'],np.nan)
    for i in range(len(a['age'])):
        G=Rt=0.;q=q50*np.exp(beta*(a['age'][i]-50)/20)
        for j in range(a['Y'].shape[1]):
            if not np.isfinite(a['Y'][i,j]):continue
            Rt=((1-alpha)*Rt+q)*(1-kr)**a['D'][i,j]
            start,end=a['ptr'][i,j]
            for p,d in zip(a['plays'][start:end],a['dt'][start:end]):
                G=(A-(A-G)*(1-kg)**p)*(1-kf)**d
            out[i,j]=G+Rt
    return out

def subset(a,ids):return {k:(v if k in ['dt','plays'] else np.ascontiguousarray(v[ids])) for k,v in a.items()}
