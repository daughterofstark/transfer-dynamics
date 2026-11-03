"""Reproducible fitting, saved-fit audit, and reporting orchestration."""
from pathlib import Path
import os,json,sys,hashlib,subprocess,platform
from concurrent.futures import ProcessPoolExecutor,as_completed
import multiprocessing as mp
import numpy as np
import model as m
import fitting as f
from inputs import load_model,counts,sha256
ROOT=Path(__file__).resolve().parents[2];REF=ROOT/'paper/reference'
PREFIX={'primary':'constant7','saturating':'saturating8','drift':'drift','slowing':'slowing'}
BENCHMARKS=['mean_change','retest_only','no_forgetting','static_dose_response']

def read(path):return json.loads(Path(path).read_text())
def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');tmp.replace(path)
def files_for(model):
    p=PREFIX[model]
    if model in ['primary','saturating']:return p+'_point.json',p+'_cv_fits.json',p+'_bootstrap.json'
    if model=='drift':return 'drift_point_fit.json','drift_cv_fits.json','drift_bootstrap_records.json'
    return 'slowing_point.json','slowing_cv.json',None

def manifest(args):
    sources=sorted((ROOT/'paper/analysis').glob('*.py'))+sorted((ROOT/'paper/analysis').glob('*.c'))+[ROOT/'reproduce.py',ROOT/'paper/specification/bootstrap_seeds.json']
    return dict(input_sha256=sha256(args.input),selection_sha256=sha256(args.selection) if args.selection.exists() else None,
        source_sha256={str(p.relative_to(ROOT)):sha256(p) for p in sources},python=platform.python_version(),
        versions={name:__import__(name).__version__ for name in ['numpy','scipy','pandas']},fold_seed=291029)

def validate(args):
    a=load_model(args.input);got=counts(a);expected=read(ROOT/'paper/specification/inputs.json')
    assert sha256(args.input)==expected['timing_input.npz']['sha256'],'Not the frozen paper input'
    if args.selection.exists():assert sha256(args.selection)==expected['selection_input.npz']['sha256']
    assert all(got[k]==expected['cohort'][k] for k in ['participants','test_timepoints','intervals','gameplays','visit_counts'])
    save(args.output/'input_validation.json',got);save(args.output/'run_manifest.json',manifest(args));print('Inputs validated:',got,flush=True)

def benchmark_predict(a,r,kind):
    import benchmarks as b
    aa=f.center(a,r['reference_coefficients']);z=(aa['GI0']-100)/15
    if kind=='mean_change':
        p=r['parameters'];pr=np.broadcast_to((p['mean']+p['baseline_GI_coefficient_per15']*z)[:,None],a['Y'].shape).copy()
    else:
        o=b.Objective(aa,np.ones(len(z)),kind,baseline=True)
        x=np.array([r['parameters'][k] for k in o.names]);pr=o.predict(x)[0]+r['baseline_GI_coefficient_per15']*z[:,None]
    pr[~np.isfinite(a['Y'])]=np.nan;return pr

def predict(a,r,kind,adaptive=False):
    if kind in ['primary','saturating']:return f.predict(a,r)
    if kind=='drift':
        import drift
        return drift.predict(a,r)
    if kind=='slowing':
        import slowing,slowing_adaptive
        pr=slowing.predict(a,r,nodes=128 if adaptive else None)
        if adaptive:
            # Preserve global ordered segment pointers when finding owners.
            for i in slowing_adaptive.affected(a,r):
                pr[i],err=slowing_adaptive.integrate_person(a,r,int(i));assert err<2e-6
        return pr
    return benchmark_predict(a,r,kind)

def rmse(a,p,w=None):
    assert np.array_equal(np.isfinite(a['Y']),np.isfinite(p))
    return float(np.sqrt(np.average(np.nanmean((a['Y']-p)**2,axis=1),weights=w)))

