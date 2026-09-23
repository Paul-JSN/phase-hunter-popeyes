/* Phase Hunter reaction art - all original.
   Spinny is a spin arrow with a face, arms and a temper. Everything here is
   drawn from scratch: no third-party characters, frames, photos or logos.   */

const P = {
  ink:"#0B1424", skin:"#34C2B0", skin2:"#1F8577", light:"#FFFFFF", cream:"#F4F1EA",
  orange:"#E08B45", purple:"#9B7BD4", blue:"#5C9BD1", grey:"#8FA6BA", dark:"#16283F",
  red:"#D45B4A", gold:"#EBC15A"
};
const LINE = `stroke="${P.ink}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"`;

/* ---- eyes, brows, mouths --------------------------------------------- */
function eyes(kind){
  const white = (cx,rx=6.4,ry=7.4)=>`<ellipse cx="${cx}" cy="-3" rx="${rx}" ry="${ry}" fill="${P.light}" ${LINE}/>`;
  switch(kind){
    case "wide":   return white(-7)+white(7)+`<circle cx="-6" cy="-2" r="3" fill="${P.ink}"/><circle cx="8" cy="-2" r="3" fill="${P.ink}"/>`;
    case "shrunk": return white(-7,7,8)+white(7,7,8)+`<circle cx="-7" cy="-3" r="1.7" fill="${P.ink}"/><circle cx="7" cy="-3" r="1.7" fill="${P.ink}"/>`;
    case "half":   return white(-7)+white(7)+`<circle cx="-7" cy="-1" r="2.8" fill="${P.ink}"/><circle cx="7" cy="-1" r="2.8" fill="${P.ink}"/>
                           <path d="M-14 -6 h14 M0 -6 h14" ${LINE} stroke-width="5"/>`;
    case "teary":  return white(-7,7.6,8.6)+white(7,7.6,8.6)+
                          `<circle cx="-6" cy="-2" r="4" fill="${P.ink}"/><circle cx="8" cy="-2" r="4" fill="${P.ink}"/>
                           <circle cx="-8" cy="-5" r="1.8" fill="${P.light}"/><circle cx="6" cy="-5" r="1.8" fill="${P.light}"/>`;
    case "x":      return `<path d="M-11 -7 l7 7 M-4 -7 l-7 7" ${LINE}/><path d="M4 -7 l7 7 M11 -7 l-7 7" ${LINE}/>`;
    case "spark":  return white(-7)+white(7)+`<circle cx="-7" cy="-2" r="3" fill="${P.ink}"/><circle cx="7" cy="-2" r="3" fill="${P.ink}"/>
                           <circle cx="-8.5" cy="-4" r="1.6" fill="${P.light}"/><circle cx="5.5" cy="-4" r="1.6" fill="${P.light}"/>`;
    case "shades": return `<path d="M-15 -8 h30 v3 h-30 z" fill="${P.ink}"/>
                           <path d="M-14 -5 h11 q1 7 -5 7 q-6 0 -6 -7 z" fill="${P.ink}"/>
                           <path d="M14 -5 h-11 q-1 7 5 7 q6 0 6 -7 z" fill="${P.ink}"/>`;
    default:       return white(-7)+white(7)+`<circle cx="-7" cy="-2" r="2.6" fill="${P.ink}"/><circle cx="7" cy="-2" r="2.6" fill="${P.ink}"/>`;
  }
}
function brows(kind){
  switch(kind){
    case "angry": return `<path d="M-14 -13 l9 4" ${LINE}/><path d="M14 -13 l-9 4" ${LINE}/>`;
    case "sad":   return `<path d="M-14 -10 l9 -4" ${LINE}/><path d="M14 -10 l-9 -4" ${LINE}/>`;
    case "raised":return `<path d="M-13 -14 q4 -3 8 -1" ${LINE}/><path d="M13 -14 q-4 -3 -8 -1" ${LINE}/>`;
    case "smug":  return `<path d="M-13 -13 q5 -2 9 1" ${LINE}/><path d="M13 -11 l-8 -1" ${LINE}/>`;
    default:      return "";
  }
}
function mouth(kind){
  switch(kind){
    case "shout": return `<path d="M-8 6 q8 -3 16 0 q-2 12 -8 12 q-6 0 -8 -12 z" fill="${P.ink}"/>
                          <path d="M-4 15 q4 4 8 0" fill="${P.red}"/>`;
    case "smile": return `<path d="M-8 7 q8 8 16 0" ${LINE} fill="none"/>`;
    case "grin":  return `<path d="M-9 6 q9 11 18 0 z" fill="${P.ink}"/><path d="M-6 6 h12" stroke="${P.light}" stroke-width="1.6"/>`;
    case "frown": return `<path d="M-8 13 q8 -8 16 0" ${LINE} fill="none"/>`;
    case "flat":  return `<path d="M-7 10 h14" ${LINE}/>`;
    case "smirk": return `<path d="M-6 9 q8 5 12 -3" ${LINE} fill="none"/>`;
    case "wail":  return `<path d="M-7 8 q7 -4 14 0 q-1 13 -7 13 q-6 0 -7 -13 z" fill="${P.ink}"/>`;
    default:      return `<path d="M-7 8 q7 5 14 0" ${LINE} fill="none"/>`;
  }
}
/* arms give the poses their comedy.
   Every limb is drawn twice: a dark casing, then a skin-coloured core, so it
   stays visible against both the teal body and a dark background.          */
