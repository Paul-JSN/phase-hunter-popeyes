"""Build five stages with joint whole-register Z readout distributions.

Run scripts/recover_readout.py first for the archived noisy N=8 states.
Clean-state distributions are cached to avoid repeated diagonalization.
"""
from pathlib import Path
import json,sys,time,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.annni import AnnniChain
from src.classify import classify
from src.measurement import joint_outcomes
from src.reference import reference_labels
GRID=24
STAGES=[
 {'id':'clean8','name':'Clear skies','sub':'8 spins · no interference','qubits':8,'p':0.,'source':'exact'},
 {'id':'noise01','name':'Static','sub':'8 spins · 1% gate errors','qubits':8,'p':.01,'source':'scan'},
 {'id':'noise05','name':'Whiteout','sub':'8 spins · 5% gate errors','qubits':8,'p':.05,'source':'scan'},
 {'id':'short6','name':'Broken ring','sub':'6 spins · the stripes cannot fit','qubits':6,'p':0.,'source':'exact'},
 {'id':'long12','name':'Long chain','sub':'12 spins · sharper borders','qubits':12,'p':0.,'source':'exact'}]

def exact_readout(n,kappas,hs):
    path=ROOT/f'data/exact_readout_N{n}.npz'
    if path.exists():
        cached=np.load(path)
        if np.array_equal(cached['kappas'],kappas) and np.array_equal(cached['hs'],hs):return dict(cached)
    chain=AnnniChain(n);outcomes,inverse=joint_outcomes(n)
    readout=np.empty((len(hs),len(kappas),len(outcomes)));energy=np.empty((len(hs),len(kappas)))
    for a,h in enumerate(hs):
        for b,k in enumerate(kappas):
            state,energy[a,b]=chain.ground_state(float(k),float(h));p=np.abs(state)**2;p/=p.sum()
            readout[a,b]=np.bincount(inverse,weights=p,minlength=len(outcomes))
    result=dict(readout=readout,outcomes=outcomes,energy=energy,kappas=kappas,hs=hs)
    np.savez_compressed(path,**result);return result

def main():
    kappas=np.linspace(0,1,GRID);hs=np.linspace(0,2,GRID)
    ref=reference_labels(*np.meshgrid(kappas,hs));scan=np.load(ROOT/'data/pennylane_scan_N8.npz')
    recovered=np.load(ROOT/'data/readout_N8.npz')
    digest=hashlib.sha256((ROOT/'data/pennylane_scan_N8.npz').read_bytes()).hexdigest()
    if str(recovered['archive_sha256'])!=digest:raise RuntimeError('Readout belongs to a different scan')
    for key,value in [('kappas',kappas),('hs',hs)]:np.testing.assert_allclose(recovered[key],value,rtol=0,atol=1e-14)
    payload={'grid':GRID,'kappas':kappas.round(4).tolist(),'hs':hs.round(4).tolist(),'reference':ref.tolist(),'stages':[],
      'measurement_protocol':'whole-register Z; each shot supplies both site-averaged correlators; joint categorical outcomes',
      'note':'Clean stages use exact states; noisy stages use recovered and verified archived VQE fits with target depolarization after every CNOT.'}
    for stage in STAGES:
        started=time.time()
        if stage['source']=='exact':
            clean=exact_readout(stage['qubits'],kappas,hs);readout=clean['readout'];outcomes=clean['outcomes']
        else:
            index=int(np.flatnonzero(np.isclose(recovered['noise'],stage['p']))[0]);readout=recovered['readout'][index];outcomes=recovered['outcomes']
        means=readout@outcomes;second=readout@(outcomes**2);sd=np.sqrt(np.maximum(0,second-means**2))
        covariance=readout@(outcomes[:,0]*outcomes[:,1])-means[:,:,0]*means[:,:,1]
        z1,z2=means[:,:,0],means[:,:,1]
        if stage['source']=='scan':
            np.testing.assert_allclose(z1,scan[f"p{stage['p']}_zz1"],atol=1e-7,rtol=0)
            np.testing.assert_allclose(z2,scan[f"p{stage['p']}_zz2"],atol=1e-7,rtol=0)
        truth=classify(z1,z2,kappas,hs);agreement=float((truth[ref!=3]==ref[ref!=3]).mean())
        payload['stages'].append({**stage,'zz1':z1.round(8).tolist(),'zz2':z2.round(8).tolist(),
          'sd1':sd[:,:,0].round(8).tolist(),'sd2':sd[:,:,1].round(8).tolist(),'cov12':covariance.round(8).tolist(),
          'outcomes':outcomes.tolist(),'readout':readout.round(12).tolist(),'truth':truth.tolist(),'agreement_with_analytic':round(agreement,4)})
        print(stage['id'],f'{agreement:.2%}',f'{time.time()-started:.1f}s',flush=True)
    text=json.dumps(payload,separators=(',',':'))
    (ROOT/'game/dataset.json').write_text(text);(ROOT/'game/dataset.js').write_text('window.PHASE_HUNTER_DATA = '+text+';\n')
    print(f'Wrote joint readout stages: {len(text)/1024:.0f} KB')
if __name__=='__main__':main()
