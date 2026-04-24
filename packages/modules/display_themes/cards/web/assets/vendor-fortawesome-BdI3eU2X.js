import{g as un,d as nt,w as at,c as G,h as tt}from"./vendor-smTHQY9_.js";function Ce(e,n){(n==null||n>e.length)&&(n=e.length);for(var a=0,t=Array(n);a<n;a++)t[a]=e[a];return t}function rt(e,n,a){return n&&(function(t,r){for(var i=0;i<r.length;i++){var o=r[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(t,na(o.key),o)}})(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),e}function pe(e,n){var a=typeof Symbol<"u"&&e[Symbol.iterator]||e["@@iterator"];if(!a){if(Array.isArray(e)||(a=en(e))||n){a&&(e=a);var t=0,r=function(){};return{s:r,n:function(){return t>=e.length?{done:!0}:{done:!1,value:e[t++]}},e:function(c){throw c},f:r}}throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var i,o=!0,l=!1;return{s:function(){a=a.call(e)},n:function(){var c=a.next();return o=c.done,c},e:function(c){l=!0,i=c},f:function(){try{o||a.return==null||a.return()}finally{if(l)throw i}}}}function y(e,n,a){return(n=na(n))in e?Object.defineProperty(e,n,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[n]=a,e}function dn(e,n){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(e);n&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(e,r).enumerable})),a.push.apply(a,t)}return a}function f(e){for(var n=1;n<arguments.length;n++){var a=arguments[n]!=null?arguments[n]:{};n%2?dn(Object(a),!0).forEach(function(t){y(e,t,a[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):dn(Object(a)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))})}return e}function ye(e,n){return(function(a){if(Array.isArray(a))return a})(e)||(function(a,t){var r=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(r!=null){var i,o,l,c,s=[],u=!0,d=!1;try{if(l=(r=r.call(a)).next,t===0){if(Object(r)!==r)return;u=!1}else for(;!(u=(i=l.call(r)).done)&&(s.push(i.value),s.length!==t);u=!0);}catch(m){d=!0,o=m}finally{try{if(!u&&r.return!=null&&(c=r.return(),Object(c)!==c))return}finally{if(d)throw o}}return s}})(e,n)||en(e,n)||(function(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)})()}function C(e){return(function(n){if(Array.isArray(n))return Ce(n)})(e)||(function(n){if(typeof Symbol<"u"&&n[Symbol.iterator]!=null||n["@@iterator"]!=null)return Array.from(n)})(e)||en(e)||(function(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)})()}function na(e){var n=(function(a,t){if(typeof a!="object"||!a)return a;var r=a[Symbol.toPrimitive];if(r!==void 0){var i=r.call(a,t);if(typeof i!="object")return i;throw new TypeError("@@toPrimitive must return a primitive value.")}return(t==="string"?String:Number)(a)})(e,"string");return typeof n=="symbol"?n:n+""}function Qe(e){return(Qe=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(n){return typeof n}:function(n){return n&&typeof Symbol=="function"&&n.constructor===Symbol&&n!==Symbol.prototype?"symbol":typeof n})(e)}function en(e,n){if(e){if(typeof e=="string")return Ce(e,n);var a={}.toString.call(e).slice(8,-1);return a==="Object"&&e.constructor&&(a=e.constructor.name),a==="Map"||a==="Set"?Array.from(e):a==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(a)?Ce(e,n):void 0}}var mn=function(){},nn={},aa={},ta=null,ra={mark:mn,measure:mn};try{typeof window<"u"&&(nn=window),typeof document<"u"&&(aa=document),typeof MutationObserver<"u"&&(ta=MutationObserver),typeof performance<"u"&&(ra=performance)}catch{}var pn=(nn.navigator||{}).userAgent,gn=pn===void 0?"":pn,Y=nn,k=aa,hn=ta,ce=ra;Y.document;var bn,B=!!k.documentElement&&!!k.head&&typeof k.addEventListener=="function"&&typeof k.createElement=="function",ia=~gn.indexOf("MSIE")||~gn.indexOf("Trident/"),oa={classic:{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fab:"brands","fa-brands":"brands"},duotone:{fa:"solid",fad:"solid","fa-solid":"solid","fa-duotone":"solid",fadr:"regular","fa-regular":"regular",fadl:"light","fa-light":"light",fadt:"thin","fa-thin":"thin"},sharp:{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light",fast:"thin","fa-thin":"thin"},"sharp-duotone":{fa:"solid",fasds:"solid","fa-solid":"solid",fasdr:"regular","fa-regular":"regular",fasdl:"light","fa-light":"light",fasdt:"thin","fa-thin":"thin"},slab:{"fa-regular":"regular",faslr:"regular"},"slab-press":{"fa-regular":"regular",faslpr:"regular"},thumbprint:{"fa-light":"light",fatl:"light"},whiteboard:{"fa-semibold":"semibold",fawsb:"semibold"},notdog:{"fa-solid":"solid",fans:"solid"},"notdog-duo":{"fa-solid":"solid",fands:"solid"},etch:{"fa-solid":"solid",faes:"solid"},graphite:{"fa-thin":"thin",fagt:"thin"},jelly:{"fa-regular":"regular",fajr:"regular"},"jelly-fill":{"fa-regular":"regular",fajfr:"regular"},"jelly-duo":{"fa-regular":"regular",fajdr:"regular"},chisel:{"fa-regular":"regular",facr:"regular"},utility:{"fa-semibold":"semibold",fausb:"semibold"},"utility-duo":{"fa-semibold":"semibold",faudsb:"semibold"},"utility-fill":{"fa-semibold":"semibold",faufsb:"semibold"}},la=["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-utility","fa-utility-duo","fa-utility-fill"],M="classic",oe="duotone",sa="sharp",fa="sharp-duotone",ca="chisel",ua="etch",da="graphite",ma="jelly",pa="jelly-duo",ga="jelly-fill",ha="notdog",ba="notdog-duo",ya="slab",va="slab-press",xa="thumbprint",wa="utility",ka="utility-duo",Sa="utility-fill",za="whiteboard",ja=[M,oe,sa,fa,ca,ua,da,ma,pa,ga,ha,ba,ya,va,xa,wa,ka,Sa,za];y(y(y(y(y(y(y(y(y(y(bn={},M,"Classic"),oe,"Duotone"),sa,"Sharp"),fa,"Sharp Duotone"),ca,"Chisel"),ua,"Etch"),da,"Graphite"),ma,"Jelly"),pa,"Jelly Duo"),ga,"Jelly Fill"),y(y(y(y(y(y(y(y(y(bn,ha,"Notdog"),ba,"Notdog Duo"),ya,"Slab"),va,"Slab Press"),xa,"Thumbprint"),wa,"Utility"),ka,"Utility Duo"),Sa,"Utility Fill"),za,"Whiteboard");var it=new Map([["classic",{defaultShortPrefixId:"fas",defaultStyleId:"solid",styleIds:["solid","regular","light","thin","brands"],futureStyleIds:[],defaultFontWeight:900}],["duotone",{defaultShortPrefixId:"fad",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp",{defaultShortPrefixId:"fass",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp-duotone",{defaultShortPrefixId:"fasds",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["chisel",{defaultShortPrefixId:"facr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["etch",{defaultShortPrefixId:"faes",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["graphite",{defaultShortPrefixId:"fagt",defaultStyleId:"thin",styleIds:["thin"],futureStyleIds:[],defaultFontWeight:100}],["jelly",{defaultShortPrefixId:"fajr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-duo",{defaultShortPrefixId:"fajdr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-fill",{defaultShortPrefixId:"fajfr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["notdog",{defaultShortPrefixId:"fans",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["notdog-duo",{defaultShortPrefixId:"fands",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["slab",{defaultShortPrefixId:"faslr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab-press",{defaultShortPrefixId:"faslpr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["thumbprint",{defaultShortPrefixId:"fatl",defaultStyleId:"light",styleIds:["light"],futureStyleIds:[],defaultFontWeight:300}],["utility",{defaultShortPrefixId:"fausb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-duo",{defaultShortPrefixId:"faudsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-fill",{defaultShortPrefixId:"faufsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["whiteboard",{defaultShortPrefixId:"fawsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}]]),Aa=["fak","fa-kit","fakd","fa-kit-duotone"],ot={fak:"kit","fa-kit":"kit"},lt={fakd:"kit-duotone","fa-kit-duotone":"kit-duotone"};y(y({},"kit","Kit"),"kit-duotone","Kit Duotone");var yn,st={kit:"fak"},ft={"kit-duotone":"fakd"},ct="duotone-group",ut="swap-opacity",dt="primary",mt="secondary";y(y(y(y(y(y(y(y(y(y(yn={},"classic","Classic"),"duotone","Duotone"),"sharp","Sharp"),"sharp-duotone","Sharp Duotone"),"chisel","Chisel"),"etch","Etch"),"graphite","Graphite"),"jelly","Jelly"),"jelly-duo","Jelly Duo"),"jelly-fill","Jelly Fill"),y(y(y(y(y(y(y(y(y(yn,"notdog","Notdog"),"notdog-duo","Notdog Duo"),"slab","Slab"),"slab-press","Slab Press"),"thumbprint","Thumbprint"),"utility","Utility"),"utility-duo","Utility Duo"),"utility-fill","Utility Fill"),"whiteboard","Whiteboard");y(y({},"kit","Kit"),"kit-duotone","Kit Duotone");var Ee={classic:{fab:"fa-brands",fad:"fa-duotone",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"},duotone:{fadr:"fa-regular",fadl:"fa-light",fadt:"fa-thin"},sharp:{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light",fast:"fa-thin"},"sharp-duotone":{fasds:"fa-solid",fasdr:"fa-regular",fasdl:"fa-light",fasdt:"fa-thin"},slab:{faslr:"fa-regular"},"slab-press":{faslpr:"fa-regular"},whiteboard:{fawsb:"fa-semibold"},thumbprint:{fatl:"fa-light"},notdog:{fans:"fa-solid"},"notdog-duo":{fands:"fa-solid"},etch:{faes:"fa-solid"},graphite:{fagt:"fa-thin"},jelly:{fajr:"fa-regular"},"jelly-fill":{fajfr:"fa-regular"},"jelly-duo":{fajdr:"fa-regular"},chisel:{facr:"fa-regular"},utility:{fausb:"fa-semibold"},"utility-duo":{faudsb:"fa-semibold"},"utility-fill":{faufsb:"fa-semibold"}},Na=["fa","fas","far","fal","fat","fad","fadr","fadl","fadt","fab","fass","fasr","fasl","fast","fasds","fasdr","fasdl","fasdt","faslr","faslpr","fawsb","fatl","fans","fands","faes","fagt","fajr","fajfr","fajdr","facr","fausb","faudsb","faufsb"].concat(["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-utility","fa-utility-duo","fa-utility-fill"],["fa-solid","fa-regular","fa-light","fa-thin","fa-duotone","fa-brands","fa-semibold"]),Ma=[1,2,3,4,5,6,7,8,9,10],pt=Ma.concat([11,12,13,14,15,16,17,18,19,20]),gt=[].concat(C(Object.keys({classic:["fas","far","fal","fat","fad"],duotone:["fadr","fadl","fadt"],sharp:["fass","fasr","fasl","fast"],"sharp-duotone":["fasds","fasdr","fasdl","fasdt"],slab:["faslr"],"slab-press":["faslpr"],whiteboard:["fawsb"],thumbprint:["fatl"],notdog:["fans"],"notdog-duo":["fands"],etch:["faes"],graphite:["fagt"],jelly:["fajr"],"jelly-fill":["fajfr"],"jelly-duo":["fajdr"],chisel:["facr"],utility:["fausb"],"utility-duo":["faudsb"],"utility-fill":["faufsb"]})),["solid","regular","light","thin","duotone","brands","semibold"],["aw","fw","pull-left","pull-right"],["2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","inverse","layers","layers-bottom-left","layers-bottom-right","layers-counter","layers-text","layers-top-left","layers-top-right","li","pull-end","pull-start","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul","width-auto","width-fixed",ct,ut,dt,mt]).concat(Ma.map(function(e){return"".concat(e,"x")})).concat(pt.map(function(e){return"w-".concat(e)})),T="___FONT_AWESOME___",Pa="svg-inline--fa",q="data-fa-i2svg",De="data-fa-pseudo-element",Te="data-prefix",Re="data-icon",vn="fontawesome-i2svg",ht=["HTML","HEAD","STYLE","SCRIPT"],Oa=["::before","::after",":before",":after"],Ia=(function(){try{return!0}catch{return!1}})();function le(e){return new Proxy(e,{get:function(n,a){return a in n?n[a]:n[M]}})}var Fa=f({},oa);Fa[M]=f(f(f(f({},{"fa-duotone":"duotone"}),oa[M]),ot),lt);var bt=le(Fa),We=f({},{chisel:{regular:"facr"},classic:{brands:"fab",light:"fal",regular:"far",solid:"fas",thin:"fat"},duotone:{light:"fadl",regular:"fadr",solid:"fad",thin:"fadt"},etch:{solid:"faes"},graphite:{thin:"fagt"},jelly:{regular:"fajr"},"jelly-duo":{regular:"fajdr"},"jelly-fill":{regular:"fajfr"},notdog:{solid:"fans"},"notdog-duo":{solid:"fands"},sharp:{light:"fasl",regular:"fasr",solid:"fass",thin:"fast"},"sharp-duotone":{light:"fasdl",regular:"fasdr",solid:"fasds",thin:"fasdt"},slab:{regular:"faslr"},"slab-press":{regular:"faslpr"},thumbprint:{light:"fatl"},utility:{semibold:"fausb"},"utility-duo":{semibold:"faudsb"},"utility-fill":{semibold:"faufsb"},whiteboard:{semibold:"fawsb"}});We[M]=f(f(f(f({},{duotone:"fad"}),We[M]),st),ft);var xn=le(We),Be=f({},Ee);Be[M]=f(f({},Be[M]),{fak:"fa-kit"});var an=le(Be),ze=f({},{classic:{"fa-brands":"fab","fa-duotone":"fad","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"},duotone:{"fa-regular":"fadr","fa-light":"fadl","fa-thin":"fadt"},sharp:{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl","fa-thin":"fast"},"sharp-duotone":{"fa-solid":"fasds","fa-regular":"fasdr","fa-light":"fasdl","fa-thin":"fasdt"},slab:{"fa-regular":"faslr"},"slab-press":{"fa-regular":"faslpr"},whiteboard:{"fa-semibold":"fawsb"},thumbprint:{"fa-light":"fatl"},notdog:{"fa-solid":"fans"},"notdog-duo":{"fa-solid":"fands"},etch:{"fa-solid":"faes"},graphite:{"fa-thin":"fagt"},jelly:{"fa-regular":"fajr"},"jelly-fill":{"fa-regular":"fajfr"},"jelly-duo":{"fa-regular":"fajdr"},chisel:{"fa-regular":"facr"},utility:{"fa-semibold":"fausb"},"utility-duo":{"fa-semibold":"faudsb"},"utility-fill":{"fa-semibold":"faufsb"}});ze[M]=f(f({},ze[M]),{"fa-kit":"fak"}),le(ze);var yt=/fa(k|kd|s|r|l|t|d|dr|dl|dt|b|slr|slpr|wsb|tl|ns|nds|es|gt|jr|jfr|jdr|usb|ufsb|udsb|cr|ss|sr|sl|st|sds|sdr|sdl|sdt)?[\-\ ]/,La="fa-layers-text",vt=/Font ?Awesome ?([567 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp Duotone|Sharp|Kit|Notdog Duo|Notdog|Chisel|Etch|Graphite|Thumbprint|Jelly Fill|Jelly Duo|Jelly|Utility|Utility Fill|Utility Duo|Slab Press|Slab|Whiteboard)?.*/i;le(f({},{classic:{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},duotone:{900:"fad",400:"fadr",300:"fadl",100:"fadt"},sharp:{900:"fass",400:"fasr",300:"fasl",100:"fast"},"sharp-duotone":{900:"fasds",400:"fasdr",300:"fasdl",100:"fasdt"},slab:{400:"faslr"},"slab-press":{400:"faslpr"},whiteboard:{600:"fawsb"},thumbprint:{300:"fatl"},notdog:{900:"fans"},"notdog-duo":{900:"fands"},etch:{900:"faes"},graphite:{100:"fagt"},chisel:{400:"facr"},jelly:{400:"fajr"},"jelly-fill":{400:"fajfr"},"jelly-duo":{400:"fajdr"},utility:{600:"fausb"},"utility-duo":{600:"faudsb"},"utility-fill":{600:"faufsb"}}));var xt=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],je={GROUP:"duotone-group",PRIMARY:"primary",SECONDARY:"secondary"},wt=[].concat(C(["kit"]),C(gt)),re=Y.FontAwesomeConfig||{};k&&typeof k.querySelector=="function"&&[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-search-pseudo-elements","searchPseudoElements"],["data-search-pseudo-elements-warnings","searchPseudoElementsWarnings"],["data-search-pseudo-elements-full-scan","searchPseudoElementsFullScan"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]].forEach(function(e){var n=ye(e,2),a=n[0],t=n[1],r=(function(i){return i===""||i!=="false"&&(i==="true"||i)})((function(i){var o=k.querySelector("script["+i+"]");if(o)return o.getAttribute(i)})(a));r!=null&&(re[t]=r)});var Ca={styleDefault:"solid",familyDefault:M,cssPrefix:"fa",replacementClass:Pa,autoReplaceSvg:!0,autoAddCss:!0,searchPseudoElements:!1,searchPseudoElementsWarnings:!0,searchPseudoElementsFullScan:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};re.familyPrefix&&(re.cssPrefix=re.familyPrefix);var $=f(f({},Ca),re);$.autoReplaceSvg||($.observeMutations=!1);var h={};Object.keys(Ca).forEach(function(e){Object.defineProperty(h,e,{enumerable:!0,set:function(n){$[e]=n,Ue.forEach(function(a){return a(h)})},get:function(){return $[e]}})}),Object.defineProperty(h,"familyPrefix",{enumerable:!0,set:function(e){$.cssPrefix=e,Ue.forEach(function(n){return n(h)})},get:function(){return $.cssPrefix}}),Y.FontAwesomeConfig=h;var Ue=[],V=16,D={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function wn(){for(var e=12,n="";e-- >0;)n+="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"[62*Math.random()|0];return n}function ee(e){for(var n=[],a=(e||[]).length>>>0;a--;)n[a]=e[a];return n}function tn(e){return e.classList?ee(e.classList):(e.getAttribute("class")||"").split(" ").filter(function(n){return n})}function kn(e){return"".concat(e).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function ve(e){return Object.keys(e||{}).reduce(function(n,a){return n+"".concat(a,": ").concat(e[a].trim(),";")},"")}function rn(e){return e.size!==D.size||e.x!==D.x||e.y!==D.y||e.rotate!==D.rotate||e.flipX||e.flipY}function Ea(){var e="fa",n=Pa,a=h.cssPrefix,t=h.replacementClass,r=`:root, :host {
  --fa-font-solid: normal 900 1em/1 'Font Awesome 7 Free';
  --fa-font-regular: normal 400 1em/1 'Font Awesome 7 Free';
  --fa-font-light: normal 300 1em/1 'Font Awesome 7 Pro';
  --fa-font-thin: normal 100 1em/1 'Font Awesome 7 Pro';
  --fa-font-duotone: normal 900 1em/1 'Font Awesome 7 Duotone';
  --fa-font-duotone-regular: normal 400 1em/1 'Font Awesome 7 Duotone';
  --fa-font-duotone-light: normal 300 1em/1 'Font Awesome 7 Duotone';
  --fa-font-duotone-thin: normal 100 1em/1 'Font Awesome 7 Duotone';
  --fa-font-brands: normal 400 1em/1 'Font Awesome 7 Brands';
  --fa-font-sharp-solid: normal 900 1em/1 'Font Awesome 7 Sharp';
  --fa-font-sharp-regular: normal 400 1em/1 'Font Awesome 7 Sharp';
  --fa-font-sharp-light: normal 300 1em/1 'Font Awesome 7 Sharp';
  --fa-font-sharp-thin: normal 100 1em/1 'Font Awesome 7 Sharp';
  --fa-font-sharp-duotone-solid: normal 900 1em/1 'Font Awesome 7 Sharp Duotone';
  --fa-font-sharp-duotone-regular: normal 400 1em/1 'Font Awesome 7 Sharp Duotone';
  --fa-font-sharp-duotone-light: normal 300 1em/1 'Font Awesome 7 Sharp Duotone';
  --fa-font-sharp-duotone-thin: normal 100 1em/1 'Font Awesome 7 Sharp Duotone';
  --fa-font-slab-regular: normal 400 1em/1 'Font Awesome 7 Slab';
  --fa-font-slab-press-regular: normal 400 1em/1 'Font Awesome 7 Slab Press';
  --fa-font-whiteboard-semibold: normal 600 1em/1 'Font Awesome 7 Whiteboard';
  --fa-font-thumbprint-light: normal 300 1em/1 'Font Awesome 7 Thumbprint';
  --fa-font-notdog-solid: normal 900 1em/1 'Font Awesome 7 Notdog';
  --fa-font-notdog-duo-solid: normal 900 1em/1 'Font Awesome 7 Notdog Duo';
  --fa-font-etch-solid: normal 900 1em/1 'Font Awesome 7 Etch';
  --fa-font-graphite-thin: normal 100 1em/1 'Font Awesome 7 Graphite';
  --fa-font-jelly-regular: normal 400 1em/1 'Font Awesome 7 Jelly';
  --fa-font-jelly-fill-regular: normal 400 1em/1 'Font Awesome 7 Jelly Fill';
  --fa-font-jelly-duo-regular: normal 400 1em/1 'Font Awesome 7 Jelly Duo';
  --fa-font-chisel-regular: normal 400 1em/1 'Font Awesome 7 Chisel';
  --fa-font-utility-semibold: normal 600 1em/1 'Font Awesome 7 Utility';
  --fa-font-utility-duo-semibold: normal 600 1em/1 'Font Awesome 7 Utility Duo';
  --fa-font-utility-fill-semibold: normal 600 1em/1 'Font Awesome 7 Utility Fill';
}

.svg-inline--fa {
  box-sizing: content-box;
  display: var(--fa-display, inline-block);
  height: 1em;
  overflow: visible;
  vertical-align: -0.125em;
  width: var(--fa-width, 1.25em);
}
.svg-inline--fa.fa-2xs {
  vertical-align: 0.1em;
}
.svg-inline--fa.fa-xs {
  vertical-align: 0em;
}
.svg-inline--fa.fa-sm {
  vertical-align: -0.0714285714em;
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
.svg-inline--fa.fa-pull-left,
.svg-inline--fa .fa-pull-start {
  float: inline-start;
  margin-inline-end: var(--fa-pull-margin, 0.3em);
}
.svg-inline--fa.fa-pull-right,
.svg-inline--fa .fa-pull-end {
  float: inline-end;
  margin-inline-start: var(--fa-pull-margin, 0.3em);
}
.svg-inline--fa.fa-li {
  width: var(--fa-li-width, 2em);
  inset-inline-start: calc(-1 * var(--fa-li-width, 2em));
  inset-block-start: 0.25em; /* syncing vertical alignment with Web Font rendering */
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
  width: var(--fa-width, 1.25em);
}
.fa-layers .svg-inline--fa {
  inset: 0;
  margin: auto;
  position: absolute;
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
  font-size: calc(10 / 16 * 1em); /* converts a 10px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 10 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 10 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-xs {
  font-size: calc(12 / 16 * 1em); /* converts a 12px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 12 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 12 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-sm {
  font-size: calc(14 / 16 * 1em); /* converts a 14px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 14 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 14 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-lg {
  font-size: calc(20 / 16 * 1em); /* converts a 20px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 20 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 20 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-xl {
  font-size: calc(24 / 16 * 1em); /* converts a 24px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 24 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 24 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-2xl {
  font-size: calc(32 / 16 * 1em); /* converts a 32px size into an em-based value that's relative to the scale's 16px base */
  line-height: calc(1 / 32 * 1em); /* sets the line-height of the icon back to that of it's parent */
  vertical-align: calc((6 / 32 - 0.375) * 1em); /* vertically centers the icon taking into account the surrounding text's descender */
}

.fa-width-auto {
  --fa-width: auto;
}

.fa-fw,
.fa-width-fixed {
  --fa-width: 1.25em;
}

.fa-ul {
  list-style-type: none;
  margin-inline-start: var(--fa-li-margin, 2.5em);
  padding-inline-start: 0;
}
.fa-ul > li {
  position: relative;
}

.fa-li {
  inset-inline-start: calc(-1 * var(--fa-li-width, 2em));
  position: absolute;
  text-align: center;
  width: var(--fa-li-width, 2em);
  line-height: inherit;
}

/* Heads Up: Bordered Icons will not be supported in the future!
  - This feature will be deprecated in the next major release of Font Awesome (v8)!
  - You may continue to use it in this version *v7), but it will not be supported in Font Awesome v8.
*/
/* Notes:
* --@{v.$css-prefix}-border-width = 1/16 by default (to render as ~1px based on a 16px default font-size)
* --@{v.$css-prefix}-border-padding =
  ** 3/16 for vertical padding (to give ~2px of vertical whitespace around an icon considering it's vertical alignment)
  ** 4/16 for horizontal padding (to give ~4px of horizontal whitespace around an icon)
*/
.fa-border {
  border-color: var(--fa-border-color, #eee);
  border-radius: var(--fa-border-radius, 0.1em);
  border-style: var(--fa-border-style, solid);
  border-width: var(--fa-border-width, 0.0625em);
  box-sizing: var(--fa-border-box-sizing, content-box);
  padding: var(--fa-border-padding, 0.1875em 0.25em);
}

.fa-pull-left,
.fa-pull-start {
  float: inline-start;
  margin-inline-end: var(--fa-pull-margin, 0.3em);
}

.fa-pull-right,
.fa-pull-end {
  float: inline-end;
  margin-inline-start: var(--fa-pull-margin, 0.3em);
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
    animation: none !important;
    transition: none !important;
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

.svg-inline--fa.fa-inverse {
  fill: var(--fa-inverse, #fff);
}

.fa-stack {
  display: inline-block;
  height: 2em;
  line-height: 2em;
  position: relative;
  vertical-align: middle;
  width: 2.5em;
}

.fa-inverse {
  color: var(--fa-inverse, #fff);
}

.svg-inline--fa.fa-stack-1x {
  --fa-width: 1.25em;
  height: 1em;
  width: var(--fa-width);
}
.svg-inline--fa.fa-stack-2x {
  --fa-width: 2.5em;
  height: 2em;
  width: var(--fa-width);
}

.fa-stack-1x,
.fa-stack-2x {
  inset: 0;
  margin: auto;
  position: absolute;
  z-index: var(--fa-stack-z-index, auto);
}`;if(a!==e||t!==n){var i=new RegExp("\\.".concat(e,"\\-"),"g"),o=new RegExp("\\--".concat(e,"\\-"),"g"),l=new RegExp("\\.".concat(n),"g");r=r.replace(i,".".concat(a,"-")).replace(o,"--".concat(a,"-")).replace(l,".".concat(t))}return r}var Sn=!1;function Ae(){h.autoAddCss&&!Sn&&((function(e){if(e&&B){var n=k.createElement("style");n.setAttribute("type","text/css"),n.innerHTML=e;for(var a=k.head.childNodes,t=null,r=a.length-1;r>-1;r--){var i=a[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(t=i)}k.head.insertBefore(n,t)}})(Ea()),Sn=!0)}var kt={mixout:function(){return{dom:{css:Ea,insertCss:Ae}}},hooks:function(){return{beforeDOMElementCreation:function(){Ae()},beforeI2svg:function(){Ae()}}}},R=Y||{};R[T]||(R[T]={}),R[T].styles||(R[T].styles={}),R[T].hooks||(R[T].hooks={}),R[T].shims||(R[T].shims=[]);var L=R[T],Da=[],Ta=function(){k.removeEventListener("DOMContentLoaded",Ta),on=1,Da.map(function(e){return e()})},on=!1;function se(e){var n=e.tag,a=e.attributes,t=a===void 0?{}:a,r=e.children,i=r===void 0?[]:r;return typeof e=="string"?kn(e):"<".concat(n," ").concat((function(o){return Object.keys(o||{}).reduce(function(l,c){return l+"".concat(c,'="').concat(kn(o[c]),'" ')},"").trim()})(t),">").concat(i.map(se).join(""),"</").concat(n,">")}function zn(e,n,a){if(e&&e[n]&&e[n][a])return{prefix:n,iconName:a,icon:e[n][a]}}B&&((on=(k.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(k.readyState))||k.addEventListener("DOMContentLoaded",Ta));var Ne=function(e,n,a,t){var r,i,o,l=Object.keys(e),c=l.length,s=n;for(a===void 0?(r=1,o=e[l[0]]):(r=0,o=a);r<c;r++)o=s(o,e[i=l[r]],i,e);return o};function Ra(e){return C(e).length!==1?null:e.codePointAt(0).toString(16)}function jn(e){return Object.keys(e).reduce(function(n,a){var t=e[a];return t.icon?n[t.iconName]=t.icon:n[a]=t,n},{})}function Ye(e,n){var a=(arguments.length>2&&arguments[2]!==void 0?arguments[2]:{}).skipHooks,t=a!==void 0&&a,r=jn(n);typeof L.hooks.addPack!="function"||t?L.styles[e]=f(f({},L.styles[e]||{}),r):L.hooks.addPack(e,jn(n)),e==="fas"&&Ye("fa",n)}var ie=L.styles,St=L.shims,Wa=Object.keys(an),zt=Wa.reduce(function(e,n){return e[n]=Object.keys(an[n]),e},{}),ln=null,Ba={},Ua={},Ya={},Ja={},Ha={};function jt(e,n){var a,t=n.split("-"),r=t[0],i=t.slice(1).join("-");return r!==e||i===""||(a=i,~wt.indexOf(a))?null:i}var An,Ka=function(){var e=function(t){return Ne(ie,function(r,i,o){return r[o]=Ne(i,t,{}),r},{})};Ba=e(function(t,r,i){return r[3]&&(t[r[3]]=i),r[2]&&r[2].filter(function(o){return typeof o=="number"}).forEach(function(o){t[o.toString(16)]=i}),t}),Ua=e(function(t,r,i){return t[i]=i,r[2]&&r[2].filter(function(o){return typeof o=="string"}).forEach(function(o){t[o]=i}),t}),Ha=e(function(t,r,i){var o=r[2];return t[i]=i,o.forEach(function(l){t[l]=i}),t});var n="far"in ie||h.autoFetchSvg,a=Ne(St,function(t,r){var i=r[0],o=r[1],l=r[2];return o!=="far"||n||(o="fas"),typeof i=="string"&&(t.names[i]={prefix:o,iconName:l}),typeof i=="number"&&(t.unicodes[i.toString(16)]={prefix:o,iconName:l}),t},{names:{},unicodes:{}});Ya=a.names,Ja=a.unicodes,ln=xe(h.styleDefault,{family:h.familyDefault})};function Je(e,n){return(Ba[e]||{})[n]}function K(e,n){return(Ha[e]||{})[n]}function qa(e){return Ya[e]||{prefix:null,iconName:null}}function J(){return ln}An=function(e){ln=xe(e.styleDefault,{family:h.familyDefault})},Ue.push(An),Ka();function xe(e){var n=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).family,a=n===void 0?M:n,t=bt[a][e];if(a===oe&&!e)return"fad";var r=xn[a][e]||xn[a][t],i=e in L.styles?e:null;return r||i||null}function Nn(e){return e.sort().filter(function(n,a,t){return t.indexOf(n)===a})}var Mn=Na.concat(Aa);function we(e){var n,a,t=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).skipLookups,r=t!==void 0&&t,i=null,o=Nn(e.filter(function(m){return Mn.includes(m)})),l=Nn(e.filter(function(m){return!Mn.includes(m)})),c=ye(o.filter(function(m){return i=m,!la.includes(m)}),1)[0],s=c===void 0?null:c,u=(function(m){var p=M,v=Wa.reduce(function(g,b){return g[b]="".concat(h.cssPrefix,"-").concat(b),g},{});return ja.forEach(function(g){(m.includes(v[g])||m.some(function(b){return zt[g].includes(b)}))&&(p=g)}),p})(o),d=f(f({},(n=[],a=null,l.forEach(function(m){var p=jt(h.cssPrefix,m);p?a=p:m&&n.push(m)}),{iconName:a,rest:n})),{},{prefix:xe(s,{family:u})});return f(f(f({},d),(function(m){var p=m.values,v=m.family,g=m.canonical,b=m.givenPrefix,w=b===void 0?"":b,S=m.styles,F=S===void 0?{}:S,E=m.config,x=E===void 0?{}:E,O=v===oe,j=p.includes("fa-duotone")||p.includes("fad"),A=x.familyDefault==="duotone",I=g.prefix==="fad"||g.prefix==="fa-duotone";if(!O&&(j||A||I)&&(g.prefix="fad"),(p.includes("fa-brands")||p.includes("fab"))&&(g.prefix="fab"),!g.prefix&&At.includes(v)&&(Object.keys(F).find(function(N){return Nt.includes(N)})||x.autoFetchSvg)){var z=it.get(v).defaultShortPrefixId;g.prefix=z,g.iconName=K(g.prefix,g.iconName)||g.iconName}return g.prefix!=="fa"&&w!=="fa"||(g.prefix=J()||"fas"),g})({values:e,family:u,styles:ie,config:h,canonical:d,givenPrefix:i})),(function(m,p,v){var g=v.prefix,b=v.iconName;if(m||!g||!b)return{prefix:g,iconName:b};var w=p==="fa"?qa(b):{},S=K(g,b);return b=w.iconName||S||b,(g=w.prefix||g)!=="far"||ie.far||!ie.fas||h.autoFetchSvg||(g="fas"),{prefix:g,iconName:b}})(r,i,d))}var At=ja.filter(function(e){return e!==M||e!==oe}),Nt=Object.keys(Ee).filter(function(e){return e!==M}).map(function(e){return Object.keys(Ee[e])}).flat(),Mt=(function(){return rt(function e(){(function(n,a){if(!(n instanceof a))throw new TypeError("Cannot call a class as a function")})(this,e),this.definitions={}},[{key:"add",value:function(){for(var e=this,n=arguments.length,a=new Array(n),t=0;t<n;t++)a[t]=arguments[t];var r=a.reduce(this._pullDefinitions,{});Object.keys(r).forEach(function(i){e.definitions[i]=f(f({},e.definitions[i]||{}),r[i]),Ye(i,r[i]);var o=an[M][i];o&&Ye(o,r[i]),Ka()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(e,n){var a=n.prefix&&n.iconName&&n.icon?{0:n}:n;return Object.keys(a).map(function(t){var r=a[t],i=r.prefix,o=r.iconName,l=r.icon,c=l[2];e[i]||(e[i]={}),c.length>0&&c.forEach(function(s){typeof s=="string"&&(e[i][s]=l)}),e[i][o]=l}),e}}])})(),Pn=[],Z={},Q={},Pt=Object.keys(Q);function He(e,n){for(var a=arguments.length,t=new Array(a>2?a-2:0),r=2;r<a;r++)t[r-2]=arguments[r];return(Z[e]||[]).forEach(function(i){n=i.apply(null,[n].concat(t))}),n}function _(e){for(var n=arguments.length,a=new Array(n>1?n-1:0),t=1;t<n;t++)a[t-1]=arguments[t];(Z[e]||[]).forEach(function(r){r.apply(null,a)})}function H(){var e=arguments[0],n=Array.prototype.slice.call(arguments,1);return Q[e]?Q[e].apply(null,n):void 0}function Ke(e){e.prefix==="fa"&&(e.prefix="fas");var n=e.iconName,a=e.prefix||J();if(n)return n=K(a,n)||n,zn(_a.definitions,a,n)||zn(L.styles,a,n)}var _a=new Mt,Ot={i2svg:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return B?(_("beforeI2svg",e),H("pseudoElements2svg",e),H("i2svg",e)):Promise.reject(new Error("Operation requires a DOM of some kind."))},watch:function(){var e,n=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},a=n.autoReplaceSvgRoot;h.autoReplaceSvg===!1&&(h.autoReplaceSvg=!0),h.observeMutations=!0,e=function(){It({autoReplaceSvgRoot:a}),_("watch",n)},B&&(on?setTimeout(e,0):Da.push(e))}},fe={noAuto:function(){h.autoReplaceSvg=!1,h.observeMutations=!1,_("noAuto")},config:h,dom:Ot,parse:{icon:function(e){if(e===null)return null;if(Qe(e)==="object"&&e.prefix&&e.iconName)return{prefix:e.prefix,iconName:K(e.prefix,e.iconName)||e.iconName};if(Array.isArray(e)&&e.length===2){var n=e[1].indexOf("fa-")===0?e[1].slice(3):e[1],a=xe(e[0]);return{prefix:a,iconName:K(a,n)||n}}if(typeof e=="string"&&(e.indexOf("".concat(h.cssPrefix,"-"))>-1||e.match(yt))){var t=we(e.split(" "),{skipLookups:!0});return{prefix:t.prefix||J(),iconName:K(t.prefix,t.iconName)||t.iconName}}if(typeof e=="string"){var r=J();return{prefix:r,iconName:K(r,e)||e}}}},library:_a,findIconDefinition:Ke,toHtml:se},It=function(){var e=(arguments.length>0&&arguments[0]!==void 0?arguments[0]:{}).autoReplaceSvgRoot,n=e===void 0?k:e;(Object.keys(L.styles).length>0||h.autoFetchSvg)&&B&&h.autoReplaceSvg&&fe.dom.i2svg({node:n})};function ke(e,n){return Object.defineProperty(e,"abstract",{get:n}),Object.defineProperty(e,"html",{get:function(){return e.abstract.map(function(a){return se(a)})}}),Object.defineProperty(e,"node",{get:function(){if(B){var a=k.createElement("div");return a.innerHTML=e.html,a.children}}}),e}function sn(e){var n=e.icons,a=n.main,t=n.mask,r=e.prefix,i=e.iconName,o=e.transform,l=e.symbol,c=e.maskId,s=e.extra,u=e.watchable,d=u!==void 0&&u,m=t.found?t:a,p=m.width,v=m.height,g=[h.replacementClass,i?"".concat(h.cssPrefix,"-").concat(i):""].filter(function(x){return s.classes.indexOf(x)===-1}).filter(function(x){return x!==""||!!x}).concat(s.classes).join(" "),b={children:[],attributes:f(f({},s.attributes),{},{"data-prefix":r,"data-icon":i,class:g,role:s.attributes.role||"img",viewBox:"0 0 ".concat(p," ").concat(v)})};(function(x){return["aria-label","aria-labelledby","title","role"].some(function(O){return O in x})})(s.attributes)||s.attributes["aria-hidden"]||(b.attributes["aria-hidden"]="true"),d&&(b.attributes[q]="");var w=f(f({},b),{},{prefix:r,iconName:i,main:a,mask:t,maskId:c,transform:o,symbol:l,styles:f({},s.styles)}),S=t.found&&a.found?H("generateAbstractMask",w)||{children:[],attributes:{}}:H("generateAbstractIcon",w)||{children:[],attributes:{}},F=S.children,E=S.attributes;return w.children=F,w.attributes=E,l?(function(x){var O=x.prefix,j=x.iconName,A=x.children,I=x.attributes,z=x.symbol,N=z===!0?"".concat(O,"-").concat(h.cssPrefix,"-").concat(j):z;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:f(f({},I),{},{id:N}),children:A}]}]})(w):(function(x){var O=x.children,j=x.main,A=x.mask,I=x.attributes,z=x.styles,N=x.transform;if(rn(N)&&j.found&&!A.found){var U={x:j.width/j.height/2,y:.5};I.style=ve(f(f({},z),{},{"transform-origin":"".concat(U.x+N.x/16,"em ").concat(U.y+N.y/16,"em")}))}return[{tag:"svg",attributes:I,children:O}]})(w)}function On(e){var n=e.content,a=e.width,t=e.height,r=e.transform,i=e.extra,o=e.watchable,l=o!==void 0&&o,c=f(f({},i.attributes),{},{class:i.classes.join(" ")});l&&(c[q]="");var s=f({},i.styles);rn(r)&&(s.transform=(function(m){var p=m.transform,v=m.width,g=v===void 0?16:v,b=m.height,w=b===void 0?16:b,S="";return S+=ia?"translate(".concat(p.x/V-g/2,"em, ").concat(p.y/V-w/2,"em) "):"translate(calc(-50% + ".concat(p.x/V,"em), calc(-50% + ").concat(p.y/V,"em)) "),S+="scale(".concat(p.size/V*(p.flipX?-1:1),", ").concat(p.size/V*(p.flipY?-1:1),") "),S+"rotate(".concat(p.rotate,"deg) ")})({transform:r,width:a,height:t}),s["-webkit-transform"]=s.transform);var u=ve(s);u.length>0&&(c.style=u);var d=[];return d.push({tag:"span",attributes:c,children:[n]}),d}var Me=L.styles;function qe(e){var n=e[0],a=e[1],t=ye(e.slice(4),1)[0];return{found:!0,width:n,height:a,icon:Array.isArray(t)?{tag:"g",attributes:{class:"".concat(h.cssPrefix,"-").concat(je.GROUP)},children:[{tag:"path",attributes:{class:"".concat(h.cssPrefix,"-").concat(je.SECONDARY),fill:"currentColor",d:t[0]}},{tag:"path",attributes:{class:"".concat(h.cssPrefix,"-").concat(je.PRIMARY),fill:"currentColor",d:t[1]}}]}:{tag:"path",attributes:{fill:"currentColor",d:t}}}}var Ft={found:!1,width:512,height:512};function _e(e,n){var a=n;return n==="fa"&&h.styleDefault!==null&&(n=J()),new Promise(function(t,r){if(a==="fa"){var i=qa(e)||{};e=i.iconName||e,n=i.prefix||n}if(e&&n&&Me[n]&&Me[n][e])return t(qe(Me[n][e]));!Ia&&h.showMissingIcons,t(f(f({},Ft),{},{icon:h.showMissingIcons&&e&&H("missingIconAbstract")||{}}))})}var In=function(){},Ge=h.measurePerformance&&ce&&ce.mark&&ce.measure?ce:{mark:In,measure:In},te='FA "7.2.0"',Lt=function(e){Ge.mark("".concat(te," ").concat(e," ends")),Ge.measure("".concat(te," ").concat(e),"".concat(te," ").concat(e," begins"),"".concat(te," ").concat(e," ends"))},fn=function(e){return Ge.mark("".concat(te," ").concat(e," begins")),function(){return Lt(e)}},ge=function(){};function Fn(e){return typeof(e.getAttribute?e.getAttribute(q):null)=="string"}function Ct(e){return k.createElementNS("http://www.w3.org/2000/svg",e)}function Et(e){return k.createElement(e)}function Ga(e){var n=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).ceFn,a=n===void 0?e.tag==="svg"?Ct:Et:n;if(typeof e=="string")return k.createTextNode(e);var t=a(e.tag);return Object.keys(e.attributes||[]).forEach(function(r){t.setAttribute(r,e.attributes[r])}),(e.children||[]).forEach(function(r){t.appendChild(Ga(r,{ceFn:a}))}),t}var he={replace:function(e){var n=e[0];if(n.parentNode)if(e[1].forEach(function(t){n.parentNode.insertBefore(Ga(t),n)}),n.getAttribute(q)===null&&h.keepOriginalSource){var a=k.createComment((function(t){var r=" ".concat(t.outerHTML," ");return"".concat(r,"Font Awesome fontawesome.com ")})(n));n.parentNode.replaceChild(a,n)}else n.remove()},nest:function(e){var n=e[0],a=e[1];if(~tn(n).indexOf(h.replacementClass))return he.replace(e);var t=new RegExp("".concat(h.cssPrefix,"-.*"));if(delete a[0].attributes.id,a[0].attributes.class){var r=a[0].attributes.class.split(" ").reduce(function(o,l){return l===h.replacementClass||l.match(t)?o.toSvg.push(l):o.toNode.push(l),o},{toNode:[],toSvg:[]});a[0].attributes.class=r.toSvg.join(" "),r.toNode.length===0?n.removeAttribute("class"):n.setAttribute("class",r.toNode.join(" "))}var i=a.map(function(o){return se(o)}).join(`
`);n.setAttribute(q,""),n.innerHTML=i}};function Ln(e){e()}function Va(e,n){var a=typeof n=="function"?n:ge;if(e.length===0)a();else{var t=Ln;h.mutateApproach==="async"&&(t=Y.requestAnimationFrame||Ln),t(function(){var r=h.autoReplaceSvg===!0?he.replace:he[h.autoReplaceSvg]||he.replace,i=fn("mutate");e.map(r),i(),a()})}}var cn=!1;function Xa(){cn=!0}function Ve(){cn=!1}var be=null;function Cn(e){if(hn&&h.observeMutations){var n=e.treeCallback,a=n===void 0?ge:n,t=e.nodeCallback,r=t===void 0?ge:t,i=e.pseudoElementsCallback,o=i===void 0?ge:i,l=e.observeMutationsRoot,c=l===void 0?k:l;be=new hn(function(s){if(!cn){var u=J();ee(s).forEach(function(d){if(d.type==="childList"&&d.addedNodes.length>0&&!Fn(d.addedNodes[0])&&(h.searchPseudoElements&&o(d.target),a(d.target)),d.type==="attributes"&&d.target.parentNode&&h.searchPseudoElements&&o([d.target],!0),d.type==="attributes"&&Fn(d.target)&&~xt.indexOf(d.attributeName))if(d.attributeName==="class"&&(function(b){var w=b.getAttribute?b.getAttribute(Te):null,S=b.getAttribute?b.getAttribute(Re):null;return w&&S})(d.target)){var m=we(tn(d.target)),p=m.prefix,v=m.iconName;d.target.setAttribute(Te,p||u),v&&d.target.setAttribute(Re,v)}else(g=d.target)&&g.classList&&g.classList.contains&&g.classList.contains(h.replacementClass)&&r(d.target);var g})}}),B&&be.observe(c,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function Dt(e){var n,a,t=e.getAttribute("data-prefix"),r=e.getAttribute("data-icon"),i=e.innerText!==void 0?e.innerText.trim():"",o=we(tn(e));return o.prefix||(o.prefix=J()),t&&r&&(o.prefix=t,o.iconName=r),o.iconName&&o.prefix||(o.prefix&&i.length>0&&(o.iconName=(n=o.prefix,a=e.innerText,(Ua[n]||{})[a]||Je(o.prefix,Ra(e.innerText)))),!o.iconName&&h.autoFetchSvg&&e.firstChild&&e.firstChild.nodeType===Node.TEXT_NODE&&(o.iconName=e.firstChild.data)),o}function En(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},a=Dt(e),t=a.iconName,r=a.prefix,i=a.rest,o=(function(s){return ee(s.attributes).reduce(function(u,d){return u.name!=="class"&&u.name!=="style"&&(u[d.name]=d.value),u},{})})(e),l=He("parseNodeAttributes",{},e),c=n.styleParser?(function(s){var u=s.getAttribute("style"),d=[];return u&&(d=u.split(";").reduce(function(m,p){var v=p.split(":"),g=v[0],b=v.slice(1);return g&&b.length>0&&(m[g]=b.join(":").trim()),m},{})),d})(e):[];return f({iconName:t,prefix:r,transform:D,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:i,styles:c,attributes:o}},l)}var Tt=L.styles;function $a(e){var n=h.autoReplaceSvg==="nest"?En(e,{styleParser:!1}):En(e);return~n.extra.classes.indexOf(La)?H("generateLayersText",e,n):H("generateSvgReplacementMutation",e,n)}function Dn(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!B)return Promise.resolve();var a=k.documentElement.classList,t=function(u){return a.add("".concat(vn,"-").concat(u))},r=function(u){return a.remove("".concat(vn,"-").concat(u))},i=h.autoFetchSvg?[].concat(C(Aa),C(Na)):la.concat(Object.keys(Tt));i.includes("fa")||i.push("fa");var o=[".".concat(La,":not([").concat(q,"])")].concat(i.map(function(u){return".".concat(u,":not([").concat(q,"])")})).join(", ");if(o.length===0)return Promise.resolve();var l=[];try{l=ee(e.querySelectorAll(o))}catch{}if(!(l.length>0))return Promise.resolve();t("pending"),r("complete");var c=fn("onTree"),s=l.reduce(function(u,d){try{var m=$a(d);m&&u.push(m)}catch(p){Ia||p.name}return u},[]);return new Promise(function(u,d){Promise.all(s).then(function(m){Va(m,function(){t("active"),t("complete"),r("pending"),typeof n=="function"&&n(),c(),u()})}).catch(function(m){c(),d(m)})})}function Rt(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;$a(e).then(function(a){a&&Va([a],n)})}var Wt=function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},a=n.transform,t=a===void 0?D:a,r=n.symbol,i=r!==void 0&&r,o=n.mask,l=o===void 0?null:o,c=n.maskId,s=c===void 0?null:c,u=n.classes,d=u===void 0?[]:u,m=n.attributes,p=m===void 0?{}:m,v=n.styles,g=v===void 0?{}:v;if(e){var b=e.prefix,w=e.iconName,S=e.icon;return ke(f({type:"icon"},e),function(){return _("beforeDOMElementCreation",{iconDefinition:e,params:n}),sn({icons:{main:qe(S),mask:l?qe(l.icon):{found:!1,width:null,height:null,icon:{}}},prefix:b,iconName:w,transform:f(f({},D),t),symbol:i,maskId:s,extra:{attributes:p,styles:g,classes:d}})})}},Bt={mixout:function(){return{icon:(e=Wt,function(n){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=(n||{}).icon?n:Ke(n||{}),r=a.mask;return r&&(r=(r||{}).icon?r:Ke(r||{})),e(t,f(f({},a),{},{mask:r}))})};var e},hooks:function(){return{mutationObserverCallbacks:function(e){return e.treeCallback=Dn,e.nodeCallback=Rt,e}}},provides:function(e){e.i2svg=function(n){var a=n.node,t=a===void 0?k:a,r=n.callback;return Dn(t,r===void 0?function(){}:r)},e.generateSvgReplacementMutation=function(n,a){var t=a.iconName,r=a.prefix,i=a.transform,o=a.symbol,l=a.mask,c=a.maskId,s=a.extra;return new Promise(function(u,d){Promise.all([_e(t,r),l.iconName?_e(l.iconName,l.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(m){var p=ye(m,2),v=p[0],g=p[1];u([n,sn({icons:{main:v,mask:g},prefix:r,iconName:t,transform:i,symbol:o,maskId:c,extra:s,watchable:!0})])}).catch(d)})},e.generateAbstractIcon=function(n){var a,t=n.children,r=n.attributes,i=n.main,o=n.transform,l=ve(n.styles);return l.length>0&&(r.style=l),rn(o)&&(a=H("generateAbstractTransformGrouping",{main:i,transform:o,containerWidth:i.width,iconWidth:i.width})),t.push(a||i.icon),{children:t,attributes:r}}}},Ut={mixout:function(){return{layer:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},a=n.classes,t=a===void 0?[]:a;return ke({type:"layer"},function(){_("beforeDOMElementCreation",{assembler:e,params:n});var r=[];return e(function(i){Array.isArray(i)?i.map(function(o){r=r.concat(o.abstract)}):r=r.concat(i.abstract)}),[{tag:"span",attributes:{class:["".concat(h.cssPrefix,"-layers")].concat(C(t)).join(" ")},children:r}]})}}}},Yt={mixout:function(){return{counter:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};n.title;var a=n.classes,t=a===void 0?[]:a,r=n.attributes,i=r===void 0?{}:r,o=n.styles,l=o===void 0?{}:o;return ke({type:"counter",content:e},function(){return _("beforeDOMElementCreation",{content:e,params:n}),(function(c){var s=c.content,u=c.extra,d=f(f({},u.attributes),{},{class:u.classes.join(" ")}),m=ve(u.styles);m.length>0&&(d.style=m);var p=[];return p.push({tag:"span",attributes:d,children:[s]}),p})({content:e.toString(),extra:{attributes:i,styles:l,classes:["".concat(h.cssPrefix,"-layers-counter")].concat(C(t))}})})}}}},Jt={mixout:function(){return{text:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},a=n.transform,t=a===void 0?D:a,r=n.classes,i=r===void 0?[]:r,o=n.attributes,l=o===void 0?{}:o,c=n.styles,s=c===void 0?{}:c;return ke({type:"text",content:e},function(){return _("beforeDOMElementCreation",{content:e,params:n}),On({content:e,transform:f(f({},D),t),extra:{attributes:l,styles:s,classes:["".concat(h.cssPrefix,"-layers-text")].concat(C(i))}})})}}},provides:function(e){e.generateLayersText=function(n,a){var t=a.transform,r=a.extra,i=null,o=null;if(ia){var l=parseInt(getComputedStyle(n).fontSize,10),c=n.getBoundingClientRect();i=c.width/l,o=c.height/l}return Promise.resolve([n,On({content:n.innerHTML,width:i,height:o,transform:t,extra:r,watchable:!0})])}}},Tn=new RegExp('"',"ug"),Rn=[1105920,1112319],Wn=f(f(f(f({},{FontAwesome:{normal:"fas",400:"fas"}}),{"Font Awesome 7 Free":{900:"fas",400:"far"},"Font Awesome 7 Pro":{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},"Font Awesome 7 Brands":{400:"fab",normal:"fab"},"Font Awesome 7 Duotone":{900:"fad",400:"fadr",normal:"fadr",300:"fadl",100:"fadt"},"Font Awesome 7 Sharp":{900:"fass",400:"fasr",normal:"fasr",300:"fasl",100:"fast"},"Font Awesome 7 Sharp Duotone":{900:"fasds",400:"fasdr",normal:"fasdr",300:"fasdl",100:"fasdt"},"Font Awesome 7 Jelly":{400:"fajr",normal:"fajr"},"Font Awesome 7 Jelly Fill":{400:"fajfr",normal:"fajfr"},"Font Awesome 7 Jelly Duo":{400:"fajdr",normal:"fajdr"},"Font Awesome 7 Slab":{400:"faslr",normal:"faslr"},"Font Awesome 7 Slab Press":{400:"faslpr",normal:"faslpr"},"Font Awesome 7 Thumbprint":{300:"fatl",normal:"fatl"},"Font Awesome 7 Notdog":{900:"fans",normal:"fans"},"Font Awesome 7 Notdog Duo":{900:"fands",normal:"fands"},"Font Awesome 7 Etch":{900:"faes",normal:"faes"},"Font Awesome 7 Graphite":{100:"fagt",normal:"fagt"},"Font Awesome 7 Chisel":{400:"facr",normal:"facr"},"Font Awesome 7 Whiteboard":{600:"fawsb",normal:"fawsb"},"Font Awesome 7 Utility":{600:"fausb",normal:"fausb"},"Font Awesome 7 Utility Duo":{600:"faudsb",normal:"faudsb"},"Font Awesome 7 Utility Fill":{600:"faufsb",normal:"faufsb"}}),{"Font Awesome 5 Free":{900:"fas",400:"far"},"Font Awesome 5 Pro":{900:"fas",400:"far",normal:"far",300:"fal"},"Font Awesome 5 Brands":{400:"fab",normal:"fab"},"Font Awesome 5 Duotone":{900:"fad"}}),{"Font Awesome Kit":{400:"fak",normal:"fak"},"Font Awesome Kit Duotone":{400:"fakd",normal:"fakd"}}),Xe=Object.keys(Wn).reduce(function(e,n){return e[n.toLowerCase()]=Wn[n],e},{}),Ht=Object.keys(Xe).reduce(function(e,n){var a=Xe[n];return e[n]=a[900]||C(Object.entries(a))[0][1],e},{});function Bn(e,n){var a="".concat("data-fa-pseudo-element-pending").concat(n.replace(":","-"));return new Promise(function(t,r){if(e.getAttribute(a)!==null)return t();var i,o,l,c=ee(e.children).filter(function(A){return A.getAttribute(De)===n})[0],s=Y.getComputedStyle(e,n),u=s.getPropertyValue("font-family"),d=u.match(vt),m=s.getPropertyValue("font-weight"),p=s.getPropertyValue("content");if(c&&!d)return e.removeChild(c),t();if(d&&p!=="none"&&p!==""){var v=s.getPropertyValue("content"),g=(function(A,I){var z=A.replace(/^['"]|['"]$/g,"").toLowerCase(),N=parseInt(I),U=isNaN(N)?"normal":N;return(Xe[z]||{})[U]||Ht[z]})(u,m),b=(function(A){return Ra(C(A.replace(Tn,""))[0]||"")})(v),w=d[0].startsWith("FontAwesome"),S=(function(A){var I=A.getPropertyValue("font-feature-settings").includes("ss01"),z=A.getPropertyValue("content").replace(Tn,""),N=z.codePointAt(0),U=N>=Rn[0]&&N<=Rn[1],Se=z.length===2&&z[0]===z[1];return U||Se||I})(s),F=Je(g,b),E=F;if(w){var x=(o=Ja[i=b],l=Je("fas",i),o||(l?{prefix:"fas",iconName:l}:null)||{prefix:null,iconName:null});x.iconName&&x.prefix&&(F=x.iconName,g=x.prefix)}if(!F||S||c&&c.getAttribute(Te)===g&&c.getAttribute(Re)===E)t();else{e.setAttribute(a,E),c&&e.removeChild(c);var O={iconName:null,prefix:null,transform:D,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}},j=O.extra;j.attributes[De]=n,_e(F,g).then(function(A){var I=sn(f(f({},O),{},{icons:{main:A,mask:{prefix:null,iconName:null,rest:[]}},prefix:g,iconName:E,extra:j,watchable:!0})),z=k.createElementNS("http://www.w3.org/2000/svg","svg");n==="::before"?e.insertBefore(z,e.firstChild):e.appendChild(z),z.outerHTML=I.map(function(N){return se(N)}).join(`
`),e.removeAttribute(a),t()}).catch(r)}}else t()})}function Kt(e){return Promise.all([Bn(e,"::before"),Bn(e,"::after")])}function qt(e){return!(e.parentNode===document.head||~ht.indexOf(e.tagName.toUpperCase())||e.getAttribute(De)||e.parentNode&&e.parentNode.tagName==="svg")}var _t=function(e){return!!e&&Oa.some(function(n){return e.includes(n)})},Gt=function(e){if(!e)return[];var n,a=new Set,t=e.split(/,(?![^()]*\))/).map(function(l){return l.trim()}),r=pe(t=t.flatMap(function(l){return l.includes("(")?l:l.split(",").map(function(c){return c.trim()})}));try{for(r.s();!(n=r.n()).done;){var i=n.value;if(_t(i)){var o=Oa.reduce(function(l,c){return l.replace(c,"")},i);o!==""&&o!=="*"&&a.add(o)}}}catch(l){r.e(l)}finally{r.f()}return a};function Un(e){if(B){var n;if(arguments.length>1&&arguments[1]!==void 0&&arguments[1])n=e;else if(h.searchPseudoElementsFullScan)n=e.querySelectorAll("*");else{var a,t=new Set,r=pe(document.styleSheets);try{for(r.s();!(a=r.n()).done;){var i=a.value;try{var o,l=pe(i.cssRules);try{for(l.s();!(o=l.n()).done;){var c,s=o.value,u=pe(Gt(s.selectorText));try{for(u.s();!(c=u.n()).done;){var d=c.value;t.add(d)}}catch(p){u.e(p)}finally{u.f()}}}catch(p){l.e(p)}finally{l.f()}}catch{h.searchPseudoElementsWarnings}}}catch(p){r.e(p)}finally{r.f()}if(!t.size)return;var m=Array.from(t).join(", ");try{n=e.querySelectorAll(m)}catch{}}return new Promise(function(p,v){var g=ee(n).filter(qt).map(Kt),b=fn("searchPseudoElements");Xa(),Promise.all(g).then(function(){b(),Ve(),p()}).catch(function(){b(),Ve(),v()})})}}var Yn=!1,Jn=function(e){return e.toLowerCase().split(" ").reduce(function(n,a){var t=a.toLowerCase().split("-"),r=t[0],i=t.slice(1).join("-");if(r&&i==="h")return n.flipX=!0,n;if(r&&i==="v")return n.flipY=!0,n;if(i=parseFloat(i),isNaN(i))return n;switch(r){case"grow":n.size=n.size+i;break;case"shrink":n.size=n.size-i;break;case"left":n.x=n.x-i;break;case"right":n.x=n.x+i;break;case"up":n.y=n.y-i;break;case"down":n.y=n.y+i;break;case"rotate":n.rotate=n.rotate+i}return n},{size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0})},Vt={mixout:function(){return{parse:{transform:function(e){return Jn(e)}}}},hooks:function(){return{parseNodeAttributes:function(e,n){var a=n.getAttribute("data-fa-transform");return a&&(e.transform=Jn(a)),e}}},provides:function(e){e.generateAbstractTransformGrouping=function(n){var a=n.main,t=n.transform,r=n.containerWidth,i=n.iconWidth,o={transform:"translate(".concat(r/2," 256)")},l="translate(".concat(32*t.x,", ").concat(32*t.y,") "),c="scale(".concat(t.size/16*(t.flipX?-1:1),", ").concat(t.size/16*(t.flipY?-1:1),") "),s="rotate(".concat(t.rotate," 0 0)"),u={outer:o,inner:{transform:"".concat(l," ").concat(c," ").concat(s)},path:{transform:"translate(".concat(i/2*-1," -256)")}};return{tag:"g",attributes:f({},u.outer),children:[{tag:"g",attributes:f({},u.inner),children:[{tag:a.icon.tag,children:a.icon.children,attributes:f(f({},a.icon.attributes),u.path)}]}]}}}},Pe={x:0,y:0,width:"100%",height:"100%"};function Hn(e){var n=!(arguments.length>1&&arguments[1]!==void 0)||arguments[1];return e.attributes&&(e.attributes.fill||n)&&(e.attributes.fill="black"),e}var ne,Xt={hooks:function(){return{parseNodeAttributes:function(e,n){var a=n.getAttribute("data-fa-mask"),t=a?we(a.split(" ").map(function(r){return r.trim()})):{prefix:null,iconName:null,rest:[]};return t.prefix||(t.prefix=J()),e.mask=t,e.maskId=n.getAttribute("data-fa-mask-id"),e}}},provides:function(e){e.generateAbstractMask=function(n){var a,t=n.children,r=n.attributes,i=n.main,o=n.mask,l=n.maskId,c=n.transform,s=i.width,u=i.icon,d=o.width,m=o.icon,p=(function(O){var j=O.transform,A=O.containerWidth,I=O.iconWidth,z={transform:"translate(".concat(A/2," 256)")},N="translate(".concat(32*j.x,", ").concat(32*j.y,") "),U="scale(".concat(j.size/16*(j.flipX?-1:1),", ").concat(j.size/16*(j.flipY?-1:1),") "),Se="rotate(".concat(j.rotate," 0 0)");return{outer:z,inner:{transform:"".concat(N," ").concat(U," ").concat(Se)},path:{transform:"translate(".concat(I/2*-1," -256)")}}})({transform:c,containerWidth:d,iconWidth:s}),v={tag:"rect",attributes:f(f({},Pe),{},{fill:"white"})},g=u.children?{children:u.children.map(Hn)}:{},b={tag:"g",attributes:f({},p.inner),children:[Hn(f({tag:u.tag,attributes:f(f({},u.attributes),p.path)},g))]},w={tag:"g",attributes:f({},p.outer),children:[b]},S="mask-".concat(l||wn()),F="clip-".concat(l||wn()),E={tag:"mask",attributes:f(f({},Pe),{},{id:S,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[v,w]},x={tag:"defs",children:[{tag:"clipPath",attributes:{id:F},children:(a=m,a.tag==="g"?a.children:[a])},E]};return t.push(x,{tag:"rect",attributes:f({fill:"currentColor","clip-path":"url(#".concat(F,")"),mask:"url(#".concat(S,")")},Pe)}),{children:t,attributes:r}}}};ne=fe,Pn=[kt,Bt,Ut,Yt,Jt,{hooks:function(){return{mutationObserverCallbacks:function(e){return e.pseudoElementsCallback=Un,e}}},provides:function(e){e.pseudoElements2svg=function(n){var a=n.node,t=a===void 0?k:a;h.searchPseudoElements&&Un(t)}}},{mixout:function(){return{dom:{unwatch:function(){Xa(),Yn=!0}}}},hooks:function(){return{bootstrap:function(){Cn(He("mutationObserverCallbacks",{}))},noAuto:function(){be&&be.disconnect()},watch:function(e){var n=e.observeMutationsRoot;Yn?Ve():Cn(He("mutationObserverCallbacks",{observeMutationsRoot:n}))}}}},Vt,Xt,{provides:function(e){var n=!1;Y.matchMedia&&(n=Y.matchMedia("(prefers-reduced-motion: reduce)").matches),e.missingIconAbstract=function(){var a=[],t={fill:"currentColor"},r={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};a.push({tag:"path",attributes:f(f({},t),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var i=f(f({},r),{},{attributeName:"opacity"}),o={tag:"circle",attributes:f(f({},t),{},{cx:"256",cy:"364",r:"28"}),children:[]};return n||o.children.push({tag:"animate",attributes:f(f({},r),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:f(f({},i),{},{values:"1;0;1;1;0;1;"})}),a.push(o),a.push({tag:"path",attributes:f(f({},t),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:n?[]:[{tag:"animate",attributes:f(f({},i),{},{values:"1;0;0;0;0;1;"})}]}),n||a.push({tag:"path",attributes:f(f({},t),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:f(f({},i),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:a}}}},{hooks:function(){return{parseNodeAttributes:function(e,n){var a=n.getAttribute("data-fa-symbol"),t=a!==null&&(a===""||a);return e.symbol=t,e}}}}],Z={},Object.keys(Q).forEach(function(e){Pt.indexOf(e)===-1&&delete Q[e]}),Pn.forEach(function(e){var n=e.mixout?e.mixout():{};if(Object.keys(n).forEach(function(t){typeof n[t]=="function"&&(ne[t]=n[t]),Qe(n[t])==="object"&&Object.keys(n[t]).forEach(function(r){ne[t]||(ne[t]={}),ne[t][r]=n[t][r]})}),e.hooks){var a=e.hooks();Object.keys(a).forEach(function(t){Z[t]||(Z[t]=[]),Z[t].push(a[t])})}e.provides&&e.provides(Q)});var ar=fe.library,$e=fe.parse,$t=fe.icon;function P(e,n,a){return(n=(function(t){var r=(function(i,o){if(typeof i!="object"||!i)return i;var l=i[Symbol.toPrimitive];if(l!==void 0){var c=l.call(i,o);if(typeof c!="object")return c;throw new TypeError("@@toPrimitive must return a primitive value.")}return(o==="string"?String:Number)(i)})(t,"string");return typeof r=="symbol"?r:r+""})(n))in e?Object.defineProperty(e,n,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[n]=a,e}function Kn(e,n){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var t=Object.getOwnPropertySymbols(e);n&&(t=t.filter(function(r){return Object.getOwnPropertyDescriptor(e,r).enumerable})),a.push.apply(a,t)}return a}function W(e){for(var n=1;n<arguments.length;n++){var a=arguments[n]!=null?arguments[n]:{};n%2?Kn(Object(a),!0).forEach(function(t){P(e,t,a[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):Kn(Object(a)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))})}return e}function Ze(e){return(Ze=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(n){return typeof n}:function(n){return n&&typeof Symbol=="function"&&n.constructor===Symbol&&n!==Symbol.prototype?"symbol":typeof n})(e)}function Oe(e,n){return Array.isArray(n)&&n.length>0||!Array.isArray(n)&&n?P({},e,n):{}}var Ie,qn,X,ue,Fe,de,ae,_n,Gn,Vn,Xn,$n,Zn,Qn,me,Le,Zt=typeof globalThis<"u"?globalThis:typeof window<"u"?window:un!==void 0?un:typeof self<"u"?self:{},Za={exports:{}};Ie=Za,qn=Zt,X=function(e,n,a){if(!Gn(n)||Xn(n)||$n(n)||Zn(n)||_n(n))return n;var t,r=0,i=0;if(Vn(n))for(t=[],i=n.length;r<i;r++)t.push(X(e,n[r],a));else for(var o in t={},n)Object.prototype.hasOwnProperty.call(n,o)&&(t[e(o,a)]=X(e,n[o],a));return t},ue=function(e){return Qn(e)?e:(e=e.replace(/[\-_\s]+(.)?/g,function(n,a){return a?a.toUpperCase():""})).substr(0,1).toLowerCase()+e.substr(1)},Fe=function(e){var n=ue(e);return n.substr(0,1).toUpperCase()+n.substr(1)},de=function(e,n){return(function(a,t){var r=(t=t||{}).separator||"_",i=t.split||/(?=[A-Z])/;return a.split(i).join(r)})(e,n).toLowerCase()},ae=Object.prototype.toString,_n=function(e){return typeof e=="function"},Gn=function(e){return e===Object(e)},Vn=function(e){return ae.call(e)=="[object Array]"},Xn=function(e){return ae.call(e)=="[object Date]"},$n=function(e){return ae.call(e)=="[object RegExp]"},Zn=function(e){return ae.call(e)=="[object Boolean]"},Qn=function(e){return(e-=0)==e},me=function(e,n){var a=n&&"process"in n?n.process:n;return typeof a!="function"?e:function(t,r){return a(t,e,r)}},Le={camelize:ue,decamelize:de,pascalize:Fe,depascalize:de,camelizeKeys:function(e,n){return X(me(ue,n),e)},decamelizeKeys:function(e,n){return X(me(de,n),e,n)},pascalizeKeys:function(e,n){return X(me(Fe,n),e)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}},Ie.exports?Ie.exports=Le:qn.humps=Le;var Qt=Za.exports,er=["class","style"];function Qa(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},a=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof e=="string")return e;var t=(e.children||[]).map(function(c){return Qa(c)}),r=Object.keys(e.attributes||{}).reduce(function(c,s){var u=e.attributes[s];switch(s){case"class":c.class=u.split(/\s+/).reduce(function(d,m){return d[m]=!0,d},{});break;case"style":c.style=u.split(";").map(function(d){return d.trim()}).filter(function(d){return d}).reduce(function(d,m){var p=m.indexOf(":"),v=Qt.camelize(m.slice(0,p)),g=m.slice(p+1).trim();return d[v]=g,d},{});break;default:c.attrs[s]=u}return c},{attrs:{},class:{},style:{}});a.class;var i=a.style,o=i===void 0?{}:i,l=(function(c,s){if(c==null)return{};var u,d,m=(function(v,g){if(v==null)return{};var b={};for(var w in v)if({}.hasOwnProperty.call(v,w)){if(g.indexOf(w)!==-1)continue;b[w]=v[w]}return b})(c,s);if(Object.getOwnPropertySymbols){var p=Object.getOwnPropertySymbols(c);for(d=0;d<p.length;d++)u=p[d],s.indexOf(u)===-1&&{}.propertyIsEnumerable.call(c,u)&&(m[u]=c[u])}return m})(a,er);return tt(e.tag,W(W(W({},n),{},{class:r.class,style:W(W({},r.style),o)},r.attrs),l),t)}var et=!1;try{et=!0}catch{}function ea(e){return e&&Ze(e)==="object"&&e.prefix&&e.iconName&&e.icon?e:$e.icon?$e.icon(e):e===null?null:Ze(e)==="object"&&e.prefix&&e.iconName?e:Array.isArray(e)&&e.length===2?{prefix:e[0],iconName:e[1]}:typeof e=="string"?{prefix:"fas",iconName:e}:void 0}var tr=nt({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(e){return[!0,!1,"horizontal","vertical","both"].indexOf(e)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},maskId:{type:String,default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(e){return["right","left"].indexOf(e)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(e){return[90,180,270].indexOf(Number.parseInt(e,10))>-1}},rotateBy:{type:Boolean,default:!1},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(e){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(e)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},titleId:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1},widthAuto:{type:Boolean,default:!1}},setup:function(e,n){var a=n.attrs,t=G(function(){return ea(e.icon)}),r=G(function(){return Oe("classes",(function(s){var u,d=(P(P(P(P(P(P(P(P(P(P(u={"fa-spin":s.spin,"fa-pulse":s.pulse,"fa-fw":s.fixedWidth,"fa-border":s.border,"fa-li":s.listItem,"fa-inverse":s.inverse,"fa-flip":s.flip===!0,"fa-flip-horizontal":s.flip==="horizontal"||s.flip==="both","fa-flip-vertical":s.flip==="vertical"||s.flip==="both"},"fa-".concat(s.size),s.size!==null),"fa-rotate-".concat(s.rotation),s.rotation!==null),"fa-rotate-by",s.rotateBy),"fa-pull-".concat(s.pull),s.pull!==null),"fa-swap-opacity",s.swapOpacity),"fa-bounce",s.bounce),"fa-shake",s.shake),"fa-beat",s.beat),"fa-fade",s.fade),"fa-beat-fade",s.beatFade),P(P(P(P(u,"fa-flash",s.flash),"fa-spin-pulse",s.spinPulse),"fa-spin-reverse",s.spinReverse),"fa-width-auto",s.widthAuto));return Object.keys(d).map(function(m){return d[m]?m:null}).filter(function(m){return m})})(e))}),i=G(function(){return Oe("transform",typeof e.transform=="string"?$e.transform(e.transform):e.transform)}),o=G(function(){return Oe("mask",ea(e.mask))}),l=G(function(){var s=W(W(W(W({},r.value),i.value),o.value),{},{symbol:e.symbol,maskId:e.maskId});return s.title=e.title,s.titleId=e.titleId,$t(t.value,s)});at(l,function(s){if(!s)return(function(){var u;!et&&console&&typeof console.error=="function"&&(u=console).error.apply(u,arguments)})("Could not find one or more icon(s)",t.value,o.value)},{immediate:!0});var c=G(function(){return l.value?Qa(l.value.abstract[0],{},a):null});return function(){return c.value}}}),rr={prefix:"fas",iconName:"right-long",icon:[576,512,["long-arrow-alt-right"],"f30b","M566.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-128 128c-9.2 9.2-22.9 11.9-34.9 6.9S384 396.9 384 384l0-64-336 0c-26.5 0-48-21.5-48-48l0-32c0-26.5 21.5-48 48-48l336 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l128 128z"]},ir={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-384c0-35.3-28.7-64-64-64L64 0zM96 64l192 0c17.7 0 32 14.3 32 32l0 32c0 17.7-14.3 32-32 32L96 160c-17.7 0-32-14.3-32-32l0-32c0-17.7 14.3-32 32-32zm16 168a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zM88 352a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zM64 424c0-13.3 10.7-24 24-24l112 0c13.3 0 24 10.7 24 24s-10.7 24-24 24L88 448c-13.3 0-24-10.7-24-24zm232-24c13.3 0 24 10.7 24 24s-10.7 24-24 24-24-10.7-24-24 10.7-24 24-24z"]},or={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4l-26.1 74.6 293.8 0-26.1-74.6C372.3 104.6 360.2 96 346.6 96L165.4 96c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32l181.2 0c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2l0 192c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-32-320 0 0 32c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32L0 256c0-26.7 16.4-49.6 39.6-59.2zM128 304a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},lr={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zM64 240l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm128 0l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zM64 368l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zm112 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16z"]},sr={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 0c0-17.7-14.3-32-32-32S224-17.7 224 0l0 256c0 17.7 14.3 32 32 32s32-14.3 32-32L288 0zM146.3 98.4c14.5-10.1 18-30.1 7.9-44.6s-30.1-18-44.6-7.9C43.4 92.1 0 169 0 256 0 397.4 114.6 512 256 512S512 397.4 512 256c0-87-43.4-163.9-109.7-210.1-14.5-10.1-34.4-6.6-44.6 7.9s-6.6 34.4 7.9 44.6c49.8 34.8 82.3 92.4 82.3 157.6 0 106-86 192-192 192S64 362 64 256c0-65.2 32.5-122.9 82.3-157.6z"]},fr={prefix:"fas",iconName:"eye",icon:[576,512,[128065],"f06e","M288 32c-80.8 0-145.5 36.8-192.6 80.6-46.8 43.5-78.1 95.4-93 131.1-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6s145.5-36.8 192.6-80.6c46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6zM144 256a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm144-64c0 35.3-28.7 64-64 64-11.5 0-22.3-3-31.7-8.4-1 10.9-.1 22.1 2.9 33.2 13.7 51.2 66.4 81.6 117.6 67.9s81.6-66.4 67.9-117.6c-12.2-45.7-55.5-74.8-101.1-70.8 5.3 9.3 8.4 20.1 8.4 31.7z"]},cr={prefix:"fas",iconName:"delete-left",icon:[640,512,[9003,"backspace"],"f55a","M576 128c0-35.3-28.7-64-64-64L205.3 64c-17 0-33.3 6.7-45.3 18.7L9.4 233.4c-6 6-9.4 14.1-9.4 22.6s3.4 16.6 9.4 22.6L160 429.3c12 12 28.3 18.7 45.3 18.7L512 448c35.3 0 64-28.7 64-64l0-256zM284.1 188.1c9.4-9.4 24.6-9.4 33.9 0l33.9 33.9 33.9-33.9c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-33.9 33.9 33.9 33.9c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-33.9-33.9-33.9 33.9c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l33.9-33.9-33.9-33.9c-9.4-9.4-9.4-24.6 0-33.9z"]},ur={prefix:"fas",iconName:"pen-to-square",icon:[512,512,["edit"],"f044","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L368 46.1 465.9 144 490.3 119.6c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L432 177.9 334.1 80 172.4 241.7zM96 64C43 64 0 107 0 160L0 416c0 53 43 96 96 96l256 0c53 0 96-43 96-96l0-96c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 96c0 17.7-14.3 32-32 32L96 448c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l96 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 64z"]},dr={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512 256 256 0 1 1 0-512zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},mr={prefix:"fas",iconName:"arrow-right-to-bracket",icon:[512,512,["sign-in"],"f090","M352 96l64 0c17.7 0 32 14.3 32 32l0 256c0 17.7-14.3 32-32 32l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l64 0c53 0 96-43 96-96l0-256c0-53-43-96-96-96l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32zm-9.4 182.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L242.7 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},pr={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM167 167c9.4-9.4 24.6-9.4 33.9 0l55 55 55-55c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-55 55 55 55c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-55-55-55 55c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l55-55-55-55c-9.4-9.4-9.4-24.6 0-33.9z"]},gr={prefix:"fas",iconName:"plug-circle-bolt",icon:[640,512,[],"e55b","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm177.4-77c-5.8-4.2-13.8-4-19.4 .5l-80 64c-5.3 4.2-7.4 11.4-5.1 17.8S433.2 416 440 416l32.9 0-15.9 42.4c-2.5 6.7-.2 14.3 5.6 18.6s13.8 4 19.4-.5l80-64c5.3-4.2 7.4-11.4 5.1-17.8S558.8 384 552 384l-32.9 0 15.9-42.4c2.5-6.7 .2-14.3-5.6-18.6z"]},hr={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l64 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-64 0z"]},br={prefix:"fas",iconName:"circle-user",icon:[512,512,[62142,"user-circle"],"f2bd","M399 384.2C376.9 345.8 335.4 320 288 320l-64 0c-47.4 0-88.9 25.8-111 64.2 35.2 39.2 86.2 63.8 143 63.8s107.8-24.7 143-63.8zM0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zm256 16a72 72 0 1 0 0-144 72 72 0 1 0 0 144z"]},yr={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 64c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l16 0c35.3 0 64 28.7 64 64l0 256c0 35.3-28.7 64-64 64L64 448c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l16 0zM392 184c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 32-32 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l32 0 0 32c0 13.3 10.7 24 24 24s24-10.7 24-24l0-32 32 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-32 0 0-32zM64 240c0 13.3 10.7 24 24 24l112 0c13.3 0 24-10.7 24-24s-10.7-24-24-24L88 216c-13.3 0-24 10.7-24 24z"]},vr={prefix:"fas",iconName:"wrench",icon:[576,512,[128295],"f0ad","M509.4 98.6c7.6-7.6 20.3-5.7 24.1 4.3 6.8 17.7 10.5 37 10.5 57.1 0 88.4-71.6 160-160 160-17.5 0-34.4-2.8-50.2-8L146.9 498.9c-28.1 28.1-73.7 28.1-101.8 0s-28.1-73.7 0-101.8L232 210.2c-5.2-15.8-8-32.6-8-50.2 0-88.4 71.6-160 160-160 20.1 0 39.4 3.7 57.1 10.5 10 3.8 11.8 16.5 4.3 24.1l-88.7 88.7c-3 3-4.7 7.1-4.7 11.3l0 41.4c0 8.8 7.2 16 16 16l41.4 0c4.2 0 8.3-1.7 11.3-4.7l88.7-88.7z"]},xr={prefix:"fas",iconName:"eraser",icon:[576,512,[],"f12d","M178.5 416l123 0 65.3-65.3-173.5-173.5-126.7 126.7 112 112zM224 480l-45.5 0c-17 0-33.3-6.7-45.3-18.7L17 345C6.1 334.1 0 319.4 0 304s6.1-30.1 17-41L263 17C273.9 6.1 288.6 0 304 0s30.1 6.1 41 17L527 199c10.9 10.9 17 25.6 17 41s-6.1 30.1-17 41l-135 135 120 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-288 0z"]},wr={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M64 64C64 28.7 92.7 0 128 0L288 0c35.3 0 64 28.7 64 64l0 224c44.2 0 80 35.8 80 80l0 12c0 11 9 20 20 20s20-9 20-20l0-127.7c-32.5-10.2-56-40.5-56-76.3l0-32c0-8.8 7.2-16 16-16l16 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 32 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 16 0c8.8 0 16 7.2 16 16l0 32c0 35.8-23.5 66.1-56 76.3L520 380c0 37.6-30.4 68-68 68s-68-30.4-68-68l0-12c0-17.7-14.3-32-32-32l0 129.4c9.3 3.3 16 12.2 16 22.6 0 13.3-10.7 24-24 24L72 512c-13.3 0-24-10.7-24-24 0-10.5 6.7-19.3 16-22.6L64 64zm82.7 125.7l39 0-20.9 66.9c-2.4 7.6 3.3 15.4 11.3 15.4 2.9 0 5.6-1 7.8-2.9l94.6-82c3.1-2.7 4.9-6.6 4.9-10.7 0-7.8-6.3-14.1-14.1-14.1l-39 0 20.9-66.9c2.4-7.6-3.3-15.4-11.3-15.4-2.9 0-5.6 1-7.8 2.9l-94.6 82c-3.1 2.7-4.9 6.6-4.9 10.7 0 7.8 6.3 14.1 14.1 14.1z"]},kr={prefix:"fas",iconName:"house",icon:[512,512,[127968,63498,63500,"home","home-alt","home-lg-alt"],"f015","M277.8 8.6c-12.3-11.4-31.3-11.4-43.5 0l-224 208c-9.6 9-12.8 22.9-8 35.1S18.8 272 32 272l16 0 0 176c0 35.3 28.7 64 64 64l288 0c35.3 0 64-28.7 64-64l0-176 16 0c13.2 0 25-8.1 29.8-20.3s1.6-26.2-8-35.1l-224-208zM240 320l32 0c26.5 0 48 21.5 48 48l0 96-128 0 0-96c0-26.5 21.5-48 48-48z"]},Sr={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64 0-16.2-6-31.1-16-42.3l69.5-138.9c5.9-11.9 1.1-26.3-10.7-32.2s-26.3-1.1-32.2 10.7L261.1 288.2c-1.7-.1-3.4-.2-5.1-.2-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},zr={prefix:"fas",iconName:"right-left",icon:[512,512,["exchange-alt"],"f362","M502.6 150.6l-96 96c-9.2 9.2-22.9 11.9-34.9 6.9S352 236.9 352 224l0-64-320 0c-17.7 0-32-14.3-32-32S14.3 96 32 96l320 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l96 96c12.5 12.5 12.5 32.8 0 45.3zm-397.3 352l-96-96c-12.5-12.5-12.5-32.8 0-45.3l96-96c9.2-9.2 22.9-11.9 34.9-6.9S160 275.1 160 288l0 64 320 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-320 0 0 64c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9z"]},jr={prefix:"fas",iconName:"lock-open",icon:[576,512,[],"f3c1","M384 96c0-35.3 28.7-64 64-64s64 28.7 64 64l0 32c0 17.7 14.3 32 32 32s32-14.3 32-32l0-32c0-70.7-57.3-128-128-128S320 25.3 320 96l0 64-160 0c-35.3 0-64 28.7-64 64l0 224c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-224c0-35.3-28.7-64-64-64l-32 0 0-64z"]},Ar={prefix:"fas",iconName:"circle-check",icon:[512,512,[61533,"check-circle"],"f058","M256 512a256 256 0 1 1 0-512 256 256 0 1 1 0 512zM374 145.7c-10.7-7.8-25.7-5.4-33.5 5.3L221.1 315.2 169 263.1c-9.4-9.4-24.6-9.4-33.9 0s-9.4 24.6 0 33.9l72 72c5 5 11.8 7.5 18.8 7s13.4-4.1 17.5-9.8L379.3 179.2c7.8-10.7 5.4-25.7-5.3-33.5z"]},Nr={prefix:"fas",iconName:"plug-circle-xmark",icon:[640,512,[],"e560","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM496 256a144 144 0 1 1 0 288 144 144 0 1 1 0-288zm59.3 107.3c6.2-6.2 6.2-16.4 0-22.6s-16.4-6.2-22.6 0l-36.7 36.7-36.7-36.7c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l36.7 36.7-36.7 36.7c-6.2 6.2-6.2 16.4 0 22.6s16.4 6.2 22.6 0l36.7-36.7 36.7 36.7c6.2 6.2 16.4 6.2 22.6 0s6.2-16.4 0-22.6l-36.7-36.7 36.7-36.7z"]},Mr={prefix:"fas",iconName:"solar-panel",icon:[576,512,[],"f5ba","M121.8 32c-30 0-56 20.8-62.5 50.1L9.6 306.1C.7 346.1 31.1 384 72 384l184.1 0 0 64-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l192 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0 0-64 184.1 0c40.9 0 71.4-37.9 62.5-77.9l-49.8-224C510.4 52.8 484.5 32 454.5 32L121.8 32zM245.6 96l85.2 0 7.3 88-99.8 0 7.3-88zm-55.5 88l-87.8 0 19.6-88 75.6 0-7.3 88zM91.6 232l94.5 0-7.3 88-106.7 0 19.6-88zm142.6 0l107.8 0 7.3 88-122.5 0 7.3-88zm156 0l94.5 0 19.6 88-106.7 0-7.3-88zM474 184l-87.8 0-7.3-88 75.6 0 19.6 88z"]},Pr={prefix:"fas",iconName:"plug-circle-check",icon:[640,512,[],"e55c","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm201.4-60.9c-7.1-5.2-17.2-3.6-22.4 3.5l-53 72.9-26.8-26.8c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l40 40c3.3 3.3 7.9 5 12.6 4.6s8.9-2.8 11.7-6.5l64-88c5.2-7.1 3.6-17.2-3.5-22.3z"]},Or={prefix:"fas",iconName:"star",icon:[576,512,[11088,61446],"f005","M309.5-18.9c-4.1-8-12.4-13.1-21.4-13.1s-17.3 5.1-21.4 13.1L193.1 125.3 33.2 150.7c-8.9 1.4-16.3 7.7-19.1 16.3s-.5 18 5.8 24.4l114.4 114.5-25.2 159.9c-1.4 8.9 2.3 17.9 9.6 23.2s16.9 6.1 25 2L288.1 417.6 432.4 491c8 4.1 17.7 3.3 25-2s11-14.2 9.6-23.2L441.7 305.9 556.1 191.4c6.4-6.4 8.6-15.8 5.8-24.4s-10.1-14.9-19.1-16.3L383 125.3 309.5-18.9z"]},Ir={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 0c14.7 0 28.2 8.1 35.2 21l216 400c6.7 12.4 6.4 27.4-.8 39.5S486.1 480 472 480L40 480c-14.1 0-27.2-7.4-34.4-19.5s-7.5-27.1-.8-39.5l216-400c7-12.9 20.5-21 35.2-21zm0 352a32 32 0 1 0 0 64 32 32 0 1 0 0-64zm0-192c-18.2 0-32.7 15.5-31.4 33.7l7.4 104c.9 12.5 11.4 22.3 23.9 22.3 12.6 0 23-9.7 23.9-22.3l7.4-104c1.3-18.2-13.1-33.7-31.4-33.7z"]},Fr={prefix:"fas",iconName:"lock",icon:[384,512,[128274],"f023","M128 96l0 64 128 0 0-64c0-35.3-28.7-64-64-64s-64 28.7-64 64zM64 160l0-64C64 25.3 121.3-32 192-32S320 25.3 320 96l0 64c35.3 0 64 28.7 64 64l0 224c0 35.3-28.7 64-64 64L64 512c-35.3 0-64-28.7-64-64L0 224c0-35.3 28.7-64 64-64z"]},Lr={prefix:"fas",iconName:"arrow-right-from-bracket",icon:[512,512,["sign-out"],"f08b","M160 96c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 32C43 32 0 75 0 128L0 384c0 53 43 96 96 96l64 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l64 0zM502.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L402.7 224 192 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},Cr={prefix:"fas",iconName:"eye-slash",icon:[576,512,[],"f070","M41-24.9c-9.4-9.4-24.6-9.4-33.9 0S-2.3-.3 7 9.1l528 528c9.4 9.4 24.6 9.4 33.9 0s9.4-24.6 0-33.9l-96.4-96.4c2.7-2.4 5.4-4.8 8-7.2 46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6-56.8 0-105.6 18.2-146 44.2L41-24.9zM204.5 138.7c23.5-16.8 52.4-26.7 83.5-26.7 79.5 0 144 64.5 144 144 0 31.1-9.9 59.9-26.7 83.5l-34.7-34.7c12.7-21.4 17-47.7 10.1-73.7-13.7-51.2-66.4-81.6-117.6-67.9-8.6 2.3-16.7 5.7-24 10l-34.7-34.7zM325.3 395.1c-11.9 3.2-24.4 4.9-37.3 4.9-79.5 0-144-64.5-144-144 0-12.9 1.7-25.4 4.9-37.3L69.4 139.2c-32.6 36.8-55 75.8-66.9 104.5-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6 37.3 0 71.2-7.9 101.5-20.6l-64.2-64.2z"]},Er={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M338.8-9.9c11.9 8.6 16.3 24.2 10.9 37.8L271.3 224 416 224c13.5 0 25.5 8.4 30.1 21.1s.7 26.9-9.6 35.5l-288 240c-11.3 9.4-27.4 9.9-39.3 1.3s-16.3-24.2-10.9-37.8L176.7 288 32 288c-13.5 0-25.5-8.4-30.1-21.1s-.7-26.9 9.6-35.5l288-240c11.3-9.4 27.4-9.9 39.3-1.3z"]},Dr={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M256 64c-56.8 0-107.9 24.7-143.1 64l47.1 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 192c-17.7 0-32-14.3-32-32L0 32C0 14.3 14.3 0 32 0S64 14.3 64 32l0 54.7C110.9 33.6 179.5 0 256 0 397.4 0 512 114.6 512 256S397.4 512 256 512c-87 0-163.9-43.4-210.1-109.7-10.1-14.5-6.6-34.4 7.9-44.6s34.4-6.6 44.6 7.9c34.8 49.8 92.4 82.3 157.6 82.3 106 0 192-86 192-192S362 64 256 64z"]},Tr={prefix:"fas",iconName:"coins",icon:[512,512,[],"f51e","M128 96l0-16c0-44.2 86-80 192-80S512 35.8 512 80l0 16c0 30.6-41.3 57.2-102 70.7-2.4-2.8-4.9-5.5-7.4-8-15.5-15.3-35.5-26.9-56.4-35.5-41.9-17.5-96.5-27.1-154.2-27.1-21.9 0-43.3 1.4-63.8 4.1-.2-1.3-.2-2.7-.2-4.1zM432 353l0-46.2c15.1-3.9 29.3-8.5 42.2-13.9 13.2-5.5 26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zm0-96l0-33c0-4.5-.4-8.8-1-13 15.5-3.9 30-8.6 43.2-14.2s26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zM0 240l0-16c0-44.2 86-80 192-80s192 35.8 192 80l0 16c0 44.2-86 80-192 80S0 284.2 0 240zm384 96c0 44.2-86 80-192 80S0 380.2 0 336l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3l0 15.4zm0 80.6l0 15.4c0 44.2-86 80-192 80S0 476.2 0 432l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3z"]},Rr={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-192 0z"]},Wr={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM224 160a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm-8 64l48 0c13.3 0 24 10.7 24 24l0 88 8 0c13.3 0 24 10.7 24 24s-10.7 24-24 24l-80 0c-13.3 0-24-10.7-24-24s10.7-24 24-24l24 0 0-64-24 0c-13.3 0-24-10.7-24-24s10.7-24 24-24z"]},Br={prefix:"far",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M464 256a208 208 0 1 1 -416 0 208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0 256 256 0 1 0 -512 0zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},Ur={prefix:"far",iconName:"star",icon:[576,512,[11088,61446],"f005","M288.1-32c9 0 17.3 5.1 21.4 13.1L383 125.3 542.9 150.7c8.9 1.4 16.3 7.7 19.1 16.3s.5 18-5.8 24.4L441.7 305.9 467 465.8c1.4 8.9-2.3 17.9-9.6 23.2s-17 6.1-25 2L288.1 417.6 143.8 491c-8 4.1-17.7 3.3-25-2s-11-14.2-9.6-23.2L134.4 305.9 20 191.4c-6.4-6.4-8.6-15.8-5.8-24.4s10.1-14.9 19.1-16.3l159.9-25.4 73.6-144.2c4.1-8 12.4-13.1 21.4-13.1zm0 76.8L230.3 158c-3.5 6.8-10 11.6-17.6 12.8l-125.5 20 89.8 89.9c5.4 5.4 7.9 13.1 6.7 20.7l-19.8 125.5 113.3-57.6c6.8-3.5 14.9-3.5 21.8 0l113.3 57.6-19.8-125.5c-1.2-7.6 1.3-15.3 6.7-20.7l89.8-89.9-125.5-20c-7.6-1.2-14.1-6-17.6-12.8L288.1 44.8z"]};export{Br as A,Er as B,hr as C,Rr as D,lr as E,tr as F,zr as G,rr as H,Tr as I,Nr as J,Pr as K,gr as L,Dr as M,sr as N,xr as a,Fr as b,jr as c,br as d,mr as e,cr as f,Lr as g,fr as h,Cr as i,Sr as j,yr as k,ar as l,Mr as m,kr as n,wr as o,Ar as p,Ir as q,pr as r,ir as s,vr as t,or as u,ur as v,Wr as w,Or as x,Ur as y,dr as z};
