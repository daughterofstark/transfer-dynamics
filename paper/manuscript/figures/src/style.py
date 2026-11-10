"""Shared figure conventions; labels stay neutral, color encodes plotted quantities."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__import__('os').environ.get('CT_FIGURE_OUTPUT',Path(__file__).resolve().parents[1]))
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


def analysis_root():
 """Locate the standalone repository or its local manuscript working copy."""
 for parent in Path(__file__).resolve().parents:
  for candidate in (parent, parent/'review_v17/publication-pr'):
   if (candidate/'reproduce.py').is_file() and (candidate/'paper/analysis').is_dir():
    return candidate
 raise FileNotFoundError('Cannot locate the analysis repository; use reproduce.py figures.')

def figure_data():
 return Path(__import__('os').environ.get('CT_FIGURE_DATA', analysis_root()/'paper/reference/figure_data'))

def fit_data():
 return Path(__import__('os').environ.get('CT_FIT_DATA', analysis_root()/'paper/reference'))
