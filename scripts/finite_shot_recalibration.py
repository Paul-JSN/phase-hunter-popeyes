"""Paired finite-shot test of map recalibration, using shared whole-register reads.

Both methods see exactly the same noisy observations. The fixed method uses
precomputed noiseless centroids; recalibration fits centroids to the measured map
without labels or additional quantum shots. This is transductive map inference,
not a held-out test of a calibration learned on another map, nor state recovery.
"""
from pathlib import Path
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.classify import fit_centroids,assign,classify
from src.reference import reference_labels,FLOATING

SEEDS=200
SHOTS=[20,100,500]
COLORS=['#007f7a','#d4742b','#7356a6']

def measure_map(probabilities,outcomes,shots,rng):
    shape=probabilities.shape[:-1]
    counts=np.array([rng.multinomial(shots,p/p.sum()) for p in probabilities.reshape(-1,probabilities.shape[-1])])
    return (counts@outcomes/shots).reshape(*shape,2)

def main():
    data=np.load(ROOT/'data/readout_N8.npz');k,h=data['kappas'],data['hs']
    outcomes=data['outcomes'];hist=data['readout'];means=hist@outcomes
    zero=int(np.flatnonzero(data['noise']==0)[0]);clean=means[zero]
    centroids=fit_centroids(clean[:,:,0],clean[:,:,1],k,h)
    target=assign(clean[:,:,0],clean[:,:,1],centroids)
    scored=reference_labels(*np.meshgrid(k,h))!=FLOATING
    report={'seeds':SEEDS,'shots_per_point':SHOTS,'grid':[len(h),len(k)],
      'target':'noiseless labels of the same prepared variational states; analytic floating cells excluded',
      'protocol':'Paired whole-register multinomial readouts. Both classifiers reuse the same full measured map; no extra calibration shots. Fixed centroids from infinite-shot noiseless simulations. Recalibration is unsupervised and transductive, not held-out generalization or quantum-state repair.',
      'noise':{}}
    maps={}
    for p in [.01,.05]:
        index=int(np.flatnonzero(np.isclose(data['noise'],p))[0]);rows={}
        noisy=means[index];fixed=assign(noisy[:,:,0],noisy[:,:,1],centroids)
        recal=classify(noisy[:,:,0],noisy[:,:,1],k,h)
        maps[str(p)]={'fixed':fixed.tolist(),'recalibrated':recal.tolist()}
        for shots in SHOTS:
            scores=[]
            for seed in range(SEEDS):
                sample=measure_map(hist[index],outcomes,shots,np.random.default_rng(2026000+seed))
                a=assign(sample[:,:,0],sample[:,:,1],centroids)
                b=classify(sample[:,:,0],sample[:,:,1],k,h)
                scores.append([(a[scored]==target[scored]).mean(),(b[scored]==target[scored]).mean()])
            scores=np.array(scores);gain=scores[:,1]-scores[:,0]
            row={'total_shots':int(shots*len(k)*len(h))}
            for i,name in enumerate(['fixed','recalibrated']):
                row[name]={'mean':float(scores[:,i].mean()),'sd':float(scores[:,i].std(ddof=1)),
                  'standard_error':float(scores[:,i].std(ddof=1)/np.sqrt(SEEDS))}
            row['paired_gain']={'mean':float(gain.mean()),'standard_error':float(gain.std(ddof=1)/np.sqrt(SEEDS)),
              'fraction_improved':float((gain>0).mean())}
            rows[str(shots)]=row
            print(f'p={p} shots={shots}: fixed {scores[:,0].mean():.3%}, recalibrated {scores[:,1].mean():.3%}',flush=True)
        report['noise'][str(p)]=rows
    (ROOT/'data/finite_shot_recalibration.json').write_text(json.dumps(report,indent=2)+'\n')
    payload={'kappas':k.tolist(),'hs':h.tolist(),'clean':target.tolist(),'maps':maps,'study':report,
      'decay':json.loads((ROOT/'data/noise_analysis.json').read_text())['order_parameter_decay']}
    (ROOT/'game/noise-comparison.js').write_text('window.NOISE_COMPARISON = '+json.dumps(payload,separators=(',',':'))+';\n')
    fig,axes=plt.subplots(1,3,figsize=(11,3.6),sharex=True,sharey=True)
    for ax,labels,title in zip(axes,[target,maps['0.05']['fixed'],maps['0.05']['recalibrated']],
      ['Clean · same circuit, p = 0','Noisy · p = 0.05, fixed rule','Recalibrated · same noisy data']):
        ax.imshow(labels,origin='lower',extent=[0,1,0,2],aspect='auto',cmap=ListedColormap(COLORS),vmin=0,vmax=2,interpolation='nearest')
        ax.set(title=title,xlabel='Frustration κ')
    axes[0].set_ylabel('Field h')
    fig.legend(handles=[Patch(color=c,label=l) for c,l in zip(COLORS,['Ferromagnetic','Paramagnetic','Antiphase'])],loc='lower center',ncol=3,frameon=False)
    fig.suptitle('Recalibration changes our interpretation, not the quantum state',fontsize=12)
    fig.tight_layout(rect=[0,.08,1,.96]);fig.savefig(ROOT/'figures/noise_comparison.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),sharey=True)
    for ax,(p,rows) in zip(axes,report['noise'].items()):
        for name,color in [('fixed','#d4742b'),('recalibrated','#007f7a')]:
            ax.errorbar(SHOTS,[100*rows[str(s)][name]['mean'] for s in SHOTS],
              yerr=[100*rows[str(s)][name]['sd'] for s in SHOTS],fmt='o-',capsize=4,color=color,label=name)
        ax.set(xscale='log',xticks=SHOTS,xticklabels=SHOTS,xlabel='Whole-register shots per point',title=f'Gate noise p = {p}',ylim=(65,101))
        ax.legend(frameon=False)
    axes[0].set_ylabel('Agreement with noiseless map (%)')
    fig.suptitle('Same measurements for both methods · 200 seeds · bars: ±1 SD',fontsize=11)
    fig.tight_layout();fig.savefig(ROOT/'figures/finite_shot_recalibration.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
