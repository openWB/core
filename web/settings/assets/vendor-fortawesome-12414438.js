import{d as Ka,f as ue,j as L,w as hn,h as Re}from"./vendor-b78ff8c0.js";function me(a,e){var n=Object.keys(a);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(a);e&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),n.push.apply(n,t)}return n}function u(a){for(var e=1;e<arguments.length;e++){var n=arguments[e]!=null?arguments[e]:{};e%2?me(Object(n),!0).forEach(function(t){z(a,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(n)):me(Object(n)).forEach(function(t){Object.defineProperty(a,t,Object.getOwnPropertyDescriptor(n,t))})}return a}function Ca(a){return Ca=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},Ca(a)}function yn(a,e){if(!(a instanceof e))throw new TypeError("Cannot call a class as a function")}function ve(a,e){for(var n=0;n<e.length;n++){var t=e[n];t.enumerable=t.enumerable||!1,t.configurable=!0,"value"in t&&(t.writable=!0),Object.defineProperty(a,t.key,t)}}function xn(a,e,n){return e&&ve(a.prototype,e),n&&ve(a,n),Object.defineProperty(a,"prototype",{writable:!1}),a}function z(a,e,n){return e in a?Object.defineProperty(a,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):a[e]=n,a}function Qa(a,e){return wn(a)||zn(a,e)||De(a,e)||Hn()}function fa(a){return kn(a)||Cn(a)||De(a)||An()}function kn(a){if(Array.isArray(a))return Ta(a)}function wn(a){if(Array.isArray(a))return a}function Cn(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function zn(a,e){var n=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(n!=null){var t=[],r=!0,i=!1,o,s;try{for(n=n.call(a);!(r=(o=n.next()).done)&&(t.push(o.value),!(e&&t.length===e));r=!0);}catch(c){i=!0,s=c}finally{try{!r&&n.return!=null&&n.return()}finally{if(i)throw s}}return t}}function De(a,e){if(a){if(typeof a=="string")return Ta(a,e);var n=Object.prototype.toString.call(a).slice(8,-1);if(n==="Object"&&a.constructor&&(n=a.constructor.name),n==="Map"||n==="Set")return Array.from(a);if(n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return Ta(a,e)}}function Ta(a,e){(e==null||e>a.length)&&(e=a.length);for(var n=0,t=new Array(e);n<e;n++)t[n]=a[n];return t}function An(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function Hn(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var de=function(){},Za={},je={},$e=null,Ye={mark:de,measure:de};try{typeof window<"u"&&(Za=window),typeof document<"u"&&(je=document),typeof MutationObserver<"u"&&($e=MutationObserver),typeof performance<"u"&&(Ye=performance)}catch{}var Sn=Za.navigator||{},pe=Sn.userAgent,be=pe===void 0?"":pe,$=Za,x=je,ge=$e,ma=Ye;$.document;var R=!!x.documentElement&&!!x.head&&typeof x.addEventListener=="function"&&typeof x.createElement=="function",Ue=~be.indexOf("MSIE")||~be.indexOf("Trident/"),va,da,pa,ba,ga,_="___FONT_AWESOME___",Fa=16,Be="fa",We="svg-inline--fa",G="data-fa-i2svg",Ra="data-fa-pseudo-element",Mn="data-fa-pseudo-element-pending",Ja="data-prefix",ae="data-icon",he="fontawesome-i2svg",On="async",Nn=["HTML","HEAD","STYLE","SCRIPT"],Ge=function(){try{return!1}catch{return!1}}(),y="classic",k="sharp",ee=[y,k];function la(a){return new Proxy(a,{get:function(n,t){return t in n?n[t]:n[y]}})}var ra=la((va={},z(va,y,{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fad:"duotone","fa-duotone":"duotone",fab:"brands","fa-brands":"brands",fak:"kit","fa-kit":"kit"}),z(va,k,{fa:"solid",fass:"solid","fa-solid":"solid"}),va)),ia=la((da={},z(da,y,{solid:"fas",regular:"far",light:"fal",thin:"fat",duotone:"fad",brands:"fab",kit:"fak"}),z(da,k,{solid:"fass"}),da)),oa=la((pa={},z(pa,y,{fab:"fa-brands",fad:"fa-duotone",fak:"fa-kit",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"}),z(pa,k,{fass:"fa-solid"}),pa)),Ln=la((ba={},z(ba,y,{"fa-brands":"fab","fa-duotone":"fad","fa-kit":"fak","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"}),z(ba,k,{"fa-solid":"fass"}),ba)),Vn=/fa(s|r|l|t|d|b|k|ss)?[\-\ ]/,Xe="fa-layers-text",Pn=/Font ?Awesome ?([56 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp|Kit)?.*/i,En=la((ga={},z(ga,y,{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"}),z(ga,k,{900:"fass"}),ga)),qe=[1,2,3,4,5,6,7,8,9,10],In=qe.concat([11,12,13,14,15,16,17,18,19,20]),_n=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],B={GROUP:"duotone-group",SWAP_OPACITY:"swap-opacity",PRIMARY:"primary",SECONDARY:"secondary"},sa=new Set;Object.keys(ia[y]).map(sa.add.bind(sa));Object.keys(ia[k]).map(sa.add.bind(sa));var Tn=[].concat(ee,fa(sa),["2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","fw","inverse","layers-counter","layers-text","layers","li","pull-left","pull-right","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul",B.GROUP,B.SWAP_OPACITY,B.PRIMARY,B.SECONDARY]).concat(qe.map(function(a){return"".concat(a,"x")})).concat(In.map(function(a){return"w-".concat(a)})),ea=$.FontAwesomeConfig||{};function Fn(a){var e=x.querySelector("script["+a+"]");if(e)return e.getAttribute(a)}function Rn(a){return a===""?!0:a==="false"?!1:a==="true"?!0:a}if(x&&typeof x.querySelector=="function"){var Dn=[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-auto-a11y","autoA11y"],["data-search-pseudo-elements","searchPseudoElements"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]];Dn.forEach(function(a){var e=Qa(a,2),n=e[0],t=e[1],r=Rn(Fn(n));r!=null&&(ea[t]=r)})}var Ke={styleDefault:"solid",familyDefault:"classic",cssPrefix:Be,replacementClass:We,autoReplaceSvg:!0,autoAddCss:!0,autoA11y:!0,searchPseudoElements:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};ea.familyPrefix&&(ea.cssPrefix=ea.familyPrefix);var Z=u(u({},Ke),ea);Z.autoReplaceSvg||(Z.observeMutations=!1);var m={};Object.keys(Ke).forEach(function(a){Object.defineProperty(m,a,{enumerable:!0,set:function(n){Z[a]=n,na.forEach(function(t){return t(m)})},get:function(){return Z[a]}})});Object.defineProperty(m,"familyPrefix",{enumerable:!0,set:function(e){Z.cssPrefix=e,na.forEach(function(n){return n(m)})},get:function(){return Z.cssPrefix}});$.FontAwesomeConfig=m;var na=[];function jn(a){return na.push(a),function(){na.splice(na.indexOf(a),1)}}var j=Fa,I={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function $n(a){if(!(!a||!R)){var e=x.createElement("style");e.setAttribute("type","text/css"),e.innerHTML=a;for(var n=x.head.childNodes,t=null,r=n.length-1;r>-1;r--){var i=n[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(t=i)}return x.head.insertBefore(e,t),a}}var Yn="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";function ca(){for(var a=12,e="";a-- >0;)e+=Yn[Math.random()*62|0];return e}function J(a){for(var e=[],n=(a||[]).length>>>0;n--;)e[n]=a[n];return e}function ne(a){return a.classList?J(a.classList):(a.getAttribute("class")||"").split(" ").filter(function(e){return e})}function Qe(a){return"".concat(a).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function Un(a){return Object.keys(a||{}).reduce(function(e,n){return e+"".concat(n,'="').concat(Qe(a[n]),'" ')},"").trim()}function Ma(a){return Object.keys(a||{}).reduce(function(e,n){return e+"".concat(n,": ").concat(a[n].trim(),";")},"")}function te(a){return a.size!==I.size||a.x!==I.x||a.y!==I.y||a.rotate!==I.rotate||a.flipX||a.flipY}function Bn(a){var e=a.transform,n=a.containerWidth,t=a.iconWidth,r={transform:"translate(".concat(n/2," 256)")},i="translate(".concat(e.x*32,", ").concat(e.y*32,") "),o="scale(".concat(e.size/16*(e.flipX?-1:1),", ").concat(e.size/16*(e.flipY?-1:1),") "),s="rotate(".concat(e.rotate," 0 0)"),c={transform:"".concat(i," ").concat(o," ").concat(s)},l={transform:"translate(".concat(t/2*-1," -256)")};return{outer:r,inner:c,path:l}}function Wn(a){var e=a.transform,n=a.width,t=n===void 0?Fa:n,r=a.height,i=r===void 0?Fa:r,o=a.startCentered,s=o===void 0?!1:o,c="";return s&&Ue?c+="translate(".concat(e.x/j-t/2,"em, ").concat(e.y/j-i/2,"em) "):s?c+="translate(calc(-50% + ".concat(e.x/j,"em), calc(-50% + ").concat(e.y/j,"em)) "):c+="translate(".concat(e.x/j,"em, ").concat(e.y/j,"em) "),c+="scale(".concat(e.size/j*(e.flipX?-1:1),", ").concat(e.size/j*(e.flipY?-1:1),") "),c+="rotate(".concat(e.rotate,"deg) "),c}var Gn=`:root, :host {
  --fa-font-solid: normal 900 1em/1 "Font Awesome 6 Solid";
  --fa-font-regular: normal 400 1em/1 "Font Awesome 6 Regular";
  --fa-font-light: normal 300 1em/1 "Font Awesome 6 Light";
  --fa-font-thin: normal 100 1em/1 "Font Awesome 6 Thin";
  --fa-font-duotone: normal 900 1em/1 "Font Awesome 6 Duotone";
  --fa-font-sharp-solid: normal 900 1em/1 "Font Awesome 6 Sharp";
  --fa-font-brands: normal 400 1em/1 "Font Awesome 6 Brands";
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
  -webkit-transform-origin: center center;
          transform-origin: center center;
}

.fa-layers-text {
  left: 50%;
  top: 50%;
  -webkit-transform: translate(-50%, -50%);
          transform: translate(-50%, -50%);
  -webkit-transform-origin: center center;
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
  -webkit-transform: scale(var(--fa-counter-scale, 0.25));
          transform: scale(var(--fa-counter-scale, 0.25));
  -webkit-transform-origin: top right;
          transform-origin: top right;
}

.fa-layers-bottom-right {
  bottom: var(--fa-bottom, 0);
  right: var(--fa-right, 0);
  top: auto;
  -webkit-transform: scale(var(--fa-layers-scale, 0.25));
          transform: scale(var(--fa-layers-scale, 0.25));
  -webkit-transform-origin: bottom right;
          transform-origin: bottom right;
}

.fa-layers-bottom-left {
  bottom: var(--fa-bottom, 0);
  left: var(--fa-left, 0);
  right: auto;
  top: auto;
  -webkit-transform: scale(var(--fa-layers-scale, 0.25));
          transform: scale(var(--fa-layers-scale, 0.25));
  -webkit-transform-origin: bottom left;
          transform-origin: bottom left;
}

.fa-layers-top-right {
  top: var(--fa-top, 0);
  right: var(--fa-right, 0);
  -webkit-transform: scale(var(--fa-layers-scale, 0.25));
          transform: scale(var(--fa-layers-scale, 0.25));
  -webkit-transform-origin: top right;
          transform-origin: top right;
}

.fa-layers-top-left {
  left: var(--fa-left, 0);
  right: auto;
  top: var(--fa-top, 0);
  -webkit-transform: scale(var(--fa-layers-scale, 0.25));
          transform: scale(var(--fa-layers-scale, 0.25));
  -webkit-transform-origin: top left;
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
  left: calc(var(--fa-li-width, 2em) * -1);
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
  -webkit-animation-name: fa-beat;
          animation-name: fa-beat;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, ease-in-out);
          animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-bounce {
  -webkit-animation-name: fa-bounce;
          animation-name: fa-bounce;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.28, 0.84, 0.42, 1));
          animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.28, 0.84, 0.42, 1));
}

.fa-fade {
  -webkit-animation-name: fa-fade;
          animation-name: fa-fade;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
          animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
}

.fa-beat-fade {
  -webkit-animation-name: fa-beat-fade;
          animation-name: fa-beat-fade;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
          animation-timing-function: var(--fa-animation-timing, cubic-bezier(0.4, 0, 0.6, 1));
}

.fa-flip {
  -webkit-animation-name: fa-flip;
          animation-name: fa-flip;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, ease-in-out);
          animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-shake {
  -webkit-animation-name: fa-shake;
          animation-name: fa-shake;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, linear);
          animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin {
  -webkit-animation-name: fa-spin;
          animation-name: fa-spin;
  -webkit-animation-delay: var(--fa-animation-delay, 0s);
          animation-delay: var(--fa-animation-delay, 0s);
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 2s);
          animation-duration: var(--fa-animation-duration, 2s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, linear);
          animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin-reverse {
  --fa-animation-direction: reverse;
}

.fa-pulse,
.fa-spin-pulse {
  -webkit-animation-name: fa-spin;
          animation-name: fa-spin;
  -webkit-animation-direction: var(--fa-animation-direction, normal);
          animation-direction: var(--fa-animation-direction, normal);
  -webkit-animation-duration: var(--fa-animation-duration, 1s);
          animation-duration: var(--fa-animation-duration, 1s);
  -webkit-animation-iteration-count: var(--fa-animation-iteration-count, infinite);
          animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  -webkit-animation-timing-function: var(--fa-animation-timing, steps(8));
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
    -webkit-animation-delay: -1ms;
            animation-delay: -1ms;
    -webkit-animation-duration: 1ms;
            animation-duration: 1ms;
    -webkit-animation-iteration-count: 1;
            animation-iteration-count: 1;
    transition-delay: 0s;
    transition-duration: 0s;
  }
}
@-webkit-keyframes fa-beat {
  0%, 90% {
    -webkit-transform: scale(1);
            transform: scale(1);
  }
  45% {
    -webkit-transform: scale(var(--fa-beat-scale, 1.25));
            transform: scale(var(--fa-beat-scale, 1.25));
  }
}
@keyframes fa-beat {
  0%, 90% {
    -webkit-transform: scale(1);
            transform: scale(1);
  }
  45% {
    -webkit-transform: scale(var(--fa-beat-scale, 1.25));
            transform: scale(var(--fa-beat-scale, 1.25));
  }
}
@-webkit-keyframes fa-bounce {
  0% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
  10% {
    -webkit-transform: scale(var(--fa-bounce-start-scale-x, 1.1), var(--fa-bounce-start-scale-y, 0.9)) translateY(0);
            transform: scale(var(--fa-bounce-start-scale-x, 1.1), var(--fa-bounce-start-scale-y, 0.9)) translateY(0);
  }
  30% {
    -webkit-transform: scale(var(--fa-bounce-jump-scale-x, 0.9), var(--fa-bounce-jump-scale-y, 1.1)) translateY(var(--fa-bounce-height, -0.5em));
            transform: scale(var(--fa-bounce-jump-scale-x, 0.9), var(--fa-bounce-jump-scale-y, 1.1)) translateY(var(--fa-bounce-height, -0.5em));
  }
  50% {
    -webkit-transform: scale(var(--fa-bounce-land-scale-x, 1.05), var(--fa-bounce-land-scale-y, 0.95)) translateY(0);
            transform: scale(var(--fa-bounce-land-scale-x, 1.05), var(--fa-bounce-land-scale-y, 0.95)) translateY(0);
  }
  57% {
    -webkit-transform: scale(1, 1) translateY(var(--fa-bounce-rebound, -0.125em));
            transform: scale(1, 1) translateY(var(--fa-bounce-rebound, -0.125em));
  }
  64% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
  100% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
}
@keyframes fa-bounce {
  0% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
  10% {
    -webkit-transform: scale(var(--fa-bounce-start-scale-x, 1.1), var(--fa-bounce-start-scale-y, 0.9)) translateY(0);
            transform: scale(var(--fa-bounce-start-scale-x, 1.1), var(--fa-bounce-start-scale-y, 0.9)) translateY(0);
  }
  30% {
    -webkit-transform: scale(var(--fa-bounce-jump-scale-x, 0.9), var(--fa-bounce-jump-scale-y, 1.1)) translateY(var(--fa-bounce-height, -0.5em));
            transform: scale(var(--fa-bounce-jump-scale-x, 0.9), var(--fa-bounce-jump-scale-y, 1.1)) translateY(var(--fa-bounce-height, -0.5em));
  }
  50% {
    -webkit-transform: scale(var(--fa-bounce-land-scale-x, 1.05), var(--fa-bounce-land-scale-y, 0.95)) translateY(0);
            transform: scale(var(--fa-bounce-land-scale-x, 1.05), var(--fa-bounce-land-scale-y, 0.95)) translateY(0);
  }
  57% {
    -webkit-transform: scale(1, 1) translateY(var(--fa-bounce-rebound, -0.125em));
            transform: scale(1, 1) translateY(var(--fa-bounce-rebound, -0.125em));
  }
  64% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
  100% {
    -webkit-transform: scale(1, 1) translateY(0);
            transform: scale(1, 1) translateY(0);
  }
}
@-webkit-keyframes fa-fade {
  50% {
    opacity: var(--fa-fade-opacity, 0.4);
  }
}
@keyframes fa-fade {
  50% {
    opacity: var(--fa-fade-opacity, 0.4);
  }
}
@-webkit-keyframes fa-beat-fade {
  0%, 100% {
    opacity: var(--fa-beat-fade-opacity, 0.4);
    -webkit-transform: scale(1);
            transform: scale(1);
  }
  50% {
    opacity: 1;
    -webkit-transform: scale(var(--fa-beat-fade-scale, 1.125));
            transform: scale(var(--fa-beat-fade-scale, 1.125));
  }
}
@keyframes fa-beat-fade {
  0%, 100% {
    opacity: var(--fa-beat-fade-opacity, 0.4);
    -webkit-transform: scale(1);
            transform: scale(1);
  }
  50% {
    opacity: 1;
    -webkit-transform: scale(var(--fa-beat-fade-scale, 1.125));
            transform: scale(var(--fa-beat-fade-scale, 1.125));
  }
}
@-webkit-keyframes fa-flip {
  50% {
    -webkit-transform: rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -180deg));
            transform: rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -180deg));
  }
}
@keyframes fa-flip {
  50% {
    -webkit-transform: rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -180deg));
            transform: rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -180deg));
  }
}
@-webkit-keyframes fa-shake {
  0% {
    -webkit-transform: rotate(-15deg);
            transform: rotate(-15deg);
  }
  4% {
    -webkit-transform: rotate(15deg);
            transform: rotate(15deg);
  }
  8%, 24% {
    -webkit-transform: rotate(-18deg);
            transform: rotate(-18deg);
  }
  12%, 28% {
    -webkit-transform: rotate(18deg);
            transform: rotate(18deg);
  }
  16% {
    -webkit-transform: rotate(-22deg);
            transform: rotate(-22deg);
  }
  20% {
    -webkit-transform: rotate(22deg);
            transform: rotate(22deg);
  }
  32% {
    -webkit-transform: rotate(-12deg);
            transform: rotate(-12deg);
  }
  36% {
    -webkit-transform: rotate(12deg);
            transform: rotate(12deg);
  }
  40%, 100% {
    -webkit-transform: rotate(0deg);
            transform: rotate(0deg);
  }
}
@keyframes fa-shake {
  0% {
    -webkit-transform: rotate(-15deg);
            transform: rotate(-15deg);
  }
  4% {
    -webkit-transform: rotate(15deg);
            transform: rotate(15deg);
  }
  8%, 24% {
    -webkit-transform: rotate(-18deg);
            transform: rotate(-18deg);
  }
  12%, 28% {
    -webkit-transform: rotate(18deg);
            transform: rotate(18deg);
  }
  16% {
    -webkit-transform: rotate(-22deg);
            transform: rotate(-22deg);
  }
  20% {
    -webkit-transform: rotate(22deg);
            transform: rotate(22deg);
  }
  32% {
    -webkit-transform: rotate(-12deg);
            transform: rotate(-12deg);
  }
  36% {
    -webkit-transform: rotate(12deg);
            transform: rotate(12deg);
  }
  40%, 100% {
    -webkit-transform: rotate(0deg);
            transform: rotate(0deg);
  }
}
@-webkit-keyframes fa-spin {
  0% {
    -webkit-transform: rotate(0deg);
            transform: rotate(0deg);
  }
  100% {
    -webkit-transform: rotate(360deg);
            transform: rotate(360deg);
  }
}
@keyframes fa-spin {
  0% {
    -webkit-transform: rotate(0deg);
            transform: rotate(0deg);
  }
  100% {
    -webkit-transform: rotate(360deg);
            transform: rotate(360deg);
  }
}
.fa-rotate-90 {
  -webkit-transform: rotate(90deg);
          transform: rotate(90deg);
}

