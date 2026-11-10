"""Rebuild Tables S1/S3 from aggregate statistics; no participant records."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

def baseline_summary(moments, coefficients):
    """Mean/SD of GI-c0-c1*t-c2*t² from group mean and sample covariance."""
    c0,c1,c2=coefficients
    w=np.array([1.,-c1,-c2])
    mean=float(w@np.asarray(moments['mean'])-c0)
    variance=float(w@np.asarray(moments['sample_covariance'])@w)
    assert variance>=-1e-10
    return mean,float(np.sqrt(max(0.,variance)))

def selections(path,out,point):
    a=json.loads(Path(path).read_text());assert a['schema_version']==1
    groups=a['groups'];counts=a['selection_counts'];rows=[]
    def add(label,fn):rows.append({'Characteristic':label,**{k:fn(d) for k,d in groups.items()}})
    def ms(v):return f'{v[0]:.2f} ({v[1]:.2f})'
    def med(q):return f'{q["median"]:.1f} [{q["q25"]:.1f}, {q["q75"]:.1f}]'
    add('Participants, n',lambda d:f'{d["n"]:,}')
    for field,label in [('age_t1','Age at T1, mean (SD), years'),('grand_index','GI at T1, mean (SD)')]:
        add(label,lambda d,k=field:ms((d['mean_sd'][k]['mean'],d['mean_sd'][k]['sd'])))
    add('Age-referenced baseline GI, mean (SD)',lambda d:ms(baseline_summary(d['baseline_age_moments'],point['reference_coefficients'])))
    for field,label in [('plays_before','Gameplays before T1, median [IQR]'),('days_signup_to_t1','Days from signup to T1, median [IQR]')]:
        add(label,lambda d,k=field:med(d['quantiles'][k]))
    for label in ['Female','Male','Gender not reported','High school or less','Some college or undergraduate degree','Professional or graduate education','Other education','Education not reported']:
        add(f'{label}, n (%)',lambda d,k=label:f'{d["category_counts"][k]:,} ({100*d["category_counts"][k]/d["n"]:.1f}%)')
    pd.DataFrame(rows).to_csv(out/'supplement_table_1.csv',index=False)
    remaining=counts['returned']
    flow=[dict(stage='Baseline-eligible users in the comparison table',excluded=0,remaining=counts['baseline_eligible']),
          dict(stage='No subsequent recorded NCPT test',excluded=counts['baseline_eligible']-remaining,remaining=remaining)]
    codes=['battery_change','subtest_composition','invalid_GI','gameplay_rate','four_SD']
    labels=['Different battery at the second test','Required subtests missing at the second test','No valid second-test GI despite the required subtests being present','First interval exceeded 20 gameplays per (calendar-day difference + 1)','Second-test GI or first-interval GI change outside the frozen four-SD bounds']
    for code,label in zip(codes,labels):
        k=counts['first_failure'][code];remaining-=k;flow.append(dict(stage=label,excluded=k,remaining=remaining))
    assert remaining==counts['included']
    flow.append(dict(stage='Final model cohort',excluded=0,remaining=remaining))
    pd.DataFrame(flow).to_csv(out/'supplement_table_3.csv',index=False)
    later=[dict(reason=k,retained_participants_with_followup_ending=counts['later_failure'][k]['participants'],recorded_visits_omitted_within_first_five=counts['later_failure'][k]['omitted_visits']) for k in codes]
    pd.DataFrame(later).to_csv(out/'supplement_table_3_later_followup.csv',index=False)
