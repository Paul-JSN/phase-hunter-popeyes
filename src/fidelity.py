"""Basis-invariant subspace fidelity and a fixed symmetry-sector ground state.

For h>0 the ANNNI Hamiltonian has non-positive off-diagonal entries and is
irreducible in the computational basis. Its unique positive ground state is
invariant under translations and global spin flip. We diagonalize in that
fixed sector to avoid arbitrary choices among near-degenerate symmetry partners.
No phase-boundary labels enter the computation. h=0 is excluded from fidelity
stencils because exact degeneracies there require a separate treatment.
"""
import numpy as np


def subspace_fidelity(lo, hi):
    """Root Uhlmann fidelity of normalized projectors onto two subspaces.

Inputs have orthonormal columns. The FULL rectangular overlap is used; no
arbitrary columns are discarded if ranks differ. Rank changes are penalized.
For rank one this reduces to the absolute state overlap.
"""
    singular=np.linalg.svd(lo.conj().T @ hi, compute_uv=False)
    return float(np.clip(singular.sum()/np.sqrt(lo.shape[1]*hi.shape[1]),0,1))


def invariant_basis(n):
    dim=1<<n;mask=dim-1;seen=set();orbits=[]
    for start in range(dim):
        if start in seen: continue
        orbit=set(); value=start
        for _ in range(n):
            orbit.update((value,value^mask))
            value=((value<<1)&mask)|(value>>(n-1))
        seen.update(orbit);orbits.append(sorted(orbit))
    basis=np.zeros((dim,len(orbits)))
    for j,orbit in enumerate(orbits):basis[orbit,j]=1/np.sqrt(len(orbit))
    return basis


def fidelity_susceptibility(n_qubits=8, grid=40):
    from .annni import AnnniChain
    chain=AnnniChain(n_qubits); basis=invariant_basis(n_qubits)
    # Project the three fixed operators once, rather than at every grid cell.
    nn=basis.T @ ((-chain.n*chain.zz1)[:,None]*basis)
    nnn=basis.T @ ((chain.n*chain.zz2)[:,None]*basis)
    field=basis.T @ chain.xsum @ basis
    kappas=np.linspace(0,1,grid);hs=np.linspace(0,2,grid)
    chi=np.full((grid,grid),np.nan)
    for b,kappa in enumerate(kappas):
        states=[None]
        for h in hs[1:]:
            _,v=np.linalg.eigh(nn+kappa*nnn-h*field);states.append(v[:,0])
        for a in range(1,grid):
            below=max(a-1,1);above=min(a+1,grid-1)
            overlap=abs(np.vdot(states[below],states[above]))
            chi[a,b]=2*(1-np.clip(overlap,0,1))/(hs[above]-hs[below])**2
    return kappas,hs,chi
