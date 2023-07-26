import{g as ce,d as _e,f as U,w as bn,h as Te}from"./vendor-20bb207d.js";function fe(a,e){var n=Object.keys(a);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(a);e&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),n.push.apply(n,t)}return n}function u(a){for(var e=1;e<arguments.length;e++){var n=arguments[e]!=null?arguments[e]:{};e%2?fe(Object(n),!0).forEach(function(t){A(a,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(n)):fe(Object(n)).forEach(function(t){Object.defineProperty(a,t,Object.getOwnPropertyDescriptor(n,t))})}return a}function wa(a){"@babel/helpers - typeof";return wa=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},wa(a)}function gn(a,e){if(!(a instanceof e))throw new TypeError("Cannot call a class as a function")}function le(a,e){for(var n=0;n<e.length;n++){var t=e[n];t.enumerable=t.enumerable||!1,t.configurable=!0,"value"in t&&(t.writable=!0),Object.defineProperty(a,t.key,t)}}function hn(a,e,n){return e&&le(a.prototype,e),n&&le(a,n),Object.defineProperty(a,"prototype",{writable:!1}),a}function A(a,e,n){return e in a?Object.defineProperty(a,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):a[e]=n,a}function qa(a,e){return xn(a)||wn(a,e)||Fe(a,e)||An()}function ca(a){return yn(a)||kn(a)||Fe(a)||zn()}function yn(a){if(Array.isArray(a))return _a(a)}function xn(a){if(Array.isArray(a))return a}function kn(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function wn(a,e){var n=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(n!=null){var t=[],r=!0,i=!1,o,s;try{for(n=n.call(a);!(r=(o=n.next()).done)&&(t.push(o.value),!(e&&t.length===e));r=!0);}catch(c){i=!0,s=c}finally{try{!r&&n.return!=null&&n.return()}finally{if(i)throw s}}return t}}function Fe(a,e){if(a){if(typeof a=="string")return _a(a,e);var n=Object.prototype.toString.call(a).slice(8,-1);if(n==="Object"&&a.constructor&&(n=a.constructor.name),n==="Map"||n==="Set")return Array.from(a);if(n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return _a(a,e)}}function _a(a,e){(e==null||e>a.length)&&(e=a.length);for(var n=0,t=new Array(e);n<e;n++)t[n]=a[n];return t}function zn(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function An(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var ue=function(){},Ka={},Re={},De=null,je={mark:ue,measure:ue};try{typeof window<"u"&&(Ka=window),typeof document<"u"&&(Re=document),typeof MutationObserver<"u"&&(De=MutationObserver),typeof performance<"u"&&(je=performance)}catch{}var Cn=Ka.navigator||{},me=Cn.userAgent,ve=me===void 0?"":me,j=Ka,x=Re,de=De,ua=je;j.document;var F=!!x.documentElement&&!!x.head&&typeof x.addEventListener=="function"&&typeof x.createElement=="function",$e=~ve.indexOf("MSIE")||~ve.indexOf("Trident/"),ma,va,da,pa,ba,I="___FONT_AWESOME___",Ta=16,Ye="fa",Ue="svg-inline--fa",G="data-fa-i2svg",Fa="data-fa-pseudo-element",Hn="data-fa-pseudo-element-pending",Qa="data-prefix",Za="data-icon",pe="fontawesome-i2svg",Mn="async",Sn=["HTML","HEAD","STYLE","SCRIPT"],Be=function(){try{return!1}catch{return!1}}(),y="classic",k="sharp",Ja=[y,k];function fa(a){return new Proxy(a,{get:function(n,t){return t in n?n[t]:n[y]}})}var ta=fa((ma={},A(ma,y,{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fad:"duotone","fa-duotone":"duotone",fab:"brands","fa-brands":"brands",fak:"kit","fa-kit":"kit"}),A(ma,k,{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light"}),ma)),ra=fa((va={},A(va,y,{solid:"fas",regular:"far",light:"fal",thin:"fat",duotone:"fad",brands:"fab",kit:"fak"}),A(va,k,{solid:"fass",regular:"fasr",light:"fasl"}),va)),ia=fa((da={},A(da,y,{fab:"fa-brands",fad:"fa-duotone",fak:"fa-kit",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"}),A(da,k,{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light"}),da)),On=fa((pa={},A(pa,y,{"fa-brands":"fab","fa-duotone":"fad","fa-kit":"fak","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"}),A(pa,k,{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl"}),pa)),Nn=/fa(s|r|l|t|d|b|k|ss|sr|sl)?[\-\ ]/,We="fa-layers-text",Vn=/Font ?Awesome ?([56 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp|Kit)?.*/i,Ln=fa((ba={},A(ba,y,{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"}),A(ba,k,{900:"fass",400:"fasr",300:"fasl"}),ba)),Ge=[1,2,3,4,5,6,7,8,9,10],Pn=Ge.concat([11,12,13,14,15,16,17,18,19,20]),En=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],B={GROUP:"duotone-group",SWAP_OPACITY:"swap-opacity",PRIMARY:"primary",SECONDARY:"secondary"},oa=new Set;Object.keys(ra[y]).map(oa.add.bind(oa));Object.keys(ra[k]).map(oa.add.bind(oa));var In=[].concat(Ja,ca(oa),["2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","fw","inverse","layers-counter","layers-text","layers","li","pull-left","pull-right","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul",B.GROUP,B.SWAP_OPACITY,B.PRIMARY,B.SECONDARY]).concat(Ge.map(function(a){return"".concat(a,"x")})).concat(Pn.map(function(a){return"w-".concat(a)})),ea=j.FontAwesomeConfig||{};function _n(a){var e=x.querySelector("script["+a+"]");if(e)return e.getAttribute(a)}function Tn(a){return a===""?!0:a==="false"?!1:a==="true"?!0:a}if(x&&typeof x.querySelector=="function"){var Fn=[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-auto-a11y","autoA11y"],["data-search-pseudo-elements","searchPseudoElements"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]];Fn.forEach(function(a){var e=qa(a,2),n=e[0],t=e[1],r=Tn(_n(n));r!=null&&(ea[t]=r)})}var Xe={styleDefault:"solid",familyDefault:"classic",cssPrefix:Ye,replacementClass:Ue,autoReplaceSvg:!0,autoAddCss:!0,autoA11y:!0,searchPseudoElements:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};ea.familyPrefix&&(ea.cssPrefix=ea.familyPrefix);var Z=u(u({},Xe),ea);Z.autoReplaceSvg||(Z.observeMutations=!1);var m={};Object.keys(Xe).forEach(function(a){Object.defineProperty(m,a,{enumerable:!0,set:function(n){Z[a]=n,na.forEach(function(t){return t(m)})},get:function(){return Z[a]}})});Object.defineProperty(m,"familyPrefix",{enumerable:!0,set:function(e){Z.cssPrefix=e,na.forEach(function(n){return n(m)})},get:function(){return Z.cssPrefix}});j.FontAwesomeConfig=m;var na=[];function Rn(a){return na.push(a),function(){na.splice(na.indexOf(a),1)}}var D=Ta,P={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function Dn(a){if(!(!a||!F)){var e=x.createElement("style");e.setAttribute("type","text/css"),e.innerHTML=a;for(var n=x.head.childNodes,t=null,r=n.length-1;r>-1;r--){var i=n[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(t=i)}return x.head.insertBefore(e,t),a}}var jn="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";function sa(){for(var a=12,e="";a-- >0;)e+=jn[Math.random()*62|0];return e}function J(a){for(var e=[],n=(a||[]).length>>>0;n--;)e[n]=a[n];return e}function ae(a){return a.classList?J(a.classList):(a.getAttribute("class")||"").split(" ").filter(function(e){return e})}function qe(a){return"".concat(a).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function $n(a){return Object.keys(a||{}).reduce(function(e,n){return e+"".concat(n,'="').concat(qe(a[n]),'" ')},"").trim()}function Ha(a){return Object.keys(a||{}).reduce(function(e,n){return e+"".concat(n,": ").concat(a[n].trim(),";")},"")}function ee(a){return a.size!==P.size||a.x!==P.x||a.y!==P.y||a.rotate!==P.rotate||a.flipX||a.flipY}function Yn(a){var e=a.transform,n=a.containerWidth,t=a.iconWidth,r={transform:"translate(".concat(n/2," 256)")},i="translate(".concat(e.x*32,", ").concat(e.y*32,") "),o="scale(".concat(e.size/16*(e.flipX?-1:1),", ").concat(e.size/16*(e.flipY?-1:1),") "),s="rotate(".concat(e.rotate," 0 0)"),c={transform:"".concat(i," ").concat(o," ").concat(s)},l={transform:"translate(".concat(t/2*-1," -256)")};return{outer:r,inner:c,path:l}}function Un(a){var e=a.transform,n=a.width,t=n===void 0?Ta:n,r=a.height,i=r===void 0?Ta:r,o=a.startCentered,s=o===void 0?!1:o,c="";return s&&$e?c+="translate(".concat(e.x/D-t/2,"em, ").concat(e.y/D-i/2,"em) "):s?c+="translate(calc(-50% + ".concat(e.x/D,"em), calc(-50% + ").concat(e.y/D,"em)) "):c+="translate(".concat(e.x/D,"em, ").concat(e.y/D,"em) "),c+="scale(".concat(e.size/D*(e.flipX?-1:1),", ").concat(e.size/D*(e.flipY?-1:1),") "),c+="rotate(".concat(e.rotate,"deg) "),c}var Bn=`:root, :host {
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
}`;function Ke(){var a=Ye,e=Ue,n=m.cssPrefix,t=m.replacementClass,r=Bn;if(n!==a||t!==e){var i=new RegExp("\\.".concat(a,"\\-"),"g"),o=new RegExp("\\--".concat(a,"\\-"),"g"),s=new RegExp("\\.".concat(e),"g");r=r.replace(i,".".concat(n,"-")).replace(o,"--".concat(n,"-")).replace(s,".".concat(t))}return r}var be=!1;function Va(){m.autoAddCss&&!be&&(Dn(Ke()),be=!0)}var Wn={mixout:function(){return{dom:{css:Ke,insertCss:Va}}},hooks:function(){return{beforeDOMElementCreation:function(){Va()},beforeI2svg:function(){Va()}}}},_=j||{};_[I]||(_[I]={});_[I].styles||(_[I].styles={});_[I].hooks||(_[I].hooks={});_[I].shims||(_[I].shims=[]);var V=_[I],Qe=[],Gn=function a(){x.removeEventListener("DOMContentLoaded",a),za=1,Qe.map(function(e){return e()})},za=!1;F&&(za=(x.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(x.readyState),za||x.addEventListener("DOMContentLoaded",Gn));function Xn(a){F&&(za?setTimeout(a,0):Qe.push(a))}function la(a){var e=a.tag,n=a.attributes,t=n===void 0?{}:n,r=a.children,i=r===void 0?[]:r;return typeof a=="string"?qe(a):"<".concat(e," ").concat($n(t),">").concat(i.map(la).join(""),"</").concat(e,">")}function ge(a,e,n){if(a&&a[e]&&a[e][n])return{prefix:e,iconName:n,icon:a[e][n]}}var qn=function(e,n){return function(t,r,i,o){return e.call(n,t,r,i,o)}},La=function(e,n,t,r){var i=Object.keys(e),o=i.length,s=r!==void 0?qn(n,r):n,c,l,f;for(t===void 0?(c=1,f=e[i[0]]):(c=0,f=t);c<o;c++)l=i[c],f=s(f,e[l],l,e);return f};function Kn(a){for(var e=[],n=0,t=a.length;n<t;){var r=a.charCodeAt(n++);if(r>=55296&&r<=56319&&n<t){var i=a.charCodeAt(n++);(i&64512)==56320?e.push(((r&1023)<<10)+(i&1023)+65536):(e.push(r),n--)}else e.push(r)}return e}function Ra(a){var e=Kn(a);return e.length===1?e[0].toString(16):null}function Qn(a,e){var n=a.length,t=a.charCodeAt(e),r;return t>=55296&&t<=56319&&n>e+1&&(r=a.charCodeAt(e+1),r>=56320&&r<=57343)?(t-55296)*1024+r-56320+65536:t}function he(a){return Object.keys(a).reduce(function(e,n){var t=a[n],r=!!t.icon;return r?e[t.iconName]=t.icon:e[n]=t,e},{})}function Da(a,e){var n=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{},t=n.skipHooks,r=t===void 0?!1:t,i=he(e);typeof V.hooks.addPack=="function"&&!r?V.hooks.addPack(a,he(e)):V.styles[a]=u(u({},V.styles[a]||{}),i),a==="fas"&&Da("fa",e)}var ga,ha,ya,q=V.styles,Zn=V.shims,Jn=(ga={},A(ga,y,Object.values(ia[y])),A(ga,k,Object.values(ia[k])),ga),ne=null,Ze={},Je={},an={},en={},nn={},at=(ha={},A(ha,y,Object.keys(ta[y])),A(ha,k,Object.keys(ta[k])),ha);function et(a){return~In.indexOf(a)}function nt(a,e){var n=e.split("-"),t=n[0],r=n.slice(1).join("-");return t===a&&r!==""&&!et(r)?r:null}var tn=function(){var e=function(i){return La(q,function(o,s,c){return o[c]=La(s,i,{}),o},{})};Ze=e(function(r,i,o){if(i[3]&&(r[i[3]]=o),i[2]){var s=i[2].filter(function(c){return typeof c=="number"});s.forEach(function(c){r[c.toString(16)]=o})}return r}),Je=e(function(r,i,o){if(r[o]=o,i[2]){var s=i[2].filter(function(c){return typeof c=="string"});s.forEach(function(c){r[c]=o})}return r}),nn=e(function(r,i,o){var s=i[2];return r[o]=o,s.forEach(function(c){r[c]=o}),r});var n="far"in q||m.autoFetchSvg,t=La(Zn,function(r,i){var o=i[0],s=i[1],c=i[2];return s==="far"&&!n&&(s="fas"),typeof o=="string"&&(r.names[o]={prefix:s,iconName:c}),typeof o=="number"&&(r.unicodes[o.toString(16)]={prefix:s,iconName:c}),r},{names:{},unicodes:{}});an=t.names,en=t.unicodes,ne=Ma(m.styleDefault,{family:m.familyDefault})};Rn(function(a){ne=Ma(a.styleDefault,{family:m.familyDefault})});tn();function te(a,e){return(Ze[a]||{})[e]}function tt(a,e){return(Je[a]||{})[e]}function W(a,e){return(nn[a]||{})[e]}function rn(a){return an[a]||{prefix:null,iconName:null}}function rt(a){var e=en[a],n=te("fas",a);return e||(n?{prefix:"fas",iconName:n}:null)||{prefix:null,iconName:null}}function $(){return ne}var re=function(){return{prefix:null,iconName:null,rest:[]}};function Ma(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=e.family,t=n===void 0?y:n,r=ta[t][a],i=ra[t][a]||ra[t][r],o=a in V.styles?a:null;return i||o||null}var ye=(ya={},A(ya,y,Object.keys(ia[y])),A(ya,k,Object.keys(ia[k])),ya);function Sa(a){var e,n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.skipLookups,r=t===void 0?!1:t,i=(e={},A(e,y,"".concat(m.cssPrefix,"-").concat(y)),A(e,k,"".concat(m.cssPrefix,"-").concat(k)),e),o=null,s=y;(a.includes(i[y])||a.some(function(l){return ye[y].includes(l)}))&&(s=y),(a.includes(i[k])||a.some(function(l){return ye[k].includes(l)}))&&(s=k);var c=a.reduce(function(l,f){var v=nt(m.cssPrefix,f);if(q[f]?(f=Jn[s].includes(f)?On[s][f]:f,o=f,l.prefix=f):at[s].indexOf(f)>-1?(o=f,l.prefix=Ma(f,{family:s})):v?l.iconName=v:f!==m.replacementClass&&f!==i[y]&&f!==i[k]&&l.rest.push(f),!r&&l.prefix&&l.iconName){var b=o==="fa"?rn(l.iconName):{},g=W(l.prefix,l.iconName);b.prefix&&(o=null),l.iconName=b.iconName||g||l.iconName,l.prefix=b.prefix||l.prefix,l.prefix==="far"&&!q.far&&q.fas&&!m.autoFetchSvg&&(l.prefix="fas")}return l},re());return(a.includes("fa-brands")||a.includes("fab"))&&(c.prefix="fab"),(a.includes("fa-duotone")||a.includes("fad"))&&(c.prefix="fad"),!c.prefix&&s===k&&(q.fass||m.autoFetchSvg)&&(c.prefix="fass",c.iconName=W(c.prefix,c.iconName)||c.iconName),(c.prefix==="fa"||o==="fa")&&(c.prefix=$()||"fas"),c}var it=function(){function a(){gn(this,a),this.definitions={}}return hn(a,[{key:"add",value:function(){for(var n=this,t=arguments.length,r=new Array(t),i=0;i<t;i++)r[i]=arguments[i];var o=r.reduce(this._pullDefinitions,{});Object.keys(o).forEach(function(s){n.definitions[s]=u(u({},n.definitions[s]||{}),o[s]),Da(s,o[s]);var c=ia[y][s];c&&Da(c,o[s]),tn()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(n,t){var r=t.prefix&&t.iconName&&t.icon?{0:t}:t;return Object.keys(r).map(function(i){var o=r[i],s=o.prefix,c=o.iconName,l=o.icon,f=l[2];n[s]||(n[s]={}),f.length>0&&f.forEach(function(v){typeof v=="string"&&(n[s][v]=l)}),n[s][c]=l}),n}}]),a}(),xe=[],K={},Q={},ot=Object.keys(Q);function st(a,e){var n=e.mixoutsTo;return xe=a,K={},Object.keys(Q).forEach(function(t){ot.indexOf(t)===-1&&delete Q[t]}),xe.forEach(function(t){var r=t.mixout?t.mixout():{};if(Object.keys(r).forEach(function(o){typeof r[o]=="function"&&(n[o]=r[o]),wa(r[o])==="object"&&Object.keys(r[o]).forEach(function(s){n[o]||(n[o]={}),n[o][s]=r[o][s]})}),t.hooks){var i=t.hooks();Object.keys(i).forEach(function(o){K[o]||(K[o]=[]),K[o].push(i[o])})}t.provides&&t.provides(Q)}),n}function ja(a,e){for(var n=arguments.length,t=new Array(n>2?n-2:0),r=2;r<n;r++)t[r-2]=arguments[r];var i=K[a]||[];return i.forEach(function(o){e=o.apply(null,[e].concat(t))}),e}function X(a){for(var e=arguments.length,n=new Array(e>1?e-1:0),t=1;t<e;t++)n[t-1]=arguments[t];var r=K[a]||[];r.forEach(function(i){i.apply(null,n)})}function T(){var a=arguments[0],e=Array.prototype.slice.call(arguments,1);return Q[a]?Q[a].apply(null,e):void 0}function $a(a){a.prefix==="fa"&&(a.prefix="fas");var e=a.iconName,n=a.prefix||$();if(e)return e=W(n,e)||e,ge(on.definitions,n,e)||ge(V.styles,n,e)}var on=new it,ct=function(){m.autoReplaceSvg=!1,m.observeMutations=!1,X("noAuto")},ft={i2svg:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return F?(X("beforeI2svg",e),T("pseudoElements2svg",e),T("i2svg",e)):Promise.reject("Operation requires a DOM of some kind.")},watch:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=e.autoReplaceSvgRoot;m.autoReplaceSvg===!1&&(m.autoReplaceSvg=!0),m.observeMutations=!0,Xn(function(){ut({autoReplaceSvgRoot:n}),X("watch",e)})}},lt={icon:function(e){if(e===null)return null;if(wa(e)==="object"&&e.prefix&&e.iconName)return{prefix:e.prefix,iconName:W(e.prefix,e.iconName)||e.iconName};if(Array.isArray(e)&&e.length===2){var n=e[1].indexOf("fa-")===0?e[1].slice(3):e[1],t=Ma(e[0]);return{prefix:t,iconName:W(t,n)||n}}if(typeof e=="string"&&(e.indexOf("".concat(m.cssPrefix,"-"))>-1||e.match(Nn))){var r=Sa(e.split(" "),{skipLookups:!0});return{prefix:r.prefix||$(),iconName:W(r.prefix,r.iconName)||r.iconName}}if(typeof e=="string"){var i=$();return{prefix:i,iconName:W(i,e)||e}}}},O={noAuto:ct,config:m,dom:ft,parse:lt,library:on,findIconDefinition:$a,toHtml:la},ut=function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=e.autoReplaceSvgRoot,t=n===void 0?x:n;(Object.keys(V.styles).length>0||m.autoFetchSvg)&&F&&m.autoReplaceSvg&&O.dom.i2svg({node:t})};function Oa(a,e){return Object.defineProperty(a,"abstract",{get:e}),Object.defineProperty(a,"html",{get:function(){return a.abstract.map(function(t){return la(t)})}}),Object.defineProperty(a,"node",{get:function(){if(F){var t=x.createElement("div");return t.innerHTML=a.html,t.children}}}),a}function mt(a){var e=a.children,n=a.main,t=a.mask,r=a.attributes,i=a.styles,o=a.transform;if(ee(o)&&n.found&&!t.found){var s=n.width,c=n.height,l={x:s/c/2,y:.5};r.style=Ha(u(u({},i),{},{"transform-origin":"".concat(l.x+o.x/16,"em ").concat(l.y+o.y/16,"em")}))}return[{tag:"svg",attributes:r,children:e}]}function vt(a){var e=a.prefix,n=a.iconName,t=a.children,r=a.attributes,i=a.symbol,o=i===!0?"".concat(e,"-").concat(m.cssPrefix,"-").concat(n):i;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:u(u({},r),{},{id:o}),children:t}]}]}function ie(a){var e=a.icons,n=e.main,t=e.mask,r=a.prefix,i=a.iconName,o=a.transform,s=a.symbol,c=a.title,l=a.maskId,f=a.titleId,v=a.extra,b=a.watchable,g=b===void 0?!1:b,C=t.found?t:n,H=C.width,M=C.height,d=r==="fak",p=[m.replacementClass,i?"".concat(m.cssPrefix,"-").concat(i):""].filter(function(R){return v.classes.indexOf(R)===-1}).filter(function(R){return R!==""||!!R}).concat(v.classes).join(" "),h={children:[],attributes:u(u({},v.attributes),{},{"data-prefix":r,"data-icon":i,class:p,role:v.attributes.role||"img",xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 ".concat(H," ").concat(M)})},w=d&&!~v.classes.indexOf("fa-fw")?{width:"".concat(H/M*16*.0625,"em")}:{};g&&(h.attributes[G]=""),c&&(h.children.push({tag:"title",attributes:{id:h.attributes["aria-labelledby"]||"title-".concat(f||sa())},children:[c]}),delete h.attributes.title);var z=u(u({},h),{},{prefix:r,iconName:i,main:n,mask:t,maskId:l,transform:o,symbol:s,styles:u(u({},w),v.styles)}),L=t.found&&n.found?T("generateAbstractMask",z)||{children:[],attributes:{}}:T("generateAbstractIcon",z)||{children:[],attributes:{}},N=L.children,Na=L.attributes;return z.children=N,z.attributes=Na,s?vt(z):mt(z)}function ke(a){var e=a.content,n=a.width,t=a.height,r=a.transform,i=a.title,o=a.extra,s=a.watchable,c=s===void 0?!1:s,l=u(u(u({},o.attributes),i?{title:i}:{}),{},{class:o.classes.join(" ")});c&&(l[G]="");var f=u({},o.styles);ee(r)&&(f.transform=Un({transform:r,startCentered:!0,width:n,height:t}),f["-webkit-transform"]=f.transform);var v=Ha(f);v.length>0&&(l.style=v);var b=[];return b.push({tag:"span",attributes:l,children:[e]}),i&&b.push({tag:"span",attributes:{class:"sr-only"},children:[i]}),b}function dt(a){var e=a.content,n=a.title,t=a.extra,r=u(u(u({},t.attributes),n?{title:n}:{}),{},{class:t.classes.join(" ")}),i=Ha(t.styles);i.length>0&&(r.style=i);var o=[];return o.push({tag:"span",attributes:r,children:[e]}),n&&o.push({tag:"span",attributes:{class:"sr-only"},children:[n]}),o}var Pa=V.styles;function Ya(a){var e=a[0],n=a[1],t=a.slice(4),r=qa(t,1),i=r[0],o=null;return Array.isArray(i)?o={tag:"g",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.GROUP)},children:[{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.SECONDARY),fill:"currentColor",d:i[0]}},{tag:"path",attributes:{class:"".concat(m.cssPrefix,"-").concat(B.PRIMARY),fill:"currentColor",d:i[1]}}]}:o={tag:"path",attributes:{fill:"currentColor",d:i}},{found:!0,width:e,height:n,icon:o}}var pt={found:!1,width:512,height:512};function bt(a,e){!Be&&!m.showMissingIcons&&a&&console.error('Icon with name "'.concat(a,'" and prefix "').concat(e,'" is missing.'))}function Ua(a,e){var n=e;return e==="fa"&&m.styleDefault!==null&&(e=$()),new Promise(function(t,r){if(T("missingIconAbstract"),n==="fa"){var i=rn(a)||{};a=i.iconName||a,e=i.prefix||e}if(a&&e&&Pa[e]&&Pa[e][a]){var o=Pa[e][a];return t(Ya(o))}bt(a,e),t(u(u({},pt),{},{icon:m.showMissingIcons&&a?T("missingIconAbstract")||{}:{}}))})}var we=function(){},Ba=m.measurePerformance&&ua&&ua.mark&&ua.measure?ua:{mark:we,measure:we},aa='FA "6.4.0"',gt=function(e){return Ba.mark("".concat(aa," ").concat(e," begins")),function(){return sn(e)}},sn=function(e){Ba.mark("".concat(aa," ").concat(e," ends")),Ba.measure("".concat(aa," ").concat(e),"".concat(aa," ").concat(e," begins"),"".concat(aa," ").concat(e," ends"))},oe={begin:gt,end:sn},xa=function(){};function ze(a){var e=a.getAttribute?a.getAttribute(G):null;return typeof e=="string"}function ht(a){var e=a.getAttribute?a.getAttribute(Qa):null,n=a.getAttribute?a.getAttribute(Za):null;return e&&n}function yt(a){return a&&a.classList&&a.classList.contains&&a.classList.contains(m.replacementClass)}function xt(){if(m.autoReplaceSvg===!0)return ka.replace;var a=ka[m.autoReplaceSvg];return a||ka.replace}function kt(a){return x.createElementNS("http://www.w3.org/2000/svg",a)}function wt(a){return x.createElement(a)}function cn(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=e.ceFn,t=n===void 0?a.tag==="svg"?kt:wt:n;if(typeof a=="string")return x.createTextNode(a);var r=t(a.tag);Object.keys(a.attributes||[]).forEach(function(o){r.setAttribute(o,a.attributes[o])});var i=a.children||[];return i.forEach(function(o){r.appendChild(cn(o,{ceFn:t}))}),r}function zt(a){var e=" ".concat(a.outerHTML," ");return e="".concat(e,"Font Awesome fontawesome.com "),e}var ka={replace:function(e){var n=e[0];if(n.parentNode)if(e[1].forEach(function(r){n.parentNode.insertBefore(cn(r),n)}),n.getAttribute(G)===null&&m.keepOriginalSource){var t=x.createComment(zt(n));n.parentNode.replaceChild(t,n)}else n.remove()},nest:function(e){var n=e[0],t=e[1];if(~ae(n).indexOf(m.replacementClass))return ka.replace(e);var r=new RegExp("".concat(m.cssPrefix,"-.*"));if(delete t[0].attributes.id,t[0].attributes.class){var i=t[0].attributes.class.split(" ").reduce(function(s,c){return c===m.replacementClass||c.match(r)?s.toSvg.push(c):s.toNode.push(c),s},{toNode:[],toSvg:[]});t[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?n.removeAttribute("class"):n.setAttribute("class",i.toNode.join(" "))}var o=t.map(function(s){return la(s)}).join(`
`);n.setAttribute(G,""),n.innerHTML=o}};function Ae(a){a()}function fn(a,e){var n=typeof e=="function"?e:xa;if(a.length===0)n();else{var t=Ae;m.mutateApproach===Mn&&(t=j.requestAnimationFrame||Ae),t(function(){var r=xt(),i=oe.begin("mutate");a.map(r),i(),n()})}}var se=!1;function ln(){se=!0}function Wa(){se=!1}var Aa=null;function Ce(a){if(de&&m.observeMutations){var e=a.treeCallback,n=e===void 0?xa:e,t=a.nodeCallback,r=t===void 0?xa:t,i=a.pseudoElementsCallback,o=i===void 0?xa:i,s=a.observeMutationsRoot,c=s===void 0?x:s;Aa=new de(function(l){if(!se){var f=$();J(l).forEach(function(v){if(v.type==="childList"&&v.addedNodes.length>0&&!ze(v.addedNodes[0])&&(m.searchPseudoElements&&o(v.target),n(v.target)),v.type==="attributes"&&v.target.parentNode&&m.searchPseudoElements&&o(v.target.parentNode),v.type==="attributes"&&ze(v.target)&&~En.indexOf(v.attributeName))if(v.attributeName==="class"&&ht(v.target)){var b=Sa(ae(v.target)),g=b.prefix,C=b.iconName;v.target.setAttribute(Qa,g||f),C&&v.target.setAttribute(Za,C)}else yt(v.target)&&r(v.target)})}}),F&&Aa.observe(c,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function At(){Aa&&Aa.disconnect()}function Ct(a){var e=a.getAttribute("style"),n=[];return e&&(n=e.split(";").reduce(function(t,r){var i=r.split(":"),o=i[0],s=i.slice(1);return o&&s.length>0&&(t[o]=s.join(":").trim()),t},{})),n}function Ht(a){var e=a.getAttribute("data-prefix"),n=a.getAttribute("data-icon"),t=a.innerText!==void 0?a.innerText.trim():"",r=Sa(ae(a));return r.prefix||(r.prefix=$()),e&&n&&(r.prefix=e,r.iconName=n),r.iconName&&r.prefix||(r.prefix&&t.length>0&&(r.iconName=tt(r.prefix,a.innerText)||te(r.prefix,Ra(a.innerText))),!r.iconName&&m.autoFetchSvg&&a.firstChild&&a.firstChild.nodeType===Node.TEXT_NODE&&(r.iconName=a.firstChild.data)),r}function Mt(a){var e=J(a.attributes).reduce(function(r,i){return r.name!=="class"&&r.name!=="style"&&(r[i.name]=i.value),r},{}),n=a.getAttribute("title"),t=a.getAttribute("data-fa-title-id");return m.autoA11y&&(n?e["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(t||sa()):(e["aria-hidden"]="true",e.focusable="false")),e}function St(){return{iconName:null,title:null,titleId:null,prefix:null,transform:P,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}}}function He(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},n=Ht(a),t=n.iconName,r=n.prefix,i=n.rest,o=Mt(a),s=ja("parseNodeAttributes",{},a),c=e.styleParser?Ct(a):[];return u({iconName:t,title:a.getAttribute("title"),titleId:a.getAttribute("data-fa-title-id"),prefix:r,transform:P,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:i,styles:c,attributes:o}},s)}var Ot=V.styles;function un(a){var e=m.autoReplaceSvg==="nest"?He(a,{styleParser:!1}):He(a);return~e.extra.classes.indexOf(We)?T("generateLayersText",a,e):T("generateSvgReplacementMutation",a,e)}var Y=new Set;Ja.map(function(a){Y.add("fa-".concat(a))});Object.keys(ta[y]).map(Y.add.bind(Y));Object.keys(ta[k]).map(Y.add.bind(Y));Y=ca(Y);function Me(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!F)return Promise.resolve();var n=x.documentElement.classList,t=function(v){return n.add("".concat(pe,"-").concat(v))},r=function(v){return n.remove("".concat(pe,"-").concat(v))},i=m.autoFetchSvg?Y:Ja.map(function(f){return"fa-".concat(f)}).concat(Object.keys(Ot));i.includes("fa")||i.push("fa");var o=[".".concat(We,":not([").concat(G,"])")].concat(i.map(function(f){return".".concat(f,":not([").concat(G,"])")})).join(", ");if(o.length===0)return Promise.resolve();var s=[];try{s=J(a.querySelectorAll(o))}catch{}if(s.length>0)t("pending"),r("complete");else return Promise.resolve();var c=oe.begin("onTree"),l=s.reduce(function(f,v){try{var b=un(v);b&&f.push(b)}catch(g){Be||g.name==="MissingIcon"&&console.error(g)}return f},[]);return new Promise(function(f,v){Promise.all(l).then(function(b){fn(b,function(){t("active"),t("complete"),r("pending"),typeof e=="function"&&e(),c(),f()})}).catch(function(b){c(),v(b)})})}function Nt(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;un(a).then(function(n){n&&fn([n],e)})}function Vt(a){return function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=(e||{}).icon?e:$a(e||{}),r=n.mask;return r&&(r=(r||{}).icon?r:$a(r||{})),a(t,u(u({},n),{},{mask:r}))}}var Lt=function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=n.transform,r=t===void 0?P:t,i=n.symbol,o=i===void 0?!1:i,s=n.mask,c=s===void 0?null:s,l=n.maskId,f=l===void 0?null:l,v=n.title,b=v===void 0?null:v,g=n.titleId,C=g===void 0?null:g,H=n.classes,M=H===void 0?[]:H,d=n.attributes,p=d===void 0?{}:d,h=n.styles,w=h===void 0?{}:h;if(e){var z=e.prefix,L=e.iconName,N=e.icon;return Oa(u({type:"icon"},e),function(){return X("beforeDOMElementCreation",{iconDefinition:e,params:n}),m.autoA11y&&(b?p["aria-labelledby"]="".concat(m.replacementClass,"-title-").concat(C||sa()):(p["aria-hidden"]="true",p.focusable="false")),ie({icons:{main:Ya(N),mask:c?Ya(c.icon):{found:!1,width:null,height:null,icon:{}}},prefix:z,iconName:L,transform:u(u({},P),r),symbol:o,title:b,maskId:f,titleId:C,extra:{attributes:p,styles:w,classes:M}})})}},Pt={mixout:function(){return{icon:Vt(Lt)}},hooks:function(){return{mutationObserverCallbacks:function(n){return n.treeCallback=Me,n.nodeCallback=Nt,n}}},provides:function(e){e.i2svg=function(n){var t=n.node,r=t===void 0?x:t,i=n.callback,o=i===void 0?function(){}:i;return Me(r,o)},e.generateSvgReplacementMutation=function(n,t){var r=t.iconName,i=t.title,o=t.titleId,s=t.prefix,c=t.transform,l=t.symbol,f=t.mask,v=t.maskId,b=t.extra;return new Promise(function(g,C){Promise.all([Ua(r,s),f.iconName?Ua(f.iconName,f.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(H){var M=qa(H,2),d=M[0],p=M[1];g([n,ie({icons:{main:d,mask:p},prefix:s,iconName:r,transform:c,symbol:l,maskId:v,title:i,titleId:o,extra:b,watchable:!0})])}).catch(C)})},e.generateAbstractIcon=function(n){var t=n.children,r=n.attributes,i=n.main,o=n.transform,s=n.styles,c=Ha(s);c.length>0&&(r.style=c);var l;return ee(o)&&(l=T("generateAbstractTransformGrouping",{main:i,transform:o,containerWidth:i.width,iconWidth:i.width})),t.push(l||i.icon),{children:t,attributes:r}}}},Et={mixout:function(){return{layer:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.classes,i=r===void 0?[]:r;return Oa({type:"layer"},function(){X("beforeDOMElementCreation",{assembler:n,params:t});var o=[];return n(function(s){Array.isArray(s)?s.map(function(c){o=o.concat(c.abstract)}):o=o.concat(s.abstract)}),[{tag:"span",attributes:{class:["".concat(m.cssPrefix,"-layers")].concat(ca(i)).join(" ")},children:o}]})}}}},It={mixout:function(){return{counter:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.title,i=r===void 0?null:r,o=t.classes,s=o===void 0?[]:o,c=t.attributes,l=c===void 0?{}:c,f=t.styles,v=f===void 0?{}:f;return Oa({type:"counter",content:n},function(){return X("beforeDOMElementCreation",{content:n,params:t}),dt({content:n.toString(),title:i,extra:{attributes:l,styles:v,classes:["".concat(m.cssPrefix,"-layers-counter")].concat(ca(s))}})})}}}},_t={mixout:function(){return{text:function(n){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=t.transform,i=r===void 0?P:r,o=t.title,s=o===void 0?null:o,c=t.classes,l=c===void 0?[]:c,f=t.attributes,v=f===void 0?{}:f,b=t.styles,g=b===void 0?{}:b;return Oa({type:"text",content:n},function(){return X("beforeDOMElementCreation",{content:n,params:t}),ke({content:n,transform:u(u({},P),i),title:s,extra:{attributes:v,styles:g,classes:["".concat(m.cssPrefix,"-layers-text")].concat(ca(l))}})})}}},provides:function(e){e.generateLayersText=function(n,t){var r=t.title,i=t.transform,o=t.extra,s=null,c=null;if($e){var l=parseInt(getComputedStyle(n).fontSize,10),f=n.getBoundingClientRect();s=f.width/l,c=f.height/l}return m.autoA11y&&!r&&(o.attributes["aria-hidden"]="true"),Promise.resolve([n,ke({content:n.innerHTML,width:s,height:c,transform:i,title:r,extra:o,watchable:!0})])}}},Tt=new RegExp('"',"ug"),Se=[1105920,1112319];function Ft(a){var e=a.replace(Tt,""),n=Qn(e,0),t=n>=Se[0]&&n<=Se[1],r=e.length===2?e[0]===e[1]:!1;return{value:Ra(r?e[0]:e),isSecondary:t||r}}function Oe(a,e){var n="".concat(Hn).concat(e.replace(":","-"));return new Promise(function(t,r){if(a.getAttribute(n)!==null)return t();var i=J(a.children),o=i.filter(function(N){return N.getAttribute(Fa)===e})[0],s=j.getComputedStyle(a,e),c=s.getPropertyValue("font-family").match(Vn),l=s.getPropertyValue("font-weight"),f=s.getPropertyValue("content");if(o&&!c)return a.removeChild(o),t();if(c&&f!=="none"&&f!==""){var v=s.getPropertyValue("content"),b=~["Sharp"].indexOf(c[2])?k:y,g=~["Solid","Regular","Light","Thin","Duotone","Brands","Kit"].indexOf(c[2])?ra[b][c[2].toLowerCase()]:Ln[b][l],C=Ft(v),H=C.value,M=C.isSecondary,d=c[0].startsWith("FontAwesome"),p=te(g,H),h=p;if(d){var w=rt(H);w.iconName&&w.prefix&&(p=w.iconName,g=w.prefix)}if(p&&!M&&(!o||o.getAttribute(Qa)!==g||o.getAttribute(Za)!==h)){a.setAttribute(n,h),o&&a.removeChild(o);var z=St(),L=z.extra;L.attributes[Fa]=e,Ua(p,g).then(function(N){var Na=ie(u(u({},z),{},{icons:{main:N,mask:re()},prefix:g,iconName:h,extra:L,watchable:!0})),R=x.createElement("svg");e==="::before"?a.insertBefore(R,a.firstChild):a.appendChild(R),R.outerHTML=Na.map(function(pn){return la(pn)}).join(`
`),a.removeAttribute(n),t()}).catch(r)}else t()}else t()})}function Rt(a){return Promise.all([Oe(a,"::before"),Oe(a,"::after")])}function Dt(a){return a.parentNode!==document.head&&!~Sn.indexOf(a.tagName.toUpperCase())&&!a.getAttribute(Fa)&&(!a.parentNode||a.parentNode.tagName!=="svg")}function Ne(a){if(F)return new Promise(function(e,n){var t=J(a.querySelectorAll("*")).filter(Dt).map(Rt),r=oe.begin("searchPseudoElements");ln(),Promise.all(t).then(function(){r(),Wa(),e()}).catch(function(){r(),Wa(),n()})})}var jt={hooks:function(){return{mutationObserverCallbacks:function(n){return n.pseudoElementsCallback=Ne,n}}},provides:function(e){e.pseudoElements2svg=function(n){var t=n.node,r=t===void 0?x:t;m.searchPseudoElements&&Ne(r)}}},Ve=!1,$t={mixout:function(){return{dom:{unwatch:function(){ln(),Ve=!0}}}},hooks:function(){return{bootstrap:function(){Ce(ja("mutationObserverCallbacks",{}))},noAuto:function(){At()},watch:function(n){var t=n.observeMutationsRoot;Ve?Wa():Ce(ja("mutationObserverCallbacks",{observeMutationsRoot:t}))}}}},Le=function(e){var n={size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0};return e.toLowerCase().split(" ").reduce(function(t,r){var i=r.toLowerCase().split("-"),o=i[0],s=i.slice(1).join("-");if(o&&s==="h")return t.flipX=!0,t;if(o&&s==="v")return t.flipY=!0,t;if(s=parseFloat(s),isNaN(s))return t;switch(o){case"grow":t.size=t.size+s;break;case"shrink":t.size=t.size-s;break;case"left":t.x=t.x-s;break;case"right":t.x=t.x+s;break;case"up":t.y=t.y-s;break;case"down":t.y=t.y+s;break;case"rotate":t.rotate=t.rotate+s;break}return t},n)},Yt={mixout:function(){return{parse:{transform:function(n){return Le(n)}}}},hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-transform");return r&&(n.transform=Le(r)),n}}},provides:function(e){e.generateAbstractTransformGrouping=function(n){var t=n.main,r=n.transform,i=n.containerWidth,o=n.iconWidth,s={transform:"translate(".concat(i/2," 256)")},c="translate(".concat(r.x*32,", ").concat(r.y*32,") "),l="scale(".concat(r.size/16*(r.flipX?-1:1),", ").concat(r.size/16*(r.flipY?-1:1),") "),f="rotate(".concat(r.rotate," 0 0)"),v={transform:"".concat(c," ").concat(l," ").concat(f)},b={transform:"translate(".concat(o/2*-1," -256)")},g={outer:s,inner:v,path:b};return{tag:"g",attributes:u({},g.outer),children:[{tag:"g",attributes:u({},g.inner),children:[{tag:t.icon.tag,children:t.icon.children,attributes:u(u({},t.icon.attributes),g.path)}]}]}}}},Ea={x:0,y:0,width:"100%",height:"100%"};function Pe(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!0;return a.attributes&&(a.attributes.fill||e)&&(a.attributes.fill="black"),a}function Ut(a){return a.tag==="g"?a.children:[a]}var Bt={hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-mask"),i=r?Sa(r.split(" ").map(function(o){return o.trim()})):re();return i.prefix||(i.prefix=$()),n.mask=i,n.maskId=t.getAttribute("data-fa-mask-id"),n}}},provides:function(e){e.generateAbstractMask=function(n){var t=n.children,r=n.attributes,i=n.main,o=n.mask,s=n.maskId,c=n.transform,l=i.width,f=i.icon,v=o.width,b=o.icon,g=Yn({transform:c,containerWidth:v,iconWidth:l}),C={tag:"rect",attributes:u(u({},Ea),{},{fill:"white"})},H=f.children?{children:f.children.map(Pe)}:{},M={tag:"g",attributes:u({},g.inner),children:[Pe(u({tag:f.tag,attributes:u(u({},f.attributes),g.path)},H))]},d={tag:"g",attributes:u({},g.outer),children:[M]},p="mask-".concat(s||sa()),h="clip-".concat(s||sa()),w={tag:"mask",attributes:u(u({},Ea),{},{id:p,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[C,d]},z={tag:"defs",children:[{tag:"clipPath",attributes:{id:h},children:Ut(b)},w]};return t.push(z,{tag:"rect",attributes:u({fill:"currentColor","clip-path":"url(#".concat(h,")"),mask:"url(#".concat(p,")")},Ea)}),{children:t,attributes:r}}}},Wt={provides:function(e){var n=!1;j.matchMedia&&(n=j.matchMedia("(prefers-reduced-motion: reduce)").matches),e.missingIconAbstract=function(){var t=[],r={fill:"currentColor"},i={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};t.push({tag:"path",attributes:u(u({},r),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var o=u(u({},i),{},{attributeName:"opacity"}),s={tag:"circle",attributes:u(u({},r),{},{cx:"256",cy:"364",r:"28"}),children:[]};return n||s.children.push({tag:"animate",attributes:u(u({},i),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:u(u({},o),{},{values:"1;0;1;1;0;1;"})}),t.push(s),t.push({tag:"path",attributes:u(u({},r),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:n?[]:[{tag:"animate",attributes:u(u({},o),{},{values:"1;0;0;0;0;1;"})}]}),n||t.push({tag:"path",attributes:u(u({},r),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:u(u({},o),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:t}}}},Gt={hooks:function(){return{parseNodeAttributes:function(n,t){var r=t.getAttribute("data-fa-symbol"),i=r===null?!1:r===""?!0:r;return n.symbol=i,n}}}},Xt=[Wn,Pt,Et,It,_t,jt,$t,Yt,Bt,Wt,Gt];st(Xt,{mixoutsTo:O});O.noAuto;var qt=O.config,Or=O.library;O.dom;var Ga=O.parse;O.findIconDefinition;O.toHtml;var Kt=O.icon;O.layer;O.text;O.counter;var Qt={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm64 80v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm128 0v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H208c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H336zM64 400v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H80c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H208zm112 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V400c0-8.8-7.2-16-16-16H336c-8.8 0-16 7.2-16 16z"]},Nr=Qt,Zt={prefix:"fas",iconName:"forward-step",icon:[320,512,["step-forward"],"f051","M52.5 440.6c-9.5 7.9-22.8 9.7-34.1 4.4S0 428.4 0 416V96C0 83.6 7.2 72.3 18.4 67s24.5-3.6 34.1 4.4l192 160L256 241V96c0-17.7 14.3-32 32-32s32 14.3 32 32V416c0 17.7-14.3 32-32 32s-32-14.3-32-32V271l-11.5 9.6-192 160z"]},Vr=Zt,Jt={prefix:"fas",iconName:"box-archive",icon:[512,512,["archive"],"f187","M32 32H480c17.7 0 32 14.3 32 32V96c0 17.7-14.3 32-32 32H32C14.3 128 0 113.7 0 96V64C0 46.3 14.3 32 32 32zm0 128H480V416c0 35.3-28.7 64-64 64H96c-35.3 0-64-28.7-64-64V160zm128 80c0 8.8 7.2 16 16 16H336c8.8 0 16-7.2 16-16s-7.2-16-16-16H176c-8.8 0-16 7.2-16 16z"]},Lr=Jt,Pr={prefix:"fas",iconName:"lock",icon:[448,512,[128274],"f023","M144 144v48H304V144c0-44.2-35.8-80-80-80s-80 35.8-80 80zM80 192V144C80 64.5 144.5 0 224 0s144 64.5 144 144v48h16c35.3 0 64 28.7 64 64V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V256c0-35.3 28.7-64 64-64H80z"]},Er={prefix:"fas",iconName:"plug",icon:[384,512,[128268],"f1e6","M96 0C78.3 0 64 14.3 64 32v96h64V32c0-17.7-14.3-32-32-32zM288 0c-17.7 0-32 14.3-32 32v96h64V32c0-17.7-14.3-32-32-32zM32 160c-17.7 0-32 14.3-32 32s14.3 32 32 32v32c0 77.4 55 142 128 156.8V480c0 17.7 14.3 32 32 32s32-14.3 32-32V412.8C297 398 352 333.4 352 256V224c17.7 0 32-14.3 32-32s-14.3-32-32-32H32z"]},Ir={prefix:"fas",iconName:"user",icon:[448,512,[128100,62144],"f007","M224 256A128 128 0 1 0 224 0a128 128 0 1 0 0 256zm-45.7 48C79.8 304 0 383.8 0 482.3C0 498.7 13.3 512 29.7 512H418.3c16.4 0 29.7-13.3 29.7-29.7C448 383.8 368.2 304 269.7 304H178.3z"]},_r={prefix:"fas",iconName:"globe",icon:[512,512,[127760],"f0ac","M352 256c0 22.2-1.2 43.6-3.3 64H163.3c-2.2-20.4-3.3-41.8-3.3-64s1.2-43.6 3.3-64H348.7c2.2 20.4 3.3 41.8 3.3 64zm28.8-64H503.9c5.3 20.5 8.1 41.9 8.1 64s-2.8 43.5-8.1 64H380.8c2.1-20.6 3.2-42 3.2-64s-1.1-43.4-3.2-64zm112.6-32H376.7c-10-63.9-29.8-117.4-55.3-151.6c78.3 20.7 142 77.5 171.9 151.6zm-149.1 0H167.7c6.1-36.4 15.5-68.6 27-94.7c10.5-23.6 22.2-40.7 33.5-51.5C239.4 3.2 248.7 0 256 0s16.6 3.2 27.8 13.8c11.3 10.8 23 27.9 33.5 51.5c11.6 26 20.9 58.2 27 94.7zm-209 0H18.6C48.6 85.9 112.2 29.1 190.6 8.4C165.1 42.6 145.3 96.1 135.3 160zM8.1 192H131.2c-2.1 20.6-3.2 42-3.2 64s1.1 43.4 3.2 64H8.1C2.8 299.5 0 278.1 0 256s2.8-43.5 8.1-64zM194.7 446.6c-11.6-26-20.9-58.2-27-94.6H344.3c-6.1 36.4-15.5 68.6-27 94.6c-10.5 23.6-22.2 40.7-33.5 51.5C272.6 508.8 263.3 512 256 512s-16.6-3.2-27.8-13.8c-11.3-10.8-23-27.9-33.5-51.5zM135.3 352c10 63.9 29.8 117.4 55.3 151.6C112.2 482.9 48.6 426.1 18.6 352H135.3zm358.1 0c-30 74.1-93.6 130.9-171.9 151.6c25.5-34.2 45.2-87.7 55.3-151.6H493.4z"]},Tr={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M96 0C60.7 0 32 28.7 32 64V448c-17.7 0-32 14.3-32 32s14.3 32 32 32H320c17.7 0 32-14.3 32-32s-14.3-32-32-32V304h16c22.1 0 40 17.9 40 40v32c0 39.8 32.2 72 72 72s72-32.2 72-72V252.3c32.5-10.2 56-40.5 56-76.3V144c0-8.8-7.2-16-16-16H544V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H480V80c0-8.8-7.2-16-16-16s-16 7.2-16 16v48H432c-8.8 0-16 7.2-16 16v32c0 35.8 23.5 66.1 56 76.3V376c0 13.3-10.7 24-24 24s-24-10.7-24-24V344c0-48.6-39.4-88-88-88H320V64c0-35.3-28.7-64-64-64H96zM216.9 82.7c6 4 8.5 11.5 6.3 18.3l-25 74.9H256c6.7 0 12.7 4.2 15 10.4s.5 13.3-4.6 17.7l-112 96c-5.5 4.7-13.4 5.1-19.3 1.1s-8.5-11.5-6.3-18.3l25-74.9H96c-6.7 0-12.7-4.2-15-10.4s-.5-13.3 4.6-17.7l112-96c5.5-4.7 13.4-5.1 19.3-1.1z"]},Fr={prefix:"fas",iconName:"microchip",icon:[512,512,[],"f2db","M176 24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64c-35.3 0-64 28.7-64 64H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64v56H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64v56H24c-13.3 0-24 10.7-24 24s10.7 24 24 24H64c0 35.3 28.7 64 64 64v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448h56v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448h56v40c0 13.3 10.7 24 24 24s24-10.7 24-24V448c35.3 0 64-28.7 64-64h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448V280h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448V176h40c13.3 0 24-10.7 24-24s-10.7-24-24-24H448c0-35.3-28.7-64-64-64V24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H280V24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H176V24zM160 128H352c17.7 0 32 14.3 32 32V352c0 17.7-14.3 32-32 32H160c-17.7 0-32-14.3-32-32V160c0-17.7 14.3-32 32-32zm192 32H160V352H352V160z"]},Rr={prefix:"fas",iconName:"unlock",icon:[448,512,[128275],"f09c","M144 144c0-44.2 35.8-80 80-80c31.9 0 59.4 18.6 72.3 45.7c7.6 16 26.7 22.8 42.6 15.2s22.8-26.7 15.2-42.6C331 33.7 281.5 0 224 0C144.5 0 80 64.5 80 144v48H64c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V256c0-35.3-28.7-64-64-64H144V144z"]},Dr={prefix:"fas",iconName:"clipboard",icon:[384,512,[128203],"f328","M192 0c-41.8 0-77.4 26.7-90.5 64H64C28.7 64 0 92.7 0 128V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H282.5C269.4 26.7 233.8 0 192 0zm0 64a32 32 0 1 1 0 64 32 32 0 1 1 0-64zM112 192H272c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16s7.2-16 16-16z"]},jr={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 96c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32h64c17.7 0 32 14.3 32 32h16c35.3 0 64 28.7 64 64V384c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V160c0-35.3 28.7-64 64-64l16 0zm304 96c0-8.8-7.2-16-16-16s-16 7.2-16 16v32H320c-8.8 0-16 7.2-16 16s7.2 16 16 16h32v32c0 8.8 7.2 16 16 16s16-7.2 16-16V256h32c8.8 0 16-7.2 16-16s-7.2-16-16-16H384V192zM80 240c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16s-7.2-16-16-16H96c-8.8 0-16 7.2-16 16z"]},ar={prefix:"fas",iconName:"circle-check",icon:[512,512,[61533,"check-circle"],"f058","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM369 209L241 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L335 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"]},$r=ar,Yr={prefix:"fas",iconName:"box-open",icon:[640,512,[],"f49e","M58.9 42.1c3-6.1 9.6-9.6 16.3-8.7L320 64 564.8 33.4c6.7-.8 13.3 2.7 16.3 8.7l41.7 83.4c9 17.9-.6 39.6-19.8 45.1L439.6 217.3c-13.9 4-28.8-1.9-36.2-14.3L320 64 236.6 203c-7.4 12.4-22.3 18.3-36.2 14.3L37.1 170.6c-19.3-5.5-28.8-27.2-19.8-45.1L58.9 42.1zM321.1 128l54.9 91.4c14.9 24.8 44.6 36.6 72.5 28.6L576 211.6v167c0 22-15 41.2-36.4 46.6l-204.1 51c-10.2 2.6-20.9 2.6-31 0l-204.1-51C79 419.7 64 400.5 64 378.5v-167L191.6 248c27.8 8 57.6-3.8 72.5-28.6L318.9 128h2.2z"]},er={prefix:"fas",iconName:"file-zipper",icon:[384,512,["file-archive"],"f1c6","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0H64zM256 0V128H384L256 0zM96 48c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm-6.3 71.8c3.7-14 16.4-23.8 30.9-23.8h14.8c14.5 0 27.2 9.7 30.9 23.8l23.5 88.2c1.4 5.4 2.1 10.9 2.1 16.4c0 35.2-28.8 63.7-64 63.7s-64-28.5-64-63.7c0-5.5 .7-11.1 2.1-16.4l23.5-88.2zM112 336c-8.8 0-16 7.2-16 16s7.2 16 16 16h32c8.8 0 16-7.2 16-16s-7.2-16-16-16H112z"]},Ur=er,Br={prefix:"fas",iconName:"filter",icon:[512,512,[],"f0b0","M3.9 54.9C10.5 40.9 24.5 32 40 32H472c15.5 0 29.5 8.9 36.1 22.9s4.6 30.5-5.2 42.5L320 320.9V448c0 12.1-6.8 23.2-17.7 28.6s-23.8 4.3-33.5-3l-64-48c-8.1-6-12.8-15.5-12.8-25.6V320.9L9 97.3C-.7 85.4-2.8 68.8 3.9 54.9z"]},nr={prefix:"fas",iconName:"up-down-left-right",icon:[512,512,["arrows-alt"],"f0b2","M278.6 9.4c-12.5-12.5-32.8-12.5-45.3 0l-64 64c-9.2 9.2-11.9 22.9-6.9 34.9s16.6 19.8 29.6 19.8h32v96H128V192c0-12.9-7.8-24.6-19.8-29.6s-25.7-2.2-34.9 6.9l-64 64c-12.5 12.5-12.5 32.8 0 45.3l64 64c9.2 9.2 22.9 11.9 34.9 6.9s19.8-16.6 19.8-29.6V288h96v96H192c-12.9 0-24.6 7.8-29.6 19.8s-2.2 25.7 6.9 34.9l64 64c12.5 12.5 32.8 12.5 45.3 0l64-64c9.2-9.2 11.9-22.9 6.9-34.9s-16.6-19.8-29.6-19.8H288V288h96v32c0 12.9 7.8 24.6 19.8 29.6s25.7 2.2 34.9-6.9l64-64c12.5-12.5 12.5-32.8 0-45.3l-64-64c-9.2-9.2-22.9-11.9-34.9-6.9s-19.8 16.6-19.8 29.6v32H288V128h32c12.9 0 24.6-7.8 29.6-19.8s2.2-25.7-6.9-34.9l-64-64z"]},Wr=nr,Gr={prefix:"fas",iconName:"code",icon:[640,512,[],"f121","M392.8 1.2c-17-4.9-34.7 5-39.6 22l-128 448c-4.9 17 5 34.7 22 39.6s34.7-5 39.6-22l128-448c4.9-17-5-34.7-22-39.6zm80.6 120.1c-12.5 12.5-12.5 32.8 0 45.3L562.7 256l-89.4 89.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l112-112c12.5-12.5 12.5-32.8 0-45.3l-112-112c-12.5-12.5-32.8-12.5-45.3 0zm-306.7 0c-12.5-12.5-32.8-12.5-45.3 0l-112 112c-12.5 12.5-12.5 32.8 0 45.3l112 112c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256l89.4-89.4c12.5-12.5 12.5-32.8 0-45.3z"]},Xr={prefix:"fas",iconName:"solar-panel",icon:[640,512,[],"f5ba","M122.2 0C91.7 0 65.5 21.5 59.5 51.4L8.3 307.4C.4 347 30.6 384 71 384H288v64H224c-17.7 0-32 14.3-32 32s14.3 32 32 32H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H352V384H569c40.4 0 70.7-36.9 62.8-76.6l-51.2-256C574.5 21.5 548.3 0 517.8 0H122.2zM260.9 64H379.1l10.4 104h-139L260.9 64zM202.3 168H101.4L122.2 64h90.4L202.3 168zM91.8 216H197.5L187.1 320H71L91.8 216zm153.9 0H394.3l10.4 104-169.4 0 10.4-104zm196.8 0H548.2L569 320h-116L442.5 216zm96-48H437.7L427.3 64h90.4l31.4-6.3L517.8 64l20.8 104z"]},tr={prefix:"fas",iconName:"circle-up",icon:[512,512,[61467,"arrow-alt-circle-up"],"f35b","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM135.1 217.4l107.1-99.9c3.8-3.5 8.7-5.5 13.8-5.5s10.1 2 13.8 5.5l107.1 99.9c4.5 4.2 7.1 10.1 7.1 16.3c0 12.3-10 22.3-22.3 22.3H304v96c0 17.7-14.3 32-32 32H240c-17.7 0-32-14.3-32-32V256H150.3C138 256 128 246 128 233.7c0-6.2 2.6-12.1 7.1-16.3z"]},qr=tr,Kr={prefix:"fas",iconName:"clipboard-check",icon:[384,512,[],"f46c","M192 0c-41.8 0-77.4 26.7-90.5 64H64C28.7 64 0 92.7 0 128V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H282.5C269.4 26.7 233.8 0 192 0zm0 64a32 32 0 1 1 0 64 32 32 0 1 1 0-64zM305 273L177 401c-9.4 9.4-24.6 9.4-33.9 0L79 337c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L271 239c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"]},rr={prefix:"fas",iconName:"circle-question",icon:[512,512,[62108,"question-circle"],"f059","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM169.8 165.3c7.9-22.3 29.1-37.3 52.8-37.3h58.3c34.9 0 63.1 28.3 63.1 63.1c0 22.6-12.1 43.5-31.7 54.8L280 264.4c-.2 13-10.9 23.6-24 23.6c-13.3 0-24-10.7-24-24V250.5c0-8.6 4.6-16.5 12.1-20.8l44.3-25.4c4.7-2.7 7.6-7.7 7.6-13.1c0-8.4-6.8-15.1-15.1-15.1H222.6c-3.4 0-6.4 2.1-7.5 5.3l-.4 1.2c-4.4 12.5-18.2 19-30.6 14.6s-19-18.2-14.6-30.6l.4-1.2zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z"]},Qr=rr,Zr={prefix:"fas",iconName:"house-signal",icon:[576,512,[],"e012","M357.7 8.5c-12.3-11.3-31.2-11.3-43.4 0l-208 192c-9.4 8.6-12.7 22-8.5 34c87.1 25.3 155.6 94.2 180.3 181.6H464c26.5 0 48-21.5 48-48V256h32c13.2 0 25-8.1 29.8-20.3s1.6-26.2-8.1-35.2l-208-192zM288 208c0-8.8 7.2-16 16-16h64c8.8 0 16 7.2 16 16v64c0 8.8-7.2 16-16 16H304c-8.8 0-16-7.2-16-16V208zM24 256c-13.3 0-24 10.7-24 24s10.7 24 24 24c101.6 0 184 82.4 184 184c0 13.3 10.7 24 24 24s24-10.7 24-24c0-128.1-103.9-232-232-232zm8 256a32 32 0 1 0 0-64 32 32 0 1 0 0 64zM0 376c0 13.3 10.7 24 24 24c48.6 0 88 39.4 88 88c0 13.3 10.7 24 24 24s24-10.7 24-24c0-75.1-60.9-136-136-136c-13.3 0-24 10.7-24 24z"]},Jr={prefix:"fas",iconName:"trash",icon:[448,512,[],"f1f8","M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z"]},ir={prefix:"fas",iconName:"up-right-from-square",icon:[512,512,["external-link-alt"],"f35d","M352 0c-12.9 0-24.6 7.8-29.6 19.8s-2.2 25.7 6.9 34.9L370.7 96 201.4 265.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L416 141.3l41.4 41.4c9.2 9.2 22.9 11.9 34.9 6.9s19.8-16.6 19.8-29.6V32c0-17.7-14.3-32-32-32H352zM80 32C35.8 32 0 67.8 0 112V432c0 44.2 35.8 80 80 80H400c44.2 0 80-35.8 80-80V320c0-17.7-14.3-32-32-32s-32 14.3-32 32V432c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V112c0-8.8 7.2-16 16-16H192c17.7 0 32-14.3 32-32s-14.3-32-32-32H80z"]},ai=ir,ei={prefix:"fas",iconName:"tag",icon:[448,512,[127991],"f02b","M0 80V229.5c0 17 6.7 33.3 18.7 45.3l176 176c25 25 65.5 25 90.5 0L418.7 317.3c25-25 25-65.5 0-90.5l-176-176c-12-12-28.3-18.7-45.3-18.7H48C21.5 32 0 53.5 0 80zm112 32a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"]},ni={prefix:"fas",iconName:"envelope",icon:[512,512,[128386,9993,61443],"f0e0","M48 64C21.5 64 0 85.5 0 112c0 15.1 7.1 29.3 19.2 38.4L236.8 313.6c11.4 8.5 27 8.5 38.4 0L492.8 150.4c12.1-9.1 19.2-23.3 19.2-38.4c0-26.5-21.5-48-48-48H48zM0 176V384c0 35.3 28.7 64 64 64H448c35.3 0 64-28.7 64-64V176L294.4 339.2c-22.8 17.1-54 17.1-76.8 0L0 176z"]},or={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM216 336h24V272H216c-13.3 0-24-10.7-24-24s10.7-24 24-24h48c13.3 0 24 10.7 24 24v88h8c13.3 0 24 10.7 24 24s-10.7 24-24 24H216c-13.3 0-24-10.7-24-24s10.7-24 24-24zm40-208a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"]},ti=or,sr={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M125.7 160H176c17.7 0 32 14.3 32 32s-14.3 32-32 32H48c-17.7 0-32-14.3-32-32V64c0-17.7 14.3-32 32-32s32 14.3 32 32v51.2L97.6 97.6c87.5-87.5 229.3-87.5 316.8 0s87.5 229.3 0 316.8s-229.3 87.5-316.8 0c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0c62.5 62.5 163.8 62.5 226.3 0s62.5-163.8 0-226.3s-163.8-62.5-226.3 0L125.7 160z"]},ri=sr,ii={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512A256 256 0 1 1 256 0zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},cr={prefix:"fas",iconName:"backward-step",icon:[320,512,["step-backward"],"f048","M267.5 440.6c9.5 7.9 22.8 9.7 34.1 4.4s18.4-16.6 18.4-29V96c0-12.4-7.2-23.7-18.4-29s-24.5-3.6-34.1 4.4l-192 160L64 241V96c0-17.7-14.3-32-32-32S0 78.3 0 96V416c0 17.7 14.3 32 32 32s32-14.3 32-32V271l11.5 9.6 192 160z"]},oi=cr,si={prefix:"fas",iconName:"keyboard",icon:[576,512,[9e3],"f11c","M64 64C28.7 64 0 92.7 0 128V384c0 35.3 28.7 64 64 64H512c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H64zm16 64h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM64 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V240zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V336c0-8.8 7.2-16 16-16zm80-176c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V144zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V240c0-8.8 7.2-16 16-16zM160 336c0-8.8 7.2-16 16-16H400c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16V336zM272 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H272c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM256 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H272c-8.8 0-16-7.2-16-16V240zM368 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H368c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM352 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H368c-8.8 0-16-7.2-16-16V240zM464 128h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V144c0-8.8 7.2-16 16-16zM448 240c0-8.8 7.2-16 16-16h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V240zm16 80h32c8.8 0 16 7.2 16 16v32c0 8.8-7.2 16-16 16H464c-8.8 0-16-7.2-16-16V336c0-8.8 7.2-16 16-16z"]},ci={prefix:"fas",iconName:"network-wired",icon:[640,512,[],"f6ff","M256 64H384v64H256V64zM240 0c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48h48v32H32c-17.7 0-32 14.3-32 32s14.3 32 32 32h96v32H80c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48H240c26.5 0 48-21.5 48-48V368c0-26.5-21.5-48-48-48H192V288H448v32H400c-26.5 0-48 21.5-48 48v96c0 26.5 21.5 48 48 48H560c26.5 0 48-21.5 48-48V368c0-26.5-21.5-48-48-48H512V288h96c17.7 0 32-14.3 32-32s-14.3-32-32-32H352V192h48c26.5 0 48-21.5 48-48V48c0-26.5-21.5-48-48-48H240zM96 448V384H224v64H96zm320-64H544v64H416V384z"]},fi={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32V256c0 17.7 14.3 32 32 32s32-14.3 32-32V32zM143.5 120.6c13.6-11.3 15.4-31.5 4.1-45.1s-31.5-15.4-45.1-4.1C49.7 115.4 16 181.8 16 256c0 132.5 107.5 240 240 240s240-107.5 240-240c0-74.2-33.8-140.6-86.6-184.6c-13.6-11.3-33.8-9.4-45.1 4.1s-9.4 33.8 4.1 45.1c38.9 32.3 63.5 81 63.5 135.4c0 97.2-78.8 176-176 176s-176-78.8-176-176c0-54.4 24.7-103.1 63.5-135.4z"]},li={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V64c0-35.3-28.7-64-64-64H64zM96 64H288c17.7 0 32 14.3 32 32v32c0 17.7-14.3 32-32 32H96c-17.7 0-32-14.3-32-32V96c0-17.7 14.3-32 32-32zm32 160a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zM96 352a32 32 0 1 1 0-64 32 32 0 1 1 0 64zM64 416c0-17.7 14.3-32 32-32h96c17.7 0 32 14.3 32 32s-14.3 32-32 32H96c-17.7 0-32-14.3-32-32zM192 256a32 32 0 1 1 0-64 32 32 0 1 1 0 64zm32 64a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zm64-64a32 32 0 1 1 0-64 32 32 0 1 1 0 64zm32 64a32 32 0 1 1 -64 0 32 32 0 1 1 64 0zM288 448a32 32 0 1 1 0-64 32 32 0 1 1 0 64z"]},ui={prefix:"fas",iconName:"download",icon:[512,512,[],"f019","M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32V274.7l-73.4-73.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l128 128c12.5 12.5 32.8 12.5 45.3 0l128-128c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L288 274.7V32zM64 352c-35.3 0-64 28.7-64 64v32c0 35.3 28.7 64 64 64H448c35.3 0 64-28.7 64-64V416c0-35.3-28.7-64-64-64H346.5l-45.3 45.3c-25 25-65.5 25-90.5 0L165.5 352H64zm368 56a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"]},mi={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v64c0 8.8 7.2 16 16 16H368c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},vi={prefix:"fas",iconName:"upload",icon:[512,512,[],"f093","M288 109.3V352c0 17.7-14.3 32-32 32s-32-14.3-32-32V109.3l-73.4 73.4c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3l128-128c12.5-12.5 32.8-12.5 45.3 0l128 128c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L288 109.3zM64 352H192c0 35.3 28.7 64 64 64s64-28.7 64-64H448c35.3 0 64 28.7 64 64v32c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V416c0-35.3 28.7-64 64-64zM432 456a24 24 0 1 0 0-48 24 24 0 1 0 0 48z"]},fr={prefix:"fas",iconName:"file-arrow-down",icon:[384,512,["file-download"],"f56d","M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0H64zM256 0V128H384L256 0zM216 232V334.1l31-31c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-72 72c-9.4 9.4-24.6 9.4-33.9 0l-72-72c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l31 31V232c0-13.3 10.7-24 24-24s24 10.7 24 24z"]},di=fr,pi={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M349.4 44.6c5.9-13.7 1.5-29.7-10.6-38.5s-28.6-8-39.9 1.8l-256 224c-10 8.8-13.6 22.9-8.9 35.3S50.7 288 64 288H175.5L98.6 467.4c-5.9 13.7-1.5 29.7 10.6 38.5s28.6 8 39.9-1.8l256-224c10-8.8 13.6-22.9 8.9-35.3s-16.6-20.7-30-20.7H272.5L349.4 44.6z"]},bi={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4L109.1 192H402.9l-26.1-74.6C372.3 104.6 360.2 96 346.6 96H165.4c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32H346.6c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2V400v48c0 17.7-14.3 32-32 32H448c-17.7 0-32-14.3-32-32V400H96v48c0 17.7-14.3 32-32 32H32c-17.7 0-32-14.3-32-32V400 256c0-26.7 16.4-49.6 39.6-59.2zM128 288a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},gi={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64c0-17.4-6.9-33.1-18.1-44.6L366 161.7c5.3-12.1-.2-26.3-12.3-31.6s-26.3 .2-31.6 12.3L257.9 288c-.6 0-1.3 0-1.9 0c-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},hi={prefix:"fas",iconName:"chevron-down",icon:[512,512,[],"f078","M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"]},yi={prefix:"fas",iconName:"skull-crossbones",icon:[448,512,[128369,9760],"f714","M368 128c0 44.4-25.4 83.5-64 106.4V256c0 17.7-14.3 32-32 32H176c-17.7 0-32-14.3-32-32V234.4c-38.6-23-64-62.1-64-106.4C80 57.3 144.5 0 224 0s144 57.3 144 128zM168 176a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm144-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM3.4 273.7c7.9-15.8 27.1-22.2 42.9-14.3L224 348.2l177.7-88.8c15.8-7.9 35-1.5 42.9 14.3s1.5 35-14.3 42.9L295.6 384l134.8 67.4c15.8 7.9 22.2 27.1 14.3 42.9s-27.1 22.2-42.9 14.3L224 419.8 46.3 508.6c-15.8 7.9-35 1.5-42.9-14.3s-1.5-35 14.3-42.9L152.4 384 17.7 316.6C1.9 308.7-4.5 289.5 3.4 273.7z"]},xi={prefix:"fas",iconName:"plus",icon:[448,512,[10133,61543,"add"],"2b","M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32V224H48c-17.7 0-32 14.3-32 32s14.3 32 32 32H192V432c0 17.7 14.3 32 32 32s32-14.3 32-32V288H400c17.7 0 32-14.3 32-32s-14.3-32-32-32H256V80z"]},lr={prefix:"fas",iconName:"xmark",icon:[384,512,[128473,10005,10006,10060,215,"close","multiply","remove","times"],"f00d","M342.6 150.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L192 210.7 86.6 105.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L146.7 256 41.4 361.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L192 301.3 297.4 406.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L237.3 256 342.6 150.6z"]},ki=lr,wi={prefix:"fas",iconName:"chevron-right",icon:[320,512,[9002],"f054","M310.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-192 192c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3L242.7 256 73.4 86.6c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l192 192z"]},zi={prefix:"fas",iconName:"check",icon:[448,512,[10003,10004],"f00c","M438.6 105.4c12.5 12.5 12.5 32.8 0 45.3l-256 256c-12.5 12.5-32.8 12.5-45.3 0l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L160 338.7 393.4 105.4c12.5-12.5 32.8-12.5 45.3 0z"]},ur={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 32c14.2 0 27.3 7.5 34.5 19.8l216 368c7.3 12.4 7.3 27.7 .2 40.1S486.3 480 472 480H40c-14.3 0-27.6-7.7-34.7-20.1s-7-27.8 .2-40.1l216-368C228.7 39.5 241.8 32 256 32zm0 128c-13.3 0-24 10.7-24 24V296c0 13.3 10.7 24 24 24s24-10.7 24-24V184c0-13.3-10.7-24-24-24zm32 224a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},Ai=ur,Ci={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32V64H288V32c0-17.7 14.3-32 32-32s32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32c0-17.7 14.3-32 32-32zM0 192H448V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm80 64c-8.8 0-16 7.2-16 16v96c0 8.8 7.2 16 16 16h96c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H80z"]},mr={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM175 175c9.4-9.4 24.6-9.4 33.9 0l47 47 47-47c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-47 47 47 47c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-47-47-47 47c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l47-47-47-47c-9.4-9.4-9.4-24.6 0-33.9z"]},Hi=mr,Mi={prefix:"far",iconName:"eye-slash",icon:[640,512,[],"f070","M38.8 5.1C28.4-3.1 13.3-1.2 5.1 9.2S-1.2 34.7 9.2 42.9l592 464c10.4 8.2 25.5 6.3 33.7-4.1s6.3-25.5-4.1-33.7L525.6 386.7c39.6-40.6 66.4-86.1 79.9-118.4c3.3-7.9 3.3-16.7 0-24.6c-14.9-35.7-46.2-87.7-93-131.1C465.5 68.8 400.8 32 320 32c-68.2 0-125 26.3-169.3 60.8L38.8 5.1zm151 118.3C226 97.7 269.5 80 320 80c65.2 0 118.8 29.6 159.9 67.7C518.4 183.5 545 226 558.6 256c-12.6 28-36.6 66.8-70.9 100.9l-53.8-42.2c9.1-17.6 14.2-37.5 14.2-58.7c0-70.7-57.3-128-128-128c-32.2 0-61.7 11.9-84.2 31.5l-46.1-36.1zM394.9 284.2l-81.5-63.9c4.2-8.5 6.6-18.2 6.6-28.3c0-5.5-.7-10.9-2-16c.7 0 1.3 0 2 0c44.2 0 80 35.8 80 80c0 9.9-1.8 19.4-5.1 28.2zm9.4 130.3C378.8 425.4 350.7 432 320 432c-65.2 0-118.8-29.6-159.9-67.7C121.6 328.5 95 286 81.4 256c8.3-18.4 21.5-41.5 39.4-64.8L83.1 161.5C60.3 191.2 44 220.8 34.5 243.7c-3.3 7.9-3.3 16.7 0 24.6c14.9 35.7 46.2 87.7 93 131.1C174.5 443.2 239.2 480 320 480c47.8 0 89.9-12.9 126.2-32.5l-41.9-33zM192 256c0 70.7 57.3 128 128 128c13.3 0 26.1-2 38.2-5.8L302 334c-23.5-5.4-43.1-21.2-53.7-42.3l-56.1-44.2c-.2 2.8-.3 5.6-.3 8.5z"]},vr={prefix:"far",iconName:"circle-question",icon:[512,512,[62108,"question-circle"],"f059","M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm169.8-90.7c7.9-22.3 29.1-37.3 52.8-37.3h58.3c34.9 0 63.1 28.3 63.1 63.1c0 22.6-12.1 43.5-31.7 54.8L280 264.4c-.2 13-10.9 23.6-24 23.6c-13.3 0-24-10.7-24-24V250.5c0-8.6 4.6-16.5 12.1-20.8l44.3-25.4c4.7-2.7 7.6-7.7 7.6-13.1c0-8.4-6.8-15.1-15.1-15.1H222.6c-3.4 0-6.4 2.1-7.5 5.3l-.4 1.2c-4.4 12.5-18.2 19-30.6 14.6s-19-18.2-14.6-30.6l.4-1.2zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z"]},Si=vr,Oi={prefix:"far",iconName:"eye",icon:[576,512,[128065],"f06e","M288 80c-65.2 0-118.8 29.6-159.9 67.7C89.6 183.5 63 226 49.4 256c13.6 30 40.2 72.5 78.6 108.3C169.2 402.4 222.8 432 288 432s118.8-29.6 159.9-67.7C486.4 328.5 513 286 526.6 256c-13.6-30-40.2-72.5-78.6-108.3C406.8 109.6 353.2 80 288 80zM95.4 112.6C142.5 68.8 207.2 32 288 32s145.5 36.8 192.6 80.6c46.8 43.5 78.1 95.4 93 131.1c3.3 7.9 3.3 16.7 0 24.6c-14.9 35.7-46.2 87.7-93 131.1C433.5 443.2 368.8 480 288 480s-145.5-36.8-192.6-80.6C48.6 356 17.3 304 2.5 268.3c-3.3-7.9-3.3-16.7 0-24.6C17.3 208 48.6 156 95.4 112.6zM288 336c44.2 0 80-35.8 80-80s-35.8-80-80-80c-.7 0-1.3 0-2 0c1.3 5.1 2 10.5 2 16c0 35.3-28.7 64-64 64c-5.5 0-10.9-.7-16-2c0 .7 0 1.3 0 2c0 44.2 35.8 80 80 80zm0-208a128 128 0 1 1 0 256 128 128 0 1 1 0-256z"]},Ni={prefix:"far",iconName:"file",icon:[384,512,[128196,128459,61462],"f15b","M320 464c8.8 0 16-7.2 16-16V160H256c-17.7 0-32-14.3-32-32V48H64c-8.8 0-16 7.2-16 16V448c0 8.8 7.2 16 16 16H320zM0 64C0 28.7 28.7 0 64 0H229.5c17 0 33.3 6.7 45.3 18.7l90.5 90.5c12 12 18.7 28.3 18.7 45.3V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V64z"]};function Ee(a,e){var n=Object.keys(a);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(a);e&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),n.push.apply(n,t)}return n}function E(a){for(var e=1;e<arguments.length;e++){var n=arguments[e]!=null?arguments[e]:{};e%2?Ee(Object(n),!0).forEach(function(t){S(a,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(n)):Ee(Object(n)).forEach(function(t){Object.defineProperty(a,t,Object.getOwnPropertyDescriptor(n,t))})}return a}function Ca(a){"@babel/helpers - typeof";return Ca=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},Ca(a)}function S(a,e,n){return e in a?Object.defineProperty(a,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):a[e]=n,a}function dr(a,e){if(a==null)return{};var n={},t=Object.keys(a),r,i;for(i=0;i<t.length;i++)r=t[i],!(e.indexOf(r)>=0)&&(n[r]=a[r]);return n}function pr(a,e){if(a==null)return{};var n=dr(a,e),t,r;if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(a);for(r=0;r<i.length;r++)t=i[r],!(e.indexOf(t)>=0)&&Object.prototype.propertyIsEnumerable.call(a,t)&&(n[t]=a[t])}return n}function br(a){return gr(a)||hr(a)||yr(a)||xr()}function gr(a){if(Array.isArray(a))return Xa(a)}function hr(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function yr(a,e){if(a){if(typeof a=="string")return Xa(a,e);var n=Object.prototype.toString.call(a).slice(8,-1);if(n==="Object"&&a.constructor&&(n=a.constructor.name),n==="Map"||n==="Set")return Array.from(a);if(n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return Xa(a,e)}}function Xa(a,e){(e==null||e>a.length)&&(e=a.length);for(var n=0,t=new Array(e);n<e;n++)t[n]=a[n];return t}function xr(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var kr=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof ce<"u"?ce:typeof self<"u"?self:{},mn={exports:{}};(function(a){(function(e){var n=function(d,p,h){if(!l(p)||v(p)||b(p)||g(p)||c(p))return p;var w,z=0,L=0;if(f(p))for(w=[],L=p.length;z<L;z++)w.push(n(d,p[z],h));else{w={};for(var N in p)Object.prototype.hasOwnProperty.call(p,N)&&(w[d(N,h)]=n(d,p[N],h))}return w},t=function(d,p){p=p||{};var h=p.separator||"_",w=p.split||/(?=[A-Z])/;return d.split(w).join(h)},r=function(d){return C(d)?d:(d=d.replace(/[\-_\s]+(.)?/g,function(p,h){return h?h.toUpperCase():""}),d.substr(0,1).toLowerCase()+d.substr(1))},i=function(d){var p=r(d);return p.substr(0,1).toUpperCase()+p.substr(1)},o=function(d,p){return t(d,p).toLowerCase()},s=Object.prototype.toString,c=function(d){return typeof d=="function"},l=function(d){return d===Object(d)},f=function(d){return s.call(d)=="[object Array]"},v=function(d){return s.call(d)=="[object Date]"},b=function(d){return s.call(d)=="[object RegExp]"},g=function(d){return s.call(d)=="[object Boolean]"},C=function(d){return d=d-0,d===d},H=function(d,p){var h=p&&"process"in p?p.process:p;return typeof h!="function"?d:function(w,z){return h(w,d,z)}},M={camelize:r,decamelize:o,pascalize:i,depascalize:o,camelizeKeys:function(d,p){return n(H(r,p),d)},decamelizeKeys:function(d,p){return n(H(o,p),d,p)},pascalizeKeys:function(d,p){return n(H(i,p),d)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}};a.exports?a.exports=M:e.humps=M})(kr)})(mn);var wr=mn.exports,zr=["class","style"];function Ar(a){return a.split(";").map(function(e){return e.trim()}).filter(function(e){return e}).reduce(function(e,n){var t=n.indexOf(":"),r=wr.camelize(n.slice(0,t)),i=n.slice(t+1).trim();return e[r]=i,e},{})}function Cr(a){return a.split(/\s+/).reduce(function(e,n){return e[n]=!0,e},{})}function vn(a){var e=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof a=="string")return a;var t=(a.children||[]).map(function(c){return vn(c)}),r=Object.keys(a.attributes||{}).reduce(function(c,l){var f=a.attributes[l];switch(l){case"class":c.class=Cr(f);break;case"style":c.style=Ar(f);break;default:c.attrs[l]=f}return c},{attrs:{},class:{},style:{}});n.class;var i=n.style,o=i===void 0?{}:i,s=pr(n,zr);return Te(a.tag,E(E(E({},e),{},{class:r.class,style:E(E({},r.style),o)},r.attrs),s),t)}var dn=!1;try{dn=!1}catch{}function Hr(){if(!dn&&console&&typeof console.error=="function"){var a;(a=console).error.apply(a,arguments)}}function Ia(a,e){return Array.isArray(e)&&e.length>0||!Array.isArray(e)&&e?S({},a,e):{}}function Mr(a){var e,n=(e={"fa-spin":a.spin,"fa-pulse":a.pulse,"fa-fw":a.fixedWidth,"fa-border":a.border,"fa-li":a.listItem,"fa-inverse":a.inverse,"fa-flip":a.flip===!0,"fa-flip-horizontal":a.flip==="horizontal"||a.flip==="both","fa-flip-vertical":a.flip==="vertical"||a.flip==="both"},S(e,"fa-".concat(a.size),a.size!==null),S(e,"fa-rotate-".concat(a.rotation),a.rotation!==null),S(e,"fa-pull-".concat(a.pull),a.pull!==null),S(e,"fa-swap-opacity",a.swapOpacity),S(e,"fa-bounce",a.bounce),S(e,"fa-shake",a.shake),S(e,"fa-beat",a.beat),S(e,"fa-fade",a.fade),S(e,"fa-beat-fade",a.beatFade),S(e,"fa-flash",a.flash),S(e,"fa-spin-pulse",a.spinPulse),S(e,"fa-spin-reverse",a.spinReverse),e);return Object.keys(n).map(function(t){return n[t]?t:null}).filter(function(t){return t})}function Ie(a){if(a&&Ca(a)==="object"&&a.prefix&&a.iconName&&a.icon)return a;if(Ga.icon)return Ga.icon(a);if(a===null)return null;if(Ca(a)==="object"&&a.prefix&&a.iconName)return a;if(Array.isArray(a)&&a.length===2)return{prefix:a[0],iconName:a[1]};if(typeof a=="string")return{prefix:"fas",iconName:a}}var Vi=_e({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(e){return[!0,!1,"horizontal","vertical","both"].indexOf(e)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(e){return["right","left"].indexOf(e)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(e){return[90,180,270].indexOf(Number.parseInt(e,10))>-1}},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(e){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(e)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1}},setup:function(e,n){var t=n.attrs,r=U(function(){return Ie(e.icon)}),i=U(function(){return Ia("classes",Mr(e))}),o=U(function(){return Ia("transform",typeof e.transform=="string"?Ga.transform(e.transform):e.transform)}),s=U(function(){return Ia("mask",Ie(e.mask))}),c=U(function(){return Kt(r.value,E(E(E(E({},i.value),o.value),s.value),{},{symbol:e.symbol,title:e.title}))});bn(c,function(f){if(!f)return Hr("Could not find one or more icon(s)",r.value,s.value)},{immediate:!0});var l=U(function(){return c.value?vn(c.value.abstract[0],{},t):null});return function(){return l.value}}}),Li=_e({name:"FontAwesomeLayers",props:{fixedWidth:{type:Boolean,default:!1}},setup:function(e,n){var t=n.slots,r=qt.familyPrefix,i=U(function(){return["".concat(r,"-layers")].concat(br(e.fixedWidth?["".concat(r,"-fw")]:[]))});return function(){return Te("div",{class:i.value},t.default?t.default():[])}}}),Pi={prefix:"fab",iconName:"paypal",icon:[384,512,[],"f1ed","M111.4 295.9c-3.5 19.2-17.4 108.7-21.5 134-.3 1.8-1 2.5-3 2.5H12.3c-7.6 0-13.1-6.6-12.1-13.9L58.8 46.6c1.5-9.6 10.1-16.9 20-16.9 152.3 0 165.1-3.7 204 11.4 60.1 23.3 65.6 79.5 44 140.3-21.5 62.6-72.5 89.5-140.1 90.3-43.4.7-69.5-7-75.3 24.2zM357.1 152c-1.8-1.3-2.5-1.8-3 1.3-2 11.4-5.1 22.5-8.8 33.6-39.9 113.8-150.5 103.9-204.5 103.9-6.1 0-10.1 3.3-10.9 9.4-22.6 140.4-27.1 169.7-27.1 169.7-1 7.1 3.5 12.9 10.6 12.9h63.5c8.6 0 15.7-6.3 17.4-14.9.7-5.4-1.1 6.1 14.4-91.3 4.6-22 14.3-19.7 29.3-19.7 71 0 126.4-28.8 142.9-112.3 6.5-34.8 4.6-71.4-23.8-92.6z"]};export{yi as $,Ci as A,Oi as B,Mi as C,ai as D,Pi as E,Vi as F,$r as G,Ai as H,bi as I,Tr as J,jr as K,Xr as L,gi as M,Br as N,ui as O,Zr as P,Fr as Q,Jr as R,Nr as S,mi as T,Ni as U,Li as V,pi as W,Er as X,di as Y,qr as Z,fi as _,Si as a,Lr as a0,Ur as a1,vi as a2,Yr as a3,Wr as a4,ei as b,Hi as c,xi as d,ti as e,Qr as f,zi as g,wi as h,hi as i,Dr as j,Kr as k,Or as l,li as m,Vr as n,oi as o,ri as p,ki as q,si as r,ni as s,ci as t,_r as u,Ir as v,Gr as w,Pr as x,Rr as y,ii as z};
