import numpy as np
import time
from scipy.optimize import minimize
import slowing as m
def finish(o,x):
    a=o.a;ids=np.flatnonzero(a['plays']>0);owner=np.searchsorted(a['ptr'][:,0,0],ids,side='right')-1;ids=ids[o.w[owner]>0];rates=np.unique(a['plays'][ids]/a['dt'][ids]);near=[]
    for u in o.u:
        if -np.expm1(u*np.log1p(-x[1]))+1e-9>=1:continue
        distance=abs(np.exp(u*np.log1p(-x[1]))-1+np.exp(rates*np.log1p(-x[0]))-1e-9)
        for i in np.argsort(distance)[:2]:
            if distance[i]<1e-4:near.append((float(distance[i]),float(rates[i]),float(u)))
    for _,rate,u in sorted(near)[:4]:
        def expand(z):
            xx=x.copy();xx[1:]=z*m.SCALE[1:];kc=-np.expm1(u*np.log1p(-xx[1]));xx[0]=-np.expm1(np.log(kc+1e-9)/rate);return xx
        def fun(z):
            xx=expand(z);v,g=o(xx);kc=-np.expm1(u*np.log1p(-xx[1]));dk=u*np.exp(u*np.log1p(-xx[1]))/(1-xx[1]);g[1]+=g[0]*(-(1-xx[0])*dk/(rate*(kc+1e-9)));return v,g[1:]*m.SCALE[1:]
        bounds=[(lo/sc,None if hi is None else hi/sc) for (lo,hi),sc in zip(m.BOUNDS[1:],m.SCALE[1:])];bounds[0]=(bounds[0][0],min(m.BOUNDS[1][1],-np.expm1(np.log(1e-9)/u)*(1-1e-10))/m.SCALE[1])
        opt=minimize(fun,x[1:]/m.SCALE[1:],jac=True,bounds=bounds,method='L-BFGS-B',options={'ftol':1e-13,'gtol':1e-8,'maxiter':300,'maxls':50})
        xx=expand(opt.x)
        if not m.BOUNDS[0][0]<=xx[0]<=m.BOUNDS[0][1]:continue
        check=m.boundary_check(o,xx,rate,u)
        if opt.success and check['passed']:return xx,check
    return None

def fit(a,w,label):
    o=m.Objective(a,w);bounds=[(lo/sc,None if hi is None else hi/sc) for (lo,hi),sc in zip(m.BOUNDS,m.SCALE)];begin=time.monotonic()
    def fun(z):v,g=o(z*m.SCALE);return v,g*m.SCALE
    attempts=[]
    for start in m.STARTS[:2]:
        opt=minimize(fun,np.array(start)/m.SCALE,jac=True,method='L-BFGS-B',bounds=bounds,options={'ftol':1e-10,'gtol':1e-7,'maxiter':300,'maxls':40,'maxcor':20});x=opt.x*m.SCALE;v,g=o(x);stationarity=None
        print('CV preliminary',label,'loss',v,'gradient',m.m.active_gradient(x,g),'seconds',round(time.monotonic()-begin),flush=True)
        if m.m.active_gradient(x,g)>=1e-4:
            result=finish(o,x)
            if result is not None:x,stationarity=result;v,g=o(x)
        accepted=bool((opt.success and m.m.active_gradient(x,g)<1e-4) or stationarity and stationarity['passed'])
        attempts.append(dict(wmse=float(v),gradient=m.m.active_gradient(x,g),accepted=accepted))
        if accepted:
            ok=w>0;loss=float(np.average(np.nanmean((a['Y'][ok]-o.pred[ok])**2,axis=1),weights=w[ok]));assert abs(v-loss)<1e-8
            return dict(model='hyperbolic_training7',parameters=dict(zip(m.NAMES,map(float,x))),wmse=float(v),gradient=m.m.active_gradient(x,g),stationarity=stationarity,accepted=True,bound_hits=[m.NAMES[j] for j,(lo,hi) in enumerate(m.BOUNDS) if x[j]-lo<1e-8 or hi is not None and hi-x[j]<1e-8],baseline_GI_coefficient_per15=float(o.eta[0]),reference_coefficients=o.reference.tolist(),nodes=24,loss_audit_error=abs(v-loss),starts=attempts,reference_refit=True,derived=m.derived(x),elapsed_seconds=time.monotonic()-begin)
    raise RuntimeError(attempts)
