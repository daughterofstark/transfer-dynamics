"""Adopted title-free three-across Figure 3; frozen plot values.

Earlier versions and alternative layouts are preserved separately.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import setup,save,TEAL,ORANGE,figure_data
BASE=Path(__file__).resolve().parents[1]
O=Path(__import__('os').environ.get('CT_FIGURE_OUTPUT',BASE));D=figure_data()
t=pd.read_csv(D/'figure2_time_comparison.csv')
q=pd.read_csv(D/'figure2_dose_response.csv')
v=pd.read_csv(D/'figure2_visits.csv')
setup();gray='#687580'
PW,PH=2.9,2.0

def observed(ax,x,y,se):
 ax.errorbar(x,y,yerr=1.96*se,fmt='o',ms=4.3,color=TEAL,
             elinewidth=1.1,capsize=2,capthick=1,zorder=4)

def render(layout):
 if layout=='across':
  fw,fh=10.6,3.25
  origins=[(.65,.83),(4.05,.83),(7.45,.83)]
 else:
  fw,fh=3.75,9.0
  origins=[(.65,6.55),(.65,3.72),(.65,.89)]
 fig=plt.figure(figsize=(fw,fh))
 axs=[fig.add_axes([x/fw,y/fh,PW/fw,PH/fh]) for x,y in origins]
 for i,(ax,(x,y)) in enumerate(zip(axs,origins)):
  ax.set(ylim=(-.5,7),yticks=[0,2,4,6])
  if layout=='stacked' or i==0:ax.set_ylabel('Mean GI gain from T1',labelpad=7)
  ax.tick_params(labelsize=9)
  ax.xaxis.labelpad=6
  for spine in ['left','bottom']:
   ax.spines[spine].set_color('#8a9297');ax.spines[spine].set_linewidth(.8)
  fig.text((x-.31)/fw,(y+PH+.12)/fh,'abc'[i],weight='bold',fontsize=12)
 ax=axs[0]
 observed(ax,q.games_mean,q.observed,q.se)
 ax.plot(q.games_mean,q.predicted,ls='--',color=ORANGE,lw=1.7)
 ax.set(xlabel='Gameplays between T1 and T2',xlim=(0,1400),xticks=[0,400,800,1200])
 ax=axs[1]
 observed(ax,t.months,t.observed,t.se)
 ax.plot(t.months,t.predicted,ls='--',color=ORANGE,lw=1.7)
 ax.set(xlabel='Months between T1 and T2',xlim=(0,62),xticks=[0,12,24,36,48,60])
 ax=axs[2]
 observed(ax,v.visit-.065,v.observed,v.se)
 ax.plot(v.visit+.065,v.predicted,'s',color=ORANGE,ms=4.7)
 ax.set(xlabel='NCPT test timepoint',xlim=(.65,5.35),xticks=v.visit,
        xticklabels=[f'T{int(i)}' for i in v.visit])
 handles=[Line2D([],[],color=TEAL,marker='o',linestyle='none',markersize=4.3,label='Observed'),
          Line2D([],[],color=ORANGE,marker='s',linestyle='--',markersize=4.3,lw=1.7,label='Model')]
 fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),ncol=2,
            frameon=False,fontsize=9,columnspacing=1.2,handlelength=1.8,handletextpad=.5)
 # Assert that layout edits did not change plotted observations or predictions.
 assert np.allclose(axs[0].lines[0].get_ydata(),q.observed)
 assert np.allclose(axs[0].lines[-1].get_ydata(),q.predicted)
 assert np.allclose(axs[1].lines[0].get_ydata(),t.observed)
 assert np.allclose(axs[1].lines[-1].get_ydata(),t.predicted)
 assert np.allclose(axs[2].lines[0].get_ydata(),v.observed)
 assert np.allclose(axs[2].lines[-1].get_ydata(),v.predicted)
 save(fig,'Figure_3')
render('across')
(O/'figure3_current_checks.json').write_text(json.dumps({
 'status':'Finalized three-across layout; observed and model only; no-forgetting benchmark retained in supplement',
 'panel_size_inches':[PW,PH],
 'identical_plotted_values_asserted':True,
 'confidence_intervals':'Observed mean +/- 1.96 SE, unchanged',
 'data_files_sha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in
 ['figure2_time_comparison.csv','figure2_dose_response.csv','figure2_visits.csv']},
 'model_refits':0},indent=2)+'\n')
