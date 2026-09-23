"""Joint whole-register Z readout, plus the explicit random-pair comparator.

The production game and budget study use sample_joint. The older random-pair
functions remain solely for a documented protocol comparison in the notebook.
"""
import numpy as np


def shot_counts(shots):
    if int(shots) != shots or shots < 2:
        raise ValueError("A ping needs at least two integer shots.")
    return int(shots)//2, int(shots)-int(shots)//2


def single_shot_sd(mean):
    return np.sqrt(np.maximum(0.0, 1.0-np.clip(mean, -1.0, 1.0)**2))


def sample_correlators(zz1, zz2, shots, rng):
    counts = shot_counts(shots)
    return tuple(float(2*rng.binomial(n, (1+np.clip(m, -1, 1))/2)/n-1)
                 for m,n in zip((zz1,zz2),counts))


def joint_outcomes(n):
    """Joint (site-averaged C1, C2) values of each computational-basis bitstring.

    Grouping bitstrings with identical observable pairs is lossless for these
    two observables, including their covariance and all higher moments.
    """
    index=np.arange(2**n)
    z=1-2*((index[:,None]>>np.arange(n)[None,:])&1)
    values=np.stack([np.mean(z*np.roll(z,-d,axis=1),axis=1) for d in (1,2)],axis=1)
    return np.unique(values,axis=0,return_inverse=True)


def joint_moments(probabilities,outcomes):
    p=np.asarray(probabilities,dtype=float);v=np.asarray(outcomes,dtype=float)
    p=p/p.sum();means=p@v;centered=v-means
    covariance=(centered.T*p)@centered
    return means,covariance


def sample_joint(probabilities,outcomes,shots,rng):
    """One Z-basis readout per preparation; both correlators use every shot.

    A multinomial draw generalizes the binomial to the possible joint outcome
    pairs. It retains physical bounds and covariance without Gaussian clipping.
    """
    if int(shots)!=shots or shots<1:raise ValueError('shots must be a positive integer')
    p=np.asarray(probabilities,dtype=float);v=np.asarray(outcomes,dtype=float)
    if p.ndim!=1 or v.shape!=(len(p),2) or not np.all(np.isfinite(p)) or np.any(p<0) or p.sum()<=0:
        raise ValueError('Invalid joint readout distribution')
    counts=rng.multinomial(int(shots),p/p.sum())
    return tuple(counts@v/int(shots))
