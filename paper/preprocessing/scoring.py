"""Scoring primitives used upstream; see docs/data_preparation.md."""
import csv
import numpy as np
def num(x):
    try:return float(x) if x is not None else np.nan
    except (ValueError,TypeError):return np.nan

def span_metrics(text):
    if not isinstance(text,str) or '/' not in text:return {}
    lines=text.split('/');header=lines[0].split(',')
    required=['span','letters_correct','sum_correct']
    if not all(k in header for k in required):return {'cs_bad_log':1}
    rows=list(csv.DictReader(lines))
    if not rows:return {'cs_bad_log':1}
    valid=all(num(r.get('span'))>=4 and r.get('letters_correct') in ['T','F'] and r.get('sum_correct') in ['T','F'] for r in rows)
    if not valid:return {'cs_bad_log':1}
    spans=[num(r['span']) for r in rows]
    success=[num(r['span']) for r in rows if r['letters_correct']=='T' and r['sum_correct']=='T']
    return {'cs_bad_log':0,'cs_trials':len(rows),'cs_fully_correct':len(success),
        'cs_max_attempted':max(spans),'cs_max_success':max(success,default=0),
        'cs_nonmonotone_sequence':int(any(b<a or b>a+1 for a,b in zip(spans,spans[1:]))),
        'cs_last_both_wrong':int(rows[-1]['letters_correct']=='F' and rows[-1]['sum_correct']=='F')}


def completion_valid(duration,correct,errors):
    """Near-full timed administration OR near-complete, not rushed response list."""
    duration=np.asarray(duration,dtype=float);correct=np.asarray(correct,dtype=float);errors=np.asarray(errors,dtype=float)
    basic=np.isfinite(duration)&np.isfinite(correct)&(duration>0)&(duration<=90)&(correct>=0)
    near_full=duration>=89
    responses=correct+errors
    near_complete=np.isfinite(errors)&(errors>=0)&(responses>=66)&(responses<=69)&(duration>=20)
    return basic&(near_full|near_complete)