const LIMB = (d)=>`<path d="${d}" stroke="${P.ink}" stroke-width="9" fill="none" stroke-linecap="round"/>
                   <path d="${d}" stroke="${P.skin}" stroke-width="5" fill="none" stroke-linecap="round"/>`;
const HAND = (cx,cy,r=5.5)=>`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${P.skin}" stroke="${P.ink}" stroke-width="2.4"/>`;
function arms(pose){
  switch(pose){
    case "spread":  return LIMB("M-17 6 q-16 -8 -28 0")+LIMB("M17 6 q16 -8 28 0")+HAND(-45,6)+HAND(45,6);
    case "shrug":   return LIMB("M-17 4 q-14 4 -16 14")+LIMB("M17 4 q14 4 16 14")+HAND(-33,18)+HAND(33,18);
    case "cheer":   return LIMB("M-16 4 q-14 -8 -12 -24")+LIMB("M16 4 q14 -8 12 -24")+HAND(-28,-21)+HAND(28,-21);
    case "point":   return LIMB("M16 4 q16 -2 26 -12")+HAND(43,-13);
    case "facepalm":return LIMB("M-17 4 q-10 -14 2 -16")+`<ellipse cx="-11" cy="-13" rx="8" ry="6" fill="${P.skin}" stroke="${P.ink}" stroke-width="2.4"/>`;
    case "flail":   return LIMB("M-16 4 q-16 -8 -14 -20")+LIMB("M16 4 q16 6 14 18")+HAND(-30,-16)+HAND(30,22);
    default:        return "";
  }
}
/* the character */
function spin(o){
  const {mood="ok", pose="", x=0, y=0, s=1, tilt=0, tears=false, sweat=false, glow=0} = o;
  const M = {
    ok:     {e:"ok",     b:"",       m:"smile"},
    smug:   {e:"half",   b:"smug",   m:"smirk"},
    shout:  {e:"wide",   b:"angry",  m:"shout"},
    panic:  {e:"shrunk", b:"sad",    m:"wail"},
    dead:   {e:"x",      b:"",       m:"flat"},
    sad:    {e:"teary",  b:"sad",    m:"frown"},
    cool:   {e:"shades", b:"",       m:"grin"},
    happy:  {e:"spark",  b:"raised", m:"grin"},
    flat:   {e:"half",   b:"",       m:"flat"},
    shocked:{e:"wide",   b:"raised", m:"shout"}
  }[mood] || {e:"ok",b:"",m:"smile"};
  return `<g transform="translate(${x} ${y}) scale(${s}) rotate(${tilt})">
    ${glow?`<circle r="30" fill="${P.skin}" opacity="${0.14*glow}"/>`:""}
    ${arms(pose)}
    <circle r="21" fill="${P.skin}" ${LINE}/>
    <path d="M0 -21 v-9 M-6 -25 l6 -6 l6 6" ${LINE} fill="none"/>
    ${brows(M.b)}${eyes(M.e)}${mouth(M.m)}
    ${tears?`<path d="M-11 4 q-3 8 1 12 q4 -4 1 -12" fill="${P.blue}" opacity=".9"/>
             <path d="M11 4 q3 8 -1 12 q-4 -4 -1 -12" fill="${P.blue}" opacity=".9"/>`:""}
    ${sweat?`<path d="M16 -16 q4 7 0 9 q-4 -2 0 -9" fill="${P.blue}"/>`:""}
  </g>`;
}

