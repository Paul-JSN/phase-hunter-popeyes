"""Recover full-register Z readout statistics of the archived N=8 scan.

The archive predates parameter saving. Replay its deterministic warm/cold fits,
validate every recovered mean and energy against the archive, and save parameters
and joint (C1,C2) outcome probabilities. Abort rather than invent missing statistics.
Original scan used 150 cold / 60 warm Adam steps, seed 0, four ansatz layers.

    python scripts/recover_readout.py --workers 2

Column checkpoints allow resuming. Neither this script nor its workers overwrite
the archived means. Checkpoints belong to one SHA-256 input hash only.
"""
from pathlib import Path
import sys,json,hashlib,argparse,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
ARCHIVE=ROOT/'data/pennylane_scan_N8.npz'

def column(task):
    b,cache,digest=task;cache=Path(cache);file=cache/f'column-{b:02d}.npz'
    if file.exists():
        with np.load(file) as old:
            if str(old['archive_sha256'])==digest:return b,'cached'
    import pennylane as qml
    from src.pennylane_pipeline import vqe_ground_state,ansatz,build_hamiltonian
    from src.annni import AnnniChain
    scan=np.load(ARCHIVE);n=8;layers=int(scan['layers']) if 'layers' in scan else 4;chain=AnnniChain(n)
    outcomes,inverse=np.unique(np.stack([chain.zz1,chain.zz2],axis=1),axis=0,return_inverse=True)
    rows=len(scan['hs']);noise=scan['noise'];hist=np.zeros((len(noise),rows,len(outcomes)))
    params_all=np.zeros((rows,layers,n,2));deviations=[]
    devices={float(p):qml.device('default.qubit' if p==0 else 'default.mixed',wires=n) for p in noise}
    def probs(params,p):
        @qml.qnode(devices[float(p)])
        def circuit():
            ansatz(params,n,layers,noise=float(p));return qml.probs(wires=range(n))
        values=np.asarray(circuit(),dtype=float);values=np.maximum(values,0);return values/values.sum()
    warm=None;start=time.time()
    for a,h in enumerate(scan['hs']):
        if 'parameters' in scan:
            params=np.asarray(scan['parameters'][a,b])
            device=qml.device('default.qubit',wires=n)
            @qml.qnode(device)
            def energy_node():
                ansatz(params,n,layers)
                return qml.expval(build_hamiltonian(n,float(scan['kappas'][b]),float(h)))
            energy=float(energy_node())
        else:
            params,energy=vqe_ground_state(n,float(scan['kappas'][b]),float(h),layers=layers,steps=150 if warm is None else 60,init=warm)
            # Replay what the archived run actually did, including its cold-refit choice.
            if scan['refits'][a,b]:params,energy=vqe_ground_state(n,float(scan['kappas'][b]),float(h),layers=layers,steps=150)
        warm=np.asarray(params);params_all[a]=warm
        error=abs(energy-scan['energy_vqe'][a,b]);deviations.append(error)
        if error>1e-7:raise RuntimeError(f'Archived energy mismatch at ({a},{b}): {error}')
        for j,p in enumerate(noise):
            distribution=probs(params,p);hist[j,a]=np.bincount(inverse,weights=distribution,minlength=len(outcomes))
            expected=np.array([scan[f'p{p}_zz1'][a,b],scan[f'p{p}_zz2'][a,b]])
            delta=float(np.max(np.abs(hist[j,a]@outcomes-expected)));deviations.append(delta)
            if delta>1e-7:raise RuntimeError(f'Archived mean mismatch at ({a},{b},p={p}): {delta}')
    np.savez_compressed(file,parameters=params_all,readout=hist,outcomes=outcomes,noise=noise,archive_sha256=digest,max_difference=max(deviations))
    return b,f'{time.time()-start:.1f}s, max archive difference {max(deviations):.2g}'

def main():
    from concurrent.futures import ProcessPoolExecutor,as_completed
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=2);parser.add_argument('--start-column',type=int,default=0);args=parser.parse_args()
    digest=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest();scan=np.load(ARCHIVE)
    cache=ROOT/'.readout-checkpoints';cache.mkdir(exist_ok=True)
    start=time.time();tasks=[(b,str(cache),digest) for b in range(args.start_column,len(scan['kappas']))]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done,future in enumerate(as_completed([pool.submit(column,t) for t in tasks]),1):
            b,message=future.result();print(f'{done}/{len(tasks)} columns; kappa column {b}: {message}; elapsed {(time.time()-start)/60:.1f}m',flush=True)
    if not all((cache/f'column-{b:02d}.npz').exists() for b in range(len(scan['kappas']))):
        print('Requested columns recovered; run without --start-column to assemble the complete archive.');return
    records=[np.load(cache/f'column-{b:02d}.npz') for b in range(len(scan['kappas']))]
    readout=np.stack([r['readout'] for r in records],axis=2)
    params=np.stack([r['parameters'] for r in records],axis=1)
    np.savez_compressed(ROOT/'data/readout_N8.npz',readout=readout,parameters=params,outcomes=records[0]['outcomes'],noise=scan['noise'],kappas=scan['kappas'],hs=scan['hs'],archive_sha256=digest)
    report={'protocol':'whole-register Z; joint site-averaged C1/C2 outcomes','archive_sha256':digest,
       'grid':[len(scan['hs']),len(scan['kappas'])],'max_recovery_difference':max(float(r['max_difference']) for r in records),
       'cold_steps':int(scan['steps']) if 'steps' in scan else 150,'warm_steps':int(scan['warm_steps']) if 'warm_steps' in scan else 60,'layers':int(scan['layers']) if 'layers' in scan else 4,'seed':0,'minutes':(time.time()-start)/60}
    (ROOT/'data/readout_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
