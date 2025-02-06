import{g as fe,d as zt,c as J,w as Lt,h as At}from"./vendor-CFVb6_YQ.js";const ue=()=>{};let te={},qe={},Ke=null,Xe={mark:ue,measure:ue};try{typeof window<"u"&&(te=window),typeof document<"u"&&(qe=document),typeof MutationObserver<"u"&&(Ke=MutationObserver),typeof performance<"u"&&(Xe=performance)}catch{}const{userAgent:me=""}=te.navigator||{},_=te,g=qe,de=Ke,pn=Xe;_.document;const B=!!g.documentElement&&!!g.head&&typeof g.addEventListener=="function"&&typeof g.createElement=="function",Ve=~me.indexOf("MSIE")||~me.indexOf("Trident/");var h="classic",Ge="duotone",O="sharp",C="sharp-duotone",Nt=[h,Ge,O,C],Mt={fak:"kit","fa-kit":"kit"},Ot={fakd:"kit-duotone","fa-kit-duotone":"kit-duotone"},Ze={classic:{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fad:"duotone","fa-duotone":"duotone",fab:"brands","fa-brands":"brands"},sharp:{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light",fast:"thin","fa-thin":"thin"},"sharp-duotone":{fa:"solid",fasds:"solid","fa-solid":"solid"}},Je=[1,2,3,4,5,6,7,8,9,10],Ct=Je.concat([11,12,13,14,15,16,17,18,19,20]),on={GROUP:"duotone-group",SWAP_OPACITY:"swap-opacity",PRIMARY:"primary",SECONDARY:"secondary"},Pt=[...Object.keys({classic:["fas","far","fal","fat"],sharp:["fass","fasr","fasl","fast"],"sharp-duotone":["fasds"]}),"solid","regular","light","thin","duotone","brands","2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","fw","inverse","layers-counter","layers-text","layers","li","pull-left","pull-right","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul",on.GROUP,on.SWAP_OPACITY,on.PRIMARY,on.SECONDARY].concat(Je.map(n=>"".concat(n,"x"))).concat(Ct.map(n=>"w-".concat(n))),St={kit:"fak"},jt={"kit-duotone":"fakd"};const R="___FONT_AWESOME___",Dn=16,Qe="svg-inline--fa",G="data-fa-i2svg",Tn="data-fa-pseudo-element",Bn="data-prefix",Yn="data-icon",pe="fontawesome-i2svg",Et=["HTML","HEAD","STYLE","SCRIPT"],$e=(()=>{try{return!0}catch{return!1}})(),nt=[h,O,C];function un(n){return new Proxy(n,{get:(e,t)=>t in e?e[t]:e[h]})}const et={...Ze};et[h]={...Ze[h],...Mt,...Ot};const X=un(et),Wn={classic:{solid:"fas",regular:"far",light:"fal",thin:"fat",duotone:"fad",brands:"fab"},sharp:{solid:"fass",regular:"fasr",light:"fasl",thin:"fast"},"sharp-duotone":{solid:"fasds"}};Wn[h]={...Wn[h],...St,...jt};const cn=un(Wn),Hn={classic:{fab:"fa-brands",fad:"fa-duotone",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"},sharp:{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light",fast:"fa-thin"},"sharp-duotone":{fasds:"fa-solid"}};Hn[h]={...Hn[h],fak:"fa-kit"};const V=un(Hn),_n={classic:{"fa-brands":"fab","fa-duotone":"fad","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"},sharp:{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl","fa-thin":"fast"},"sharp-duotone":{"fa-solid":"fasds"}};_n[h]={..._n[h],"fa-kit":"fak"};const Ft=un(_n),It=/fa(s|r|l|t|d|b|k|kd|ss|sr|sl|st|sds)?[\-\ ]/,tt="fa-layers-text",Rt=/Font ?Awesome ?([56 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp Duotone|Sharp|Kit)?.*/i;un({classic:{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},sharp:{900:"fass",400:"fasr",300:"fasl",100:"fast"},"sharp-duotone":{900:"fasds"}});const Dt=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],On=on,Q=new Set;Object.keys(cn[h]).map(Q.add.bind(Q)),Object.keys(cn[O]).map(Q.add.bind(Q)),Object.keys(cn[C]).map(Q.add.bind(Q));const Tt=["kit",...Pt],ln=_.FontAwesomeConfig||{};g&&typeof g.querySelector=="function"&&[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-auto-a11y","autoA11y"],["data-search-pseudo-elements","searchPseudoElements"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]].forEach(n=>{let[e,t]=n;const a=function(r){return r===""||r!=="false"&&(r==="true"||r)}(function(r){var i=g.querySelector("script["+r+"]");if(i)return i.getAttribute(r)}(e));a!=null&&(ln[t]=a)});const at={styleDefault:"solid",familyDefault:"classic",cssPrefix:"fa",replacementClass:Qe,autoReplaceSvg:!0,autoAddCss:!0,autoA11y:!0,searchPseudoElements:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};ln.familyPrefix&&(ln.cssPrefix=ln.familyPrefix);const nn={...at,...ln};nn.autoReplaceSvg||(nn.observeMutations=!1);const f={};Object.keys(at).forEach(n=>{Object.defineProperty(f,n,{enumerable:!0,set:function(e){nn[n]=e,Un.forEach(t=>t(f))},get:function(){return nn[n]}})}),Object.defineProperty(f,"familyPrefix",{enumerable:!0,set:function(n){nn.cssPrefix=n,Un.forEach(e=>e(f))},get:function(){return nn.cssPrefix}}),_.FontAwesomeConfig=f;const Un=[],W=Dn,E={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function fn(){let n=12,e="";for(;n-- >0;)e+="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"[62*Math.random()|0];return e}function an(n){const e=[];for(let t=(n||[]).length>>>0;t--;)e[t]=n[t];return e}function ae(n){return n.classList?an(n.classList):(n.getAttribute("class")||"").split(" ").filter(e=>e)}function ge(n){return"".concat(n).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function wn(n){return Object.keys(n||{}).reduce((e,t)=>e+"".concat(t,": ").concat(n[t].trim(),";"),"")}function re(n){return n.size!==E.size||n.x!==E.x||n.y!==E.y||n.rotate!==E.rotate||n.flipX||n.flipY}function rt(){const n="fa",e=Qe,t=f.cssPrefix,a=f.replacementClass;let r=`:root, :host {
  --fa-font-solid: normal 900 1em/1 "Font Awesome 6 Free";
  --fa-font-regular: normal 400 1em/1 "Font Awesome 6 Free";
  --fa-font-light: normal 300 1em/1 "Font Awesome 6 Pro";
  --fa-font-thin: normal 100 1em/1 "Font Awesome 6 Pro";
  --fa-font-duotone: normal 900 1em/1 "Font Awesome 6 Duotone";
  --fa-font-brands: normal 400 1em/1 "Font Awesome 6 Brands";
  --fa-font-sharp-solid: normal 900 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-regular: normal 400 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-light: normal 300 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-thin: normal 100 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-duotone-solid: normal 900 1em/1 "Font Awesome 6 Sharp Duotone";
}

svg:not(:root).svg-inline--fa, svg:not(:host).svg-inline--fa {
  overflow: visible;
  box-sizing: content-box;
}

.svg-inline--fa {
  display: var(--fa-display, inline-block);
  height: 1em;
  overflow: visible;
  vertical-align: -0.125em;
}
.svg-inline--fa.fa-2xs {
  vertical-align: 0.1em;
}
.svg-inline--fa.fa-xs {
  vertical-align: 0em;
}
.svg-inline--fa.fa-sm {
  vertical-align: -0.0714285705em;
}
.svg-inline--fa.fa-lg {
  vertical-align: -0.2em;
}
.svg-inline--fa.fa-xl {
  vertical-align: -0.25em;
}
.svg-inline--fa.fa-2xl {
  vertical-align: -0.3125em;
}
.svg-inline--fa.fa-pull-left {
  margin-right: var(--fa-pull-margin, 0.3em);
  width: auto;
}
.svg-inline--fa.fa-pull-right {
  margin-left: var(--fa-pull-margin, 0.3em);
  width: auto;
}
.svg-inline--fa.fa-li {
  width: var(--fa-li-width, 2em);
  top: 0.25em;
}
.svg-inline--fa.fa-fw {
  width: var(--fa-fw-width, 1.25em);
}

.fa-layers svg.svg-inline--fa {
  bottom: 0;
  left: 0;
  margin: auto;
  position: absolute;
  right: 0;
  top: 0;
}

.fa-layers-counter, .fa-layers-text {
  display: inline-block;
  position: absolute;
  text-align: center;
}

.fa-layers {
  display: inline-block;
  height: 1em;
  position: relative;
  text-align: center;
  vertical-align: -0.125em;
  width: 1em;
}
.fa-layers svg.svg-inline--fa {
  transform-origin: center center;
}

.fa-layers-text {
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  transform-origin: center center;
}

