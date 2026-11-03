"""Reconcile a completed frozen-fit replay with the numerical sources for v23."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];REF=ROOT/'paper/reference'
def read(p):return json.loads(p.read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'outputs');args=p.parse_args();o=args.output
    checks={}
    for dest,ref in [('supplement_table_1.csv','participant_comparison.csv'),('supplement_table_3.csv','participant_flow.csv'),('supplement_table_3_later_followup.csv','retained_followup_truncation.csv')]:
        pd.testing.assert_frame_equal(pd.read_csv(o/'tables'/dest),pd.read_csv(REF/ref));checks[dest]='exact'
    for name in ['figure2_visits.csv','figure2_dose_response.csv','figure2_time_comparison.csv']:
        old=pd.read_csv(REF/'figure_data'/name);new=pd.read_csv(o/'figure_data'/name)
        cols=list(new.select_dtypes(include='number').columns)
        np.testing.assert_allclose(new[cols],old[cols],atol=1e-10,rtol=0)
        checks[name]=float(np.max(abs(new[cols].to_numpy()-old[cols].to_numpy())))
    w=read(o/'tables/within_person.json');old=read(REF/'within_person.json')
    for kind in ['basic','adjusted']:
        for k,v in w[kind]['coefficients'].items():
            np.testing.assert_allclose([v['estimate'],v['se'],*v['ci95']],[old[kind]['coefficients'][k]['estimate'],old[kind]['coefficients'][k]['se'],*old[kind]['coefficients'][k]['ci95']],atol=1e-10,rtol=0)
    checks['within_person']='matches coefficients and cluster uncertainty'
    expected=dict(primary=6.890850763960274,saturating=6.890850762956193,mean_change=7.0323795907392395,retest_only=6.972689529274483,no_forgetting=6.9196135948213415,static_dose_response=6.916924694281484,drift=6.888298356055407,slowing=6.890548186296809)
    metrics=read(o/'prediction_metrics.json')
    for kind,v in metrics.items():assert abs(v['rmse']-expected[kind])<1e-10,(kind,v)
    checks['heldout_RMSE']='matches to 1e-10 GI points'
    effect=read(o/'tables/effect_size.json');assert abs(effect['GI_difference']['estimate']-3.1999408)<1e-5
    slow=read(o/'tables/slowing_400.json');assert abs(slow['slowing']['half_retention_days']-152)<1
    booster=read(o/'figures/booster_comparison.json');old=read(REF/'booster_comparison.json')
    errors=[]
    for k in ['steady','booster','stop']:
        for metric in ['day360','mean_days91_360']:
            for key in ['estimate','CI']:
                error=float(np.max(abs(np.asarray(booster[metric][k][key])-np.asarray(old[metric][k][key]))));errors.append(error);assert error<1e-4
    checks['booster_max_difference']=max(errors)
    checks['model_count_totals']=read(o/'tables/cohort.json')
    (o/'paper_output_reconciliation.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
