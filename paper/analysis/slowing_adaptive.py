import numpy as np
from scipy.integrate import quad_vec
import slowing as m
def integrate_person(a,fit,i,tol=1e-7):
    sub=m.m.subset(a,np.array([i]));x=m.vector(fit);kg,k=x[:2];lam=-np.log1p(-k)
    o=m.Objective(sub,np.ones(1),reference=fit['reference_coefficients'],single=True,profile=False)
    intervals=sub['ptr'][0][np.isfinite(sub['Y'][0])];start=int(intervals[0,0]);end=int(intervals[-1,1]);p=a['plays'][start:end];d=a['dt'][start:end];rate=p[p>0]/d[p>0]
    g=-np.expm1(rate*np.log1p(-kg));points=-np.log(g+1e-9)/lam;points=np.unique(points[(points>0)&(points<50)])
    def fn(u):
        o.u[0]=u;o(x);return np.nan_to_num(o.pred[0])*np.exp(-u)
    result,error=quad_vec(fn,0,50,epsabs=tol,epsrel=tol/10,points=points,limit=10000)
    result+=fit['baseline_GI_coefficient_per15']*o.b[0];result[~np.isfinite(sub['Y'][0])]=np.nan
    return result,float(error)

def affected(a,fit):
    x=m.vector(fit);lam=-np.log1p(-x[1]);threshold=-np.log1p(-np.exp(-20*lam))/(-np.log1p(-x[0]))
    ids=np.flatnonzero(a['plays']/a['dt']>threshold)
    return np.unique(np.searchsorted(a['ptr'][:,0,0],ids,side='right')-1)