.fa-layers-counter {
  background-color: var(--fa-counter-background-color, #ff253a);
  border-radius: var(--fa-counter-border-radius, 1em);
  box-sizing: border-box;
  color: var(--fa-inverse, #fff);
  line-height: var(--fa-counter-line-height, 1);
  max-width: var(--fa-counter-max-width, 5em);
  min-width: var(--fa-counter-min-width, 1.5em);
  overflow: hidden;
  padding: var(--fa-counter-padding, 0.25em 0.5em);
  right: var(--fa-right, 0);
  text-overflow: ellipsis;
  top: var(--fa-top, 0);
  transform: scale(var(--fa-counter-scale, 0.25));
  transform-origin: top right;
}

.fa-layers-bottom-right {
  bottom: var(--fa-bottom, 0);
  right: var(--fa-right, 0);
  top: auto;
  transform: scale(var(--fa-layers-scale, 0.25));
  transform-origin: bottom right;
}

.fa-layers-bottom-left {
  bottom: var(--fa-bottom, 0);
  left: var(--fa-left, 0);
  right: auto;
  top: auto;
  transform: scale(var(--fa-layers-scale, 0.25));
  transform-origin: bottom left;
}

.fa-layers-top-right {
  top: var(--fa-top, 0);
  right: var(--fa-right, 0);
  transform: scale(var(--fa-layers-scale, 0.25));
  transform-origin: top right;
}

.fa-layers-top-left {
  left: var(--fa-left, 0);
  right: auto;
  top: var(--fa-top, 0);
  transform: scale(var(--fa-layers-scale, 0.25));
  transform-origin: top left;
}

.fa-1x {
  font-size: 1em;
}

.fa-2x {
  font-size: 2em;
}

.fa-3x {
  font-size: 3em;
}

.fa-4x {
  font-size: 4em;
}

.fa-5x {
  font-size: 5em;
}

.fa-6x {
  font-size: 6em;
}

.fa-7x {
  font-size: 7em;
}

.fa-8x {
  font-size: 8em;
}

.fa-9x {
  font-size: 9em;
}

.fa-10x {
  font-size: 10em;
}

.fa-2xs {
  font-size: 0.625em;
  line-height: 0.1em;
  vertical-align: 0.225em;
}

.fa-xs {
  font-size: 0.75em;
  line-height: 0.0833333337em;
  vertical-align: 0.125em;
}

.fa-sm {
  font-size: 0.875em;
  line-height: 0.0714285718em;
  vertical-align: 0.0535714295em;
}

.fa-lg {
  font-size: 1.25em;
  line-height: 0.05em;
  vertical-align: -0.075em;
}

.fa-xl {
  font-size: 1.5em;
  line-height: 0.0416666682em;
  vertical-align: -0.125em;
}

.fa-2xl {
  font-size: 2em;
  line-height: 0.03125em;
  vertical-align: -0.1875em;
}

.fa-fw {
  text-align: center;
  width: 1.25em;
}

.fa-ul {
  list-style-type: none;
  margin-left: var(--fa-li-margin, 2.5em);
  padding-left: 0;
}
.fa-ul > li {
  position: relative;
}

.fa-li {
  left: calc(-1 * var(--fa-li-width, 2em));
  position: absolute;
  text-align: center;
  width: var(--fa-li-width, 2em);
  line-height: inherit;
}

.fa-border {
  border-color: var(--fa-border-color, #eee);
  border-radius: var(--fa-border-radius, 0.1em);
  border-style: var(--fa-border-style, solid);
  border-width: var(--fa-border-width, 0.08em);
  padding: var(--fa-border-padding, 0.2em 0.25em 0.15em);
}

.fa-pull-left {
  float: left;
  margin-right: var(--fa-pull-margin, 0.3em);
}

.fa-pull-right {
  float: right;
  margin-left: var(--fa-pull-margin, 0.3em);
}

.fa-beat {
  animation-name: fa-beat;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-bounce {
  animation-name: fa-bounce;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.28, 0.84, 0.42, 1));
}

.fa-fade {
  animation-name: fa-fade;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
}

.fa-beat-fade {
  animation-name: fa-beat-fade;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
}

.fa-flip {
  animation-name: fa-flip;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-shake {
  animation-name: fa-shake;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin {
  animation-name: fa-spin;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 2s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin-reverse {
  --fa-animation-direction: reverse;
}

.fa-pulse,
.fa-spin-pulse {
  animation-name: fa-spin;
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, steps(8));
}

@media (prefers-reduced-motion: reduce) {
  .fa-beat,
.fa-bounce,
.fa-fade,
.fa-beat-fade,
.fa-flip,
.fa-pulse,
.fa-shake,
.fa-spin,
.fa-spin-pulse {
    animation-delay: -1ms;
    animation-duration: 1ms;
    animation-iteration-count: 1;
    transition-delay: 0s;
    transition-duration: 0s;
  }
}
@keyframes fa-beat {
  0%, 90% {
    transform: scale(1);
  }
  45% {
    transform: scale(var(--fa-beat-scale, 1.25));
  }
}
@keyframes fa-bounce {
  0% {
    transform: scale(1, 1) translateY(0);
  }
  10% {
    transform: scale(var(--fa-bounce-start-scale-x, 1.1), var(--fa-bounce-start-scale-y, 0.9)) translateY(0);
  }
  30% {
    transform: scale(var(--fa-bounce-jump-scale-x, 0.9), var(--fa-bounce-jump-scale-y, 1.1)) translateY(var(--fa-bounce-height, -0.5em));
  }
  50% {
    transform: scale(var(--fa-bounce-land-scale-x, 1.05), var(--fa-bounce-land-scale-y, 0.95)) translateY(0);
  }
  57% {
    transform: scale(1, 1) translateY(var(--fa-bounce-rebound, -0.125em));
  }
  64% {
    transform: scale(1, 1) translateY(0);
  }
  100% {
    transform: scale(1, 1) translateY(0);
  }
}
@keyframes fa-fade {
  50% {
    opacity: var(--fa-fade-opacity, 0.4);
  }
}
@keyframes fa-beat-fade {
  0%, 100% {
    opacity: var(--fa-beat-fade-opacity, 0.4);
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(var(--fa-beat-fade-scale, 1.125));
  }
}
@keyframes fa-flip {
  50% {
    transform: rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -180deg));
  }
}
@keyframes fa-shake {
  0% {
    transform: rotate(-15deg);
  }
  4% {
    transform: rotate(15deg);
  }
  8%, 24% {
    transform: rotate(-18deg);
  }
  12%, 28% {
    transform: rotate(18deg);
  }
  16% {
    transform: rotate(-22deg);
  }
  20% {
    transform: rotate(22deg);
  }
  32% {
    transform: rotate(-12deg);
  }
  36% {
    transform: rotate(12deg);
  }
  40%, 100% {
    transform: rotate(0deg);
  }
}
@keyframes fa-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
.fa-rotate-90 {
  transform: rotate(90deg);
}

.fa-rotate-180 {
  transform: rotate(180deg);
}

.fa-rotate-270 {
  transform: rotate(270deg);
}

.fa-flip-horizontal {
  transform: scale(-1, 1);
}

.fa-flip-vertical {
  transform: scale(1, -1);
}

.fa-flip-both,
.fa-flip-horizontal.fa-flip-vertical {
  transform: scale(-1, -1);
}

.fa-rotate-by {
  transform: rotate(var(--fa-rotate-angle, 0));
}

.fa-stack {
  display: inline-block;
  vertical-align: middle;
  height: 2em;
  position: relative;
  width: 2.5em;
}

.fa-stack-1x,
.fa-stack-2x {
  bottom: 0;
  left: 0;
  margin: auto;
  position: absolute;
  right: 0;
  top: 0;
  z-index: var(--fa-stack-z-index, auto);
}

.svg-inline--fa.fa-stack-1x {
  height: 1em;
  width: 1.25em;
}
.svg-inline--fa.fa-stack-2x {
  height: 2em;
  width: 2.5em;
}

.fa-inverse {
  color: var(--fa-inverse, #fff);
}

.sr-only,
.fa-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only-focusable:not(:focus),
.fa-sr-only-focusable:not(:focus) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.svg-inline--fa .fa-primary {
  fill: var(--fa-primary-color, currentColor);
  opacity: var(--fa-primary-opacity, 1);
}

.svg-inline--fa .fa-secondary {
  fill: var(--fa-secondary-color, currentColor);
  opacity: var(--fa-secondary-opacity, 0.4);
}

.svg-inline--fa.fa-swap-opacity .fa-primary {
  opacity: var(--fa-secondary-opacity, 0.4);
}

.svg-inline--fa.fa-swap-opacity .fa-secondary {
  opacity: var(--fa-primary-opacity, 1);
}

.svg-inline--fa mask .fa-primary,
.svg-inline--fa mask .fa-secondary {
  fill: black;
}

.fad.fa-inverse,
.fa-duotone.fa-inverse {
  color: var(--fa-inverse, #fff);
}`;if(t!==n||a!==e){const i=new RegExp("\\.".concat(n,"\\-"),"g"),o=new RegExp("\\--".concat(n,"\\-"),"g"),c=new RegExp("\\.".concat(e),"g");r=r.replace(i,".".concat(t,"-")).replace(o,"--".concat(t,"-")).replace(c,".".concat(a))}return r}let he=!1;function Cn(){f.autoAddCss&&!he&&(function(n){if(!n||!B)return;const e=g.createElement("style");e.setAttribute("type","text/css"),e.innerHTML=n;const t=g.head.childNodes;let a=null;for(let r=t.length-1;r>-1;r--){const i=t[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(a=i)}g.head.insertBefore(e,a)}(rt()),he=!0)}var Bt={mixout:()=>({dom:{css:rt,insertCss:Cn}}),hooks:()=>({beforeDOMElementCreation(){Cn()},beforeI2svg(){Cn()}})};const D=_||{};D[R]||(D[R]={}),D[R].styles||(D[R].styles={}),D[R].hooks||(D[R].hooks={}),D[R].shims||(D[R].shims=[]);var F=D[R];const it=[],ot=function(){g.removeEventListener("DOMContentLoaded",ot),xn=1,it.map(n=>n())};let xn=!1;function mn(n){const{tag:e,attributes:t={},children:a=[]}=n;return typeof n=="string"?ge(n):"<".concat(e," ").concat(function(r){return Object.keys(r||{}).reduce((i,o)=>i+"".concat(o,'="').concat(ge(r[o]),'" '),"").trim()}(t),">").concat(a.map(mn).join(""),"</").concat(e,">")}function be(n,e,t){if(n&&n[e]&&n[e][t])return{prefix:e,iconName:t,icon:n[e][t]}}B&&(xn=(g.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(g.readyState),xn||g.addEventListener("DOMContentLoaded",ot));var Pn=function(n,e,t,a){var r,i,o,c=Object.keys(n),l=c.length,s=e;for(t===void 0?(r=1,o=n[c[0]]):(r=0,o=t);r<l;r++)o=s(o,n[i=c[r]],i,n);return o};function st(n){const e=function(t){const a=[];let r=0;const i=t.length;for(;r<i;){const o=t.charCodeAt(r++);if(o>=55296&&o<=56319&&r<i){const c=t.charCodeAt(r++);(64512&c)==56320?a.push(((1023&o)<<10)+(1023&c)+65536):(a.push(o),r--)}else a.push(o)}return a}(n);return e.length===1?e[0].toString(16):null}function ye(n){return Object.keys(n).reduce((e,t)=>{const a=n[t];return a.icon?e[a.iconName]=a.icon:e[t]=a,e},{})}function qn(n,e){let t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};const{skipHooks:a=!1}=t,r=ye(e);typeof F.hooks.addPack!="function"||a?F.styles[n]={...F.styles[n]||{},...r}:F.hooks.addPack(n,ye(e)),n==="fas"&&qn("fa",e)}const{styles:K,shims:Yt}=F,Wt={[h]:Object.values(V[h]),[O]:Object.values(V[O]),[C]:Object.values(V[C])};let ie=null,ct={},lt={},ft={},ut={},mt={};const Ht={[h]:Object.keys(X[h]),[O]:Object.keys(X[O]),[C]:Object.keys(X[C])};function _t(n,e){const t=e.split("-"),a=t[0],r=t.slice(1).join("-");return a!==n||r===""||(i=r,~Tt.indexOf(i))?null:r;var i}const dt=()=>{const n=a=>Pn(K,(r,i,o)=>(r[o]=Pn(i,a,{}),r),{});ct=n((a,r,i)=>(r[3]&&(a[r[3]]=i),r[2]&&r[2].filter(o=>typeof o=="number").forEach(o=>{a[o.toString(16)]=i}),a)),lt=n((a,r,i)=>(a[i]=i,r[2]&&r[2].filter(o=>typeof o=="string").forEach(o=>{a[o]=i}),a)),mt=n((a,r,i)=>{const o=r[2];return a[i]=i,o.forEach(c=>{a[c]=i}),a});const e="far"in K||f.autoFetchSvg,t=Pn(Yt,(a,r)=>{const i=r[0];let o=r[1];const c=r[2];return o!=="far"||e||(o="fas"),typeof i=="string"&&(a.names[i]={prefix:o,iconName:c}),typeof i=="number"&&(a.unicodes[i.toString(16)]={prefix:o,iconName:c}),a},{names:{},unicodes:{}});ft=t.names,ut=t.unicodes,ie=zn(f.styleDefault,{family:f.familyDefault})};var ve;function Kn(n,e){return(ct[n]||{})[e]}function H(n,e){return(mt[n]||{})[e]}function pt(n){return ft[n]||{prefix:null,iconName:null}}function U(){return ie}ve=n=>{ie=zn(n.styleDefault,{family:f.familyDefault})},Un.push(ve),dt();function zn(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{family:t=h}=e,a=X[t][n],r=cn[t][n]||cn[t][a],i=n in F.styles?n:null;return r||i||null}const Ut={[h]:Object.keys(V[h]),[O]:Object.keys(V[O]),[C]:Object.keys(V[C])};function Ln(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{skipLookups:t=!1}=e,a={[h]:"".concat(f.cssPrefix,"-").concat(h),[O]:"".concat(f.cssPrefix,"-").concat(O),[C]:"".concat(f.cssPrefix,"-").concat(C)};let r=null,i=h;const o=Nt.filter(l=>l!==Ge);o.forEach(l=>{(n.includes(a[l])||n.some(s=>Ut[l].includes(s)))&&(i=l)});const c=n.reduce((l,s)=>{const u=_t(f.cssPrefix,s);if(K[s]?(s=Wt[i].includes(s)?Ft[i][s]:s,r=s,l.prefix=s):Ht[i].indexOf(s)>-1?(r=s,l.prefix=zn(s,{family:i})):u?l.iconName=u:s===f.replacementClass||o.some(d=>s===a[d])||l.rest.push(s),!t&&l.prefix&&l.iconName){const d=r==="fa"?pt(l.iconName):{},m=H(l.prefix,l.iconName);d.prefix&&(r=null),l.iconName=d.iconName||m||l.iconName,l.prefix=d.prefix||l.prefix,l.prefix!=="far"||K.far||!K.fas||f.autoFetchSvg||(l.prefix="fas")}return l},{prefix:null,iconName:null,rest:[]});return(n.includes("fa-brands")||n.includes("fab"))&&(c.prefix="fab"),(n.includes("fa-duotone")||n.includes("fad"))&&(c.prefix="fad"),c.prefix||i!==O||!K.fass&&!f.autoFetchSvg||(c.prefix="fass",c.iconName=H(c.prefix,c.iconName)||c.iconName),c.prefix||i!==C||!K.fasds&&!f.autoFetchSvg||(c.prefix="fasds",c.iconName=H(c.prefix,c.iconName)||c.iconName),c.prefix!=="fa"&&r!=="fa"||(c.prefix=U()||"fas"),c}let xe=[],en={};const tn={},qt=Object.keys(tn);function Xn(n,e){for(var t=arguments.length,a=new Array(t>2?t-2:0),r=2;r<t;r++)a[r-2]=arguments[r];return(en[n]||[]).forEach(i=>{e=i.apply(null,[e,...a])}),e}function Z(n){for(var e=arguments.length,t=new Array(e>1?e-1:0),a=1;a<e;a++)t[a-1]=arguments[a];(en[n]||[]).forEach(r=>{r.apply(null,t)})}function q(){const n=arguments[0],e=Array.prototype.slice.call(arguments,1);return tn[n]?tn[n].apply(null,e):void 0}function Vn(n){n.prefix==="fa"&&(n.prefix="fas");let{iconName:e}=n;const t=n.prefix||U();if(e)return e=H(t,e)||e,be(gt.definitions,t,e)||be(F.styles,t,e)}const gt=new class{constructor(){this.definitions={}}add(){for(var n=arguments.length,e=new Array(n),t=0;t<n;t++)e[t]=arguments[t];const a=e.reduce(this._pullDefinitions,{});Object.keys(a).forEach(r=>{this.definitions[r]={...this.definitions[r]||{},...a[r]},qn(r,a[r]);const i=V[h][r];i&&qn(i,a[r]),dt()})}reset(){this.definitions={}}_pullDefinitions(n,e){const t=e.prefix&&e.iconName&&e.icon?{0:e}:e;return Object.keys(t).map(a=>{const{prefix:r,iconName:i,icon:o}=t[a],c=o[2];n[r]||(n[r]={}),c.length>0&&c.forEach(l=>{typeof l=="string"&&(n[r][l]=o)}),n[r][i]=o}),n}},Kt={i2svg:function(){let n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return B?(Z("beforeI2svg",n),q("pseudoElements2svg",n),q("i2svg",n)):Promise.reject(new Error("Operation requires a DOM of some kind."))},watch:function(){let n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};const{autoReplaceSvgRoot:e}=n;var t;f.autoReplaceSvg===!1&&(f.autoReplaceSvg=!0),f.observeMutations=!0,t=()=>{Xt({autoReplaceSvgRoot:e}),Z("watch",n)},B&&(xn?setTimeout(t,0):it.push(t))}},dn={noAuto:()=>{f.autoReplaceSvg=!1,f.observeMutations=!1,Z("noAuto")},config:f,dom:Kt,parse:{icon:n=>{if(n===null)return null;if(typeof n=="object"&&n.prefix&&n.iconName)return{prefix:n.prefix,iconName:H(n.prefix,n.iconName)||n.iconName};if(Array.isArray(n)&&n.length===2){const e=n[1].indexOf("fa-")===0?n[1].slice(3):n[1],t=zn(n[0]);return{prefix:t,iconName:H(t,e)||e}}if(typeof n=="string"&&(n.indexOf("".concat(f.cssPrefix,"-"))>-1||n.match(It))){const e=Ln(n.split(" "),{skipLookups:!0});return{prefix:e.prefix||U(),iconName:H(e.prefix,e.iconName)||e.iconName}}if(typeof n=="string"){const e=U();return{prefix:e,iconName:H(e,n)||n}}}},library:gt,findIconDefinition:Vn,toHtml:mn},Xt=function(){let n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};const{autoReplaceSvgRoot:e=g}=n;(Object.keys(F.styles).length>0||f.autoFetchSvg)&&B&&f.autoReplaceSvg&&dn.dom.i2svg({node:e})};function An(n,e){return Object.defineProperty(n,"abstract",{get:e}),Object.defineProperty(n,"html",{get:function(){return n.abstract.map(t=>mn(t))}}),Object.defineProperty(n,"node",{get:function(){if(!B)return;const t=g.createElement("div");return t.innerHTML=n.html,t.children}}),n}function oe(n){const{icons:{main:e,mask:t},prefix:a,iconName:r,transform:i,symbol:o,title:c,maskId:l,titleId:s,extra:u,watchable:d=!1}=n,{width:m,height:p}=t.found?t:e,w=a==="fak",z=[f.replacementClass,r?"".concat(f.cssPrefix,"-").concat(r):""].filter(b=>u.classes.indexOf(b)===-1).filter(b=>b!==""||!!b).concat(u.classes).join(" ");let k={children:[],attributes:{...u.attributes,"data-prefix":a,"data-icon":r,class:z,role:u.attributes.role||"img",xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 ".concat(m," ").concat(p)}};const N=w&&!~u.classes.indexOf("fa-fw")?{width:"".concat(m/p*16*.0625,"em")}:{};d&&(k.attributes[G]=""),c&&(k.children.push({tag:"title",attributes:{id:k.attributes["aria-labelledby"]||"title-".concat(s||fn())},children:[c]}),delete k.attributes.title);const y={...k,prefix:a,iconName:r,main:e,mask:t,maskId:l,transform:i,symbol:o,styles:{...N,...u.styles}},{children:v,attributes:M}=t.found&&e.found?q("generateAbstractMask",y)||{children:[],attributes:{}}:q("generateAbstractIcon",y)||{children:[],attributes:{}};return y.children=v,y.attributes=M,o?function(b){let{prefix:L,iconName:x,children:I,attributes:Y,symbol:P}=b;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:{...Y,id:P===!0?"".concat(L,"-").concat(f.cssPrefix,"-").concat(x):P},children:I}]}]}(y):function(b){let{children:L,main:x,mask:I,attributes:Y,styles:P,transform:S}=b;if(re(S)&&x.found&&!I.found){const{width:Nn,height:Mn}=x,le={x:Nn/Mn/2,y:.5};Y.style=wn({...P,"transform-origin":"".concat(le.x+S.x/16,"em ").concat(le.y+S.y/16,"em")})}return[{tag:"svg",attributes:Y,children:L}]}(y)}function ke(n){const{content:e,width:t,height:a,transform:r,title:i,extra:o,watchable:c=!1}=n,l={...o.attributes,...i?{title:i}:{},class:o.classes.join(" ")};c&&(l[G]="");const s={...o.styles};re(r)&&(s.transform=function(m){let{transform:p,width:w=Dn,height:z=Dn,startCentered:k=!1}=m,N="";return N+=k&&Ve?"translate(".concat(p.x/W-w/2,"em, ").concat(p.y/W-z/2,"em) "):k?"translate(calc(-50% + ".concat(p.x/W,"em), calc(-50% + ").concat(p.y/W,"em)) "):"translate(".concat(p.x/W,"em, ").concat(p.y/W,"em) "),N+="scale(".concat(p.size/W*(p.flipX?-1:1),", ").concat(p.size/W*(p.flipY?-1:1),") "),N+="rotate(".concat(p.rotate,"deg) "),N}({transform:r,startCentered:!0,width:t,height:a}),s["-webkit-transform"]=s.transform);const u=wn(s);u.length>0&&(l.style=u);const d=[];return d.push({tag:"span",attributes:l,children:[e]}),i&&d.push({tag:"span",attributes:{class:"sr-only"},children:[i]}),d}const{styles:Sn}=F;function Gn(n){const e=n[0],t=n[1],[a]=n.slice(4);let r=null;return r=Array.isArray(a)?{tag:"g",attributes:{class:"".concat(f.cssPrefix,"-").concat(On.GROUP)},children:[{tag:"path",attributes:{class:"".concat(f.cssPrefix,"-").concat(On.SECONDARY),fill:"currentColor",d:a[0]}},{tag:"path",attributes:{class:"".concat(f.cssPrefix,"-").concat(On.PRIMARY),fill:"currentColor",d:a[1]}}]}:{tag:"path",attributes:{fill:"currentColor",d:a}},{found:!0,width:e,height:t,icon:r}}const Vt={found:!1,width:512,height:512};function Zn(n,e){let t=e;return e==="fa"&&f.styleDefault!==null&&(e=U()),new Promise((a,r)=>{if(t==="fa"){const i=pt(n)||{};n=i.iconName||n,e=i.prefix||e}if(n&&e&&Sn[e]&&Sn[e][n])return a(Gn(Sn[e][n]));!$e&&f.showMissingIcons,a({...Vt,icon:f.showMissingIcons&&n&&q("missingIconAbstract")||{}})})}const we=()=>{},Jn=f.measurePerformance&&pn&&pn.mark&&pn.measure?pn:{mark:we,measure:we},sn='FA "6.6.0"',Gt=n=>{Jn.mark("".concat(sn," ").concat(n," ends")),Jn.measure("".concat(sn," ").concat(n),"".concat(sn," ").concat(n," begins"),"".concat(sn," ").concat(n," ends"))};var se=n=>(Jn.mark("".concat(sn," ").concat(n," begins")),()=>Gt(n));const yn=()=>{};function ze(n){return typeof(n.getAttribute?n.getAttribute(G):null)=="string"}function Zt(n){return g.createElementNS("http://www.w3.org/2000/svg",n)}function Jt(n){return g.createElement(n)}function ht(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{ceFn:t=n.tag==="svg"?Zt:Jt}=e;if(typeof n=="string")return g.createTextNode(n);const a=t(n.tag);return Object.keys(n.attributes||[]).forEach(function(r){a.setAttribute(r,n.attributes[r])}),(n.children||[]).forEach(function(r){a.appendChild(ht(r,{ceFn:t}))}),a}const vn={replace:function(n){const e=n[0];if(e.parentNode)if(n[1].forEach(t=>{e.parentNode.insertBefore(ht(t),e)}),e.getAttribute(G)===null&&f.keepOriginalSource){let t=g.createComment(function(a){let r=" ".concat(a.outerHTML," ");return r="".concat(r,"Font Awesome fontawesome.com "),r}(e));e.parentNode.replaceChild(t,e)}else e.remove()},nest:function(n){const e=n[0],t=n[1];if(~ae(e).indexOf(f.replacementClass))return vn.replace(n);const a=new RegExp("".concat(f.cssPrefix,"-.*"));if(delete t[0].attributes.id,t[0].attributes.class){const i=t[0].attributes.class.split(" ").reduce((o,c)=>(c===f.replacementClass||c.match(a)?o.toSvg.push(c):o.toNode.push(c),o),{toNode:[],toSvg:[]});t[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?e.removeAttribute("class"):e.setAttribute("class",i.toNode.join(" "))}const r=t.map(i=>mn(i)).join(`
`);e.setAttribute(G,""),e.innerHTML=r}};function Le(n){n()}function bt(n,e){const t=typeof e=="function"?e:yn;if(n.length===0)t();else{let a=Le;f.mutateApproach==="async"&&(a=_.requestAnimationFrame||Le),a(()=>{const r=f.autoReplaceSvg===!0?vn.replace:vn[f.autoReplaceSvg]||vn.replace,i=se("mutate");n.map(r),i(),t()})}}let ce=!1;function yt(){ce=!0}function Qn(){ce=!1}let kn=null;function Ae(n){if(!de||!f.observeMutations)return;const{treeCallback:e=yn,nodeCallback:t=yn,pseudoElementsCallback:a=yn,observeMutationsRoot:r=g}=n;kn=new de(i=>{if(ce)return;const o=U();an(i).forEach(c=>{if(c.type==="childList"&&c.addedNodes.length>0&&!ze(c.addedNodes[0])&&(f.searchPseudoElements&&a(c.target),e(c.target)),c.type==="attributes"&&c.target.parentNode&&f.searchPseudoElements&&a(c.target.parentNode),c.type==="attributes"&&ze(c.target)&&~Dt.indexOf(c.attributeName))if(c.attributeName==="class"&&function(s){const u=s.getAttribute?s.getAttribute(Bn):null,d=s.getAttribute?s.getAttribute(Yn):null;return u&&d}(c.target)){const{prefix:s,iconName:u}=Ln(ae(c.target));c.target.setAttribute(Bn,s||o),u&&c.target.setAttribute(Yn,u)}else(l=c.target)&&l.classList&&l.classList.contains&&l.classList.contains(f.replacementClass)&&t(c.target);var l})}),B&&kn.observe(r,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}function Qt(n){const e=n.getAttribute("data-prefix"),t=n.getAttribute("data-icon"),a=n.innerText!==void 0?n.innerText.trim():"";let r=Ln(ae(n));return r.prefix||(r.prefix=U()),e&&t&&(r.prefix=e,r.iconName=t),r.iconName&&r.prefix||(r.prefix&&a.length>0&&(r.iconName=(i=r.prefix,o=n.innerText,(lt[i]||{})[o]||Kn(r.prefix,st(n.innerText)))),!r.iconName&&f.autoFetchSvg&&n.firstChild&&n.firstChild.nodeType===Node.TEXT_NODE&&(r.iconName=n.firstChild.data)),r;var i,o}function Ne(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0};const{iconName:t,prefix:a,rest:r}=Qt(n),i=function(l){const s=an(l.attributes).reduce((m,p)=>(m.name!=="class"&&m.name!=="style"&&(m[p.name]=p.value),m),{}),u=l.getAttribute("title"),d=l.getAttribute("data-fa-title-id");return f.autoA11y&&(u?s["aria-labelledby"]="".concat(f.replacementClass,"-title-").concat(d||fn()):(s["aria-hidden"]="true",s.focusable="false")),s}(n),o=Xn("parseNodeAttributes",{},n);let c=e.styleParser?function(l){const s=l.getAttribute("style");let u=[];return s&&(u=s.split(";").reduce((d,m)=>{const p=m.split(":"),w=p[0],z=p.slice(1);return w&&z.length>0&&(d[w]=z.join(":").trim()),d},{})),u}(n):[];return{iconName:t,title:n.getAttribute("title"),titleId:n.getAttribute("data-fa-title-id"),prefix:a,transform:E,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:r,styles:c,attributes:i},...o}}const{styles:$t}=F;function vt(n){const e=f.autoReplaceSvg==="nest"?Ne(n,{styleParser:!1}):Ne(n);return~e.extra.classes.indexOf(tt)?q("generateLayersText",n,e):q("generateSvgReplacementMutation",n,e)}let j=new Set;function Me(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!B)return Promise.resolve();const t=g.documentElement.classList,a=u=>t.add("".concat(pe,"-").concat(u)),r=u=>t.remove("".concat(pe,"-").concat(u)),i=f.autoFetchSvg?j:nt.map(u=>"fa-".concat(u)).concat(Object.keys($t));i.includes("fa")||i.push("fa");const o=[".".concat(tt,":not([").concat(G,"])")].concat(i.map(u=>".".concat(u,":not([").concat(G,"])"))).join(", ");if(o.length===0)return Promise.resolve();let c=[];try{c=an(n.querySelectorAll(o))}catch{}if(!(c.length>0))return Promise.resolve();a("pending"),r("complete");const l=se("onTree"),s=c.reduce((u,d)=>{try{const m=vt(d);m&&u.push(m)}catch(m){$e||m.name}return u},[]);return new Promise((u,d)=>{Promise.all(s).then(m=>{bt(m,()=>{a("active"),a("complete"),r("pending"),typeof e=="function"&&e(),l(),u()})}).catch(m=>{l(),d(m)})})}function na(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;vt(n).then(t=>{t&&bt([t],e)})}nt.map(n=>{j.add("fa-".concat(n))}),Object.keys(X[h]).map(j.add.bind(j)),Object.keys(X[O]).map(j.add.bind(j)),Object.keys(X[C]).map(j.add.bind(j)),j=[...j];const ea=function(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{transform:t=E,symbol:a=!1,mask:r=null,maskId:i=null,title:o=null,titleId:c=null,classes:l=[],attributes:s={},styles:u={}}=e;if(!n)return;const{prefix:d,iconName:m,icon:p}=n;return An({type:"icon",...n},()=>(Z("beforeDOMElementCreation",{iconDefinition:n,params:e}),f.autoA11y&&(o?s["aria-labelledby"]="".concat(f.replacementClass,"-title-").concat(c||fn()):(s["aria-hidden"]="true",s.focusable="false")),oe({icons:{main:Gn(p),mask:r?Gn(r.icon):{found:!1,width:null,height:null,icon:{}}},prefix:d,iconName:m,transform:{...E,...t},symbol:a,title:o,maskId:i,titleId:c,extra:{attributes:s,styles:u,classes:l}})))};var ta={mixout(){return{icon:(n=ea,function(e){let t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const a=(e||{}).icon?e:Vn(e||{});let{mask:r}=t;return r&&(r=(r||{}).icon?r:Vn(r||{})),n(a,{...t,mask:r})})};var n},hooks:()=>({mutationObserverCallbacks:n=>(n.treeCallback=Me,n.nodeCallback=na,n)}),provides(n){n.i2svg=function(e){const{node:t=g,callback:a=()=>{}}=e;return Me(t,a)},n.generateSvgReplacementMutation=function(e,t){const{iconName:a,title:r,titleId:i,prefix:o,transform:c,symbol:l,mask:s,maskId:u,extra:d}=t;return new Promise((m,p)=>{Promise.all([Zn(a,o),s.iconName?Zn(s.iconName,s.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(w=>{let[z,k]=w;m([e,oe({icons:{main:z,mask:k},prefix:o,iconName:a,transform:c,symbol:l,maskId:u,title:r,titleId:i,extra:d,watchable:!0})])}).catch(p)})},n.generateAbstractIcon=function(e){let{children:t,attributes:a,main:r,transform:i,styles:o}=e;const c=wn(o);let l;return c.length>0&&(a.style=c),re(i)&&(l=q("generateAbstractTransformGrouping",{main:r,transform:i,containerWidth:r.width,iconWidth:r.width})),t.push(l||r.icon),{children:t,attributes:a}}}},aa={mixout:()=>({layer(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{classes:t=[]}=e;return An({type:"layer"},()=>{Z("beforeDOMElementCreation",{assembler:n,params:e});let a=[];return n(r=>{Array.isArray(r)?r.map(i=>{a=a.concat(i.abstract)}):a=a.concat(r.abstract)}),[{tag:"span",attributes:{class:["".concat(f.cssPrefix,"-layers"),...t].join(" ")},children:a}]})}})},ra={mixout:()=>({counter(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{title:t=null,classes:a=[],attributes:r={},styles:i={}}=e;return An({type:"counter",content:n},()=>(Z("beforeDOMElementCreation",{content:n,params:e}),function(o){const{content:c,title:l,extra:s}=o,u={...s.attributes,...l?{title:l}:{},class:s.classes.join(" ")},d=wn(s.styles);d.length>0&&(u.style=d);const m=[];return m.push({tag:"span",attributes:u,children:[c]}),l&&m.push({tag:"span",attributes:{class:"sr-only"},children:[l]}),m}({content:n.toString(),title:t,extra:{attributes:r,styles:i,classes:["".concat(f.cssPrefix,"-layers-counter"),...a]}})))}})},ia={mixout:()=>({text(n){let e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};const{transform:t=E,title:a=null,classes:r=[],attributes:i={},styles:o={}}=e;return An({type:"text",content:n},()=>(Z("beforeDOMElementCreation",{content:n,params:e}),ke({content:n,transform:{...E,...t},title:a,extra:{attributes:i,styles:o,classes:["".concat(f.cssPrefix,"-layers-text"),...r]}})))}}),provides(n){n.generateLayersText=function(e,t){const{title:a,transform:r,extra:i}=t;let o=null,c=null;if(Ve){const l=parseInt(getComputedStyle(e).fontSize,10),s=e.getBoundingClientRect();o=s.width/l,c=s.height/l}return f.autoA11y&&!a&&(i.attributes["aria-hidden"]="true"),Promise.resolve([e,ke({content:e.innerHTML,width:o,height:c,transform:r,title:a,extra:i,watchable:!0})])}}};const oa=new RegExp('"',"ug"),Oe=[1105920,1112319],Ce={FontAwesome:{normal:"fas",400:"fas"},"Font Awesome 6 Free":{900:"fas",400:"far"},"Font Awesome 6 Pro":{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},"Font Awesome 6 Brands":{400:"fab",normal:"fab"},"Font Awesome 6 Duotone":{900:"fad"},"Font Awesome 6 Sharp":{900:"fass",400:"fasr",normal:"fasr",300:"fasl",100:"fast"},"Font Awesome 6 Sharp Duotone":{900:"fasds"},"Font Awesome 5 Free":{900:"fas",400:"far"},"Font Awesome 5 Pro":{900:"fas",400:"far",normal:"far",300:"fal"},"Font Awesome 5 Brands":{400:"fab",normal:"fab"},"Font Awesome 5 Duotone":{900:"fad"},"Font Awesome Kit":{400:"fak",normal:"fak"},"Font Awesome Kit Duotone":{400:"fakd",normal:"fakd"}},$n=Object.keys(Ce).reduce((n,e)=>(n[e.toLowerCase()]=Ce[e],n),{}),sa=Object.keys($n).reduce((n,e)=>{const t=$n[e];return n[e]=t[900]||[...Object.entries(t)][0][1],n},{});function Pe(n,e){const t="".concat("data-fa-pseudo-element-pending").concat(e.replace(":","-"));return new Promise((a,r)=>{if(n.getAttribute(t)!==null)return a();const i=an(n.children).filter(d=>d.getAttribute(Tn)===e)[0],o=_.getComputedStyle(n,e),c=o.getPropertyValue("font-family"),l=c.match(Rt),s=o.getPropertyValue("font-weight"),u=o.getPropertyValue("content");if(i&&!l)return n.removeChild(i),a();if(l&&u!=="none"&&u!==""){const d=o.getPropertyValue("content");let m=function(y,v){const M=y.replace(/^['"]|['"]$/g,"").toLowerCase(),b=parseInt(v),L=isNaN(b)?"normal":b;return($n[M]||{})[L]||sa[M]}(c,s);const{value:p,isSecondary:w}=function(y){const v=y.replace(oa,""),M=function(x,I){const Y=x.length;let P,S=x.charCodeAt(I);return S>=55296&&S<=56319&&Y>I+1&&(P=x.charCodeAt(I+1),P>=56320&&P<=57343)?1024*(S-55296)+P-56320+65536:S}(v,0),b=M>=Oe[0]&&M<=Oe[1],L=v.length===2&&v[0]===v[1];return{value:st(L?v[0]:v),isSecondary:b||L}}(d),z=l[0].startsWith("FontAwesome");let k=Kn(m,p),N=k;if(z){const y=function(v){const M=ut[v],b=Kn("fas",v);return M||(b?{prefix:"fas",iconName:b}:null)||{prefix:null,iconName:null}}(p);y.iconName&&y.prefix&&(k=y.iconName,m=y.prefix)}if(!k||w||i&&i.getAttribute(Bn)===m&&i.getAttribute(Yn)===N)a();else{n.setAttribute(t,N),i&&n.removeChild(i);const y={iconName:null,title:null,titleId:null,prefix:null,transform:E,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}},{extra:v}=y;v.attributes[Tn]=e,Zn(k,m).then(M=>{const b=oe({...y,icons:{main:M,mask:{prefix:null,iconName:null,rest:[]}},prefix:m,iconName:N,extra:v,watchable:!0}),L=g.createElementNS("http://www.w3.org/2000/svg","svg");e==="::before"?n.insertBefore(L,n.firstChild):n.appendChild(L),L.outerHTML=b.map(x=>mn(x)).join(`
`),n.removeAttribute(t),a()}).catch(r)}}else a()})}function ca(n){return Promise.all([Pe(n,"::before"),Pe(n,"::after")])}function la(n){return!(n.parentNode===document.head||~Et.indexOf(n.tagName.toUpperCase())||n.getAttribute(Tn)||n.parentNode&&n.parentNode.tagName==="svg")}function Se(n){if(B)return new Promise((e,t)=>{const a=an(n.querySelectorAll("*")).filter(la).map(ca),r=se("searchPseudoElements");yt(),Promise.all(a).then(()=>{r(),Qn(),e()}).catch(()=>{r(),Qn(),t()})})}let je=!1;const Ee=n=>n.toLowerCase().split(" ").reduce((e,t)=>{const a=t.toLowerCase().split("-"),r=a[0];let i=a.slice(1).join("-");if(r&&i==="h")return e.flipX=!0,e;if(r&&i==="v")return e.flipY=!0,e;if(i=parseFloat(i),isNaN(i))return e;switch(r){case"grow":e.size=e.size+i;break;case"shrink":e.size=e.size-i;break;case"left":e.x=e.x-i;break;case"right":e.x=e.x+i;break;case"up":e.y=e.y-i;break;case"down":e.y=e.y+i;break;case"rotate":e.rotate=e.rotate+i}return e},{size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0}),jn={x:0,y:0,width:"100%",height:"100%"};function Fe(n){let e=!(arguments.length>1&&arguments[1]!==void 0)||arguments[1];return n.attributes&&(n.attributes.fill||e)&&(n.attributes.fill="black"),n}(function(n,e){let{mixoutsTo:t}=e;xe=n,en={},Object.keys(tn).forEach(a=>{qt.indexOf(a)===-1&&delete tn[a]}),xe.forEach(a=>{const r=a.mixout?a.mixout():{};if(Object.keys(r).forEach(i=>{typeof r[i]=="function"&&(t[i]=r[i]),typeof r[i]=="object"&&Object.keys(r[i]).forEach(o=>{t[i]||(t[i]={}),t[i][o]=r[i][o]})}),a.hooks){const i=a.hooks();Object.keys(i).forEach(o=>{en[o]||(en[o]=[]),en[o].push(i[o])})}a.provides&&a.provides(tn)})})([Bt,ta,aa,ra,ia,{hooks:()=>({mutationObserverCallbacks:n=>(n.pseudoElementsCallback=Se,n)}),provides(n){n.pseudoElements2svg=function(e){const{node:t=g}=e;f.searchPseudoElements&&Se(t)}}},{mixout:()=>({dom:{unwatch(){yt(),je=!0}}}),hooks:()=>({bootstrap(){Ae(Xn("mutationObserverCallbacks",{}))},noAuto(){kn&&kn.disconnect()},watch(n){const{observeMutationsRoot:e}=n;je?Qn():Ae(Xn("mutationObserverCallbacks",{observeMutationsRoot:e}))}})},{mixout:()=>({parse:{transform:n=>Ee(n)}}),hooks:()=>({parseNodeAttributes(n,e){const t=e.getAttribute("data-fa-transform");return t&&(n.transform=Ee(t)),n}}),provides(n){n.generateAbstractTransformGrouping=function(e){let{main:t,transform:a,containerWidth:r,iconWidth:i}=e;const o={transform:"translate(".concat(r/2," 256)")},c="translate(".concat(32*a.x,", ").concat(32*a.y,") "),l="scale(".concat(a.size/16*(a.flipX?-1:1),", ").concat(a.size/16*(a.flipY?-1:1),") "),s="rotate(".concat(a.rotate," 0 0)"),u={transform:"".concat(c," ").concat(l," ").concat(s)},d={transform:"translate(".concat(i/2*-1," -256)")};return{tag:"g",attributes:{...o},children:[{tag:"g",attributes:{...u},children:[{tag:t.icon.tag,children:t.icon.children,attributes:{...t.icon.attributes,...d}}]}]}}}},{hooks:()=>({parseNodeAttributes(n,e){const t=e.getAttribute("data-fa-mask"),a=t?Ln(t.split(" ").map(r=>r.trim())):{prefix:null,iconName:null,rest:[]};return a.prefix||(a.prefix=U()),n.mask=a,n.maskId=e.getAttribute("data-fa-mask-id"),n}}),provides(n){n.generateAbstractMask=function(e){let{children:t,attributes:a,main:r,mask:i,maskId:o,transform:c}=e;const{width:l,icon:s}=r,{width:u,icon:d}=i,m=function(L){let{transform:x,containerWidth:I,iconWidth:Y}=L;const P={transform:"translate(".concat(I/2," 256)")},S="translate(".concat(32*x.x,", ").concat(32*x.y,") "),Nn="scale(".concat(x.size/16*(x.flipX?-1:1),", ").concat(x.size/16*(x.flipY?-1:1),") "),Mn="rotate(".concat(x.rotate," 0 0)");return{outer:P,inner:{transform:"".concat(S," ").concat(Nn," ").concat(Mn)},path:{transform:"translate(".concat(Y/2*-1," -256)")}}}({transform:c,containerWidth:u,iconWidth:l}),p={tag:"rect",attributes:{...jn,fill:"white"}},w=s.children?{children:s.children.map(Fe)}:{},z={tag:"g",attributes:{...m.inner},children:[Fe({tag:s.tag,attributes:{...s.attributes,...m.path},...w})]},k={tag:"g",attributes:{...m.outer},children:[z]},N="mask-".concat(o||fn()),y="clip-".concat(o||fn()),v={tag:"mask",attributes:{...jn,id:N,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"},children:[p,k]},M={tag:"defs",children:[{tag:"clipPath",attributes:{id:y},children:(b=d,b.tag==="g"?b.children:[b])},v]};var b;return t.push(M,{tag:"rect",attributes:{fill:"currentColor","clip-path":"url(#".concat(y,")"),mask:"url(#".concat(N,")"),...jn}}),{children:t,attributes:a}}}},{provides(n){let e=!1;_.matchMedia&&(e=_.matchMedia("(prefers-reduced-motion: reduce)").matches),n.missingIconAbstract=function(){const t=[],a={fill:"currentColor"},r={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};t.push({tag:"path",attributes:{...a,d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"}});const i={...r,attributeName:"opacity"},o={tag:"circle",attributes:{...a,cx:"256",cy:"364",r:"28"},children:[]};return e||o.children.push({tag:"animate",attributes:{...r,attributeName:"r",values:"28;14;28;28;14;28;"}},{tag:"animate",attributes:{...i,values:"1;0;1;1;0;1;"}}),t.push(o),t.push({tag:"path",attributes:{...a,opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"},children:e?[]:[{tag:"animate",attributes:{...i,values:"1;0;0;0;0;1;"}}]}),e||t.push({tag:"path",attributes:{...a,opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"},children:[{tag:"animate",attributes:{...i,values:"0;0;1;1;0;0;"}}]}),{tag:"g",attributes:{class:"missing"},children:t}}}},{hooks:()=>({parseNodeAttributes(n,e){const t=e.getAttribute("data-fa-symbol"),a=t!==null&&(t===""||t);return n.symbol=a,n}})}],{mixoutsTo:dn});const ba=dn.library,ne=dn.parse,fa=dn.icon;function Ie(n,e){var t=Object.keys(n);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(n);e&&(a=a.filter(function(r){return Object.getOwnPropertyDescriptor(n,r).enumerable})),t.push.apply(t,a)}return t}function T(n){for(var e=1;e<arguments.length;e++){var t=arguments[e]!=null?arguments[e]:{};e%2?Ie(Object(t),!0).forEach(function(a){A(n,a,t[a])}):Object.getOwnPropertyDescriptors?Object.defineProperties(n,Object.getOwnPropertyDescriptors(t)):Ie(Object(t)).forEach(function(a){Object.defineProperty(n,a,Object.getOwnPropertyDescriptor(t,a))})}return n}function ua(n){var e=function(t,a){if(typeof t!="object"||!t)return t;var r=t[Symbol.toPrimitive];if(r!==void 0){var i=r.call(t,a||"default");if(typeof i!="object")return i;throw new TypeError("@@toPrimitive must return a primitive value.")}return(a==="string"?String:Number)(t)}(n,"string");return typeof e=="symbol"?e:e+""}function ee(n){return(ee=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(n)}function A(n,e,t){return(e=ua(e))in n?Object.defineProperty(n,e,{value:t,enumerable:!0,configurable:!0,writable:!0}):n[e]=t,n}function ma(n,e){if(n==null)return{};var t,a,r=function(o,c){if(o==null)return{};var l={};for(var s in o)if(Object.prototype.hasOwnProperty.call(o,s)){if(c.indexOf(s)>=0)continue;l[s]=o[s]}return l}(n,e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(n);for(a=0;a<i.length;a++)t=i[a],e.indexOf(t)>=0||Object.prototype.propertyIsEnumerable.call(n,t)&&(r[t]=n[t])}return r}var En,Re,$,gn,Fn,hn,rn,De,Te,Be,Ye,We,He,_e,bn,In,da=typeof globalThis<"u"?globalThis:typeof window<"u"?window:fe!==void 0?fe:typeof self<"u"?self:{},xt={exports:{}};En=xt,Re=da,$=function(n,e,t){if(!Te(e)||Ye(e)||We(e)||He(e)||De(e))return e;var a,r=0,i=0;if(Be(e))for(a=[],i=e.length;r<i;r++)a.push($(n,e[r],t));else for(var o in a={},e)Object.prototype.hasOwnProperty.call(e,o)&&(a[n(o,t)]=$(n,e[o],t));return a},gn=function(n){return _e(n)?n:(n=n.replace(/[\-_\s]+(.)?/g,function(e,t){return t?t.toUpperCase():""})).substr(0,1).toLowerCase()+n.substr(1)},Fn=function(n){var e=gn(n);return e.substr(0,1).toUpperCase()+e.substr(1)},hn=function(n,e){return function(t,a){var r=(a=a||{}).separator||"_",i=a.split||/(?=[A-Z])/;return t.split(i).join(r)}(n,e).toLowerCase()},rn=Object.prototype.toString,De=function(n){return typeof n=="function"},Te=function(n){return n===Object(n)},Be=function(n){return rn.call(n)=="[object Array]"},Ye=function(n){return rn.call(n)=="[object Date]"},We=function(n){return rn.call(n)=="[object RegExp]"},He=function(n){return rn.call(n)=="[object Boolean]"},_e=function(n){return(n-=0)==n},bn=function(n,e){var t=e&&"process"in e?e.process:e;return typeof t!="function"?n:function(a,r){return t(a,n,r)}},In={camelize:gn,decamelize:hn,pascalize:Fn,depascalize:hn,camelizeKeys:function(n,e){return $(bn(gn,e),n)},decamelizeKeys:function(n,e){return $(bn(hn,e),n,e)},pascalizeKeys:function(n,e){return $(bn(Fn,e),n)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}},En.exports?En.exports=In:Re.humps=In;var pa=xt.exports,ga=["class","style"];function kt(n){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof n=="string")return n;var a=(n.children||[]).map(function(l){return kt(l)}),r=Object.keys(n.attributes||{}).reduce(function(l,s){var u=n.attributes[s];switch(s){case"class":l.class=u.split(/\s+/).reduce(function(d,m){return d[m]=!0,d},{});break;case"style":l.style=u.split(";").map(function(d){return d.trim()}).filter(function(d){return d}).reduce(function(d,m){var p=m.indexOf(":"),w=pa.camelize(m.slice(0,p)),z=m.slice(p+1).trim();return d[w]=z,d},{});break;default:l.attrs[s]=u}return l},{attrs:{},class:{},style:{}});t.class;var i=t.style,o=i===void 0?{}:i,c=ma(t,ga);return At(n.tag,T(T(T({},e),{},{class:r.class,style:T(T({},r.style),o)},r.attrs),c),a)}var wt=!1;try{wt=!0}catch{}function Rn(n,e){return Array.isArray(e)&&e.length>0||!Array.isArray(e)&&e?A({},n,e):{}}function Ue(n){return n&&ee(n)==="object"&&n.prefix&&n.iconName&&n.icon?n:ne.icon?ne.icon(n):n===null?null:ee(n)==="object"&&n.prefix&&n.iconName?n:Array.isArray(n)&&n.length===2?{prefix:n[0],iconName:n[1]}:typeof n=="string"?{prefix:"fas",iconName:n}:void 0}var ya=zt({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(n){return[!0,!1,"horizontal","vertical","both"].indexOf(n)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},maskId:{type:String,default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(n){return["right","left"].indexOf(n)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(n){return[90,180,270].indexOf(Number.parseInt(n,10))>-1}},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(n){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(n)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},titleId:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1}},setup:function(n,e){var t=e.attrs,a=J(function(){return Ue(n.icon)}),r=J(function(){return Rn("classes",function(s){var u,d=(A(A(A(A(A(A(A(A(A(A(u={"fa-spin":s.spin,"fa-pulse":s.pulse,"fa-fw":s.fixedWidth,"fa-border":s.border,"fa-li":s.listItem,"fa-inverse":s.inverse,"fa-flip":s.flip===!0,"fa-flip-horizontal":s.flip==="horizontal"||s.flip==="both","fa-flip-vertical":s.flip==="vertical"||s.flip==="both"},"fa-".concat(s.size),s.size!==null),"fa-rotate-".concat(s.rotation),s.rotation!==null),"fa-pull-".concat(s.pull),s.pull!==null),"fa-swap-opacity",s.swapOpacity),"fa-bounce",s.bounce),"fa-shake",s.shake),"fa-beat",s.beat),"fa-fade",s.fade),"fa-beat-fade",s.beatFade),"fa-flash",s.flash),A(A(u,"fa-spin-pulse",s.spinPulse),"fa-spin-reverse",s.spinReverse));return Object.keys(d).map(function(m){return d[m]?m:null}).filter(function(m){return m})}(n))}),i=J(function(){return Rn("transform",typeof n.transform=="string"?ne.transform(n.transform):n.transform)}),o=J(function(){return Rn("mask",Ue(n.mask))}),c=J(function(){return fa(a.value,T(T(T(T({},r.value),i.value),o.value),{},{symbol:n.symbol,title:n.title,titleId:n.titleId,maskId:n.maskId}))});Lt(c,function(s){if(!s)return function(){var u;!wt&&console&&typeof console.error=="function"&&(u=console).error.apply(u,arguments)}("Could not find one or more icon(s)",a.value,o.value)},{immediate:!0});var l=J(function(){return c.value?kt(c.value.abstract[0],{},t):null});return function(){return l.value}}});const va={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 48 0c26.5 0 48 21.5 48 48l0 48L0 160l0-48C0 85.5 21.5 64 48 64l48 0 0-32c0-17.7 14.3-32 32-32zM0 192l448 0 0 272c0 26.5-21.5 48-48 48L48 512c-26.5 0-48-21.5-48-48L0 192zm64 80l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm128 0l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zM64 400l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zm112 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16z"]},xa={prefix:"fas",iconName:"lock",icon:[448,512,[128274],"f023","M144 144l0 48 160 0 0-48c0-44.2-35.8-80-80-80s-80 35.8-80 80zM80 192l0-48C80 64.5 144.5 0 224 0s144 64.5 144 144l0 48 16 0c35.3 0 64 28.7 64 64l0 192c0 35.3-28.7 64-64 64L64 512c-35.3 0-64-28.7-64-64L0 256c0-35.3 28.7-64 64-64l16 0z"]},ka={prefix:"fas",iconName:"pen-to-square",icon:[512,512,["edit"],"f044","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L362.3 51.7l97.9 97.9 30.1-30.1c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L437.7 172.3 339.7 74.3 172.4 241.7zM96 64C43 64 0 107 0 160L0 416c0 53 43 96 96 96l256 0c53 0 96-43 96-96l0-96c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 96c0 17.7-14.3 32-32 32L96 448c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l96 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 64z"]},wa={prefix:"fas",iconName:"star",icon:[576,512,[11088,61446],"f005","M316.9 18C311.6 7 300.4 0 288.1 0s-23.4 7-28.8 18L195 150.3 51.4 171.5c-12 1.8-22 10.2-25.7 21.7s-.7 24.2 7.9 32.7L137.8 329 113.2 474.7c-2 12 3 24.2 12.9 31.3s23 8 33.8 2.3l128.3-68.5 128.3 68.5c10.8 5.7 23.9 4.9 33.8-2.3s14.9-19.3 12.9-31.3L438.5 329 542.7 225.9c8.6-8.5 11.7-21.2 7.9-32.7s-13.7-19.9-25.7-21.7L381.2 150.3 316.9 18z"]},za={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M96 0C60.7 0 32 28.7 32 64l0 384c-17.7 0-32 14.3-32 32s14.3 32 32 32l288 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l0-144 16 0c22.1 0 40 17.9 40 40l0 32c0 39.8 32.2 72 72 72s72-32.2 72-72l0-123.7c32.5-10.2 56-40.5 56-76.3l0-32c0-8.8-7.2-16-16-16l-16 0 0-48c0-8.8-7.2-16-16-16s-16 7.2-16 16l0 48-32 0 0-48c0-8.8-7.2-16-16-16s-16 7.2-16 16l0 48-16 0c-8.8 0-16 7.2-16 16l0 32c0 35.8 23.5 66.1 56 76.3L472 376c0 13.3-10.7 24-24 24s-24-10.7-24-24l0-32c0-48.6-39.4-88-88-88l-16 0 0-192c0-35.3-28.7-64-64-64L96 0zM216.9 82.7c6 4 8.5 11.5 6.3 18.3l-25 74.9 57.8 0c6.7 0 12.7 4.2 15 10.4s.5 13.3-4.6 17.7l-112 96c-5.5 4.7-13.4 5.1-19.3 1.1s-8.5-11.5-6.3-18.3l25-74.9L96 208c-6.7 0-12.7-4.2-15-10.4s-.5-13.3 4.6-17.7l112-96c5.5-4.7 13.4-5.1 19.3-1.1z"]},La={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 96c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l16 0c35.3 0 64 28.7 64 64l0 224c0 35.3-28.7 64-64 64L64 448c-35.3 0-64-28.7-64-64L0 160c0-35.3 28.7-64 64-64l16 0zm304 96c0-8.8-7.2-16-16-16s-16 7.2-16 16l0 32-32 0c-8.8 0-16 7.2-16 16s7.2 16 16 16l32 0 0 32c0 8.8 7.2 16 16 16s16-7.2 16-16l0-32 32 0c8.8 0 16-7.2 16-16s-7.2-16-16-16l-32 0 0-32zM80 240c0 8.8 7.2 16 16 16l96 0c8.8 0 16-7.2 16-16s-7.2-16-16-16l-96 0c-8.8 0-16 7.2-16 16z"]},Aa={prefix:"fas",iconName:"plug-circle-bolt",icon:[576,512,[],"e55b","M96 0C78.3 0 64 14.3 64 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32l0 32c0 77.4 55 142 128 156.8l0 67.2c0 17.7 14.3 32 32 32s32-14.3 32-32l0-67.2c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32L32 160zM432 512a144 144 0 1 0 0-288 144 144 0 1 0 0 288zm47.9-225c4.3 3.7 5.4 9.9 2.6 14.9L452.4 356l35.6 0c5.2 0 9.8 3.3 11.4 8.2s-.1 10.3-4.2 13.4l-96 72c-4.5 3.4-10.8 3.2-15.1-.6s-5.4-9.9-2.6-14.9L411.6 380 376 380c-5.2 0-9.8-3.3-11.4-8.2s.1-10.3 4.2-13.4l96-72c4.5-3.4 10.8-3.2 15.1 .6z"]},Na={prefix:"fas",iconName:"solar-panel",icon:[640,512,[],"f5ba","M122.2 0C91.7 0 65.5 21.5 59.5 51.4L8.3 307.4C.4 347 30.6 384 71 384l217 0 0 64-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l192 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0 0-64 217 0c40.4 0 70.7-36.9 62.8-76.6l-51.2-256C574.5 21.5 548.3 0 517.8 0L122.2 0zM260.9 64l118.2 0 10.4 104-139 0L260.9 64zM202.3 168l-100.8 0L122.2 64l90.4 0L202.3 168zM91.8 216l105.6 0L187.1 320 71 320 91.8 216zm153.9 0l148.6 0 10.4 104-169.4 0 10.4-104zm196.8 0l105.6 0L569 320l-116 0L442.5 216zm96-48l-100.8 0L427.3 64l90.4 0 31.4-6.3L517.8 64l20.8 104z"]},Ma={prefix:"fas",iconName:"lock-open",icon:[576,512,[],"f3c1","M352 144c0-44.2 35.8-80 80-80s80 35.8 80 80l0 48c0 17.7 14.3 32 32 32s32-14.3 32-32l0-48C576 64.5 511.5 0 432 0S288 64.5 288 144l0 48L64 192c-35.3 0-64 28.7-64 64L0 448c0 35.3 28.7 64 64 64l320 0c35.3 0 64-28.7 64-64l0-192c0-35.3-28.7-64-64-64l-32 0 0-48z"]},Oa={prefix:"fas",iconName:"wrench",icon:[512,512,[128295],"f0ad","M352 320c88.4 0 160-71.6 160-160c0-15.3-2.2-30.1-6.2-44.2c-3.1-10.8-16.4-13.2-24.3-5.3l-76.8 76.8c-3 3-7.1 4.7-11.3 4.7L336 192c-8.8 0-16-7.2-16-16l0-57.4c0-4.2 1.7-8.3 4.7-11.3l76.8-76.8c7.9-7.9 5.4-21.2-5.3-24.3C382.1 2.2 367.3 0 352 0C263.6 0 192 71.6 192 160c0 19.1 3.4 37.5 9.5 54.5L19.9 396.1C7.2 408.8 0 426.1 0 444.1C0 481.6 30.4 512 67.9 512c18 0 35.3-7.2 48-19.9L297.5 310.5c17 6.2 35.4 9.5 54.5 9.5zM80 408a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"]},Ca={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM216 336l24 0 0-64-24 0c-13.3 0-24-10.7-24-24s10.7-24 24-24l48 0c13.3 0 24 10.7 24 24l0 88 8 0c13.3 0 24 10.7 24 24s-10.7 24-24 24l-80 0c-13.3 0-24-10.7-24-24s10.7-24 24-24zm40-208a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"]},Pa={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M125.7 160l50.3 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L48 224c-17.7 0-32-14.3-32-32L16 64c0-17.7 14.3-32 32-32s32 14.3 32 32l0 51.2L97.6 97.6c87.5-87.5 229.3-87.5 316.8 0s87.5 229.3 0 316.8s-229.3 87.5-316.8 0c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0c62.5 62.5 163.8 62.5 226.3 0s62.5-163.8 0-226.3s-163.8-62.5-226.3 0L125.7 160z"]},Sa={prefix:"fas",iconName:"plug-circle-check",icon:[576,512,[],"e55c","M96 0C78.3 0 64 14.3 64 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32l0 32c0 77.4 55 142 128 156.8l0 67.2c0 17.7 14.3 32 32 32s32-14.3 32-32l0-67.2c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32L32 160zM576 368a144 144 0 1 0 -288 0 144 144 0 1 0 288 0zm-76.7-43.3c6.2 6.2 6.2 16.4 0 22.6l-72 72c-6.2 6.2-16.4 6.2-22.6 0l-40-40c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0L416 385.4l60.7-60.7c6.2-6.2 16.4-6.2 22.6 0z"]},ja={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512A256 256 0 1 1 256 0zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},Ea={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 224c0 17.7 14.3 32 32 32s32-14.3 32-32l0-224zM143.5 120.6c13.6-11.3 15.4-31.5 4.1-45.1s-31.5-15.4-45.1-4.1C49.7 115.4 16 181.8 16 256c0 132.5 107.5 240 240 240s240-107.5 240-240c0-74.2-33.8-140.6-86.6-184.6c-13.6-11.3-33.8-9.4-45.1 4.1s-9.4 33.8 4.1 45.1c38.9 32.3 63.5 81 63.5 135.4c0 97.2-78.8 176-176 176s-176-78.8-176-176c0-54.4 24.7-103.1 63.5-135.4z"]},Fa={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-384c0-35.3-28.7-64-64-64L64 0zM96 64l192 0c17.7 0 32 14.3 32 32l0 32c0 17.7-14.3 32-32 32L96 160c-17.7 0-32-14.3-32-32l0-32c0-17.7 14.3-32 32-32zm32 160a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zM96 352a32 32 0 1 1 0-64 32 32 0 1 1 0 64zM64 416c0-17.7 14.3-32 32-32l96 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-96 0c-17.7 0-32-14.3-32-32zM192 256a32 32 0 1 1 0-64 32 32 0 1 1 0 64zm32 64a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zm64-64a32 32 0 1 1 0-64 32 32 0 1 1 0 64zm32 64a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zM288 448a32 32 0 1 1 0-64 32 32 0 1 1 0 64z"]},Ia={prefix:"fas",iconName:"delete-left",icon:[576,512,[9003,"backspace"],"f55a","M576 128c0-35.3-28.7-64-64-64L205.3 64c-17 0-33.3 6.7-45.3 18.7L9.4 233.4c-6 6-9.4 14.1-9.4 22.6s3.4 16.6 9.4 22.6L160 429.3c12 12 28.3 18.7 45.3 18.7L512 448c35.3 0 64-28.7 64-64l0-256zM271 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},Ra={prefix:"fas",iconName:"house",icon:[576,512,[127968,63498,63500,"home","home-alt","home-lg-alt"],"f015","M575.8 255.5c0 18-15 32.1-32 32.1l-32 0 .7 160.2c0 2.7-.2 5.4-.5 8.1l0 16.2c0 22.1-17.9 40-40 40l-16 0c-1.1 0-2.2 0-3.3-.1c-1.4 .1-2.8 .1-4.2 .1L416 512l-24 0c-22.1 0-40-17.9-40-40l0-24 0-64c0-17.7-14.3-32-32-32l-64 0c-17.7 0-32 14.3-32 32l0 64 0 24c0 22.1-17.9 40-40 40l-24 0-31.9 0c-1.5 0-3-.1-4.5-.2c-1.2 .1-2.4 .2-3.6 .2l-16 0c-22.1 0-40-17.9-40-40l0-112c0-.9 0-1.9 .1-2.8l0-69.7-32 0c-18 0-32-14-32-32.1c0-9 3-17 10-24L266.4 8c7-7 15-8 22-8s15 2 21 7L564.8 231.5c8 7 12 15 11 24z"]},Da={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 48 0c26.5 0 48 21.5 48 48l0 48L0 160l0-48C0 85.5 21.5 64 48 64l48 0 0-32c0-17.7 14.3-32 32-32zM0 192l448 0 0 272c0 26.5-21.5 48-48 48L48 512c-26.5 0-48-21.5-48-48L0 192zm80 64c-8.8 0-16 7.2-16 16l0 64c0 8.8 7.2 16 16 16l288 0c8.8 0 16-7.2 16-16l0-64c0-8.8-7.2-16-16-16L80 256z"]},Ta={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M349.4 44.6c5.9-13.7 1.5-29.7-10.6-38.5s-28.6-8-39.9 1.8l-256 224c-10 8.8-13.6 22.9-8.9 35.3S50.7 288 64 288l111.5 0L98.6 467.4c-5.9 13.7-1.5 29.7 10.6 38.5s28.6 8 39.9-1.8l256-224c10-8.8 13.6-22.9 8.9-35.3s-16.6-20.7-30-20.7l-111.5 0L349.4 44.6z"]},Ba={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4L109.1 192l293.8 0-26.1-74.6C372.3 104.6 360.2 96 346.6 96L165.4 96c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32l181.2 0c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2l0 144 0 48c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-48L96 400l0 48c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-48L0 256c0-26.7 16.4-49.6 39.6-59.2zM128 288a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},Ya={prefix:"fas",iconName:"plug-circle-xmark",icon:[576,512,[],"e560","M96 0C78.3 0 64 14.3 64 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32l0 96 64 0 0-96c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32l0 32c0 77.4 55 142 128 156.8l0 67.2c0 17.7 14.3 32 32 32s32-14.3 32-32l0-67.2c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32L32 160zM432 512a144 144 0 1 0 0-288 144 144 0 1 0 0 288zm59.3-180.7L454.6 368l36.7 36.7c6.2 6.2 6.2 16.4 0 22.6s-16.4 6.2-22.6 0L432 390.6l-36.7 36.7c-6.2 6.2-16.4 6.2-22.6 0s-6.2-16.4 0-22.6L409.4 368l-36.7-36.7c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0L432 345.4l36.7-36.7c6.2-6.2 16.4-6.2 22.6 0s6.2 16.4 0 22.6z"]},Wa={prefix:"fas",iconName:"eraser",icon:[576,512,[],"f12d","M290.7 57.4L57.4 290.7c-25 25-25 65.5 0 90.5l80 80c12 12 28.3 18.7 45.3 18.7L288 480l9.4 0L512 480c17.7 0 32-14.3 32-32s-14.3-32-32-32l-124.1 0L518.6 285.3c25-25 25-65.5 0-90.5L381.3 57.4c-25-25-65.5-25-90.5 0zM297.4 416l-9.4 0-105.4 0-80-80L227.3 211.3 364.7 348.7 297.4 416z"]},Ha={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64c0-17.4-6.9-33.1-18.1-44.6L366 161.7c5.3-12.1-.2-26.3-12.3-31.6s-26.3 .2-31.6 12.3L257.9 288c-.6 0-1.3 0-1.9 0c-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},_a={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 32c14.2 0 27.3 7.5 34.5 19.8l216 368c7.3 12.4 7.3 27.7 .2 40.1S486.3 480 472 480L40 480c-14.3 0-27.6-7.7-34.7-20.1s-7-27.8 .2-40.1l216-368C228.7 39.5 241.8 32 256 32zm0 128c-13.3 0-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24s24-10.7 24-24l0-112c0-13.3-10.7-24-24-24zm32 224a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},Ua={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 48 0c26.5 0 48 21.5 48 48l0 48L0 160l0-48C0 85.5 21.5 64 48 64l48 0 0-32c0-17.7 14.3-32 32-32zM0 192l448 0 0 272c0 26.5-21.5 48-48 48L48 512c-26.5 0-48-21.5-48-48L0 192zm80 64c-8.8 0-16 7.2-16 16l0 96c0 8.8 7.2 16 16 16l96 0c8.8 0 16-7.2 16-16l0-96c0-8.8-7.2-16-16-16l-96 0z"]},qa={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM175 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},Ka={prefix:"far",iconName:"star",icon:[576,512,[11088,61446],"f005","M287.9 0c9.2 0 17.6 5.2 21.6 13.5l68.6 141.3 153.2 22.6c9 1.3 16.5 7.6 19.3 16.3s.5 18.1-5.9 24.5L433.6 328.4l26.2 155.6c1.5 9-2.2 18.1-9.7 23.5s-17.3 6-25.3 1.7l-137-73.2L151 509.1c-8.1 4.3-17.9 3.7-25.3-1.7s-11.2-14.5-9.7-23.5l26.2-155.6L31.1 218.2c-6.5-6.4-8.7-15.9-5.9-24.5s10.3-14.9 19.3-16.3l153.2-22.6L266.3 13.5C270.4 5.2 278.7 0 287.9 0zm0 79L235.4 187.2c-3.5 7.1-10.2 12.1-18.1 13.3L99 217.9 184.9 303c5.5 5.5 8.1 13.3 6.8 21L171.4 443.7l105.2-56.2c7.1-3.8 15.6-3.8 22.6 0l105.2 56.2L384.2 324.1c-1.3-7.7 1.2-15.5 6.8-21l85.9-85.1L358.6 200.5c-7.8-1.2-14.6-6.1-18.1-13.3L287.9 79z"]},Xa={prefix:"far",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M464 256A208 208 0 1 1 48 256a208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0A256 256 0 1 0 0 256zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]};export{Sa as A,Aa as B,Pa as C,Ea as D,ya as F,Wa as a,xa as b,Ma as c,Ha as d,La as e,Ia as f,Na as g,Ra as h,za as i,Fa as j,Oa as k,ba as l,Ba as m,ka as n,qa as o,_a as p,Ca as q,wa as r,Ka as s,ja as t,Xa as u,Ta as v,Ua as w,Da as x,va as y,Ya as z};
