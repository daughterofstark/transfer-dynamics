"""Working conceptual schematic with daily dots and an explicit summation panel.

Reproducible illustrative counts, not empirical participant data.
Daily dots adopted by the author; earlier versions are preserved separately.

All four rows share calendar time. Retest inputs occur immediately after testing,
so each test contributes to later performance, not its own recorded score.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from style import setup,save,TEAL,ORANGE,INK,GRAY
setup()
fig=plt.figure(figsize=(9.5,7.7))
# Preserve the physical spacing of panels a/b while adding 1.5 inches below.
def y(v):return (1.5+6.2*v)/7.7
def row(bottom,height):return [left,y(bottom),width,6.2*height/7.7]
left,width=.275,.675
axtrain=fig.add_axes(row(.765,.125))
axtest=fig.add_axes(row(.640,.065))
axgain=fig.add_axes(row(.365,.160))
axretest=fig.add_axes(row(.150,.160))
axes=[axtrain,axtest,axgain,axretest]
end=150
tests=[0,39,103,150]
# Variable integer counts with exactly the same totals and active/pause periods
# as the primary schematic. A fixed seed keeps visual revisions reproducible.
rng=np.random.default_rng(20261102)
def variable_counts(days,mean):
 return rng.multinomial(days*mean,np.full(days,1/days))
daily=np.r_[variable_counts(30,5),np.zeros(26,dtype=int),
             variable_counts(34,3),np.zeros(15,dtype=int),variable_counts(45,4)]
assert len(daily)==150 and daily.sum()==432
assert daily[30:56].sum()==daily[90:105].sum()==0
for ax in axes:
 ax.set_xlim(-2,end+2)
 ax.set_xticks([]);ax.set_yticks([])
 for spine in ax.spines.values():spine.set_visible(False)
 for t in tests:
  ax.axvline(t,color='#dce0e2',lw=.75,ls=(0,(2,3)),zorder=0)
axtrain.set_ylim(-.6,max(daily)+1)
axtrain.scatter(np.arange(end)+.5,daily,s=8,color=TEAL,linewidths=0,zorder=3)
axtest.set_ylim(-.8,.8)
axtest.plot([0,end],[0,0],color=GRAY,lw=.8)
axtest.scatter(tests,np.zeros(len(tests)),color=INK,s=25,zorder=3)
for i,t in enumerate(tests,1):axtest.text(t,-.45,f'T{i}',ha='center',va='top',fontsize=10)
# Illustrative dynamics; arbitrary scales, intentionally no numerical axes.
gain=[0.]
for p in daily:
 learn=1-(1-.035)**p
 gain.append((gain[-1]+learn*(1-gain[-1]))*(1-.012))
axgain.plot(np.arange(end+1),gain,color=TEAL,lw=2)
axgain.set_ylim(-.03,1.05)
rt=[0.];rv=[0.];r=0.
for start,stop in zip(tests[:-1],tests[1:]):
 rt.extend([start,start+1e-5]);rv.extend([r,r+.45]);r+=.45
 ts=np.linspace(start+1e-5,stop,180)
 values=r*(1-.004)**(ts-start)
 rt.extend(ts.tolist());rv.extend(values.tolist());r=float(values[-1])
axretest.plot(rt,rv,color=ORANGE,lw=2)
axretest.set_ylim(-.03,1.12)
axretest.spines['bottom'].set_visible(True)
axretest.spines['bottom'].set_color(GRAY)
axretest.spines['bottom'].set_linewidth(.8)
axretest.set_xlabel('Calendar time',labelpad=9)
fig.text(.045,y(.945),'a',weight='bold',fontsize=12)
fig.text(.095,y(.945),'Cognitive training and testing',fontsize=12)
fig.text(.045,y(.575),'b',weight='bold',fontsize=12)
fig.text(.095,y(.575),'Contributions to NCPT improvement',fontsize=12)
for label_y,s in [(.8275,'Daily cognitive\ntraining'),(.6725,'NCPT tests'),(.445,'Training-related\ngain'),(.230,'Retest-related\ngain')]:
 fig.text(.245,y(label_y),s,ha='right',va='center',fontsize=10.5,linespacing=1.5)
# Panel c: three distinct inputs sum to a predicted change at follow-up.
fig.text(.045,1.43/7.7,'c',weight='bold',fontsize=12)
fig.text(.095,1.43/7.7,'Predicted NCPT improvement',fontsize=12)
combine=fig.add_axes([0,0,1,1.30/7.7])
combine.set(xlim=(0,9.5),ylim=(0,1.30),aspect='equal')
combine.axis('off')
for cx,label in [(1.55,'Training-\nrelated gain'),(3.50,'Retest-\nrelated gain'),(5.45,'Baseline\ncorrection')]:
 combine.add_patch(Circle((cx,.66),.55,facecolor='white',edgecolor=GRAY,lw=1))
 combine.text(cx,.66,label,ha='center',va='center',fontsize=10,linespacing=1.5)
for cx in [2.525,4.475]:combine.text(cx,.66,'+',ha='center',va='center',fontsize=18)
combine.add_patch(FancyArrowPatch((6.17,.66),(7.02,.66),arrowstyle='-|>',mutation_scale=12,color=INK,lw=1.1))
combine.add_patch(FancyBboxPatch((7.13,.25),1.72,.82,boxstyle='round,pad=.02,rounding_size=.06',
 facecolor='white',edgecolor=GRAY,lw=1))
combine.text(7.99,.66,'Predicted\nGI change',ha='center',va='center',fontsize=10.5,linespacing=1.5)
save(fig,'Figure_1')
