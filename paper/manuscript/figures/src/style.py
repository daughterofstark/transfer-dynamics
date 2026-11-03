"""Shared figure conventions; labels stay neutral, color encodes plotted quantities."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__import__('os').environ['CT_FIGURE_OUTPUT'])
TEAL='#087f8c'
ORANGE='#ba5a22'
PURPLE='#78569b'
INK='#252a2d'
GRAY='#aeb6ba'
def setup():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,
  'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
  'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
def daily_training(ax,counts,**kwargs):
 """Daily counts held constant over each calendar-day bin, as in Figure 4a."""
 return ax.stairs(counts,np.arange(len(counts)+1),baseline=None,**kwargs)
def save(fig,name):
 for ext in ['png','svg']:
  fig.savefig(OUT/f'{name}.{ext}',dpi=300,facecolor='white')
 plt.close(fig)
