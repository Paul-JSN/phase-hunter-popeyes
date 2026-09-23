/* Locally stored GIFs; source pages and upload credits: assets/famous/CREDITS.md.
   Captions describe player actions, never unrevealed phase labels. */
const FAMOUS_REACTIONS = (() => {
  const media = {
    ronaldo: ['Ronaldo · SUIII!', 'Ronaldo running and jumping in his Siuuu celebration'],
    math: ['Confused math lady', 'A confused woman surrounded by mathematical formulas'],
    fine: ['This is fine', 'The This is fine dog sitting in a burning room'],
    homer: ['Homer in the bushes', 'Homer Simpson backing into a hedge'],
    money: ['Take my money', 'Fry waving banknotes in Futurama'],
    leo: ['Leo pointing', 'Leonardo DiCaprio pointing at a television'],
    cook: ['Let him cook', 'Deadpool gesturing to let someone cook'],
    pikachu: ['Surprised Pikachu', 'Pikachu blinking with a surprised expression'],
    stonks: ['Not stonks', 'Meme Man beside a falling chart labelled not stonks'],
    brain: ['Galaxy brain', 'An animated glowing blue brain'],
    notes: ['SpongeBob takes notes', 'SpongeBob writing notes on a checklist'],
    travolta: ['Confused Travolta', 'John Travolta looking around in confusion']
  };
  const entries = {
    first_ping: ['leo', 'Me after ONE measurement: I know quantum physics.'],
    noisy_ping: ['math', '20 shots. 100% confidence. Absolutely no follow-up questions.'],
    cheap_habit: ['fine', 'Five bargain scans later: this is statistically fine.'],
    big_spend: ['money', 'SHUT UP AND TAKE MY SHOTS.'],
    repeat_ping: ['math', 'Same spot. Another scan. Peer review has entered the chat.'],
    floating_hit: ['homer', 'Me when the phase refuses to pick a side.'],
    broke: ['homer', 'My energy budget has left the chat.'],
    noise_up: ['fine', 'New stage. Same confidence. This is fine.'],
    reveal_high: ['ronaldo', 'SUIIII! Boundary located. Celebration justified.'],
    reveal_mid: ['leo', 'That bit! That bit was definitely science.'],
    reveal_low: ['homer', 'Me quietly deleting “quantum expert” from my bio.'],
    beat_agent: ['ronaldo', 'SUIIII! Human 1. Robot 0.'],
    lost_agent: ['math', 'The AI did the homework. I brought confidence.'],
    ai_start: ['cook', 'Hold up. Let him compute.'],
    repeat_changed: ['pikachu', 'Me discovering that probability means probability.'],
    overspend: ['stonks', 'More budget. No better score. Not stonks.'],
    personal_best: ['brain', 'New best. The brain has entered a new phase.'],
    tutorial_milestone: ['notes', 'Write that down. WRITE THAT DOWN.'],
    no_scans: ['travolta', 'Looking for evidence I never collected.']
  };
  const lessons = {
    first_ping: 'One scan samples one location. Map several locations before drawing a boundary.',
    noisy_ping: 'A strong reading with few shots can still fluctuate. Repeat it before trusting it.',
    cheap_habit: 'Cheap scans cover more ground, but each estimate has more sampling uncertainty.',
    big_spend: 'More shots reduce random scatter. They do not remove gate noise.',
    repeat_ping: 'Fresh measurements can differ at the same point. Combine evidence from repeated scans.',
    floating_hit: 'This finite-size classifier does not reliably identify the narrow floating phase.',
    broke: 'Spend some scans on coverage and save some to refine the uncertain boundary.',
    noise_up: 'Check the stage: gate noise changes readings, and ring size can change the phase pattern.',
    reveal_high: 'Broad scans find the rough border. Targeted scans help sharpen your estimate.',
    reveal_mid: 'Refine the spots where neighboring readings change from ORDER to CHAOS.',
    reveal_low: 'Bracket the boundary: find ORDER and CHAOS nearby, then scan between them.',
    beat_agent: 'You beat this baseline on this map. Try another map to test your strategy.',
    lost_agent: 'Try the AI demo: it brackets the boundary and scans between the two sides.',
    ai_start: 'The AI scans between two sides of a bracket, narrowing its boundary estimate.',
    repeat_changed: 'The state can stay the same while finite-shot estimates change. Repeat and combine evidence.',
    overspend: 'On this retry, more spending did not improve your score. Try changing where you scan.',
    personal_best: 'A new personal best! Compare scan choices on the same map to find what helped.',
    tutorial_milestone: 'You collected two scans. Compare their readings to guide your boundary, then refine it.',
    no_scans: 'Without scans, the line is a guess. Measure several locations before calling the border.'
  };
  // New event types inherit existing artwork when the famous pack is off.
  const fallbacks={ai_start:'first_ping',repeat_changed:'repeat_ping',overspend:'reveal_low',
    personal_best:'reveal_high',tutorial_milestone:'first_ping',no_scans:'reveal_low'};
  for(const [event,fallback] of Object.entries(fallbacks)) CARDS[event]={...CARDS[fallback]};
  const alternatives={
    noisy_ping:[['pikachu','My sample size: tiny. My conclusions: enormous.']],
    cheap_habit:[['stonks','Budget efficiency: stonks. Certainty: not stonks.']],
    repeat_ping:[['notes','Checking my work? In THIS economy?']],
    repeat_changed:[['math','Same coordinates. Different reading. My brain is buffering.']],
    broke:[['stonks','Energy: zero. Unanswered questions: several.']],
    reveal_mid:[['notes','Some of this was science. Taking notes for the sequel.']],
    reveal_low:[['travolta','The boundary was not where the vibes said it was.']],
    lost_agent:[['notes','Dear diary: today the algorithm had a plan.']]
  };
  const byEvent={}, pools={}, cards={}, turns={};
  for(const [event,entry] of Object.entries(entries)){
    pools[event]=[entry,...(alternatives[event]||[])].map(([file,text],index)=>{
      const id=`famous_${event}${index?'_'+index:''}`;
      CARDS[id]={scene:id,text};cards[id]={event,file};return id;
    });
    byEvent[event]=pools[event][0];
  }
  function choose(event){const pool=pools[event];if(!pool)return event;
    const turn=turns[event]||0;turns[event]=turn+1;return pool[turn%pool.length];}
  function lesson(id){return lessons[cards[id]?.event||id.replace(/^popeye_/,'')]||'';}
  function art(id, still = false) {
    const item = cards[id];
    if (!item) return '';
    const file = item.file, [name, alt] = media[file];
    return `<img class="famous-frame" src="assets/famous/${file}.${still ? 'png' : 'gif'}"
      alt="${alt}" onerror="this.onerror=null;this.src='assets/famous/${file}.png'">
      <span class="meme-credit">${name} · via Tenor</span>`;
  }
  // Explicit previews never advance the automatic rotation.
  const previews = ['reveal_high', 'noisy_ping', 'noise_up', 'broke', 'big_spend', 'first_ping',
    'ai_start','repeat_changed','overspend','personal_best','tutorial_milestone','no_scans'];
  return {
    byEvent, lessons, previews, art, choose, lesson, fallbacks,
    gallery() {
      return `<div class="kicker">${Object.keys(media).length} GIFs · ${Object.keys(cards).length} contextual captions</div>
        <h3>Laugh. Learn. Scan again.</h3>
        <p>Each GIF has a game-specific punchline and one useful idea. Tap a preview to see it move.
        Common events rotate through alternate jokes. SUIII celebrates a three-star result or an AI win.
        Your five personal recordings remain available in the separate Personal memes switch.</p>
        <div class="meme-gallery">${previews.map(event => {
          const id = byEvent[event];
          return `<figure><div class="gallery-art">${art(id, true)}</div>
            <figcaption><b>${CARDS[id].text}</b><p>${lessons[event]}</p>
            <button class="btn ghost" onclick="previewFamous('${event}')">Preview GIF</button></figcaption></figure>`;
        }).join('')}</div>
        <p class="small">GIFs play silently. With reduced motion enabled, still previews are shown.
        <a href="assets/famous/CREDITS.md" target="_blank" rel="noopener">Sources and credits</a></p>
        <button class="btn" id="closeFamousGallery">Back to the hunt</button>`;
    }
  };
})();
