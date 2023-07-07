import{g as fn,d as dt,c as G,w as vt,h as pt}from"./vendor-e07709f3.js";function cn(a,n){var t=Object.keys(a);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(a);n&&(e=e.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),t.push.apply(t,e)}return t}function u(a){for(var n=1;n<arguments.length;n++){var t=arguments[n]!=null?arguments[n]:{};n%2?cn(Object(t),!0).forEach(function(e){O(a,e,t[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(t)):cn(Object(t)).forEach(function(e){Object.defineProperty(a,e,Object.getOwnPropertyDescriptor(t,e))})}return a}function wa(a){"@babel/helpers - typeof";return wa=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(n){return typeof n}:function(n){return n&&typeof Symbol=="function"&&n.constructor===Symbol&&n!==Symbol.prototype?"symbol":typeof n},wa(a)}function gt(a,n){if(!(a instanceof n))throw new TypeError("Cannot call a class as a function")}function ln(a,n){for(var t=0;t<n.length;t++){var e=n[t];e.enumerable=e.enumerable||!1,e.configurable=!0,"value"in e&&(e.writable=!0),Object.defineProperty(a,e.key,e)}}function bt(a,n,t){return n&&ln(a.prototype,n),t&&ln(a,t),Object.defineProperty(a,"prototype",{writable:!1}),a}function O(a,n,t){return n in a?Object.defineProperty(a,n,{value:t,enumerable:!0,configurable:!0,writable:!0}):a[n]=t,a}function Ga(a,n){return yt(a)||kt(a,n)||Hn(a,n)||At()}function fa(a){return ht(a)||xt(a)||Hn(a)||wt()}function ht(a){if(Array.isArray(a))return Ha(a)}function yt(a){if(Array.isArray(a))return a}function xt(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function kt(a,n){var t=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(t!=null){var e=[],r=!0,i=!1,o,s;try{for(t=t.call(a);!(r=(o=t.next()).done)&&(e.push(o.value),!(n&&e.length===n));r=!0);}catch(f){i=!0,s=f}finally{try{!r&&t.return!=null&&t.return()}finally{if(i)throw s}}return e}}function Hn(a,n){if(a){if(typeof a=="string")return Ha(a,n);var t=Object.prototype.toString.call(a).slice(8,-1);if(t==="Object"&&a.constructor&&(t=a.constructor.name),t==="Map"||t==="Set")return Array.from(a);if(t==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t))return Ha(a,n)}}function Ha(a,n){(n==null||n>a.length)&&(n=a.length);for(var t=0,e=new Array(n);t<n;t++)e[t]=a[t];return e}function wt(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function At(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var un=function(){},Ka={},Vn={},Rn=null,Fn={mark:un,measure:un};try{typeof window<"u"&&(Ka=window),typeof document<"u"&&(Vn=document),typeof MutationObserver<"u"&&(Rn=MutationObserver),typeof performance<"u"&&(Fn=performance)}catch{}var Ot=Ka.navigator||{},mn=Ot.userAgent,dn=mn===void 0?"":mn,j=Ka,x=Vn,vn=Rn,ua=Fn;j.document;var R=!!x.documentElement&&!!x.head&&typeof x.addEventListener=="function"&&typeof x.createElement=="function",Dn=~dn.indexOf("MSIE")||~dn.indexOf("Trident/"),ma,da,va,pa,ga,T="___FONT_AWESOME___",Va=16,jn="fa",Yn="svg-inline--fa",W="data-fa-i2svg",Ra="data-fa-pseudo-element",St="data-fa-pseudo-element-pending",qa="data-prefix",Qa="data-icon",pn="fontawesome-i2svg",Ct="async",zt=["HTML","HEAD","STYLE","SCRIPT"],$n=function(){try{return!1}catch{return!1}}(),y="classic",k="sharp",Za=[y,k];function ca(a){return new Proxy(a,{get:function(t,e){return e in t?t[e]:t[y]}})}var ea=ca((ma={},O(ma,y,{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fad:"duotone","fa-duotone":"duotone",fab:"brands","fa-brands":"brands",fak:"kit","fa-kit":"kit"}),O(ma,k,{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light"}),ma)),ra=ca((da={},O(da,y,{solid:"fas",regular:"far",light:"fal",thin:"fat",duotone:"fad",brands:"fab",kit:"fak"}),O(da,k,{solid:"fass",regular:"fasr",light:"fasl"}),da)),ia=ca((va={},O(va,y,{fab:"fa-brands",fad:"fa-duotone",fak:"fa-kit",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"}),O(va,k,{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light"}),va)),Pt=ca((pa={},O(pa,y,{"fa-brands":"fab","fa-duotone":"fad","fa-kit":"fak","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"}),O(pa,k,{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl"}),pa)),Nt=/fa(s|r|l|t|d|b|k|ss|sr|sl)?[\-\ ]/,Un="fa-layers-text",Et=/Font ?Awesome ?([56 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp|Kit)?.*/i,Mt=ca((ga={},O(ga,y,{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"}),O(ga,k,{900:"fass",400:"fasr",300:"fasl"}),ga)),Bn=[1,2,3,4,5,6,7,8,9,10],Lt=Bn.concat([11,12,13,14,15,16,17,18,19,20]),It=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],U={GROUP:"duotone-group",SWAP_OPACITY:"swap-opacity",PRIMARY:"primary",SECONDARY:"secondary"},oa=new Set;Object.keys(ra[y]).map(oa.add.bind(oa));Object.keys(ra[k]).map(oa.add.bind(oa));var _t=[].concat(Za,fa(oa),["2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","fw","inverse","layers-counter","layers-text","layers","li","pull-left","pull-right","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul",U.GROUP,U.SWAP_OPACITY,U.PRIMARY,U.SECONDARY]).concat(Bn.map(function(a){return"".concat(a,"x")})).concat(Lt.map(function(a){return"w-".concat(a)})),na=j.FontAwesomeConfig||{};function Tt(a){var n=x.querySelector("script["+a+"]");if(n)return n.getAttribute(a)}function Ht(a){return a===""?!0:a==="false"?!1:a==="true"?!0:a}if(x&&typeof x.querySelector=="function"){var Vt=[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-auto-a11y","autoA11y"],["data-search-pseudo-elements","searchPseudoElements"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]];Vt.forEach(function(a){var n=Ga(a,2),t=n[0],e=n[1],r=Ht(Tt(t));r!=null&&(na[e]=r)})}var Wn={styleDefault:"solid",familyDefault:"classic",cssPrefix:jn,replacementClass:Yn,autoReplaceSvg:!0,autoAddCss:!0,autoA11y:!0,searchPseudoElements:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};na.familyPrefix&&(na.cssPrefix=na.familyPrefix);var Z=u(u({},Wn),na);Z.autoReplaceSvg||(Z.observeMutations=!1);var m={};Object.keys(Wn).forEach(function(a){Object.defineProperty(m,a,{enumerable:!0,set:function(t){Z[a]=t,ta.forEach(function(e){return e(m)})},get:function(){return Z[a]}})});Object.defineProperty(m,"familyPrefix",{enumerable:!0,set:function(n){Z.cssPrefix=n,ta.forEach(function(t){return t(m)})},get:function(){return Z.cssPrefix}});j.FontAwesomeConfig=m;var ta=[];function Rt(a){return ta.push(a),function(){ta.splice(ta.indexOf(a),1)}}var D=Va,I={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function Ft(a){if(!(!a||!R)){var n=x.createElement("style");n.setAttribute("type","text/css"),n.innerHTML=a;for(var t=x.head.childNodes,e=null,r=t.length-1;r>-1;r--){var i=t[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(e=i)}return x.head.insertBefore(n,e),a}}var Dt="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";function sa(){for(var a=12,n="";a-- >0;)n+=Dt[Math.random()*62|0];return n}function J(a){for(var n=[],t=(a||[]).length>>>0;t--;)n[t]=a[t];return n}function Ja(a){return a.classList?J(a.classList):(a.getAttribute("class")||"").split(" ").filter(function(n){return n})}function Xn(a){return"".concat(a).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function jt(a){return Object.keys(a||{}).reduce(function(n,t){return n+"".concat(t,'="').concat(Xn(a[t]),'" ')},"").trim()}function Ca(a){return Object.keys(a||{}).reduce(function(n,t){return n+"".concat(t,": ").concat(a[t].trim(),";")},"")}function an(a){return a.size!==I.size||a.x!==I.x||a.y!==I.y||a.rotate!==I.rotate||a.flipX||a.flipY}function Yt(a){var n=a.transform,t=a.containerWidth,e=a.iconWidth,r={transform:"translate(".concat(t/2," 256)")},i="translate(".concat(n.x*32,", ").concat(n.y*32,") "),o="scale(".concat(n.size/16*(n.flipX?-1:1),", ").concat(n.size/16*(n.flipY?-1:1),") "),s="rotate(".concat(n.rotate," 0 0)"),f={transform:"".concat(i," ").concat(o," ").concat(s)},l={transform:"translate(".concat(e/2*-1," -256)")};return{outer:r,inner:f,path:l}}function $t(a){var n=a.transform,t=a.width,e=t===void 0?Va:t,r=a.height,i=r===void 0?Va:r,o=a.startCentered,s=o===void 0?!1:o,f="";return s&&Dn?f+="translate(".concat(n.x/D-e/2,"em, ").concat(n.y/D-i/2,"em) "):s?f+="translate(calc(-50% + ".concat(n.x/D,"em), calc(-50% + ").concat(n.y/D,"em)) "):f+="translate(".concat(n.x/D,"em, ").concat(n.y/D,"em) "),f+="scale(".concat(n.size/D*(n.flipX?-1:1),", ").concat(n.size/D*(n.flipY?-1:1),") "),f+="rotate(".concat(n.rotate,"deg) "),f}var Ut=`:root, :host {
  --fa-font-solid: normal 900 1em/1 "Font Awesome 6 Solid";
  --fa-font-regular: normal 400 1em/1 "Font Awesome 6 Regular";
  --fa-font-light: normal 300 1em/1 "Font Awesome 6 Light";
  --fa-font-thin: normal 100 1em/1 "Font Awesome 6 Thin";
  --fa-font-duotone: normal 900 1em/1 "Font Awesome 6 Duotone";
  --fa-font-sharp-solid: normal 900 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-regular: normal 400 1em/1 "Font Awesome 6 Sharp";
  --fa-font-sharp-light: normal 300 1em/1 "Font Awesome 6 Sharp";
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
    -webkit-transition-delay: 0s;
            transition-delay: 0s;
    -webkit-transition-duration: 0s;
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
}`;function Gn(){var a=jn,n=Yn,t=m.cssPrefix,e=m.replacementClass,r=Ut;if(t!==a||e!==n){var i=new RegExp("\\.".concat(a,"\\-"),"g"),o=new RegExp("\\--".concat(a,"\\-"),"g"),s=new RegExp("\\.".concat(n),"g");r=r.replace(i,".".concat(t,"-")).replace(o,"--".concat(t,"-")).replace(s,".".concat(e))}return r}var gn=!1;function Ma(){m.autoAddCss&&!gn&&(Ft(Gn()),gn=!0)}var Bt={mixout:function(){return{dom:{css:Gn,insertCss:Ma}}},hooks:function(){return{beforeDOMElementCreation:function(){Ma()},beforeI2svg:function(){Ma()}}}},H=j||{};H[T]||(H[T]={});H[T].styles||(H[T].styles={});H[T].hooks||(H[T].hooks={});H[T].shims||(H[T].shims=[]);var M=H[T],Kn=[],Wt=function a(){x.removeEventListener("DOMContentLoaded",a),Aa=1,Kn.map(function(n){return n()})},Aa=!1;R&&(Aa=(x.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(x.readyState),Aa||x.addEventListener("DOMContentLoaded",Wt));function Xt(a){R&&(Aa?setTimeout(a,0):Kn.push(a))}function la(a){var n=a.tag,t=a.attributes,e=t===void 0?{}:t,r=a.children,i=r===void 0?[]:r;return typeof a=="string"?Xn(a):"<".concat(n," ").concat(jt(e),">").concat(i.map(la).join(""),"</").concat(n,">")}function bn(a,n,t){if(a&&a[n]&&a[n][t])return{prefix:n,iconName:t,icon:a[n][t]}}var Gt=function(n,t){return function(e,r,i,o){return n.call(t,e,r,i,o)}},La=function(n,t,e,r){var i=Object.keys(n),o=i.length,s=r!==void 0?Gt(t,r):t,f,l,c;for(e===void 0?(f=1,c=n[i[0]]):(f=0,c=e);f<o;f++)l=i[f],c=s(c,n[l],l,n);return c};function Kt(a){for(var n=[],t=0,e=a.length;t<e;){var r=a.charCodeAt(t++);if(r>=55296&&r<=56319&&t<e){var i=a.charCodeAt(t++);(i&64512)==56320?n.push(((r&1023)<<10)+(i&1023)+65536):(n.push(r),t--)}else n.push(r)}return n}function Fa(a){var n=Kt(a);return n.length===1?n[0].toString(16):null}function qt(a,n){var t=a.length,e=a.charCodeAt(n),r;return e>=55296&&e<=56319&&t>n+1&&(r=a.charCodeAt(n+1),r>=56320&&r<=57343)?(e-55296)*1024+r-56320+65536:e}function hn(a){return Object.keys(a).reduce(function(n,t){var e=a[t],r=!!e.icon;return r?n[e.iconName]=e.icon:n[t]=e,n},{})}function Da(a,n){var t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{},e=t.skipHooks,r=e===void 0?!1:e,i=hn(n);typeof M.hooks.addPack=="function"&&!r?M.hooks.addPack(a,hn(n)):M.styles[a]=u(u({},M.styles[a]||{}),i),a==="fas"&&Da("fa",n)}var ba,ha,ya,K=M.styles,Qt=M.shims,Zt=(ba={},O(ba,y,Object.values(ia[y])),O(ba,k,Object.values(ia[k])),ba),nn=null,qn={},Qn={},Zn={},Jn={},at={},Jt=(ha={},O(ha,y,Object.keys(ea[y])),O(ha,k,Object.keys(ea[k])),ha);function ae(a){return~_t.indexOf(a)}function ne(a,n){var t=n.split("-"),e=t[0],r=t.slice(1).join("-");return e===a&&r!==""&&!ae(r)?r:null}var nt=function(){var n=function(i){return La(K,function(o,s,f){return o[f]=La(s,i,{}),o},{})};qn=n(function(r,i,o){if(i[3]&&(r[i[3]]=o),i[2]){var s=i[2].filter(function(f){return typeof f=="number"});s.forEach(function(f){r[f.toString(16)]=o})}return r}),Qn=n(function(r,i,o){if(r[o]=o,i[2]){var s=i[2].filter(function(f){return typeof f=="string"});s.forEach(function(f){r[f]=o})}return r}),at=n(function(r,i,o){var s=i[2];return r[o]=o,s.forEach(function(f){r[f]=o}),r});var t="far"in K||m.autoFetchSvg,e=La(Qt,function(r,i){var o=i[0],s=i[1],f=i[2];return s==="far"&&!t&&(s="fas"),typeof o=="string"&&(r.names[o]={prefix:s,iconName:f}),typeof o=="number"&&(r.unicodes[o.toString(16)]={prefix:s,iconName:f}),r},{names:{},unicodes:{}});Zn=e.names,Jn=e.unicodes,nn=za(m.styleDefault,{family:m.familyDefault})};Rt(function(a){nn=za(a.styleDefault,{family:m.familyDefault})});nt();function tn(a,n){return(qn[a]||{})[n]}function te(a,n){return(Qn[a]||{})[n]}function B(a,n){return(at[a]||{})[n]}function tt(a){return Zn[a]||{prefix:null,iconName:null}}function ee(a){var n=Jn[a],t=tn("fas",a);return n||(t?{prefix:"fas",iconName:t}:null)||{prefix:null,iconName:null}}function Y(){return nn}var en=function(){return{prefix:null,iconName:null,rest:[]}};function za(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.family,e=t===void 0?y:t,r=ea[e][a],i=ra[e][a]||ra[e][r],o=a in M.styles?a:null;return i||o||null}var yn=(ya={},O(ya,y,Object.keys(ia[y])),O(ya,k,Object.keys(ia[k])),ya);function Pa(a){var n,t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},e=t.skipLookups,r=e===void 0?!1:e,i=(n={},O(n,y,"".concat(m.cssPrefix,"-").concat(y)),O(n,k,"".concat(m.cssPrefix,"-").concat(k)),n),o=null,s=y;(a.includes(i[y])||a.some(function(l){return yn[y].includes(l)}))&&(s=y),(a.includes(i[k])||a.some(function(l){return yn[k].includes(l)}))&&(s=k);var f=a.reduce(function(l,c){var d=ne(m.cssPrefix,c);if(K[c]?(c=Zt[s].includes(c)?Pt[s][c]:c,o=c,l.prefix=c):Jt[s].indexOf(c)>-1?(o=c,l.prefix=za(c,{family:s})):d?l.iconName=d:c!==m.replacementClass&&c!==i[y]&&c!==i[k]&&l.rest.push(c),!r&&l.prefix&&l.iconName){var g=o==="fa"?tt(l.iconName):{},b=B(l.prefix,l.iconName);g.prefix&&(o=null),l.iconName=g.iconName||b||l.iconName,l.prefix=g.prefix||l.prefix,l.prefix==="far"&&!K.far&&K.fas&&!m.autoFetchSvg&&(l.prefix="fas")}return l},en());return(a.includes("fa-brands")||a.includes("fab"))&&(f.prefix="fab"),(a.includes("fa-duotone")||a.includes("fad"))&&(f.prefix="fad"),!f.prefix&&s===k&&(K.fass||m.autoFetchSvg)&&(f.prefix="fass",f.iconName=B(f.prefix,f.iconName)||f.iconName),(f.prefix==="fa"||o==="fa")&&(f.prefix=Y()||"fas"),f}var re=function(){function a(){gt(this,a),this.definitions={}}return bt(a,[{key:"add",value:function(){for(var t=this,e=arguments.length,r=new Array(e),i=0;i<e;i++)r[i]=arguments[i];var o=r.reduce(this._pullDefinitions,{});Object.keys(o).forEach(function(s){t.definitions[s]=u(u({},t.definitions[s]||{}),o[s]),Da(s,o[s]);var f=ia[y][s];f&&Da(f,o[s]),nt()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(t,e){var r=e.prefix&&e.iconName&&e.icon?{0:e}:e;return Object.keys(r).map(function(i){var o=r[i],s=o.prefix,f=o.iconName,l=o.icon,c=l[2];t[s]||(t[s]={}),c.length>0&&c.forEach(function(d){typeof d=="string"&&(t[s][d]=l)}),t[s][f]=l}),t}}]),a}(),xn=[],q={},Q={},ie=Object.keys(Q);function oe(a,n){var t=n.mixoutsTo;return xn=a,q={},Object.keys(Q).forEach(function(e){ie.indexOf(e)===-1&&delete Q[e]}),xn.forEach(function(e){var r=e.mixout?e.mixout():{};if(Object.keys(r).forEach(function(o){typeof r[o]=="function"&&(t[o]=r[o]),wa(r[o])==="object"&&Object.keys(r[o]).forEach(function(s){t[o]||(t[o]={}),t[o][s]=r[o][s]})}),e.hooks){var i=e.hooks();Object.keys(i).forEach(function(o){q[o]||(q[o]=[]),q[o].push(i[o])})}e.provides&&e.provides(Q)}),t}function ja(a,n){for(var t=arguments.length,e=new Array(t>2?t-2:0),r=2;r<t;r++)e[r-2]=arguments[r];var i=q[a]||[];return i.forEach(function(o){n=o.apply(null,[n].concat(e))}),n}function X(a){for(var n=arguments.length,t=new Array(n>1?n-1:0),e=1;e<n;e++)t[e-1]=arguments[e];var r=q[a]||[];r.forEach(function(i){i.apply(null,t)})}function V(){var a=arguments[0],n=Array.prototype.slice.call(arguments,1);return Q[a]?Q[a].apply(null,n):void 0}function Ya(a){a.prefix==="fa"&&(a.prefix="fas");var n=a.iconName,t=a.prefix||Y();if(n)return n=B(t,n)||n,bn(et.definitions,t,n)||bn(M.styles,t,n)}var et=new re,se=function(){m.autoReplaceSvg=!1,m.observeMutations=!1,X("noAuto")},fe={i2svg:function(){var n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return R?(X("beforeI2svg",n),V("pseudoElements2svg",n),V("i2svg",n)):Promise.reject("Operation requires a DOM of some kind.")},watch:function(){var n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},t=n.autoReplaceSvgRoot;m.autoReplaceSvg===!1&&(m.autoReplaceSvg=!0),m.observeMutations=!0,Xt(function(){le({autoReplaceSvgRoot:t}),X("watch",n)})}},ce={icon:function(n){if(n===null)return null;if(wa(n)==="object"&&n.prefix&&n.iconName)return{prefix:n.prefix,iconName:B(n.prefix,n.iconName)||n.iconName};if(Array.isArray(n)&&n.length===2){var t=n[1].indexOf("fa-")===0?n[1].slice(3):n[1],e=za(n[0]);return{prefix:e,iconName:B(e,t)||t}}if(typeof n=="string"&&(n.indexOf("".concat(m.cssPrefix,"-"))>-1||n.match(Nt))){var r=Pa(n.split(" "),{skipLookups:!0});return{prefix:r.prefix||Y(),iconName:B(r.prefix,r.iconName)||r.iconName}}if(typeof n=="string"){var i=Y();return{prefix:i,iconName:B(i,n)||n}}}},N={noAuto:se,config:m,dom:fe,parse:ce,library:et,findIconDefinition:Ya,toHtml:la},le=function(){var n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},t=n.autoReplaceSvgRoot,e=t===void 0?x:t;(Object.keys(M.styles).length>0||m.autoFetchSvg)&&R&&m.autoReplaceSvg&&N.dom.i2svg({node:e})};function Na(a,n){return Object.defineProperty(a,"abstract",{get:n}),Object.defineProperty(a,"html",{get:function(){return a.abstract.map(function(e){return la(e)})}}),Object.defineProperty(a,"node",{get:function(){if(R){var e=x.createElement("div");return e.innerHTML=a.html,e.children}}}),a}function ue(a){var n=a.children,t=a.main,e=a.mask,r=a.attributes,i=a.styles,o=a.transform;if(an(o)&&t.found&&!e.found){var s=t.width,f=t.height,l={x:s/f/2,y:.5};r.style=Ca(u(u({},i),{},{"transform-origin":"".concat(l.x+o.x/16,"em ").concat(l.y+o.y/16,"em")}))}return[{tag:"svg",attributes:r,children:n}]}function me(a){var n=a.prefix,t=a.iconName,e=a.children,r=a.attributes,i=a.symbol,o=i===!0?"".concat(n,"-").concat(m.cssPrefix,"-").concat(t):i;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:u(u({},r),{},{id:o}),children:e}]}]}function rn(a){var n=a.icons,t=n.main,e=n.mask,r=a.prefix,i=a.iconName,o=a.transform,s=a.symbol,f=a.title,l=a.maskId,c=a.titleId,d=a.extra,g=a.watchable,b=g===void 0?!1:g,S=e.found?e:t,C=S.width,z=S.height,v=r==="fak",p=[m.replacementClass,i?"".concat(m.cssPrefix,"-").concat(i):""].filter(function(F){return d.classes.indexOf(F)===-1}).filter(function(F){return F!==""||!!F}).concat(d.classes).join(" "),h={children:[],attributes:u(u({},d.attributes),{},{"data-prefix":r,"data-icon":i,class:p,role:d.attributes.role||"img",xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 ".concat(C," ").concat(z)})},w=v&&!~d.classes.indexOf("fa-fw")?{width:"".concat(C/z*16*.0625,"em")}:{};b&&(h.attributes[W]=""),f&&(h.children.push({tag:"title",attributes:{id:h.attributes["aria-labelledby"]||"title-".concat(c||sa())},children:[f]}),delete h.attributes.title);var A=u(u({},h),{},{prefix:r,iconName:i,main:t,mask:e,maskId:l,transform:o,symbol:s,styles:u(u({},w),d.styles)}),L=e.found&&t.found?V("generateAbstractMask",A)||{children:[],attributes:{}}:V("generateAbstractIcon",A)||{children:[],attributes:{}},E=L.children,Ea=L.attributes;return A.children=E,A.attributes=Ea,s?me(A):ue(A)}function kn(a){var n=a.content,t=a.width,e=a.height,r=a.transform,i=a.title,o=a.extra,s=a.watchable,f=s===void 0?!1:s,l=u(u(u({},o.attributes),i?{title:i}:{}),{},{class:o.classes.join(" ")});f&&(l[W]="");var c=u({},o.styles);an(r)&&(c.transform=$t({transform:r,startCentered:!0,width:t,height:e}),c["-webkit-transform"]=c.transform);var d=Ca(c);d.length>0&&(l.style=d);var g=[];return g.push({tag:"span",attributes:l,children:[n]}),i&&g.push({tag:"span",attributes:{class:"sr-only"},children:[i]}),g}function de(a){var n=a.content,t=a.title,e=a.extra,r=u(u(u({},e.attributes),t?{title:t}:{}),{},{class:e.classes.join(" ")}),i=Ca(e.styles);i.length>0&&(r.style=i);var o=[];return o.push({tag:"span",attributes:r,children:[n]}),t&&o.push({tag:"span",attributes:{class:"sr-only"},children:[t]}),o}var Ia=M.styles;function $a(a){var n=a[0],t=a[1],e=a.slice(4),r=Ga(e,1),i=r[0],o=null;return Array.isArray(i)?o={tag:"g",attributes:{class:"".concat(m.cssPrefix,"-").concat(U.GROUP)},children:[{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(U.SECONDARY),fill:"currentColor",d:i[0]}},{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(U.PRIMARY),fill:"currentColor",d:i[1]}}]}:o={tag:"path",attributes:{fill:"currentColor",d:i}},{found:!0,width:n,height:t,icon:o}}var ve={found:!1,width:512,height:512};function pe(a,n){!$n&&!m.showMissingIcons&&a&&console.error('Icon with name "'.concat(a,'" and prefix "').concat(n,'" is missing.'))}function Ua(a,n){var t=n;return n==="fa"&&m.styleDefault!==null&&(n=Y()),new Promise(function(e,r){if(V("missingIconAbstract"),t==="fa"){var i=tt(a)||{};a=i.iconName||a,n=i.prefix||n}if(a&&n&&Ia[n]&&Ia[n][a]){var o=Ia[n][a];return e($a(o))}pe(a,n),e(u(u({},ve),{},{icon:m.showMissingIcons&&a?V("missingIconAbstract")||{}:{}}))})}var wn=function(){},Ba=m.measurePerformance&&ua&&ua.mark&&ua.measure?ua:{mark:wn,measure:wn},aa='FA "6.4.0"',ge=function(n){return Ba.mark("".concat(aa," ").concat(n," begins")),function(){return rt(n)}},rt=function(n){Ba.mark("".concat(aa," ").concat(n," ends")),Ba.measure("".concat(aa," ").concat(n),"".concat(aa," ").concat(n," begins"),"".concat(aa," ").concat(n," ends"))},on={begin:ge,end:rt},xa=function(){};function An(a){var n=a.getAttribute?a.getAttribute(W):null;return typeof n=="string"}function be(a){var n=a.getAttribute?a.getAttribute(qa):null,t=a.getAttribute?a.getAttribute(Qa):null;return n&&t}function he(a){return a&&a.classList&&a.classList.contains&&a.classList.contains(m.replacementClass)}function ye(){if(m.autoReplaceSvg===!0)return ka.replace;var a=ka[m.autoReplaceSvg];return a||ka.replace}function xe(a){return x.createElementNS("http://www.w3.org/2000/svg",a)}function ke(a){return x.createElement(a)}function it(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.ceFn,e=t===void 0?a.tag==="svg"?xe:ke:t;if(typeof a=="string")return x.createTextNode(a);var r=e(a.tag);Object.keys(a.attributes||[]).forEach(function(o){r.setAttribute(o,a.attributes[o])});var i=a.children||[];return i.forEach(function(o){r.appendChild(it(o,{ceFn:e}))}),r}function we(a){var n=" ".concat(a.outerHTML," ");return n="".concat(n,"Font Awesome fontawesome.com "),n}var ka={replace:function(n){var t=n[0];if(t.parentNode)if(n[1].forEach(function(r){t.parentNode.insertBefore(it(r),t)}),t.getAttribute(W)===null&&m.keepOriginalSource){var e=x.createComment(we(t));t.parentNode.replaceChild(e,t)}else t.remove()},nest:function(n){var t=n[0],e=n[1];if(~Ja(t).indexOf(m.replacementClass))return ka.replace(n);var r=new RegExp("".concat(m.cssPrefix,"-.*"));if(delete e[0].attributes.id,e[0].attributes.class){var i=e[0].attributes.class.split(" ").reduce(function(s,f){return f===m.replacementClass||f.match(r)?s.toSvg.push(f):s.toNode.push(f),s},{toNode:[],toSvg:[]});e[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?t.removeAttribute("class"):t.setAttribute("class",i.toNode.join(" "))}var o=e.map(function(s){return la(s)}).join(`
`);t.setAttribute(W,""),t.innerHTML=o}};function On(a){a()}function ot(a,n){var t=typeof n=="function"?n:xa;if(a.length===0)t();else{var e=On;m.mutateApproach===Ct&&(e=j.requestAnimationFrame||On),e(function(){var r=ye(),i=on.begin("mutate");a.map(r),i(),t()})}}var sn=!1;function st(){sn=!0}function Wa(){sn=!1}var Oa=null;function Sn(a){if(vn&&m.observeMutations){var n=a.treeCallback,t=n===void 0?xa:n,e=a.nodeCallback,r=e===void 0?xa:e,i=a.pseudoElementsCallback,o=i===void 0?xa:i,s=a.observeMutationsRoot,f=s===void 0?x:s;Oa=new vn(function(l){if(!sn){var c=Y();J(l).forEach(function(d){if(d.type==="childList"&&d.addedNodes.length>0&&!An(d.addedNodes[0])&&(m.searchPseudoElements&&o(d.target),t(d.target)),d.type==="attributes"&&d.target.parentNode&&m.searchPseudoElements&&o(d.target.parentNode),d.type==="attributes"&&An(d.target)&&~It.indexOf(d.attributeName))if(d.attributeName==="class"&&be(d.target)){var g=Pa(Ja(d.target)),b=g.prefix,S=g.iconName;d.target.setAttribute(qa,b||c),S&&d.target.setAttribute(Qa,S)}else he(d.target)&&r(d.target)})}}),R&&Oa.observe(f,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function Ae(){Oa&&Oa.disconnect()}function Oe(a){var n=a.getAttribute("style"),t=[];return n&&(t=n.split(";").reduce(function(e,r){var i=r.split(":"),o=i[0],s=i.slice(1);return o&&s.length>0&&(e[o]=s.join(":").trim()),e},{})),t}function Se(a){var n=a.getAttribute("data-prefix"),t=a.getAttribute("data-icon"),e=a.innerText!==void 0?a.innerText.trim():"",r=Pa(Ja(a));return r.prefix||(r.prefix=Y()),n&&t&&(r.prefix=n,r.iconName=t),r.iconName&&r.prefix||(r.prefix&&e.length>0&&(r.iconName=te(r.prefix,a.innerText)||tn(r.prefix,Fa(a.innerText))),!r.iconName&&m.autoFetchSvg&&a.firstChild&&a.firstChild.nodeType===Node.TEXT_NODE&&(r.iconName=a.firstChild.data)),r}function Ce(a){var n=J(a.attributes).reduce(function(r,i){return r.name!=="class"&&r.name!=="style"&&(r[i.name]=i.value),r},{}),t=a.getAttribute("title"),e=a.getAttribute("data-fa-title-id");return m.autoA11y&&(t?n["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(e||sa()):(n["aria-hidden"]="true",n.focusable="false")),n}function ze(){return{iconName:null,title:null,titleId:null,prefix:null,transform:I,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}}}function Cn(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},t=Se(a),e=t.iconName,r=t.prefix,i=t.rest,o=Ce(a),s=ja("parseNodeAttributes",{},a),f=n.styleParser?Oe(a):[];return u({iconName:e,title:a.getAttribute("title"),titleId:a.getAttribute("data-fa-title-id"),prefix:r,transform:I,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:i,styles:f,attributes:o}},s)}var Pe=M.styles;function ft(a){var n=m.autoReplaceSvg==="nest"?Cn(a,{styleParser:!1}):Cn(a);return~n.extra.classes.indexOf(Un)?V("generateLayersText",a,n):V("generateSvgReplacementMutation",a,n)}var $=new Set;Za.map(function(a){$.add("fa-".concat(a))});Object.keys(ea[y]).map($.add.bind($));Object.keys(ea[k]).map($.add.bind($));$=fa($);function zn(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!R)return Promise.resolve();var t=x.documentElement.classList,e=function(d){return t.add("".concat(pn,"-").concat(d))},r=function(d){return t.remove("".concat(pn,"-").concat(d))},i=m.autoFetchSvg?$:Za.map(function(c){return"fa-".concat(c)}).concat(Object.keys(Pe));i.includes("fa")||i.push("fa");var o=[".".concat(Un,":not([").concat(W,"])")].concat(i.map(function(c){return".".concat(c,":not([").concat(W,"])")})).join(", ");if(o.length===0)return Promise.resolve();var s=[];try{s=J(a.querySelectorAll(o))}catch{}if(s.length>0)e("pending"),r("complete");else return Promise.resolve();var f=on.begin("onTree"),l=s.reduce(function(c,d){try{var g=ft(d);g&&c.push(g)}catch(b){$n||b.name==="MissingIcon"&&console.error(b)}return c},[]);return new Promise(function(c,d){Promise.all(l).then(function(g){ot(g,function(){e("active"),e("complete"),r("pending"),typeof n=="function"&&n(),f(),c()})}).catch(function(g){f(),d(g)})})}function Ne(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;ft(a).then(function(t){t&&ot([t],n)})}function Ee(a){return function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},e=(n||{}).icon?n:Ya(n||{}),r=t.mask;return r&&(r=(r||{}).icon?r:Ya(r||{})),a(e,u(u({},t),{},{mask:r}))}}var Me=function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},e=t.transform,r=e===void 0?I:e,i=t.symbol,o=i===void 0?!1:i,s=t.mask,f=s===void 0?null:s,l=t.maskId,c=l===void 0?null:l,d=t.title,g=d===void 0?null:d,b=t.titleId,S=b===void 0?null:b,C=t.classes,z=C===void 0?[]:C,v=t.attributes,p=v===void 0?{}:v,h=t.styles,w=h===void 0?{}:h;if(n){var A=n.prefix,L=n.iconName,E=n.icon;return Na(u({type:"icon"},n),function(){return X("beforeDOMElementCreation",{iconDefinition:n,params:t}),m.autoA11y&&(g?p["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(S||sa()):(p["aria-hidden"]="true",p.focusable="false")),rn({icons:{main:$a(E),mask:f?$a(f.icon):{found:!1,width:null,height:null,icon:{}}},prefix:A,iconName:L,transform:u(u({},I),r),symbol:o,title:g,maskId:c,titleId:S,extra:{attributes:p,styles:w,classes:z}})})}},Le={mixout:function(){return{icon:Ee(Me)}},hooks:function(){return{mutationObserverCallbacks:function(t){return t.treeCallback=zn,t.nodeCallback=Ne,t}}},provides:function(n){n.i2svg=function(t){var e=t.node,r=e===void 0?x:e,i=t.callback,o=i===void 0?function(){}:i;return zn(r,o)},n.generateSvgReplacementMutation=function(t,e){var r=e.iconName,i=e.title,o=e.titleId,s=e.prefix,f=e.transform,l=e.symbol,c=e.mask,d=e.maskId,g=e.extra;return new Promise(function(b,S){Promise.all([Ua(r,s),c.iconName?Ua(c.iconName,c.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(C){var z=Ga(C,2),v=z[0],p=z[1];b([t,rn({icons:{main:v,mask:p},prefix:s,iconName:r,transform:f,symbol:l,maskId:d,title:i,titleId:o,extra:g,watchable:!0})])}).catch(S)})},n.generateAbstractIcon=function(t){var e=t.children,r=t.attributes,i=t.main,o=t.transform,s=t.styles,f=Ca(s);f.length>0&&(r.style=f);var l;return an(o)&&(l=V("generateAbstractTransformGrouping",{main:i,transform:o,containerWidth:i.width,iconWidth:i.width})),e.push(l||i.icon),{children:e,attributes:r}}}},Ie={mixout:function(){return{layer:function(t){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=e.classes,i=r===void 0?[]:r;return Na({type:"layer"},function(){X("beforeDOMElementCreation",{assembler:t,params:e});var o=[];return t(function(s){Array.isArray(s)?s.map(function(f){o=o.concat(f.abstract)}):o=o.concat(s.abstract)}),[{tag:"span",attributes:{class:["".concat(m.cssPrefix,"-layers")].concat(fa(i)).join(" ")},children:o}]})}}}},_e={mixout:function(){return{counter:function(t){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=e.title,i=r===void 0?null:r,o=e.classes,s=o===void 0?[]:o,f=e.attributes,l=f===void 0?{}:f,c=e.styles,d=c===void 0?{}:c;return Na({type:"counter",content:t},function(){return X("beforeDOMElementCreation",{content:t,params:e}),de({content:t.toString(),title:i,extra:{attributes:l,styles:d,classes:["".concat(m.cssPrefix,"-layers-counter")].concat(fa(s))}})})}}}},Te={mixout:function(){return{text:function(t){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=e.transform,i=r===void 0?I:r,o=e.title,s=o===void 0?null:o,f=e.classes,l=f===void 0?[]:f,c=e.attributes,d=c===void 0?{}:c,g=e.styles,b=g===void 0?{}:g;return Na({type:"text",content:t},function(){return X("beforeDOMElementCreation",{content:t,params:e}),kn({content:t,transform:u(u({},I),i),title:s,extra:{attributes:d,styles:b,classes:["".concat(m.cssPrefix,"-layers-text")].concat(fa(l))}})})}}},provides:function(n){n.generateLayersText=function(t,e){var r=e.title,i=e.transform,o=e.extra,s=null,f=null;if(Dn){var l=parseInt(getComputedStyle(t).fontSize,10),c=t.getBoundingClientRect();s=c.width/l,f=c.height/l}return m.autoA11y&&!r&&(o.attributes["aria-hidden"]="true"),Promise.resolve([t,kn({content:t.innerHTML,width:s,height:f,transform:i,title:r,extra:o,watchable:!0})])}}},He=new RegExp('"',"ug"),Pn=[1105920,1112319];function Ve(a){var n=a.replace(He,""),t=qt(n,0),e=t>=Pn[0]&&t<=Pn[1],r=n.length===2?n[0]===n[1]:!1;return{value:Fa(r?n[0]:n),isSecondary:e||r}}function Nn(a,n){var t="".concat(St).concat(n.replace(":","-"));return new Promise(function(e,r){if(a.getAttribute(t)!==null)return e();var i=J(a.children),o=i.filter(function(E){return E.getAttribute(Ra)===n})[0],s=j.getComputedStyle(a,n),f=s.getPropertyValue("font-family").match(Et),l=s.getPropertyValue("font-weight"),c=s.getPropertyValue("content");if(o&&!f)return a.removeChild(o),e();if(f&&c!=="none"&&c!==""){var d=s.getPropertyValue("content"),g=~["Sharp"].indexOf(f[2])?k:y,b=~["Solid","Regular","Light","Thin","Duotone","Brands","Kit"].indexOf(f[2])?ra[g][f[2].toLowerCase()]:Mt[g][l],S=Ve(d),C=S.value,z=S.isSecondary,v=f[0].startsWith("FontAwesome"),p=tn(b,C),h=p;if(v){var w=ee(C);w.iconName&&w.prefix&&(p=w.iconName,b=w.prefix)}if(p&&!z&&(!o||o.getAttribute(qa)!==b||o.getAttribute(Qa)!==h)){a.setAttribute(t,h),o&&a.removeChild(o);var A=ze(),L=A.extra;L.attributes[Ra]=n,Ua(p,b).then(function(E){var Ea=rn(u(u({},A),{},{icons:{main:E,mask:en()},prefix:b,iconName:h,extra:L,watchable:!0})),F=x.createElement("svg");n==="::before"?a.insertBefore(F,a.firstChild):a.appendChild(F),F.outerHTML=Ea.map(function(mt){return la(mt)}).join(`
`),a.removeAttribute(t),e()}).catch(r)}else e()}else e()})}function Re(a){return Promise.all([Nn(a,"::before"),Nn(a,"::after")])}function Fe(a){return a.parentNode!==document.head&&!~zt.indexOf(a.tagName.toUpperCase())&&!a.getAttribute(Ra)&&(!a.parentNode||a.parentNode.tagName!=="svg")}function En(a){if(R)return new Promise(function(n,t){var e=J(a.querySelectorAll("*")).filter(Fe).map(Re),r=on.begin("searchPseudoElements");st(),Promise.all(e).then(function(){r(),Wa(),n()}).catch(function(){r(),Wa(),t()})})}var De={hooks:function(){return{mutationObserverCallbacks:function(t){return t.pseudoElementsCallback=En,t}}},provides:function(n){n.pseudoElements2svg=function(t){var e=t.node,r=e===void 0?x:e;m.searchPseudoElements&&En(r)}}},Mn=!1,je={mixout:function(){return{dom:{unwatch:function(){st(),Mn=!0}}}},hooks:function(){return{bootstrap:function(){Sn(ja("mutationObserverCallbacks",{}))},noAuto:function(){Ae()},watch:function(t){var e=t.observeMutationsRoot;Mn?Wa():Sn(ja("mutationObserverCallbacks",{observeMutationsRoot:e}))}}}},Ln=function(n){var t={size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0};return n.toLowerCase().split(" ").reduce(function(e,r){var i=r.toLowerCase().split("-"),o=i[0],s=i.slice(1).join("-");if(o&&s==="h")return e.flipX=!0,e;if(o&&s==="v")return e.flipY=!0,e;if(s=parseFloat(s),isNaN(s))return e;switch(o){case"grow":e.size=e.size+s;break;case"shrink":e.size=e.size-s;break;case"left":e.x=e.x-s;break;case"right":e.x=e.x+s;break;case"up":e.y=e.y-s;break;case"down":e.y=e.y+s;break;case"rotate":e.rotate=e.rotate+s;break}return e},t)},Ye={mixout:function(){return{parse:{transform:function(t){return Ln(t)}}}},hooks:function(){return{parseNodeAttributes:function(t,e){var r=e.getAttribute("data-fa-transform");return r&&(t.transform=Ln(r)),t}}},provides:function(n){n.generateAbstractTransformGrouping=function(t){var e=t.main,r=t.transform,i=t.containerWidth,o=t.iconWidth,s={transform:"translate(".concat(i/2," 256)")},f="translate(".concat(r.x*32,", ").concat(r.y*32,") "),l="scale(".concat(r.size/16*(r.flipX?-1:1),", ").concat(r.size/16*(r.flipY?-1:1),") "),c="rotate(".concat(r.rotate," 0 0)"),d={transform:"".concat(f," ").concat(l," ").concat(c)},g={transform:"translate(".concat(o/2*-1," -256)")},b={outer:s,inner:d,path:g};return{tag:"g",attributes:u({},b.outer),children:[{tag:"g",attributes:u({},b.inner),children:[{tag:e.icon.tag,children:e.icon.children,attributes:u(u({},e.icon.attributes),b.path)}]}]}}}},_a={x:0,y:0,width:"100%",height:"100%"};function In(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!0;return a.attributes&&(a.attributes.fill||n)&&(a.attributes.fill="black"),a}function $e(a){return a.tag==="g"?a.children:[a]}var Ue={hooks:function(){return{parseNodeAttributes:function(t,e){var r=e.getAttribute("data-fa-mask"),i=r?Pa(r.split(" ").map(function(o){return o.trim()})):en();return i.prefix||(i.prefix=Y()),t.mask=i,t.maskId=e.getAttribute("data-fa-mask-id"),t}}},provides:function(n){n.generateAbstractMask=function(t){var e=t.children,r=t.attributes,i=t.main,o=t.mask,s=t.maskId,f=t.transform,l=i.width,c=i.icon,d=o.width,g=o.icon,b=Yt({transform:f,containerWidth:d,iconWidth:l}),S={tag:"rect",attributes:u(u({},_a),{},{fill:"white"})},C=c.children?{children:c.children.map(In)}:{},z={tag:"g",attributes:u({},b.inner),children:[In(u({tag:c.tag,attributes:u(u({},c.attributes),b.path)},C))]},v={tag:"g",attributes:u({},b.outer),children:[z]},p="mask-".concat(s||sa()),h="clip-".concat(s||sa()),w={tag:"mask",attributes:u(u({},_a),{},{id:p,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[S,v]},A={tag:"defs",children:[{tag:"clipPath",attributes:{id:h},children:$e(g)},w]};return e.push(A,{tag:"rect",attributes:u({fill:"currentColor","clip-path":"url(#".concat(h,")"),mask:"url(#".concat(p,")")},_a)}),{children:e,attributes:r}}}},Be={provides:function(n){var t=!1;j.matchMedia&&(t=j.matchMedia("(prefers-reduced-motion: reduce)").matches),n.missingIconAbstract=function(){var e=[],r={fill:"currentColor"},i={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};e.push({tag:"path",attributes:u(u({},r),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var o=u(u({},i),{},{attributeName:"opacity"}),s={tag:"circle",attributes:u(u({},r),{},{cx:"256",cy:"364",r:"28"}),children:[]};return t||s.children.push({tag:"animate",attributes:u(u({},i),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:u(u({},o),{},{values:"1;0;1;1;0;1;"})}),e.push(s),e.push({tag:"path",attributes:u(u({},r),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:t?[]:[{tag:"animate",attributes:u(u({},o),{},{values:"1;0;0;0;0;1;"})}]}),t||e.push({tag:"path",attributes:u(u({},r),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:u(u({},o),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:e}}}},We={hooks:function(){return{parseNodeAttributes:function(t,e){var r=e.getAttribute("data-fa-symbol"),i=r===null?!1:r===""?!0:r;return t.symbol=i,t}}}},Xe=[Bt,Le,Ie,_e,Te,De,je,Ye,Ue,Be,We];oe(Xe,{mixoutsTo:N});N.noAuto;N.config;var ur=N.library;N.dom;var Xa=N.parse;N.findIconDefinition;N.toHtml;var Ge=N.icon;N.layer;N.text;N.counter;function _n(a,n){var t=Object.keys(a);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(a);n&&(e=e.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),t.push.apply(t,e)}return t}function _(a){for(var n=1;n<arguments.length;n++){var t=arguments[n]!=null?arguments[n]:{};n%2?_n(Object(t),!0).forEach(function(e){P(a,e,t[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(t)):_n(Object(t)).forEach(function(e){Object.defineProperty(a,e,Object.getOwnPropertyDescriptor(t,e))})}return a}function Sa(a){"@babel/helpers - typeof";return Sa=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(n){return typeof n}:function(n){return n&&typeof Symbol=="function"&&n.constructor===Symbol&&n!==Symbol.prototype?"symbol":typeof n},Sa(a)}function P(a,n,t){return n in a?Object.defineProperty(a,n,{value:t,enumerable:!0,configurable:!0,writable:!0}):a[n]=t,a}function Ke(a,n){if(a==null)return{};var t={},e=Object.keys(a),r,i;for(i=0;i<e.length;i++)r=e[i],!(n.indexOf(r)>=0)&&(t[r]=a[r]);return t}function qe(a,n){if(a==null)return{};var t=Ke(a,n),e,r;if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(a);for(r=0;r<i.length;r++)e=i[r],!(n.indexOf(e)>=0)&&Object.prototype.propertyIsEnumerable.call(a,e)&&(t[e]=a[e])}return t}var Qe=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof fn<"u"?fn:typeof self<"u"?self:{},ct={exports:{}};(function(a){(function(n){var t=function(v,p,h){if(!l(p)||d(p)||g(p)||b(p)||f(p))return p;var w,A=0,L=0;if(c(p))for(w=[],L=p.length;A<L;A++)w.push(t(v,p[A],h));else{w={};for(var E in p)Object.prototype.hasOwnProperty.call(p,E)&&(w[v(E,h)]=t(v,p[E],h))}return w},e=function(v,p){p=p||{};var h=p.separator||"_",w=p.split||/(?=[A-Z])/;return v.split(w).join(h)},r=function(v){return S(v)?v:(v=v.replace(/[\-_\s]+(.)?/g,function(p,h){return h?h.toUpperCase():""}),v.substr(0,1).toLowerCase()+v.substr(1))},i=function(v){var p=r(v);return p.substr(0,1).toUpperCase()+p.substr(1)},o=function(v,p){return e(v,p).toLowerCase()},s=Object.prototype.toString,f=function(v){return typeof v=="function"},l=function(v){return v===Object(v)},c=function(v){return s.call(v)=="[object Array]"},d=function(v){return s.call(v)=="[object Date]"},g=function(v){return s.call(v)=="[object RegExp]"},b=function(v){return s.call(v)=="[object Boolean]"},S=function(v){return v=v-0,v===v},C=function(v,p){var h=p&&"process"in p?p.process:p;return typeof h!="function"?v:function(w,A){return h(w,v,A)}},z={camelize:r,decamelize:o,pascalize:i,depascalize:o,camelizeKeys:function(v,p){return t(C(r,p),v)},decamelizeKeys:function(v,p){return t(C(o,p),v,p)},pascalizeKeys:function(v,p){return t(C(i,p),v)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}};a.exports?a.exports=z:n.humps=z})(Qe)})(ct);var Ze=ct.exports,Je=["class","style"];function ar(a){return a.split(";").map(function(n){return n.trim()}).filter(function(n){return n}).reduce(function(n,t){var e=t.indexOf(":"),r=Ze.camelize(t.slice(0,e)),i=t.slice(e+1).trim();return n[r]=i,n},{})}function nr(a){return a.split(/\s+/).reduce(function(n,t){return n[t]=!0,n},{})}function lt(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof a=="string")return a;var e=(a.children||[]).map(function(f){return lt(f)}),r=Object.keys(a.attributes||{}).reduce(function(f,l){var c=a.attributes[l];switch(l){case"class":f.class=nr(c);break;case"style":f.style=ar(c);break;default:f.attrs[l]=c}return f},{attrs:{},class:{},style:{}});t.class;var i=t.style,o=i===void 0?{}:i,s=qe(t,Je);return pt(a.tag,_(_(_({},n),{},{class:r.class,style:_(_({},r.style),o)},r.attrs),s),e)}var ut=!1;try{ut=!1}catch{}function tr(){if(!ut&&console&&typeof console.error=="function"){var a;(a=console).error.apply(a,arguments)}}function Ta(a,n){return Array.isArray(n)&&n.length>0||!Array.isArray(n)&&n?P({},a,n):{}}function er(a){var n,t=(n={"fa-spin":a.spin,"fa-pulse":a.pulse,"fa-fw":a.fixedWidth,"fa-border":a.border,"fa-li":a.listItem,"fa-inverse":a.inverse,"fa-flip":a.flip===!0,"fa-flip-horizontal":a.flip==="horizontal"||a.flip==="both","fa-flip-vertical":a.flip==="vertical"||a.flip==="both"},P(n,"fa-".concat(a.size),a.size!==null),P(n,"fa-rotate-".concat(a.rotation),a.rotation!==null),P(n,"fa-pull-".concat(a.pull),a.pull!==null),P(n,"fa-swap-opacity",a.swapOpacity),P(n,"fa-bounce",a.bounce),P(n,"fa-shake",a.shake),P(n,"fa-beat",a.beat),P(n,"fa-fade",a.fade),P(n,"fa-beat-fade",a.beatFade),P(n,"fa-flash",a.flash),P(n,"fa-spin-pulse",a.spinPulse),P(n,"fa-spin-reverse",a.spinReverse),n);return Object.keys(t).map(function(e){return t[e]?e:null}).filter(function(e){return e})}function Tn(a){if(a&&Sa(a)==="object"&&a.prefix&&a.iconName&&a.icon)return a;if(Xa.icon)return Xa.icon(a);if(a===null)return null;if(Sa(a)==="object"&&a.prefix&&a.iconName)return a;if(Array.isArray(a)&&a.length===2)return{prefix:a[0],iconName:a[1]};if(typeof a=="string")return{prefix:"fas",iconName:a}}var mr=dt({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(n){return[!0,!1,"horizontal","vertical","both"].indexOf(n)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(n){return["right","left"].indexOf(n)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(n){return[90,180,270].indexOf(Number.parseInt(n,10))>-1}},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(n){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(n)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1}},setup:function(n,t){var e=t.attrs,r=G(function(){return Tn(n.icon)}),i=G(function(){return Ta("classes",er(n))}),o=G(function(){return Ta("transform",typeof n.transform=="string"?Xa.transform(n.transform):n.transform)}),s=G(function(){return Ta("mask",Tn(n.mask))}),f=G(function(){return Ge(r.value,_(_(_(_({},i.value),o.value),s.value),{},{symbol:n.symbol,title:n.title}))});vt(f,function(c){if(!c)return tr("Could not find one or more icon(s)",r.value,s.value)},{immediate:!0});var l=G(function(){return f.value?lt(f.value.abstract[0],{},e):null});return function(){return l.value}}}),rr={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm64 80v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm128 0v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H208c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H336zM64 400v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H208zm112 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H336c-8.8 0-16 7.2-16 16z"]},dr=rr,vr={prefix:"fas",iconName:"lock",icon:[448,512,[128274],"f023","M144 144v48H304V144c0-44.2-35.8-80-80-80s-80 35.8-80 80zM80 192V144C80 64.5 144.5 0 224 0s144 64.5 144 144v48h16c35.3 0 64 28.7 64 64V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V256c0-35.3 28.7-64 64-64H80z"]},ir={prefix:"fas",iconName:"pen-to-square",icon:[512,512,["edit"],"f044","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L362.3 51.7l97.9 97.9 30.1-30.1c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L437.7 172.3 339.7 74.3 172.4 241.7zM96 64C43 64 0 107 0 160V416c0 53 43 96 96 96H352c53 0 96-43 96-96V320c0-17.7-14.3-32-32-32s-32 14.3-32 32v96c0 17.7-14.3 32-32 32H96c-17.7 0-32-14.3-32-32V160c0-17.7 14.3-32 32-32h96c17.7 0 32-14.3 32-32s-14.3-32-32-32H96z"]},pr=ir,gr={prefix:"fas",iconName:"star",icon:[576,512,[11088,61446],"f005","M316.9 18C311.6 7 300.4 0 288.1 0s-23.4 7-28.8 18L195 150.3 51.4 171.5c-12 1.8-22 10.2-25.7 21.7s-.7 24.2 7.9 32.7L137.8 329 113.2 474.7c-2 12 3 24.2 12.9 31.3s23 8 33.8 2.3l128.3-68.5 128.3 68.5c10.8 5.7 23.9 4.9 33.8-2.3s14.9-19.3 12.9-31.3L438.5 329 542.7 225.9c8.6-8.5 11.7-21.2 7.9-32.7s-13.7-19.9-25.7-21.7L381.2 150.3 316.9 18z"]},br={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M96 0C60.7 0 32 28.7 32 64V448c-17.7 0-32 14.3-32 32s14.3 32 32 32H320c17.7 0 32-14.3 32-32s-14.3-32-32-32V304h16c22.1 0 40 17.9 40 40v32c0 39.8 32.2 72 72 72s72-32.2 72-72V252.3c32.5-10.2 56-40.5 56-76.3V144c0-8.8-7.2-16-16-16H544V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H480V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H432c-8.8 0-16 7.2-16 16v32c0 35.8 23.5 66.1 56 76.3V376c0 13.3-10.7 24-24 24s-24-10.7-24-24V344c0-48.6-39.4-88-88-88H320V64c0-35.3-28.7-64-64-64H96zM216.9 82.7c6 4 8.5 11.5 6.3 18.3l-25 74.9H256c6.7 0 12.7 4.2 15 10.4s.5 13.3-4.6 17.7l-112 96c-5.5 4.7-13.4 5.1-19.3 1.1s-8.5-11.5-6.3-18.3l25-74.9H96c-6.7 0-12.7-4.2-15-10.4s-.5-13.3 4.6-17.7l112-96c5.5-4.7 13.4-5.1 19.3-1.1z"]},hr={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 96c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32h16c35.3 0 64 28.7 64 64V384c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V160c0-35.3 28.7-64 64-64l16 0zm304 96c0-8.8-7.2-16-16-16s-16 7.2-16 16v32H320c-8.8 0-16 7.2-16 16s7.2 16 16 16h32v32c0 8.8 7.2 16 16 16s16-7.2 16-16V256h32c8.8 0 16-7.2 16-16s-7.2-16-16-16H384V192zM80 240c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16s-7.2-16-16-16H96c-8.8 0-16 7.2-16 16z"]},yr={prefix:"fas",iconName:"plug-circle-bolt",icon:[576,512,[],"e55b","M96 0C78.3 0 64 14.3 64 32v96h64V32c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32v96h64V32c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32v32c0 77.4 55 142 128 156.8V480c0 17.7 14.3 32 32 32s32-14.3 32-32V412.8c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32H32zM432 512a144 144 0 1 0 0-288 144 144 0 1 0 0 288zm47.9-225c4.3 3.7 5.4 9.9 2.6 14.9L452.4 356H488c5.2 0 9.8 3.3 11.4 8.2s-.1 10.3-4.2 13.4l-96 72c-4.5 3.4-10.8 3.2-15.1-.6s-5.4-9.9-2.6-14.9L411.6 380H376c-5.2 0-9.8-3.3-11.4-8.2s.1-10.3 4.2-13.4l96-72c4.5-3.4 10.8-3.2 15.1 .6z"]},xr={prefix:"fas",iconName:"solar-panel",icon:[640,512,[],"f5ba","M122.2 0C91.7 0 65.5 21.5 59.5 51.4L8.3 307.4C.4 347 30.6 384 71 384H288v64H224c-17.7 0-32 14.3-32 32s14.3 32 32 32H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H352V384H569c40.4 0 70.7-36.9 62.8-76.6l-51.2-256C574.5 21.5 548.3 0 517.8 0H122.2zM260.9 64H379.1l10.4 104h-139L260.9 64zM202.3 168H101.4L122.2 64h90.4L202.3 168zM91.8 216H197.5L187.1 320H71L91.8 216zm153.9 0H394.3l10.4 104-169.4 0 10.4-104zm196.8 0H548.2L569 320h-116L442.5 216zm96-48H437.7L427.3 64h90.4l31.4-6.3L517.8 64l20.8 104z"]},kr={prefix:"fas",iconName:"lock-open",icon:[576,512,[],"f3c1","M352 144c0-44.2 35.8-80 80-80s80 35.8 80 80v48c0 17.7 14.3 32 32 32s32-14.3 32-32V144C576 64.5 511.5 0 432 0S288 64.5 288 144v48H64c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V256c0-35.3-28.7-64-64-64H352V144z"]},wr={prefix:"fas",iconName:"wrench",icon:[512,512,[128295],"f0ad","M352 320c88.4 0 160-71.6 160-160c0-15.3-2.2-30.1-6.2-44.2c-3.1-10.8-16.4-13.2-24.3-5.3l-76.8 76.8c-3 3-7.1 4.7-11.3 4.7H336c-8.8 0-16-7.2-16-16V118.6c0-4.2 1.7-8.3 4.7-11.3l76.8-76.8c7.9-7.9 5.4-21.2-5.3-24.3C382.1 2.2 367.3 0 352 0C263.6 0 192 71.6 192 160c0 19.1 3.4 37.5 9.5 54.5L19.9 396.1C7.2 408.8 0 426.1 0 444.1C0 481.6 30.4 512 67.9 512c18 0 35.3-7.2 48-19.9L297.5 310.5c17 6.2 35.4 9.5 54.5 9.5zM80 408a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"]},or={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM216 336h24V272H216c-13.3 0-24-10.7-24-24s10.7-24 24-24h48c13.3 0 24 10.7 24 24v88h8c13.3 0 24 10.7 24 24s-10.7 24-24 24H216c-13.3 0-24-10.7-24-24s10.7-24 24-24zm40-208a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"]},Ar=or,Or={prefix:"fas",iconName:"plug-circle-check",icon:[576,512,[],"e55c","M96 0C78.3 0 64 14.3 64 32v96h64V32c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32v96h64V32c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32v32c0 77.4 55 142 128 156.8V480c0 17.7 14.3 32 32 32s32-14.3 32-32V412.8c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32H32zM576 368a144 144 0 1 0 -288 0 144 144 0 1 0 288 0zm-76.7-43.3c6.2 6.2 6.2 16.4 0 22.6l-72 72c-6.2 6.2-16.4 6.2-22.6 0l-40-40c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0L416 385.4l60.7-60.7c6.2-6.2 16.4-6.2 22.6 0z"]},Sr={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512A256 256 0 1 1 256 0zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},Cr={prefix:"fas",iconName:"delete-left",icon:[576,512,[9003,"backspace"],"f55a","M576 128c0-35.3-28.7-64-64-64H205.3c-17 0-33.3 6.7-45.3 18.7L9.4 233.4c-6 6-9.4 14.1-9.4 22.6s3.4 16.6 9.4 22.6L160 429.3c12 12 28.3 18.7 45.3 18.7H512c35.3 0 64-28.7 64-64V128zM271 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},sr={prefix:"fas",iconName:"house",icon:[576,512,[127968,63498,63500,"home","home-alt","home-lg-alt"],"f015","M575.8 255.5c0 18-15 32.1-32 32.1h-32l.7 160.2c0 2.7-.2 5.4-.5 8.1V472c0 22.1-17.9 40-40 40H456c-1.1 0-2.2 0-3.3-.1c-1.4 .1-2.8 .1-4.2 .1H416 392c-22.1 0-40-17.9-40-40V448 384c0-17.7-14.3-32-32-32H256c-17.7 0-32 14.3-32 32v64 24c0 22.1-17.9 40-40 40H160 128.1c-1.5 0-3-.1-4.5-.2c-1.2 .1-2.4 .2-3.6 .2H104c-22.1 0-40-17.9-40-40V360c0-.9 0-1.9 .1-2.8V287.6H32c-18 0-32-14-32-32.1c0-9 3-17 10-24L266.4 8c7-7 15-8 22-8s15 2 21 7L564.8 231.5c8 7 12 15 11 24z"]},zr=sr,Pr={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v64c0 8.8 7.2 16 16 16H368c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},Nr={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M349.4 44.6c5.9-13.7 1.5-29.7-10.6-38.5s-28.6-8-39.9 1.8l-256 224c-10 8.8-13.6 22.9-8.9 35.3S50.7 288 64 288H175.5L98.6 467.4c-5.9 13.7-1.5 29.7 10.6 38.5s28.6 8 39.9-1.8l256-224c10-8.8 13.6-22.9 8.9-35.3s-16.6-20.7-30-20.7H272.5L349.4 44.6z"]},Er={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4L109.1 192H402.9l-26.1-74.6C372.3 104.6 360.2 96 346.6 96H165.4c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32H346.6c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2V400v48c0 17.7-14.3 32-32 32H448c-17.7 0-32-14.3-32-32V400H96v48c0 17.7-14.3 32-32 32H32c-17.7 0-32-14.3-32-32V400 256c0-26.7 16.4-49.6 39.6-59.2zM128 288a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},Mr={prefix:"fas",iconName:"plug-circle-xmark",icon:[576,512,[],"e560","M96 0C78.3 0 64 14.3 64 32v96h64V32c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32v96h64V32c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32v32c0 77.4 55 142 128 156.8V480c0 17.7 14.3 32 32 32s32-14.3 32-32V412.8c12.3-2.5 24.1-6.4 35.1-11.5c-2.1-10.8-3.1-21.9-3.1-33.3c0-80.3 53.8-148 127.3-169.2c.5-2.2 .7-4.5 .7-6.8c0-17.7-14.3-32-32-32H32zM432 512a144 144 0 1 0 0-288 144 144 0 1 0 0 288zm59.3-180.7L454.6 368l36.7 36.7c6.2 6.2 6.2 16.4 0 22.6s-16.4 6.2-22.6 0L432 390.6l-36.7 36.7c-6.2 6.2-16.4 6.2-22.6 0s-6.2-16.4 0-22.6L409.4 368l-36.7-36.7c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0L432 345.4l36.7-36.7c6.2-6.2 16.4-6.2 22.6 0s6.2 16.4 0 22.6z"]},Lr={prefix:"fas",iconName:"eraser",icon:[576,512,[],"f12d","M290.7 57.4L57.4 290.7c-25 25-25 65.5 0 90.5l80 80c12 12 28.3 18.7 45.3 18.7H288h9.4H512c17.7 0 32-14.3 32-32s-14.3-32-32-32H387.9L518.6 285.3c25-25 25-65.5 0-90.5L381.3 57.4c-25-25-65.5-25-90.5 0zM297.4 416H288l-105.4 0-80-80L227.3 211.3 364.7 348.7 297.4 416z"]},Ir={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64c0-17.4-6.9-33.1-18.1-44.6L366 161.7c5.3-12.1-.2-26.3-12.3-31.6s-26.3 .2-31.6 12.3L257.9 288c-.6 0-1.3 0-1.9 0c-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},fr={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 32c14.2 0 27.3 7.5 34.5 19.8l216 368c7.3 12.4 7.3 27.7 .2 40.1S486.3 480 472 480H40c-14.3 0-27.6-7.7-34.7-20.1s-7-27.8 .2-40.1l216-368C228.7 39.5 241.8 32 256 32zm0 128c-13.3 0-24 10.7-24 24V296c0 13.3 10.7 24 24 24s24-10.7 24-24V184c0-13.3-10.7-24-24-24zm32 224a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},_r=fr,Tr={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v96c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},cr={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM175 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},Hr=cr,Vr={prefix:"far",iconName:"star",icon:[576,512,[11088,61446],"f005","M287.9 0c9.2 0 17.6 5.2 21.6 13.5l68.6 141.3 153.2 22.6c9 1.3 16.5 7.6 19.3 16.3s.5 18.1-5.9 24.5L433.6 328.4l26.2 155.6c1.5 9-2.2 18.1-9.6 23.5s-17.3 6-25.3 1.7l-137-73.2L151 509.1c-8.1 4.3-17.9 3.7-25.3-1.7s-11.2-14.5-9.7-23.5l26.2-155.6L31.1 218.2c-6.5-6.4-8.7-15.9-5.9-24.5s10.3-14.9 19.3-16.3l153.2-22.6L266.3 13.5C270.4 5.2 278.7 0 287.9 0zm0 79L235.4 187.2c-3.5 7.1-10.2 12.1-18.1 13.3L99 217.9 184.9 303c5.5 5.5 8.1 13.3 6.8 21L171.4 443.7l105.2-56.2c7.1-3.8 15.6-3.8 22.6 0l105.2 56.2L384.2 324.1c-1.3-7.7 1.2-15.5 6.8-21l85.9-85.1L358.6 200.5c-7.8-1.2-14.6-6.1-18.1-13.3L287.9 79z"]},Rr={prefix:"far",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M464 256A208 208 0 1 1 48 256a208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0A256 256 0 1 0 0 256zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]};export{dr as A,mr as F,kr as a,Cr as b,Lr as c,Ir as d,hr as e,vr as f,xr as g,zr as h,br as i,Mr as j,Or as k,ur as l,yr as m,wr as n,Er as o,pr as p,Hr as q,_r as r,Ar as s,gr as t,Vr as u,Sr as v,Rr as w,Nr as x,Tr as y,Pr as z};