/* ---- macro furniture -------------------------------------------------- */
const svg = (w,h,body,bg=P.dark) =>
  `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
     <rect width="${w}" height="${h}" fill="${bg}"/>${body}</svg>`;
const CAP = `font-family:Impact,"Arial Narrow",Haettenschweiler,system-ui;font-weight:900;letter-spacing:.6px`;
function caption(text,y,size=17){
  // Impact is roughly 0.46em per character; shrink long lines so nothing clips.
  const fitted = Math.max(8.5, Math.min(size, 138/(text.length*0.47)));
  return `<text x="75" y="${y}" text-anchor="middle" style="${CAP}" font-size="${fitted.toFixed(1)}"
            textLength="${Math.min(140, text.length*fitted*0.47).toFixed(0)}" lengthAdjust="spacingAndGlyphs"
            fill="${P.light}" stroke="${P.ink}" stroke-width="${(fitted*0.26).toFixed(1)}" paint-order="stroke"
            stroke-linejoin="round">${text}</text>`;
}
const macro=(body,top,bottom,bg)=>svg(150,110,`${body}${top?caption(top,20):""}${bottom?caption(bottom,101):""}`,bg);
function dialog(title,l1,l2,button="OK"){
  return svg(150,110,`
    <rect x="8" y="18" width="134" height="74" rx="3" fill="#D9DEE3" ${LINE}/>
    <rect x="8" y="18" width="134" height="16" fill="${P.skin2}" ${LINE}/>
    <text x="14" y="30" font-size="9.5" font-family="system-ui" font-weight="700" fill="${P.light}">${title}</text>
    <g transform="translate(132 26)"><rect x="-7" y="-6" width="14" height="12" fill="${P.red}" ${LINE}/>
      <path d="M-3 -2 l6 4 M3 -2 l-6 4" stroke="${P.light}" stroke-width="1.6"/></g>
    <circle cx="30" cy="56" r="11" fill="${P.blue}" ${LINE}/>
    <text x="30" y="61" text-anchor="middle" font-size="14" font-family="Georgia,serif" font-weight="700" fill="${P.light}">i</text>
    <text x="50" y="54" font-size="10" font-family="system-ui" fill="${P.ink}">${l1}</text>
    <text x="50" y="66" font-size="10" font-family="system-ui" fill="${P.ink}">${l2}</text>
    <g transform="translate(75 81)"><rect x="-22" y="-9" width="44" height="17" rx="2" fill="#E8ECEF" ${LINE}/>
      <text x="0" y="3" text-anchor="middle" font-size="10" font-family="system-ui" fill="${P.ink}">${button}</text></g>`, P.ink);
}
const rival=(x,y,s=1,mood="ok")=>`<g transform="translate(${x} ${y}) scale(${s})">
  <rect x="-16" y="-15" width="32" height="30" rx="7" fill="${P.dark}" ${LINE}/>
  <path d="M0 -15 v-7" ${LINE}/><circle cx="0" cy="-24" r="3" fill="${P.grey}" ${LINE}/>
  <circle cx="-6" cy="-3" r="2.8" fill="${P.skin}"/><circle cx="6" cy="-3" r="2.8" fill="${P.skin}"/>
  ${mood==="sad"?`<path d="M-6 8 q6 -5 12 0" ${LINE} fill="none"/>`:`<path d="M-6 5 q6 6 12 0" ${LINE} fill="none"/>`}</g>`;

