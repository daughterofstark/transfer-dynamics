from pathlib import Path
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import json,numpy as np,pandas as pd
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent

def panel_fit(y,X,names,valid):
    n=valid.sum(1);keep=n>=2;y=y[keep];X=X[keep];valid=valid[keep];n=n[keep]
    ym=np.sum(np.where(valid,y,0),axis=1)/n
    xm=np.sum(np.where(valid[:,:,None],X,0),axis=1)/n[:,None]
    yy=(y-ym[:,None])[valid];xx=(X-xm[:,None,:])[valid]
    ids=np.broadcast_to(np.arange(len(n))[:,None],valid.shape)[valid]
    w=(np.ones(valid.shape)/n[:,None])[valid]
    H=xx.T@(w[:,None]*xx);rhs=xx.T@(w*yy)
    assert np.linalg.matrix_rank(H)==len(names)
    b=np.linalg.solve(H,rhs);res=yy-xx@b
    scores=np.zeros((len(n),len(names)));np.add.at(scores,ids,xx*(w*res)[:,None])
    bread=np.linalg.inv(H);cov=bread@(scores.T@scores)@bread*len(n)/(len(n)-1);se=np.sqrt(np.diag(cov))
    return dict(participants=len(n),intervals=len(yy),equal_total_weight_per_participant=True,
        cluster='participant',uncertainty='Asymptotic cluster-sandwich, G/(G-1) correction',
        weighted_within_R2=float(1-np.sum(w*res**2)/np.sum(w*yy**2)),
        condition_number=float(np.linalg.cond(H)),
        coefficients={k:dict(estimate=float(b[j]),se=float(se[j]),ci95=[float(b[j]-1.96*se[j]),float(b[j]+1.96*se[j])]) for j,k in enumerate(names)},
        one_to_three_games_per_day_association_GI=float(b[0]*np.log(2)),
        one_to_three_games_per_day_ci95=[float((b[0]-1.96*se[0])*np.log(2)),float((b[0]+1.96*se[0])*np.log(2))])
