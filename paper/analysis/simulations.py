from scipy.special import roots_legendre
from scipy.optimize import brentq
import numpy as np
from workflow import read,save
def quadrature(n):
    x, w = roots_legendre(n)
    u = np.exp((x + 1) * 9 - 14)
    weights = w * 9 * u * np.exp(-u)
    return u, weights / weights.sum()

def schedule(total, days=90):
    # Identical integer-day schedule to Figure 4.
    return np.diff(np.floor(np.arange(days + 1) * total / days + .5)).astype(int)

def evaluate(params, doses, slowing, nodes=48):
    kl = params['learning_per_game']
    k = params['training_decay_scale' if slowing else 'training_forgetting_per_day']
    maximum = params['game_ceiling_GI']
    u, w = quadrature(nodes) if slowing else (np.ones(1), np.ones(1))
    z = np.zeros(len(u))
    lam = -np.log1p(-k)
    for dose in doses:
        learn = -np.expm1(dose * np.log1p(-kl))
        z = (z + learn * (1 - z)) * np.exp(-lam * u)
    gain = float(maximum * (w @ z))
    def remaining(t):
        return float((w @ (z * np.exp(-lam * u * t))) / (w @ z))
    half = brentq(lambda t: remaining(t) - .5, 0, 1e7)
    return {'gain_at_cessation_GI': gain, 'half_retention_days': half,
            'remaining_fraction': {str(d): remaining(d) for d in [90, 180, 365]},
            'gain_after_cessation_GI': {str(d): gain * remaining(d) for d in [90, 180, 365]}}

def run(source,out,stats):
    primary=read(source/'constant7_point.json')['parameters'];slow=read(source/'slowing_point.json')['parameters']
    result={name:evaluate(p,schedule(400),is_slow) for name,p,is_slow in [('exponential',primary,False),('slowing',slow,True)]}
    save(out/'slowing_400.json',result)
    vals=[evaluate(b['fit']['parameters'],schedule(400),False)['gain_at_cessation_GI'] for b in read(source/'constant7_bootstrap.json')]
    gain=result['exponential']['gain_at_cessation_GI'];ci=np.percentile(vals,[2.5,97.5])
    save(out/'effect_size.json',dict(gameplays=400,days=90,GI_difference=dict(estimate=gain,CI=ci.tolist()),change_SD=stats['change_SD'],baseline_SD=stats['baseline_SD'],change_standardized=dict(estimate=gain/stats['change_SD'],CI=(ci/stats['change_SD']).tolist()),baseline_standardized=dict(estimate=gain/stats['baseline_SD'],CI=(ci/stats['baseline_SD']).tolist())))

def timing_contrasts(source,out):
    rows=[read(source/'constant7_point.json')]+[b['fit'] for b in read(source/'constant7_bootstrap.json')]
    values=[]
    for row in rows:
        p=row['parameters'];d={}
        for n in [90,730]:
            gain=evaluate(p,schedule(400,n),False)['gain_at_cessation_GI']
            retest=p['test_increment_age50_GI']*(1-p['retest_forgetting_per_day'])**n
            d[f'training_{n}']=gain;d[f'retest_{n}']=retest;d[f'total_{n}']=gain+retest
        d['total_difference']=d['total_90']-d['total_730'];d['training_difference']=d['training_90']-d['training_730'];values.append(d)
    outdata={k:dict(estimate=values[0][k],CI=np.percentile([r[k] for r in values[1:]],[2.5,97.5]).tolist()) for k in values[0]}
    p=read(source/'benchmark_point_fits.json')['static_dose_response']['parameters']
    outdata['static_total']=p['training_max']*(1-(1-p['learning_per_game'])**400)+p['q_T2']
    save(out/'timing_contrast.json',outdata)