def replay(args):
    a=load_model(args.input);n=len(a['age']);fold=f.folds(n);source=args.results or REF
    kinds=['primary','saturating',*BENCHMARKS]+(['drift','slowing'] if args.comparisons else [])
    metrics={};checks=[]
    for kind in kinds:
        if kind in BENCHMARKS:
            rows=[r for r in read(source/'benchmark_cv_fits.json') if r['model']==kind]
            point=read(source/'benchmark_point_fits.json')[kind]
        else:
            p,c,_=files_for(kind);point=read(source/p);rows=read(source/c)
        assert sorted(r['fold'] for r in rows)==list(range(5)),f'{kind}: need all five folds'
        pred=np.full_like(a['Y'],np.nan);fm=[]
        for row in rows:
            k=row['fold'];fit=row['fit'];w=(fold!=k).astype(float)
            np.testing.assert_allclose(f.reference(a,w),fit['reference_coefficients'],atol=1e-10,rtol=0)
            pr=predict(a,fit,kind,adaptive=False)
            if kind=='slowing':
                import slowing,slowing_adaptive
                pr=slowing.predict(a,fit,nodes=128)
                ids=slowing_adaptive.affected(a,fit);ids=ids[fold[ids]==k]
                for i in ids:
                    pr[i],err=slowing_adaptive.integrate_person(a,fit,int(i));assert err<2e-6
                print('Slowing adaptive fold',k,'participants',len(ids),flush=True)
            pred[fold==k]=pr[fold==k]
            sm=m.subset(a,np.flatnonzero(fold==k)[:30]);p1=predict(sm,fit,kind)
            sm['Y']=sm['Y']+37.;p2=predict(sm,fit,kind)
            perturb=float(np.nanmax(abs(p1-p2)));assert perturb<1e-8
            fm.append(dict(fold=k,rmse=rmse(m.subset(a,np.flatnonzero(fold==k)),pr[fold==k]),heldout_outcome_perturbation_error=perturb))
        metrics[kind]=dict(rmse=rmse(a,pred),folds=fm)
        (args.output/'predictions').mkdir(exist_ok=True);np.save(args.output/'predictions'/f'{kind}_cv.npy',pred)
        if kind in ['primary','saturating','drift']:
            obj=m.Objective(f.center(a,point['reference_coefficients']),np.ones(n)) if kind!='drift' else __import__('drift').Objective(a,np.ones(n))
            loss,_=obj(m.vector(point));err=abs(loss-point['wmse']);assert err<1e-7
            checks.append(dict(model=kind,full_sample_loss_error=err))
        print('Replayed',kind,'RMSE',metrics[kind]['rmse'],flush=True)
    if args.audit_bootstrap:
        seeds=read(ROOT/'paper/specification/bootstrap_seeds.json')
        for kind in ['primary','saturating']+(['drift'] if args.comparisons else []):
            rows=read(source/files_for(kind)[2]);num=200 if kind=='drift' else 500
            assert len(rows)==num and sorted(r['draw'] for r in rows)==sorted(s['draw'] for s in seeds[:num])
            errors=[];boundary_count=0
            for row in sorted(rows,key=lambda x:x['draw']):
                assert row['seed']==next(s['seed'] for s in seeds if s['draw']==row['draw'])
                fit=row['fit'];w=np.bincount(np.random.default_rng(row['seed']).integers(n,size=n),minlength=n).astype(float)
                coef=f.reference(a,w);np.testing.assert_allclose(coef,fit['reference_coefficients'],atol=1e-10,rtol=0)
                o=m.Objective(f.center(a,coef),w) if kind!='drift' else __import__('drift').Objective(a,w)
                x=m.vector(fit);loss,g=o(x);error=abs(loss-fit['wmse']);assert error<1e-7;errors.append(error)
                fixed={} if kind=='saturating' else {6:0.}
                if m.active_gradient(x,g,fixed=fixed)>=1e-4:
                    assert fit['stationarity'];check=m.boundary_check(o,x,fit['stationarity']['boundary_gameplays_per_day'],fixed);assert check['passed'];boundary_count+=1
                if len(errors)%100==0:print(kind,'bootstrap audited',len(errors),flush=True)
            checks.append(dict(model=kind,bootstrap_audited=len(errors),max_loss_error=max(errors),boundary_stationarity_checks=boundary_count,new_bootstrap_fits=0))
    save(args.output/'prediction_metrics.json',metrics);save(args.output/'replay_audit.json',checks)
    record=manifest(args)
    record['fit_files_sha256']={p.name:sha256(p) for p in sorted(source.glob('*.json'))}
    save(args.output/'replay_manifest.json',record)

def init_worker(input_path):
    global A
    A=load_model(input_path)

