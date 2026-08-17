import{g as pa,d as ue,w as me,c as V,h as gt}from"./vendor-SSn4Ws0e.js";function Bt(t,a){(a==null||a>t.length)&&(a=t.length);for(var n=0,e=Array(a);n<a;n++)e[n]=t[n];return e}function de(t,a,n){return a&&(function(e,i){for(var r=0;r<i.length;r++){var o=i[r];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,rn(o.key),o)}})(t.prototype,a),Object.defineProperty(t,"prototype",{writable:!1}),t}function pt(t,a){var n=typeof Symbol<"u"&&t[Symbol.iterator]||t["@@iterator"];if(!n){if(Array.isArray(t)||(n=ra(t))||a){n&&(t=n);var e=0,i=function(){};return{s:i,n:function(){return e>=t.length?{done:!0}:{done:!1,value:t[e++]}},e:function(c){throw c},f:i}}throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var r,o=!0,s=!1;return{s:function(){n=n.call(t)},n:function(){var c=n.next();return o=c.done,c},e:function(c){s=!0,r=c},f:function(){try{o||n.return==null||n.return()}finally{if(s)throw r}}}}function h(t,a,n){return(a=rn(a))in t?Object.defineProperty(t,a,{value:n,enumerable:!0,configurable:!0,writable:!0}):t[a]=n,t}function ba(t,a){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(t);a&&(e=e.filter(function(i){return Object.getOwnPropertyDescriptor(t,i).enumerable})),n.push.apply(n,e)}return n}function f(t){for(var a=1;a<arguments.length;a++){var n=arguments[a]!=null?arguments[a]:{};a%2?ba(Object(n),!0).forEach(function(e){h(t,e,n[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):ba(Object(n)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))})}return t}function yt(t,a){return(function(n){if(Array.isArray(n))return n})(t)||(function(n,e){var i=n==null?null:typeof Symbol<"u"&&n[Symbol.iterator]||n["@@iterator"];if(i!=null){var r,o,s,c,l=[],u=!0,d=!1;try{if(s=(i=i.call(n)).next,e===0){if(Object(i)!==i)return;u=!1}else for(;!(u=(r=s.call(i)).done)&&(l.push(r.value),l.length!==e);u=!0);}catch(m){d=!0,o=m}finally{try{if(!u&&i.return!=null&&(c=i.return(),Object(c)!==c))return}finally{if(d)throw o}}return l}})(t,a)||ra(t,a)||(function(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)})()}function D(t){return(function(a){if(Array.isArray(a))return Bt(a)})(t)||(function(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)})(t)||ra(t)||(function(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)})()}function rn(t){var a=(function(n,e){if(typeof n!="object"||!n)return n;var i=n[Symbol.toPrimitive];if(i!==void 0){var r=i.call(n,e);if(typeof r!="object")return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return(e==="string"?String:Number)(n)})(t,"string");return typeof a=="symbol"?a:a+""}function ia(t){return(ia=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(a){return typeof a}:function(a){return a&&typeof Symbol=="function"&&a.constructor===Symbol&&a!==Symbol.prototype?"symbol":typeof a})(t)}function ra(t,a){if(t){if(typeof t=="string")return Bt(t,a);var n={}.toString.call(t).slice(8,-1);return n==="Object"&&t.constructor&&(n=t.constructor.name),n==="Map"||n==="Set"?Array.from(t):n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?Bt(t,a):void 0}}var ha=function(){},oa={},on={},ln=null,sn={mark:ha,measure:ha};try{typeof window<"u"&&(oa=window),typeof document<"u"&&(on=document),typeof MutationObserver<"u"&&(ln=MutationObserver),typeof performance<"u"&&(sn=performance)}catch{}var va=(oa.navigator||{}).userAgent,ya=va===void 0?"":va,U=oa,S=on,xa=ln,ct=sn;U.document;var jt,R=!!S.documentElement&&!!S.head&&typeof S.addEventListener=="function"&&typeof S.createElement=="function",fn=~ya.indexOf("MSIE")||~ya.indexOf("Trident/"),cn={classic:{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fab:"brands","fa-brands":"brands"},duotone:{fa:"solid",fad:"solid","fa-solid":"solid","fa-duotone":"solid",fadr:"regular","fa-regular":"regular",fadl:"light","fa-light":"light",fadt:"thin","fa-thin":"thin"},sharp:{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light",fast:"thin","fa-thin":"thin"},"sharp-duotone":{fa:"solid",fasds:"solid","fa-solid":"solid",fasdr:"regular","fa-regular":"regular",fasdl:"light","fa-light":"light",fasdt:"thin","fa-thin":"thin"},slab:{"fa-regular":"regular",faslr:"regular"},"slab-press":{"fa-regular":"regular",faslpr:"regular"},"slab-duo":{"fa-regular":"regular",fasldr:"regular"},"slab-press-duo":{"fa-regular":"regular",faslpdr:"regular"},thumbprint:{"fa-light":"light",fatl:"light"},vellum:{"fa-solid":"solid",favs:"solid"},pixel:{"fa-regular":"regular",fapr:"regular"},mosaic:{"fa-solid":"solid",fams:"solid"},whiteboard:{"fa-semibold":"semibold",fawsb:"semibold"},notdog:{"fa-solid":"solid",fans:"solid"},"notdog-duo":{"fa-solid":"solid",fands:"solid"},etch:{"fa-solid":"solid",faes:"solid"},graphite:{"fa-thin":"thin",fagt:"thin"},jelly:{"fa-regular":"regular",fajr:"regular"},"jelly-fill":{"fa-regular":"regular",fajfr:"regular"},"jelly-duo":{"fa-regular":"regular",fajdr:"regular"},chisel:{"fa-regular":"regular",facr:"regular"},utility:{"fa-semibold":"semibold",fausb:"semibold"},"utility-duo":{"fa-semibold":"semibold",faudsb:"semibold"},"utility-fill":{"fa-semibold":"semibold",faufsb:"semibold"}},un=["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-slab-press-duo","fa-slab-duo","fa-mosaic","fa-pixel","fa-vellum","fa-utility","fa-utility-duo","fa-utility-fill"],F="classic",ot="duotone",mn="sharp",dn="sharp-duotone",gn="chisel",pn="etch",bn="graphite",hn="jelly",vn="jelly-duo",yn="jelly-fill",xn="mosaic",zn="notdog",wn="notdog-duo",Sn="pixel",kn="slab",jn="slab-duo",An="slab-press",Pn="slab-press-duo",Nn="thumbprint",Mn="utility",In="utility-duo",Fn="utility-fill",On="vellum",Ln="whiteboard",Cn=[F,ot,mn,dn,gn,pn,bn,hn,vn,yn,xn,zn,wn,Sn,kn,jn,An,Pn,Nn,Mn,In,Fn,On,Ln];h(h(h(h(h(h(h(h(h(h(jt={},F,"Classic"),ot,"Duotone"),mn,"Sharp"),dn,"Sharp Duotone"),gn,"Chisel"),pn,"Etch"),bn,"Graphite"),hn,"Jelly"),vn,"Jelly Duo"),yn,"Jelly Fill"),h(h(h(h(h(h(h(h(h(h(jt,xn,"Mosaic"),zn,"Notdog"),wn,"Notdog Duo"),Sn,"Pixel"),kn,"Slab"),jn,"Slab Duo"),An,"Slab Press"),Pn,"Slab Press Duo"),Nn,"Thumbprint"),Mn,"Utility"),h(h(h(h(jt,In,"Utility Duo"),Fn,"Utility Fill"),On,"Vellum"),Ln,"Whiteboard");var ge=new Map([["classic",{defaultShortPrefixId:"fas",defaultStyleId:"solid",styleIds:["solid","regular","light","thin","brands"],futureStyleIds:[],defaultFontWeight:900}],["duotone",{defaultShortPrefixId:"fad",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp",{defaultShortPrefixId:"fass",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp-duotone",{defaultShortPrefixId:"fasds",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["chisel",{defaultShortPrefixId:"facr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["etch",{defaultShortPrefixId:"faes",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["graphite",{defaultShortPrefixId:"fagt",defaultStyleId:"thin",styleIds:["thin"],futureStyleIds:[],defaultFontWeight:100}],["jelly",{defaultShortPrefixId:"fajr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-duo",{defaultShortPrefixId:"fajdr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-fill",{defaultShortPrefixId:"fajfr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["mosaic",{defaultShortPrefixId:"fams",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["notdog",{defaultShortPrefixId:"fans",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["notdog-duo",{defaultShortPrefixId:"fands",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["pixel",{defaultShortPrefixId:"fapr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab",{defaultShortPrefixId:"faslr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab-duo",{defaultShortPrefixId:"fasldr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab-press",{defaultShortPrefixId:"faslpr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab-press-duo",{defaultShortPrefixId:"faslpdr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["thumbprint",{defaultShortPrefixId:"fatl",defaultStyleId:"light",styleIds:["light"],futureStyleIds:[],defaultFontWeight:300}],["utility",{defaultShortPrefixId:"fausb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-duo",{defaultShortPrefixId:"faudsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-fill",{defaultShortPrefixId:"faufsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["vellum",{defaultShortPrefixId:"favs",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["whiteboard",{defaultShortPrefixId:"fawsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}]]),En=["fak","fa-kit","fakd","fa-kit-duotone"],pe={fak:"kit","fa-kit":"kit"},be={fakd:"kit-duotone","fa-kit-duotone":"kit-duotone"};h(h({},"kit","Kit"),"kit-duotone","Kit Duotone");var At,he={kit:"fak"},ve={"kit-duotone":"fakd"},ye="duotone-group",xe="swap-opacity",ze="primary",we="secondary";h(h(h(h(h(h(h(h(h(h(At={},"classic","Classic"),"duotone","Duotone"),"sharp","Sharp"),"sharp-duotone","Sharp Duotone"),"chisel","Chisel"),"etch","Etch"),"graphite","Graphite"),"jelly","Jelly"),"jelly-duo","Jelly Duo"),"jelly-fill","Jelly Fill"),h(h(h(h(h(h(h(h(h(h(At,"mosaic","Mosaic"),"notdog","Notdog"),"notdog-duo","Notdog Duo"),"pixel","Pixel"),"slab","Slab"),"slab-duo","Slab Duo"),"slab-press","Slab Press"),"slab-press-duo","Slab Press Duo"),"thumbprint","Thumbprint"),"utility","Utility"),h(h(h(h(At,"utility-duo","Utility Duo"),"utility-fill","Utility Fill"),"vellum","Vellum"),"whiteboard","Whiteboard");h(h({},"kit","Kit"),"kit-duotone","Kit Duotone");var Rt={classic:{fab:"fa-brands",fad:"fa-duotone",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"},duotone:{fadr:"fa-regular",fadl:"fa-light",fadt:"fa-thin"},sharp:{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light",fast:"fa-thin"},"sharp-duotone":{fasds:"fa-solid",fasdr:"fa-regular",fasdl:"fa-light",fasdt:"fa-thin"},slab:{faslr:"fa-regular"},"slab-press":{faslpr:"fa-regular"},"slab-duo":{fasldr:"fa-regular"},"slab-press-duo":{faslpdr:"fa-regular"},pixel:{fapr:"fa-regular"},mosaic:{fams:"fa-solid"},vellum:{favs:"fa-solid"},whiteboard:{fawsb:"fa-semibold"},thumbprint:{fatl:"fa-light"},notdog:{fans:"fa-solid"},"notdog-duo":{fands:"fa-solid"},etch:{faes:"fa-solid"},graphite:{fagt:"fa-thin"},jelly:{fajr:"fa-regular"},"jelly-fill":{fajfr:"fa-regular"},"jelly-duo":{fajdr:"fa-regular"},chisel:{facr:"fa-regular"},utility:{fausb:"fa-semibold"},"utility-duo":{faudsb:"fa-semibold"},"utility-fill":{faufsb:"fa-semibold"}},Dn=["fa","fas","far","fal","fat","fad","fadr","fadl","fadt","fab","fass","fasr","fasl","fast","fasds","fasdr","fasdl","fasdt","faslr","faslpr","fasldr","faslpdr","fapr","fams","favs","fawsb","fatl","fans","fands","faes","fagt","fajr","fajfr","fajdr","facr","fausb","faudsb","faufsb"].concat(["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-slab-press-duo","fa-slab-duo","fa-mosaic","fa-pixel","fa-vellum","fa-utility","fa-utility-duo","fa-utility-fill"],["fa-solid","fa-regular","fa-light","fa-thin","fa-duotone","fa-brands","fa-semibold"]),Tn=[1,2,3,4,5,6,7,8,9,10],Se=Tn.concat([11,12,13,14,15,16,17,18,19,20]),ke=[].concat(D(Object.keys({classic:["fas","far","fal","fat","fad"],duotone:["fadr","fadl","fadt"],sharp:["fass","fasr","fasl","fast"],"sharp-duotone":["fasds","fasdr","fasdl","fasdt"],slab:["faslr"],"slab-press":["faslpr"],"slab-duo":["fasldr"],"slab-press-duo":["faslpdr"],pixel:["fapr"],mosaic:["fams"],vellum:["favs"],whiteboard:["fawsb"],thumbprint:["fatl"],notdog:["fans"],"notdog-duo":["fands"],etch:["faes"],graphite:["fagt"],jelly:["fajr"],"jelly-fill":["fajfr"],"jelly-duo":["fajdr"],chisel:["facr"],utility:["fausb"],"utility-duo":["faudsb"],"utility-fill":["faufsb"]})),["solid","regular","light","thin","duotone","brands","semibold"],["aw","fw","pull-left","pull-right"],["2xs","xs","sm","lg","xl","2xl","beat","beat-fade","border","bounce","buzz","canvas-square","canvas-roomy","fade","flip-360","flip-both","flip-horizontal","flip-vertical","flip","float","inverse","jello","layers","layers-bottom-left","layers-bottom-right","layers-counter","layers-text","layers-top-left","layers-top-right","li","pull-end","pull-start","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","spin-snap","spin-snap-4","spin-snap-8","stack-1x","stack-2x","stack","swing","ul","wag","width-auto","width-fixed",ye,xe,ze,we]).concat(Tn.map(function(t){return"".concat(t,"x")})).concat(Se.map(function(t){return"w-".concat(t)})),W="___FONT_AWESOME___",Wn="svg-inline--fa",H="data-fa-i2svg",Xt="data-fa-pseudo-element",Ut="data-prefix",Yt="data-icon",za="fontawesome-i2svg",je=["HTML","HEAD","STYLE","SCRIPT"],Bn=["::before","::after",":before",":after"],Rn=(function(){try{return!0}catch{return!1}})();function lt(t){return new Proxy(t,{get:function(a,n){return n in a?a[n]:a[F]}})}var Xn=f({},cn);Xn[F]=f(f(f(f({},{"fa-duotone":"duotone"}),cn[F]),pe),be);var Ae=lt(Xn),qt=f({},{chisel:{regular:"facr"},classic:{brands:"fab",light:"fal",regular:"far",solid:"fas",thin:"fat"},duotone:{light:"fadl",regular:"fadr",solid:"fad",thin:"fadt"},etch:{solid:"faes"},graphite:{thin:"fagt"},jelly:{regular:"fajr"},"jelly-duo":{regular:"fajdr"},"jelly-fill":{regular:"fajfr"},mosaic:{solid:"fams"},notdog:{solid:"fans"},"notdog-duo":{solid:"fands"},pixel:{regular:"fapr"},sharp:{light:"fasl",regular:"fasr",solid:"fass",thin:"fast"},"sharp-duotone":{light:"fasdl",regular:"fasdr",solid:"fasds",thin:"fasdt"},slab:{regular:"faslr"},"slab-duo":{regular:"fasldr"},"slab-press":{regular:"faslpr"},"slab-press-duo":{regular:"faslpdr"},thumbprint:{light:"fatl"},utility:{semibold:"fausb"},"utility-duo":{semibold:"faudsb"},"utility-fill":{semibold:"faufsb"},vellum:{solid:"favs"},whiteboard:{semibold:"fawsb"}});qt[F]=f(f(f(f({},{duotone:"fad"}),qt[F]),he),ve);var wa=lt(qt),Jt=f({},Rt);Jt[F]=f(f({},Jt[F]),{fak:"fa-kit"});var la=lt(Jt),Pt=f({},{classic:{"fa-brands":"fab","fa-duotone":"fad","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"},duotone:{"fa-regular":"fadr","fa-light":"fadl","fa-thin":"fadt"},sharp:{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl","fa-thin":"fast"},"sharp-duotone":{"fa-solid":"fasds","fa-regular":"fasdr","fa-light":"fasdl","fa-thin":"fasdt"},slab:{"fa-regular":"faslr"},"slab-press":{"fa-regular":"faslpr"},"slab-duo":{"fa-regular":"fasldr"},"slab-press-duo":{"fa-regular":"faslpdr"},pixel:{"fa-regular":"fapr"},mosaic:{"fa-solid":"fams"},vellum:{"fa-solid":"favs"},whiteboard:{"fa-semibold":"fawsb"},thumbprint:{"fa-light":"fatl"},notdog:{"fa-solid":"fans"},"notdog-duo":{"fa-solid":"fands"},etch:{"fa-solid":"faes"},graphite:{"fa-thin":"fagt"},jelly:{"fa-regular":"fajr"},"jelly-fill":{"fa-regular":"fajfr"},"jelly-duo":{"fa-regular":"fajdr"},chisel:{"fa-regular":"facr"},utility:{"fa-semibold":"fausb"},"utility-duo":{"fa-semibold":"faudsb"},"utility-fill":{"fa-semibold":"faufsb"}});Pt[F]=f(f({},Pt[F]),{"fa-kit":"fak"}),lt(Pt);var Pe=/fa(k|kd|s|r|l|t|d|dr|dl|dt|b|slr|slpr|wsb|tl|ns|nds|es|gt|jr|jfr|jdr|usb|ufsb|udsb|cr|ss|sr|sl|st|sds|sdr|sdl|sdt|sldr|slpdr|pr|ms|vs)?[\-\ ]/,Un="fa-layers-text",Ne=/Font ?Awesome ?([567 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp Duotone|Sharp|Kit|Notdog Duo|Notdog|Chisel|Etch|Graphite|Thumbprint|Jelly Fill|Jelly Duo|Jelly|Utility|Utility Fill|Utility Duo|Slab Press|Slab|Slab Duo|Slab Press Duo|Pixel|Mosaic|Vellum|Whiteboard)?.*/i;lt(f({},{classic:{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},duotone:{900:"fad",400:"fadr",300:"fadl",100:"fadt"},sharp:{900:"fass",400:"fasr",300:"fasl",100:"fast"},"sharp-duotone":{900:"fasds",400:"fasdr",300:"fasdl",100:"fasdt"},slab:{400:"faslr"},"slab-press":{400:"faslpr"},"slab-duo":{400:"fasldr"},"slab-press-duo":{400:"faslpdr"},vellum:{900:"favs"},mosaic:{900:"fams"},pixel:{400:"fapr"},whiteboard:{600:"fawsb"},thumbprint:{300:"fatl"},notdog:{900:"fans"},"notdog-duo":{900:"fands"},etch:{900:"faes"},graphite:{100:"fagt"},chisel:{400:"facr"},jelly:{400:"fajr"},"jelly-fill":{400:"fajfr"},"jelly-duo":{400:"fajdr"},utility:{600:"fausb"},"utility-duo":{600:"faudsb"},"utility-fill":{600:"faufsb"}}));var Me=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],Nt={GROUP:"duotone-group",PRIMARY:"primary",SECONDARY:"secondary"},Ie=[].concat(D(["kit"]),D(ke)),it=U.FontAwesomeConfig||{};S&&typeof S.querySelector=="function"&&[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-search-pseudo-elements","searchPseudoElements"],["data-search-pseudo-elements-warnings","searchPseudoElementsWarnings"],["data-search-pseudo-elements-full-scan","searchPseudoElementsFullScan"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]].forEach(function(t){var a=yt(t,2),n=a[0],e=a[1],i=(function(r){return r===""||r!=="false"&&(r==="true"||r)})((function(r){var o=S.querySelector("script["+r+"]");if(o)return o.getAttribute(r)})(n));i!=null&&(it[e]=i)});var Yn={styleDefault:"solid",familyDefault:F,cssPrefix:"fa",replacementClass:Wn,autoReplaceSvg:!0,autoAddCss:!0,searchPseudoElements:!1,searchPseudoElementsWarnings:!0,searchPseudoElementsFullScan:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};it.familyPrefix&&(it.cssPrefix=it.familyPrefix);var $=f(f({},Yn),it);$.autoReplaceSvg||($.observeMutations=!1);var b={};Object.keys(Yn).forEach(function(t){Object.defineProperty(b,t,{enumerable:!0,set:function(a){$[t]=a,Ht.forEach(function(n){return n(b)})},get:function(){return $[t]}})}),Object.defineProperty(b,"familyPrefix",{enumerable:!0,set:function(t){$.cssPrefix=t,Ht.forEach(function(a){return a(b)})},get:function(){return $.cssPrefix}}),U.FontAwesomeConfig=b;var Ht=[],G=16,T={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function Sa(){for(var t=12,a="";t-- >0;)a+="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"[62*Math.random()|0];return a}function tt(t){for(var a=[],n=(t||[]).length>>>0;n--;)a[n]=t[n];return a}function sa(t){return t.classList?tt(t.classList):(t.getAttribute("class")||"").split(" ").filter(function(a){return a})}function ka(t){return"".concat(t).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function xt(t){return Object.keys(t||{}).reduce(function(a,n){return a+"".concat(n,": ").concat(t[n].trim(),";")},"")}function fa(t){return t.size!==T.size||t.x!==T.x||t.y!==T.y||t.rotate!==T.rotate||t.flipX||t.flipY}function qn(){var t="fa",a=Wn,n=b.cssPrefix,e=b.replacementClass,i=`:root, :host {
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
  --fa-font-slab-duo-regular: normal 400 1em/1 'Font Awesome 7 Slab Duo';
  --fa-font-slab-press-duo-regular: normal 400 1em/1 'Font Awesome 7 Slab Press Duo';
  --fa-font-pixel-regular: normal 400 1em/1 'Font Awesome 7 Pixel';
  --fa-font-mosaic-solid: normal 900 1em/1 'Font Awesome 7 Mosaic';
  --fa-font-vellum-solid: normal 900 1em/1 'Font Awesome 7 Vellum';
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

.fa-canvas-square {
  padding-block: 0.125em;
  margin-block-end: -0.125em;
}

.fa-canvas-roomy {
  padding-block: 0.25em;
  padding-inline: 0.125em;
  margin-block-end: -0.25em;
  box-sizing: content-box;
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
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-beat-fade {
  animation-name: fa-beat-fade;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-flip {
  animation-name: fa-flip;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1.5s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
}

.fa-flip-360 {
  animation-name: fa-flip-360;
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
  animation-duration: var(--fa-animation-duration, 0.75s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
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

.fa-spin-snap {
  animation-name: fa-spin-snap;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 3s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin-snap-4 {
  animation-name: fa-spin-snap-4;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 2.4s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-spin-snap-8 {
  animation-name: fa-spin-snap-8;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 4s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-buzz {
  animation-name: fa-buzz;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 0.6s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, linear);
}

.fa-wag {
  animation-name: fa-wag;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 0.9s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-out);
  transform-origin: bottom center;
}

.fa-float {
  animation-name: fa-float;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 3s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-in-out);
  will-change: transform;
}

.fa-swing {
  animation-name: fa-swing;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 1.2s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-out);
  transform-origin: top center;
}

.fa-jello {
  animation-name: fa-jello;
  animation-delay: var(--fa-animation-delay, 0s);
  animation-direction: var(--fa-animation-direction, normal);
  animation-duration: var(--fa-animation-duration, 0.9s);
  animation-iteration-count: var(--fa-animation-iteration-count, infinite);
  animation-timing-function: var(--fa-animation-timing, ease-out);
}

@media (prefers-reduced-motion: reduce) {
  .fa-beat,
  .fa-bounce,
  .fa-fade,
  .fa-beat-fade,
  .fa-flip,
  .fa-flip-360,
  .fa-pulse,
  .fa-shake,
  .fa-spin,
  .fa-spin-pulse,
  .fa-buzz,
  .fa-float,
  .fa-jello,
  .fa-spin-snap,
  .fa-spin-snap-4,
  .fa-spin-snap-8,
  .fa-swing,
  .fa-wag {
    animation: none !important;
    transition: none !important;
  }
}
@keyframes fa-beat {
  0% {
    transform: scale(1);
  }
  25% {
    transform: scale(calc(1.25 * var(--fa-beat-scale, 1.25)));
  }
  45% {
    transform: scale(calc(1.22 * var(--fa-beat-scale, 1.22)));
  }
  65% {
    transform: scale(calc(1.25 * var(--fa-beat-scale, 1.25)));
  }
  90% {
    transform: scale(1);
  }
}
@keyframes fa-bounce {
  0% {
    transform: scale(1, 1) translateY(0);
    animation-timing-function: var(--fa-animation-timing);
  }
  14% {
    transform: scale(var(--fa-bounce-start-scale-x, 1.06), var(--fa-bounce-start-scale-y, 0.94)) translateY(var(--fa-bounce-anticipation, 3px));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
  }
  32% {
    transform: scale(var(--fa-bounce-jump-scale-x, 0.94), var(--fa-bounce-jump-scale-y, 1.12)) translateY(calc(-1 * var(--fa-bounce-height, 0.5em)));
    animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
  }
  52% {
    transform: scale(1, 1) translateY(calc(-1 * var(--fa-bounce-height, 0.5em) * 1.1));
    animation-timing-function: cubic-bezier(0.5, 0, 1, 0.5);
  }
  70% {
    transform: scale(var(--fa-bounce-land-scale-x, 1.06), var(--fa-bounce-land-scale-y, 0.92)) translateY(0);
    animation-timing-function: cubic-bezier(0.33, 0.33, 0.66, 1);
  }
  85% {
    transform: scale(0.98, 1.04) translateY(calc(-2px * var(--fa-bounce-rebound, 1)));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 1);
  }
  100% {
    transform: scale(1, 1) translateY(0);
  }
}
@keyframes fa-fade {
  0% {
    opacity: 1;
    transform: scale(1);
    animation-timing-function: cubic-bezier(0.2, 0, 0.4, 1);
  }
  40% {
    opacity: var(--fa-fade-opacity, 0.4);
    transform: scale(0.98);
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes fa-beat-fade {
  0% {
    opacity: var(--fa-beat-fade-opacity, 0.4);
    transform: scale(1);
    animation-timing-function: cubic-bezier(0.2, 0, 0.4, 1);
  }
  25% {
    opacity: calc(var(--fa-beat-fade-opacity, 0.4) + 0.4);
    transform: scale(var(--fa-beat-fade-scale, 1.28));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  45% {
    opacity: 1;
    transform: scale(var(--fa-beat-fade-scale, 1.25));
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  65% {
    opacity: calc(var(--fa-beat-fade-opacity, 0.4) + 0.4);
    transform: scale(var(--fa-beat-fade-scale, 1.28));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  100% {
    opacity: var(--fa-beat-fade-opacity, 0.4);
    transform: scale(1);
  }
}
@keyframes fa-flip {
  0% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), 0deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.4, 1);
  }
  8% {
    transform: perspective(2em) scale(var(--fa-flip-anticipation-scale, 0.95)) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), 0deg);
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
  }
  35% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), calc(var(--fa-flip-angle, -360deg) * 0.6));
    animation-timing-function: linear;
  }
  65% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), calc(var(--fa-flip-angle, -360deg) * 0.5));
    animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
  }
  92% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), calc(var(--fa-flip-angle, -360deg) * var(--fa-flip-overshoot, 1.04)));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 1);
  }
  100% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -360deg));
  }
}
@keyframes fa-flip-360 {
  0% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), 0deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.4, 1);
  }
  8% {
    transform: perspective(2em) scale(var(--fa-flip-anticipation-scale, 0.95)) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), 0deg);
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
  }
  50% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), calc(var(--fa-flip-angle, -360deg) * 0.6));
    animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
  }
  80% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), calc(var(--fa-flip-angle, -360deg) * var(--fa-flip-overshoot, 1.04)));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 1);
  }
  100% {
    transform: perspective(2em) scale(1) rotate3d(var(--fa-flip-x, 0), var(--fa-flip-y, 1), var(--fa-flip-z, 0), var(--fa-flip-angle, -360deg));
  }
}
@keyframes fa-shake {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.8, 1);
  }
  8% {
    transform: rotate(35deg) translateX(1px);
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  20% {
    transform: rotate(-22deg) translateX(-1px);
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  35% {
    transform: rotate(15deg) translateX(1px);
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  50% {
    transform: rotate(-9deg);
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  65% {
    transform: rotate(5deg);
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  78% {
    transform: rotate(-3deg);
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  90% {
    transform: rotate(1deg);
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  100% {
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
@keyframes fa-spin-snap {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  12% {
    transform: rotate(60deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  16.67% {
    transform: rotate(60deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  28.67% {
    transform: rotate(120deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  33.33% {
    transform: rotate(120deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  45.33% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  62% {
    transform: rotate(240deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  66.67% {
    transform: rotate(240deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  78.67% {
    transform: rotate(300deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  83.33% {
    transform: rotate(300deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  95.33% {
    transform: rotate(360deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  100% {
    transform: rotate(360deg);
  }
}
@keyframes fa-spin-snap-4 {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  15% {
    transform: rotate(90deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  25% {
    transform: rotate(90deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  40% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  65% {
    transform: rotate(270deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  75% {
    transform: rotate(270deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  90% {
    transform: rotate(360deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  100% {
    transform: rotate(360deg);
  }
}
@keyframes fa-spin-snap-8 {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  9% {
    transform: rotate(45deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  12.5% {
    transform: rotate(45deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  21.5% {
    transform: rotate(90deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  25% {
    transform: rotate(90deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  34% {
    transform: rotate(135deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  37.5% {
    transform: rotate(135deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  46.5% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: rotate(180deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  59% {
    transform: rotate(225deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  62.5% {
    transform: rotate(225deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  71.5% {
    transform: rotate(270deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  75% {
    transform: rotate(270deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  84% {
    transform: rotate(315deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  87.5% {
    transform: rotate(315deg);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  96.5% {
    transform: rotate(360deg);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  100% {
    transform: rotate(360deg);
  }
}
@keyframes fa-buzz {
  0% {
    transform: translateX(0) rotate(0deg);
    animation-timing-function: cubic-bezier(0.1, 0, 0.9, 1);
  }
  5% {
    transform: translateX(var(--fa-buzz-distance, 4px)) rotate(0.5deg);
  }
  10% {
    transform: translateX(calc(-1 * var(--fa-buzz-distance, 4px))) rotate(-0.5deg);
  }
  15% {
    transform: translateX(var(--fa-buzz-distance, 4px)) rotate(0.3deg);
  }
  20% {
    transform: translateX(calc(-1 * var(--fa-buzz-distance, 4px))) rotate(-0.3deg);
  }
  25% {
    transform: translateX(calc(var(--fa-buzz-distance, 4px) * 0.7)) rotate(0.2deg);
  }
  30% {
    transform: translateX(calc(-1 * var(--fa-buzz-distance, 4px) * 0.7)) rotate(-0.2deg);
  }
  35% {
    transform: translateX(calc(var(--fa-buzz-distance, 4px) * 0.4)) rotate(0.1deg);
  }
  40% {
    transform: translateX(0) rotate(0deg);
  }
  100% {
    transform: translateX(0) rotate(0deg);
  }
}
@keyframes fa-wag {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.6, 1);
  }
  12% {
    transform: rotate(var(--fa-wag-angle, 12deg));
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  24% {
    transform: rotate(2deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.6, 1);
  }
  36% {
    transform: rotate(calc(var(--fa-wag-angle, 12deg) * 0.85));
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  48% {
    transform: rotate(1deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.6, 1);
  }
  58% {
    transform: rotate(calc(var(--fa-wag-angle, 12deg) * 0.6));
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  68% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(0deg);
  }
}
@keyframes fa-float {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--fa-float-squash-x, 1.02), var(--fa-float-squash-y, 0.98));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
  }
  15% {
    transform: translateY(calc(-0.4 * var(--fa-float-height, 6px))) translateX(var(--fa-float-drift, 1px)) rotate(var(--fa-float-tilt, 1deg)) scale(1, 1);
    animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
  }
  35% {
    transform: translateY(calc(-1 * var(--fa-float-height, 6px))) translateX(0) rotate(0deg) scale(var(--fa-float-stretch-x, 0.98), var(--fa-float-stretch-y, 1.03));
    animation-timing-function: cubic-bezier(0.5, 0, 0.5, 0);
  }
  50% {
    transform: translateY(calc(-0.92 * var(--fa-float-height, 6px))) translateX(calc(-0.5 * var(--fa-float-drift, 1px))) rotate(calc(-0.5 * var(--fa-float-tilt, 1deg))) scale(0.995, 1.01);
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
  }
  70% {
    transform: translateY(calc(-0.3 * var(--fa-float-height, 6px))) translateX(calc(-1 * var(--fa-float-drift, 1px))) rotate(calc(-1 * var(--fa-float-tilt, 1deg))) scale(1, 1);
    animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
  }
  90% {
    transform: translateY(calc(0.05 * var(--fa-float-height, 6px))) translateX(0) rotate(0deg) scale(var(--fa-float-squash-x, 1.02), var(--fa-float-squash-y, 0.98));
    animation-timing-function: cubic-bezier(0.33, 0, 0.66, 1);
  }
  100% {
    transform: translateY(0) translateX(0) rotate(0deg) scale(var(--fa-float-squash-x, 1.02), var(--fa-float-squash-y, 0.98));
  }
}
@keyframes fa-swing {
  0% {
    transform: rotate(0deg);
    animation-timing-function: cubic-bezier(0.2, 0, 0.8, 1);
  }
  8% {
    transform: rotate(var(--fa-swing-angle, 22deg));
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  18% {
    transform: rotate(calc(-1 * var(--fa-swing-angle, 22deg) * 0.85));
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  28% {
    transform: rotate(calc(var(--fa-swing-angle, 22deg) * 0.65));
    animation-timing-function: cubic-bezier(0.35, 0, 0.65, 1);
  }
  38% {
    transform: rotate(calc(-1 * var(--fa-swing-angle, 22deg) * 0.45));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  48% {
    transform: rotate(calc(var(--fa-swing-angle, 22deg) * 0.25));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  56% {
    transform: rotate(calc(-1 * var(--fa-swing-angle, 22deg) * 0.1));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  64% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(0deg);
  }
}
@keyframes fa-jello {
  0% {
    transform: scale(1, 1);
    animation-timing-function: cubic-bezier(0.2, 0, 0.8, 1);
  }
  12% {
    transform: scale(var(--fa-jello-scale-x, 1.15), calc(2 - var(--fa-jello-scale-x, 1.15)));
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  24% {
    transform: scale(calc(2 - var(--fa-jello-scale-y, 1.12)), var(--fa-jello-scale-y, 1.12));
    animation-timing-function: cubic-bezier(0.3, 0, 0.7, 1);
  }
  36% {
    transform: scale(calc(1 + (var(--fa-jello-scale-x, 1.15) - 1) * 0.5), calc(2 - (1 + (var(--fa-jello-scale-x, 1.15) - 1) * 0.5)));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  48% {
    transform: scale(calc(2 - (1 + (var(--fa-jello-scale-y, 1.12) - 1) * 0.3)), calc(1 + (var(--fa-jello-scale-y, 1.12) - 1) * 0.3));
    animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
  }
  58% {
    transform: scale(1.02, 0.98);
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
  68% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
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
}`;if(n!==t||e!==a){var r=new RegExp("\\.".concat(t,"\\-"),"g"),o=new RegExp("\\--".concat(t,"\\-"),"g"),s=new RegExp("\\.".concat(a),"g");i=i.replace(r,".".concat(n,"-")).replace(o,"--".concat(n,"-")).replace(s,".".concat(e))}return i}var ja=!1;function Mt(){b.autoAddCss&&!ja&&((function(t){if(t&&R){var a=S.createElement("style");a.setAttribute("type","text/css"),a.innerHTML=t;for(var n=S.head.childNodes,e=null,i=n.length-1;i>-1;i--){var r=n[i],o=(r.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(e=r)}S.head.insertBefore(a,e)}})(qn()),ja=!0)}var Fe={mixout:function(){return{dom:{css:qn,insertCss:Mt}}},hooks:function(){return{beforeDOMElementCreation:function(){Mt()},beforeI2svg:function(){Mt()}}}},B=U||{};B[W]||(B[W]={}),B[W].styles||(B[W].styles={}),B[W].hooks||(B[W].hooks={}),B[W].shims||(B[W].shims=[]);var E=B[W],Jn=[],Hn=function(){S.removeEventListener("DOMContentLoaded",Hn),ca=1,Jn.map(function(t){return t()})},ca=!1;function st(t){var a=t.tag,n=t.attributes,e=n===void 0?{}:n,i=t.children,r=i===void 0?[]:i;return typeof t=="string"?ka(t):"<".concat(a," ").concat((function(o){return Object.keys(o||{}).reduce(function(s,c){return s+"".concat(c,'="').concat(ka(o[c]),'" ')},"").trim()})(e),">").concat(r.map(st).join(""),"</").concat(a,">")}function Aa(t,a,n){if(t&&t[a]&&t[a][n])return{prefix:a,iconName:n,icon:t[a][n]}}R&&((ca=(S.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(S.readyState))||S.addEventListener("DOMContentLoaded",Hn));var It=function(t,a,n,e){var i,r,o,s=Object.keys(t),c=s.length,l=a;for(n===void 0?(i=1,o=t[s[0]]):(i=0,o=n);i<c;i++)o=l(o,t[r=s[i]],r,t);return o};function Kn(t){return D(t).length!==1?null:t.codePointAt(0).toString(16)}function Pa(t){return Object.keys(t).reduce(function(a,n){var e=t[n];return e.icon?a[e.iconName]=e.icon:a[n]=e,a},{})}function Kt(t,a){var n=(arguments.length>2&&arguments[2]!==void 0?arguments[2]:{}).skipHooks,e=n!==void 0&&n,i=Pa(a);typeof E.hooks.addPack!="function"||e?E.styles[t]=f(f({},E.styles[t]||{}),i):E.hooks.addPack(t,Pa(a)),t==="fas"&&Kt("fa",a)}var rt=E.styles,Oe=E.shims,Vn=Object.keys(la),Le=Vn.reduce(function(t,a){return t[a]=Object.keys(la[a]),t},{}),ua=null,Gn={},_n={},$n={},Zn={},Qn={};function Ce(t,a){var n,e=a.split("-"),i=e[0],r=e.slice(1).join("-");return i!==t||r===""||(n=r,~Ie.indexOf(n))?null:r}var Na,te=function(){var t=function(e){return It(rt,function(i,r,o){return i[o]=It(r,e,{}),i},{})};Gn=t(function(e,i,r){return i[3]&&(e[i[3]]=r),i[2]&&i[2].filter(function(o){return typeof o=="number"}).forEach(function(o){e[o.toString(16)]=r}),e}),_n=t(function(e,i,r){return e[r]=r,i[2]&&i[2].filter(function(o){return typeof o=="string"}).forEach(function(o){e[o]=r}),e}),Qn=t(function(e,i,r){var o=i[2];return e[r]=r,o.forEach(function(s){e[s]=r}),e});var a="far"in rt||b.autoFetchSvg,n=It(Oe,function(e,i){var r=i[0],o=i[1],s=i[2];return o!=="far"||a||(o="fas"),typeof r=="string"&&(e.names[r]={prefix:o,iconName:s}),typeof r=="number"&&(e.unicodes[r.toString(16)]={prefix:o,iconName:s}),e},{names:{},unicodes:{}});$n=n.names,Zn=n.unicodes,ua=zt(b.styleDefault,{family:b.familyDefault})};function Vt(t,a){return(Gn[t]||{})[a]}function J(t,a){return(Qn[t]||{})[a]}function ae(t){return $n[t]||{prefix:null,iconName:null}}function Y(){return ua}Na=function(t){ua=zt(t.styleDefault,{family:b.familyDefault})},Ht.push(Na),te();function zt(t){var a=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).family,n=a===void 0?F:a,e=Ae[n][t];if(n===ot&&!t)return"fad";var i=wa[n][t]||wa[n][e],r=t in E.styles?t:null;return i||r||null}function Ma(t){return t.sort().filter(function(a,n,e){return e.indexOf(a)===n})}var Ia=Dn.concat(En);function wt(t){var a,n,e=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).skipLookups,i=e!==void 0&&e,r=null,o=Ma(t.filter(function(m){return Ia.includes(m)})),s=Ma(t.filter(function(m){return!Ia.includes(m)})),c=yt(o.filter(function(m){return r=m,!un.includes(m)}),1)[0],l=c===void 0?null:c,u=(function(m){var g=F,x=Vn.reduce(function(p,v){return p[v]="".concat(b.cssPrefix,"-").concat(v),p},{});return Cn.forEach(function(p){(m.includes(x[p])||m.some(function(v){return Le[p].includes(v)}))&&(g=p)}),g})(o),d=f(f({},(a=[],n=null,s.forEach(function(m){var g=Ce(b.cssPrefix,m);g?n=g:m&&a.push(m)}),{iconName:n,rest:a})),{},{prefix:zt(l,{family:u})});return f(f(f({},d),(function(m){var g=m.values,x=m.family,p=m.canonical,v=m.givenPrefix,j=v===void 0?"":v,z=m.styles,L=z===void 0?{}:z,C=m.config,y=C===void 0?{}:C,P=x===ot,A=g.includes("fa-duotone")||g.includes("fad"),N=y.familyDefault==="duotone",O=p.prefix==="fad"||p.prefix==="fa-duotone";if(!P&&(A||N||O)&&(p.prefix="fad"),(g.includes("fa-brands")||g.includes("fab"))&&(p.prefix="fab"),!p.prefix&&Ee.includes(x)&&(Object.keys(L).find(function(I){return De.includes(I)})||y.autoFetchSvg)){var M=ge.get(x).defaultShortPrefixId;p.prefix=M,p.iconName=J(p.prefix,p.iconName)||p.iconName}return p.prefix!=="fa"&&j!=="fa"||(p.prefix=Y()||"fas"),p})({values:t,family:u,styles:rt,config:b,canonical:d,givenPrefix:r})),(function(m,g,x){var p=x.prefix,v=x.iconName;if(m||!p||!v)return{prefix:p,iconName:v};var j=g==="fa"?ae(v):{},z=J(p,v);return v=j.iconName||z||v,(p=j.prefix||p)!=="far"||rt.far||!rt.fas||b.autoFetchSvg||(p="fas"),{prefix:p,iconName:v}})(i,r,d))}var Ee=Cn.filter(function(t){return t!==F||t!==ot}),De=Object.keys(Rt).filter(function(t){return t!==F}).map(function(t){return Object.keys(Rt[t])}).flat(),Te=(function(){return de(function t(){(function(a,n){if(!(a instanceof n))throw new TypeError("Cannot call a class as a function")})(this,t),this.definitions={}},[{key:"add",value:function(){for(var t=this,a=arguments.length,n=new Array(a),e=0;e<a;e++)n[e]=arguments[e];var i=n.reduce(this._pullDefinitions,{});Object.keys(i).forEach(function(r){t.definitions[r]=f(f({},t.definitions[r]||{}),i[r]),Kt(r,i[r]);var o=la[F][r];o&&Kt(o,i[r]),te()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(t,a){var n=a.prefix&&a.iconName&&a.icon?{0:a}:a;return Object.keys(n).map(function(e){var i=n[e],r=i.prefix,o=i.iconName,s=i.icon,c=s[2];t[r]||(t[r]={}),c.length>0&&c.forEach(function(l){typeof l=="string"&&(t[r][l]=s)}),t[r][o]=s}),t}}])})(),Fa=[],Z={},Q={},We=Object.keys(Q);function Gt(t,a){for(var n=arguments.length,e=new Array(n>2?n-2:0),i=2;i<n;i++)e[i-2]=arguments[i];return(Z[t]||[]).forEach(function(r){a=r.apply(null,[a].concat(e))}),a}function K(t){for(var a=arguments.length,n=new Array(a>1?a-1:0),e=1;e<a;e++)n[e-1]=arguments[e];(Z[t]||[]).forEach(function(i){i.apply(null,n)})}function q(){var t=arguments[0],a=Array.prototype.slice.call(arguments,1);return Q[t]?Q[t].apply(null,a):void 0}function _t(t){t.prefix==="fa"&&(t.prefix="fas");var a=t.iconName,n=t.prefix||Y();if(a)return a=J(n,a)||a,Aa(ne.definitions,n,a)||Aa(E.styles,n,a)}var ne=new Te,Be={i2svg:function(){var t=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return R?(K("beforeI2svg",t),q("pseudoElements2svg",t),q("i2svg",t)):Promise.reject(new Error("Operation requires a DOM of some kind."))},watch:function(){var t,a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=a.autoReplaceSvgRoot;b.autoReplaceSvg===!1&&(b.autoReplaceSvg=!0),b.observeMutations=!0,t=function(){Re({autoReplaceSvgRoot:n}),K("watch",a)},R&&(ca?setTimeout(t,0):Jn.push(t))}},ft={noAuto:function(){b.autoReplaceSvg=!1,b.observeMutations=!1,K("noAuto")},config:b,dom:Be,parse:{icon:function(t){if(t===null)return null;if(ia(t)==="object"&&t.prefix&&t.iconName)return{prefix:t.prefix,iconName:J(t.prefix,t.iconName)||t.iconName};if(Array.isArray(t)&&t.length===2){var a=t[1].indexOf("fa-")===0?t[1].slice(3):t[1],n=zt(t[0]);return{prefix:n,iconName:J(n,a)||a}}if(typeof t=="string"&&(t.indexOf("".concat(b.cssPrefix,"-"))>-1||t.match(Pe))){var e=wt(t.split(" "),{skipLookups:!0});return{prefix:e.prefix||Y(),iconName:J(e.prefix,e.iconName)||e.iconName}}if(typeof t=="string"){var i=Y();return{prefix:i,iconName:J(i,t)||t}}}},library:ne,findIconDefinition:_t,toHtml:st},Re=function(){var t=(arguments.length>0&&arguments[0]!==void 0?arguments[0]:{}).autoReplaceSvgRoot,a=t===void 0?S:t;(Object.keys(E.styles).length>0||b.autoFetchSvg)&&R&&b.autoReplaceSvg&&ft.dom.i2svg({node:a})};function St(t,a){return Object.defineProperty(t,"abstract",{get:a}),Object.defineProperty(t,"html",{get:function(){return t.abstract.map(function(n){return st(n)})}}),Object.defineProperty(t,"node",{get:function(){if(R){var n=S.createElement("div");return n.innerHTML=t.html,n.children}}}),t}function ma(t){var a=t.icons,n=a.main,e=a.mask,i=t.prefix,r=t.iconName,o=t.transform,s=t.symbol,c=t.maskId,l=t.extra,u=t.watchable,d=u!==void 0&&u,m=e.found?e:n,g=m.width,x=m.height,p=[b.replacementClass,r?"".concat(b.cssPrefix,"-").concat(r):""].filter(function(y){return l.classes.indexOf(y)===-1}).filter(function(y){return y!==""||!!y}).concat(l.classes).join(" "),v={children:[],attributes:f(f({},l.attributes),{},{"data-prefix":i,"data-icon":r,class:p,role:l.attributes.role||"img",viewBox:"0 0 ".concat(g," ").concat(x)})};(function(y){return["aria-label","aria-labelledby","title","role"].some(function(P){return P in y})})(l.attributes)||l.attributes["aria-hidden"]||(v.attributes["aria-hidden"]="true"),d&&(v.attributes[H]="");var j=f(f({},v),{},{prefix:i,iconName:r,main:n,mask:e,maskId:c,transform:o,symbol:s,styles:f({},l.styles)}),z=e.found&&n.found?q("generateAbstractMask",j)||{children:[],attributes:{}}:q("generateAbstractIcon",j)||{children:[],attributes:{}},L=z.children,C=z.attributes;return j.children=L,j.attributes=C,s?(function(y){var P=y.prefix,A=y.iconName,N=y.children,O=y.attributes,M=y.symbol,I=M===!0?"".concat(P,"-").concat(b.cssPrefix,"-").concat(A):M;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:f(f({},O),{},{id:I}),children:N}]}]})(j):(function(y){var P=y.children,A=y.main,N=y.mask,O=y.attributes,M=y.styles,I=y.transform;if(fa(I)&&A.found&&!N.found){var X={x:A.width/A.height/2,y:.5};O.style=xt(f(f({},M),{},{"transform-origin":"".concat(X.x+I.x/16,"em ").concat(X.y+I.y/16,"em")}))}return[{tag:"svg",attributes:O,children:P}]})(j)}function Oa(t){var a=t.content,n=t.width,e=t.height,i=t.transform,r=t.extra,o=t.watchable,s=o!==void 0&&o,c=f(f({},r.attributes),{},{class:r.classes.join(" ")});s&&(c[H]="");var l=f({},r.styles);fa(i)&&(l.transform=(function(m){var g=m.transform,x=m.width,p=x===void 0?16:x,v=m.height,j=v===void 0?16:v,z="";return z+=fn?"translate(".concat(g.x/G-p/2,"em, ").concat(g.y/G-j/2,"em) "):"translate(calc(-50% + ".concat(g.x/G,"em), calc(-50% + ").concat(g.y/G,"em)) "),z+="scale(".concat(g.size/G*(g.flipX?-1:1),", ").concat(g.size/G*(g.flipY?-1:1),") "),z+"rotate(".concat(g.rotate,"deg) ")})({transform:i,width:n,height:e}),l["-webkit-transform"]=l.transform);var u=xt(l);u.length>0&&(c.style=u);var d=[];return d.push({tag:"span",attributes:c,children:[a]}),d}var Ft=E.styles;function $t(t){var a=t[0],n=t[1],e=yt(t.slice(4),1)[0];return{found:!0,width:a,height:n,icon:Array.isArray(e)?{tag:"g",attributes:{class:"".concat(b.cssPrefix,"-").concat(Nt.GROUP)},children:[{tag:"path",attributes:{class:"".concat(b.cssPrefix,"-").concat(Nt.SECONDARY),fill:"currentColor",d:e[0]}},{tag:"path",attributes:{class:"".concat(b.cssPrefix,"-").concat(Nt.PRIMARY),fill:"currentColor",d:e[1]}}]}:{tag:"path",attributes:{fill:"currentColor",d:e}}}}var Xe={found:!1,width:512,height:512};function Zt(t,a){var n=a;return a==="fa"&&b.styleDefault!==null&&(a=Y()),new Promise(function(e,i){if(n==="fa"){var r=ae(t)||{};t=r.iconName||t,a=r.prefix||a}if(t&&a&&Ft[a]&&Ft[a][t])return e($t(Ft[a][t]));!Rn&&b.showMissingIcons,e(f(f({},Xe),{},{icon:b.showMissingIcons&&t&&q("missingIconAbstract")||{}}))})}var La=function(){},Qt=b.measurePerformance&&ct&&ct.mark&&ct.measure?ct:{mark:La,measure:La},et='FA "7.3.1"',Ue=function(t){Qt.mark("".concat(et," ").concat(t," ends")),Qt.measure("".concat(et," ").concat(t),"".concat(et," ").concat(t," begins"),"".concat(et," ").concat(t," ends"))},da=function(t){return Qt.mark("".concat(et," ").concat(t," begins")),function(){return Ue(t)}},bt=function(){};function Ca(t){return typeof(t.getAttribute?t.getAttribute(H):null)=="string"}function Ye(t){return S.createElementNS("http://www.w3.org/2000/svg",t)}function qe(t){return S.createElement(t)}function ee(t){var a=(arguments.length>1&&arguments[1]!==void 0?arguments[1]:{}).ceFn,n=a===void 0?t.tag==="svg"?Ye:qe:a;if(typeof t=="string")return S.createTextNode(t);var e=n(t.tag);return Object.keys(t.attributes||[]).forEach(function(i){e.setAttribute(i,t.attributes[i])}),(t.children||[]).forEach(function(i){e.appendChild(ee(i,{ceFn:n}))}),e}var ht={replace:function(t){var a=t[0];if(a.parentNode)if(t[1].forEach(function(e){a.parentNode.insertBefore(ee(e),a)}),a.getAttribute(H)===null&&b.keepOriginalSource){var n=S.createComment((function(e){var i=" ".concat(e.outerHTML," ");return"".concat(i,"Font Awesome fontawesome.com ")})(a));a.parentNode.replaceChild(n,a)}else a.remove()},nest:function(t){var a=t[0],n=t[1];if(~sa(a).indexOf(b.replacementClass))return ht.replace(t);var e=new RegExp("".concat(b.cssPrefix,"-.*"));if(delete n[0].attributes.id,n[0].attributes.class){var i=n[0].attributes.class.split(" ").reduce(function(o,s){return s===b.replacementClass||s.match(e)?o.toSvg.push(s):o.toNode.push(s),o},{toNode:[],toSvg:[]});n[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?a.removeAttribute("class"):a.setAttribute("class",i.toNode.join(" "))}var r=n.map(function(o){return st(o)}).join(`
`);a.setAttribute(H,""),a.innerHTML=r}};function Ea(t){t()}function ie(t,a){var n=typeof a=="function"?a:bt;if(t.length===0)n();else{var e=Ea;b.mutateApproach==="async"&&(e=U.requestAnimationFrame||Ea),e(function(){var i=b.autoReplaceSvg===!0?ht.replace:ht[b.autoReplaceSvg]||ht.replace,r=da("mutate");t.map(i),r(),n()})}}var ga=!1;function re(){ga=!0}function ta(){ga=!1}var vt=null;function Da(t){if(xa&&b.observeMutations){var a=t.treeCallback,n=a===void 0?bt:a,e=t.nodeCallback,i=e===void 0?bt:e,r=t.pseudoElementsCallback,o=r===void 0?bt:r,s=t.observeMutationsRoot,c=s===void 0?S:s;vt=new xa(function(l){if(!ga){var u=Y();tt(l).forEach(function(d){if(d.type==="childList"&&d.addedNodes.length>0&&!Ca(d.addedNodes[0])&&(b.searchPseudoElements&&o(d.target),n(d.target)),d.type==="attributes"&&d.target.parentNode&&b.searchPseudoElements&&o([d.target],!0),d.type==="attributes"&&Ca(d.target)&&~Me.indexOf(d.attributeName))if(d.attributeName==="class"&&(function(v){var j=v.getAttribute?v.getAttribute(Ut):null,z=v.getAttribute?v.getAttribute(Yt):null;return j&&z})(d.target)){var m=wt(sa(d.target)),g=m.prefix,x=m.iconName;d.target.setAttribute(Ut,g||u),x&&d.target.setAttribute(Yt,x)}else(p=d.target)&&p.classList&&p.classList.contains&&p.classList.contains(b.replacementClass)&&i(d.target);var p})}}),R&&vt.observe(c,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function Je(t){var a,n,e=t.getAttribute("data-prefix"),i=t.getAttribute("data-icon"),r=t.innerText!==void 0?t.innerText.trim():"",o=wt(sa(t));return o.prefix||(o.prefix=Y()),e&&i&&(o.prefix=e,o.iconName=i),o.iconName&&o.prefix||(o.prefix&&r.length>0&&(o.iconName=(a=o.prefix,n=t.innerText,(_n[a]||{})[n]||Vt(o.prefix,Kn(t.innerText)))),!o.iconName&&b.autoFetchSvg&&t.firstChild&&t.firstChild.nodeType===Node.TEXT_NODE&&(o.iconName=t.firstChild.data)),o}function Ta(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},n=Je(t),e=n.iconName,i=n.prefix,r=n.rest,o=(function(l){return tt(l.attributes).reduce(function(u,d){return u.name!=="class"&&u.name!=="style"&&(u[d.name]=d.value),u},{})})(t),s=Gt("parseNodeAttributes",{},t),c=a.styleParser?(function(l){var u=l.getAttribute("style"),d=[];return u&&(d=u.split(";").reduce(function(m,g){var x=g.split(":"),p=x[0],v=x.slice(1);return p&&v.length>0&&(m[p]=v.join(":").trim()),m},{})),d})(t):[];return f({iconName:e,prefix:i,transform:T,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:r,styles:c,attributes:o}},s)}var He=E.styles;function oe(t){var a=b.autoReplaceSvg==="nest"?Ta(t,{styleParser:!1}):Ta(t);return~a.extra.classes.indexOf(Un)?q("generateLayersText",t,a):q("generateSvgReplacementMutation",t,a)}function Wa(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!R)return Promise.resolve();var n=S.documentElement.classList,e=function(u){return n.add("".concat(za,"-").concat(u))},i=function(u){return n.remove("".concat(za,"-").concat(u))},r=b.autoFetchSvg?[].concat(D(En),D(Dn)):un.concat(Object.keys(He));r.includes("fa")||r.push("fa");var o=[".".concat(Un,":not([").concat(H,"])")].concat(r.map(function(u){return".".concat(u,":not([").concat(H,"])")})).join(", ");if(o.length===0)return Promise.resolve();var s=[];try{s=tt(t.querySelectorAll(o))}catch{}if(!(s.length>0))return Promise.resolve();e("pending"),i("complete");var c=da("onTree"),l=s.reduce(function(u,d){try{var m=oe(d);m&&u.push(m)}catch(g){Rn||g.name}return u},[]);return new Promise(function(u,d){Promise.all(l).then(function(m){ie(m,function(){e("active"),e("complete"),i("pending"),typeof a=="function"&&a(),c(),u()})}).catch(function(m){c(),d(m)})})}function Ke(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;oe(t).then(function(n){n&&ie([n],a)})}var Ve=function(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=a.transform,e=n===void 0?T:n,i=a.symbol,r=i!==void 0&&i,o=a.mask,s=o===void 0?null:o,c=a.maskId,l=c===void 0?null:c,u=a.classes,d=u===void 0?[]:u,m=a.attributes,g=m===void 0?{}:m,x=a.styles,p=x===void 0?{}:x;if(t){var v=t.prefix,j=t.iconName,z=t.icon;return St(f({type:"icon"},t),function(){return K("beforeDOMElementCreation",{iconDefinition:t,params:a}),ma({icons:{main:$t(z),mask:s?$t(s.icon):{found:!1,width:null,height:null,icon:{}}},prefix:v,iconName:j,transform:f(f({},T),e),symbol:r,maskId:l,extra:{attributes:g,styles:p,classes:d}})})}},Ge={mixout:function(){return{icon:(t=Ve,function(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},e=(a||{}).icon?a:_t(a||{}),i=n.mask;return i&&(i=(i||{}).icon?i:_t(i||{})),t(e,f(f({},n),{},{mask:i}))})};var t},hooks:function(){return{mutationObserverCallbacks:function(t){return t.treeCallback=Wa,t.nodeCallback=Ke,t}}},provides:function(t){t.i2svg=function(a){var n=a.node,e=n===void 0?S:n,i=a.callback;return Wa(e,i===void 0?function(){}:i)},t.generateSvgReplacementMutation=function(a,n){var e=n.iconName,i=n.prefix,r=n.transform,o=n.symbol,s=n.mask,c=n.maskId,l=n.extra;return new Promise(function(u,d){Promise.all([Zt(e,i),s.iconName?Zt(s.iconName,s.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(m){var g=yt(m,2),x=g[0],p=g[1];u([a,ma({icons:{main:x,mask:p},prefix:i,iconName:e,transform:r,symbol:o,maskId:c,extra:l,watchable:!0})])}).catch(d)})},t.generateAbstractIcon=function(a){var n,e=a.children,i=a.attributes,r=a.main,o=a.transform,s=xt(a.styles);return s.length>0&&(i.style=s),fa(o)&&(n=q("generateAbstractTransformGrouping",{main:r,transform:o,containerWidth:r.width,iconWidth:r.width})),e.push(n||r.icon),{children:e,attributes:i}}}},_e={mixout:function(){return{layer:function(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=a.classes,e=n===void 0?[]:n;return St({type:"layer"},function(){K("beforeDOMElementCreation",{assembler:t,params:a});var i=[];return t(function(r){Array.isArray(r)?r.map(function(o){i=i.concat(o.abstract)}):i=i.concat(r.abstract)}),[{tag:"span",attributes:{class:["".concat(b.cssPrefix,"-layers")].concat(D(e)).join(" ")},children:i}]})}}}},$e={mixout:function(){return{counter:function(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};a.title;var n=a.classes,e=n===void 0?[]:n,i=a.attributes,r=i===void 0?{}:i,o=a.styles,s=o===void 0?{}:o;return St({type:"counter",content:t},function(){return K("beforeDOMElementCreation",{content:t,params:a}),(function(c){var l=c.content,u=c.extra,d=f(f({},u.attributes),{},{class:u.classes.join(" ")}),m=xt(u.styles);m.length>0&&(d.style=m);var g=[];return g.push({tag:"span",attributes:d,children:[l]}),g})({content:t.toString(),extra:{attributes:r,styles:s,classes:["".concat(b.cssPrefix,"-layers-counter")].concat(D(e))}})})}}}},Ze={mixout:function(){return{text:function(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=a.transform,e=n===void 0?T:n,i=a.classes,r=i===void 0?[]:i,o=a.attributes,s=o===void 0?{}:o,c=a.styles,l=c===void 0?{}:c;return St({type:"text",content:t},function(){return K("beforeDOMElementCreation",{content:t,params:a}),Oa({content:t,transform:f(f({},T),e),extra:{attributes:s,styles:l,classes:["".concat(b.cssPrefix,"-layers-text")].concat(D(r))}})})}}},provides:function(t){t.generateLayersText=function(a,n){var e=n.transform,i=n.extra,r=null,o=null;if(fn){var s=parseInt(getComputedStyle(a).fontSize,10),c=a.getBoundingClientRect();r=c.width/s,o=c.height/s}return Promise.resolve([a,Oa({content:a.innerHTML,width:r,height:o,transform:e,extra:i,watchable:!0})])}}},Ba=new RegExp('"',"ug"),Ra=[1105920,1112319],Xa=f(f(f(f({},{FontAwesome:{normal:"fas",400:"fas"}}),{"Font Awesome 7 Free":{900:"fas",400:"far"},"Font Awesome 7 Pro":{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},"Font Awesome 7 Brands":{400:"fab",normal:"fab"},"Font Awesome 7 Duotone":{900:"fad",400:"fadr",normal:"fadr",300:"fadl",100:"fadt"},"Font Awesome 7 Sharp":{900:"fass",400:"fasr",normal:"fasr",300:"fasl",100:"fast"},"Font Awesome 7 Sharp Duotone":{900:"fasds",400:"fasdr",normal:"fasdr",300:"fasdl",100:"fasdt"},"Font Awesome 7 Jelly":{400:"fajr",normal:"fajr"},"Font Awesome 7 Jelly Fill":{400:"fajfr",normal:"fajfr"},"Font Awesome 7 Jelly Duo":{400:"fajdr",normal:"fajdr"},"Font Awesome 7 Slab":{400:"faslr",normal:"faslr"},"Font Awesome 7 Slab Press":{400:"faslpr",normal:"faslpr"},"Font Awesome 7 Slab Duo":{400:"fasldr",normal:"fasldr"},"Font Awesome 7 Slab Press Duo":{400:"faslpdr",normal:"faslpdr"},"Font Awesome 7 Pixel":{400:"fapr",normal:"fapr"},"Font Awesome 7 Mosaic":{900:"fams",normal:"fams"},"Font Awesome 7 Vellum":{900:"favs",normal:"favs"},"Font Awesome 7 Thumbprint":{300:"fatl",normal:"fatl"},"Font Awesome 7 Notdog":{900:"fans",normal:"fans"},"Font Awesome 7 Notdog Duo":{900:"fands",normal:"fands"},"Font Awesome 7 Etch":{900:"faes",normal:"faes"},"Font Awesome 7 Graphite":{100:"fagt",normal:"fagt"},"Font Awesome 7 Chisel":{400:"facr",normal:"facr"},"Font Awesome 7 Whiteboard":{600:"fawsb",normal:"fawsb"},"Font Awesome 7 Utility":{600:"fausb",normal:"fausb"},"Font Awesome 7 Utility Duo":{600:"faudsb",normal:"faudsb"},"Font Awesome 7 Utility Fill":{600:"faufsb",normal:"faufsb"}}),{"Font Awesome 5 Free":{900:"fas",400:"far"},"Font Awesome 5 Pro":{900:"fas",400:"far",normal:"far",300:"fal"},"Font Awesome 5 Brands":{400:"fab",normal:"fab"},"Font Awesome 5 Duotone":{900:"fad"}}),{"Font Awesome Kit":{400:"fak",normal:"fak"},"Font Awesome Kit Duotone":{400:"fakd",normal:"fakd"}}),aa=Object.keys(Xa).reduce(function(t,a){return t[a.toLowerCase()]=Xa[a],t},{}),Qe=Object.keys(aa).reduce(function(t,a){var n=aa[a];return t[a]=n[900]||D(Object.entries(n))[0][1],t},{});function Ua(t,a){var n="".concat("data-fa-pseudo-element-pending").concat(a.replace(":","-"));return new Promise(function(e,i){if(t.getAttribute(n)!==null)return e();var r,o,s,c=tt(t.children).filter(function(N){return N.getAttribute(Xt)===a})[0],l=U.getComputedStyle(t,a),u=l.getPropertyValue("font-family"),d=u.match(Ne),m=l.getPropertyValue("font-weight"),g=l.getPropertyValue("content");if(c&&!d)return t.removeChild(c),e();if(d&&g!=="none"&&g!==""){var x=l.getPropertyValue("content"),p=(function(N,O){var M=N.replace(/^['"]|['"]$/g,"").toLowerCase(),I=parseInt(O),X=isNaN(I)?"normal":I;return(aa[M]||{})[X]||Qe[M]})(u,m),v=(function(N){return Kn(D(N.replace(Ba,""))[0]||"")})(x),j=d[0].startsWith("FontAwesome"),z=(function(N){var O=N.getPropertyValue("font-feature-settings").includes("ss01"),M=N.getPropertyValue("content").replace(Ba,""),I=M.codePointAt(0),X=I>=Ra[0]&&I<=Ra[1],kt=M.length===2&&M[0]===M[1];return X||kt||O})(l),L=Vt(p,v),C=L;if(j){var y=(o=Zn[r=v],s=Vt("fas",r),o||(s?{prefix:"fas",iconName:s}:null)||{prefix:null,iconName:null});y.iconName&&y.prefix&&(L=y.iconName,p=y.prefix)}if(!L||z||c&&c.getAttribute(Ut)===p&&c.getAttribute(Yt)===C)e();else{t.setAttribute(n,C),c&&t.removeChild(c);var P={iconName:null,prefix:null,transform:T,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}},A=P.extra;A.attributes[Xt]=a,Zt(L,p).then(function(N){var O=ma(f(f({},P),{},{icons:{main:N,mask:{prefix:null,iconName:null,rest:[]}},prefix:p,iconName:C,extra:A,watchable:!0})),M=S.createElementNS("http://www.w3.org/2000/svg","svg");a==="::before"?t.insertBefore(M,t.firstChild):t.appendChild(M),M.outerHTML=O.map(function(I){return st(I)}).join(`
`),t.removeAttribute(n),e()}).catch(i)}}else e()})}function ti(t){return Promise.all([Ua(t,"::before"),Ua(t,"::after")])}function ai(t){return!(t.parentNode===document.head||~je.indexOf(t.tagName.toUpperCase())||t.getAttribute(Xt)||t.parentNode&&t.parentNode.tagName==="svg")}var ni=function(t){return!!t&&Bn.some(function(a){return t.includes(a)})},ei=function(t){if(!t)return[];var a,n=new Set,e=t.split(/,(?![^()]*\))/).map(function(s){return s.trim()}),i=pt(e=e.flatMap(function(s){return s.includes("(")?s:s.split(",").map(function(c){return c.trim()})}));try{for(i.s();!(a=i.n()).done;){var r=a.value;if(ni(r)){var o=Bn.reduce(function(s,c){return s.replace(c,"")},r);o!==""&&o!=="*"&&n.add(o)}}}catch(s){i.e(s)}finally{i.f()}return n};function Ya(t){if(R){var a;if(arguments.length>1&&arguments[1]!==void 0&&arguments[1])a=t;else if(b.searchPseudoElementsFullScan)a=t.querySelectorAll("*");else{var n,e=new Set,i=pt(document.styleSheets);try{for(i.s();!(n=i.n()).done;){var r=n.value;try{var o,s=pt(r.cssRules);try{for(s.s();!(o=s.n()).done;){var c,l=o.value,u=pt(ei(l.selectorText));try{for(u.s();!(c=u.n()).done;){var d=c.value;e.add(d)}}catch(g){u.e(g)}finally{u.f()}}}catch(g){s.e(g)}finally{s.f()}}catch{b.searchPseudoElementsWarnings}}}catch(g){i.e(g)}finally{i.f()}if(!e.size)return;var m=Array.from(e).join(", ");try{a=t.querySelectorAll(m)}catch{}}return new Promise(function(g,x){var p=tt(a).filter(ai).map(ti),v=da("searchPseudoElements");re(),Promise.all(p).then(function(){v(),ta(),g()}).catch(function(){v(),ta(),x()})})}}var qa=!1,Ja=function(t){return t.toLowerCase().split(" ").reduce(function(a,n){var e=n.toLowerCase().split("-"),i=e[0],r=e.slice(1).join("-");if(i&&r==="h")return a.flipX=!0,a;if(i&&r==="v")return a.flipY=!0,a;if(r=parseFloat(r),isNaN(r))return a;switch(i){case"grow":a.size=a.size+r;break;case"shrink":a.size=a.size-r;break;case"left":a.x=a.x-r;break;case"right":a.x=a.x+r;break;case"up":a.y=a.y-r;break;case"down":a.y=a.y+r;break;case"rotate":a.rotate=a.rotate+r}return a},{size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0})},ii={mixout:function(){return{parse:{transform:function(t){return Ja(t)}}}},hooks:function(){return{parseNodeAttributes:function(t,a){var n=a.getAttribute("data-fa-transform");return n&&(t.transform=Ja(n)),t}}},provides:function(t){t.generateAbstractTransformGrouping=function(a){var n=a.main,e=a.transform,i=a.containerWidth,r=a.iconWidth,o={transform:"translate(".concat(i/2," 256)")},s="translate(".concat(32*e.x,", ").concat(32*e.y,") "),c="scale(".concat(e.size/16*(e.flipX?-1:1),", ").concat(e.size/16*(e.flipY?-1:1),") "),l="rotate(".concat(e.rotate," 0 0)"),u={outer:o,inner:{transform:"".concat(s," ").concat(c," ").concat(l)},path:{transform:"translate(".concat(r/2*-1," -256)")}};return{tag:"g",attributes:f({},u.outer),children:[{tag:"g",attributes:f({},u.inner),children:[{tag:n.icon.tag,children:n.icon.children,attributes:f(f({},n.icon.attributes),u.path)}]}]}}}},Ot={x:0,y:0,width:"100%",height:"100%"};function Ha(t){var a=!(arguments.length>1&&arguments[1]!==void 0)||arguments[1];return t.attributes&&(t.attributes.fill||a)&&(t.attributes.fill="black"),t}var at,ri={hooks:function(){return{parseNodeAttributes:function(t,a){var n=a.getAttribute("data-fa-mask"),e=n?wt(n.split(" ").map(function(i){return i.trim()})):{prefix:null,iconName:null,rest:[]};return e.prefix||(e.prefix=Y()),t.mask=e,t.maskId=a.getAttribute("data-fa-mask-id"),t}}},provides:function(t){t.generateAbstractMask=function(a){var n,e=a.children,i=a.attributes,r=a.main,o=a.mask,s=a.maskId,c=a.transform,l=r.width,u=r.icon,d=o.width,m=o.icon,g=(function(P){var A=P.transform,N=P.containerWidth,O=P.iconWidth,M={transform:"translate(".concat(N/2," 256)")},I="translate(".concat(32*A.x,", ").concat(32*A.y,") "),X="scale(".concat(A.size/16*(A.flipX?-1:1),", ").concat(A.size/16*(A.flipY?-1:1),") "),kt="rotate(".concat(A.rotate," 0 0)");return{outer:M,inner:{transform:"".concat(I," ").concat(X," ").concat(kt)},path:{transform:"translate(".concat(O/2*-1," -256)")}}})({transform:c,containerWidth:d,iconWidth:l}),x={tag:"rect",attributes:f(f({},Ot),{},{fill:"white"})},p=u.children?{children:u.children.map(Ha)}:{},v={tag:"g",attributes:f({},g.inner),children:[Ha(f({tag:u.tag,attributes:f(f({},u.attributes),g.path)},p))]},j={tag:"g",attributes:f({},g.outer),children:[v]},z="mask-".concat(s||Sa()),L="clip-".concat(s||Sa()),C={tag:"mask",attributes:f(f({},Ot),{},{id:z,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[x,j]},y={tag:"defs",children:[{tag:"clipPath",attributes:{id:L},children:(n=m,n.tag==="g"?n.children:[n])},C]};return e.push(y,{tag:"rect",attributes:f({fill:"currentColor","clip-path":"url(#".concat(L,")"),mask:"url(#".concat(z,")")},Ot)}),{children:e,attributes:i}}}};at=ft,Fa=[Fe,Ge,_e,$e,Ze,{hooks:function(){return{mutationObserverCallbacks:function(t){return t.pseudoElementsCallback=Ya,t}}},provides:function(t){t.pseudoElements2svg=function(a){var n=a.node,e=n===void 0?S:n;b.searchPseudoElements&&Ya(e)}}},{mixout:function(){return{dom:{unwatch:function(){re(),qa=!0}}}},hooks:function(){return{bootstrap:function(){Da(Gt("mutationObserverCallbacks",{}))},noAuto:function(){vt&&vt.disconnect()},watch:function(t){var a=t.observeMutationsRoot;qa?ta():Da(Gt("mutationObserverCallbacks",{observeMutationsRoot:a}))}}}},ii,ri,{provides:function(t){var a=!1;U.matchMedia&&(a=U.matchMedia("(prefers-reduced-motion: reduce)").matches),t.missingIconAbstract=function(){var n=[],e={fill:"currentColor"},i={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};n.push({tag:"path",attributes:f(f({},e),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var r=f(f({},i),{},{attributeName:"opacity"}),o={tag:"circle",attributes:f(f({},e),{},{cx:"256",cy:"364",r:"28"}),children:[]};return a||o.children.push({tag:"animate",attributes:f(f({},i),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:f(f({},r),{},{values:"1;0;1;1;0;1;"})}),n.push(o),n.push({tag:"path",attributes:f(f({},e),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:a?[]:[{tag:"animate",attributes:f(f({},r),{},{values:"1;0;0;0;0;1;"})}]}),a||n.push({tag:"path",attributes:f(f({},e),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:f(f({},r),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:n}}}},{hooks:function(){return{parseNodeAttributes:function(t,a){var n=a.getAttribute("data-fa-symbol"),e=n!==null&&(n===""||n);return t.symbol=e,t}}}}],Z={},Object.keys(Q).forEach(function(t){We.indexOf(t)===-1&&delete Q[t]}),Fa.forEach(function(t){var a=t.mixout?t.mixout():{};if(Object.keys(a).forEach(function(e){typeof a[e]=="function"&&(at[e]=a[e]),ia(a[e])==="object"&&Object.keys(a[e]).forEach(function(i){at[e]||(at[e]={}),at[e][i]=a[e][i]})}),t.hooks){var n=t.hooks();Object.keys(n).forEach(function(e){Z[e]||(Z[e]=[]),Z[e].push(n[e])})}t.provides&&t.provides(Q)});var pi=ft.library,na=ft.parse,oi=ft.icon;function Lt(t,a){(a==null||a>t.length)&&(a=t.length);for(var n=0,e=Array(a);n<a;n++)e[n]=t[n];return e}function w(t,a,n){return(a=(function(e){var i=(function(r,o){if(typeof r!="object"||!r)return r;var s=r[Symbol.toPrimitive];if(s!==void 0){var c=s.call(r,o);if(typeof c!="object")return c;throw new TypeError("@@toPrimitive must return a primitive value.")}return(o==="string"?String:Number)(r)})(e,"string");return typeof i=="symbol"?i:i+""})(a))in t?Object.defineProperty(t,a,{value:n,enumerable:!0,configurable:!0,writable:!0}):t[a]=n,t}function Ka(t,a){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(t);a&&(e=e.filter(function(i){return Object.getOwnPropertyDescriptor(t,i).enumerable})),n.push.apply(n,e)}return n}function k(t){for(var a=1;a<arguments.length;a++){var n=arguments[a]!=null?arguments[a]:{};a%2?Ka(Object(n),!0).forEach(function(e){w(t,e,n[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):Ka(Object(n)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))})}return t}function Ct(t,a){if(t==null)return{};var n,e,i=(function(o,s){if(o==null)return{};var c={};for(var l in o)if({}.hasOwnProperty.call(o,l)){if(s.indexOf(l)!==-1)continue;c[l]=o[l]}return c})(t,a);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);for(e=0;e<r.length;e++)n=r[e],a.indexOf(n)===-1&&{}.propertyIsEnumerable.call(t,n)&&(i[n]=t[n])}return i}function li(t){return(function(a){if(Array.isArray(a))return Lt(a)})(t)||(function(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)})(t)||(function(a,n){if(a){if(typeof a=="string")return Lt(a,n);var e={}.toString.call(a).slice(8,-1);return e==="Object"&&a.constructor&&(e=a.constructor.name),e==="Map"||e==="Set"?Array.from(a):e==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(e)?Lt(a,n):void 0}})(t)||(function(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)})()}function ea(t){return(ea=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(a){return typeof a}:function(a){return a&&typeof Symbol=="function"&&a.constructor===Symbol&&a!==Symbol.prototype?"symbol":typeof a})(t)}function Et(t,a){return Array.isArray(a)&&a.length>0||!Array.isArray(a)&&a?w({},t,a):{}}var Dt,Va,_,ut,Tt,mt,nt,Ga,_a,$a,Za,Qa,tn,an,dt,Wt,si=typeof globalThis<"u"?globalThis:typeof window<"u"?window:pa!==void 0?pa:typeof self<"u"?self:{},le={exports:{}};Dt=le,Va=si,_=function(t,a,n){if(!_a(a)||Za(a)||Qa(a)||tn(a)||Ga(a))return a;var e,i=0,r=0;if($a(a))for(e=[],r=a.length;i<r;i++)e.push(_(t,a[i],n));else for(var o in e={},a)Object.prototype.hasOwnProperty.call(a,o)&&(e[t(o,n)]=_(t,a[o],n));return e},ut=function(t){return an(t)?t:(t=t.replace(/[\-_\s]+(.)?/g,function(a,n){return n?n.toUpperCase():""})).substr(0,1).toLowerCase()+t.substr(1)},Tt=function(t){var a=ut(t);return a.substr(0,1).toUpperCase()+a.substr(1)},mt=function(t,a){return(function(n,e){var i=(e=e||{}).separator||"_",r=e.split||/(?=[A-Z])/;return n.split(r).join(i)})(t,a).toLowerCase()},nt=Object.prototype.toString,Ga=function(t){return typeof t=="function"},_a=function(t){return t===Object(t)},$a=function(t){return nt.call(t)=="[object Array]"},Za=function(t){return nt.call(t)=="[object Date]"},Qa=function(t){return nt.call(t)=="[object RegExp]"},tn=function(t){return nt.call(t)=="[object Boolean]"},an=function(t){return(t-=0)==t},dt=function(t,a){var n=a&&"process"in a?a.process:a;return typeof n!="function"?t:function(e,i){return n(e,t,i)}},Wt={camelize:ut,decamelize:mt,pascalize:Tt,depascalize:mt,camelizeKeys:function(t,a){return _(dt(ut,a),t)},decamelizeKeys:function(t,a){return _(dt(mt,a),t,a)},pascalizeKeys:function(t,a){return _(dt(Tt,a),t)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}},Dt.exports?Dt.exports=Wt:Va.humps=Wt;var fi=le.exports,ci=["gradientFill"],ui=["class","style"],mi=["type","stops","id"];function di(t,a){return gt("stop",k({key:"".concat(a,"-").concat(t.offset),offset:t.offset,"stop-color":t.color},t.opacity!==void 0&&{"stop-opacity":t.opacity}))}function se(t){if(typeof t=="string")return t;var a=(t.children||[]).map(se);return t.tag==="path"&&t.attributes&&"fill"in t.attributes?k(k({},t),{},{attributes:k(k({},t.attributes),{},{fill:void 0}),children:a}):k(k({},t),{},{children:a})}function fe(t){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof t=="string")return t;var e=a.gradientFill,i=e===void 0?null:e,r=Ct(a,ci),o=i||"fill"in n?se(t):t,s=(o.children||[]).map(function(z){return fe(z,{},{})}),c=Object.keys(o.attributes||{}).reduce(function(z,L){var C=o.attributes[L];switch(L){case"class":z.class=C.split(/\s+/).reduce(function(y,P){return y[P]=!0,y},{});break;case"style":z.style=C.split(";").map(function(y){return y.trim()}).filter(function(y){return y}).reduce(function(y,P){var A=P.indexOf(":"),N=fi.camelize(P.slice(0,A)),O=P.slice(A+1).trim();return y[N]=O,y},{});break;default:z.attrs[L]=C}return z},{attrs:{},class:{},style:{}});n.class;var l=n.style,u=l===void 0?{}:l,d=Ct(n,ui);if(i&&i.id&&(i.type==="linear"||i.type==="radial")){var m=i.type,g=i.stops,x=g===void 0?[]:g,p=i.id,v=Ct(i,mi),j=gt(m==="linear"?"linearGradient":"radialGradient",k(k({},v),{},{id:p}),x.map(di));return gt(o.tag,k(k(k(k({},r),{},{class:c.class,style:k(k({},c.style),u)},c.attrs),d),{},{fill:"url(#".concat(p,")")}),[j].concat(li(s)))}return gt(t.tag,k(k(k({},r),{},{class:c.class,style:k(k({},c.style),u)},c.attrs),d),s)}var ce=!1;try{ce=!0}catch{}function nn(){var t;!ce&&console&&typeof console.error=="function"&&(t=console).error.apply(t,arguments)}function en(t){return t&&ea(t)==="object"&&t.prefix&&t.iconName&&t.icon?t:na.icon?na.icon(t):t===null?null:ea(t)==="object"&&t.prefix&&t.iconName?t:Array.isArray(t)&&t.length===2?{prefix:t[0],iconName:t[1]}:typeof t=="string"?{prefix:"fas",iconName:t}:void 0}var bi=ue({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(t){return[!0,!1,"horizontal","vertical","both"].indexOf(t)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},maskId:{type:String,default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(t){return["right","left"].indexOf(t)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(t){return[90,180,270].indexOf(Number.parseInt(t,10))>-1}},rotateBy:{type:Boolean,default:!1},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(t){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(t)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},titleId:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1},widthAuto:{type:Boolean,default:!1},canvasSquare:{type:Boolean,default:!1},canvasRoomy:{type:Boolean,default:!1},gradientFill:{type:Object,default:null,validator:function(t){return!(typeof t.id!="string"||!t.id)&&(t.type==="linear"||t.type==="radial")}},flip360:{type:Boolean,default:!1},buzz:{type:Boolean,default:!1},float:{type:Boolean,default:!1},jello:{type:Boolean,default:!1},spinSnap:{type:Boolean,default:!1},spinSnap4:{type:Boolean,default:!1},spinSnap8:{type:Boolean,default:!1},swing:{type:Boolean,default:!1},wag:{type:Boolean,default:!1}},setup:function(t,a){var n=a.attrs,e=V(function(){return en(t.icon)}),i=V(function(){return Et("classes",(function(l){var u,d=(w(w(w(w(w(w(w(w(w(w(u={"fa-spin":l.spin,"fa-pulse":l.pulse,"fa-fw":l.fixedWidth,"fa-border":l.border,"fa-li":l.listItem,"fa-inverse":l.inverse,"fa-flip":l.flip===!0,"fa-flip-horizontal":l.flip==="horizontal"||l.flip==="both","fa-flip-vertical":l.flip==="vertical"||l.flip==="both"},"fa-".concat(l.size),l.size!==null),"fa-rotate-".concat(l.rotation),l.rotation!==null),"fa-rotate-by",l.rotateBy),"fa-pull-".concat(l.pull),l.pull!==null),"fa-swap-opacity",l.swapOpacity),"fa-bounce",l.bounce),"fa-shake",l.shake),"fa-beat",l.beat),"fa-fade",l.fade),"fa-beat-fade",l.beatFade),w(w(w(w(w(w(w(w(w(w(u,"fa-flash",l.flash),"fa-spin-pulse",l.spinPulse),"fa-spin-reverse",l.spinReverse),"fa-width-auto",l.widthAuto),"fa-canvas-square",l.canvasSquare),"fa-canvas-roomy",l.canvasRoomy),"fa-flip-360",l.flip360),"fa-buzz",l.buzz),"fa-float",l.float),"fa-jello",l.jello),w(w(w(w(w(u,"fa-spin-snap",l.spinSnap),"fa-spin-snap-4",l.spinSnap4),"fa-spin-snap-8",l.spinSnap8),"fa-swing",l.swing),"fa-wag",l.wag));return Object.keys(d).map(function(m){return d[m]?m:null}).filter(function(m){return m})})(t))}),r=V(function(){return Et("transform",typeof t.transform=="string"?na.transform(t.transform):t.transform)}),o=V(function(){return Et("mask",en(t.mask))}),s=V(function(){var l=k(k(k(k({},i.value),r.value),o.value),{},{symbol:t.symbol,maskId:t.maskId});return l.title=t.title,l.titleId=t.titleId,oi(e.value,l)});me(s,function(l){if(!l)return nn("Could not find one or more icon(s)",e.value,o.value)},{immediate:!0}),t.gradientFill&&t.symbol&&nn("gradientFill is not supported when symbol is true and will be ignored");var c=V(function(){return s.value?fe(s.value.abstract[0],{gradientFill:t.symbol?null:t.gradientFill},n):null});return function(){return c.value}}}),hi={prefix:"fas",iconName:"right-long",icon:[576,512,["long-arrow-alt-right"],"f30b","M566.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-128 128c-9.2 9.2-22.9 11.9-34.9 6.9S384 396.9 384 384l0-64-336 0c-26.5 0-48-21.5-48-48l0-32c0-26.5 21.5-48 48-48l336 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l128 128z"]},vi={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-384c0-35.3-28.7-64-64-64L64 0zM96 64l192 0c17.7 0 32 14.3 32 32l0 32c0 17.7-14.3 32-32 32L96 160c-17.7 0-32-14.3-32-32l0-32c0-17.7 14.3-32 32-32zm16 168a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zM88 352a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zM64 424c0-13.3 10.7-24 24-24l112 0c13.3 0 24 10.7 24 24s-10.7 24-24 24L88 448c-13.3 0-24-10.7-24-24zm232-24c13.3 0 24 10.7 24 24s-10.7 24-24 24-24-10.7-24-24 10.7-24 24-24z"]},yi={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4l-26.1 74.6 293.8 0-26.1-74.6C372.3 104.6 360.2 96 346.6 96L165.4 96c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32l181.2 0c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2l0 192c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-32-320 0 0 32c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32L0 256c0-26.7 16.4-49.6 39.6-59.2zM128 304a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},xi={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zM64 240l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm128 0l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zM64 368l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zm112 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16z"]},zi={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 0c0-17.7-14.3-32-32-32S224-17.7 224 0l0 256c0 17.7 14.3 32 32 32s32-14.3 32-32L288 0zM146.3 98.4c14.5-10.1 18-30.1 7.9-44.6s-30.1-18-44.6-7.9C43.4 92.1 0 169 0 256 0 397.4 114.6 512 256 512S512 397.4 512 256c0-87-43.4-163.9-109.7-210.1-14.5-10.1-34.4-6.6-44.6 7.9s-6.6 34.4 7.9 44.6c49.8 34.8 82.3 92.4 82.3 157.6 0 106-86 192-192 192S64 362 64 256c0-65.2 32.5-122.9 82.3-157.6z"]},wi={prefix:"fas",iconName:"eye",icon:[576,512,[128065],"f06e","M288 32c-80.8 0-145.5 36.8-192.6 80.6-46.8 43.5-78.1 95.4-93 131.1-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6s145.5-36.8 192.6-80.6c46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6zM144 256a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm144-64c0 35.3-28.7 64-64 64-11.5 0-22.3-3-31.7-8.4-1 10.9-.1 22.1 2.9 33.2 13.7 51.2 66.4 81.6 117.6 67.9s81.6-66.4 67.9-117.6c-12.2-45.7-55.5-74.8-101.1-70.8 5.3 9.3 8.4 20.1 8.4 31.7z"]},Si={prefix:"fas",iconName:"delete-left",icon:[640,512,[9003,"backspace"],"f55a","M576 128c0-35.3-28.7-64-64-64L205.3 64c-17 0-33.3 6.7-45.3 18.7L9.4 233.4c-6 6-9.4 14.1-9.4 22.6s3.4 16.6 9.4 22.6L160 429.3c12 12 28.3 18.7 45.3 18.7L512 448c35.3 0 64-28.7 64-64l0-256zM284.1 188.1c9.4-9.4 24.6-9.4 33.9 0l33.9 33.9 33.9-33.9c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-33.9 33.9 33.9 33.9c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-33.9-33.9-33.9 33.9c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l33.9-33.9-33.9-33.9c-9.4-9.4-9.4-24.6 0-33.9z"]},ki={prefix:"fas",iconName:"pen-to-square",icon:[512,512,["edit"],"f044","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L368 46.1 465.9 144 490.3 119.6c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L432 177.9 334.1 80 172.4 241.7zM96 64C43 64 0 107 0 160L0 416c0 53 43 96 96 96l256 0c53 0 96-43 96-96l0-96c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 96c0 17.7-14.3 32-32 32L96 448c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l96 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 64z"]},ji={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512 256 256 0 1 1 0-512zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},Ai={prefix:"fas",iconName:"battery-half",icon:[640,512,["battery-3"],"f242","M528 128c8.8 0 16 7.2 16 16l0 224c0 8.8-7.2 16-16 16l-416 0c-8.8 0-16-7.2-16-16l0-224c0-8.8 7.2-16 16-16l416 0zM112 64c-44.2 0-80 35.8-80 80l0 224c0 44.2 35.8 80 80 80l416 0c44.2 0 80-35.8 80-80l0-48c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l0-48c0-44.2-35.8-80-80-80L112 64zm56 112c-13.3 0-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24l144 0c13.3 0 24-10.7 24-24l0-112c0-13.3-10.7-24-24-24l-144 0z"]},Pi={prefix:"fas",iconName:"arrow-right-to-bracket",icon:[512,512,["sign-in"],"f090","M352 96l64 0c17.7 0 32 14.3 32 32l0 256c0 17.7-14.3 32-32 32l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l64 0c53 0 96-43 96-96l0-256c0-53-43-96-96-96l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32zm-9.4 182.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L242.7 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},Ni={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM167 167c9.4-9.4 24.6-9.4 33.9 0l55 55 55-55c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-55 55 55 55c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-55-55-55 55c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l55-55-55-55c-9.4-9.4-9.4-24.6 0-33.9z"]},Mi={prefix:"fas",iconName:"plug-circle-bolt",icon:[640,512,[],"e55b","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm177.4-77c-5.8-4.2-13.8-4-19.4 .5l-80 64c-5.3 4.2-7.4 11.4-5.1 17.8S433.2 416 440 416l32.9 0-15.9 42.4c-2.5 6.7-.2 14.3 5.6 18.6s13.8 4 19.4-.5l80-64c5.3-4.2 7.4-11.4 5.1-17.8S558.8 384 552 384l-32.9 0 15.9-42.4c2.5-6.7 .2-14.3-5.6-18.6z"]},Ii={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l64 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-64 0z"]},Fi={prefix:"fas",iconName:"circle-user",icon:[512,512,[62142,"user-circle"],"f2bd","M399 384.2C376.9 345.8 335.4 320 288 320l-64 0c-47.4 0-88.9 25.8-111 64.2 35.2 39.2 86.2 63.8 143 63.8s107.8-24.7 143-63.8zM0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zm256 16a72 72 0 1 0 0-144 72 72 0 1 0 0 144z"]},Oi={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 64c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l16 0c35.3 0 64 28.7 64 64l0 256c0 35.3-28.7 64-64 64L64 448c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l16 0zM392 184c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 32-32 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l32 0 0 32c0 13.3 10.7 24 24 24s24-10.7 24-24l0-32 32 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-32 0 0-32zM64 240c0 13.3 10.7 24 24 24l112 0c13.3 0 24-10.7 24-24s-10.7-24-24-24L88 216c-13.3 0-24 10.7-24 24z"]},Li={prefix:"fas",iconName:"wrench",icon:[576,512,[128295],"f0ad","M509.4 98.6c7.6-7.6 20.3-5.7 24.1 4.3 6.8 17.7 10.5 37 10.5 57.1 0 88.4-71.6 160-160 160-17.5 0-34.4-2.8-50.2-8L146.9 498.9c-28.1 28.1-73.7 28.1-101.8 0s-28.1-73.7 0-101.8L232 210.2c-5.2-15.8-8-32.6-8-50.2 0-88.4 71.6-160 160-160 20.1 0 39.4 3.7 57.1 10.5 10 3.8 11.8 16.5 4.3 24.1l-88.7 88.7c-3 3-4.7 7.1-4.7 11.3l0 41.4c0 8.8 7.2 16 16 16l41.4 0c4.2 0 8.3-1.7 11.3-4.7l88.7-88.7z"]},Ci={prefix:"fas",iconName:"eraser",icon:[576,512,[],"f12d","M178.5 416l123 0 65.3-65.3-173.5-173.5-126.7 126.7 112 112zM224 480l-45.5 0c-17 0-33.3-6.7-45.3-18.7L17 345C6.1 334.1 0 319.4 0 304s6.1-30.1 17-41L263 17C273.9 6.1 288.6 0 304 0s30.1 6.1 41 17L527 199c10.9 10.9 17 25.6 17 41s-6.1 30.1-17 41l-135 135 120 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-288 0z"]},Ei={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M64 64C64 28.7 92.7 0 128 0L288 0c35.3 0 64 28.7 64 64l0 224c44.2 0 80 35.8 80 80l0 12c0 11 9 20 20 20s20-9 20-20l0-127.7c-32.5-10.2-56-40.5-56-76.3l0-32c0-8.8 7.2-16 16-16l16 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 32 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 16 0c8.8 0 16 7.2 16 16l0 32c0 35.8-23.5 66.1-56 76.3L520 380c0 37.6-30.4 68-68 68s-68-30.4-68-68l0-12c0-17.7-14.3-32-32-32l0 129.4c9.3 3.3 16 12.2 16 22.6 0 13.3-10.7 24-24 24L72 512c-13.3 0-24-10.7-24-24 0-10.5 6.7-19.3 16-22.6L64 64zm82.7 125.7l39 0-20.9 66.9c-2.4 7.6 3.3 15.4 11.3 15.4 2.9 0 5.6-1 7.8-2.9l94.6-82c3.1-2.7 4.9-6.6 4.9-10.7 0-7.8-6.3-14.1-14.1-14.1l-39 0 20.9-66.9c2.4-7.6-3.3-15.4-11.3-15.4-2.9 0-5.6 1-7.8 2.9l-94.6 82c-3.1 2.7-4.9 6.6-4.9 10.7 0 7.8 6.3 14.1 14.1 14.1z"]},Di={prefix:"fas",iconName:"house",icon:[512,512,[127968,63498,63500,"home","home-alt","home-lg-alt"],"f015","M277.8 8.6c-12.3-11.4-31.3-11.4-43.5 0l-224 208c-9.6 9-12.8 22.9-8 35.1S18.8 272 32 272l16 0 0 176c0 35.3 28.7 64 64 64l288 0c35.3 0 64-28.7 64-64l0-176 16 0c13.2 0 25-8.1 29.8-20.3s1.6-26.2-8-35.1l-224-208zM240 320l32 0c26.5 0 48 21.5 48 48l0 96-128 0 0-96c0-26.5 21.5-48 48-48z"]},Ti={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64 0-16.2-6-31.1-16-42.3l69.5-138.9c5.9-11.9 1.1-26.3-10.7-32.2s-26.3-1.1-32.2 10.7L261.1 288.2c-1.7-.1-3.4-.2-5.1-.2-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},Wi={prefix:"fas",iconName:"right-left",icon:[512,512,["exchange-alt"],"f362","M502.6 150.6l-96 96c-9.2 9.2-22.9 11.9-34.9 6.9S352 236.9 352 224l0-64-320 0c-17.7 0-32-14.3-32-32S14.3 96 32 96l320 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l96 96c12.5 12.5 12.5 32.8 0 45.3zm-397.3 352l-96-96c-12.5-12.5-12.5-32.8 0-45.3l96-96c9.2-9.2 22.9-11.9 34.9-6.9S160 275.1 160 288l0 64 320 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-320 0 0 64c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9z"]},Bi={prefix:"fas",iconName:"lock-open",icon:[576,512,[],"f3c1","M384 96c0-35.3 28.7-64 64-64s64 28.7 64 64l0 32c0 17.7 14.3 32 32 32s32-14.3 32-32l0-32c0-70.7-57.3-128-128-128S320 25.3 320 96l0 64-160 0c-35.3 0-64 28.7-64 64l0 224c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-224c0-35.3-28.7-64-64-64l-32 0 0-64z"]},Ri={prefix:"fas",iconName:"circle-check",icon:[512,512,[61533,"check-circle"],"f058","M256 512a256 256 0 1 1 0-512 256 256 0 1 1 0 512zM374 145.7c-10.7-7.8-25.7-5.4-33.5 5.3L221.1 315.2 169 263.1c-9.4-9.4-24.6-9.4-33.9 0s-9.4 24.6 0 33.9l72 72c5 5 11.8 7.5 18.8 7s13.4-4.1 17.5-9.8L379.3 179.2c7.8-10.7 5.4-25.7-5.3-33.5z"]},Xi={prefix:"fas",iconName:"plug-circle-xmark",icon:[640,512,[],"e560","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM496 256a144 144 0 1 1 0 288 144 144 0 1 1 0-288zm59.3 107.3c6.2-6.2 6.2-16.4 0-22.6s-16.4-6.2-22.6 0l-36.7 36.7-36.7-36.7c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l36.7 36.7-36.7 36.7c-6.2 6.2-6.2 16.4 0 22.6s16.4 6.2 22.6 0l36.7-36.7 36.7 36.7c6.2 6.2 16.4 6.2 22.6 0s6.2-16.4 0-22.6l-36.7-36.7 36.7-36.7z"]},Ui={prefix:"fas",iconName:"solar-panel",icon:[576,512,[],"f5ba","M121.8 32c-30 0-56 20.8-62.5 50.1L9.6 306.1C.7 346.1 31.1 384 72 384l184.1 0 0 64-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l192 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0 0-64 184.1 0c40.9 0 71.4-37.9 62.5-77.9l-49.8-224C510.4 52.8 484.5 32 454.5 32L121.8 32zM245.6 96l85.2 0 7.3 88-99.8 0 7.3-88zm-55.5 88l-87.8 0 19.6-88 75.6 0-7.3 88zM91.6 232l94.5 0-7.3 88-106.7 0 19.6-88zm142.6 0l107.8 0 7.3 88-122.5 0 7.3-88zm156 0l94.5 0 19.6 88-106.7 0-7.3-88zM474 184l-87.8 0-7.3-88 75.6 0 19.6 88z"]},Yi={prefix:"fas",iconName:"plug-circle-check",icon:[640,512,[],"e55c","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm201.4-60.9c-7.1-5.2-17.2-3.6-22.4 3.5l-53 72.9-26.8-26.8c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l40 40c3.3 3.3 7.9 5 12.6 4.6s8.9-2.8 11.7-6.5l64-88c5.2-7.1 3.6-17.2-3.5-22.3z"]},qi={prefix:"fas",iconName:"star",icon:[576,512,[11088,61446],"f005","M309.5-18.9c-4.1-8-12.4-13.1-21.4-13.1s-17.3 5.1-21.4 13.1L193.1 125.3 33.2 150.7c-8.9 1.4-16.3 7.7-19.1 16.3s-.5 18 5.8 24.4l114.4 114.5-25.2 159.9c-1.4 8.9 2.3 17.9 9.6 23.2s16.9 6.1 25 2L288.1 417.6 432.4 491c8 4.1 17.7 3.3 25-2s11-14.2 9.6-23.2L441.7 305.9 556.1 191.4c6.4-6.4 8.6-15.8 5.8-24.4s-10.1-14.9-19.1-16.3L383 125.3 309.5-18.9z"]},Ji={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 0c14.7 0 28.2 8.1 35.2 21l216 400c6.7 12.4 6.4 27.4-.8 39.5S486.1 480 472 480L40 480c-14.1 0-27.2-7.4-34.4-19.5s-7.5-27.1-.8-39.5l216-400c7-12.9 20.5-21 35.2-21zm0 352a32 32 0 1 0 0 64 32 32 0 1 0 0-64zm0-192c-18.2 0-32.7 15.5-31.4 33.7l7.4 104c.9 12.5 11.4 22.3 23.9 22.3 12.6 0 23-9.7 23.9-22.3l7.4-104c1.3-18.2-13.1-33.7-31.4-33.7z"]},Hi={prefix:"fas",iconName:"lock",icon:[384,512,[128274],"f023","M128 96l0 64 128 0 0-64c0-35.3-28.7-64-64-64s-64 28.7-64 64zM64 160l0-64C64 25.3 121.3-32 192-32S320 25.3 320 96l0 64c35.3 0 64 28.7 64 64l0 224c0 35.3-28.7 64-64 64L64 512c-35.3 0-64-28.7-64-64L0 224c0-35.3 28.7-64 64-64z"]},Ki={prefix:"fas",iconName:"arrow-right-from-bracket",icon:[512,512,["sign-out"],"f08b","M160 96c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 32C43 32 0 75 0 128L0 384c0 53 43 96 96 96l64 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l64 0zM502.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L402.7 224 192 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},Vi={prefix:"fas",iconName:"battery-full",icon:[640,512,[128267,"battery","battery-5"],"f240","M528 128c8.8 0 16 7.2 16 16l0 224c0 8.8-7.2 16-16 16l-416 0c-8.8 0-16-7.2-16-16l0-224c0-8.8 7.2-16 16-16l416 0zM112 64c-44.2 0-80 35.8-80 80l0 224c0 44.2 35.8 80 80 80l416 0c44.2 0 80-35.8 80-80l0-48c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l0-48c0-44.2-35.8-80-80-80L112 64zm56 112c-13.3 0-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24l304 0c13.3 0 24-10.7 24-24l0-112c0-13.3-10.7-24-24-24l-304 0z"]},Gi={prefix:"fas",iconName:"eye-slash",icon:[576,512,[],"f070","M41-24.9c-9.4-9.4-24.6-9.4-33.9 0S-2.3-.3 7 9.1l528 528c9.4 9.4 24.6 9.4 33.9 0s9.4-24.6 0-33.9l-96.4-96.4c2.7-2.4 5.4-4.8 8-7.2 46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6-56.8 0-105.6 18.2-146 44.2L41-24.9zM204.5 138.7c23.5-16.8 52.4-26.7 83.5-26.7 79.5 0 144 64.5 144 144 0 31.1-9.9 59.9-26.7 83.5l-34.7-34.7c12.7-21.4 17-47.7 10.1-73.7-13.7-51.2-66.4-81.6-117.6-67.9-8.6 2.3-16.7 5.7-24 10l-34.7-34.7zM325.3 395.1c-11.9 3.2-24.4 4.9-37.3 4.9-79.5 0-144-64.5-144-144 0-12.9 1.7-25.4 4.9-37.3L69.4 139.2c-32.6 36.8-55 75.8-66.9 104.5-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6 37.3 0 71.2-7.9 101.5-20.6l-64.2-64.2z"]},_i={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M338.8-9.9c11.9 8.6 16.3 24.2 10.9 37.8L271.3 224 416 224c13.5 0 25.5 8.4 30.1 21.1s.7 26.9-9.6 35.5l-288 240c-11.3 9.4-27.4 9.9-39.3 1.3s-16.3-24.2-10.9-37.8L176.7 288 32 288c-13.5 0-25.5-8.4-30.1-21.1s-.7-26.9 9.6-35.5l288-240c11.3-9.4 27.4-9.9 39.3-1.3z"]},$i={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M256 64c-56.8 0-107.9 24.7-143.1 64l47.1 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 192c-17.7 0-32-14.3-32-32L0 32C0 14.3 14.3 0 32 0S64 14.3 64 32l0 54.7C110.9 33.6 179.5 0 256 0 397.4 0 512 114.6 512 256S397.4 512 256 512c-87 0-163.9-43.4-210.1-109.7-10.1-14.5-6.6-34.4 7.9-44.6s34.4-6.6 44.6 7.9c34.8 49.8 92.4 82.3 157.6 82.3 106 0 192-86 192-192S362 64 256 64z"]},Zi={prefix:"fas",iconName:"coins",icon:[512,512,[],"f51e","M128 96l0-16c0-44.2 86-80 192-80S512 35.8 512 80l0 16c0 30.6-41.3 57.2-102 70.7-2.4-2.8-4.9-5.5-7.4-8-15.5-15.3-35.5-26.9-56.4-35.5-41.9-17.5-96.5-27.1-154.2-27.1-21.9 0-43.3 1.4-63.8 4.1-.2-1.3-.2-2.7-.2-4.1zM432 353l0-46.2c15.1-3.9 29.3-8.5 42.2-13.9 13.2-5.5 26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zm0-96l0-33c0-4.5-.4-8.8-1-13 15.5-3.9 30-8.6 43.2-14.2s26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zM0 240l0-16c0-44.2 86-80 192-80s192 35.8 192 80l0 16c0 44.2-86 80-192 80S0 284.2 0 240zm384 96c0 44.2-86 80-192 80S0 380.2 0 336l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3l0 15.4zm0 80.6l0 15.4c0 44.2-86 80-192 80S0 476.2 0 432l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3z"]},Qi={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-192 0z"]},tr={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM224 160a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm-8 64l48 0c13.3 0 24 10.7 24 24l0 88 8 0c13.3 0 24 10.7 24 24s-10.7 24-24 24l-80 0c-13.3 0-24-10.7-24-24s10.7-24 24-24l24 0 0-64-24 0c-13.3 0-24-10.7-24-24s10.7-24 24-24z"]},ar={prefix:"far",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M464 256a208 208 0 1 1 -416 0 208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0 256 256 0 1 0 -512 0zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},nr={prefix:"far",iconName:"star",icon:[576,512,[11088,61446],"f005","M288.1-32c9 0 17.3 5.1 21.4 13.1L383 125.3 542.9 150.7c8.9 1.4 16.3 7.7 19.1 16.3s.5 18-5.8 24.4L441.7 305.9 467 465.8c1.4 8.9-2.3 17.9-9.6 23.2s-17 6.1-25 2L288.1 417.6 143.8 491c-8 4.1-17.7 3.3-25-2s-11-14.2-9.6-23.2L134.4 305.9 20 191.4c-6.4-6.4-8.6-15.8-5.8-24.4s10.1-14.9 19.1-16.3l159.9-25.4 73.6-144.2c4.1-8 12.4-13.1 21.4-13.1zm0 76.8L230.3 158c-3.5 6.8-10 11.6-17.6 12.8l-125.5 20 89.8 89.9c5.4 5.4 7.9 13.1 6.7 20.7l-19.8 125.5 113.3-57.6c6.8-3.5 14.9-3.5 21.8 0l113.3 57.6-19.8-125.5c-1.2-7.6 1.3-15.3 6.7-20.7l89.8-89.9-125.5-20c-7.6-1.2-14.1-6-17.6-12.8L288.1 44.8z"]};export{nr as A,ji as B,ar as C,_i as D,Ii as E,bi as F,Qi as G,xi as H,Wi as I,hi as J,Zi as K,Xi as L,Yi as M,Mi as N,$i as O,zi as P,Ci as a,Hi as b,Bi as c,Fi as d,Pi as e,Si as f,Ki as g,wi as h,Gi as i,Ti as j,Vi as k,pi as l,Ui as m,Di as n,Ei as o,Ai as p,yi as q,Ri as r,Ji as s,Ni as t,vi as u,Li as v,Oi as w,ki as x,tr as y,qi as z};
