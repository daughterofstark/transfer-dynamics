"""Generate numerical manuscript tables and plotting data, never edit prose."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import model as m
import fitting as f
from inputs import load_model,counts
from workflow import REF,ROOT,read,save,files_for

def csv(out,name,rows):pd.DataFrame(rows).to_csv(out/name,index=False)
def interval(x):return np.percentile(x,[2.5,97.5]).tolist()
def stat(point,values):return dict(estimate=float(point),CI=interval(values))

def selections(path,out,point):
    with np.load(path,allow_pickle=False) as z:b=pd.DataFrame(dict(z))
    b['gender']=b.gender.replace('',np.nan)
    t=(b.age_t1-50)/20;c=point['reference_coefficients'];b['age_referenced_baseline_GI']=b.grand_index-(c[0]+c[1]*t+c[2]*t*t)
    cols={'T1 only':b[~b.returned],'Returned for testing (any battery)':b[b.returned],'Included in model (subset of repeat testers)':b[b.in_analysis]}
    rows=[]
    def add(label,fn):rows.append({'Characteristic':label,**{k:fn(v) for k,v in cols.items()}})
    def ms(v):return f'{v.mean():.2f} ({v.std(ddof=1):.2f})'
    def med(v):return f'{v.median():.1f} [{v.quantile(.25):.1f}, {v.quantile(.75):.1f}]'
    def pct(mask):return f'{int(mask.sum()):,} ({100*mask.mean():.1f}%)'
    add('Participants, n',lambda d:f'{len(d):,}')
    for field,label in [('age_t1','Age at T1, mean (SD), years'),('grand_index','GI at T1, mean (SD)'),('age_referenced_baseline_GI','Age-referenced baseline GI, mean (SD)')]:add(label,lambda d,k=field:ms(d[k]))
    for field,label in [('plays_before','Gameplays before T1, median [IQR]'),('days_signup_to_t1','Days from signup to T1, median [IQR]')]:add(label,lambda d,k=field:med(d[k]))
    for label,v in [('Female','f'),('Male','m')]:add(f'{label}, n (%)',lambda d,v=v:pct(d.gender.eq(v)))
    add('Gender not reported, n (%)',lambda d:pct(d.gender.isna()))
    for label,values in [('High school or less',[1,2]),('Some college or undergraduate degree',[3,4,8]),('Professional or graduate education',[5,6,7]),('Other education',[99])]:add(f'{label}, n (%)',lambda d,v=values:pct(d.education_level.isin(v)))
    add('Education not reported, n (%)',lambda d:pct(d.education_level.isna()))
    csv(out,'supplement_table_1.csv',rows)
    # The failure labels were established upstream; this table counts them.
    remaining=int(b.returned.sum())
    flow=[dict(stage='Baseline-eligible users in the comparison table',excluded=0,remaining=len(b)),dict(stage='No subsequent recorded NCPT test',excluded=int((~b.returned).sum()),remaining=remaining)]
    codes=['battery_change','subtest_composition','invalid_GI','gameplay_rate','four_SD']
    labels=['Different battery at the second test','Required subtests missing at the second test','No valid second-test GI despite the required subtests being present','First interval exceeded 20 gameplays per (calendar-day difference + 1)','Second-test GI or first-interval GI change outside the frozen four-SD bounds']
    for code,label in zip(codes,labels):
        k=int(b.first_failure.eq(code).sum());remaining-=k;flow.append(dict(stage=label,excluded=k,remaining=remaining))
    assert remaining==int(b.in_analysis.sum())
    assert ((b.returned&b.first_failure.eq(''))==b.in_analysis).all()
    flow.append(dict(stage='Final model cohort',excluded=0,remaining=remaining));csv(out,'supplement_table_3.csv',flow)
    later=[]
    for code in codes:
        q=b[b.later_failure.eq(code)];assert q.in_analysis.all()
        later.append(dict(reason=code,retained_participants_with_followup_ending=len(q),recorded_visits_omitted_within_first_five=int(q.omitted_visits.sum())))
    csv(out,'supplement_table_3_later_followup.csv',later)

def within(a):
    from within_person import panel_fit
    y=a['Y'];n=len(y);v=np.isfinite(y);occasion=np.broadcast_to(np.arange(4),y.shape)
    inc=y-np.column_stack([np.zeros(n),y[:,:-1]]);rate=a['P']/(a['D']+1)
    col=[np.log1p(rate)];names=['log1p_training_rate']
    for j in [1,2,3]:col.append((occasion==j).astype(float));names.append(f'T{j+2}')
    basic=panel_fit(inc,np.stack(col,axis=-1),names,v)
    l=np.log1p(a['D_exact'])/5;prior=np.cumsum(np.nan_to_num(a['P']),axis=1)-np.nan_to_num(a['P'])
    col.extend([l,l*l,np.log1p(prior)/5]);names.extend(['log1p_days_over5','squared_log_days','log1p_prior_gameplays_over5'])
    for label,z in [('age20',(a['age']-50)/20),('baselineGI15',(a['GI0']-100)/15)]:
        for j in [1,2,3]:col.append(z[:,None]*(occasion==j));names.append(f'{label}_by_T{j+2}')
    return dict(basic=basic,adjusted=panel_fit(inc,np.stack(col,axis=-1),names,v))

def figure_data(a,p,output):
    output.mkdir(exist_ok=True);y=a['Y'];n=len(y);v=np.isfinite(y)
    rows=[dict(visit=1,n=n,observed=0.,predicted=0.,se=0.)]
    for j in range(4):
        z=y[v[:,j],j];pr=p[v[:,j],j];rows.append(dict(visit=j+2,n=len(z),observed=z.mean(),predicted=pr.mean(),se=z.std(ddof=1)/np.sqrt(len(z))))
    csv(output,'figure2_visits.csv',rows)
    first=pd.DataFrame(dict(games=a['P'][:,0],days=a['D_exact'][:,0],observed=y[:,0],predicted=p[:,0]))
    first['dose_bin']=pd.qcut(first.games,20,duplicates='drop');rows=[]
    for _,z in first.groupby('dose_bin',observed=True):rows.append(dict(n=len(z),games_mean=z.games.mean(),games_median=z.games.median(),games_min=z.games.min(),games_max=z.games.max(),observed=z.observed.mean(),predicted=z.predicted.mean(),se=z.observed.std(ddof=1)/np.sqrt(len(z)),median_days=z.days.median()))
    csv(output,'figure2_dose_response.csv',rows)
    z=first[first.games.between(300,500)].copy();z['time_bin']=pd.cut(z.days,[0,100,150,240,365,730,1460,np.inf],include_lowest=True)
    t=z.groupby('time_bin',observed=True).agg(n=('games','size'),days=('days','mean'),games=('games','mean'),observed=('observed','mean'),predicted=('predicted','mean'),sd=('observed','std')).reset_index()
    t['se']=t.sd/np.sqrt(t.n);t['months']=t.days/(365.25/12);t.to_csv(output/'figure2_time_comparison.csv',index=False)

def run(args):
    a=load_model(args.input);source=args.results or REF;out=args.output/'tables';out.mkdir(exist_ok=True)
    point=read(source/'constant7_point.json');boots=read(source/'constant7_bootstrap.json')
    assert len(boots)==500,'Full 500 primary draws required for paper reporting'
    x=m.vector(point);xx=np.array([m.vector(b['fit']) for b in boots]);stats=counts(a)
    save(out/'cohort.json',stats)
    names=m.NAMES[:6]+['baseline_GI_coefficient_per15'];mat=np.column_stack([xx[:,:6],[b['fit']['baseline_GI_coefficient_per15'] for b in boots]])
    rows=[]
    for name,j,group in [('baseline_GI_coefficient_per15',6,'General'),('game_ceiling_GI',2,'Cognitive training'),('learning_per_game',0,'Cognitive training'),('training_forgetting_per_day',1,'Cognitive training'),('test_increment_age50_GI',3,'Retest'),('age_beta_per20',4,'Retest'),('retest_forgetting_per_day',5,'Retest')]:
        value=point[name] if j==6 else x[j];lo,hi=interval(mat[:,j]);rows.append(dict(group=group,quantity=name,estimate=value,low=lo,high=hi,derived=False))
        if j in [1,5]:
            lo,hi=interval(np.log(.5)/np.log1p(-xx[:,j]));rows.append(dict(group=group,quantity='training_half_life_days' if j==1 else 'retest_half_life_days',estimate=m.half(x[j]),low=lo,high=hi,derived=True))
    csv(out,'table_1.csv',rows)
    pd.DataFrame(mat,columns=names).corr().to_csv(out/'supplement_table_6.csv')
    cc=np.array([b['fit']['reference_coefficients'] for b in boots]);save(out/'age_reference.json',dict(coefficients=[stat(v,cc[:,j]) for j,v in enumerate(point['reference_coefficients'])],log_half_life_correlation=float(np.corrcoef(np.log(np.log(.5)/np.log1p(-xx[:,1])),np.log(np.log(.5)/np.log1p(-xx[:,5])))[0,1])))
    derived=[m.derived(v) for v in xx];save(out/'maintenance.json',{key:stat(value,[v[key] for v in derived]) for key,value in m.derived(x).items() if value is not None})
    defs=read(ROOT/'paper/specification/battery_summary.json');rows=[]
    for d in defs:
        mask=a['battery']==d['battery_id'];rows.append(dict(**d,model_participants=int(mask.sum()),model_completions=int(mask.sum()+np.isfinite(a['Y'][mask]).sum())))
    csv(out,'supplement_table_2.csv',rows)
    if not args.selection.exists():raise FileNotFoundError('selection_input.npz is required for Tables S1/S3')
    selections(args.selection,out,point)
    save(out/'within_person.json',within(a))
    metrics=read(args.output/'prediction_metrics.json')
    csv(out,'supplement_table_4.csv',[dict(model=k,heldout_RMSE=metrics[k]['rmse']) for k in ['mean_change','retest_only','no_forgetting','static_dose_response','primary']])
    import simulations
    simulations.run(source,out,stats)
    comparison=[]
    for kind in ['primary','saturating','drift','slowing']:
        pf,_,bf=files_for(kind);pt=read(source/pf);bs=read(source/bf) if bf else []
        for key in ['training_half_life_days','retest_half_life_days','dose_80_games_day','dose_3GI_games_day']:
            value=pt['derived'].get(key)
            if kind=='slowing' and key=='training_half_life_days':value=read(out/'slowing_400.json')['slowing']['half_retention_days']
            vals=[b['fit']['derived'].get(key) for b in bs]
            lo,hi=interval(vals) if vals and None not in vals else [None,None]
            comparison.append(dict(model=kind,quantity=key,estimate=value,low=lo,high=hi,report_as_bound=kind=='drift' and key=='retest_half_life_days'))
        comparison.append(dict(model=kind,quantity='heldout_RMSE',estimate=metrics.get(kind,{}).get('rmse'),low=None,high=None,report_as_bound=False))
    csv(out,'supplement_table_5.csv',comparison)
    sat=read(source/'saturating8_bootstrap.json');assert len(sat)==500
    alpha=np.array([b['fit']['parameters']['test_diminishing_fraction'] for b in sat]);save(out/'retest_saturation.json',dict(estimate=read(source/'saturating8_point.json')['parameters']['test_diminishing_fraction'],CI=interval(alpha),zero=int((alpha<=1e-8).sum()),max=float(alpha.max())))
    p=np.load(args.output/'predictions/primary_cv.npy');figure_data(a,p,args.output/'figure_data')
    print('Numerical tables and plotting data:',out,flush=True)
