"""Figure 2: joint distribution and separate marginal cumulative distributions.

Frozen cohort, unchanged counts/limits. No models fitted. Requires local inputs.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from style import setup,save,INK
OUT=Path(__import__('os').environ['CT_FIGURE_OUTPUT'])
a=np.load(__import__('os').environ['CT_INPUT'])
d,p=a['D'][:,0],a['P'][:,0]
assert len(d)==len(p)==172731
assert np.isfinite(d).all() and np.isfinite(p).all()
limd,limp=np.percentile(d,99),np.percentile(p,99)
setup()
fig=plt.figure(figsize=(9.5,5.6))
axjoint=fig.add_axes([.095,.13,.355,.76])
cax=fig.add_axes([.470,.20,.015,.62])
axdays=fig.add_axes([.660,.61,.305,.28])
axgames=fig.add_axes([.660,.13,.305,.28])
h=axjoint.hexbin(d,p,gridsize=45,extent=(0,limd,0,limp),mincnt=1,
                 norm=LogNorm(),cmap='viridis')
fig.colorbar(h,cax=cax,label='Participants')
axjoint.set(xlabel='Days between T1 and T2',ylabel='Gameplays between T1 and T2',
            xlim=(0,limd),ylim=(0,limp))
for ax,v,xlabel in [(axdays,d,'Days between T1 and T2'),
                    (axgames,p,'Gameplays between T1 and T2')]:
 values=np.sort(v)
 percentages=100*np.arange(1,len(values)+1)/len(values)
 ax.plot(values,percentages,color=INK,lw=1.7)
 ax.set(xlim=(0,1000),ylim=(0,100),xticks=[0,250,500,750,1000],
        yticks=[0,50,100],xlabel=xlabel,ylabel='Cumulative percentage')
 ax.tick_params(labelsize=9)
 ax.xaxis.labelpad=6
 ax.yaxis.labelpad=6
fig.text(.045,.925,'a',weight='bold',fontsize=12)
fig.text(.610,.925,'b',weight='bold',fontsize=12)
fig.text(.610,.445,'c',weight='bold',fontsize=12)
save(fig,'Figure_2')
(OUT/'figure2_layout_checks.json').write_text(json.dumps({
 'participants':len(d),'joint_panel_gridsize':45,
 'joint_panel_99th_percentile_limits':[float(limd),float(limp)],
 'cumulative_panel_xlim':[0,1000],
 'cumulative_panel_ylim':[0,100],
 'all_participants_in_each_cumulative_distribution':True,
 'changed':'Layout only; separated calendar days and gameplays into b and c.',
 'model_refits':0},indent=2)+'\n')
