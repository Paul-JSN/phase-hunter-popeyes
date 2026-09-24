"""Build the results narrative and tables from verified result files."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 load=lambda name:json.loads((ROOT/'data'/name).read_text())
 clean=load('summary.json');noise=load('noise_analysis.json');size=load('commensuration.json')
 budget=load('budget_study.json');large=load('large_n_cut_analysis.json');second=load('second_method.json');readout=load('readout_validation.json');finite=load('finite_shot_recalibration.json')
 finite_rows='\n'.join(f"| {p} | {shots} | {100*r['fixed']['mean']:.2f}% | {100*r['recalibrated']['mean']:.2f}% | {100*r['paired_gain']['mean']:+.2f} ± {100*r['paired_gain']['standard_error']:.3f} pp |" for p,rows in finite['noise'].items() for shots,r in rows.items())
 stages=['Clear skies','Static','Whiteout'];methods=['random','grid','bisect','adaptive']
 sizes='\n'.join(f"| {r['qubits']} | {'Yes' if r['period_four_fits'] else 'No'} | {r['zz2']:.3f} | {100*r['agreement_excluding_floating']:.1f}% |" for r in size['rows'])
 areas='\n'.join(f"| {p} | {100*r['fixed_rule']['ordered']:.2f}% | {100*r['recalibrated']['ordered']:.2f}% |" for p,r in noise['phase_areas'].items())
 scores='\n'.join('| '+stage+' | '+' | '.join(f"{100*budget[stage][m]['16']['mean']:.2f}%" for m in methods)+' |' for stage in stages)
 crossings='\n'.join('| '+stage+' | '+' | '.join(str(budget['pings_to_reach_90pct'][stage][m] or 'Not reached') for m in methods)+' |' for stage in stages)
 borderline='\n'.join(f"| {r['stage']} | {r['strategy']} | {r['budget']} | {100*r['mean']:.2f}% | {100*r['standard_error']:.2f} pp |" for r in budget['borderline_crossings']) or '| None | — | — | — | — |'
 fmt=lambda v:'No crossing' if v is None else f'{v:.3f}'
 cutrows='\n'.join(f"| {e['kappa']:.1f} | {p[1:]} | {r['attenuation_factor']:.3f} | {r['mean_residual_after_rescaling']:.4f} | {fmt(r['shift_fixed'])} | {fmt(r['shift_rescaled'])} |" for e in large['cuts'].values() for p,r in e['noise'].items())
 residuals=[v['mean_residual_after_rescaling'] for e in large['cuts'].values() for v in e['noise'].values()]
 shifts=[abs(v['shift_rescaled']) for e in large['cuts'].values() for v in e['noise'].values() if v['shift_rescaled'] is not None]
 quality=noise['vqe_quality'];fidelity=second['fidelity_susceptibility'];zne=second['zero_noise_extrapolation']
 text=f'''# Phase Hunter

**Team Popeyes (solo): Tanish Singh Rajpal**

Q-SITE 2026 · Quantum Coalition Scientific Track

Carnegie Mellon University, Information Networking Institute

**[Play the game](game/index.html)** — scan a hidden quantum phase map, spend a finite measurement budget, and try to beat the AI.

![Phase Hunter nautical interface with measured points and an educational reaction](figures/gameplay.png)

The first round is **Scan → Draw → Reveal**: one clean map, one scan strength, three clues before revealing. Stage choices, shot strengths and the AI appear after the first reveal; experienced players can skip ahead. Memes remain optional. No build step or account is needed.

After revealing, select **Why noise changes the map** for an interactive clean/noisy/recalibrated comparison and the finite-shot experiment below. Returning players can choose **Replay the simple demo**.

<details>
<summary>Watch a current gameplay recording</summary>

![A round in the current nautical interface](figures/gameplay.gif)

</details>

## Submission artifacts

- [Executed scientific notebook](phase_hunter.ipynb): model checks, commensuration, noisy inference, shared readout, strategy comparisons, fidelity, mitigation and N=12 cuts.
- [Three-page writeup](docs/Phase_Hunter_Writeup.pdf).
- [Playable browser experiment](game/index.html).
- Presentation video: still to be recorded.
- Team roster: **Team Popeyes, solo — Tanish Singh Rajpal**.

## Questions and contributions

1. **Does the ring fit the order?** A six-spin ring frustrates the period-four stripe and strongly degrades the same classifier's reference agreement.
2. **What does gate noise change?** Separate signal attenuation from the response of a fixed or recalibrated inference rule.
3. **How should a player spend measurements?** Compare four strategies at exact equal budgets, using shared whole-register shots and 200 seeds.
4. **Does the noise observation extend to a larger ring?** Test two completed noisy cuts at N=12, including preparation error and threshold shifts.
5. **Can another diagnostic corroborate the map?** Compare fidelity-susceptibility peaks with clustering, and quantify where they disagree.

The underlying quantum states are simulated classically. There is no hardware result, quantum-speedup claim, or claim that this game is impossible classically.

## Model and observables

The periodic axial next-nearest-neighbour Ising model is

`H = -Σ ZᵢZᵢ₊₁ + κ Σ ZᵢZᵢ₊₂ - h Σ Xᵢ`.

The scan spans κ∈[0,1] and h∈[0,2]. Two site-averaged observables provide the fingerprint:

| Observable | Interpretation |
|---|---|
| C1 = meanᵢ ⟨ZᵢZᵢ₊₁⟩ | Large positive values indicate neighboring spins align. |
| C2 = meanᵢ ⟨ZᵢZᵢ₊₂⟩ | Large negative values identify the ++-- stripe signature. |
| Both small | Weak Z correlations, characteristic of the paramagnetic region. |

Three seeded k-means clusters start in known phase interiors. The analytic floating-band reference is excluded from primary scoring because the classifier does not independently detect it. Finite-size label agreement should not be confused with a thermodynamic transition measurement.

### Clean N=8 diagram

The 40×40 PennyLane grid contains 1,600 exact ground states. Agreement with the handout's reference is **{100*clean['accuracy_excluding_floating']:.2f}% excluding floating cells**, or **{100*clean['accuracy_all_cells']:.2f}% over all cells**. An independent NumPy implementation agrees to approximately 3×10⁻¹⁴ in energies and correlators.

![Clean phase diagram](figures/clean_phase_diagram.png)

### Commensuration: the distinctive six-spin failure

A perfect period-four `++--` stripe closes on a ring only when N is divisible by four. On N=6, enumeration gives the strict bound **C2 ≥ −1/3** for every Z-basis bitstring; a quantum expectation is a convex average and obeys the same bound. For N=8 and N=12 the lower bound is −1.

At the same antiphase-interior point, **κ={size['kappa']}, h={size['h']}**, the exact ground-state values and matched-grid classifier scores are:

| Ring size | Period four fits? | C2 | 24×24 reference agreement |
|---|---|---:|---:|
{sizes}

![Commensuration signal and matched-grid classification scores](figures/commensuration.png)

The N=6 result is finite-ring frustration and a limitation of this correlation-based classifier. It does **not** mean that the infinite-model antiphase disappears. Choose N divisible by four when testing an unfrustrated stripe; other sizes are useful controlled frustration experiments. These 24×24 game-grid scores differ from the denser 40×40 headline metric above.

[Quantitative data](data/commensuration.json) · Rebuild with `python scripts/analyse_size.py`.

## Gate noise: signal attenuation versus classification

![The same prepared circuit: clean, noisy with the fixed rule, and recalibrated](figures/noise_comparison.png)

The three maps share axes and phase colours. “Clean” here means the same variational state without gate noise, not an exact ground state. **Recalibration changes the inferred labels; it does not repair the quantum state.**

The saved 24×24 N=8 scan fits a four-layer RY/RZ and CNOT-ring ansatz on `default.qubit`. Identical parameters are evaluated on `default.mixed` at p=0, 0.01 and 0.05. A target `DepolarizingChannel(p)` follows every CNOT. Keeping the prepared state fixed across noise strengths separates channel effects from preparation differences within each point.

| Noise p | Ordered area: fixed clean rule | Ordered area: recalibrated rule |
|---|---:|---:|
{areas}

A fixed classifier labels about **39% less area as ordered at p=0.05**. Recalibration recovers most area, with small boundary changes: the cut near κ=0.30 shifts one h-grid step. This establishes sensitivity of inferred labels to noisy observables, not invariance of physical transitions under noise.

![Noise comparison](figures/phase_diagrams_noise.png)

The selected antiphase interior loses about 47% of its order parameter versus 40% for the ferromagnetic interior. This is an empirical circuit-dependent comparison; distance alone is not isolated as its cause.

Preparation remains imperfect: mean energy error **{quality['energy_error_mean']:.3f}**, maximum **{quality['energy_error_max']:.3f}**, and **{quality['points_above_0_05']}/576** points above 0.05. Mean correlator errors versus exact states are 0.027 and 0.042. Future scans retain the better warm/cold fit and save parameters; the archived expectation values used here remain unchanged.

### Does recalibration survive limited shots?

We tested **20, 100 and 500 whole-register shots per point**, at p=0.01 and 0.05, over **200 seeds**. Each paired comparison uses exactly the same noisy observations. The fixed rule starts with centroids from noiseless simulations; recalibration learns centroids from that same measured map, with no extra quantum shots and no target labels.

| Gate noise p | Shots/point | Fixed-rule agreement | Recalibrated agreement | Paired gain ± standard error |
|---:|---:|---:|---:|---:|
{finite_rows}

At 5% noise, recalibration helps even at 20 shots per point. At 1% noise, it slightly **hurts** at 20 and 100 shots: refitting can introduce uncertainty when the original rule already works well. The result supports conditional usefulness, not automatic improvement.

![Finite-shot recalibration with standard-deviation error bars](figures/finite_shot_recalibration.png)

Scores compare against the noiseless labels of the **same prepared circuit**, with reference floating cells excluded. They measure recovery of an inferred map, not accuracy against exact thermodynamic phases. Error bars show one standard deviation across runs; the table reports standard errors of paired mean gains.

Each full 24×24 map costs **11,520 / 57,600 / 288,000** shots at these three settings. This is separate from the sparse game-ping budget study. Recalibration is transductive: it fits the map being scored, without labels. Generalization to a separate map, hardware noise and finite-shot zero-noise extrapolation remain untested.

[Results and protocol](data/finite_shot_recalibration.json) · `python scripts/finite_shot_recalibration.py`.

## Whole-register shots: use all the information

Both correlators are diagonal in Z. A single shot measures the full register and produces one bitstring z. From it compute `C_d(z) = (1/N) Σ zᵢzᵢ₊d` for **both** distances.

- Every one of the 20, 100 or 500 shots contributes to both estimates.
- Site averaging is performed within each readout; sites are not assumed independent.
- Bitstrings with identical (C1,C2) are grouped into joint outcomes without losing information about these observables.
- A ping samples multinomial counts over those outcomes. Estimates remain bounded, and the shared-shot covariance is retained.
- The ping covariance is the per-shot covariance divided by the shot count.

Two independent binomials would discard the joint statistics. Likewise, borrowing clean-state standard deviations for noisy states is not justified. The notebook compares against a random-pair protocol that splits preparations between distances and discards simultaneous readouts and spatial averaging.

The noisy archive originally saved only means. `recover_readout.py` replays its deterministic fits, verifies each saved energy and noisy mean, then stores circuit parameters and joint outcome probabilities. Maximum recovery discrepancy is **{readout['max_recovery_difference']:.2g}**. No target accuracy was used to tune these distributions.

[Readout validation](data/readout_validation.json) · [Recovered distributions](data/readout_N8.npz) · [Sampling implementation](src/measurement.py).

## Measurement-budget study

Random, grid, bisection and adaptive sampling each receive exactly **6, 10, 16, 24, 36 or 50 pings**, at **100 whole-register shots per ping**, across **200 seeds**. Grid fills its entire budget; bisection distributes leftover scans across columns.

A fixed heuristic `max(C1,-C2)>0.46` labels each measurement. Three-nearest weighted voting reconstructs the map. Scores compare with each stage's cluster labels, excluding reference floating cells. This reconstruction differs from the game's five-handle line.

![Whole-register budget study](figures/budget_study.png)

| Stage, 16 pings | Random | Grid | Bisection | Adaptive |
|---|---:|---:|---:|---:|
{scores}

### First tested budget reaching 90% mean agreement

| Stage | Random | Grid | Bisection | Adaptive |
|---|---:|---:|---:|---:|
{crossings}

These are crossings on a coarse budget ladder, not interpolated minimum costs or guarantees for an individual run. A strategy need not improve monotonically at every tested budget. Cross-stage changes mix noise, preparation and stage-specific classification; they do not isolate universal noise overhead.

### Borderline crossings

Any tested mean within **two standard errors of 90%** is flagged below, including points just below the line. Standard error is `sample SD / sqrt(200)`. Plot shading is **one standard deviation across runs**, not a confidence interval for the mean. The two-SE flag is an uncertainty screen, not a simultaneous confidence guarantee across all comparisons.

| Stage | Strategy | Pings | Mean | Standard error |
|---|---|---:|---:|---:|
{borderline}

[Full results and protocol](data/budget_study.json). Grid, bisection and adaptive sampling first reach 90% at 24 pings in Whiteout; random sampling remains below 90% through 50 pings, although its final mean is borderline. In Clear skies, all three structured strategies first cross at 24 versus 36 for random, whose crossing is also borderline.

## Larger-system extension: noisy N=12 cuts

The completed run contains **18 points: two nine-point cuts** at κ=0.2 and κ=0.8, h=0.1…1.3 with spacing 0.15. The four-layer variational circuit uses the same target-channel placement as N=8. This tests whether attenuation and inference sensitivity persist at larger N without claiming a full noisy N=12 phase diagram.

Fit one attenuation factor α per cut, then compare a fixed 0.46 threshold with the rescaled threshold α×0.46. Shifts below are relative to the same cut's p=0 crossing; a negative shift means a lower h. “No crossing” means the fixed threshold was not crossed in the sampled interval.

| κ | p | Attenuation α | Mean rescaling residual | Fixed shift Δh | Rescaled shift Δh |
|---:|---:|---:|---:|---:|---:|
{cutrows}

![N=12 noisy cuts with fixed and rescaled thresholds](figures/large_n_cut.png)

Across the four cut/noise combinations, the largest mean residual after rescaling is **{max(residuals):.4f}** and the largest available absolute rescaled-crossing shift is **{max(shifts):.3f} in h**, compared with spacing 0.15. This supports approximate attenuation of these sampled observables to the extent shown by those residuals; it does not prove invariant thermodynamic boundaries.

N=12 preparation-energy errors are **{large['preparation_energy_error']['mean']:.3f} mean** and **{large['preparation_energy_error']['max']:.3f} maximum**. Sparse interpolation, the chosen threshold and remaining fit error limit interpretation. This completed larger-system noise experiment is the evidence relevant to the rubric extension; credit is the judges' decision.

[Raw cuts](data/large_n_cut.json) · [Analysis](data/large_n_cut_analysis.json) · `python scripts/large_n_cut.py --analyse-only`.

## Independent diagnostic and mitigation

Fidelity susceptibility is calculated in a fixed translation-invariant, spin-flip-even sector, excluding h=0 from the stencil. For h>0 the unique positive ground state lies in this sector, avoiding arbitrary near-degenerate symmetry partners. No classifier labels enter the calculation.

Mean peak deviation from the analytic reference is **{fidelity['mean_abs_deviation_from_analytic']:.3f} in h**, at spacing **{fidelity['grid_spacing_in_h']:.3f}**. Mean disagreement with clustering is **{fidelity['mean_abs_gap_to_clustering']:.3f}**: the methods do not agree within one grid step on average.

![Independent diagnostic and mitigation](figures/second_method.png)

Two-point exponential extrapolation from p=0.01 and 0.05 reduces mean C1/C2 errors from **{zne['mean_abs_error_before']['zz1']:.3f}/{zne['mean_abs_error_before']['zz2']:.3f}** to **{zne['mean_abs_error_after']['zz1']['exponential']:.4f}/{zne['mean_abs_error_after']['zz2']['exponential']:.4f}**. The target is the **same variational state at p=0**, not the exact ground state. This infinite-shot experiment does not test finite-shot error amplification, unknown noise or hardware performance.

## Play, learn and replay

Five stages cover clean N=8, N=8 with 1% or 5% gate noise, frustrated clean N=6, and clean N=12. The N=12 game stage is clean; the larger-system noisy cuts above are a separate scientific experiment.

Practice supplies labels and 90 energy; Hunter removes hints and supplies 60. Weak/solid/deep scans cost 1/2/4 energy for 20/100/500 shots. The AI spends the same energy on the same map: 45 solid scans in Practice or 30 in Hunter. Its scans animate and remain visible until **Your turn — same map** restores the player's budget. Retry preserves the target; New map clears it.

The introductory round fixes Practice mode and 100 shots per scan. It teaches with on-map ORDER/CHAOS labels and only one early reaction, then unlocks the full game after reveal. Detailed colour keys and meme settings are expandable. The comparison screen offers 1%/5% noise and 20/100/500-shot result selectors, plus an explicit explanation of what recalibration does.

The nautical theme uses chart paper, navy controls, sailor-red actions and spinach-green selections. Phase colors retain their scientific meaning.

**Personal memes** and **Famous meme GIFs** have independent switches. Both default on, alternating where both fit. Twelve GIFs and twenty-seven contextual captions attach short lessons to meaningful events. SUIII celebrates measured three-star results or AI wins; a no-scan reveal gets confused Travolta. Common events rotate through variants. Popeye supplies three fallback stills with thirteen captions.

<details>
<summary>Preview the current reaction library</summary>

![Current GIF reactions and learning tips](figures/memes.gif)

</details>

The original personal recordings remain available. **Memes: off** removes reaction popups and result artwork; reduced-motion mode uses still GIF previews and manual personal playback. Media are credited separately from the software license: [GIF credits](game/assets/famous/CREDITS.md), [Popeye credits](game/assets/popeye/CREDITS.md).

## Reproduce

Use a fresh Python environment with `requirements.txt`; Jupyter is optional for opening the notebook interactively. The notebook builder executes and embeds every code cell without requiring Jupyter.

```bash
python -m pip install -r requirements.txt
python scripts/run_pennylane.py --check --qubits 8
python scripts/make_stages.py
python scripts/analyse_size.py
python scripts/analyse_noise.py --qubits 8
python scripts/finite_shot_recalibration.py
python scripts/budget_study.py
python scripts/second_method.py
python scripts/large_n_cut.py --analyse-only
python scripts/write_readme.py
python scripts/build_notebook.py
python scripts/make_writeup.py
python -m unittest discover -s tests -v
node tests/test_game.cjs
```

The shipped readout and exact-state caches make stage regeneration inexpensive. To independently recover the archived noisy distributions, remove the relevant recovery cache/output in a working copy and run:

```bash
python scripts/recover_readout.py --workers 2
```

This is the expensive step: it replays VQE preparation, checks every archived energy and mean, and writes resumable checkpoints. The output records its source archive hash. To rebuild the clean headline grid, run `python scripts/make_dataset.py --qubits 8 --grid 40 --backend pennylane`, then `python scripts/make_figures.py`.

To record the current interface:

```bash
python -m pip install playwright pillow
python -m playwright install chromium
python scripts/make_gifs.py
```

The recorder uses stable control IDs and measured element bounds, validates non-static frames, and writes `figures/gameplay.png`, `figures/gameplay.gif` and `figures/memes.gif`.

## Validation and limits

[Validation record](data/validation.json) documents Hamiltonian equality, clean-grid cross-checks and the archived scan hash. [Readout validation](data/readout_validation.json) documents recovered-state agreement. These are records tied to specific inputs, not automatically refreshed certificates.

Tests cover joint sampling means/variance/covariance, exact budgets, ring-size bounds, basis-invariant fidelity, better-fit persistence, visible AI progress, same-map handoff, reaction switches and victory conditions.

Remaining limitations: unresolved floating phase; finite-ring and VQE bias; heuristic inference rules; sparse larger-system cuts; no finite-shot zero-noise-extrapolation experiment or held-out calibration transfer; no hardware run or quantum advantage. The presentation video remains to be recorded.

## Sources

- [Quantum Coalition Scientific Track handout and starter kit](https://github.com/benmcdonough20/QSITE-2026-QuantumCoalition/tree/main/Scientific%20Track).
- [PennyLane ANNNI tutorial](https://pennylane.ai/qml/demos/tutorial_annni).
- [Computational-basis probabilities (`qml.probs`)](https://docs.pennylane.ai/en/stable/code/api/pennylane.probs.html).
- [PennyLane DepolarizingChannel](https://docs.pennylane.ai/en/stable/code/api/pennylane.DepolarizingChannel.html).
'''
 (ROOT/'README.md').write_text(text);print('Wrote README.md from current results')
if __name__=='__main__':main()
