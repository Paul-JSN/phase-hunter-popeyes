/* Phase Hunter reaction art.
   Every scene below is drawn from scratch as SVG: our own mascot (Spinny, a
   spin arrow with a face), our own props, our own captions. No copyrighted
   meme images, photographs, or real people's likenesses ship with this game.  */

const MEME_PALETTE = {
  ink:"#0B1424", skin:"#2FB3A3", skin2:"#26907F", light:"#E8F0F4",
  orange:"#E08B45", purple:"#9B7BD4", blue:"#5C9BD1", grey:"#7C93A8", dark:"#16283F"
};

/* ---- the mascot ------------------------------------------------------- */
function face(mood){
  const P = MEME_PALETTE;
  return {
    neutral:`<circle cx="-5" cy="-3" r="2" fill="${P.ink}"/><circle cx="5" cy="-3" r="2" fill="${P.ink}"/>
             <path d="M-6 5 q6 4 12 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    cool:`<rect x="-12" y="-7" width="24" height="8" rx="2" fill="${P.ink}"/>
          <path d="M-12 -7 h-4 M12 -7 h4" stroke="${P.ink}" stroke-width="2" stroke-linecap="round"/>
          <path d="M-6 6 q6 5 12 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    shock:`<circle cx="-5" cy="-4" r="3.2" fill="${P.ink}"/><circle cx="5" cy="-4" r="3.2" fill="${P.ink}"/>
           <ellipse cx="0" cy="6" rx="4" ry="5" fill="${P.ink}"/>`,
    sweat:`<circle cx="-5" cy="-3" r="2" fill="${P.ink}"/><circle cx="5" cy="-3" r="2" fill="${P.ink}"/>
           <path d="M-6 7 q6 -4 12 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>
           <path d="M13 -10 q3 5 0 7 q-3 -2 0 -7" fill="${P.blue}"/>`,
    flat:`<circle cx="-5" cy="-3" r="2" fill="${P.ink}"/><circle cx="5" cy="-3" r="2" fill="${P.ink}"/>
          <path d="M-6 6 h12" stroke="${P.ink}" stroke-width="2" stroke-linecap="round"/>`,
    smug:`<path d="M-8 -4 q3 -3 6 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>
          <path d="M2 -4 q3 -3 6 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>
          <path d="M-5 6 q7 3 11 -2" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    dizzy:`<path d="M-8 -6 l6 6 M-2 -6 l-6 6" stroke="${P.ink}" stroke-width="2" stroke-linecap="round"/>
           <path d="M2 -6 l6 6 M8 -6 l-6 6" stroke="${P.ink}" stroke-width="2" stroke-linecap="round"/>
           <path d="M-5 7 q5 -5 10 0" stroke="${P.ink}" stroke-width="2" fill="none" stroke-linecap="round"/>`
  }[mood] || "";
}
function spin(mood, x=0, y=0, size=1, tilt=0, glow=0){
  const P = MEME_PALETTE;
  return `<g transform="translate(${x} ${y}) scale(${size}) rotate(${tilt})">
    ${glow ? `<circle r="30" fill="${P.skin}" opacity="${0.12*glow}"/><circle r="24" fill="${P.skin}" opacity="${0.12*glow}"/>`:""}
    <circle r="21" fill="${P.skin}"/><circle r="21" fill="none" stroke="${P.skin2}" stroke-width="2"/>
    <path d="M0 -20 v11 M-5 -15 l5 -5 l5 5" stroke="${P.light}" stroke-width="2.6" fill="none"
          stroke-linecap="round" stroke-linejoin="round"/>
    ${face(mood)}</g>`;
}
const svg = (w,h,body,bg="#16283F") =>
  `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
     <rect width="${w}" height="${h}" rx="10" fill="${bg}"/>${body}</svg>`;
const P = MEME_PALETTE;

