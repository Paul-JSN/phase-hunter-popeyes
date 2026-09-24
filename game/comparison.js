/* Saved scientific results only. Nothing here fabricates or fits map values. */
(() => {
  'use strict';
  const root = document.getElementById('comparisonContent');
  const data = window.PHASE_COMPARISON;
  if (!root) return;
  if (!data) {
    root.innerHTML = '<p class="comparison-error">Comparison data could not load. Reload the page to try again.</p>';
    return;
  }
  const colors = ['#34C2B0', '#E08B45', '#9B7BD4'];
  const percent = value => (100 * value).toFixed(1) + '%';
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const titles = {clean: 'Clean', noisy: 'Noisy', corrected: 'Corrected'};
  const subtitles = {
    clean: 'Same prepared circuit, no gate noise. p = 0.',
    noisy: '5% depolarizing noise after each CNOT. p = 0.05.',
    corrected: 'Extrapolated to p = 0 from p = 0.01 and 0.05.'
  };
  function mapSVG(key) {
    const W=360,H=310,L=66,R=18,T=18,B=60;
    const ks=data.kappas,hs=data.hs;
    const x=k=>L+(k-ks[0])/(ks.at(-1)-ks[0])*(W-L-R);
    const y=h=>H-B-(h-hs[0])/(hs.at(-1)-hs[0])*(H-T-B);
    const xb=i=>i===0?L:i===ks.length?W-R:(x(ks[i-1])+x(ks[i]))/2;
    const yb=i=>i===0?H-B:i===hs.length?T:(y(hs[i-1])+y(hs[i]))/2;
    let cells='';
    data.maps[key].labels.forEach((row,a)=>row.forEach((label,b)=>{
      cells+=`<rect x="${xb(b)}" y="${yb(a+1)}" width="${xb(b+1)-xb(b)}" height="${yb(a)-yb(a+1)}" fill="${colors[label]}"/>`;
    }));
    const border = labels => {
      let d='';
      for(let a=0;a<hs.length;a++) for(let b=0;b<ks.length;b++) {
        if(b+1<ks.length && labels[a][b]!==labels[a][b+1]) d+=`M${xb(b+1)},${yb(a)}V${yb(a+1)}`;
        if(a+1<hs.length && labels[a][b]!==labels[a+1][b]) d+=`M${xb(b)},${yb(a+1)}H${xb(b+1)}`;
      }
      return d;
    };
    let ticks='';
    for(let i=0;i<=4;i++) {
      const k=ks[0]+i/4*(ks.at(-1)-ks[0]),h=hs[0]+i/4*(hs.at(-1)-hs[0]);
      ticks+=`<text x="${x(k)}" y="${H-B+22}" text-anchor="middle">${k.toFixed(2)}</text><text x="${L-10}" y="${y(h)}" text-anchor="end" dominant-baseline="middle">${h.toFixed(1)}</text>`;
    }
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="mapTitle-${key} mapDesc-${key}">
      <title id="mapTitle-${key}">${titles[key]} classified phase map</title>
      <desc id="mapDesc-${key}">Frustration 0 to 1, field strength 0 to 2. Ordered area ${percent(data.maps[key].ordered_area)}; ${percent(data.maps[key].agreement_to_clean)} agreement with the clean map.</desc>
      <g shape-rendering="crispEdges">${cells}</g>
      <path d="${border(data.maps[key].labels)}" fill="none" stroke="#fff9e8" stroke-width="1.5"/>
      <path class="clean-border" d="${border(data.maps.clean.labels)}" fill="none" stroke="#173749" stroke-width="2" stroke-dasharray="4 3"/>
      <path d="M${L},${T}V${H-B}H${W-R}" fill="none" stroke="#284854"/>
      ${ticks}<text x="${(L+W-R)/2}" y="${H-12}" text-anchor="middle">Frustration (κ)</text>
      <text x="17" y="${(T+H-B)/2}" text-anchor="middle" transform="rotate(-90 17 ${(T+H-B)/2})">Field strength (h)</text>
    </svg>`;
  }
  root.innerHTML = `
    <h2>One magnet. Three maps.</h2>
    <p class="lede">Noise weakens the measured correlations. A fixed classifier then draws a different map. How much can correction recover?</p>
    <div class="map-toolbar">
      <div class="map-legend" aria-label="Phase colors">
        <span><i style="background:${colors[0]}"></i>Ferromagnetic</span>
        <span><i style="background:${colors[2]}"></i>Antiphase</span>
        <span><i style="background:${colors[1]}"></i>Paramagnetic</span>
      </div>
      <label><input type="checkbox" id="cleanBoundary" checked>Overlay clean boundaries</label>
    </div>
    <div class="comparison-maps">
      ${['clean','noisy','corrected'].map(key=>`<figure class="comparison-map">
        <figcaption class="map-label"><h3>${titles[key]}</h3><p>${subtitles[key]}</p></figcaption>
        ${mapSVG(key)}
        <div class="map-metrics"><div><strong>${percent(data.maps[key].ordered_area)}</strong><span>Classified ordered area</span></div><div><strong>${percent(data.maps[key].agreement_to_clean)}</strong><span>Agreement with clean map</span></div><p class="signal-error">Mean signal error vs clean: ${data.maps[key].signal_mae.toFixed(4)}</p></div>
      </figure>`).join('')}
    </div>
    <p class="method-note"><span class="boundary-key"></span> Dashed: clean classified boundaries. White: each map's classified boundaries. All panels use the same 24 × 24 grid and the same clean classifier.</p>
    <p class="method-note"><b>Infinite-shot exponential extrapolation.</b> N = 8, classically simulated prepared circuits. “Clean” is the same variational circuit at p = 0, not the exact ground state. These finite-grid labels do not locate thermodynamic transitions.</p>
    <section class="comparison-insight" aria-labelledby="phaseResponseTitle">
      <h3 id="phaseResponseTitle">Why do the phases react differently?</h3>
      <p>Signal strength and classified area answer different questions. Compare the average signal inside each phase with the size of its labeled region.</p>
      <div class="insight-grid">${data.interiors.map(item=>`<article class="phase-insight" style="border-color:${item.phase==='ferro'?colors[0]:colors[2]}">
        <h4>${esc(item.label)}</h4>
        <dl><dt>Interior signal loss</dt><dd>${percent(item.signal_loss)}</dd><dt>Classified area loss</dt><dd>${percent(item.area_loss)}</dd></dl>
        <small>${item.points} interior points · ${esc(item.observable)} · p = 0 → 0.05</small>
      </article>`).join('')}</div>
      <p class="takeaway"><b>The stripe signal weakens more, yet the ferromagnetic region loses more area.</b> A point only changes label after it crosses the classifier's decision boundary. Interior attenuation alone cannot predict how many points cross it; the distribution of points near that boundary matters too.</p>
      <details><summary>What this does and does not explain</summary><p>Gate noise changes both correlations used by the classifier. The two orders and their prepared circuits respond differently in this archive. We have not isolated spin separation as the cause. The area changes describe the response of a fixed inference rule, not the disappearance of a physical phase.</p><p>Signal loss is the reduction of the mean absolute signal over a predefined interior region. Area loss is relative to that phase's full clean labeled area. The clean classifier is never refitted to noisy or corrected data.</p></details>
    </section>
    <section class="comparison-insight" aria-labelledby="shotsTitle">
      <h3 id="shotsTitle">Does correction help with fewer shots?</h3>
      <p>Each method gets the same total shots at every grid point. The corrected estimate splits its budget between two noise settings.</p>
      <div class="shot-controls"><span>Total shots per point</span><div class="shot-options" aria-label="Select total shot budget">${data.finite_shots.budgets.map(n=>`<button type="button" data-budget="${n}" aria-pressed="${n===100}">${n}</button>`).join('')}</div></div>
      <div id="shotResults" aria-live="polite"></div>
      <p class="method-note"><b>Finite-shot linear extrapolation.</b> This test uses a different estimator from the exponential correction above. ${data.finite_shots.seeds} simulated repeats on ${data.finite_shots.points} grid points; both correlators use the same whole-register shots. ± values show the standard deviation across repeats.</p>
      <details><summary>Experiment protocol and downloadable results</summary>
        <p>For budget B, the two uncorrected estimates use all B shots at p = 0.05 or p = 0.01. Correction uses B/2 at each noise setting and computes 1.25 C(0.01) − 0.25 C(0.05). We retain unclipped estimates and reuse paired shot batches across methods. The split is fixed, not optimized.</p>
        <p>Signal error averages absolute C1 and C2 error against the same prepared circuit at p = 0 across all 576 points. Map agreement compares the three phase labels using the same clean classifier, on all cells. It differs from the game's ordered-versus-disordered score. Noise probabilities are known; this is a simulation, not a hardware result.</p>
        <p>The reference and classifier are precomputed; calibration cost is excluded, and both noise settings are assumed equally costly per shot.</p>
        <p><a href="../data/comparison.json" download>Download full results (JSON)</a> · <a href="../scripts/make_comparison.py">Reproduction script</a></p>
      </details>
    </section>`;
  document.getElementById('cleanBoundary').addEventListener('change',event=>{
    root.querySelectorAll('.clean-border').forEach(path=>path.style.display=event.target.checked?'':'none');
  });
  function updateBudget(shots) {
    const row=data.finite_shots.results.find(r=>r.shots===shots);
    root.querySelectorAll('[data-budget]').forEach(button=>button.setAttribute('aria-pressed',Number(button.dataset.budget)===shots));
    const entries=[['noisy','No correction',`p = 0.05 · ${shots} shots`],['low_noise','Lower noise only',`p = 0.01 · ${shots} shots`],['corrected','Linear correction',`${shots/2} + ${shots/2} shots`]];
    const vsNoisy=row.paired_mae_improvement.vs_noisy;
    const vsLow=row.paired_mae_improvement.vs_low_noise;
    const helps = vsNoisy.ci95[0]>0;
    const beatsLow = vsLow.ci95[0]>0;
    const agreementCI=row.paired_agreement_improvement.vs_low_noise.ci95;
    const mapSummary=agreementCI[1]<0?'Map agreement is lower than using p = 0.01 alone.':agreementCI[0]>0?'Map agreement also improves over p = 0.01 alone.':'No clear difference in map agreement was resolved against p = 0.01 alone.';
    document.getElementById('shotResults').innerHTML=`<table class="shot-results"><thead><tr><th scope="col">Method</th><th scope="col">Signal error ↓</th><th scope="col">Clean-map agreement ↑</th></tr></thead><tbody>${entries.map(([key,label,allocation])=>`<tr class="${key==='corrected'?'corrected-row':''}"><th scope="row">${label}<span class="result-spread">${allocation}</span></th><td><span class="result-value">${row[key].mae.toFixed(4)}</span><span class="result-spread">± ${row[key].mae_sd.toFixed(4)}</span></td><td><span class="result-value">${percent(row[key].agreement)}</span><span class="result-spread">± ${(100*row[key].agreement_sd).toFixed(2)} pp</span></td></tr>`).join('')}</tbody></table>
      <p class="takeaway"><b>At ${shots} shots per point:</b> ${helps?'correction reduces mean signal error versus p = 0.05.':'correction does not show a clear mean-error advantage over p = 0.05.'} ${beatsLow?'It also lowers signal error compared with spending the entire budget at p = 0.01.':'Spending the entire budget at p = 0.01 is competitive or better: correction amplifies sampling noise.'} ${mapSummary}</p>`;
  }
  root.querySelectorAll('[data-budget]').forEach(button=>button.addEventListener('click',()=>updateBudget(Number(button.dataset.budget))));
  updateBudget(100);
})();
