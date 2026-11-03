#!/usr/bin/env python3
"""One entry point for the current paper. See README.md for inputs and modes."""
from pathlib import Path
import sys,os,argparse
ROOT=Path(__file__).resolve().parent
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(ROOT/'paper/analysis'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('step',choices=['validate','replay','fit','report','figures','all'])
    p.add_argument('--input',type=Path,default=ROOT/'data/timing_input.npz')
    p.add_argument('--selection',type=Path,default=ROOT/'data/selection_input.npz')
    p.add_argument('--output',type=Path,default=ROOT/'outputs')
    p.add_argument('--model',choices=['primary','saturating','benchmarks','drift','slowing'],default='primary')
    p.add_argument('--phase',choices=['point','cv','bootstrap'],default='point')
    p.add_argument('--draws',type=int,default=None,help='Explicit smaller smoke run; default 500 (drift: 200).')
    p.add_argument('--fold',type=int,choices=range(5),help='Run one fold only for a smoke check.')
    p.add_argument('--workers',type=int,default=1)
    p.add_argument('--comparisons',action='store_true',help='Replay drift and slower quadrature comparison too.')
    p.add_argument('--audit-bootstrap',action='store_true',help='Re-evaluate every saved primary/saturating bootstrap objective and stationarity.')
    p.add_argument('--results',type=Path,help='Read fit files from this directory instead of paper/reference (e.g. a completed refit).')
    args=p.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=True)
    os.environ.update(CT_INPUT=str(args.input.resolve()),CT_SELECTION=str(args.selection.resolve()),CT_OUTPUT=str(args.output),CT_FIGURE_OUTPUT=str(args.output/'figures'),CT_FIGURE_DATA=str(args.output/'figure_data'))
    import workflow
    if args.step=='validate':workflow.validate(args)
    elif args.step=='fit':workflow.refit(args)
    elif args.step=='replay':workflow.replay(args)
    elif args.step=='report':workflow.report(args)
    elif args.step=='figures':workflow.figures(args)
    else:
        workflow.validate(args);workflow.replay(args);workflow.report(args);workflow.figures(args)
if __name__=='__main__':main()
