/* Actual cartoon stills, sourced and credited in assets/popeye/CREDITS.md.
   Every original event has a Popeye counterpart. No automatic alternation.
   Existing recorded videos retain priority when Recorded clips is on. */
const POPEYE_REACTIONS = (() => {
  const frames={
    helm:{file:'popeye.png',alt:'Popeye at the ship wheel in the original 1936 cartoon'},
    faceoff:{file:'faceoff.png',alt:'Popeye standing up to Sindbad in the original 1936 cartoon'},
    rival:{file:'rival.jpg',alt:'Popeye squaring up to Sindbad in the original 1936 cartoon'}
  };
  const entries={
    first_ping:['helm','Ahoy, phase boundary. Prepare to be measured.'],
    noisy_ping:['helm','My confidence: 100%. My shots: 20.'],
    cheap_habit:['rival','Me challenging the whole phase diagram with 20 shots.'],
    big_spend:['faceoff','500 shots. Spinach has entered the chat.'],
    repeat_ping:['helm','Same coordinates. Fresh can of evidence.'],
    floating_hit:['helm','The phase is floating. So am I.'],
    broke:['rival','All out of spinach. Still got the attitude.'],
    noise_up:['faceoff','Me vs. 5% gate noise.'],
    reveal_high:['faceoff','A strong finish. Must be the spinach.'],
    reveal_mid:['helm','Slightly off course. Still the captain.'],
    reveal_low:['rival','I brought confidence to a measurement fight.'],
    beat_agent:['faceoff','The AI forgot to eat its spinach.'],
    lost_agent:['rival','The AI brought a bigger can.']
  };
  const byEvent={};
  for(const [event,[frame,text]] of Object.entries(entries)){
    const id=`popeye_${event}`,f=frames[frame];byEvent[event]=id;
    SCENES[id]=`<img class="popeye-frame" src="assets/popeye/${f.file}" alt="${f.alt}" width="564" height="428">`;
    CARDS[id]={scene:id,text};
  }
  return {
    ids:Object.values(byEvent),
    choose(id,enabled,hasRecordedClip){
      return enabled&&!hasRecordedClip ? (byEvent[id]||id) : id;
    },
    gallery(){
      return `<div class="kicker">Team Popeyes · original cartoon frames</div>
      <h3>The whole Popeye crew</h3>
      <p>All 13 reactions use frames from <i>Popeye the Sailor Meets Sindbad the Sailor</i> (1936).
      There are three distinct still images, reused across thirteen captions. Turn Personal memes and
      Famous meme GIFs off to use Popeye throughout. Your recordings remain available.</p>
      <div class="popeye-gallery">${Object.entries(byEvent).map(([event,id])=>`<figure>${SCENES[id]}<figcaption><b>${CARDS[id].text}</b><span>${event.replaceAll('_',' ')}</span></figcaption></figure>`).join('')}</div>
      <p class="small">Frames: Fleischer Studios / Dave Fleischer, via Wikimedia Commons.
      <a href="assets/popeye/CREDITS.md" target="_blank" rel="noopener">Sources and credits</a></p>
      <button class="btn" id="closePopeyeGallery">Back to the hunt</button>`;
    }
  };
})();
