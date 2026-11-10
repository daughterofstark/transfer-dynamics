"""Reconcile a fresh saved-fit replay with the frozen manuscript summaries."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];REF=ROOT/'paper/reference'
def read(p):return json.loads(p.read_text())
def compare(actual,expected,path=''):
    if isinstance(expected,dict):
        assert set(actual)==set(expected),path
        for k in expected:compare(actual[k],expected[k],path+'/'+k)
    elif isinstance(expected,list):
        assert len(actual)==len(expected),path
        for i,(a,e) in enumerate(zip(actual,expected)):compare(a,e,path+f'/{i}')
    elif isinstance(expected,(float,int)) and not isinstance(expected,bool):
        np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-9,err_msg=path)
    else:assert actual==expected,(path,actual,expected)
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'outputs');o=p.parse_args().output
    checks={}
    for old in sorted((REF/'tables').iterdir()):
        new=o/'tables'/old.name
        if old.suffix=='.csv':pd.testing.assert_frame_equal(pd.read_csv(new),pd.read_csv(old),check_exact=False,atol=1e-9,rtol=0)
        elif old.suffix=='.json':compare(read(new),read(old),old.name)
        else:continue
        checks['tables/'+old.name]='matches'
    for old in sorted((REF/'figure_data').glob('*.csv')):
        pd.testing.assert_frame_equal(pd.read_csv(o/'figure_data'/old.name),pd.read_csv(old),check_exact=False,atol=1e-9,rtol=0)
        checks['figure_data/'+old.name]='matches'
    compare(read(o/'prediction_metrics.json'),read(REF/'prediction_metrics.json'),'prediction_metrics')
    checks['heldout_predictions']='all models and folds match'
    for name in ['booster_comparison.json','supplementary_schedule_comparison.json']:
        compare(read(o/'figures'/name),read(REF/name),name);checks[name]='all summaries match'
    for name in ['Figure_1','Figure_2','Figure_3','Figure_4','Supplementary_Figure_1']:
        for ext in ['png','svg']:assert (o/'figures'/f'{name}.{ext}').stat().st_size>1000
    checks['figures']='all five PNG/SVG exports present'
    (o/'paper_output_reconciliation.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