/* ---- scenes ----------------------------------------------------------- */
const SCENES = {
  /* arms flung wide: "it was THIS big" */
  trust: macro(`
    <path d="M6 70 H144" stroke="${P.grey}" stroke-width="2" stroke-dasharray="5 5"/>
    <path class="ph-wobble" d="M18 70 q20 -22 40 -3 q20 18 44 -12" stroke="${P.orange}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
    <g class="ph-shake">${spin({mood:"shout",pose:"spread",x:75,y:52,s:0.95})}</g>`,
    "I'M TELLING YOU BRO", "IT WAS 0.71"),

  sonar: svg(150,110,`
    <circle class="ph-ring ph-r1" cx="75" cy="58" r="22" fill="none" stroke="${P.blue}" stroke-width="2.5" opacity=".7"/>
    <circle class="ph-ring ph-r2" cx="75" cy="58" r="36" fill="none" stroke="${P.blue}" stroke-width="2.5" opacity=".45"/>
    <circle class="ph-ring ph-r3" cx="75" cy="58" r="50" fill="none" stroke="${P.blue}" stroke-width="2.5" opacity=".2"/>
    ${spin({mood:"happy",pose:"point",x:62,y:58,s:0.9})}`),

  /* sunglasses drop, rival slumps, confetti */
  shades: macro(`
    ${rival(114,66,0.85,"sad")}
    ${spin({mood:"cool",pose:"cheer",x:52,y:60,s:0.95})}
    <g class="ph-rise" fill="${P.gold}"><rect x="30" y="26" width="4" height="7" rx="1"/><rect x="96" y="20" width="4" height="7" rx="1" fill="${P.purple}"/>
      <rect x="66" y="16" width="4" height="7" rx="1" fill="${P.orange}"/></g>`,
    "", "GET REKT, AGENT"),

  /* the exit you should not have taken */
  scenic: macro(`
    <path d="M-4 84 q46 6 78 -10 q30 -14 80 -4" stroke="${P.grey}" stroke-width="15" fill="none" opacity=".3"/>
    <path d="M-4 84 q46 6 78 -10 q30 -14 80 -4" stroke="${P.light}" stroke-width="1.6" fill="none"
          stroke-dasharray="8 8" opacity=".45"/>
    <g transform="translate(40 46)">
      <rect x="-28" y="-12" width="56" height="20" rx="2" fill="${P.skin2}" stroke="${P.ink}" stroke-width="2.4"/>
      <path d="M-12 4 v-8 q0 -4 8 -4 h10" stroke="${P.light}" stroke-width="2.4" fill="none"/>
      <path d="M2 -12 l6 4 l-6 4" stroke="${P.light}" stroke-width="2.4" fill="none"/>
      <path d="M0 8 v14" stroke="${P.grey}" stroke-width="3"/>
    </g>
    <g class="ph-shake"><g transform="translate(106 66)">
      <path d="M-18 4 h36 l-5 -11 h-11 l-5 -7 h-11 z" fill="${P.purple}" stroke="${P.ink}" stroke-width="2.4"/>
      ${spin({mood:"panic",x:-1,y:-9,s:0.26})}
      <circle cx="-10" cy="7" r="5" fill="${P.ink}"/><circle cx="10" cy="7" r="5" fill="${P.ink}"/>
      <path d="M-22 0 q-11 -3 -18 3 M-22 7 q-13 2 -20 9" stroke="${P.grey}" stroke-width="2.4" opacity=".7"/>
    </g></g>`,
    "", "BRO TOOK THE SCENIC ROUTE"),

  /* full-on waterworks */
  broke: macro(`
    <g transform="translate(108 60)"><rect x="-26" y="-15" width="52" height="30" rx="4" fill="none" stroke="${P.grey}" stroke-width="3"/>
      <rect x="26" y="-6" width="5" height="12" rx="2" fill="${P.grey}"/><rect x="-22" y="-11" width="7" height="22" rx="2" fill="${P.red}"/></g>
    ${spin({mood:"sad",pose:"flail",x:48,y:60,s:0.95,tears:true})}`,
    "", "LIFE SUCKS. BUDGET: 0"),

  /* eyes out of the dark */
  fog: macro(`
    <g class="ph-drift" fill="${P.grey}" opacity=".22">
      <ellipse cx="40" cy="92" rx="46" ry="14"/><ellipse cx="116" cy="86" rx="40" ry="12"/></g>
    ${spin({mood:"shocked",x:75,y:60,s:1.15,sweat:true})}
    <g class="ph-drift ph-slow" fill="${P.grey}" opacity=".3">
      <ellipse cx="60" cy="98" rx="52" ry="13"/><ellipse cx="120" cy="100" rx="40" ry="11"/></g>`,
    "THE FOG IS COMING", "RUN", "#0A1420"),

  twopanel: svg(150,110,`
    <rect x="6" y="6" width="138" height="46" rx="6" fill="#1B2E47" ${LINE}/>
    ${spin({mood:"flat",x:32,y:29,s:0.55})}
    <text x="60" y="26" fill="${P.light}" font-size="12" font-family="system-ui" font-weight="700">20 shots</text>
    <text x="60" y="40" fill="${P.grey}" font-size="10.5" font-family="system-ui">vibes-based physics</text>
    <path d="M126 20 l12 12 M138 20 l-12 12" stroke="${P.red}" stroke-width="3" stroke-linecap="round"/>
    <rect x="6" y="58" width="138" height="46" rx="6" fill="#123832" stroke="${P.skin}" stroke-width="2.4"/>
    ${spin({mood:"cool",x:32,y:81,s:0.55})}
    <text x="60" y="78" fill="${P.light}" font-size="12" font-family="system-ui" font-weight="700">500 shots</text>
    <text x="60" y="92" fill="${P.grey}" font-size="10.5" font-family="system-ui">actual evidence</text>
    <path d="M124 82 l6 7 l12 -15" stroke="${P.skin}" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),

  ladder: svg(150,110,`
    ${[0,1,2,3].map(i=>`<g class="ph-rise" style="animation-delay:${i*0.22}s"><g transform="translate(${24+i*34} ${84-i*17})">
        ${spin({mood:["flat","ok","smug","happy"][i],s:0.42,glow:i})}</g></g>`).join("")}
    <text x="75" y="14" text-anchor="middle" fill="${P.grey}" font-size="9.5" font-family="system-ui">20 → 100 → 500 shots</text>`),

  repeat: macro(`
    ${spin({mood:"flat",pose:"facepalm",x:56,y:60,s:0.95})}
    <g transform="translate(116 58)"><circle class="ph-spin" r="18" fill="none" stroke="${P.grey}" stroke-width="3" stroke-dasharray="5 5"/>
      <circle r="4" fill="${P.grey}"/></g>`,
    "", "SAME PING. SAME ANSWER."),

  certified: macro(`
    ${spin({mood:"happy",pose:"cheer",x:52,y:62,s:0.95})}
    <g class="ph-stamp-wrap" transform="translate(112 52) rotate(-14)"><g class="ph-stamp">
      <rect x="-32" y="-17" width="64" height="34" rx="5" fill="none" stroke="${P.skin}" stroke-width="3.5"/>
      <text x="0" y="-1" fill="${P.skin}" font-size="11" font-weight="700" text-anchor="middle" font-family="system-ui">PHASE</text>
      <text x="0" y="12" fill="${P.skin}" font-size="11" font-weight="700" text-anchor="middle" font-family="system-ui">HUNTER</text>
    </g></g>`, "", "CERTIFIED"),

  wonky: dialog("phase_hunter.exe", "Task failed", "successfully."),

  floating: macro(`
    <path d="M6 80 H144" stroke="${P.purple}" stroke-width="3"/>
    <path d="M6 42 H144" stroke="${P.orange}" stroke-width="3" stroke-dasharray="6 5"/>
    <g class="ph-bob"><path d="M75 48 v10" stroke="${P.light}" stroke-width="1.6"/>
      <ellipse cx="75" cy="40" rx="10" ry="12" fill="${P.blue}" ${LINE}/>
      ${spin({mood:"shocked",x:75,y:66,s:0.62})}</g>`,
    "IT WAS FLOATING", "THE WHOLE TIME"),

  rival: macro(`
    ${spin({mood:"dead",x:44,y:64,s:0.95})}
    ${rival(108,62,0.95)}
    <g class="ph-shine"><g transform="translate(108 22)">
      <path d="M-9 -8 h18 v6 a9 9 0 0 1 -18 0 z" fill="${P.gold}" ${LINE}/>
      <path d="M-9 -6 h-5 a5 5 0 0 0 5 5 M9 -6 h5 a5 5 0 0 1 -5 5" stroke="${P.gold}" stroke-width="2" fill="none"/>
      <rect x="-3" y="4" width="6" height="5" fill="${P.gold}"/><rect x="-7" y="9" width="14" height="3" rx="1" fill="${P.gold}"/></g></g>`,
    "", "THE AGENT SENDS ITS REGARDS")
};

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
