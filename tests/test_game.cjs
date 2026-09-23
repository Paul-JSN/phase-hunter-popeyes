const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const {sample}=require('../game/measurement.js');
const outcomes=[[1,1],[-1,1],[0,-1]],probabilities=[.4,.1,.5];
assert.deepEqual(sample([1],[[1,1]],100),[1,1]);
assert.throws(()=>sample(probabilities,outcomes,0));
let seed=3;const rng=()=>((seed=(1664525*seed+1013904223)>>>0)/4294967296);
let sum=0,sumsq=0,sumB=0,sumAB=0,N=20000;
for(let i=0;i<N;i++){
  const [a,b]=sample(probabilities,outcomes,100,rng);sum+=a;sumsq+=a*a;sumB+=b;sumAB+=a*b;
  assert.ok(Math.abs(a)<=1&&Math.abs(b)<=1);
}
assert.ok(Math.abs(sum/N-.3)<.003);
assert.ok(Math.abs(sumsq/N-(sum/N)**2-.0041)<.00025);
assert.ok(Math.abs(sumAB/N-(sum/N)*(sumB/N)-.003)<.00025);
const elements={};const handlers={};
const context2d=new Proxy({measureText:()=>({width:30})},{get:(o,k)=>o[k]??(()=>{})});
function element(id){return elements[id]??=( {children:[],style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},appendChild(x){this.children.push(x)},remove(){},scrollIntoView(){},setAttribute(){},getContext:()=>context2d,width:720,height:560,addEventListener:(name,fn)=>{handlers[name]=fn},getBoundingClientRect:()=>({left:0,top:0,width:720,height:560})});}
const timers=[];
const scope={console,Math,Date,setTimeout:fn=>{timers.push(fn);return timers.length},localStorage:{getItem:()=>null,setItem(){}},document:{getElementById:element,createElement:()=>element(Math.random())},window:{addEventListener(){}}};
vm.createContext(scope);
vm.runInContext(fs.readFileSync('game/dataset.js','utf8'),scope);
vm.runInContext(fs.readFileSync('game/measurement.js','utf8'),scope);
vm.runInContext(fs.readFileSync('game/memes.js','utf8'),scope);
vm.runInContext(fs.readFileSync('game/popeye-memes.js','utf8'),scope);
vm.runInContext(fs.readFileSync('game/famous-memes.js','utf8'),scope);
let source=fs.readFileSync('game/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(source,scope);
vm.runInContext('memesOn=false;',scope);
const read=code=>vm.runInContext(code,scope);
async function drain(){
  while(timers.length){timers.shift()();await Promise.resolve();}
}
async function main(){
  const initial=read('JSON.stringify(view)');
  read('shots=20');
  const run=elements.agent.onclick();
  assert.equal(read('aiRunning'),true);
  assert.equal(read('pings.length'),1,'first scan must appear before the next animation frame');
  assert.match(elements.aiStatusTitle.textContent,/AI scanning/);
  assert.equal(elements.agent.disabled,true);
  assert.equal(elements.reveal.disabled,true);
  // Repeated clicks and player actions cannot alter an AI run.
  await elements.agent.onclick();
  read('ping(kLo(),hLo())');
  handlers.pointerdown({clientX:200,clientY:200});
  elements.reveal.onclick();
  assert.equal(read('pings.length'),1);
  assert.equal(read('revealed'),false);
  await drain();await run;
  assert.equal(read('JSON.stringify(view)'),initial);
  assert.equal(read('aiRunning'),false);
  assert.equal(read('aiPreview'),true);
  assert.equal(read('energy'),0);
  assert.equal(read('pings.length'),45,'keep AI scans visible after finishing');
  assert.equal(read('shots'),100,'AI preview shows the power used by its scans');
  assert.equal(elements.takeTurn.hidden,false);
  const target=read('agentScore');assert.ok(target>=0&&target<=1);
  assert.match(elements.aiStatusTitle.textContent,/AI finished/);
  assert.match(elements.aiStatusDetail.textContent,/45 scans/);
  const aiHandles=read('JSON.stringify(handles)');
  handlers.pointerdown({clientX:200,clientY:200});elements.template.onclick();elements.reveal.onclick();
  assert.equal(read('JSON.stringify(handles)'),aiHandles);
  assert.equal(read('revealed'),false,'AI demo must not be submitted as a human score');
  elements.takeTurn.onclick();
  assert.equal(read('agentScore'),target);
  assert.equal(read('JSON.stringify(view)'),initial);
  assert.equal(read('energy'),90);assert.equal(read('pings.length'),0);
  assert.equal(read('aiPreview'),false);assert.equal(elements.reveal.disabled,false);
  assert.equal(read('shots'),20,'restore the player scan power at handoff');
  elements.reset.onclick();assert.equal(read('agentScore'),target);
  read('shots=100; ping(kLo(),hLo())');assert.equal(read('energy'),88);
  elements.reveal.onclick();assert.equal(read('revealed'),true);
  assert.match(elements.sheet.innerHTML,/AI/,'human result retains AI comparison');
  const before=read('JSON.stringify(handles)');
  handlers.pointerdown({clientX:200,clientY:200});elements.template.onclick();
  assert.equal(read('JSON.stringify(handles)'),before);assert.equal(read('pings.length'),1);
  elements.newMap.onclick();assert.equal(read('agentScore'),null);assert.equal(read('revealed'),false);
  // Cancelling an in-flight animation must not write into the replacement round.
  const cancelled=elements.agent.onclick();assert.equal(read('pings.length'),1);
  elements.newMap.onclick();
  const newView=read('JSON.stringify(view)');
  await drain();await cancelled;
  assert.equal(read('JSON.stringify(view)'),newView);assert.equal(read('pings.length'),0);
  assert.equal(read('energy'),90);assert.equal(read('agentScore'),null);
  assert.equal(read('aiRunning'),false);assert.equal(elements.agent.disabled,false);
  // Hunter mode has 60 energy, hence exactly 30 solid scans.
  read('mode="hunter";newRound()');
  const hunter=elements.agent.onclick();await drain();await hunter;
  assert.equal(read('pings.length'),30);assert.equal(read('energy'),0);
  elements.takeTurn.onclick();assert.equal(read('energy'),60);assert.equal(read('pings.length'),0);
  assert.ok(!source.includes('truth ${'));
  // Every automatic pack combination, plus explicit previews, must honor its switches.
  read('memesOn=true;useClips=true;famousOn=true;mixedMemeCount=0');
  assert.equal(read('chooseReaction("reveal_high")'),'famous_reveal_high');
  assert.equal(read('chooseReaction("reveal_high")'),'reveal_high');
  assert.match(read('art("reveal_high")'),/clips\/cards\/reveal_high.webm/);
  assert.match(read('art("famous_reveal_high")'),/ronaldo.gif/);
  elements.clips.onclick();
  assert.equal(read('useClips'),false);
  assert.equal(read('chooseReaction("reveal_high")'),'famous_reveal_high');
  assert.equal(elements.testMeme.disabled,true);
  elements.famous.onclick();
  assert.equal(read('chooseReaction("reveal_high")'),'popeye_reveal_high');
  elements.clips.onclick();
  assert.equal(read('chooseReaction("reveal_high")'),'reveal_high');
  assert.equal(read('chooseReaction("first_ping")'),'popeye_first_ping');
  elements.clips.onclick();elements.popeye.onclick();
  assert.equal(read('chooseReaction("reveal_high")'),'reveal_high');
  assert.ok(!read('art("reveal_high")').includes('<video'));
  scope.window.matchMedia=()=>({matches:true});
  assert.match(read('art("famous_reveal_high")'),/ronaldo.png/);
  read('useClips=true');
  assert.ok(!read('art("reveal_high")').includes('autoplay'));
  elements.memes.onclick();
  const count=elements.cards.children.length;
  read('react("first_ping", "", true)');
  assert.equal(elements.cards.children.length,count);
  read('showResult("reveal_high",.97)');
  assert.ok(!elements.sheet.innerHTML.includes('big-art'));
  assert.match(elements.sheet.innerHTML,/Your expedition results/);
  assert.match(elements.sheet.innerHTML,/Targeted scans/);
  assert.equal(elements.previewFamous.disabled,true);
  // Rotating variants retain their event's lesson; previews don't advance rotation.
  const variant1=read('FAMOUS_REACTIONS.choose("repeat_changed")');
  const variant2=read('FAMOUS_REACTIONS.choose("repeat_changed")');
  assert.notEqual(variant1,variant2);
  assert.equal(read('FAMOUS_REACTIONS.choose("repeat_changed")'),variant1);
  assert.equal(read(`reactionLesson(${JSON.stringify(variant1)})`),read(`reactionLesson(${JSON.stringify(variant2)})`));
  assert.equal(read('FAMOUS_REACTIONS.previews.length'),12);
  const previewFiles=read('FAMOUS_REACTIONS.previews.map(e=>FAMOUS_REACTIONS.art(FAMOUS_REACTIONS.byEvent[e]).match(/src="([^"]+)"/)[1])');
  assert.equal(new Set(previewFiles).size,12);
  for(const file of previewFiles) assert.ok(fs.existsSync('game/'+file));
  // A lucky no-scan guess must never receive a victory GIF.
  read('pings=[];agentScore=.8;lastAttempt=null');
  assert.equal(read('resultEvent(1,70,0)'),'no_scans');
  read('pings=[{}];agentScore=null');
  assert.equal(read('resultEvent(.9,85,20)'),'personal_best');
  assert.equal(read('resultEvent(.9,null,20)'),'reveal_mid');
  assert.equal(read('resultEvent(.98,85,20)'),'reveal_high');
  read('agentScore=.8');assert.equal(read('resultEvent(.9,85,20)'),'beat_agent');
  read('agentScore=null;lastAttempt={score:.87,spent:20};mode="hunter"');
  assert.equal(read('resultEvent(.82,90,50)'),'overspend');
  assert.notEqual(read('resultEvent(.82,90,20)'),'overspend');
  read('newRound()');assert.equal(read('lastAttempt'),null);
  // With famous GIFs disabled, the six new events still have valid fallback artwork.
  read('famousOn=false;useClips=false');
  for(const event of ['ai_start','repeat_changed','overspend','personal_best','tutorial_milestone','no_scans']) {
    assert.ok(read(`art(chooseReaction(${JSON.stringify(event)}))`).length);
  }
  console.log('Expanded pack tests passed: 12 unique previews, rotation, contextual lessons, milestone selection, and fallback coverage.');
  console.log('Meme tests passed: mixed/personal/famous/fallback routing, all-off results, quiet popups, and reduced-motion assets.');
  console.log('Game tests passed: visible AI progress, persistent demo, explicit player handoff, 45/30 scans, cancellation, locked AI scoring, and preserved rematches.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