.fa-rotate-180 {
  -webkit-transform: rotate(180deg);
          transform: rotate(180deg);
}

.fa-rotate-270 {
  -webkit-transform: rotate(270deg);
          transform: rotate(270deg);
}

.fa-flip-horizontal {
  -webkit-transform: scale(-1, 1);
          transform: scale(-1, 1);
}

.fa-flip-vertical {
  -webkit-transform: scale(1, -1);
          transform: scale(1, -1);
}

.fa-flip-both,
.fa-flip-horizontal.fa-flip-vertical {
  -webkit-transform: scale(-1, -1);
          transform: scale(-1, -1);
}

.fa-rotate-by {
  -webkit-transform: rotate(var(--fa-rotate-angle, none));
          transform: rotate(var(--fa-rotate-angle, none));
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
}`;function Ze(){var a=Be,e=We,n=m.cssPrefix,t=m.replacementClass,r=Gn;if(n!==a||t!==e){var i=new RegExp("\\.".concat(a,"\\-"),"g"),o=new RegExp("\\--".concat(a,"\\-"),"g"),s=new RegExp("\\.".concat(e),"g");r=r.replace(i,".".concat(n,"-")).replace(o,"--".concat(n,"-")).replace(s,".".concat(t))}return r}var ye=!1;function Pa(){m.autoAddCss&&!ye&&($n(Ze()),ye=!0)}var Xn={mixout:function(){return{dom:{css:Ze,insertCss:Pa}}},hooks:function(){return{beforeDOMElementCreation:function(){Pa()},beforeI2svg:function(){Pa()}}}},T=$||{};T[_]||(T[_]={});T[_].styles||(T[_].styles={});T[_].hooks||(T[_].hooks={});T[_].shims||(T[_].shims=[]);var P=T[_],Je=[],qn=function a(){x.removeEventListener("DOMContentLoaded",a),za=1,Je.map(function(e){return e()})},za=!1;R&&(za=(x.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(x.readyState),za||x.addEventListener("DOMContentLoaded",qn));function Kn(a){R&&(za?setTimeout(a,0):Je.push(a))}function ua(a){var e=a.tag,n=a.attributes,t=n===void 0?{}:n,r=a.children,i=r===void 0?[]:r;return typeof a=="string"?Qe(a):"<".concat(e," ").concat(Un(t),">").concat(i.map(ua).join(""),"</").concat(e,">")}function xe(a,e,n){if(a&&a[e]&&a[e][n])return{prefix:e,iconName:n,icon:a[e][n]}}var Qn=function(e,n){return function(t,r,i,o){return e.call(n,t,r,i,o)}},Ea=function(e,n,t,r){var i=Object.keys(e),o=i.length,s=r!==void 0?Qn(n,r):n,c,l,f;for(t===void 0?(c=1,f=e[i[0]]):(c=0,f=t);c<o;c++)l=i[c],f=s(f,e[l],l,e);return f};function Zn(a){for(var e=[],n=0,t=a.length;n<t;){var r=a.charCodeAt(n++);if(r>=55296&&r<=56319&&n<t){var i=a.charCodeAt(n++);(i&64512)==56320?e.push(((r&1023)<<10)+(i&1023)+65536):(e.push(r),n--)}else e.push(r)}return e}function Da(a){var e=Zn(a);return e.length===1?e[0].toString(16):null}function Jn(a,e){var n=a.length,t=a.charCodeAt(e),r;return t>=55296&&t<=56319&&n>e+1&&(r=a.charCodeAt(e+1),r>=56320&&r<=57343)?(t-55296)*1024+r-56320+65536:t}function ke(a){return Object.keys(a).reduce(function(e,n){var t=a[n],r=!!t.icon;return r?e[t.iconName]=t.icon:e[n]=t,e},{})}function ja(a,e){var n=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{},t=n.skipHooks,r=t===void 0?!1:t,i=ke(e);typeof P.hooks.addPack=="function"&&!r?P.hooks.addPack(a,ke(e)):P.styles[a]=u(u({},P.styles[a]||{}),i),a==="fas"&&ja("fa",e)}var ha,ya,xa,q=P.styles,at=P.shims,et=(ha={},z(ha,y,Object.values(oa[y])),z(ha,k,Object.values(oa[k])),ha),re=null,an={},en={},nn={},tn={},rn={},nt=(ya={},z(ya,y,Object.keys(ra[y])),z(ya,k,Object.keys(ra[k])),ya);function tt(a){return~Tn.indexOf(a)}function rt(a,e){var n=e.split("-"),t=n[0],r=n.slice(1).join("-");return t===a&&r!==""&&!tt(r)?r:null}var on=function(){var e=function(i){return Ea(q,function(o,s,c){return o[c]=Ea(s,i,{}),o},{})};an=e(function(r,i,o){if(i[3]&&(r[i[3]]=o),i[2]){var s=i[2].filter(function(c){return typeof c=="number"});s.forEach(function(c){r[c.toString(16)]=o})}return r}),en=e(function(r,i,o){if(r[o]=o,i[2]){var s=i[2].filter(function(c){return typeof c=="string"});s.forEach(function(c){r[c]=o})}return r}),rn=e(function(r,i,o){var s=i[2];return r[o]=o,s.forEach(function(c){r[c]=o}),r});var n="far"in q||m.autoFetchSvg,t=Ea(at,function(r,i){var o=i[0],s=i[1],c=i[2];return s==="far"&&!n&&(s="fas"),typeof o=="string"&&(r.names[o]={prefix:s,iconName:c}),typeof o=="number"&&(r.unicodes[o.toString(16)]={prefix:s,iconName:c}),r},{names:{},unicodes:{}});nn=t.names,tn=t.unicodes,re=Oa(m.styleDefault,{family:m.familyDefault})};jn(function(a){re=Oa(a.styleDefault,{family:m.familyDefault})});on();function ie(a,e){return(an[a]||{})[e]}function it(a,e){return(en[a]||{})[e]}function W(a,e){return(rn[a]||{})[e]}function sn(a){return nn[a]||{prefix:null,iconName:null}}function ot(a){var e=tn[a],n=ie("fas",a);return e||(n?{prefix:"fas",iconName:n}:null)||{prefix:null,iconName:null}}function Y(){return re}var oe=function(){return{prefix:null,iconName:null,rest:[]}};function Oa(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=e.family,t=n===void 0?y:n,r=ra[t][a],i=ia[t][a]||ia[t][r],o=a in P.styles?a:null;return i||o||null}var we=(xa={},z(xa,y,Object.keys(oa[y])),z(xa,k,Object.keys(oa[k])),xa);function Na(a){var e,n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.skipLookups,r=t===void 0?!1:t,i=(e={},z(e,y,"".concat(m.cssPrefix,"-").concat(y)),z(e,k,"".concat(m.cssPrefix,"-").concat(k)),e),o=null,s=y;(a.includes(i[y])||a.some(function(l){return we[y].includes(l)}))&&(s=y),(a.includes(i[k])||a.some(function(l){return we[k].includes(l)}))&&(s=k);var c=a.reduce(function(l,f){var v=rt(m.cssPrefix,f);if(q[f]?(f=et[s].includes(f)?Ln[s][f]:f,o=f,l.prefix=f):nt[s].indexOf(f)>-1?(o=f,l.prefix=Oa(f,{family:s})):v?l.iconName=v:f!==m.replacementClass&&f!==i[y]&&f!==i[k]&&l.rest.push(f),!r&&l.prefix&&l.iconName){var b=o==="fa"?sn(l.iconName):{},g=W(l.prefix,l.iconName);b.prefix&&(o=null),l.iconName=b.iconName||g||l.iconName,l.prefix=b.prefix||l.prefix,l.prefix==="far"&&!q.far&&q.fas&&!m.autoFetchSvg&&(l.prefix="fas")}return l},oe());return(a.includes("fa-brands")||a.includes("fab"))&&(c.prefix="fab"),(a.includes("fa-duotone")||a.includes("fad"))&&(c.prefix="fad"),!c.prefix&&s===k&&(q.fass||m.autoFetchSvg)&&(c.prefix="fass",c.iconName=W(c.prefix,c.iconName)||c.iconName),(c.prefix==="fa"||o==="fa")&&(c.prefix=Y()||"fas"),c}var st=function(){function a(){yn(this,a),this.definitions={}}return xn(a,[{key:"add",value:function(){for(var n=this,t=arguments.length,r=new Array(t),i=0;i<t;i++)r[i]=arguments[i];var o=r.reduce(this._pullDefinitions,{});Object.keys(o).forEach(function(s){n.definitions[s]=u(u({},n.definitions[s]||{}),o[s]),ja(s,o[s]);var c=oa[y][s];c&&ja(c,o[s]),on()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(n,t){var r=t.prefix&&t.iconName&&t.icon?{0:t}:t;return Object.keys(r).map(function(i){var o=r[i],s=o.prefix,c=o.iconName,l=o.icon,f=l[2];n[s]||(n[s]={}),f.length>0&&f.forEach(function(v){typeof v=="string"&&(n[s][v]=l)}),n[s][c]=l}),n}}]),a}(),Ce=[],K={},Q={},ct=Object.keys(Q);function ft(a,e){var n=e.mixoutsTo;return Ce=a,K={},Object.keys(Q).forEach(function(t){ct.indexOf(t)===-1&&delete Q[t]}),Ce.forEach(function(t){var r=t.mixout?t.mixout():{};if(Object.keys(r).forEach(function(o){typeof r[o]=="function"&&(n[o]=r[o]),Ca(r[o])==="object"&&Object.keys(r[o]).forEach(function(s){n[o]||(n[o]={}),n[o][s]=r[o][s]})}),t.hooks){var i=t.hooks();Object.keys(i).forEach(function(o){K[o]||(K[o]=[]),K[o].push(i[o])})}t.provides&&t.provides(Q)}),n}function $a(a,e){for(var n=arguments.length,t=new Array(n>2?n-2:0),r=2;r<n;r++)t[r-2]=arguments[r];var i=K[a]||[];return i.forEach(function(o){e=o.apply(null,[e].concat(t))}),e}function X(a){for(var e=arguments.length,n=new Array(e>1?e-1:0),t=1;t<e;t++)n[t-1]=arguments[t];var r=K[a]||[];r.forEach(function(i){i.apply(null,n)})}function F(){var a=arguments[0],e=Array.prototype.slice.call(arguments,1);return Q[a]?Q[a].apply(null,e):void 0}function Ya(a){a.prefix==="fa"&&(a.prefix="fas");var e=a.iconName,n=a.prefix||Y();if(e)return e=W(n,e)||e,xe(cn.definitions,n,e)||xe(P.styles,n,e)}var cn=new st,lt=function(){m.autoReplaceSvg=!1,m.observeMutations=!1,X("noAuto")},ut={i2svg:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return R?(X("beforeI2svg",e),F("pseudoElements2svg",e),F("i2svg",e)):Promise.reject("Operation requires a DOM of some kind.")},watch:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=e.autoReplaceSvgRoot;m.autoReplaceSvg===!1&&(m.autoReplaceSvg=!0),m.observeMutations=!0,Kn(function(){vt({autoReplaceSvgRoot:n}),X("watch",e)})}},mt={icon:function(e){if(e===null)return null;if(Ca(e)==="object"&&e.prefix&&e.iconName)return{prefix:e.prefix,iconName:W(e.prefix,e.iconName)||e.iconName};if(Array.isArray(e)&&e.length===2){var n=e[1].indexOf("fa-")===0?e[1].slice(3):e[1],t=Oa(e[0]);return{prefix:t,iconName:W(t,n)||n}}if(typeof e=="string"&&(e.indexOf("".concat(m.cssPrefix,"-"))>-1||e.match(Vn))){var r=Na(e.split(" "),{skipLookups:!0});return{prefix:r.prefix||Y(),iconName:W(r.prefix,r.iconName)||r.iconName}}if(typeof e=="string"){var i=Y();return{prefix:i,iconName:W(i,e)||e}}}},O={noAuto:lt,config:m,dom:ut,parse:mt,library:cn,findIconDefinition:Ya,toHtml:ua},vt=function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=e.autoReplaceSvgRoot,t=n===void 0?x:n;(Object.keys(P.styles).length>0||m.autoFetchSvg)&&R&&m.autoReplaceSvg&&O.dom.i2svg({node:t})};function La(a,e){return Object.defineProperty(a,"abstract",{get:e}),Object.defineProperty(a,"html",{get:function(){return a.abstract.map(function(t){return ua(t)})}}),Object.defineProperty(a,"node",{get:function(){if(R){var t=x.createElement("div");return t.innerHTML=a.html,t.children}}}),a}function dt(a){var e=a.children,n=a.main,t=a.mask,r=a.attributes,i=a.styles,o=a.transform;if(te(o)&&n.found&&!t.found){var s=n.width,c=n.height,l={x:s/c/2,y:.5};r.style=Ma(u(u({},i),{},{"transform-origin":"".concat(l.x+o.x/16,"em ").concat(l.y+o.y/16,"em")}))}return[{tag:"svg",attributes:r,children:e}]}function pt(a){var e=a.prefix,n=a.iconName,t=a.children,r=a.attributes,i=a.symbol,o=i===!0?"".concat(e,"-").concat(m.cssPrefix,"-").concat(n):i;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:u(u({},r),{},{id:o}),children:t}]}]}function se(a){var e=a.icons,n=e.main,t=e.mask,r=a.prefix,i=a.iconName,o=a.transform,s=a.symbol,c=a.title,l=a.maskId,f=a.titleId,v=a.extra,b=a.watchable,g=b===void 0?!1:b,A=t.found?t:n,H=A.width,S=A.height,d=r==="fak",p=[m.replacementClass,i?"".concat(m.cssPrefix,"-").concat(i):""].filter(function(D){return v.classes.indexOf(D)===-1}).filter(function(D){return D!==""||!!D}).concat(v.classes).join(" "),h={children:[],attributes:u(u({},v.attributes),{},{"data-prefix":r,"data-icon":i,class:p,role:v.attributes.role||"img",xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 ".concat(H," ").concat(S)})},w=d&&!~v.classes.indexOf("fa-fw")?{width:"".concat(H/S*16*.0625,"em")}:{};g&&(h.attributes[G]=""),c&&(h.children.push({tag:"title",attributes:{id:h.attributes["aria-labelledby"]||"title-".concat(f||ca())},children:[c]}),delete h.attributes.title);var C=u(u({},h),{},{prefix:r,iconName:i,main:n,mask:t,maskId:l,transform:o,symbol:s,styles:u(u({},w),v.styles)}),E=t.found&&n.found?F("generateAbstractMask",C)||{children:[],attributes:{}}:F("generateAbstractIcon",C)||{children:[],attributes:{}},N=E.children,Va=E.attributes;return C.children=N,C.attributes=Va,s?pt(C):dt(C)}function ze(a){var e=a.content,n=a.width,t=a.height,r=a.transform,i=a.title,o=a.extra,s=a.watchable,c=s===void 0?!1:s,l=u(u(u({},o.attributes),i?{title:i}:{}),{},{class:o.classes.join(" ")});c&&(l[G]="");var f=u({},o.styles);te(r)&&(f.transform=Wn({transform:r,startCentered:!0,width:n,height:t}),f["-webkit-transform"]=f.transform);var v=Ma(f);v.length>0&&(l.style=v);var b=[];return b.push({tag:"span",attributes:l,children:[e]}),i&&b.push({tag:"span",attributes:{class:"sr-only"},children:[i]}),b}function bt(a){var e=a.content,n=a.title,t=a.extra,r=u(u(u({},t.attributes),n?{title:n}:{}),{},{class:t.classes.join(" ")}),i=Ma(t.styles);i.length>0&&(r.style=i);var o=[];return o.push({tag:"span",attributes:r,children:[e]}),n&&o.push({tag:"span",attributes:{class:"sr-only"},children:[n]}),o}var Ia=P.styles;function Ua(a){var e=a[0],n=a[1],t=a.slice(4),r=Qa(t,1),i=r[0],o=null;return Array.isArray(i)?o={tag:"g",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.GROUP)},children:[{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.SECONDARY),fill:"currentColor",d:i[0]}},{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.PRIMARY),fill:"currentColor",d:i[1]}}]}:o={tag:"path",attributes:{fill:"currentColor",d:i}},{found:!0,width:e,height:n,icon:o}}var gt={found:!1,width:512,height:512};function ht(a,e){!Ge&&!m.showMissingIcons&&a&&console.error('Icon with name "'.concat(a,'" and prefix "').concat(e,'" is missing.'))}function Ba(a,e){var n=e;return e==="fa"&&m.styleDefault!==null&&(e=Y()),new Promise(function(t,r){if(F("missingIconAbstract"),n==="fa"){var i=sn(a)||{};a=i.iconName||a,e=i.prefix||e}if(a&&e&&Ia[e]&&Ia[e][a]){var o=Ia[e][a];return t(Ua(o))}ht(a,e),t(u(u({},gt),{},{icon:m.showMissingIcons&&a?F("missingIconAbstract")||{}:{}}))})}var Ae=function(){},Wa=m.measurePerformance&&ma&&ma.mark&&ma.measure?ma:{mark:Ae,measure:Ae},aa='FA "6.2.1"',yt=function(e){return Wa.mark("".concat(aa," ").concat(e," begins")),function(){return fn(e)}},fn=function(e){Wa.mark("".concat(aa," ").concat(e," ends")),Wa.measure("".concat(aa," ").concat(e),"".concat(aa," ").concat(e," begins"),"".concat(aa," ").concat(e," ends"))},ce={begin:yt,end:fn},ka=function(){};function He(a){var e=a.getAttribute?a.getAttribute(G):null;return typeof e=="string"}function xt(a){var e=a.getAttribute?a.getAttribute(Ja):null,n=a.getAttribute?a.getAttribute(ae):null;return e&&n}function kt(a){return a&&a.classList&&a.classList.contains&&a.classList.contains(m.replacementClass)}function wt(){if(m.autoReplaceSvg===!0)return wa.replace;var a=wa[m.autoReplaceSvg];return a||wa.replace}function Ct(a){return x.createElementNS("http://www.w3.org/2000/svg",a)}function zt(a){return x.createElement(a)}function ln(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=e.ceFn,t=n===void 0?a.tag==="svg"?Ct:zt:n;if(typeof a=="string")return x.createTextNode(a);var r=t(a.tag);Object.keys(a.attributes||[]).forEach(function(o){r.setAttribute(o,a.attributes[o])});var i=a.children||[];return i.forEach(function(o){r.appendChild(ln(o,{ceFn:t}))}),r}function At(a){var e=" ".concat(a.outerHTML," ");return e="".concat(e,"Font Awesome fontawesome.com "),e}var wa={replace:function(e){var n=e[0];if(n.parentNode)if(e[1].forEach(function(r){n.parentNode.insertBefore(ln(r),n)}),n.getAttribute(G)===null&&m.keepOriginalSource){var t=x.createComment(At(n));n.parentNode.replaceChild(t,n)}else n.remove()},nest:function(e){var n=e[0],t=e[1];if(~ne(n).indexOf(m.replacementClass))return wa.replace(e);var r=new RegExp("".concat(m.cssPrefix,"-.*"));if(delete t[0].attributes.id,t[0].attributes.class){var i=t[0].attributes.class.split(" ").reduce(function(s,c){return c===m.replacementClass||c.match(r)?s.toSvg.push(c):s.toNode.push(c),s},{toNode:[],toSvg:[]});t[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?n.removeAttribute("class"):n.setAttribute("class",i.toNode.join(" "))}var o=t.map(function(s){return ua(s)}).join(`
`);n.setAttribute(G,""),n.innerHTML=o}};function Se(a){a()}function un(a,e){var n=typeof e=="function"?e:ka;if(a.length===0)n();else{var t=Se;m.mutateApproach===On&&(t=$.requestAnimationFrame||Se),t(function(){var r=wt(),i=ce.begin("mutate");a.map(r),i(),n()})}}var fe=!1;function mn(){fe=!0}function Ga(){fe=!1}var Aa=null;function Me(a){if(ge&&m.observeMutations){var e=a.treeCallback,n=e===void 0?ka:e,t=a.nodeCallback,r=t===void 0?ka:t,i=a.pseudoElementsCallback,o=i===void 0?ka:i,s=a.observeMutationsRoot,c=s===void 0?x:s;Aa=new ge(function(l){if(!fe){var f=Y();J(l).forEach(function(v){if(v.type==="childList"&&v.addedNodes.length>0&&!He(v.addedNodes[0])&&(m.searchPseudoElements&&o(v.target),n(v.target)),v.type==="attributes"&&v.target.parentNode&&m.searchPseudoElements&&o(v.target.parentNode),v.type==="attributes"&&He(v.target)&&~_n.indexOf(v.attributeName))if(v.attributeName==="class"&&xt(v.target)){var b=Na(ne(v.target)),g=b.prefix,A=b.iconName;v.target.setAttribute(Ja,g||f),A&&v.target.setAttribute(ae,A)}else kt(v.target)&&r(v.target)})}}),R&&Aa.observe(c,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function Ht(){Aa&&Aa.disconnect()}function St(a){var e=a.getAttribute("style"),n=[];return e&&(n=e.split(";").reduce(function(t,r){var i=r.split(":"),o=i[0],s=i.slice(1);return o&&s.length>0&&(t[o]=s.join(":").trim()),t},{})),n}function Mt(a){var e=a.getAttribute("data-prefix"),n=a.getAttribute("data-icon"),t=a.innerText!==void 0?a.innerText.trim():"",r=Na(ne(a));return r.prefix||(r.prefix=Y()),e&&n&&(r.prefix=e,r.iconName=n),r.iconName&&r.prefix||(r.prefix&&t.length>0&&(r.iconName=it(r.prefix,a.innerText)||ie(r.prefix,Da(a.innerText))),!r.iconName&&m.autoFetchSvg&&a.firstChild&&a.firstChild.nodeType===Node.TEXT_NODE&&(r.iconName=a.firstChild.data)),r}function Ot(a){var e=J(a.attributes).reduce(function(r,i){return r.name!=="class"&&r.name!=="style"&&(r[i.name]=i.value),r},{}),n=a.getAttribute("title"),t=a.getAttribute("data-fa-title-id");return m.autoA11y&&(n?e["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(t||ca()):(e["aria-hidden"]="true",e.focusable="false")),e}function Nt(){return{iconName:null,title:null,titleId:null,prefix:null,transform:I,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}}}function Oe(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},n=Mt(a),t=n.iconName,r=n.prefix,i=n.rest,o=Ot(a),s=$a("parseNodeAttributes",{},a),c=e.styleParser?St(a):[];return u({iconName:t,title:a.getAttribute("title"),titleId:a.getAttribute("data-fa-title-id"),prefix:r,transform:I,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:i,styles:c,attributes:o}},s)}var Lt=P.styles;function vn(a){var e=m.autoReplaceSvg==="nest"?Oe(a,{styleParser:!1}):Oe(a);return~e.extra.classes.indexOf(Xe)?F("generateLayersText",a,e):F("generateSvgReplacementMutation",a,e)}var U=new Set;ee.map(function(a){U.add("fa-".concat(a))});Object.keys(ra[y]).map(U.add.bind(U));Object.keys(ra[k]).map(U.add.bind(U));U=fa(U);function Ne(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!R)return Promise.resolve();var n=x.documentElement.classList,t=function(v){return n.add("".concat(he,"-").concat(v))},r=function(v){return n.remove("".concat(he,"-").concat(v))},i=m.autoFetchSvg?U:ee.map(function(f){return"fa-".concat(f)}).concat(Object.keys(Lt));i.includes("fa")||i.push("fa");var o=[".".concat(Xe,":not([").concat(G,"])")].concat(i.map(function(f){return".".concat(f,":not([").concat(G,"])")})).join(", ");if(o.length===0)return Promise.resolve();var s=[];try{s=J(a.querySelectorAll(o))}catch{}if(s.length>0)t("pending"),r("complete");else return Promise.resolve();var c=ce.begin("onTree"),l=s.reduce(function(f,v){try{var b=vn(v);b&&f.push(b)}catch(g){Ge||g.name==="MissingIcon"&&console.error(g)}return f},[]);return new Promise(function(f,v){Promise.all(l).then(function(b){un(b,function(){t("active"),t("complete"),r("pending"),typeof e=="function"&&e(),c(),f()})}).catch(function(b){c(),v(b)})})}function Vt(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;vn(a).then(function(n){n&&un([n],e)})}function Pt(a){return function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=(e||{}).icon?e:Ya(e||{}),r=n.mask;return r&&(r=(r||{}).icon?r:Ya(r||{})),a(t,u(u({},n),{},{mask:r}))}}var Et=function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.transform,r=t===void 0?I:t,i=n.symbol,o=i===void 0?!1:i,s=n.mask,c=s===void 0?null:s,l=n.maskId,f=l===void 0?null:l,v=n.title,b=v===void 0?null:v,g=n.titleId,A=g===void 0?null:g,H=n.classes,S=H===void 0?[]:H,d=n.attributes,p=d===void 0?{}:d,h=n.styles,w=h===void 0?{}:h;if(e){var C=e.prefix,E=e.iconName,N=e.icon;return La(u({type:"icon"},e),function(){return X("beforeDOMElementCreation",{iconDefinition:e,params:n}),m.autoA11y&&(b?p["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(A||ca()):(p["aria-hidden"]="true",p.focusable="false")),se({icons:{main:Ua(N),mask:c?Ua(c.icon):{found:!1,width:null,height:null,icon:{}}},prefix:C,iconName:E,transform:u(u({},I),r),symbol:o,title:b,maskId:f,titleId:A,extra:{attributes:p,styles:w,classes:S}})})}},It={mixout:function(){return{icon:Pt(Et)}},hooks:function(){return{mutationObserverCallbacks:function(n){return n.treeCallback=Ne,n.nodeCallback=Vt,n}}},provides:function(e){e.i2svg=function(n){var t=n.node,r=t===void 0?x:t,i=n.callback,o=i===void 0?function(){}:i;return Ne(r,o)},e.generateSvgReplacementMutation=function(n,t){var r=t.iconName,i=t.title,o=t.titleId,s=t.prefix,c=t.transform,l=t.symbol,f=t.mask,v=t.maskId,b=t.extra;return new Promise(function(g,A){Promise.all([Ba(r,s),f.iconName?Ba(f.iconName,f.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(H){var S=Qa(H,2),d=S[0],p=S[1];g([n,se({icons:{main:d,mask:p},prefix:s,iconName:r,transform:c,symbol:l,maskId:v,title:i,titleId:o,extra:b,watchable:!0})])}).catch(A)})},e.generateAbstractIcon=function(n){var t=n.children,r=n.attributes,i=n.main,o=n.transform,s=n.styles,c=Ma(s);c.length>0&&(r.style=c);var l;return te(o)&&(l=F("generateAbstractTransformGrouping",{main:i,transform:o,containerWidth:i.width,iconWidth:i.width})),t.push(l||i.icon),{children:t,attributes:r}}}},_t={mixout:function(){return{layer:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.classes,i=r===void 0?[]:r;return La({type:"layer"},function(){X("beforeDOMElementCreation",{assembler:n,params:t});var o=[];return n(function(s){Array.isArray(s)?s.map(function(c){o=o.concat(c.abstract)}):o=o.concat(s.abstract)}),[{tag:"span",attributes:{class:["".concat(m.cssPrefix,"-layers")].concat(fa(i)).join(" ")},children:o}]})}}}},Tt={mixout:function(){return{counter:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.title,i=r===void 0?null:r,o=t.classes,s=o===void 0?[]:o,c=t.attributes,l=c===void 0?{}:c,f=t.styles,v=f===void 0?{}:f;return La({type:"counter",content:n},function(){return X("beforeDOMElementCreation",{content:n,params:t}),bt({content:n.toString(),title:i,extra:{attributes:l,styles:v,classes:["".concat(m.cssPrefix,"-layers-counter")].concat(fa(s))}})})}}}},Ft={mixout:function(){return{text:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.transform,i=r===void 0?I:r,o=t.title,s=o===void 0?null:o,c=t.classes,l=c===void 0?[]:c,f=t.attributes,v=f===void 0?{}:f,b=t.styles,g=b===void 0?{}:b;return La({type:"text",content:n},function(){return X("beforeDOMElementCreation",{content:n,params:t}),ze({content:n,transform:u(u({},I),i),title:s,extra:{attributes:v,styles:g,classes:["".concat(m.cssPrefix,"-layers-text")].concat(fa(l))}})})}}},provides:function(e){e.generateLayersText=function(n,t){var r=t.title,i=t.transform,o=t.extra,s=null,c=null;if(Ue){var l=parseInt(getComputedStyle(n).fontSize,10),f=n.getBoundingClientRect();s=f.width/l,c=f.height/l}return m.autoA11y&&!r&&(o.attributes["aria-hidden"]="true"),Promise.resolve([n,ze({content:n.innerHTML,width:s,height:c,transform:i,title:r,extra:o,watchable:!0})])}}},Rt=new RegExp('"',"ug"),Le=[1105920,1112319];function Dt(a){var e=a.replace(Rt,""),n=Jn(e,0),t=n>=Le[0]&&n<=Le[1],r=e.length===2?e[0]===e[1]:!1;return{value:Da(r?e[0]:e),isSecondary:t||r}}function Ve(a,e){var n="".concat(Mn).concat(e.replace(":","-"));return new Promise(function(t,r){if(a.getAttribute(n)!==null)return t();var i=J(a.children),o=i.filter(function(N){return N.getAttribute(Ra)===e})[0],s=$.getComputedStyle(a,e),c=s.getPropertyValue("font-family").match(Pn),l=s.getPropertyValue("font-weight"),f=s.getPropertyValue("content");if(o&&!c)return a.removeChild(o),t();if(c&&f!=="none"&&f!==""){var v=s.getPropertyValue("content"),b=~["Sharp"].indexOf(c[2])?k:y,g=~["Solid","Regular","Light","Thin","Duotone","Brands","Kit"].indexOf(c[2])?ia[b][c[2].toLowerCase()]:En[b][l],A=Dt(v),H=A.value,S=A.isSecondary,d=c[0].startsWith("FontAwesome"),p=ie(g,H),h=p;if(d){var w=ot(H);w.iconName&&w.prefix&&(p=w.iconName,g=w.prefix)}if(p&&!S&&(!o||o.getAttribute(Ja)!==g||o.getAttribute(ae)!==h)){a.setAttribute(n,h),o&&a.removeChild(o);var C=Nt(),E=C.extra;E.attributes[Ra]=e,Ba(p,g).then(function(N){var Va=se(u(u({},C),{},{icons:{main:N,mask:oe()},prefix:g,iconName:h,extra:E,watchable:!0})),D=x.createElement("svg");e==="::before"?a.insertBefore(D,a.firstChild):a.appendChild(D),D.outerHTML=Va.map(function(gn){return ua(gn)}).join(`
`),a.removeAttribute(n),t()}).catch(r)}else t()}else t()})}function jt(a){return Promise.all([Ve(a,"::before"),Ve(a,"::after")])}function $t(a){return a.parentNode!==document.head&&!~Nn.indexOf(a.tagName.toUpperCase())&&!a.getAttribute(Ra)&&(!a.parentNode||a.parentNode.tagName!=="svg")}function Pe(a){if(R)return new Promise(function(e,n){var t=J(a.querySelectorAll("*")).filter($t).map(jt),r=ce.begin("searchPseudoElements");mn(),Promise.all(t).then(function(){r(),Ga(),e()}).catch(function(){r(),Ga(),n()})})}var Yt={hooks:function(){return{mutationObserverCallbacks:function(n){return n.pseudoElementsCallback=Pe,n}}},provides:function(e){e.pseudoElements2svg=function(n){var t=n.node,r=t===void 0?x:t;m.searchPseudoElements&&Pe(r)}}},Ee=!1,Ut={mixout:function(){return{dom:{unwatch:function(){mn(),Ee=!0}}}},hooks:function(){return{bootstrap:function(){Me($a("mutationObserverCallbacks",{}))},noAuto:function(){Ht()},watch:function(n){var t=n.observeMutationsRoot;Ee?Ga():Me($a("mutationObserverCallbacks",{observeMutationsRoot:t}))}}}},Ie=function(e){var n={size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0};return e.toLowerCase().split(" ").reduce(function(t,r){var i=r.toLowerCase().split("-"),o=i[0],s=i.slice(1).join("-");if(o&&s==="h")return t.flipX=!0,t;if(o&&s==="v")return t.flipY=!0,t;if(s=parseFloat(s),isNaN(s))return t;switch(o){case"grow":t.size=t.size+s;break;case"shrink":t.size=t.size-s;break;case"left":t.x=t.x-s;break;case"right":t.x=t.x+s;break;case"up":t.y=t.y-s;break;case"down":t.y=t.y+s;break;case"rotate":t.rotate=t.rotate+s;break}return t},n)},Bt={mixout:function(){return{parse:{transform:function(n){return Ie(n)}}}},hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-transform");return r&&(n.transform=Ie(r)),n}}},provides:function(e){e.generateAbstractTransformGrouping=function(n){var t=n.main,r=n.transform,i=n.containerWidth,o=n.iconWidth,s={transform:"translate(".concat(i/2," 256)")},c="translate(".concat(r.x*32,", ").concat(r.y*32,") "),l="scale(".concat(r.size/16*(r.flipX?-1:1),", ").concat(r.size/16*(r.flipY?-1:1),") "),f="rotate(".concat(r.rotate," 0 0)"),v={transform:"".concat(c," ").concat(l," ").concat(f)},b={transform:"translate(".concat(o/2*-1," -256)")},g={outer:s,inner:v,path:b};return{tag:"g",attributes:u({},g.outer),children:[{tag:"g",attributes:u({},g.inner),children:[{tag:t.icon.tag,children:t.icon.children,attributes:u(u({},t.icon.attributes),g.path)}]}]}}}},_a={x:0,y:0,width:"100%",height:"100%"};function _e(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!0;return a.attributes&&(a.attributes.fill||e)&&(a.attributes.fill="black"),a}function Wt(a){return a.tag==="g"?a.children:[a]}var Gt={hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-mask"),i=r?Na(r.split(" ").map(function(o){return o.trim()})):oe();return i.prefix||(i.prefix=Y()),n.mask=i,n.maskId=t.getAttribute("data-fa-mask-id"),n}}},provides:function(e){e.generateAbstractMask=function(n){var t=n.children,r=n.attributes,i=n.main,o=n.mask,s=n.maskId,c=n.transform,l=i.width,f=i.icon,v=o.width,b=o.icon,g=Bn({transform:c,containerWidth:v,iconWidth:l}),A={tag:"rect",attributes:u(u({},_a),{},{fill:"white"})},H=f.children?{children:f.children.map(_e)}:{},S={tag:"g",attributes:u({},g.inner),children:[_e(u({tag:f.tag,attributes:u(u({},f.attributes),g.path)},H))]},d={tag:"g",attributes:u({},g.outer),children:[S]},p="mask-".concat(s||ca()),h="clip-".concat(s||ca()),w={tag:"mask",attributes:u(u({},_a),{},{id:p,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[A,d]},C={tag:"defs",children:[{tag:"clipPath",attributes:{id:h},children:Wt(b)},w]};return t.push(C,{tag:"rect",attributes:u({fill:"currentColor","clip-path":"url(#".concat(h,")"),mask:"url(#".concat(p,")")},_a)}),{children:t,attributes:r}}}},Xt={provides:function(e){var n=!1;$.matchMedia&&(n=$.matchMedia("(prefers-reduced-motion: reduce)").matches),e.missingIconAbstract=function(){var t=[],r={fill:"currentColor"},i={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};t.push({tag:"path",attributes:u(u({},r),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var o=u(u({},i),{},{attributeName:"opacity"}),s={tag:"circle",attributes:u(u({},r),{},{cx:"256",cy:"364",r:"28"}),children:[]};return n||s.children.push({tag:"animate",attributes:u(u({},i),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:u(u({},o),{},{values:"1;0;1;1;0;1;"})}),t.push(s),t.push({tag:"path",attributes:u(u({},r),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:n?[]:[{tag:"animate",attributes:u(u({},o),{},{values:"1;0;0;0;0;1;"})}]}),n||t.push({tag:"path",attributes:u(u({},r),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:u(u({},o),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:t}}}},qt={hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-symbol"),i=r===null?!1:r===""?!0:r;return n.symbol=i,n}}}},Kt=[Xn,It,_t,Tt,Ft,Yt,Ut,Bt,Gt,Xt,qt];ft(Kt,{mixoutsTo:O});O.noAuto;var dn=O.config,Nr=O.library;O.dom;var Ha=O.parse;O.findIconDefinition;O.toHtml;var Qt=O.icon;O.layer;var Zt=O.text;O.counter;var Jt={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm64 80v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm128 0v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H208c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H336zM64 400v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H208zm112 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H336c-8.8 0-16 7.2-16 16z"]},Lr=Jt,ar={prefix:"fas",iconName:"forward-step",icon:[320,512,["step-forward"],"f051","M52.5 440.6c-9.5 7.9-22.8 9.7-34.1 4.4S0 428.4 0 416V96C0 83.6 7.2 72.3 18.4 67s24.5-3.6 34.1 4.4l192 160L256 241V96c0-17.7 14.3-32 32-32s32 14.3 32 32V416c0 17.7-14.3 32-32 32s-32-14.3-32-32V271l-11.5 9.6-192 160z"]},Vr=ar,er={prefix:"fas",iconName:"box-archive",icon:[512,512,["archive"],"f187","M32 32H480c17.7 0 32 14.3 32 32V96c0 17.7-14.3 32-32 32H32C14.3 128 0 113.7 0 96V64C0 46.3 14.3 32 32 32zm0 128H480V416c0 35.3-28.7 64-64 64H96c-35.3 0-64-28.7-64-64V160zm128 80c0 8.8 7.2 16 16 16H336c8.8 0 16-7.2 16-16s-7.2-16-16-16H176c-8.8 0-16 7.2-16 16z"]},Pr=er,Er={prefix:"fas",iconName:"lock",icon:[448,512,[128274],"f023","M144 144v48H304V144c0-44.2-35.8-80-80-80s-80 35.8-80 80zM80 192V144C80 64.5 144.5 0 224 0s144 64.5 144 144v48h16c35.3 0 64 28.7 64 64V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V256c0-35.3 28.7-64 64-64H80z"]},Ir={prefix:"fas",iconName:"plug",icon:[384,512,[128268],"f1e6","M96 0C78.3 0 64 14.3 64 32v96h64V32c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32v96h64V32c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32v32c0 77.4 55 142 128 156.8V480c0 17.7 14.3 32 32 32s32-14.3 32-32V412.8C297 398 352 333.4 352 256V224c17.7 0 32-14.3 32-32s-14.3-32-32-32H32z"]},_r={prefix:"fas",iconName:"user",icon:[448,512,[128100,62144],"f007","M224 256c70.7 0 128-57.3 128-128S294.7 0 224 0S96 57.3 96 128s57.3 128 128 128zm-45.7 48C79.8 304 0 383.8 0 482.3C0 498.7 13.3 512 29.7 512H418.3c16.4 0 29.7-13.3 29.7-29.7C448 383.8 368.2 304 269.7 304H178.3z"]},Tr={prefix:"fas",iconName:"globe",icon:[512,512,[127760],"f0ac","M352 256c0 22.2-1.2 43.6-3.3 64H163.3c-2.2-20.4-3.3-41.8-3.3-64s1.2-43.6 3.3-64H348.7c2.2 20.4 3.3 41.8 3.3 64zm28.8-64H503.9c5.3 20.5 8.1 41.9 8.1 64s-2.8 43.5-8.1 64H380.8c2.1-20.6 3.2-42 3.2-64s-1.1-43.4-3.2-64zm112.6-32H376.7c-10-63.9-29.8-117.4-55.3-151.6c78.3 20.7 142 77.5 171.9 151.6zm-149.1 0H167.7c6.1-36.4 15.5-68.6 27-94.7c10.5-23.6 22.2-40.7 33.5-51.5C239.4 3.2 248.7 0 256 0s16.6 3.2 27.8 13.8c11.3 10.8 23 27.9 33.5 51.5c11.6 26 21 58.2 27 94.7zm-209 0H18.6C48.6 85.9 112.2 29.1 190.6 8.4C165.1 42.6 145.3 96.1 135.3 160zM8.1 192H131.2c-2.1 20.6-3.2 42-3.2 64s1.1 43.4 3.2 64H8.1C2.8 299.5 0 278.1 0 256s2.8-43.5 8.1-64zM194.7 446.6c-11.6-26-20.9-58.2-27-94.6H344.3c-6.1 36.4-15.5 68.6-27 94.6c-10.5 23.6-22.2 40.7-33.5 51.5C272.6 508.8 263.3 512 256 512s-16.6-3.2-27.8-13.8c-11.3-10.8-23-27.9-33.5-51.5zM135.3 352c10 63.9 29.8 117.4 55.3 151.6C112.2 482.9 48.6 426.1 18.6 352H135.3zm358.1 0c-30 74.1-93.6 130.9-171.9 151.6c25.5-34.2 45.2-87.7 55.3-151.6H493.4z"]},Fr={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M96 0C60.7 0 32 28.7 32 64V448c-17.7 0-32 14.3-32 32s14.3 32 32 32H320c17.7 0 32-14.3 32-32s-14.3-32-32-32V304h16c22.1 0 40 17.9 40 40v32c0 39.8 32.2 72 72 72s72-32.2 72-72V252.3c32.5-10.2 56-40.5 56-76.3V144c0-8.8-7.2-16-16-16H544V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H480V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H432c-8.8 0-16 7.2-16 16v32c0 35.8 23.5 66.1 56 76.3V376c0 13.3-10.7 24-24 24s-24-10.7-24-24V344c0-48.6-39.4-88-88-88H320V64c0-35.3-28.7-64-64-64H96zM216.9 82.7c6 4 8.5 11.5 6.3 18.3l-25 74.9H256c6.7 0 12.7 4.2 15 10.4s.5 13.3-4.6 17.7l-112 96c-5.5 4.7-13.4 5.1-19.3 1.1s-8.5-11.5-6.3-18.3l25-74.9H96c-6.7 0-12.7-4.2-15-10.4s-.5-13.3 4.6-17.7l112-96c5.5-4.7 13.4-5.1 19.3-1.1z"]},Rr={prefix:"fas",iconName:"microchip",icon:[512,512,[],"f2db","M176 24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64c-35.3 0-64 28.7-64 64H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64v56H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64v56H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64c0 35.3 28.7 64 64 64v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448h56v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448h56v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448c35.3 0 64-28.7 64-64h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448V280h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448V176h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448c0-35.3-28.7-64-64-64V24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H280V24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H176V24zM160 128H352c17.7 0 32 14.3 32 32V352c0 17.7-14.3 32-32 32H160c-17.7 0-32-14.3-32-32V160c0-17.7 14.3-32 32-32zm192 32H160V352H352V160z"]},Dr={prefix:"fas",iconName:"unlock",icon:[448,512,[128275],"f09c","M144 144c0-44.2 35.8-80 80-80c31.9 0 59.4 18.6 72.3 45.7c7.6 16 26.7 22.8 42.6 15.2s22.8-26.7 15.2-42.6C331 33.7 281.5 0 224 0C144.5 0 80 64.5 80 144v48H64c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V256c0-35.3-28.7-64-64-64H144V144z"]},jr={prefix:"fas",iconName:"clipboard",icon:[384,512,[128203],"f328","M192 0c-41.8 0-77.4 26.7-90.5 64H64C28.7 64 0 92.7 0 128V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H282.5C269.4 26.7 233.8 0 192 0zm0 64a32 32 0 1 1 0 64 32 32 0 1 1 0-64zM112 192H272c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16s7.2-16 16-16z"]},$r={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 96c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32h16c35.3 0 64 28.7 64 64V384c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V160c0-35.3 28.7-64 64-64l16 0zm304 96c0-8.8-7.2-16-16-16s-16 7.2-16 16v32H320c-8.8 0-16 7.2-16 16s7.2 16 16 16h32v32c0 8.8 7.2 16 16 16s16-7.2 16-16V256h32c8.8 0 16-7.2 16-16s-7.2-16-16-16H384V192zM80 240c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16s-7.2-16-16-16H96c-8.8 0-16 7.2-16 16z"]},nr={prefix:"fas",iconName:"circle-check",icon:[512,512,[61533,"check-circle"],"f058","M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0S0 114.6 0 256S114.6 512 256 512zM369 209L241 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L335 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"]},Yr=nr,Ur={prefix:"fas",iconName:"box-open",icon:[640,512,[],"f49e","M58.9 42.1c3-6.1 9.6-9.6 16.3-8.7L320 64 564.8 33.4c6.7-.8 13.3 2.7 16.3 8.7l41.7 83.4c9 17.9-.6 39.6-19.8 45.1L439.6 217.3c-13.9 4-28.8-1.9-36.2-14.3L320 64 236.6 203c-7.4 12.4-22.3 18.3-36.2 14.3L37.1 170.6c-19.3-5.5-28.8-27.2-19.8-45.1L58.9 42.1zM321.1 128l54.9 91.4c14.9 24.8 44.6 36.6 72.5 28.6L576 211.6v167c0 22-15 41.2-36.4 46.6l-204.1 51c-10.2 2.6-20.9 2.6-31 0l-204.1-51C79 419.7 64 400.5 64 378.5v-167L191.6 248c27.8 8 57.6-3.8 72.5-28.6L318.9 128h2.2z"]},tr={prefix:"fas",iconName:"file-zipper",icon:[384,512,["file-archive"],"f1c6","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0H64zM256 0V128H384L256 0zM96 48c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm-6.3 71.8c3.7-14 16.4-23.8 30.9-23.8h14.8c14.5 0 27.2 9.7 30.9 23.8l23.5 88.2c1.4 5.4 2.1 10.9 2.1 16.4c0 35.2-28.8 63.7-64 63.7s-64-28.5-64-63.7c0-5.5 .7-11.1 2.1-16.4l23.5-88.2zM112 336c-8.8 0-16 7.2-16 16s7.2 16 16 16h32c8.8 0 16-7.2 16-16s-7.2-16-16-16H112z"]},Br=tr,Wr={prefix:"fas",iconName:"filter",icon:[512,512,[],"f0b0","M3.9 54.9C10.5 40.9 24.5 32 40 32H472c15.5 0 29.5 8.9 36.1 22.9s4.6 30.5-5.2 42.5L320 320.9V448c0 12.1-6.8 23.2-17.7 28.6s-23.8 4.3-33.5-3l-64-48c-8.1-6-12.8-15.5-12.8-25.6V320.9L9 97.3C-.7 85.4-2.8 68.8 3.9 54.9z"]},rr={prefix:"fas",iconName:"up-down-left-right",icon:[512,512,["arrows-alt"],"f0b2","M278.6 9.4c-12.5-12.5-32.8-12.5-45.3 0l-64 64c-9.2 9.2-11.9 22.9-6.9 34.9s16.6 19.8 29.6 19.8h32v96H128V192c0-12.9-7.8-24.6-19.8-29.6s-25.7-2.2-34.9 6.9l-64 64c-12.5 12.5-12.5 32.8 0 45.3l64 64c9.2 9.2 22.9 11.9 34.9 6.9s19.8-16.6 19.8-29.6V288h96v96H192c-12.9 0-24.6 7.8-29.6 19.8s-2.2 25.7 6.9 34.9l64 64c12.5 12.5 32.8 12.5 45.3 0l64-64c9.2-9.2 11.9-22.9 6.9-34.9s-16.6-19.8-29.6-19.8H288V288h96v32c0 12.9 7.8 24.6 19.8 29.6s25.7 2.2 34.9-6.9l64-64c12.5-12.5 12.5-32.8 0-45.3l-64-64c-9.2-9.2-22.9-11.9-34.9-6.9s-19.8 16.6-19.8 29.6v32H288V128h32c12.9 0 24.6-7.8 29.6-19.8s2.2-25.7-6.9-34.9l-64-64z"]},Gr=rr,Xr={prefix:"fas",iconName:"code",icon:[640,512,[],"f121","M392.8 1.2c-17-4.9-34.7 5-39.6 22l-128 448c-4.9 17 5 34.7 22 39.6s34.7-5 39.6-22l128-448c4.9-17-5-34.7-22-39.6zm80.6 120.1c-12.5 12.5-12.5 32.8 0 45.3L562.7 256l-89.4 89.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l112-112c12.5-12.5 12.5-32.8 0-45.3l-112-112c-12.5-12.5-32.8-12.5-45.3 0zm-306.7 0c-12.5-12.5-32.8-12.5-45.3 0l-112 112c-12.5 12.5-12.5 32.8 0 45.3l112 112c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256l89.4-89.4c12.5-12.5 12.5-32.8 0-45.3z"]},qr={prefix:"fas",iconName:"solar-panel",icon:[640,512,[],"f5ba","M96 0C80.7 0 67.6 10.8 64.6 25.7l-64 320c-1.9 9.4 .6 19.1 6.6 26.6S22.4 384 32 384H288v64H224c-17.7 0-32 14.3-32 32s14.3 32 32 32H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H352V384H608c9.6 0 18.7-4.3 24.7-11.7s8.5-17.2 6.6-26.6l-64-320C572.4 10.8 559.3 0 544 0H96zm5.4 168L122.2 64h90.4L202.3 168H101.4zm-9.6 48H197.5L187.1 320H71L91.8 216zm153.9 0H394.3l10.4 104H235.3l10.4-104zm196.8 0H548.2L569 320h-116L442.5 216zm96-48H437.7L427.3 64h90.4l20.8 104zm-149.1 0h-139L260.9 64H379.1l10.4 104z"]},ir={prefix:"fas",iconName:"circle-up",icon:[512,512,[61467,"arrow-alt-circle-up"],"f35b","M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0S0 114.6 0 256S114.6 512 256 512zm11.3-395.3l112 112c4.6 4.6 5.9 11.5 3.5 17.4s-8.3 9.9-14.8 9.9H304v96c0 17.7-14.3 32-32 32H240c-17.7 0-32-14.3-32-32V256H144c-6.5 0-12.3-3.9-14.8-9.9s-1.1-12.9 3.5-17.4l112-112c6.2-6.2 16.4-6.2 22.6 0z"]},Kr=ir,Qr={prefix:"fas",iconName:"clipboard-check",icon:[384,512,[],"f46c","M192 0c-41.8 0-77.4 26.7-90.5 64H64C28.7 64 0 92.7 0 128V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H282.5C269.4 26.7 233.8 0 192 0zm0 64a32 32 0 1 1 0 64 32 32 0 1 1 0-64zM305 273L177 401c-9.4 9.4-24.6 9.4-33.9 0L79 337c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L271 239c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"]},or={prefix:"fas",iconName:"circle-question",icon:[512,512,[62108,"question-circle"],"f059","M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0S0 114.6 0 256S114.6 512 256 512zM169.8 165.3c7.9-22.3 29.1-37.3 52.8-37.3h58.3c34.9 0 63.1 28.3 63.1 63.1c0 22.6-12.1 43.5-31.7 54.8L280 264.4c-.2 13-10.9 23.6-24 23.6c-13.3 0-24-10.7-24-24V250.5c0-8.6 4.6-16.5 12.1-20.8l44.3-25.4c4.7-2.7 7.6-7.7 7.6-13.1c0-8.4-6.8-15.1-15.1-15.1H222.6c-3.4 0-6.4 2.1-7.5 5.3l-.4 1.2c-4.4 12.5-18.2 19-30.6 14.6s-19-18.2-14.6-30.6l.4-1.2zM288 352c0 17.7-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32s32 14.3 32 32z"]},Zr=or,Jr={prefix:"fas",iconName:"trash",icon:[448,512,[],"f1f8","M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z"]},sr={prefix:"fas",iconName:"up-right-from-square",icon:[512,512,["external-link-alt"],"f35d","M352 0c-12.9 0-24.6 7.8-29.6 19.8s-2.2 25.7 6.9 34.9L370.7 96 201.4 265.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L416 141.3l41.4 41.4c9.2 9.2 22.9 11.9 34.9 6.9s19.8-16.6 19.8-29.6V32c0-17.7-14.3-32-32-32H352zM80 32C35.8 32 0 67.8 0 112V432c0 44.2 35.8 80 80 80H400c44.2 0 80-35.8 80-80V320c0-17.7-14.3-32-32-32s-32 14.3-32 32V432c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V112c0-8.8 7.2-16 16-16H192c17.7 0 32-14.3 32-32s-14.3-32-32-32H80z"]},ai=sr,ei={prefix:"fas",iconName:"tag",icon:[448,512,[127991],"f02b","M0 80V229.5c0 17 6.7 33.3 18.7 45.3l176 176c25 25 65.5 25 90.5 0L418.7 317.3c25-25 25-65.5 0-90.5l-176-176c-12-12-28.3-18.7-45.3-18.7H48C21.5 32 0 53.5 0 80zm112 96c-17.7 0-32-14.3-32-32s14.3-32 32-32s32 14.3 32 32s-14.3 32-32 32z"]},ni={prefix:"fas",iconName:"envelope",icon:[512,512,[128386,9993,61443],"f0e0","M48 64C21.5 64 0 85.5 0 112c0 15.1 7.1 29.3 19.2 38.4L236.8 313.6c11.4 8.5 27 8.5 38.4 0L492.8 150.4c12.1-9.1 19.2-23.3 19.2-38.4c0-26.5-21.5-48-48-48H48zM0 176V384c0 35.3 28.7 64 64 64H448c35.3 0 64-28.7 64-64V176L294.4 339.2c-22.8 17.1-54 17.1-76.8 0L0 176z"]},cr={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0S0 114.6 0 256S114.6 512 256 512zM216 336h24V272H216c-13.3 0-24-10.7-24-24s10.7-24 24-24h48c13.3 0 24 10.7 24 24v88h8c13.3 0 24 10.7 24 24s-10.7 24-24 24H216c-13.3 0-24-10.7-24-24s10.7-24 24-24zm40-144c-17.7 0-32-14.3-32-32s14.3-32 32-32s32 14.3 32 32s-14.3 32-32 32z"]},ti=cr,fr={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M125.7 160H176c17.7 0 32 14.3 32 32s-14.3 32-32 32H48c-17.7 0-32-14.3-32-32V64c0-17.7 14.3-32 32-32s32 14.3 32 32v51.2L97.6 97.6c87.5-87.5 229.3-87.5 316.8 0s87.5 229.3 0 316.8s-229.3 87.5-316.8 0c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0c62.5 62.5 163.8 62.5 226.3 0s62.5-163.8 0-226.3s-163.8-62.5-226.3 0L125.7 160z"]},ri=fr,ii={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 512C114.6 512 0 397.4 0 256S114.6 0 256 0S512 114.6 512 256s-114.6 256-256 256zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},lr={prefix:"fas",iconName:"backward-step",icon:[320,512,["step-backward"],"f048","M267.5 440.6c9.5 7.9 22.8 9.7 34.1 4.4s18.4-16.6 18.4-29V96c0-12.4-7.2-23.7-18.4-29s-24.5-3.6-34.1 4.4l-192 160L64 241V96c0-17.7-14.3-32-32-32S0 78.3 0 96V416c0 17.7 14.3 32 32 32s32-14.3 32-32V271l11.5 9.6 192 160z"]},oi=lr,si={prefix:"fas",iconName:"keyboard",icon:[576,512,[9e3],"f11c","M64 64C28.7 64 0 92.7 0 128V384c0 35.3 28.7 64 64 64H512c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H64zm16 64h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM64 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V240zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V336c0-8.8 7.2-16 16-16zm80-176c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V144zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V240c0-8.8 7.2-16 16-16zM160 336c0-8.8 7.2-16 16-16H400c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V336zM272 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H272c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM256 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H272c-8.8 0-16-7.2-16-16V240zM368 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H368c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM352 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H368c-8.8 0-16-7.2-16-16V240zM464 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM448 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V240zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V336c0-8.8 7.2-16 16-16z"]},ci={prefix:"fas",iconName:"network-wired",icon:[640,512,[],"f6ff","M256 64H384v64H256V64zM240 0c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48h48v32H32c-17.7 0-32 14.3-32 32s14.3 32 32 32h96v32H80c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48H240c26.5 0 48-21.5 48-48V368c0-26.5-21.5-48-48-48H192V288H448v32H400c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48H560c26.5 0 48-21.5 48-48V368c0-26.5-21.5-48-48-48H512V288h96c17.7 0 32-14.3 32-32s-14.3-32-32-32H352V192h48c26.5 0 48-21.5 48-48V48c0-26.5-21.5-48-48-48H240zM96 448V384H224v64H96zm320-64H544v64H416V384z"]},fi={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32V256c0 17.7 14.3 32 32 32s32-14.3 32-32V32zM143.5 120.6c13.6-11.3 15.4-31.5 4.1-45.1s-31.5-15.4-45.1-4.1C49.7 115.4 16 181.8 16 256c0 132.5 107.5 240 240 240s240-107.5 240-240c0-74.2-33.8-140.6-86.6-184.6c-13.6-11.3-33.8-9.4-45.1 4.1s-9.4 33.8 4.1 45.1c38.9 32.3 63.5 81 63.5 135.4c0 97.2-78.8 176-176 176s-176-78.8-176-176c0-54.4 24.7-103.1 63.5-135.4z"]},li={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V64c0-35.3-28.7-64-64-64H64zM96 64H288c17.7 0 32 14.3 32 32v32c0 17.7-14.3 32-32 32H96c-17.7 0-32-14.3-32-32V96c0-17.7 14.3-32 32-32zM64 224c0-17.7 14.3-32 32-32s32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32zm32 64c17.7 0 32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32zM64 416c0-17.7 14.3-32 32-32h96c17.7 0 32 14.3 32 32s-14.3 32-32 32H96c-17.7 0-32-14.3-32-32zM192 192c17.7 0 32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32zM160 320c0-17.7 14.3-32 32-32s32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32zM288 192c17.7 0 32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32zM256 320c0-17.7 14.3-32 32-32s32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32zm32 64c17.7 0 32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32z"]},ui={prefix:"fas",iconName:"download",icon:[512,512,[],"f019","M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32V274.7l-73.4-73.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l128 128c12.5 12.5 32.8 12.5 45.3 0l128-128c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L288 274.7V32zM64 352c-35.3 0-64 28.7-64 64v32c0 35.3 28.7 64 64 64H448c35.3 0 64-28.7 64-64V416c0-35.3-28.7-64-64-64H346.5l-45.3 45.3c-25 25-65.5 25-90.5 0L165.5 352H64zM432 456c-13.3 0-24-10.7-24-24s10.7-24 24-24s24 10.7 24 24s-10.7 24-24 24z"]},mi={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v64c0 8.8 7.2 16 16 16H368c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},vi={prefix:"fas",iconName:"upload",icon:[512,512,[],"f093","M288 109.3V352c0 17.7-14.3 32-32 32s-32-14.3-32-32V109.3l-73.4 73.4c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3l128-128c12.5-12.5 32.8-12.5 45.3 0l128 128c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L288 109.3zM64 352H192c0 35.3 28.7 64 64 64s64-28.7 64-64H448c35.3 0 64 28.7 64 64v32c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V416c0-35.3 28.7-64 64-64zM432 456c13.3 0 24-10.7 24-24s-10.7-24-24-24s-24 10.7-24 24s10.7 24 24 24z"]},ur={prefix:"fas",iconName:"file-arrow-down",icon:[384,512,["file-download"],"f56d","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0H64zM256 0V128H384L256 0zM216 232V334.1l31-31c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-72 72c-9.4 9.4-24.6 9.4-33.9 0l-72-72c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l31 31V232c0-13.3 10.7-24 24-24s24 10.7 24 24z"]},di=ur,pi={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M349.4 44.6c5.9-13.7 1.5-29.7-10.6-38.5s-28.6-8-39.9 1.8l-256 224c-10 8.8-13.6 22.9-8.9 35.3S50.7 288 64 288H175.5L98.6 467.4c-5.9 13.7-1.5 29.7 10.6 38.5s28.6 8 39.9-1.8l256-224c10-8.8 13.6-22.9 8.9-35.3s-16.6-20.7-30-20.7H272.5L349.4 44.6z"]},bi={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4L109.1 192H402.9l-26.1-74.6C372.3 104.6 360.2 96 346.6 96H165.4c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32H346.6c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2V400v48c0 17.7-14.3 32-32 32H448c-17.7 0-32-14.3-32-32V400H96v48c0 17.7-14.3 32-32 32H32c-17.7 0-32-14.3-32-32V400 256c0-26.7 16.4-49.6 39.6-59.2zM128 288c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32zm288 32c17.7 0 32-14.3 32-32s-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32z"]},gi={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M512 256c0 141.4-114.6 256-256 256S0 397.4 0 256S114.6 0 256 0S512 114.6 512 256zM288 96c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32zM256 416c35.3 0 64-28.7 64-64c0-17.4-6.9-33.1-18.1-44.6L366 161.7c5.3-12.1-.2-26.3-12.3-31.6s-26.3 .2-31.6 12.3L257.9 288c-.6 0-1.3 0-1.9 0c-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32zM96 288c17.7 0 32-14.3 32-32s-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32zm352-32c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32z"]},hi={prefix:"fas",iconName:"chevron-down",icon:[512,512,[],"f078","M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"]},yi={prefix:"fas",iconName:"skull-crossbones",icon:[512,512,[128369,9760],"f714","M400 128c0 44.4-25.4 83.5-64 106.4V256c0 17.7-14.3 32-32 32H208c-17.7 0-32-14.3-32-32V234.4c-38.6-23-64-62.1-64-106.4C112 57.3 176.5 0 256 0s144 57.3 144 128zM200 176c17.7 0 32-14.3 32-32s-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32zm144-32c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32zM35.4 273.7c7.9-15.8 27.1-22.2 42.9-14.3L256 348.2l177.7-88.8c15.8-7.9 35-1.5 42.9 14.3s1.5 35-14.3 42.9L327.6 384l134.8 67.4c15.8 7.9 22.2 27.1 14.3 42.9s-27.1 22.2-42.9 14.3L256 419.8 78.3 508.6c-15.8 7.9-35 1.5-42.9-14.3s-1.5-35 14.3-42.9L184.4 384 49.7 316.6c-15.8-7.9-22.2-27.1-14.3-42.9z"]},xi={prefix:"fas",iconName:"plus",icon:[448,512,[10133,61543,"add"],"2b","M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32V224H48c-17.7 0-32 14.3-32 32s14.3 32 32 32H192V432c0 17.7 14.3 32 32 32s32-14.3 32-32V288H400c17.7 0 32-14.3 32-32s-14.3-32-32-32H256V80z"]},mr={prefix:"fas",iconName:"xmark",icon:[320,512,[128473,10005,10006,10060,215,"close","multiply","remove","times"],"f00d","M310.6 150.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L160 210.7 54.6 105.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L114.7 256 9.4 361.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 301.3 265.4 406.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L205.3 256 310.6 150.6z"]},ki=mr,wi={prefix:"fas",iconName:"chevron-right",icon:[384,512,[9002],"f054","M342.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-192 192c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3L274.7 256 105.4 86.6c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l192 192z"]},Ci={prefix:"fas",iconName:"check",icon:[512,512,[10003,10004],"f00c","M470.6 105.4c12.5 12.5 12.5 32.8 0 45.3l-256 256c-12.5 12.5-32.8 12.5-45.3 0l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L192 338.7 425.4 105.4c12.5-12.5 32.8-12.5 45.3 0z"]},vr={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 32c14.2 0 27.3 7.5 34.5 19.8l216 368c7.3 12.4 7.3 27.7 .2 40.1S486.3 480 472 480H40c-14.3 0-27.6-7.7-34.7-20.1s-7-27.8 .2-40.1l216-368C228.7 39.5 241.8 32 256 32zm0 128c-13.3 0-24 10.7-24 24V296c0 13.3 10.7 24 24 24s24-10.7 24-24V184c0-13.3-10.7-24-24-24zm32 224c0-17.7-14.3-32-32-32s-32 14.3-32 32s14.3 32 32 32s32-14.3 32-32z"]},zi=vr,Ai={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v96c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},dr={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0S0 114.6 0 256S114.6 512 256 512zM175 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},Hi=dr,Si={prefix:"far",iconName:"eye-slash",icon:[640,512,[],"f070","M150.7 92.77C195 58.27 251.8 32 320 32C400.8 32 465.5 68.84 512.6 112.6C559.4 156 590.7 207.1 605.5 243.7C608.8 251.6 608.8 260.4 605.5 268.3C592.1 300.6 565.2 346.1 525.6 386.7L630.8 469.1C641.2 477.3 643.1 492.4 634.9 502.8C626.7 513.2 611.6 515.1 601.2 506.9L9.196 42.89C-1.236 34.71-3.065 19.63 5.112 9.196C13.29-1.236 28.37-3.065 38.81 5.112L150.7 92.77zM189.8 123.5L235.8 159.5C258.3 139.9 287.8 128 320 128C390.7 128 448 185.3 448 256C448 277.2 442.9 297.1 433.8 314.7L487.6 356.9C521.1 322.8 545.9 283.1 558.6 256C544.1 225.1 518.4 183.5 479.9 147.7C438.8 109.6 385.2 79.1 320 79.1C269.5 79.1 225.1 97.73 189.8 123.5L189.8 123.5zM394.9 284.2C398.2 275.4 400 265.9 400 255.1C400 211.8 364.2 175.1 320 175.1C319.3 175.1 318.7 176 317.1 176C319.3 181.1 320 186.5 320 191.1C320 202.2 317.6 211.8 313.4 220.3L394.9 284.2zM404.3 414.5L446.2 447.5C409.9 467.1 367.8 480 320 480C239.2 480 174.5 443.2 127.4 399.4C80.62 355.1 49.34 304 34.46 268.3C31.18 260.4 31.18 251.6 34.46 243.7C44 220.8 60.29 191.2 83.09 161.5L120.8 191.2C102.1 214.5 89.76 237.6 81.45 255.1C95.02 286 121.6 328.5 160.1 364.3C201.2 402.4 254.8 432 320 432C350.7 432 378.8 425.4 404.3 414.5H404.3zM192 255.1C192 253.1 192.1 250.3 192.3 247.5L248.4 291.7C258.9 312.8 278.5 328.6 302 333.1L358.2 378.2C346.1 381.1 333.3 384 319.1 384C249.3 384 191.1 326.7 191.1 255.1H192z"]},pr={prefix:"far",iconName:"circle-question",icon:[512,512,[62108,"question-circle"],"f059","M256 0C114.6 0 0 114.6 0 256s114.6 256 256 256s256-114.6 256-256S397.4 0 256 0zM256 464c-114.7 0-208-93.31-208-208S141.3 48 256 48s208 93.31 208 208S370.7 464 256 464zM256 336c-18 0-32 14-32 32s13.1 32 32 32c17.1 0 32-14 32-32S273.1 336 256 336zM289.1 128h-51.1C199 128 168 159 168 198c0 13 11 24 24 24s24-11 24-24C216 186 225.1 176 237.1 176h51.1C301.1 176 312 186 312 198c0 8-4 14.1-11 18.1L244 251C236 256 232 264 232 272V288c0 13 11 24 24 24S280 301 280 288V286l45.1-28c21-13 34-36 34-60C360 159 329 128 289.1 128z"]},Mi=pr,Oi={prefix:"far",iconName:"eye",icon:[576,512,[128065],"f06e","M160 256C160 185.3 217.3 128 288 128C358.7 128 416 185.3 416 256C416 326.7 358.7 384 288 384C217.3 384 160 326.7 160 256zM288 336C332.2 336 368 300.2 368 256C368 211.8 332.2 176 288 176C287.3 176 286.7 176 285.1 176C287.3 181.1 288 186.5 288 192C288 227.3 259.3 256 224 256C218.5 256 213.1 255.3 208 253.1C208 254.7 208 255.3 208 255.1C208 300.2 243.8 336 288 336L288 336zM95.42 112.6C142.5 68.84 207.2 32 288 32C368.8 32 433.5 68.84 480.6 112.6C527.4 156 558.7 207.1 573.5 243.7C576.8 251.6 576.8 260.4 573.5 268.3C558.7 304 527.4 355.1 480.6 399.4C433.5 443.2 368.8 480 288 480C207.2 480 142.5 443.2 95.42 399.4C48.62 355.1 17.34 304 2.461 268.3C-.8205 260.4-.8205 251.6 2.461 243.7C17.34 207.1 48.62 156 95.42 112.6V112.6zM288 80C222.8 80 169.2 109.6 128.1 147.7C89.6 183.5 63.02 225.1 49.44 256C63.02 286 89.6 328.5 128.1 364.3C169.2 402.4 222.8 432 288 432C353.2 432 406.8 402.4 447.9 364.3C486.4 328.5 512.1 286 526.6 256C512.1 225.1 486.4 183.5 447.9 147.7C406.8 109.6 353.2 80 288 80V80z"]},Ni={prefix:"far",iconName:"file",icon:[384,512,[128196,128459,61462],"f15b","M0 64C0 28.65 28.65 0 64 0H229.5C246.5 0 262.7 6.743 274.7 18.75L365.3 109.3C377.3 121.3 384 137.5 384 154.5V448C384 483.3 355.3 512 320 512H64C28.65 512 0 483.3 0 448V64zM336 448V160H256C238.3 160 224 145.7 224 128V48H64C55.16 48 48 55.16 48 64V448C48 456.8 55.16 464 64 464H320C328.8 464 336 456.8 336 448z"]};function Te(a,e){var n=Object.keys(a);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(a);e&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),n.push.apply(n,t)}return n}function V(a){for(var e=1;e<arguments.length;e++){var n=arguments[e]!=null?arguments[e]:{};e%2?Te(Object(n),!0).forEach(function(t){M(a,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(n)):Te(Object(n)).forEach(function(t){Object.defineProperty(a,t,Object.getOwnPropertyDescriptor(n,t))})}return a}function Sa(a){return Sa=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},Sa(a)}function M(a,e,n){return e in a?Object.defineProperty(a,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):a[e]=n,a}function br(a,e){if(a==null)return{};var n={},t=Object.keys(a),r,i;for(i=0;i<t.length;i++)r=t[i],!(e.indexOf(r)>=0)&&(n[r]=a[r]);return n}function gr(a,e){if(a==null)return{};var n=br(a,e),t,r;if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(a);for(r=0;r<i.length;r++)t=i[r],!(e.indexOf(t)>=0)&&Object.prototype.propertyIsEnumerable.call(a,t)&&(n[t]=a[t])}return n}function Xa(a){return hr(a)||yr(a)||xr(a)||kr()}function hr(a){if(Array.isArray(a))return qa(a)}function yr(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function xr(a,e){if(a){if(typeof a=="string")return qa(a,e);var n=Object.prototype.toString.call(a).slice(8,-1);if(n==="Object"&&a.constructor&&(n=a.constructor.name),n==="Map"||n==="Set")return Array.from(a);if(n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return qa(a,e)}}function qa(a,e){(e==null||e>a.length)&&(e=a.length);for(var n=0,t=new Array(e);n<e;n++)t[n]=a[n];return t}function kr(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var wr=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof ue<"u"?ue:typeof self<"u"?self:{},pn={exports:{}};(function(a){(function(e){var n=function(d,p,h){if(!l(p)||v(p)||b(p)||g(p)||c(p))return p;var w,C=0,E=0;if(f(p))for(w=[],E=p.length;C<E;C++)w.push(n(d,p[C],h));else{w={};for(var N in p)Object.prototype.hasOwnProperty.call(p,N)&&(w[d(N,h)]=n(d,p[N],h))}return w},t=function(d,p){p=p||{};var h=p.separator||"_",w=p.split||/(?=[A-Z])/;return d.split(w).join(h)},r=function(d){return A(d)?d:(d=d.replace(/[\-_\s]+(.)?/g,function(p,h){return h?h.toUpperCase():""}),d.substr(0,1).toLowerCase()+d.substr(1))},i=function(d){var p=r(d);return p.substr(0,1).toUpperCase()+p.substr(1)},o=function(d,p){return t(d,p).toLowerCase()},s=Object.prototype.toString,c=function(d){return typeof d=="function"},l=function(d){return d===Object(d)},f=function(d){return s.call(d)=="[object Array]"},v=function(d){return s.call(d)=="[object Date]"},b=function(d){return s.call(d)=="[object RegExp]"},g=function(d){return s.call(d)=="[object Boolean]"},A=function(d){return d=d-0,d===d},H=function(d,p){var h=p&&"process"in p?p.process:p;return typeof h!="function"?d:function(w,C){return h(w,d,C)}},S={camelize:r,decamelize:o,pascalize:i,depascalize:o,camelizeKeys:function(d,p){return n(H(r,p),d)},decamelizeKeys:function(d,p){return n(H(o,p),d,p)},pascalizeKeys:function(d,p){return n(H(i,p),d)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}};a.exports?a.exports=S:e.humps=S})(wr)})(pn);var Cr=pn.exports,zr=["class","style"];function Ar(a){return a.split(";").map(function(e){return e.trim()}).filter(function(e){return e}).reduce(function(e,n){var t=n.indexOf(":"),r=Cr.camelize(n.slice(0,t)),i=n.slice(t+1).trim();return e[r]=i,e},{})}function Hr(a){return a.split(/\s+/).reduce(function(e,n){return e[n]=!0,e},{})}function le(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof a=="string")return a;var t=(a.children||[]).map(function(c){return le(c)}),r=Object.keys(a.attributes||{}).reduce(function(c,l){var f=a.attributes[l];switch(l){case"class":c.class=Hr(f);break;case"style":c.style=Ar(f);break;default:c.attrs[l]=f}return c},{attrs:{},class:{},style:{}});n.class;var i=n.style,o=i===void 0?{}:i,s=gr(n,zr);return Re(a.tag,V(V(V({},e),{},{class:r.class,style:V(V({},r.style),o)},r.attrs),s),t)}var bn=!1;try{bn=!1}catch{}function Sr(){if(!bn&&console&&typeof console.error=="function"){var a;(a=console).error.apply(a,arguments)}}function ta(a,e){return Array.isArray(e)&&e.length>0||!Array.isArray(e)&&e?M({},a,e):{}}function Mr(a){var e,n=(e={"fa-spin":a.spin,"fa-pulse":a.pulse,"fa-fw":a.fixedWidth,"fa-border":a.border,"fa-li":a.listItem,"fa-inverse":a.inverse,"fa-flip":a.flip===!0,"fa-flip-horizontal":a.flip==="horizontal"||a.flip==="both","fa-flip-vertical":a.flip==="vertical"||a.flip==="both"},M(e,"fa-".concat(a.size),a.size!==null),M(e,"fa-rotate-".concat(a.rotation),a.rotation!==null),M(e,"fa-pull-".concat(a.pull),a.pull!==null),M(e,"fa-swap-opacity",a.swapOpacity),M(e,"fa-bounce",a.bounce),M(e,"fa-shake",a.shake),M(e,"fa-beat",a.beat),M(e,"fa-fade",a.fade),M(e,"fa-beat-fade",a.beatFade),M(e,"fa-flash",a.flash),M(e,"fa-spin-pulse",a.spinPulse),M(e,"fa-spin-reverse",a.spinReverse),e);return Object.keys(n).map(function(t){return n[t]?t:null}).filter(function(t){return t})}function Fe(a){if(a&&Sa(a)==="object"&&a.prefix&&a.iconName&&a.icon)return a;if(Ha.icon)return Ha.icon(a);if(a===null)return null;if(Sa(a)==="object"&&a.prefix&&a.iconName)return a;if(Array.isArray(a)&&a.length===2)return{prefix:a[0],iconName:a[1]};if(typeof a=="string")return{prefix:"fas",iconName:a}}var Li=Ka({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(e){return[!0,!1,"horizontal","vertical","both"].indexOf(e)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(e){return["right","left"].indexOf(e)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(e){return[90,180,270].indexOf(Number.parseInt(e,10))>-1}},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(e){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(e)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1}},setup:function(e,n){var t=n.attrs,r=L(function(){return Fe(e.icon)}),i=L(function(){return ta("classes",Mr(e))}),o=L(function(){return ta("transform",typeof e.transform=="string"?Ha.transform(e.transform):e.transform)}),s=L(function(){return ta("mask",Fe(e.mask))}),c=L(function(){return Qt(r.value,V(V(V(V({},i.value),o.value),s.value),{},{symbol:e.symbol,title:e.title}))});hn(c,function(f){if(!f)return Sr("Could not find one or more icon(s)",r.value,s.value)},{immediate:!0});var l=L(function(){return c.value?le(c.value.abstract[0],{},t):null});return function(){return l.value}}}),Vi=Ka({name:"FontAwesomeLayers",props:{fixedWidth:{type:Boolean,default:!1}},setup:function(e,n){var t=n.slots,r=dn.familyPrefix,i=L(function(){return["".concat(r,"-layers")].concat(Xa(e.fixedWidth?["".concat(r,"-fw")]:[]))});return function(){return Re("div",{class:i.value},t.default?t.default():[])}}});Ka({name:"FontAwesomeLayersText",props:{value:{type:[String,Number],default:""},transform:{type:[String,Object],default:null},counter:{type:Boolean,default:!1},position:{type:String,default:null,validator:function(e){return["bottom-left","bottom-right","top-left","top-right"].indexOf(e)>-1}}},setup:function(e,n){var t=n.attrs,r=dn.familyPrefix,i=L(function(){return ta("classes",[].concat(Xa(e.counter?["".concat(r,"-layers-counter")]:[]),Xa(e.position?["".concat(r,"-layers-").concat(e.position)]:[])))}),o=L(function(){return ta("transform",typeof e.transform=="string"?Ha.transform(e.transform):e.transform)}),s=L(function(){var l=Zt(e.value.toString(),V(V({},o.value),i.value)),f=l.abstract;return e.counter&&(f[0].attributes.class=f[0].attributes.class.replace("fa-layers-text","")),f[0]}),c=L(function(){return le(s.value,{},t)});return function(){return c.value}}});var Pi={prefix:"fab",iconName:"paypal",icon:[384,512,[],"f1ed","M111.4 295.9c-3.5 19.2-17.4 108.7-21.5 134-.3 1.8-1 2.5-3 2.5H12.3c-7.6 0-13.1-6.6-12.1-13.9L58.8 46.6c1.5-9.6 10.1-16.9 20-16.9 152.3 0 165.1-3.7 204 11.4 60.1 23.3 65.6 79.5 44 140.3-21.5 62.6-72.5 89.5-140.1 90.3-43.4.7-69.5-7-75.3 24.2zM357.1 152c-1.8-1.3-2.5-1.8-3 1.3-2 11.4-5.1 22.5-8.8 33.6-39.9 113.8-150.5 103.9-204.5 103.9-6.1 0-10.1 3.3-10.9 9.4-22.6 140.4-27.1 169.7-27.1 169.7-1 7.1 3.5 12.9 10.6 12.9h63.5c8.6 0 15.7-6.3 17.4-14.9.7-5.4-1.1 6.1 14.4-91.3 4.6-22 14.3-19.7 29.3-19.7 71 0 126.4-28.8 142.9-112.3 6.5-34.8 4.6-71.4-23.8-92.6z"]};export{yi as $,Ai as A,Oi as B,Si as C,ai as D,Pi as E,Li as F,Yr as G,zi as H,bi as I,Fr as J,$r as K,qr as L,gi as M,Wr as N,ui as O,Rr as P,Jr as Q,Gr as R,Lr as S,mi as T,Ni as U,Vi as V,pi as W,Ir as X,di as Y,Kr as Z,fi as _,Mi as a,Pr as a0,Br as a1,vi as a2,Ur as a3,ei as b,Hi as c,xi as d,ti as e,Zr as f,Ci as g,wi as h,hi as i,jr as j,Qr as k,Nr as l,li as m,Vr as n,oi as o,ri as p,ki as q,si as r,ni as s,ci as t,Tr as u,_r as v,Xr as w,Er as x,Dr as y,ii as z};
