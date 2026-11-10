"""Six equal-total maintenance schedules, Supplementary Figure 1 and Table 5.

Uses frozen point and bootstrap fits; does not refit or edit manuscript prose.
Run from any directory with Python, NumPy and Matplotlib.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
ROOT = Path(__import__('os').environ.get('CT_FIGURE_OUTPUT',BASE))
from style import fit_data
DATA = fit_data()
point_file = DATA / 'constant7_point.json'
boot_file = DATA / 'constant7_bootstrap.json'
point = json.loads(point_file.read_text())
boots = json.loads(boot_file.read_text())
assert len(boots) == 500
keys = ['learning_per_game', 'training_forgetting_per_day', 'game_ceiling_GI']
params = np.array([[f['parameters'][k] for k in keys]
    for f in [point]+[b['fit'] for b in boots]])

def spread(total, n):
    return np.diff(np.floor(np.arange(n+1)*total/n+.5)).astype(int)

def trajectory(doses):
    kl, kf, A = params.T
    gain = np.zeros(len(params))
    values = [gain.copy()]
    for p in doses:
        ell = -np.expm1(p*np.log1p(-kl))
        gain = (gain+ell*(A-gain))*(1-kf)
        values.append(gain.copy())
    return np.array(values).T

def estimate(v):
    return {'estimate':float(v[0]), 'CI95':np.percentile(v[1:],[2.5,97.5]).tolist()}

H, TOTAL = 360, 1120
t = np.arange(H)
specs = [
    ('daily','Daily',np.ones(H,dtype=bool)),
    ('weekdays','Weekdays only',t%7<5),
    ('three_weekly','Three days per week',np.isin(t%7,[0,2,4])),
    ('monthly','Monthly boosters',t%30>=23),
    ('quarterly','Quarterly boosters',t%90>=76),
    ('semiannual','Semiannual boosters',t%180>=135),
]
curves, counts, display, summary = {}, {}, {}, {}
audit_errors=[]
for name, label, mask in specs:
    counts[name] = np.zeros(H,dtype=int)
    counts[name][mask] = spread(TOTAL,int(mask.sum()))
    assert counts[name].sum()==TOTAL and counts[name].max()<=20
    display[name] = mask * (TOTAL/mask.sum())
    assert abs(display[name].sum()-TOTAL)<1e-9
    doses = np.r_[spread(400,90),counts[name]]
    curves[name] = trajectory(doses)[:,90:]
    kl, kf, A = params.T
    ell = 1-(1-kl[:,None])**doses[None,:]
    retain = (1-ell)*(1-kf[:,None])
    after = np.column_stack([np.cumprod(retain[:,:0:-1],axis=1)[:,::-1],np.ones(len(params))])
    independent = A*np.sum(ell*(1-kf[:,None])*after,axis=1)
    audit_errors.append(float(np.max(abs(independent-curves[name][:,-1]))))
    g=curves[name][:,1:]
    summary[name] = dict(label=label, active_days=int(mask.sum()),
        games_per_active_day=float(TOTAL/mask.sum()),
        integer_games_per_active_day=[int(counts[name][mask].min()),int(counts[name][mask].max())],
        mean_gain=estimate(g.mean(axis=1)), endpoint_gain=estimate(g[:,-1]),
        minimum_gain=estimate(g.min(axis=1)), maximum_gain=estimate(g.max(axis=1)))
assert max(audit_errors)<1e-11
published = json.loads((ROOT/'booster_comparison.json').read_text())
assert abs(curves['daily'][0,0]-published['day90']['estimate'])<1e-12

manifest = dict(initial_gameplays=400, initial_days=90, followup_days=H,
    maintenance_gameplays=TOTAL, bootstrap_fits=500, new_fits=0,
    schedule_definitions=dict(weekly='Follow-up day 1 is Monday; three-day schedule is Monday/Wednesday/Friday',
        monthly='23 days off, 7 days on; repeat 12 times',
        quarterly='76 days off, 14 days on; repeat 4 times',
        semiannual='135 days off, 45 days on; repeat 2 times'),
    display='Mean gameplays per active day; predictions use the actual integer counts',
    outcome='Training-related GI gain relative to no training with identical age, baseline and test history',
    summary='End-of-day means, endpoints and ranges over follow-up days 1–360; endpoint is study day 450',
    endpoint_phase='All boosters finish on follow-up day 360; weekly schedules finish on Wednesday',
    source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [point_file,boot_file]},
    independent_endpoint_error=max(audit_errors), schedules=summary)
(ROOT/'supplementary_schedule_comparison.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (ROOT/'supplementary_schedule_trajectories.csv').open('w') as f:
    w=csv.writer(f)
    w.writerow(['schedule','followup_day','study_day','gameplays','display_games','GI_gain','CI95_low','CI95_high'])
    for name, _, _ in specs:
        lo,hi=np.percentile(curves[name][1:],[2.5,97.5],axis=0)
        for d in range(H+1):
            w.writerow([name,d,90+d,0 if d==0 else counts[name][d-1],
                0 if d==0 else display[name][d-1],curves[name][0,d],lo[d],hi[d]])

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
    'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
teal,gray='#087f8c','#91999f'
fig=plt.figure(figsize=(8.2,9.0))
outer=fig.add_gridspec(3,2,left=.085,right=.985,bottom=.075,top=.965,wspace=.27,hspace=.38)
for i,(name,label,_) in enumerate(specs):
    grid=outer[i//2,i%2].subgridspec(2,1,height_ratios=[1.35,3.1],hspace=.09)
    doseax=fig.add_subplot(grid[0]); gainax=fig.add_subplot(grid[1],sharex=doseax)
    doseax.text(0,1.15,chr(ord('a')+i),transform=doseax.transAxes,fontweight='bold',fontsize=11)
    doseax.text(.065,1.15,label,transform=doseax.transAxes,fontsize=10)
    doseax.step(np.arange(H+1),np.r_[display[name],display[name][-1]],where='post',lw=.9,color=gray)
    doseax.set(ylim=(-1,22),yticks=[0,20])
    doseax.tick_params(axis='x',bottom=False,labelbottom=False)
    doseax.spines['bottom'].set_visible(False)
    if i%2==0:doseax.set_ylabel('Games/day',fontsize=8)
    lo,hi=np.percentile(curves[name][1:],[2.5,97.5],axis=0)
    gainax.fill_between(np.arange(H+1),lo,hi,color=teal,alpha=.14,lw=0)
    gainax.plot(curves[name][0],color=teal,lw=1.5)
    if name!='daily':gainax.plot(curves['daily'][0],color=gray,ls='--',lw=.85)
    gainax.set(xlim=(0,H),ylim=(0,4.05),xticks=[0,90,180,270,360],yticks=[0,1,2,3,4])
    if i%2==0:gainax.set_ylabel('Training-related GI gain')
    for ax in [doseax,gainax]:
        ax.tick_params(length=3,width=.65,pad=3)
        for spine in ax.spines.values():spine.set_linewidth(.65)
fig.supxlabel('Days after the initial 90-day training course',x=.535,y=.025,fontsize=10)
for ext in ['png','svg']:fig.savefig(ROOT/f'Supplementary_Figure_1.{ext}',dpi=300,facecolor='white')
plt.close(fig)
print(json.dumps(summary,indent=2))
