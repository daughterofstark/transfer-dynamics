"""Frozen census-weighted empirical INT maps. Requires numpy only."""
import numpy as np
from statistics import NormalDist

def fit_map(values, weights):
    x=np.asarray(values,dtype=float);w=np.asarray(weights,dtype=float)
    if len(x)!=len(w) or not len(x) or not np.isfinite(x).all() or not np.isfinite(w).all() or (w<=0).any():
        raise ValueError('Calibration requires finite scores and positive weights')
    u,inv=np.unique(x,return_inverse=True)
    if len(u)<2:raise ValueError('Cannot calibrate a constant metric')
    mass=np.bincount(inv,weights=w);mass/=mass.sum()
    p=np.cumsum(mass)-mass/2
    return {'raw':u.tolist(),'percentile':p.tolist(),'mass':mass.tolist(),
            'n':int(len(x)),'effective_n':float(w.sum()**2/np.square(w).sum())}

def apply_map(values, mapping):
    """Linear interpolation on the empirical CDF; clamp to finite endpoint midranks.

    The exact same raw value always gets the same score. No follow-up distribution,
    age, education or outcome enters application of the frozen map.
    """
    x=np.asarray(values,dtype=float)
    p=np.interp(x,mapping['raw'],mapping['percentile'])
    inverse=NormalDist().inv_cdf
    out=np.fromiter((100+15*inverse(v) if np.isfinite(v) else np.nan for v in p),dtype=float,count=len(p))
    out[~np.isfinite(x)]=np.nan
    return out

def demographic_weights(frame, target):
    keys=list(zip(frame.age_bin,frame.edu_bin))
    counts={key:keys.count(key) for key in set(keys)}
    missing=set(target)-set(counts)
    if missing:raise ValueError(f'Reference has empty demographic cells: {sorted(missing)}')
    return np.array([target[k]/counts[k] for k in keys]),counts