def fit_one(task):
    kind,phase,index,seed,point=task;n=len(A['age'])
    w=np.ones(n) if phase=='point' else (f.folds(n)!=index).astype(float) if phase=='cv' else np.bincount(np.random.default_rng(seed).integers(n,size=n),minlength=n).astype(float)
    if kind in ['primary','saturating']:
        starts=f.starts()
        if phase=='bootstrap':starts=[m.vector(point),f.starts()[0]]
        try:r=f.fitted(A,w,PREFIX[kind],starts)
        except AssertionError:
            if phase!='bootstrap':raise
            r=f.fitted(A,w,PREFIX[kind],f.starts());r['additional_starts_required']=True
    elif kind=='drift':
        import drift
        starts=f.starts() if phase!='bootstrap' else [m.vector(point),f.starts()[0]]
        r=drift.fitted(A,w,starts)
    elif kind=='slowing':
        import slowing,slowing_fit
        if phase=='bootstrap':raise ValueError('No slowing-decay bootstrap in the paper')
        r=slowing.fit(A,w,nodes=48) if phase=='point' else slowing_fit.fit(A,w,index)
    else:
        import benchmarks
        coef=f.reference(A,w);r,_=benchmarks.fit(f.center(A,coef),w,kind,baseline=True);r['reference_coefficients']=coef.tolist()
    return r if phase=='point' else dict(fold=index,fit=r) if phase=='cv' else dict(draw=index,seed=seed,fit=r)

def refit(args):
    if args.workers<1:raise ValueError('workers must be positive')
    kind=args.model;phase=args.phase;out=args.output/'fits';out.mkdir(exist_ok=True)
    # A changed code/input invalidates resume; never mix runs silently.
    current=manifest(args);mpath=out/'manifest.json'
    if mpath.exists():assert read(mpath)==current,'Code, inputs or runtime changed: use a new output directory'
    else:save(mpath,current)
    if kind=='benchmarks' and phase=='bootstrap':raise ValueError('Benchmarks have no bootstrap in this paper')
    if kind=='slowing' and phase=='bootstrap':raise ValueError('Slowing decay has no bootstrap in this paper')
    kinds=BENCHMARKS if kind=='benchmarks' else [kind]
    for k in kinds:
        if kind=='benchmarks':filename='benchmark_point_fits.json' if phase=='point' else 'benchmark_cv_fits.json'
        else:filename=files_for(k)[['point','cv','bootstrap'].index(phase)]
        path=out/filename
        point=None
        if phase=='bootstrap':
            point=read(out/files_for(k)[0]);total=200 if k=='drift' else 500
            draws=total if args.draws is None else args.draws
            if not 1<=draws<=total:raise ValueError(f'draws must be 1..{total}')
            seeds=read(ROOT/'paper/specification/bootstrap_seeds.json')[:draws]
            jobs=[(k,phase,s['draw'],s['seed'],point) for s in seeds]
        elif phase=='cv':jobs=[(k,phase,i,None,None) for i in ([args.fold] if args.fold is not None else range(5))]
        else:jobs=[(k,phase,None,None,None)]
        rows=read(path) if path.exists() else ({} if phase=='point' and kind=='benchmarks' else [])
        if phase!='point':
            key='draw' if phase=='bootstrap' else 'fold'
            done={r[key] for r in rows if kind!='benchmarks' or r['model']==k}
            assert len(done)==len([r for r in rows if kind!='benchmarks' or r['model']==k]),'Duplicate records'
            jobs=[j for j in jobs if j[2] not in done]
        if not jobs:continue
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context('spawn'),initializer=init_worker,initargs=(str(args.input),)) as pool:
            for future in as_completed([pool.submit(fit_one,j) for j in jobs]):
                r=future.result()
                if phase=='point':
                    if kind=='benchmarks':rows[k]=r
                    else:rows=r
                else:
                    if kind=='benchmarks':r['model']=k
                    rows.append(r);rows.sort(key=lambda r:(r.get('model',''),r[key]))
                save(path,rows);print('Completed',k,phase,r.get('draw',r.get('fold','full sample')),flush=True)
    print('Fit files:',out,flush=True)

def report(args):
    import reporting
    reporting.run(args)

def figures(args):
    out=args.output/'figures';out.mkdir(exist_ok=True)
    data=args.output/'figure_data';data.mkdir(exist_ok=True)
    source=args.results or REF
    import shutil
    for name in ['constant7_point.json','constant7_bootstrap.json']:shutil.copy2(source/name,data/name)
    for n in range(1,5):
        subprocess.run([sys.executable,str(ROOT/f'paper/manuscript/figures/src/figure_{n}.py')],check=True)
    print('Figures:',out,flush=True)
