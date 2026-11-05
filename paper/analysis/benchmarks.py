import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json
import numpy as np
from scipy.optimize import minimize
from concurrent.futures import ProcessPoolExecutor,as_completed
import multiprocessing as mp
R=Path(__file__).resolve().parent

def specification(kind):
    if kind=='retest_only':return ['retest_forgetting','q50','age_beta'],np.array([.002,2.,.3]),[(1e-6,.99),(0,None),(-3,3)],[[.002,3,-.4],[.0005,2,-.5],[.01,6,0]]
    if kind=='no_forgetting':return ['learning_per_game','training_max','q50','age_beta'],np.array([.005,4.,2.,.3]),[(1e-6,.99),(0,30),(0,None),(-3,3)],[[.005,4,1,-.4],[.001,6,2,-.5],[.03,3,.5,0]]
    if kind=='static_dose_response':return ['learning_per_game','training_max','q_T2','q_T3','q_T4','q_T5','age_beta'],np.array([.005,4.,2.,2.,2.,2.,.3]),[(1e-6,.99),(0,30)]+[(0,None)]*4+[(-3,3)],[[.005,4,2,3,4,5,-.4],[.001,6,1,2,3,4,-.5],[.03,3,1,2,3,4,0]]
    raise ValueError(kind)

class Objective:
    def __init__(self,a,w,kind,baseline=False):
        self.a=a;self.kind=kind;self.names,self.scale,self.bounds,_=specification(kind)
        self.valid=np.isfinite(a['Y']);self.y=np.nan_to_num(a['Y']);self.w=w[:,None]*self.valid/self.valid.sum(1)[:,None];self.w/=w.sum()
        self.age=(a['age']-50)/20;self.days=np.nan_to_num(a['D']);self.cp=np.cumsum(np.nan_to_num(a['P']),axis=1)
        self.baseline=baseline;self.b=(a['GI0']-100)/15;self.eta=0.
    def predict(self,x):
        aa=self.age;v=self.valid
        if self.kind=='retest_only':
            kr,q,beta=x;factor=np.exp(beta*aa);H=np.zeros(len(aa));Hk=H.copy();pred=np.zeros_like(self.y);jac=np.zeros((*pred.shape,3))
            for j in range(4):
                d=self.days[:,j];decay=np.exp(d*np.log1p(-kr));prev=H.copy();H=(H+1)*decay;Hk=Hk*decay-(prev+1)*d*decay/(1-kr)
                pred[:,j]=q*factor*H;jac[:,j,0]=q*factor*Hk;jac[:,j,1]=factor*H;jac[:,j,2]=pred[:,j]*aa
        else:
            kg,A=x[:2];beta=x[-1];factor=np.exp(beta*aa);z=np.exp(self.cp*np.log1p(-kg));game=A*(1-z)
            pred=game.copy();jac=np.zeros((*pred.shape,len(x)));jac[:,:,0]=A*self.cp*z/(1-kg);jac[:,:,1]=1-z
            if self.kind=='no_forgetting':
                n=np.arange(1,5)[None,:];retest=x[2]*factor[:,None]*n;jac[:,:,2]=factor[:,None]*n
            else:
                retest=factor[:,None]*x[None,2:6]
                for j in range(4):jac[:,j,2+j]=factor
            pred+=retest;jac[:,:,-1]=retest*aa[:,None]
        return pred,jac
    def __call__(self,z):
        pred,jac=self.predict(z*self.scale);e=pred-self.y
        if self.baseline:
            self.eta=-float(np.sum(self.w*e*self.b[:,None])/np.sum(self.w*self.b[:,None]**2))
            e+=self.eta*self.b[:,None]
        return float(np.sum(self.w*e*e)),np.sum(2*self.w[:,:,None]*e[:,:,None]*jac,axis=(0,1))*self.scale

def fit(a,w,kind,baseline=False):
    if kind=='mean_change':
        if baseline:
            X=np.column_stack([np.ones(len(w)),(a['GI0']-100)/15]);ym=np.nanmean(a['Y'],axis=1);b=np.linalg.solve(X.T@(w[:,None]*X),X.T@(w*ym));pred=np.where(np.isfinite(a['Y']),(X@b)[:,None],np.nan)
            return dict(model=kind,parameters={'mean':float(b[0]),'baseline_GI_coefficient_per15':float(b[1])},wmse=float(np.average(np.nanmean((a['Y']-pred)**2,axis=1),weights=w))),pred
        mu=float(np.average(np.nanmean(a['Y'],axis=1),weights=w));return dict(model=kind,parameters={'mean':mu},wmse=float(np.average(np.nanmean((a['Y']-mu)**2,axis=1),weights=w))),np.where(np.isfinite(a['Y']),mu,np.nan)
    o=Objective(a,w,kind,baseline);names,scale,bounds,starts=specification(kind);records=[]
    sb=[(l/s,None if h is None else h/s) for (l,h),s in zip(bounds,scale)]
    for start in starts:
        z=np.array(start)/scale
        for retry in range(3):
            opt=minimize(o,z,jac=True,method='L-BFGS-B',bounds=sb,options={'ftol':1e-13,'gtol':1e-8,'maxiter':1000,'maxls':100,'maxcor':20});z=opt.x;val,grad=o(z)
            pg=grad.copy()
            for j,(lo,hi) in enumerate(sb):
                if z[j]-lo<1e-8:pg[j]=min(pg[j],0)
                if hi is not None and hi-z[j]<1e-8:pg[j]=max(pg[j],0)
            if opt.success and abs(pg).max()<1e-4:break
        assert opt.success and abs(pg).max()<1e-4,(kind,opt.message,pg)
        records.append(dict(model=kind,parameters=dict(zip(names,map(float,z*scale))),wmse=val,gradient=float(abs(pg).max()),bound_hits=[names[j] for j,(lo,hi) in enumerate(sb) if z[j]-lo<1e-8 or hi is not None and hi-z[j]<1e-8]))
    best=min(records,key=lambda x:x['wmse']);best['start_losses']=[r['wmse'] for r in records]
    x=np.array([best['parameters'][k] for k in names]);o(x/scale);pred,_=o.predict(x)
    if baseline:pred+=o.eta*o.b[:,None];best['baseline_GI_coefficient_per15']=o.eta
    pred[~o.valid]=np.nan
    loss=float(np.average(np.nanmean((a['Y']-pred)**2,axis=1),weights=w));assert abs(loss-best['wmse'])<1e-8
    return best,pred