/* ---- scenes ----------------------------------------------------------- */
const SCENES = {
  /* a wobbly measuring stick and two numbers that disagree */
  trust: svg(150,110,`
    <text x="14" y="26" fill="${P.grey}" font-size="13" font-family="system-ui">truth 0.48</text>
    <text x="14" y="96" fill="${P.orange}" font-size="15" font-weight="700" font-family="system-ui">read 0.71</text>
    <path d="M12 60 H138" stroke="${P.grey}" stroke-width="2" stroke-dasharray="4 5"/>
    <path d="M30 60 q20 -26 40 -4 q18 20 40 -16" stroke="${P.orange}" stroke-width="3" fill="none" stroke-linecap="round"/>
    ${spin("shock",112,34,0.72)}`),

  /* sonar rings going out from the mascot */
  sonar: svg(150,110,`
    <circle cx="60" cy="58" r="20" fill="none" stroke="${P.blue}" stroke-width="2" opacity=".65"/>
    <circle cx="60" cy="58" r="33" fill="none" stroke="${P.blue}" stroke-width="2" opacity=".4"/>
    <circle cx="60" cy="58" r="46" fill="none" stroke="${P.blue}" stroke-width="2" opacity=".2"/>
    ${spin("neutral",60,58,0.85)}`),

  /* sunglasses drop: mascot above a beaten robot rival */
  shades: svg(150,110,`
    ${spin("cool",50,55,1.05)}
    <g transform="translate(112 62)">
      <rect x="-16" y="-16" width="32" height="30" rx="7" fill="${P.dark}" stroke="${P.grey}" stroke-width="2"/>
      <circle cx="-6" cy="-4" r="2.4" fill="${P.grey}"/><circle cx="6" cy="-4" r="2.4" fill="${P.grey}"/>
      <path d="M-7 7 q7 -5 14 0" stroke="${P.grey}" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M0 -16 v-7" stroke="${P.grey}" stroke-width="2"/><circle cx="0" cy="-25" r="2.6" fill="${P.grey}"/>
    </g>
    <text x="96" y="100" fill="${P.grey}" font-size="11" font-family="system-ui">the agent</text>`),

  /* the scenic route: a winding path past the target */
  scenic: svg(150,110,`
    <path d="M16 94 q30 -18 12 -34 q-16 -16 24 -24 q40 -8 76 10" stroke="${P.orange}" stroke-width="3"
          fill="none" stroke-dasharray="6 6" stroke-linecap="round"/>
    <circle cx="128" cy="46" r="7" fill="none" stroke="${P.light}" stroke-width="2"/>
    <circle cx="128" cy="46" r="2.5" fill="${P.light}"/>
    ${spin("sweat",34,72,0.62,-8)}
    <g transform="translate(58 84)"><rect x="-9" y="-7" width="18" height="13" rx="2" fill="${P.purple}"/>
      <path d="M-4 -7 v-3 h8 v3" stroke="${P.purple}" stroke-width="2" fill="none"/></g>`),

  /* empty battery */
  broke: svg(150,110,`
    <g transform="translate(96 56)">
      <rect x="-34" y="-17" width="64" height="34" rx="6" fill="none" stroke="${P.grey}" stroke-width="3"/>
      <rect x="34" y="-7" width="6" height="14" rx="2" fill="${P.grey}"/>
      <rect x="-29" y="-12" width="8" height="24" rx="2" fill="${P.orange}"/>
    </g>
    ${spin("dizzy",40,58,0.8)}`),

  /* floating phase: mascot drifting up on a balloon between two lines */
  floating: svg(150,110,`
    <path d="M10 82 H140" stroke="${P.purple}" stroke-width="2.5"/>
    <path d="M10 34 H140" stroke="${P.orange}" stroke-width="2.5" stroke-dasharray="5 5"/>
    <text x="12" y="96" fill="${P.purple}" font-size="10" font-family="system-ui">antiphase</text>
    <text x="12" y="26" fill="${P.orange}" font-size="10" font-family="system-ui">paramagnet</text>
    <path d="M75 46 v12" stroke="${P.light}" stroke-width="1.5"/>
    <ellipse cx="75" cy="40" rx="9" ry="11" fill="${P.blue}" opacity=".8"/>
    ${spin("shock",75,66,0.6)}`),

  /* fog rolling in */
  fog: svg(150,110,`
    ${spin("sweat",44,66,0.8)}
    <g fill="${P.grey}" opacity=".35">
      <ellipse cx="104" cy="44" rx="34" ry="14"/><ellipse cx="122" cy="62" rx="28" ry="12"/>
      <ellipse cx="96" cy="78" rx="32" ry="13"/>
    </g>
    <g fill="${P.grey}" opacity=".2"><ellipse cx="70" cy="90" rx="46" ry="12"/></g>`),

  /* two-panel: cheap vs sharp ping */
  twopanel: svg(150,110,`
    <g transform="translate(0 4)">
      <rect x="8" y="4" width="134" height="48" rx="8" fill="${P.dark}" stroke="#2c4661"/>
      ${spin("flat",34,28,0.52)}
      <text x="62" y="25" fill="${P.grey}" font-size="12" font-family="system-ui">20 shots</text>
      <text x="62" y="41" fill="${P.grey}" font-size="11" font-family="system-ui">vibes-based</text>
      <path d="M126 18 l12 12 M138 18 l-12 12" stroke="${P.orange}" stroke-width="2.5" stroke-linecap="round"/>
    </g>
    <g transform="translate(0 4)">
      <rect x="8" y="56" width="134" height="48" rx="8" fill="${P.dark}" stroke="${P.skin2}"/>
      ${spin("cool",34,80,0.52)}
      <text x="62" y="77" fill="${P.light}" font-size="12" font-family="system-ui">500 shots</text>
      <text x="62" y="93" fill="${P.grey}" font-size="11" font-family="system-ui">actual evidence</text>
      <path d="M124 80 l5 6 l11 -13" stroke="${P.skin}" stroke-width="2.8" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>
    </g>`),

  /* escalating glow: the budget ladder */
  ladder: svg(150,110,`
    ${[0,1,2,3].map(i=>`<g transform="translate(${22+i*36} ${86-i*18})">
        ${spin(["flat","neutral","smug","cool"][i],0,0,0.42,0,i)}</g>`).join("")}
    <text x="10" y="18" fill="${P.grey}" font-size="10" font-family="system-ui">20 → 100 → 500 → ask the agent</text>`),

  /* repeat ping */
  repeat: svg(150,110,`
    ${spin("flat",52,58,0.85)}
    <g transform="translate(112 58)">
      <circle r="17" fill="none" stroke="${P.grey}" stroke-width="2.5" stroke-dasharray="4 4"/>
      <path d="M0 -17 l6 -6 l-6 -6" stroke="${P.grey}" stroke-width="2.5" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>
      <circle r="4" fill="${P.grey}"/>
    </g>`),

  /* certified: a stamp */
  certified: svg(150,110,`
    ${spin("cool",50,58,0.95)}
    <g transform="translate(110 54) rotate(-14)">
      <rect x="-32" y="-18" width="64" height="36" rx="6" fill="none" stroke="${P.skin}" stroke-width="3"/>
      <text x="0" y="-2" fill="${P.skin}" font-size="11" font-weight="700" text-anchor="middle"
            font-family="system-ui">PHASE</text>
      <text x="0" y="12" fill="${P.skin}" font-size="11" font-weight="700" text-anchor="middle"
            font-family="system-ui">HUNTER</text>
    </g>`),

  /* the rival wins: robot holding the trophy */
  rival: svg(150,110,`
    ${spin("flat",36,66,0.72)}
    <g transform="translate(104 58)">
      <rect x="-18" y="-16" width="36" height="32" rx="8" fill="${P.dark}" stroke="${P.grey}" stroke-width="2"/>
      <circle cx="-7" cy="-4" r="2.6" fill="${P.skin}"/><circle cx="7" cy="-4" r="2.6" fill="${P.skin}"/>
      <path d="M-7 7 q7 4 14 -1" stroke="${P.skin}" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M0 -16 v-7" stroke="${P.grey}" stroke-width="2"/><circle cx="0" cy="-25" r="2.6" fill="${P.grey}"/>
    </g>
    <g transform="translate(104 20)">
      <path d="M-9 -8 h18 v6 a9 9 0 0 1 -18 0 z" fill="${P.orange}"/>
      <path d="M-9 -6 h-5 a5 5 0 0 0 5 5 M9 -6 h5 a5 5 0 0 1 -5 5" stroke="${P.orange}" stroke-width="2" fill="none"/>
      <rect x="-3" y="4" width="6" height="5" fill="${P.orange}"/><rect x="-7" y="9" width="14" height="3" rx="1" fill="${P.orange}"/>
    </g>`),

  /* mid score: a shrug with a wonky boundary */
  wonky: svg(150,110,`
    <path d="M14 86 q26 -10 40 -34 q14 -24 34 -6 q18 16 46 -12" stroke="${P.light}" stroke-width="2.5"
          fill="none" opacity=".45"/>
    <path d="M14 78 q30 -4 44 -28 q12 -20 32 -2 q20 18 46 -16" stroke="${P.orange}" stroke-width="3"
          fill="none" stroke-dasharray="6 5"/>
    ${spin("smug",36,40,0.55)}
    <text x="92" y="100" fill="${P.grey}" font-size="10" font-family="system-ui">close enough</text>`)
};

/* card id -> art + caption. Captions are ours. */
const CARDS = {
  first_ping:   {scene:"sonar",     text:"Sonar deployed."},
  noisy_ping:   {scene:"trust",     text:"Trust me bro."},
  cheap_habit:  {scene:"twopanel",  text:"20 shots is a personality."},
  big_spend:    {scene:"ladder",    text:"Deluxe measurement acquired."},
  repeat_ping:  {scene:"repeat",    text:"Measuring it twice won't move the boundary."},
  floating_hit: {scene:"floating",  text:"Wait, it was floating the whole time?"},
  broke:        {scene:"broke",     text:"Budget: 0. Vibes: immaculate."},
  noise_up:     {scene:"fog",       text:"The fog is coming."},
  reveal_high:  {scene:"certified", text:"Certified phase hunter."},
  reveal_mid:   {scene:"wonky",     text:"Task failed successfully."},
  reveal_low:   {scene:"scenic",    text:"Bro took the scenic route."},
  beat_agent:   {scene:"shades",    text:"I would like to speak to my developer."},
  lost_agent:   {scene:"rival",     text:"The agent sends its regards."}
};
