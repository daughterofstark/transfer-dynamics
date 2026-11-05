"""Daily maintenance and periodic booster illustration.

Uses the adopted fit and existing 500 participant bootstrap draws; no refitting.
This script only regenerates Figure 4 and its numerical summaries.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__import__('os').environ.get('CT_FIGURE_OUTPUT',ROOT))
from style import daily_training, fit_data
SOURCE = fit_data()
fit = json.loads((SOURCE / 'constant7_point.json').read_text())
boots = json.loads((SOURCE / 'constant7_bootstrap.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                    'axes.spines.top': False, 'axes.spines.right': False,
                    'svg.fonttype': 'none'})
teal, orange, purple, gray = '#087f8c', '#ba5a22', '#78569b', '#66727c'

def save(fig, name):
    for ext in ['png', 'svg']:
        fig.savefig(OUT / f'{name}.{ext}', dpi=300, facecolor='white')
    plt.close(fig)

def vec(f):
    return np.array([f['parameters'][k] for k in
                     ['learning_per_game', 'training_forgetting_per_day', 'game_ceiling_GI']])

def schedule(total, days):
    return np.diff(np.floor(np.arange(days + 1) * total / days + .5)).astype(int)

def trajectory(params, doses):
    p = np.atleast_2d(params)
    kl, kf, maximum = p.T
    gain = np.zeros(len(p))
    out = [gain.copy()]
    for dose in doses:
        learn = -np.expm1(dose * np.log1p(-kl))
        gain = (gain + learn * (maximum - gain)) * (1 - kf)
        out.append(gain.copy())
    return np.array(out).T

def equilibrium(params, dose):
    kl, kf, maximum = np.atleast_2d(params).T
    learn = -np.expm1(np.asarray(dose)[None, :] * np.log1p(-kl)[:, None])
    return maximum[:, None] * (1-kf[:, None]) * learn / (kf[:, None] + (1-kf[:, None])*learn)

x = vec(fit)
xx = np.array([vec(b['fit']) for b in boots])
assert len(xx) == 500
H = 360
initial = schedule(400, 90)
continuation = schedule(840, 270)
boost = np.zeros(270, dtype=int)
for start in [76, 166, 256]:
    boost[start:start + 14] = 20
schedules = {'steady': np.r_[initial, continuation],
             'booster': np.r_[initial, boost],
             'stop': np.r_[initial, np.zeros(270, dtype=int)]}
assert schedules['steady'][90:].sum() == schedules['booster'][90:].sum() == 840
assert np.all(schedules['booster'][166:180] == 20)
assert sum(boost > 0) == 42 and boost.max() == 20
curves = {k: trajectory(x, v)[0] for k, v in schedules.items()}
draws = {k: trajectory(xx, v) for k, v in schedules.items()}

# Independent segment closed forms verify both the 76-day pauses and 14-day
# booster blocks. The vectorized implementation above is used for plotting.
def segment(gain, dose, days):
    kl, kf, maximum = x
    learning = 1 - (1 - kl) ** dose
    r = (1 - learning) * (1 - kf)
    return r ** days * gain + maximum * learning * (1-kf) * (1 - r ** days) / (1 - r)
g = curves['booster'][90]
errors = []
for endpoint in [180, 270, 360]:
    g = segment(segment(g, 0, 76), 20, 14)
    errors.append(abs(g - curves['booster'][endpoint]))
assert max(errors) < 1e-12
assert np.all(np.isfinite(curves['steady']))

def interval(a):
    return np.percentile(a, [2.5, 97.5]).tolist()
def summary_at(k, index):
    return {'estimate': float(curves[k][index]), 'CI': interval(draws[k][:, index])}
summary = {
    'source': 'figure_data',
    'bootstrap_draws': len(xx), 'new_model_fits': 0,
    'initial_games': 400, 'initial_days': 90,
    'maintenance_games_each': 840, 'maintenance_days': 270,
    'steady_games_per_day': 840 / 270,
    'booster_days_inclusive': [[167,180],[257,270],[347,360]],
    'booster_games_per_active_day': 20, 'booster_pause_days': 76,
    'schedule_design': 'Author-approved 14 days per 90-day cycle; boosters at the end of each cycle; matched total, not optimized.',
    'segment_verification_max_abs_error': max(errors),
    'day90': summary_at('steady', 90),
    'day360': {k: summary_at(k, 360) for k in curves},
    'pre_booster': {str(i): summary_at('booster', i) for i in [166,256,346]},
    'post_booster': {str(i): summary_at('booster', i) for i in [180,270,360]},
    'mean_days91_360': {k: {'estimate': float(v[91:].mean()),
        'CI': interval(draws[k][:,91:].mean(axis=1))} for k,v in curves.items()},
    'mean_steady_minus_booster': {
        'estimate': float((curves['steady'][91:] - curves['booster'][91:]).mean()),
        'CI': interval((draws['steady'][:,91:] - draws['booster'][:,91:]).mean(axis=1))},
    'mean_definition': 'Arithmetic mean of modeled end-of-day gains for days 91–360, equally weighted days; paired bootstrap contrast.'
}
(OUT/'booster_comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
rows = {'day': np.arange(H+1)}
for k in curves:
    rows[k+'_games'] = np.r_[0, schedules[k]]
    rows[k+'_GI'] = curves[k]
    rows[k+'_lo'], rows[k+'_hi'] = np.percentile(draws[k],[2.5,97.5],axis=0)
pd.DataFrame(rows).to_csv(OUT/'illustrative_trajectories.csv',index=False)

# Main Figure 4: same training total, visibly different timing.
fig=plt.figure(figsize=(9,6.5))
gs=fig.add_gridspec(2,2,left=.09,right=.98,bottom=.20,top=.90,
                    height_ratios=[1,2.65],width_ratios=[1.35,1],hspace=.12,wspace=.34)
axdose=fig.add_subplot(gs[0,0]);axgain=fig.add_subplot(gs[1,0],sharex=axdose)
axeq=fig.add_subplot(gs[:,1])
fig.text(.035,.94,'a',fontsize=12,fontweight='bold')
fig.text(.565,.94,'b',fontsize=12,fontweight='bold')
time=np.arange(H+1)
for ax in [axdose,axgain]:
    ax.axvspan(0,90,color='#edf2f4',zorder=0)
    ax.axvline(90,color=gray,ls=':',lw=.8)
    for a,b in [(166,180),(256,270),(346,360)]:
        ax.axvspan(a,b,color=purple,alpha=.055,zorder=0)
# Show phase-average daily rates in the schedule diagram. All gain curves and
# confidence bands still use the original integer-day schedules above.
display_steady=np.r_[np.full(90,400/90),np.full(270,840/270)]
display_booster=np.r_[np.full(90,400/90),boost]
assert np.isclose(display_steady.sum(),schedules['steady'].sum())
assert np.isclose(display_booster.sum(),schedules['booster'].sum())
daily_training(axdose,display_booster,color=purple,lw=1.7)
daily_training(axdose,display_steady,color=teal,lw=1.15)
axdose.set(ylim=(-.5,23),yticks=[0,10,20],ylabel='Games/day')
axdose.tick_params(axis='x',labelbottom=False,bottom=False)
axdose.spines['bottom'].set_visible(False)
for k,color,label in [('steady',teal,'Daily maintenance'),('booster',purple,'Periodic boosters'),('stop',orange,'Stop training')]:
    low,high=np.percentile(draws[k],[2.5,97.5],axis=0)
    axgain.fill_between(time,low,high,color=color,alpha=.12,lw=0)
    axgain.plot(time,curves[k],color=color,lw=1.9,label=label)
axgain.set(xlabel='Days since training began',ylabel='Additional GI gain versus no training',
           xlim=(0,H),ylim=(0,4.1),xticks=[0,90,180,270,360])
half=fit['derived']['training_half_life_days']
axgain.plot(90+half,curves['stop'][90]/2,'o',ms=4,color=orange)
axgain.annotate('Half-life',xy=(90+half,curves['stop'][90]/2),xytext=(140,.55),fontsize=10,color='#252a2d',
                arrowprops={'arrowstyle':'-','color':gray,'lw':.9})
handles,labels=axgain.get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.53,.025),ncol=3,fontsize=10,frameon=False,
           handlelength=2.0,columnspacing=2.0)
dose=np.linspace(0,8,321);ev=equilibrium(x,dose)[0];ed=equilibrium(xx,dose)
lo,hi=np.percentile(ed,[2.5,97.5],axis=0)
axeq.fill_between(dose,lo,hi,color=teal,alpha=.14);axeq.plot(dose,ev,color=teal,lw=2)
dose80=fit['derived']['dose_80_games_day'];target=.8*x[2]
axeq.plot([0,dose80,dose80],[target,target,0],color=gray,ls=':',lw=1)
axeq.plot(dose80,target,'o',color=orange,ms=5)
axeq.annotate('80% of maximum',xy=(dose80,target),xytext=(3.6,2.3),fontsize=10,color='#252a2d',
              arrowprops={'arrowstyle':'-','color':gray,'lw':.9})
axeq.set(xlabel='Ongoing training\n(gameplays/day)',ylabel='Estimated sustained GI gain',xlim=(0,8),ylim=(0,4.1))
pd.DataFrame({'games_day':dose,'equilibrium_GI':ev,'lo':lo,'hi':hi}).to_csv(OUT/'illustrative_maintenance.csv',index=False)
save(fig,'Figure_4')
print(json.dumps(summary,indent=2))
