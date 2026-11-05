"""High-resolution prediction check for the slowing-decay comparison."""
import numpy as np
from scipy.integrate import quad
import slowing

def integrate_person(a,r,i):
    x=slowing.vector(r);kl,k,A,q,beta,kr=x;lam=-np.log1p(-k)
    def trace(u,j):
        z=0.
        for visit in range(j+1):
            st,en=a['ptr'][i,visit]
            for p,d in zip(a['plays'][st:en],a['dt'][st:en]):
                z=(1-(1-z)*(1-kl)**p)*np.exp(-lam*u*d)
        return np.exp(-u)*z
    out=np.full(4,np.nan);H=0.;maxerr=0.
    t=(a['age'][i]-50)/20;c=r['reference_coefficients'];base=r['baseline_GI_coefficient_per15']*(a['GI0'][i]-(c[0]+c[1]*t+c[2]*t*t))/15
    for j in range(4):
        if not np.isfinite(a['Y'][i,j]):continue
        H=(H+q*np.exp(beta*t))*(1-kr)**a['D'][i,j]
        g,err=quad(trace,0,50,args=(j,),epsabs=1e-10,epsrel=1e-9,limit=150)
        out[j]=A*g+H+base;maxerr=max(maxerr,A*err)
    return out,maxerr
