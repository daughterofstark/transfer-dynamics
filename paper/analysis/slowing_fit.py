"""Held-out fits for the slowing-decay comparison."""
import slowing

def fit(a,w,label):
    return slowing.fit(a,w,starts=slowing.STARTS[:2],nodes=24)
