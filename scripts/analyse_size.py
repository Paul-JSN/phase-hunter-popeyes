"""Quantify period-four commensuration on clean periodic rings."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.annni import AnnniChain

def main():
    data=json.loads((ROOT/'game/dataset.json').read_text())
    rows=[];kappa,h=.8,.1
    for n,id in [(6,'short6'),(8,'clean8'),(12,'long12')]:
        chain=AnnniChain(n);state,energy=chain.ground_state(kappa,h);m=chain.measure(state)
        stage=next(s for s in data['stages'] if s['id']==id)
        rows.append({'qubits':n,'period_four_fits':n%4==0,'zz2':m['zz2'],
          'minimum_possible_zz2':float(chain.zz2.min()),'energy':energy,
          'agreement_excluding_floating':stage['agreement_with_analytic']})
    report={'kappa':kappa,'h':h,'grid':data['grid'],'boundary':'periodic',
        'scoring':'stage three-cluster classification vs analytic reference; reference floating cells excluded',
        'rows':rows}
    (ROOT/'data/commensuration.json').write_text(json.dumps(report,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(10,3.3));colors=['#D4742B','#007F7A','#377CA8']
    axes[0].bar([str(r['qubits']) for r in rows],[-r['zz2'] for r in rows],color=colors)
    axes[0].set(xlabel='Ring size N',ylabel='Antiphase signal −C₂',title='Same point: κ=0.8, h=0.1',ylim=(0,1.13))
    axes[1].bar([str(r['qubits']) for r in rows],[100*r['agreement_excluding_floating'] for r in rows],color=colors)
    axes[1].set(xlabel='Ring size N',ylabel='Reference label agreement (%)',title='Same 24 × 24 grid; floating excluded',ylim=(0,110))
    for i,r in enumerate(rows):
        axes[0].text(i,-r['zz2']+.025,f"C₂={r['zz2']:.3f}",ha='center')
        axes[1].text(i,100*r['agreement_excluding_floating']+2,f"{100*r['agreement_excluding_floating']:.1f}%",ha='center')
    fig.tight_layout();fig.savefig(ROOT/'figures/commensuration.png',dpi=180)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
