import json
import unittest
from pathlib import Path
import numpy as np
from src.measurement import sample_correlators, single_shot_sd, sample_joint, joint_outcomes, joint_moments
from src.fidelity import invariant_basis, subspace_fidelity
from src.annni import AnnniChain
from scripts.budget_study import Stage, play, BUDGETS

ROOT=Path(__file__).resolve().parents[1]

class ScienceTests(unittest.TestCase):
    def test_sampling_mean_variance_and_range(self):
        rng=np.random.default_rng(74)
        draws=np.array([sample_correlators(.6,-.3,100,rng) for _ in range(30000)])
        np.testing.assert_allclose(draws.mean(axis=0),[.6,-.3],atol=.002)
        np.testing.assert_allclose(draws.var(axis=0),[(1-.6**2)/50,(1-.3**2)/50],rtol=.03)
        self.assertTrue(np.all(np.abs(draws)<=1))
        self.assertGreater(single_shot_sd(.6),0)
        self.assertEqual(sample_correlators(1,-1,20,rng),(1.,-1.))

    def test_joint_whole_register_variance_and_covariance(self):
        chain=AnnniChain(8);state,_=chain.ground_state(.3,.7)
        outcomes,inverse=joint_outcomes(8);p=np.bincount(inverse,weights=np.abs(state)**2,minlength=len(outcomes))
        means,cov=joint_moments(p,outcomes)
        expected=chain.measure(state)
        np.testing.assert_allclose(means,[expected['zz1'],expected['zz2']],atol=1e-12)
        np.testing.assert_allclose(np.diag(cov),np.array([expected['sd1'],expected['sd2']])**2,atol=1e-12)
        rng=np.random.default_rng(92)
        samples=np.array([sample_joint(p,outcomes,100,rng) for _ in range(20000)])
        np.testing.assert_allclose(samples.mean(axis=0),means,atol=.002)
        np.testing.assert_allclose(np.cov(samples.T),cov/100,atol=.00015)
        self.assertTrue(np.all(np.abs(samples)<=1))
        self.assertAlmostEqual(AnnniChain(6).zz2.min(),-1/3)
        self.assertEqual(chain.zz2.min(),-1)

    def test_projector_fidelity_different_ranks(self):
        lo=np.eye(4)[:,:2];hi=np.eye(4)[:,1:2]
        q=np.array([[.6,-.8],[.8,.6]])
        self.assertAlmostEqual(subspace_fidelity(lo,hi),1/np.sqrt(2))
        self.assertAlmostEqual(subspace_fidelity(lo@q,hi),subspace_fidelity(lo,hi))
        self.assertAlmostEqual(subspace_fidelity(lo,lo@q),1)

    def test_fixed_sector_has_full_ground_energy(self):
        chain=AnnniChain(8);basis=invariant_basis(8)
        np.testing.assert_allclose(basis.T@basis,np.eye(basis.shape[1]),atol=1e-14)
        for k,h in [(0,.05),(.3,.4),(.5,.05),(.8,.2),(1,2)]:
            matrix=chain.hamiltonian(k,h)
            self.assertAlmostEqual(np.linalg.eigvalsh(basis.T@matrix@basis)[0],np.linalg.eigvalsh(matrix)[0],places=10)

    def test_all_strategies_use_exact_budgets(self):
        data=json.loads((ROOT/'game/dataset.json').read_text());stage=Stage(data,data['stages'][0])
        original=stage.ping
        for method in ['random','grid','bisect','adaptive']:
            for budget in BUDGETS:
                calls=[]
                def ping(a,b,rng):
                    calls.append((a,b));return original(a,b,rng)
                stage.ping=ping
                value=play(stage,method,budget,np.random.default_rng(9))
                self.assertEqual(len(calls),budget,(method,budget))
                self.assertTrue(0<=value<=1)

class ScanPersistenceTests(unittest.TestCase):
    def test_worse_cold_refit_is_rejected_and_parameters_saved(self):
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts import run_pennylane
        args=SimpleNamespace(qubits=4,grid=2,layers=1,steps=1,warm_steps=1,energy_tol=.05,noise=[0.0])
        # Warm candidate is deliberately better than each attempted cold retry.
        candidates=[]
        for _ in range(4):
            candidates.extend([(np.ones((1,4,2)),90.0),(np.zeros((1,4,2)),100.0)])
        with TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            with patch.object(run_pennylane,'ROOT',root), patch('src.pennylane_pipeline.vqe_ground_state',side_effect=candidates), patch('src.pennylane_pipeline.noisy_correlators',return_value=(.5,-.5)):
                run_pennylane.scan(args)
            saved=np.load(root/'data/pennylane_scan_N4.npz')
            self.assertTrue(np.all(saved['energy_vqe']==90))
            self.assertEqual(saved['parameters'].shape,(2,2,1,4,2))
            self.assertTrue(np.all(saved['parameters']==1))
            self.assertEqual(saved['layers'],1)

if __name__=='__main__': unittest.main()
