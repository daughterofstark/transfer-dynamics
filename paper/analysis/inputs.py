"""Load anonymous analysis arrays; validate before passing pointers to C."""
from pathlib import Path
import os, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
KEYS={'Y','P','D','D_exact','age','GI0','battery','ptr','dt','plays'}

def sha256(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load_model(path=None):
    path=Path(path or os.environ.get('CT_INPUT',ROOT/'data/timing_input.npz'))
    with np.load(path,allow_pickle=False) as z:
        if set(z.files)!=KEYS:raise ValueError(f'Unexpected model fields: {set(z.files)^KEYS}')
        a={k:np.ascontiguousarray(z[k],dtype=np.int64 if k in ['ptr','battery'] else np.float64) for k in KEYS}
    n=len(a['age']);shape=(n,4);v=np.isfinite(a['Y'])
    assert n>0 and all(a[k].shape==shape for k in ['Y','P','D','D_exact'])
    assert a['ptr'].shape==(n,4,2)
    assert all(a[k].shape==(n,) for k in ['age','GI0','battery'])
    assert a['dt'].ndim==a['plays'].ndim==1 and len(a['dt'])==len(a['plays'])
    assert v[:,0].all() and not np.any(np.diff(v.astype(int),axis=1)>0),'Follow-ups must be a consecutive prefix'
    assert np.all((a['age']>=18)&(a['age']<90)) and np.isfinite(a['GI0']).all()
    assert np.isin(a['battery'],[17,32,39,50,60]).all()
    for k in ['P','D','D_exact']:assert np.array_equal(np.isfinite(a[k]),v),k
    assert (a['P'][v]>=0).all() and (a['D'][v]>=0).all() and (a['D_exact'][v]>0).all()
    assert (a['P'][v]<=20*(a['D'][v]+1)).all()
    assert np.isfinite(a['dt']).all() and (a['dt']>0).all()
    assert np.isfinite(a['plays']).all() and (a['plays']>=0).all()
    starts=a['ptr'][v,0];ends=a['ptr'][v,1]
    assert starts[0]==0 and ends[-1]==len(a['dt'])
    assert (ends>starts).all() and np.array_equal(starts[1:],ends[:-1]),'Segments must be contiguous and ordered'
    # Interval reconciliation without a cancellation-prone global prefix sum.
    np.testing.assert_allclose(np.add.reduceat(a['dt'],starts),a['D_exact'][v],atol=1e-7,rtol=1e-10)
    np.testing.assert_allclose(np.add.reduceat(a['plays'],starts),a['P'][v],atol=1e-8,rtol=0)
    gi=a['GI0'][:,None]+a['Y'];change=a['Y']-np.column_stack([np.zeros(n),a['Y'][:,:-1]])
    assert ((a['GI0']>=40)&(a['GI0']<=160)).all()
    assert ((gi[v]>=40)&(gi[v]<=160)).all()
    assert ((change[v]>=-26.59388096492413)&(change[v]<=32.36921748058884)).all()
    return a

def counts(a):
    v=np.isfinite(a['Y']);n=len(a['age'])
    return dict(participants=n,test_timepoints=int(n+v.sum()),intervals=int(v.sum()),
        gameplays=int(np.nansum(a['P'])),visit_counts=[n,*v.sum(0).tolist()],
        baseline_SD=float(a['GI0'].std(ddof=1)),change_SD=float(a['Y'][:,0].std(ddof=1)))
