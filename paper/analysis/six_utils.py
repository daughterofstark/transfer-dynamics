"""Six nonlinear coordinates for the slowing-decay comparator."""
import numpy as np
import model
NAMES=model.NAMES[:6];SCALE=model.SCALE[:6];BOUNDS=model.BOUNDS[:6]
fa=model.fa;ia=model.ia;half=model.half;load=model.load;subset=model.subset
def active_gradient(x,g):
    return model.active_gradient(np.r_[x,0.],np.r_[g,0.],fixed={6:0.})
