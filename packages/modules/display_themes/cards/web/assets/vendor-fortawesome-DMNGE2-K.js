import{g as ea,d as Dt,w as Rt,c as B,h as Wt}from"./vendor-ELON-1B6.js";function Ie(e,a){(a==null||a>e.length)&&(a=e.length);for(var t=0,n=Array(a);t<a;t++)n[t]=e[t];return n}function Ut(e){if(Array.isArray(e))return e}function Bt(e){if(Array.isArray(e))return Ie(e)}function Yt(e,a){if(!(e instanceof a))throw new TypeError("Cannot call a class as a function")}function Ht(e,a){for(var t=0;t<a.length;t++){var n=a[t];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,Ma(n.key),n)}}function Gt(e,a,t){return a&&Ht(e.prototype,a),Object.defineProperty(e,"prototype",{writable:!1}),e}function ie(e,a){var t=typeof Symbol<"u"&&e[Symbol.iterator]||e["@@iterator"];if(!t){if(Array.isArray(e)||(t=Ue(e))||a){t&&(e=t);var n=0,r=function(){};return{s:r,n:function(){return n>=e.length?{done:!0}:{done:!1,value:e[n++]}},e:function(l){throw l},f:r}}throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var i,o=!0,s=!1;return{s:function(){t=t.call(e)},n:function(){var l=t.next();return o=l.done,l},e:function(l){s=!0,i=l},f:function(){try{o||t.return==null||t.return()}finally{if(s)throw i}}}}function g(e,a,t){return(a=Ma(a))in e?Object.defineProperty(e,a,{value:t,enumerable:!0,configurable:!0,writable:!0}):e[a]=t,e}function Xt(e){if(typeof Symbol<"u"&&e[Symbol.iterator]!=null||e["@@iterator"]!=null)return Array.from(e)}function Kt(e,a){var t=e==null?null:typeof Symbol<"u"&&e[Symbol.iterator]||e["@@iterator"];if(t!=null){var n,r,i,o,s=[],l=!0,c=!1;try{if(i=(t=t.call(e)).next,a===0){if(Object(t)!==t)return;l=!1}else for(;!(l=(n=i.call(t)).done)&&(s.push(n.value),s.length!==a);l=!0);}catch(u){c=!0,r=u}finally{try{if(!l&&t.return!=null&&(o=t.return(),Object(o)!==o))return}finally{if(c)throw r}}return s}}function Vt(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function Jt(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function aa(e,a){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);a&&(n=n.filter(function(r){return Object.getOwnPropertyDescriptor(e,r).enumerable})),t.push.apply(t,n)}return t}function f(e){for(var a=1;a<arguments.length;a++){var t=arguments[a]!=null?arguments[a]:{};a%2?aa(Object(t),!0).forEach(function(n){g(e,n,t[n])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):aa(Object(t)).forEach(function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))})}return e}function de(e,a){return Ut(e)||Kt(e,a)||Ue(e,a)||Vt()}function E(e){return Bt(e)||Xt(e)||Ue(e)||Jt()}function qt(e,a){if(typeof e!="object"||!e)return e;var t=e[Symbol.toPrimitive];if(t!==void 0){var n=t.call(e,a);if(typeof n!="object")return n;throw new TypeError("@@toPrimitive must return a primitive value.")}return(a==="string"?String:Number)(e)}function Ma(e){var a=qt(e,"string");return typeof a=="symbol"?a:a+""}function le(e){"@babel/helpers - typeof";return le=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(a){return typeof a}:function(a){return a&&typeof Symbol=="function"&&a.constructor===Symbol&&a!==Symbol.prototype?"symbol":typeof a},le(e)}function Ue(e,a){if(e){if(typeof e=="string")return Ie(e,a);var t={}.toString.call(e).slice(8,-1);return t==="Object"&&e.constructor&&(t=e.constructor.name),t==="Map"||t==="Set"?Array.from(e):t==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t)?Ie(e,a):void 0}}var ta=function(){},Be={},La={},ja=null,Ta={mark:ta,measure:ta};try{typeof window<"u"&&(Be=window),typeof document<"u"&&(La=document),typeof MutationObserver<"u"&&(ja=MutationObserver),typeof performance<"u"&&(Ta=performance)}catch{}var Qt=Be.navigator||{},na=Qt.userAgent,ra=na===void 0?"":na,T=Be,x=La,ia=ja,ne=Ta;T.document;var j=!!x.documentElement&&!!x.head&&typeof x.addEventListener=="function"&&typeof x.createElement=="function",_a=~ra.indexOf("MSIE")||~ra.indexOf("Trident/"),ye,Zt=/fa(k|kd|s|r|l|t|d|dr|dl|dt|b|slr|slpr|wsb|tl|ns|nds|es|gt|jr|jfr|jdr|usb|ufsb|udsb|cr|ss|sr|sl|st|sds|sdr|sdl|sdt)?[\-\ ]/,en=/Font ?Awesome ?([567 ]*)(Solid|Regular|Light|Thin|Duotone|Brands|Free|Pro|Sharp Duotone|Sharp|Kit|Notdog Duo|Notdog|Chisel|Etch|Graphite|Thumbprint|Jelly Fill|Jelly Duo|Jelly|Utility|Utility Fill|Utility Duo|Slab Press|Slab|Whiteboard)?.*/i,$a={classic:{fa:"solid",fas:"solid","fa-solid":"solid",far:"regular","fa-regular":"regular",fal:"light","fa-light":"light",fat:"thin","fa-thin":"thin",fab:"brands","fa-brands":"brands"},duotone:{fa:"solid",fad:"solid","fa-solid":"solid","fa-duotone":"solid",fadr:"regular","fa-regular":"regular",fadl:"light","fa-light":"light",fadt:"thin","fa-thin":"thin"},sharp:{fa:"solid",fass:"solid","fa-solid":"solid",fasr:"regular","fa-regular":"regular",fasl:"light","fa-light":"light",fast:"thin","fa-thin":"thin"},"sharp-duotone":{fa:"solid",fasds:"solid","fa-solid":"solid",fasdr:"regular","fa-regular":"regular",fasdl:"light","fa-light":"light",fasdt:"thin","fa-thin":"thin"},slab:{"fa-regular":"regular",faslr:"regular"},"slab-press":{"fa-regular":"regular",faslpr:"regular"},thumbprint:{"fa-light":"light",fatl:"light"},whiteboard:{"fa-semibold":"semibold",fawsb:"semibold"},notdog:{"fa-solid":"solid",fans:"solid"},"notdog-duo":{"fa-solid":"solid",fands:"solid"},etch:{"fa-solid":"solid",faes:"solid"},graphite:{"fa-thin":"thin",fagt:"thin"},jelly:{"fa-regular":"regular",fajr:"regular"},"jelly-fill":{"fa-regular":"regular",fajfr:"regular"},"jelly-duo":{"fa-regular":"regular",fajdr:"regular"},chisel:{"fa-regular":"regular",facr:"regular"},utility:{"fa-semibold":"semibold",fausb:"semibold"},"utility-duo":{"fa-semibold":"semibold",faudsb:"semibold"},"utility-fill":{"fa-semibold":"semibold",faufsb:"semibold"}},an={GROUP:"duotone-group",PRIMARY:"primary",SECONDARY:"secondary"},Da=["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-utility","fa-utility-duo","fa-utility-fill"],k="classic",ee="duotone",Ra="sharp",Wa="sharp-duotone",Ua="chisel",Ba="etch",Ya="graphite",Ha="jelly",Ga="jelly-duo",Xa="jelly-fill",Ka="notdog",Va="notdog-duo",Ja="slab",qa="slab-press",Qa="thumbprint",Za="utility",et="utility-duo",at="utility-fill",tt="whiteboard",tn="Classic",nn="Duotone",rn="Sharp",on="Sharp Duotone",sn="Chisel",ln="Etch",fn="Graphite",cn="Jelly",un="Jelly Duo",dn="Jelly Fill",mn="Notdog",vn="Notdog Duo",hn="Slab",gn="Slab Press",pn="Thumbprint",yn="Utility",bn="Utility Duo",xn="Utility Fill",Sn="Whiteboard",nt=[k,ee,Ra,Wa,Ua,Ba,Ya,Ha,Ga,Xa,Ka,Va,Ja,qa,Qa,Za,et,at,tt];ye={},g(g(g(g(g(g(g(g(g(g(ye,k,tn),ee,nn),Ra,rn),Wa,on),Ua,sn),Ba,ln),Ya,fn),Ha,cn),Ga,un),Xa,dn),g(g(g(g(g(g(g(g(g(ye,Ka,mn),Va,vn),Ja,hn),qa,gn),Qa,pn),Za,yn),et,bn),at,xn),tt,Sn);var wn={classic:{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},duotone:{900:"fad",400:"fadr",300:"fadl",100:"fadt"},sharp:{900:"fass",400:"fasr",300:"fasl",100:"fast"},"sharp-duotone":{900:"fasds",400:"fasdr",300:"fasdl",100:"fasdt"},slab:{400:"faslr"},"slab-press":{400:"faslpr"},whiteboard:{600:"fawsb"},thumbprint:{300:"fatl"},notdog:{900:"fans"},"notdog-duo":{900:"fands"},etch:{900:"faes"},graphite:{100:"fagt"},chisel:{400:"facr"},jelly:{400:"fajr"},"jelly-fill":{400:"fajfr"},"jelly-duo":{400:"fajdr"},utility:{600:"fausb"},"utility-duo":{600:"faudsb"},"utility-fill":{600:"faufsb"}},An={"Font Awesome 7 Free":{900:"fas",400:"far"},"Font Awesome 7 Pro":{900:"fas",400:"far",normal:"far",300:"fal",100:"fat"},"Font Awesome 7 Brands":{400:"fab",normal:"fab"},"Font Awesome 7 Duotone":{900:"fad",400:"fadr",normal:"fadr",300:"fadl",100:"fadt"},"Font Awesome 7 Sharp":{900:"fass",400:"fasr",normal:"fasr",300:"fasl",100:"fast"},"Font Awesome 7 Sharp Duotone":{900:"fasds",400:"fasdr",normal:"fasdr",300:"fasdl",100:"fasdt"},"Font Awesome 7 Jelly":{400:"fajr",normal:"fajr"},"Font Awesome 7 Jelly Fill":{400:"fajfr",normal:"fajfr"},"Font Awesome 7 Jelly Duo":{400:"fajdr",normal:"fajdr"},"Font Awesome 7 Slab":{400:"faslr",normal:"faslr"},"Font Awesome 7 Slab Press":{400:"faslpr",normal:"faslpr"},"Font Awesome 7 Thumbprint":{300:"fatl",normal:"fatl"},"Font Awesome 7 Notdog":{900:"fans",normal:"fans"},"Font Awesome 7 Notdog Duo":{900:"fands",normal:"fands"},"Font Awesome 7 Etch":{900:"faes",normal:"faes"},"Font Awesome 7 Graphite":{100:"fagt",normal:"fagt"},"Font Awesome 7 Chisel":{400:"facr",normal:"facr"},"Font Awesome 7 Whiteboard":{600:"fawsb",normal:"fawsb"},"Font Awesome 7 Utility":{600:"fausb",normal:"fausb"},"Font Awesome 7 Utility Duo":{600:"faudsb",normal:"faudsb"},"Font Awesome 7 Utility Fill":{600:"faufsb",normal:"faufsb"}},kn=new Map([["classic",{defaultShortPrefixId:"fas",defaultStyleId:"solid",styleIds:["solid","regular","light","thin","brands"],futureStyleIds:[],defaultFontWeight:900}],["duotone",{defaultShortPrefixId:"fad",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp",{defaultShortPrefixId:"fass",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["sharp-duotone",{defaultShortPrefixId:"fasds",defaultStyleId:"solid",styleIds:["solid","regular","light","thin"],futureStyleIds:[],defaultFontWeight:900}],["chisel",{defaultShortPrefixId:"facr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["etch",{defaultShortPrefixId:"faes",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["graphite",{defaultShortPrefixId:"fagt",defaultStyleId:"thin",styleIds:["thin"],futureStyleIds:[],defaultFontWeight:100}],["jelly",{defaultShortPrefixId:"fajr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-duo",{defaultShortPrefixId:"fajdr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["jelly-fill",{defaultShortPrefixId:"fajfr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["notdog",{defaultShortPrefixId:"fans",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["notdog-duo",{defaultShortPrefixId:"fands",defaultStyleId:"solid",styleIds:["solid"],futureStyleIds:[],defaultFontWeight:900}],["slab",{defaultShortPrefixId:"faslr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["slab-press",{defaultShortPrefixId:"faslpr",defaultStyleId:"regular",styleIds:["regular"],futureStyleIds:[],defaultFontWeight:400}],["thumbprint",{defaultShortPrefixId:"fatl",defaultStyleId:"light",styleIds:["light"],futureStyleIds:[],defaultFontWeight:300}],["utility",{defaultShortPrefixId:"fausb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-duo",{defaultShortPrefixId:"faudsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["utility-fill",{defaultShortPrefixId:"faufsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}],["whiteboard",{defaultShortPrefixId:"fawsb",defaultStyleId:"semibold",styleIds:["semibold"],futureStyleIds:[],defaultFontWeight:600}]]),Pn={chisel:{regular:"facr"},classic:{brands:"fab",light:"fal",regular:"far",solid:"fas",thin:"fat"},duotone:{light:"fadl",regular:"fadr",solid:"fad",thin:"fadt"},etch:{solid:"faes"},graphite:{thin:"fagt"},jelly:{regular:"fajr"},"jelly-duo":{regular:"fajdr"},"jelly-fill":{regular:"fajfr"},notdog:{solid:"fans"},"notdog-duo":{solid:"fands"},sharp:{light:"fasl",regular:"fasr",solid:"fass",thin:"fast"},"sharp-duotone":{light:"fasdl",regular:"fasdr",solid:"fasds",thin:"fasdt"},slab:{regular:"faslr"},"slab-press":{regular:"faslpr"},thumbprint:{light:"fatl"},utility:{semibold:"fausb"},"utility-duo":{semibold:"faudsb"},"utility-fill":{semibold:"faufsb"},whiteboard:{semibold:"fawsb"}},rt=["fak","fa-kit","fakd","fa-kit-duotone"],oa={kit:{fak:"kit","fa-kit":"kit"},"kit-duotone":{fakd:"kit-duotone","fa-kit-duotone":"kit-duotone"}},In=["kit"],zn="kit",Cn="kit-duotone",On="Kit",En="Kit Duotone";g(g({},zn,On),Cn,En);var Nn={kit:{"fa-kit":"fak"}},Fn={"Font Awesome Kit":{400:"fak",normal:"fak"},"Font Awesome Kit Duotone":{400:"fakd",normal:"fakd"}},Mn={kit:{fak:"fa-kit"}},sa={kit:{kit:"fak"},"kit-duotone":{"kit-duotone":"fakd"}},be,re={GROUP:"duotone-group",SWAP_OPACITY:"swap-opacity",PRIMARY:"primary",SECONDARY:"secondary"},Ln=["fa-classic","fa-duotone","fa-sharp","fa-sharp-duotone","fa-thumbprint","fa-whiteboard","fa-notdog","fa-notdog-duo","fa-chisel","fa-etch","fa-graphite","fa-jelly","fa-jelly-fill","fa-jelly-duo","fa-slab","fa-slab-press","fa-utility","fa-utility-duo","fa-utility-fill"],jn="classic",Tn="duotone",_n="sharp",$n="sharp-duotone",Dn="chisel",Rn="etch",Wn="graphite",Un="jelly",Bn="jelly-duo",Yn="jelly-fill",Hn="notdog",Gn="notdog-duo",Xn="slab",Kn="slab-press",Vn="thumbprint",Jn="utility",qn="utility-duo",Qn="utility-fill",Zn="whiteboard",er="Classic",ar="Duotone",tr="Sharp",nr="Sharp Duotone",rr="Chisel",ir="Etch",or="Graphite",sr="Jelly",lr="Jelly Duo",fr="Jelly Fill",cr="Notdog",ur="Notdog Duo",dr="Slab",mr="Slab Press",vr="Thumbprint",hr="Utility",gr="Utility Duo",pr="Utility Fill",yr="Whiteboard";be={},g(g(g(g(g(g(g(g(g(g(be,jn,er),Tn,ar),_n,tr),$n,nr),Dn,rr),Rn,ir),Wn,or),Un,sr),Bn,lr),Yn,fr),g(g(g(g(g(g(g(g(g(be,Hn,cr),Gn,ur),Xn,dr),Kn,mr),Vn,vr),Jn,hr),qn,gr),Qn,pr),Zn,yr);var br="kit",xr="kit-duotone",Sr="Kit",wr="Kit Duotone";g(g({},br,Sr),xr,wr);var Ar={classic:{"fa-brands":"fab","fa-duotone":"fad","fa-light":"fal","fa-regular":"far","fa-solid":"fas","fa-thin":"fat"},duotone:{"fa-regular":"fadr","fa-light":"fadl","fa-thin":"fadt"},sharp:{"fa-solid":"fass","fa-regular":"fasr","fa-light":"fasl","fa-thin":"fast"},"sharp-duotone":{"fa-solid":"fasds","fa-regular":"fasdr","fa-light":"fasdl","fa-thin":"fasdt"},slab:{"fa-regular":"faslr"},"slab-press":{"fa-regular":"faslpr"},whiteboard:{"fa-semibold":"fawsb"},thumbprint:{"fa-light":"fatl"},notdog:{"fa-solid":"fans"},"notdog-duo":{"fa-solid":"fands"},etch:{"fa-solid":"faes"},graphite:{"fa-thin":"fagt"},jelly:{"fa-regular":"fajr"},"jelly-fill":{"fa-regular":"fajfr"},"jelly-duo":{"fa-regular":"fajdr"},chisel:{"fa-regular":"facr"},utility:{"fa-semibold":"fausb"},"utility-duo":{"fa-semibold":"faudsb"},"utility-fill":{"fa-semibold":"faufsb"}},kr={classic:["fas","far","fal","fat","fad"],duotone:["fadr","fadl","fadt"],sharp:["fass","fasr","fasl","fast"],"sharp-duotone":["fasds","fasdr","fasdl","fasdt"],slab:["faslr"],"slab-press":["faslpr"],whiteboard:["fawsb"],thumbprint:["fatl"],notdog:["fans"],"notdog-duo":["fands"],etch:["faes"],graphite:["fagt"],jelly:["fajr"],"jelly-fill":["fajfr"],"jelly-duo":["fajdr"],chisel:["facr"],utility:["fausb"],"utility-duo":["faudsb"],"utility-fill":["faufsb"]},ze={classic:{fab:"fa-brands",fad:"fa-duotone",fal:"fa-light",far:"fa-regular",fas:"fa-solid",fat:"fa-thin"},duotone:{fadr:"fa-regular",fadl:"fa-light",fadt:"fa-thin"},sharp:{fass:"fa-solid",fasr:"fa-regular",fasl:"fa-light",fast:"fa-thin"},"sharp-duotone":{fasds:"fa-solid",fasdr:"fa-regular",fasdl:"fa-light",fasdt:"fa-thin"},slab:{faslr:"fa-regular"},"slab-press":{faslpr:"fa-regular"},whiteboard:{fawsb:"fa-semibold"},thumbprint:{fatl:"fa-light"},notdog:{fans:"fa-solid"},"notdog-duo":{fands:"fa-solid"},etch:{faes:"fa-solid"},graphite:{fagt:"fa-thin"},jelly:{fajr:"fa-regular"},"jelly-fill":{fajfr:"fa-regular"},"jelly-duo":{fajdr:"fa-regular"},chisel:{facr:"fa-regular"},utility:{fausb:"fa-semibold"},"utility-duo":{faudsb:"fa-semibold"},"utility-fill":{faufsb:"fa-semibold"}},Pr=["fa-solid","fa-regular","fa-light","fa-thin","fa-duotone","fa-brands","fa-semibold"],it=["fa","fas","far","fal","fat","fad","fadr","fadl","fadt","fab","fass","fasr","fasl","fast","fasds","fasdr","fasdl","fasdt","faslr","faslpr","fawsb","fatl","fans","fands","faes","fagt","fajr","fajfr","fajdr","facr","fausb","faudsb","faufsb"].concat(Ln,Pr),Ir=["solid","regular","light","thin","duotone","brands","semibold"],ot=[1,2,3,4,5,6,7,8,9,10],zr=ot.concat([11,12,13,14,15,16,17,18,19,20]),Cr=["aw","fw","pull-left","pull-right"],Or=[].concat(E(Object.keys(kr)),Ir,Cr,["2xs","xs","sm","lg","xl","2xl","beat","border","fade","beat-fade","bounce","flip-both","flip-horizontal","flip-vertical","flip","inverse","layers","layers-bottom-left","layers-bottom-right","layers-counter","layers-text","layers-top-left","layers-top-right","li","pull-end","pull-start","pulse","rotate-180","rotate-270","rotate-90","rotate-by","shake","spin-pulse","spin-reverse","spin","stack-1x","stack-2x","stack","ul","width-auto","width-fixed",re.GROUP,re.SWAP_OPACITY,re.PRIMARY,re.SECONDARY]).concat(ot.map(function(e){return"".concat(e,"x")})).concat(zr.map(function(e){return"w-".concat(e)})),Er={"Font Awesome 5 Free":{900:"fas",400:"far"},"Font Awesome 5 Pro":{900:"fas",400:"far",normal:"far",300:"fal"},"Font Awesome 5 Brands":{400:"fab",normal:"fab"},"Font Awesome 5 Duotone":{900:"fad"}},M="___FONT_AWESOME___",Ce=16,st="fa",lt="svg-inline--fa",R="data-fa-i2svg",Oe="data-fa-pseudo-element",Nr="data-fa-pseudo-element-pending",Ye="data-prefix",He="data-icon",la="fontawesome-i2svg",Fr="async",Mr=["HTML","HEAD","STYLE","SCRIPT"],ft=["::before","::after",":before",":after"],ct=(function(){try{return!1}catch{return!1}})();function ae(e){return new Proxy(e,{get:function(t,n){return n in t?t[n]:t[k]}})}var ut=f({},$a);ut[k]=f(f(f(f({},{"fa-duotone":"duotone"}),$a[k]),oa.kit),oa["kit-duotone"]);var Lr=ae(ut),Ee=f({},Pn);Ee[k]=f(f(f(f({},{duotone:"fad"}),Ee[k]),sa.kit),sa["kit-duotone"]);var fa=ae(Ee),Ne=f({},ze);Ne[k]=f(f({},Ne[k]),Mn.kit);var Ge=ae(Ne),Fe=f({},Ar);Fe[k]=f(f({},Fe[k]),Nn.kit);ae(Fe);var jr=Zt,dt="fa-layers-text",Tr=en,_r=f({},wn);ae(_r);var $r=["class","data-prefix","data-icon","data-fa-transform","data-fa-mask"],xe=an,Dr=[].concat(E(In),E(Or)),q=T.FontAwesomeConfig||{};function Rr(e){var a=x.querySelector("script["+e+"]");if(a)return a.getAttribute(e)}function Wr(e){return e===""?!0:e==="false"?!1:e==="true"?!0:e}if(x&&typeof x.querySelector=="function"){var Ur=[["data-family-prefix","familyPrefix"],["data-css-prefix","cssPrefix"],["data-family-default","familyDefault"],["data-style-default","styleDefault"],["data-replacement-class","replacementClass"],["data-auto-replace-svg","autoReplaceSvg"],["data-auto-add-css","autoAddCss"],["data-search-pseudo-elements","searchPseudoElements"],["data-search-pseudo-elements-warnings","searchPseudoElementsWarnings"],["data-search-pseudo-elements-full-scan","searchPseudoElementsFullScan"],["data-observe-mutations","observeMutations"],["data-mutate-approach","mutateApproach"],["data-keep-original-source","keepOriginalSource"],["data-measure-performance","measurePerformance"],["data-show-missing-icons","showMissingIcons"]];Ur.forEach(function(e){var a=de(e,2),t=a[0],n=a[1],r=Wr(Rr(t));r!=null&&(q[n]=r)})}var mt={styleDefault:"solid",familyDefault:k,cssPrefix:st,replacementClass:lt,autoReplaceSvg:!0,autoAddCss:!0,searchPseudoElements:!1,searchPseudoElementsWarnings:!0,searchPseudoElementsFullScan:!1,observeMutations:!0,mutateApproach:"async",keepOriginalSource:!0,measurePerformance:!1,showMissingIcons:!0};q.familyPrefix&&(q.cssPrefix=q.familyPrefix);var X=f(f({},mt),q);X.autoReplaceSvg||(X.observeMutations=!1);var v={};Object.keys(mt).forEach(function(e){Object.defineProperty(v,e,{enumerable:!0,set:function(t){X[e]=t,Q.forEach(function(n){return n(v)})},get:function(){return X[e]}})});Object.defineProperty(v,"familyPrefix",{enumerable:!0,set:function(a){X.cssPrefix=a,Q.forEach(function(t){return t(v)})},get:function(){return X.cssPrefix}});T.FontAwesomeConfig=v;var Q=[];function Br(e){return Q.push(e),function(){Q.splice(Q.indexOf(e),1)}}var Y=Ce,N={size:16,x:0,y:0,rotate:0,flipX:!1,flipY:!1};function Yr(e){if(!(!e||!j)){var a=x.createElement("style");a.setAttribute("type","text/css"),a.innerHTML=e;for(var t=x.head.childNodes,n=null,r=t.length-1;r>-1;r--){var i=t[r],o=(i.tagName||"").toUpperCase();["STYLE","LINK"].indexOf(o)>-1&&(n=i)}return x.head.insertBefore(a,n),e}}var Hr="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";function ca(){for(var e=12,a="";e-- >0;)a+=Hr[Math.random()*62|0];return a}function K(e){for(var a=[],t=(e||[]).length>>>0;t--;)a[t]=e[t];return a}function Xe(e){return e.classList?K(e.classList):(e.getAttribute("class")||"").split(" ").filter(function(a){return a})}function vt(e){return"".concat(e).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function Gr(e){return Object.keys(e||{}).reduce(function(a,t){return a+"".concat(t,'="').concat(vt(e[t]),'" ')},"").trim()}function me(e){return Object.keys(e||{}).reduce(function(a,t){return a+"".concat(t,": ").concat(e[t].trim(),";")},"")}function Ke(e){return e.size!==N.size||e.x!==N.x||e.y!==N.y||e.rotate!==N.rotate||e.flipX||e.flipY}function Xr(e){var a=e.transform,t=e.containerWidth,n=e.iconWidth,r={transform:"translate(".concat(t/2," 256)")},i="translate(".concat(a.x*32,", ").concat(a.y*32,") "),o="scale(".concat(a.size/16*(a.flipX?-1:1),", ").concat(a.size/16*(a.flipY?-1:1),") "),s="rotate(".concat(a.rotate," 0 0)"),l={transform:"".concat(i," ").concat(o," ").concat(s)},c={transform:"translate(".concat(n/2*-1," -256)")};return{outer:r,inner:l,path:c}}function Kr(e){var a=e.transform,t=e.width,n=t===void 0?Ce:t,r=e.height,i=r===void 0?Ce:r,o="";return _a?o+="translate(".concat(a.x/Y-n/2,"em, ").concat(a.y/Y-i/2,"em) "):o+="translate(calc(-50% + ".concat(a.x/Y,"em), calc(-50% + ").concat(a.y/Y,"em)) "),o+="scale(".concat(a.size/Y*(a.flipX?-1:1),", ").concat(a.size/Y*(a.flipY?-1:1),") "),o+="rotate(".concat(a.rotate,"deg) "),o}var Vr=`:root, :host {
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
}`;function ht(){var e=st,a=lt,t=v.cssPrefix,n=v.replacementClass,r=Vr;if(t!==e||n!==a){var i=new RegExp("\\.".concat(e,"\\-"),"g"),o=new RegExp("\\--".concat(e,"\\-"),"g"),s=new RegExp("\\.".concat(a),"g");r=r.replace(i,".".concat(t,"-")).replace(o,"--".concat(t,"-")).replace(s,".".concat(n))}return r}var ua=!1;function Se(){v.autoAddCss&&!ua&&(Yr(ht()),ua=!0)}var Jr={mixout:function(){return{dom:{css:ht,insertCss:Se}}},hooks:function(){return{beforeDOMElementCreation:function(){Se()},beforeI2svg:function(){Se()}}}},L=T||{};L[M]||(L[M]={});L[M].styles||(L[M].styles={});L[M].hooks||(L[M].hooks={});L[M].shims||(L[M].shims=[]);var O=L[M],gt=[],pt=function(){x.removeEventListener("DOMContentLoaded",pt),fe=1,gt.map(function(a){return a()})},fe=!1;j&&(fe=(x.documentElement.doScroll?/^loaded|^c/:/^loaded|^i|^c/).test(x.readyState),fe||x.addEventListener("DOMContentLoaded",pt));function qr(e){j&&(fe?setTimeout(e,0):gt.push(e))}function te(e){var a=e.tag,t=e.attributes,n=t===void 0?{}:t,r=e.children,i=r===void 0?[]:r;return typeof e=="string"?vt(e):"<".concat(a," ").concat(Gr(n),">").concat(i.map(te).join(""),"</").concat(a,">")}function da(e,a,t){if(e&&e[a]&&e[a][t])return{prefix:a,iconName:t,icon:e[a][t]}}var we=function(a,t,n,r){var i=Object.keys(a),o=i.length,s=t,l,c,u;for(n===void 0?(l=1,u=a[i[0]]):(l=0,u=n);l<o;l++)c=i[l],u=s(u,a[c],c,a);return u};function yt(e){return E(e).length!==1?null:e.codePointAt(0).toString(16)}function ma(e){return Object.keys(e).reduce(function(a,t){var n=e[t],r=!!n.icon;return r?a[n.iconName]=n.icon:a[t]=n,a},{})}function Me(e,a){var t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{},n=t.skipHooks,r=n===void 0?!1:n,i=ma(a);typeof O.hooks.addPack=="function"&&!r?O.hooks.addPack(e,ma(a)):O.styles[e]=f(f({},O.styles[e]||{}),i),e==="fas"&&Me("fa",a)}var Z=O.styles,Qr=O.shims,bt=Object.keys(Ge),Zr=bt.reduce(function(e,a){return e[a]=Object.keys(Ge[a]),e},{}),Ve=null,xt={},St={},wt={},At={},kt={};function ei(e){return~Dr.indexOf(e)}function ai(e,a){var t=a.split("-"),n=t[0],r=t.slice(1).join("-");return n===e&&r!==""&&!ei(r)?r:null}var Pt=function(){var a=function(i){return we(Z,function(o,s,l){return o[l]=we(s,i,{}),o},{})};xt=a(function(r,i,o){if(i[3]&&(r[i[3]]=o),i[2]){var s=i[2].filter(function(l){return typeof l=="number"});s.forEach(function(l){r[l.toString(16)]=o})}return r}),St=a(function(r,i,o){if(r[o]=o,i[2]){var s=i[2].filter(function(l){return typeof l=="string"});s.forEach(function(l){r[l]=o})}return r}),kt=a(function(r,i,o){var s=i[2];return r[o]=o,s.forEach(function(l){r[l]=o}),r});var t="far"in Z||v.autoFetchSvg,n=we(Qr,function(r,i){var o=i[0],s=i[1],l=i[2];return s==="far"&&!t&&(s="fas"),typeof o=="string"&&(r.names[o]={prefix:s,iconName:l}),typeof o=="number"&&(r.unicodes[o.toString(16)]={prefix:s,iconName:l}),r},{names:{},unicodes:{}});wt=n.names,At=n.unicodes,Ve=ve(v.styleDefault,{family:v.familyDefault})};Br(function(e){Ve=ve(e.styleDefault,{family:v.familyDefault})});Pt();function Je(e,a){return(xt[e]||{})[a]}function ti(e,a){return(St[e]||{})[a]}function D(e,a){return(kt[e]||{})[a]}function It(e){return wt[e]||{prefix:null,iconName:null}}function ni(e){var a=At[e],t=Je("fas",e);return a||(t?{prefix:"fas",iconName:t}:null)||{prefix:null,iconName:null}}function _(){return Ve}var zt=function(){return{prefix:null,iconName:null,rest:[]}};function ri(e){var a=k,t=bt.reduce(function(n,r){return n[r]="".concat(v.cssPrefix,"-").concat(r),n},{});return nt.forEach(function(n){(e.includes(t[n])||e.some(function(r){return Zr[n].includes(r)}))&&(a=n)}),a}function ve(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=a.family,n=t===void 0?k:t,r=Lr[n][e];if(n===ee&&!e)return"fad";var i=fa[n][e]||fa[n][r],o=e in O.styles?e:null,s=i||o||null;return s}function ii(e){var a=[],t=null;return e.forEach(function(n){var r=ai(v.cssPrefix,n);r?t=r:n&&a.push(n)}),{iconName:t,rest:a}}function va(e){return e.sort().filter(function(a,t,n){return n.indexOf(a)===t})}var ha=it.concat(rt);function he(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=a.skipLookups,n=t===void 0?!1:t,r=null,i=va(e.filter(function(p){return ha.includes(p)})),o=va(e.filter(function(p){return!ha.includes(p)})),s=i.filter(function(p){return r=p,!Da.includes(p)}),l=de(s,1),c=l[0],u=c===void 0?null:c,m=ri(i),y=f(f({},ii(o)),{},{prefix:ve(u,{family:m})});return f(f(f({},y),fi({values:e,family:m,styles:Z,config:v,canonical:y,givenPrefix:r})),oi(n,r,y))}function oi(e,a,t){var n=t.prefix,r=t.iconName;if(e||!n||!r)return{prefix:n,iconName:r};var i=a==="fa"?It(r):{},o=D(n,r);return r=i.iconName||o||r,n=i.prefix||n,n==="far"&&!Z.far&&Z.fas&&!v.autoFetchSvg&&(n="fas"),{prefix:n,iconName:r}}var si=nt.filter(function(e){return e!==k||e!==ee}),li=Object.keys(ze).filter(function(e){return e!==k}).map(function(e){return Object.keys(ze[e])}).flat();function fi(e){var a=e.values,t=e.family,n=e.canonical,r=e.givenPrefix,i=r===void 0?"":r,o=e.styles,s=o===void 0?{}:o,l=e.config,c=l===void 0?{}:l,u=t===ee,m=a.includes("fa-duotone")||a.includes("fad"),y=c.familyDefault==="duotone",p=n.prefix==="fad"||n.prefix==="fa-duotone";if(!u&&(m||y||p)&&(n.prefix="fad"),(a.includes("fa-brands")||a.includes("fab"))&&(n.prefix="fab"),!n.prefix&&si.includes(t)){var w=Object.keys(s).find(function(A){return li.includes(A)});if(w||c.autoFetchSvg){var b=kn.get(t).defaultShortPrefixId;n.prefix=b,n.iconName=D(n.prefix,n.iconName)||n.iconName}}return(n.prefix==="fa"||i==="fa")&&(n.prefix=_()||"fas"),n}var ci=(function(){function e(){Yt(this,e),this.definitions={}}return Gt(e,[{key:"add",value:function(){for(var t=this,n=arguments.length,r=new Array(n),i=0;i<n;i++)r[i]=arguments[i];var o=r.reduce(this._pullDefinitions,{});Object.keys(o).forEach(function(s){t.definitions[s]=f(f({},t.definitions[s]||{}),o[s]),Me(s,o[s]);var l=Ge[k][s];l&&Me(l,o[s]),Pt()})}},{key:"reset",value:function(){this.definitions={}}},{key:"_pullDefinitions",value:function(t,n){var r=n.prefix&&n.iconName&&n.icon?{0:n}:n;return Object.keys(r).map(function(i){var o=r[i],s=o.prefix,l=o.iconName,c=o.icon,u=c[2];t[s]||(t[s]={}),u.length>0&&u.forEach(function(m){typeof m=="string"&&(t[s][m]=c)}),t[s][l]=c}),t}}])})(),ga=[],H={},G={},ui=Object.keys(G);function di(e,a){var t=a.mixoutsTo;return ga=e,H={},Object.keys(G).forEach(function(n){ui.indexOf(n)===-1&&delete G[n]}),ga.forEach(function(n){var r=n.mixout?n.mixout():{};if(Object.keys(r).forEach(function(o){typeof r[o]=="function"&&(t[o]=r[o]),le(r[o])==="object"&&Object.keys(r[o]).forEach(function(s){t[o]||(t[o]={}),t[o][s]=r[o][s]})}),n.hooks){var i=n.hooks();Object.keys(i).forEach(function(o){H[o]||(H[o]=[]),H[o].push(i[o])})}n.provides&&n.provides(G)}),t}function Le(e,a){for(var t=arguments.length,n=new Array(t>2?t-2:0),r=2;r<t;r++)n[r-2]=arguments[r];var i=H[e]||[];return i.forEach(function(o){a=o.apply(null,[a].concat(n))}),a}function W(e){for(var a=arguments.length,t=new Array(a>1?a-1:0),n=1;n<a;n++)t[n-1]=arguments[n];var r=H[e]||[];r.forEach(function(i){i.apply(null,t)})}function $(){var e=arguments[0],a=Array.prototype.slice.call(arguments,1);return G[e]?G[e].apply(null,a):void 0}function je(e){e.prefix==="fa"&&(e.prefix="fas");var a=e.iconName,t=e.prefix||_();if(a)return a=D(t,a)||a,da(Ct.definitions,t,a)||da(O.styles,t,a)}var Ct=new ci,mi=function(){v.autoReplaceSvg=!1,v.observeMutations=!1,W("noAuto")},vi={i2svg:function(){var a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return j?(W("beforeI2svg",a),$("pseudoElements2svg",a),$("i2svg",a)):Promise.reject(new Error("Operation requires a DOM of some kind."))},watch:function(){var a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},t=a.autoReplaceSvgRoot;v.autoReplaceSvg===!1&&(v.autoReplaceSvg=!0),v.observeMutations=!0,qr(function(){gi({autoReplaceSvgRoot:t}),W("watch",a)})}},hi={icon:function(a){if(a===null)return null;if(le(a)==="object"&&a.prefix&&a.iconName)return{prefix:a.prefix,iconName:D(a.prefix,a.iconName)||a.iconName};if(Array.isArray(a)&&a.length===2){var t=a[1].indexOf("fa-")===0?a[1].slice(3):a[1],n=ve(a[0]);return{prefix:n,iconName:D(n,t)||t}}if(typeof a=="string"&&(a.indexOf("".concat(v.cssPrefix,"-"))>-1||a.match(jr))){var r=he(a.split(" "),{skipLookups:!0});return{prefix:r.prefix||_(),iconName:D(r.prefix,r.iconName)||r.iconName}}if(typeof a=="string"){var i=_();return{prefix:i,iconName:D(i,a)||a}}}},C={noAuto:mi,config:v,dom:vi,parse:hi,library:Ct,findIconDefinition:je,toHtml:te},gi=function(){var a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},t=a.autoReplaceSvgRoot,n=t===void 0?x:t;(Object.keys(O.styles).length>0||v.autoFetchSvg)&&j&&v.autoReplaceSvg&&C.dom.i2svg({node:n})};function ge(e,a){return Object.defineProperty(e,"abstract",{get:a}),Object.defineProperty(e,"html",{get:function(){return e.abstract.map(function(n){return te(n)})}}),Object.defineProperty(e,"node",{get:function(){if(j){var n=x.createElement("div");return n.innerHTML=e.html,n.children}}}),e}function pi(e){var a=e.children,t=e.main,n=e.mask,r=e.attributes,i=e.styles,o=e.transform;if(Ke(o)&&t.found&&!n.found){var s=t.width,l=t.height,c={x:s/l/2,y:.5};r.style=me(f(f({},i),{},{"transform-origin":"".concat(c.x+o.x/16,"em ").concat(c.y+o.y/16,"em")}))}return[{tag:"svg",attributes:r,children:a}]}function yi(e){var a=e.prefix,t=e.iconName,n=e.children,r=e.attributes,i=e.symbol,o=i===!0?"".concat(a,"-").concat(v.cssPrefix,"-").concat(t):i;return[{tag:"svg",attributes:{style:"display: none;"},children:[{tag:"symbol",attributes:f(f({},r),{},{id:o}),children:n}]}]}function bi(e){var a=["aria-label","aria-labelledby","title","role"];return a.some(function(t){return t in e})}function qe(e){var a=e.icons,t=a.main,n=a.mask,r=e.prefix,i=e.iconName,o=e.transform,s=e.symbol,l=e.maskId,c=e.extra,u=e.watchable,m=u===void 0?!1:u,y=n.found?n:t,p=y.width,w=y.height,b=[v.replacementClass,i?"".concat(v.cssPrefix,"-").concat(i):""].filter(function(z){return c.classes.indexOf(z)===-1}).filter(function(z){return z!==""||!!z}).concat(c.classes).join(" "),A={children:[],attributes:f(f({},c.attributes),{},{"data-prefix":r,"data-icon":i,class:b,role:c.attributes.role||"img",viewBox:"0 0 ".concat(p," ").concat(w)})};!bi(c.attributes)&&!c.attributes["aria-hidden"]&&(A.attributes["aria-hidden"]="true"),m&&(A.attributes[R]="");var d=f(f({},A),{},{prefix:r,iconName:i,main:t,mask:n,maskId:l,transform:o,symbol:s,styles:f({},c.styles)}),h=n.found&&t.found?$("generateAbstractMask",d)||{children:[],attributes:{}}:$("generateAbstractIcon",d)||{children:[],attributes:{}},S=h.children,P=h.attributes;return d.children=S,d.attributes=P,s?yi(d):pi(d)}function pa(e){var a=e.content,t=e.width,n=e.height,r=e.transform,i=e.extra,o=e.watchable,s=o===void 0?!1:o,l=f(f({},i.attributes),{},{class:i.classes.join(" ")});s&&(l[R]="");var c=f({},i.styles);Ke(r)&&(c.transform=Kr({transform:r,width:t,height:n}),c["-webkit-transform"]=c.transform);var u=me(c);u.length>0&&(l.style=u);var m=[];return m.push({tag:"span",attributes:l,children:[a]}),m}function xi(e){var a=e.content,t=e.extra,n=f(f({},t.attributes),{},{class:t.classes.join(" ")}),r=me(t.styles);r.length>0&&(n.style=r);var i=[];return i.push({tag:"span",attributes:n,children:[a]}),i}var Ae=O.styles;function Te(e){var a=e[0],t=e[1],n=e.slice(4),r=de(n,1),i=r[0],o=null;return Array.isArray(i)?o={tag:"g",attributes:{class:"".concat(v.cssPrefix,"-").concat(xe.GROUP)},children:[{tag:"path",attributes:{class:"".concat(v.cssPrefix,"-").concat(xe.SECONDARY),fill:"currentColor",d:i[0]}},{tag:"path",attributes:{class:"".concat(v.cssPrefix,"-").concat(xe.PRIMARY),fill:"currentColor",d:i[1]}}]}:o={tag:"path",attributes:{fill:"currentColor",d:i}},{found:!0,width:a,height:t,icon:o}}var Si={found:!1,width:512,height:512};function wi(e,a){!ct&&!v.showMissingIcons&&e&&console.error('Icon with name "'.concat(e,'" and prefix "').concat(a,'" is missing.'))}function _e(e,a){var t=a;return a==="fa"&&v.styleDefault!==null&&(a=_()),new Promise(function(n,r){if(t==="fa"){var i=It(e)||{};e=i.iconName||e,a=i.prefix||a}if(e&&a&&Ae[a]&&Ae[a][e]){var o=Ae[a][e];return n(Te(o))}wi(e,a),n(f(f({},Si),{},{icon:v.showMissingIcons&&e?$("missingIconAbstract")||{}:{}}))})}var ya=function(){},$e=v.measurePerformance&&ne&&ne.mark&&ne.measure?ne:{mark:ya,measure:ya},J='FA "7.2.0"',Ai=function(a){return $e.mark("".concat(J," ").concat(a," begins")),function(){return Ot(a)}},Ot=function(a){$e.mark("".concat(J," ").concat(a," ends")),$e.measure("".concat(J," ").concat(a),"".concat(J," ").concat(a," begins"),"".concat(J," ").concat(a," ends"))},Qe={begin:Ai,end:Ot},oe=function(){};function ba(e){var a=e.getAttribute?e.getAttribute(R):null;return typeof a=="string"}function ki(e){var a=e.getAttribute?e.getAttribute(Ye):null,t=e.getAttribute?e.getAttribute(He):null;return a&&t}function Pi(e){return e&&e.classList&&e.classList.contains&&e.classList.contains(v.replacementClass)}function Ii(){if(v.autoReplaceSvg===!0)return se.replace;var e=se[v.autoReplaceSvg];return e||se.replace}function zi(e){return x.createElementNS("http://www.w3.org/2000/svg",e)}function Ci(e){return x.createElement(e)}function Et(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=a.ceFn,n=t===void 0?e.tag==="svg"?zi:Ci:t;if(typeof e=="string")return x.createTextNode(e);var r=n(e.tag);Object.keys(e.attributes||[]).forEach(function(o){r.setAttribute(o,e.attributes[o])});var i=e.children||[];return i.forEach(function(o){r.appendChild(Et(o,{ceFn:n}))}),r}function Oi(e){var a=" ".concat(e.outerHTML," ");return a="".concat(a,"Font Awesome fontawesome.com "),a}var se={replace:function(a){var t=a[0];if(t.parentNode)if(a[1].forEach(function(r){t.parentNode.insertBefore(Et(r),t)}),t.getAttribute(R)===null&&v.keepOriginalSource){var n=x.createComment(Oi(t));t.parentNode.replaceChild(n,t)}else t.remove()},nest:function(a){var t=a[0],n=a[1];if(~Xe(t).indexOf(v.replacementClass))return se.replace(a);var r=new RegExp("".concat(v.cssPrefix,"-.*"));if(delete n[0].attributes.id,n[0].attributes.class){var i=n[0].attributes.class.split(" ").reduce(function(s,l){return l===v.replacementClass||l.match(r)?s.toSvg.push(l):s.toNode.push(l),s},{toNode:[],toSvg:[]});n[0].attributes.class=i.toSvg.join(" "),i.toNode.length===0?t.removeAttribute("class"):t.setAttribute("class",i.toNode.join(" "))}var o=n.map(function(s){return te(s)}).join(`
`);t.setAttribute(R,""),t.innerHTML=o}};function xa(e){e()}function Nt(e,a){var t=typeof a=="function"?a:oe;if(e.length===0)t();else{var n=xa;v.mutateApproach===Fr&&(n=T.requestAnimationFrame||xa),n(function(){var r=Ii(),i=Qe.begin("mutate");e.map(r),i(),t()})}}var Ze=!1;function Ft(){Ze=!0}function De(){Ze=!1}var ce=null;function Sa(e){if(ia&&v.observeMutations){var a=e.treeCallback,t=a===void 0?oe:a,n=e.nodeCallback,r=n===void 0?oe:n,i=e.pseudoElementsCallback,o=i===void 0?oe:i,s=e.observeMutationsRoot,l=s===void 0?x:s;ce=new ia(function(c){if(!Ze){var u=_();K(c).forEach(function(m){if(m.type==="childList"&&m.addedNodes.length>0&&!ba(m.addedNodes[0])&&(v.searchPseudoElements&&o(m.target),t(m.target)),m.type==="attributes"&&m.target.parentNode&&v.searchPseudoElements&&o([m.target],!0),m.type==="attributes"&&ba(m.target)&&~$r.indexOf(m.attributeName))if(m.attributeName==="class"&&ki(m.target)){var y=he(Xe(m.target)),p=y.prefix,w=y.iconName;m.target.setAttribute(Ye,p||u),w&&m.target.setAttribute(He,w)}else Pi(m.target)&&r(m.target)})}}),j&&ce.observe(l,{childList:!0,attributes:!0,characterData:!0,subtree:!0})}}function Ei(){ce&&ce.disconnect()}function Ni(e){var a=e.getAttribute("style"),t=[];return a&&(t=a.split(";").reduce(function(n,r){var i=r.split(":"),o=i[0],s=i.slice(1);return o&&s.length>0&&(n[o]=s.join(":").trim()),n},{})),t}function Fi(e){var a=e.getAttribute("data-prefix"),t=e.getAttribute("data-icon"),n=e.innerText!==void 0?e.innerText.trim():"",r=he(Xe(e));return r.prefix||(r.prefix=_()),a&&t&&(r.prefix=a,r.iconName=t),r.iconName&&r.prefix||(r.prefix&&n.length>0&&(r.iconName=ti(r.prefix,e.innerText)||Je(r.prefix,yt(e.innerText))),!r.iconName&&v.autoFetchSvg&&e.firstChild&&e.firstChild.nodeType===Node.TEXT_NODE&&(r.iconName=e.firstChild.data)),r}function Mi(e){var a=K(e.attributes).reduce(function(t,n){return t.name!=="class"&&t.name!=="style"&&(t[n.name]=n.value),t},{});return a}function Li(){return{iconName:null,prefix:null,transform:N,symbol:!1,mask:{iconName:null,prefix:null,rest:[]},maskId:null,extra:{classes:[],styles:{},attributes:{}}}}function wa(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{styleParser:!0},t=Fi(e),n=t.iconName,r=t.prefix,i=t.rest,o=Mi(e),s=Le("parseNodeAttributes",{},e),l=a.styleParser?Ni(e):[];return f({iconName:n,prefix:r,transform:N,mask:{iconName:null,prefix:null,rest:[]},maskId:null,symbol:!1,extra:{classes:i,styles:l,attributes:o}},s)}var ji=O.styles;function Mt(e){var a=v.autoReplaceSvg==="nest"?wa(e,{styleParser:!1}):wa(e);return~a.extra.classes.indexOf(dt)?$("generateLayersText",e,a):$("generateSvgReplacementMutation",e,a)}function Ti(){return[].concat(E(rt),E(it))}function Aa(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;if(!j)return Promise.resolve();var t=x.documentElement.classList,n=function(m){return t.add("".concat(la,"-").concat(m))},r=function(m){return t.remove("".concat(la,"-").concat(m))},i=v.autoFetchSvg?Ti():Da.concat(Object.keys(ji));i.includes("fa")||i.push("fa");var o=[".".concat(dt,":not([").concat(R,"])")].concat(i.map(function(u){return".".concat(u,":not([").concat(R,"])")})).join(", ");if(o.length===0)return Promise.resolve();var s=[];try{s=K(e.querySelectorAll(o))}catch{}if(s.length>0)n("pending"),r("complete");else return Promise.resolve();var l=Qe.begin("onTree"),c=s.reduce(function(u,m){try{var y=Mt(m);y&&u.push(y)}catch(p){ct||p.name==="MissingIcon"&&console.error(p)}return u},[]);return new Promise(function(u,m){Promise.all(c).then(function(y){Nt(y,function(){n("active"),n("complete"),r("pending"),typeof a=="function"&&a(),l(),u()})}).catch(function(y){l(),m(y)})})}function _i(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:null;Mt(e).then(function(t){t&&Nt([t],a)})}function $i(e){return function(a){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=(a||{}).icon?a:je(a||{}),r=t.mask;return r&&(r=(r||{}).icon?r:je(r||{})),e(n,f(f({},t),{},{mask:r}))}}var Di=function(a){var t=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},n=t.transform,r=n===void 0?N:n,i=t.symbol,o=i===void 0?!1:i,s=t.mask,l=s===void 0?null:s,c=t.maskId,u=c===void 0?null:c,m=t.classes,y=m===void 0?[]:m,p=t.attributes,w=p===void 0?{}:p,b=t.styles,A=b===void 0?{}:b;if(a){var d=a.prefix,h=a.iconName,S=a.icon;return ge(f({type:"icon"},a),function(){return W("beforeDOMElementCreation",{iconDefinition:a,params:t}),qe({icons:{main:Te(S),mask:l?Te(l.icon):{found:!1,width:null,height:null,icon:{}}},prefix:d,iconName:h,transform:f(f({},N),r),symbol:o,maskId:u,extra:{attributes:w,styles:A,classes:y}})})}},Ri={mixout:function(){return{icon:$i(Di)}},hooks:function(){return{mutationObserverCallbacks:function(t){return t.treeCallback=Aa,t.nodeCallback=_i,t}}},provides:function(a){a.i2svg=function(t){var n=t.node,r=n===void 0?x:n,i=t.callback,o=i===void 0?function(){}:i;return Aa(r,o)},a.generateSvgReplacementMutation=function(t,n){var r=n.iconName,i=n.prefix,o=n.transform,s=n.symbol,l=n.mask,c=n.maskId,u=n.extra;return new Promise(function(m,y){Promise.all([_e(r,i),l.iconName?_e(l.iconName,l.prefix):Promise.resolve({found:!1,width:512,height:512,icon:{}})]).then(function(p){var w=de(p,2),b=w[0],A=w[1];m([t,qe({icons:{main:b,mask:A},prefix:i,iconName:r,transform:o,symbol:s,maskId:c,extra:u,watchable:!0})])}).catch(y)})},a.generateAbstractIcon=function(t){var n=t.children,r=t.attributes,i=t.main,o=t.transform,s=t.styles,l=me(s);l.length>0&&(r.style=l);var c;return Ke(o)&&(c=$("generateAbstractTransformGrouping",{main:i,transform:o,containerWidth:i.width,iconWidth:i.width})),n.push(c||i.icon),{children:n,attributes:r}}}},Wi={mixout:function(){return{layer:function(t){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=n.classes,i=r===void 0?[]:r;return ge({type:"layer"},function(){W("beforeDOMElementCreation",{assembler:t,params:n});var o=[];return t(function(s){Array.isArray(s)?s.map(function(l){o=o.concat(l.abstract)}):o=o.concat(s.abstract)}),[{tag:"span",attributes:{class:["".concat(v.cssPrefix,"-layers")].concat(E(i)).join(" ")},children:o}]})}}}},Ui={mixout:function(){return{counter:function(t){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};n.title;var r=n.classes,i=r===void 0?[]:r,o=n.attributes,s=o===void 0?{}:o,l=n.styles,c=l===void 0?{}:l;return ge({type:"counter",content:t},function(){return W("beforeDOMElementCreation",{content:t,params:n}),xi({content:t.toString(),extra:{attributes:s,styles:c,classes:["".concat(v.cssPrefix,"-layers-counter")].concat(E(i))}})})}}}},Bi={mixout:function(){return{text:function(t){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},r=n.transform,i=r===void 0?N:r,o=n.classes,s=o===void 0?[]:o,l=n.attributes,c=l===void 0?{}:l,u=n.styles,m=u===void 0?{}:u;return ge({type:"text",content:t},function(){return W("beforeDOMElementCreation",{content:t,params:n}),pa({content:t,transform:f(f({},N),i),extra:{attributes:c,styles:m,classes:["".concat(v.cssPrefix,"-layers-text")].concat(E(s))}})})}}},provides:function(a){a.generateLayersText=function(t,n){var r=n.transform,i=n.extra,o=null,s=null;if(_a){var l=parseInt(getComputedStyle(t).fontSize,10),c=t.getBoundingClientRect();o=c.width/l,s=c.height/l}return Promise.resolve([t,pa({content:t.innerHTML,width:o,height:s,transform:r,extra:i,watchable:!0})])}}},Lt=new RegExp('"',"ug"),ka=[1105920,1112319],Pa=f(f(f(f({},{FontAwesome:{normal:"fas",400:"fas"}}),An),Er),Fn),Re=Object.keys(Pa).reduce(function(e,a){return e[a.toLowerCase()]=Pa[a],e},{}),Yi=Object.keys(Re).reduce(function(e,a){var t=Re[a];return e[a]=t[900]||E(Object.entries(t))[0][1],e},{});function Hi(e){var a=e.replace(Lt,"");return yt(E(a)[0]||"")}function Gi(e){var a=e.getPropertyValue("font-feature-settings").includes("ss01"),t=e.getPropertyValue("content"),n=t.replace(Lt,""),r=n.codePointAt(0),i=r>=ka[0]&&r<=ka[1],o=n.length===2?n[0]===n[1]:!1;return i||o||a}function Xi(e,a){var t=e.replace(/^['"]|['"]$/g,"").toLowerCase(),n=parseInt(a),r=isNaN(n)?"normal":n;return(Re[t]||{})[r]||Yi[t]}function Ia(e,a){var t="".concat(Nr).concat(a.replace(":","-"));return new Promise(function(n,r){if(e.getAttribute(t)!==null)return n();var i=K(e.children),o=i.filter(function(U){return U.getAttribute(Oe)===a})[0],s=T.getComputedStyle(e,a),l=s.getPropertyValue("font-family"),c=l.match(Tr),u=s.getPropertyValue("font-weight"),m=s.getPropertyValue("content");if(o&&!c)return e.removeChild(o),n();if(c&&m!=="none"&&m!==""){var y=s.getPropertyValue("content"),p=Xi(l,u),w=Hi(y),b=c[0].startsWith("FontAwesome"),A=Gi(s),d=Je(p,w),h=d;if(b){var S=ni(w);S.iconName&&S.prefix&&(d=S.iconName,p=S.prefix)}if(d&&!A&&(!o||o.getAttribute(Ye)!==p||o.getAttribute(He)!==h)){e.setAttribute(t,h),o&&e.removeChild(o);var P=Li(),z=P.extra;z.attributes[Oe]=a,_e(d,p).then(function(U){var V=qe(f(f({},P),{},{icons:{main:U,mask:zt()},prefix:p,iconName:h,extra:z,watchable:!0})),pe=x.createElementNS("http://www.w3.org/2000/svg","svg");a==="::before"?e.insertBefore(pe,e.firstChild):e.appendChild(pe),pe.outerHTML=V.map(function($t){return te($t)}).join(`
`),e.removeAttribute(t),n()}).catch(r)}else n()}else n()})}function Ki(e){return Promise.all([Ia(e,"::before"),Ia(e,"::after")])}function Vi(e){return e.parentNode!==document.head&&!~Mr.indexOf(e.tagName.toUpperCase())&&!e.getAttribute(Oe)&&(!e.parentNode||e.parentNode.tagName!=="svg")}var Ji=function(a){return!!a&&ft.some(function(t){return a.includes(t)})},qi=function(a){if(!a)return[];var t=new Set,n=a.split(/,(?![^()]*\))/).map(function(l){return l.trim()});n=n.flatMap(function(l){return l.includes("(")?l:l.split(",").map(function(c){return c.trim()})});var r=ie(n),i;try{for(r.s();!(i=r.n()).done;){var o=i.value;if(Ji(o)){var s=ft.reduce(function(l,c){return l.replace(c,"")},o);s!==""&&s!=="*"&&t.add(s)}}}catch(l){r.e(l)}finally{r.f()}return t};function za(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!1;if(j){var t;if(a)t=e;else if(v.searchPseudoElementsFullScan)t=e.querySelectorAll("*");else{var n=new Set,r=ie(document.styleSheets),i;try{for(r.s();!(i=r.n()).done;){var o=i.value;try{var s=ie(o.cssRules),l;try{for(s.s();!(l=s.n()).done;){var c=l.value,u=qi(c.selectorText),m=ie(u),y;try{for(m.s();!(y=m.n()).done;){var p=y.value;n.add(p)}}catch(b){m.e(b)}finally{m.f()}}}catch(b){s.e(b)}finally{s.f()}}catch(b){v.searchPseudoElementsWarnings&&console.warn("Font Awesome: cannot parse stylesheet: ".concat(o.href," (").concat(b.message,`)
If it declares any Font Awesome CSS pseudo-elements, they will not be rendered as SVG icons. Add crossorigin="anonymous" to the <link>, enable searchPseudoElementsFullScan for slower but more thorough DOM parsing, or suppress this warning by setting searchPseudoElementsWarnings to false.`))}}}catch(b){r.e(b)}finally{r.f()}if(!n.size)return;var w=Array.from(n).join(", ");try{t=e.querySelectorAll(w)}catch{}}return new Promise(function(b,A){var d=K(t).filter(Vi).map(Ki),h=Qe.begin("searchPseudoElements");Ft(),Promise.all(d).then(function(){h(),De(),b()}).catch(function(){h(),De(),A()})})}}var Qi={hooks:function(){return{mutationObserverCallbacks:function(t){return t.pseudoElementsCallback=za,t}}},provides:function(a){a.pseudoElements2svg=function(t){var n=t.node,r=n===void 0?x:n;v.searchPseudoElements&&za(r)}}},Ca=!1,Zi={mixout:function(){return{dom:{unwatch:function(){Ft(),Ca=!0}}}},hooks:function(){return{bootstrap:function(){Sa(Le("mutationObserverCallbacks",{}))},noAuto:function(){Ei()},watch:function(t){var n=t.observeMutationsRoot;Ca?De():Sa(Le("mutationObserverCallbacks",{observeMutationsRoot:n}))}}}},Oa=function(a){var t={size:16,x:0,y:0,flipX:!1,flipY:!1,rotate:0};return a.toLowerCase().split(" ").reduce(function(n,r){var i=r.toLowerCase().split("-"),o=i[0],s=i.slice(1).join("-");if(o&&s==="h")return n.flipX=!0,n;if(o&&s==="v")return n.flipY=!0,n;if(s=parseFloat(s),isNaN(s))return n;switch(o){case"grow":n.size=n.size+s;break;case"shrink":n.size=n.size-s;break;case"left":n.x=n.x-s;break;case"right":n.x=n.x+s;break;case"up":n.y=n.y-s;break;case"down":n.y=n.y+s;break;case"rotate":n.rotate=n.rotate+s;break}return n},t)},eo={mixout:function(){return{parse:{transform:function(t){return Oa(t)}}}},hooks:function(){return{parseNodeAttributes:function(t,n){var r=n.getAttribute("data-fa-transform");return r&&(t.transform=Oa(r)),t}}},provides:function(a){a.generateAbstractTransformGrouping=function(t){var n=t.main,r=t.transform,i=t.containerWidth,o=t.iconWidth,s={transform:"translate(".concat(i/2," 256)")},l="translate(".concat(r.x*32,", ").concat(r.y*32,") "),c="scale(".concat(r.size/16*(r.flipX?-1:1),", ").concat(r.size/16*(r.flipY?-1:1),") "),u="rotate(".concat(r.rotate," 0 0)"),m={transform:"".concat(l," ").concat(c," ").concat(u)},y={transform:"translate(".concat(o/2*-1," -256)")},p={outer:s,inner:m,path:y};return{tag:"g",attributes:f({},p.outer),children:[{tag:"g",attributes:f({},p.inner),children:[{tag:n.icon.tag,children:n.icon.children,attributes:f(f({},n.icon.attributes),p.path)}]}]}}}},ke={x:0,y:0,width:"100%",height:"100%"};function Ea(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!0;return e.attributes&&(e.attributes.fill||a)&&(e.attributes.fill="black"),e}function ao(e){return e.tag==="g"?e.children:[e]}var to={hooks:function(){return{parseNodeAttributes:function(t,n){var r=n.getAttribute("data-fa-mask"),i=r?he(r.split(" ").map(function(o){return o.trim()})):zt();return i.prefix||(i.prefix=_()),t.mask=i,t.maskId=n.getAttribute("data-fa-mask-id"),t}}},provides:function(a){a.generateAbstractMask=function(t){var n=t.children,r=t.attributes,i=t.main,o=t.mask,s=t.maskId,l=t.transform,c=i.width,u=i.icon,m=o.width,y=o.icon,p=Xr({transform:l,containerWidth:m,iconWidth:c}),w={tag:"rect",attributes:f(f({},ke),{},{fill:"white"})},b=u.children?{children:u.children.map(Ea)}:{},A={tag:"g",attributes:f({},p.inner),children:[Ea(f({tag:u.tag,attributes:f(f({},u.attributes),p.path)},b))]},d={tag:"g",attributes:f({},p.outer),children:[A]},h="mask-".concat(s||ca()),S="clip-".concat(s||ca()),P={tag:"mask",attributes:f(f({},ke),{},{id:h,maskUnits:"userSpaceOnUse",maskContentUnits:"userSpaceOnUse"}),children:[w,d]},z={tag:"defs",children:[{tag:"clipPath",attributes:{id:S},children:ao(y)},P]};return n.push(z,{tag:"rect",attributes:f({fill:"currentColor","clip-path":"url(#".concat(S,")"),mask:"url(#".concat(h,")")},ke)}),{children:n,attributes:r}}}},no={provides:function(a){var t=!1;T.matchMedia&&(t=T.matchMedia("(prefers-reduced-motion: reduce)").matches),a.missingIconAbstract=function(){var n=[],r={fill:"currentColor"},i={attributeType:"XML",repeatCount:"indefinite",dur:"2s"};n.push({tag:"path",attributes:f(f({},r),{},{d:"M156.5,447.7l-12.6,29.5c-18.7-9.5-35.9-21.2-51.5-34.9l22.7-22.7C127.6,430.5,141.5,440,156.5,447.7z M40.6,272H8.5 c1.4,21.2,5.4,41.7,11.7,61.1L50,321.2C45.1,305.5,41.8,289,40.6,272z M40.6,240c1.4-18.8,5.2-37,11.1-54.1l-29.5-12.6 C14.7,194.3,10,216.7,8.5,240H40.6z M64.3,156.5c7.8-14.9,17.2-28.8,28.1-41.5L69.7,92.3c-13.7,15.6-25.5,32.8-34.9,51.5 L64.3,156.5z M397,419.6c-13.9,12-29.4,22.3-46.1,30.4l11.9,29.8c20.7-9.9,39.8-22.6,56.9-37.6L397,419.6z M115,92.4 c13.9-12,29.4-22.3,46.1-30.4l-11.9-29.8c-20.7,9.9-39.8,22.6-56.8,37.6L115,92.4z M447.7,355.5c-7.8,14.9-17.2,28.8-28.1,41.5 l22.7,22.7c13.7-15.6,25.5-32.9,34.9-51.5L447.7,355.5z M471.4,272c-1.4,18.8-5.2,37-11.1,54.1l29.5,12.6 c7.5-21.1,12.2-43.5,13.6-66.8H471.4z M321.2,462c-15.7,5-32.2,8.2-49.2,9.4v32.1c21.2-1.4,41.7-5.4,61.1-11.7L321.2,462z M240,471.4c-18.8-1.4-37-5.2-54.1-11.1l-12.6,29.5c21.1,7.5,43.5,12.2,66.8,13.6V471.4z M462,190.8c5,15.7,8.2,32.2,9.4,49.2h32.1 c-1.4-21.2-5.4-41.7-11.7-61.1L462,190.8z M92.4,397c-12-13.9-22.3-29.4-30.4-46.1l-29.8,11.9c9.9,20.7,22.6,39.8,37.6,56.9 L92.4,397z M272,40.6c18.8,1.4,36.9,5.2,54.1,11.1l12.6-29.5C317.7,14.7,295.3,10,272,8.5V40.6z M190.8,50 c15.7-5,32.2-8.2,49.2-9.4V8.5c-21.2,1.4-41.7,5.4-61.1,11.7L190.8,50z M442.3,92.3L419.6,115c12,13.9,22.3,29.4,30.5,46.1 l29.8-11.9C470,128.5,457.3,109.4,442.3,92.3z M397,92.4l22.7-22.7c-15.6-13.7-32.8-25.5-51.5-34.9l-12.6,29.5 C370.4,72.1,384.4,81.5,397,92.4z"})});var o=f(f({},i),{},{attributeName:"opacity"}),s={tag:"circle",attributes:f(f({},r),{},{cx:"256",cy:"364",r:"28"}),children:[]};return t||s.children.push({tag:"animate",attributes:f(f({},i),{},{attributeName:"r",values:"28;14;28;28;14;28;"})},{tag:"animate",attributes:f(f({},o),{},{values:"1;0;1;1;0;1;"})}),n.push(s),n.push({tag:"path",attributes:f(f({},r),{},{opacity:"1",d:"M263.7,312h-16c-6.6,0-12-5.4-12-12c0-71,77.4-63.9,77.4-107.8c0-20-17.8-40.2-57.4-40.2c-29.1,0-44.3,9.6-59.2,28.7 c-3.9,5-11.1,6-16.2,2.4l-13.1-9.2c-5.6-3.9-6.9-11.8-2.6-17.2c21.2-27.2,46.4-44.7,91.2-44.7c52.3,0,97.4,29.8,97.4,80.2 c0,67.6-77.4,63.5-77.4,107.8C275.7,306.6,270.3,312,263.7,312z"}),children:t?[]:[{tag:"animate",attributes:f(f({},o),{},{values:"1;0;0;0;0;1;"})}]}),t||n.push({tag:"path",attributes:f(f({},r),{},{opacity:"0",d:"M232.5,134.5l7,168c0.3,6.4,5.6,11.5,12,11.5h9c6.4,0,11.7-5.1,12-11.5l7-168c0.3-6.8-5.2-12.5-12-12.5h-23 C237.7,122,232.2,127.7,232.5,134.5z"}),children:[{tag:"animate",attributes:f(f({},o),{},{values:"0;0;1;1;0;0;"})}]}),{tag:"g",attributes:{class:"missing"},children:n}}}},ro={hooks:function(){return{parseNodeAttributes:function(t,n){var r=n.getAttribute("data-fa-symbol"),i=r===null?!1:r===""?!0:r;return t.symbol=i,t}}}},io=[Jr,Ri,Wi,Ui,Bi,Qi,Zi,eo,to,no,ro];di(io,{mixoutsTo:C});C.noAuto;C.config;var zo=C.library;C.dom;var We=C.parse;C.findIconDefinition;C.toHtml;var oo=C.icon;C.layer;C.text;C.counter;function I(e,a,t){return(a=co(a))in e?Object.defineProperty(e,a,{value:t,enumerable:!0,configurable:!0,writable:!0}):e[a]=t,e}function Na(e,a){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);a&&(n=n.filter(function(r){return Object.getOwnPropertyDescriptor(e,r).enumerable})),t.push.apply(t,n)}return t}function F(e){for(var a=1;a<arguments.length;a++){var t=arguments[a]!=null?arguments[a]:{};a%2?Na(Object(t),!0).forEach(function(n){I(e,n,t[n])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):Na(Object(t)).forEach(function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))})}return e}function so(e,a){if(e==null)return{};var t,n,r=lo(e,a);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);for(n=0;n<i.length;n++)t=i[n],a.indexOf(t)===-1&&{}.propertyIsEnumerable.call(e,t)&&(r[t]=e[t])}return r}function lo(e,a){if(e==null)return{};var t={};for(var n in e)if({}.hasOwnProperty.call(e,n)){if(a.indexOf(n)!==-1)continue;t[n]=e[n]}return t}function fo(e,a){if(typeof e!="object"||!e)return e;var t=e[Symbol.toPrimitive];if(t!==void 0){var n=t.call(e,a);if(typeof n!="object")return n;throw new TypeError("@@toPrimitive must return a primitive value.")}return(a==="string"?String:Number)(e)}function co(e){var a=fo(e,"string");return typeof a=="symbol"?a:a+""}function ue(e){"@babel/helpers - typeof";return ue=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(a){return typeof a}:function(a){return a&&typeof Symbol=="function"&&a.constructor===Symbol&&a!==Symbol.prototype?"symbol":typeof a},ue(e)}function Pe(e,a){return Array.isArray(a)&&a.length>0||!Array.isArray(a)&&a?I({},e,a):{}}function uo(e){var a,t=(a={"fa-spin":e.spin,"fa-pulse":e.pulse,"fa-fw":e.fixedWidth,"fa-border":e.border,"fa-li":e.listItem,"fa-inverse":e.inverse,"fa-flip":e.flip===!0,"fa-flip-horizontal":e.flip==="horizontal"||e.flip==="both","fa-flip-vertical":e.flip==="vertical"||e.flip==="both"},I(I(I(I(I(I(I(I(I(I(a,"fa-".concat(e.size),e.size!==null),"fa-rotate-".concat(e.rotation),e.rotation!==null),"fa-rotate-by",e.rotateBy),"fa-pull-".concat(e.pull),e.pull!==null),"fa-swap-opacity",e.swapOpacity),"fa-bounce",e.bounce),"fa-shake",e.shake),"fa-beat",e.beat),"fa-fade",e.fade),"fa-beat-fade",e.beatFade),I(I(I(I(a,"fa-flash",e.flash),"fa-spin-pulse",e.spinPulse),"fa-spin-reverse",e.spinReverse),"fa-width-auto",e.widthAuto));return Object.keys(t).map(function(n){return t[n]?n:null}).filter(function(n){return n})}var mo=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof ea<"u"?ea:typeof self<"u"?self:{},jt={exports:{}};(function(e){(function(a){var t=function(d,h,S){if(!c(h)||m(h)||y(h)||p(h)||l(h))return h;var P,z=0,U=0;if(u(h))for(P=[],U=h.length;z<U;z++)P.push(t(d,h[z],S));else{P={};for(var V in h)Object.prototype.hasOwnProperty.call(h,V)&&(P[d(V,S)]=t(d,h[V],S))}return P},n=function(d,h){h=h||{};var S=h.separator||"_",P=h.split||/(?=[A-Z])/;return d.split(P).join(S)},r=function(d){return w(d)?d:(d=d.replace(/[\-_\s]+(.)?/g,function(h,S){return S?S.toUpperCase():""}),d.substr(0,1).toLowerCase()+d.substr(1))},i=function(d){var h=r(d);return h.substr(0,1).toUpperCase()+h.substr(1)},o=function(d,h){return n(d,h).toLowerCase()},s=Object.prototype.toString,l=function(d){return typeof d=="function"},c=function(d){return d===Object(d)},u=function(d){return s.call(d)=="[object Array]"},m=function(d){return s.call(d)=="[object Date]"},y=function(d){return s.call(d)=="[object RegExp]"},p=function(d){return s.call(d)=="[object Boolean]"},w=function(d){return d=d-0,d===d},b=function(d,h){var S=h&&"process"in h?h.process:h;return typeof S!="function"?d:function(P,z){return S(P,d,z)}},A={camelize:r,decamelize:o,pascalize:i,depascalize:o,camelizeKeys:function(d,h){return t(b(r,h),d)},decamelizeKeys:function(d,h){return t(b(o,h),d,h)},pascalizeKeys:function(d,h){return t(b(i,h),d)},depascalizeKeys:function(){return this.decamelizeKeys.apply(this,arguments)}};e.exports?e.exports=A:a.humps=A})(mo)})(jt);var vo=jt.exports,ho=["class","style"];function go(e){return e.split(";").map(function(a){return a.trim()}).filter(function(a){return a}).reduce(function(a,t){var n=t.indexOf(":"),r=vo.camelize(t.slice(0,n)),i=t.slice(n+1).trim();return a[r]=i,a},{})}function po(e){return e.split(/\s+/).reduce(function(a,t){return a[t]=!0,a},{})}function Tt(e){var a=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(typeof e=="string")return e;var n=(e.children||[]).map(function(l){return Tt(l)}),r=Object.keys(e.attributes||{}).reduce(function(l,c){var u=e.attributes[c];switch(c){case"class":l.class=po(u);break;case"style":l.style=go(u);break;default:l.attrs[c]=u}return l},{attrs:{},class:{},style:{}});t.class;var i=t.style,o=i===void 0?{}:i,s=so(t,ho);return Wt(e.tag,F(F(F({},a),{},{class:r.class,style:F(F({},r.style),o)},r.attrs),s),n)}var _t=!1;try{_t=!1}catch{}function yo(){if(!_t&&console&&typeof console.error=="function"){var e;(e=console).error.apply(e,arguments)}}function Fa(e){if(e&&ue(e)==="object"&&e.prefix&&e.iconName&&e.icon)return e;if(We.icon)return We.icon(e);if(e===null)return null;if(ue(e)==="object"&&e.prefix&&e.iconName)return e;if(Array.isArray(e)&&e.length===2)return{prefix:e[0],iconName:e[1]};if(typeof e=="string")return{prefix:"fas",iconName:e}}var Co=Dt({name:"FontAwesomeIcon",props:{border:{type:Boolean,default:!1},fixedWidth:{type:Boolean,default:!1},flip:{type:[Boolean,String],default:!1,validator:function(a){return[!0,!1,"horizontal","vertical","both"].indexOf(a)>-1}},icon:{type:[Object,Array,String],required:!0},mask:{type:[Object,Array,String],default:null},maskId:{type:String,default:null},listItem:{type:Boolean,default:!1},pull:{type:String,default:null,validator:function(a){return["right","left"].indexOf(a)>-1}},pulse:{type:Boolean,default:!1},rotation:{type:[String,Number],default:null,validator:function(a){return[90,180,270].indexOf(Number.parseInt(a,10))>-1}},rotateBy:{type:Boolean,default:!1},swapOpacity:{type:Boolean,default:!1},size:{type:String,default:null,validator:function(a){return["2xs","xs","sm","lg","xl","2xl","1x","2x","3x","4x","5x","6x","7x","8x","9x","10x"].indexOf(a)>-1}},spin:{type:Boolean,default:!1},transform:{type:[String,Object],default:null},symbol:{type:[Boolean,String],default:!1},title:{type:String,default:null},titleId:{type:String,default:null},inverse:{type:Boolean,default:!1},bounce:{type:Boolean,default:!1},shake:{type:Boolean,default:!1},beat:{type:Boolean,default:!1},fade:{type:Boolean,default:!1},beatFade:{type:Boolean,default:!1},flash:{type:Boolean,default:!1},spinPulse:{type:Boolean,default:!1},spinReverse:{type:Boolean,default:!1},widthAuto:{type:Boolean,default:!1}},setup:function(a,t){var n=t.attrs,r=B(function(){return Fa(a.icon)}),i=B(function(){return Pe("classes",uo(a))}),o=B(function(){return Pe("transform",typeof a.transform=="string"?We.transform(a.transform):a.transform)}),s=B(function(){return Pe("mask",Fa(a.mask))}),l=B(function(){var u=F(F(F(F({},i.value),o.value),s.value),{},{symbol:a.symbol,maskId:a.maskId});return u.title=a.title,u.titleId=a.titleId,oo(r.value,u)});Rt(l,function(u){if(!u)return yo("Could not find one or more icon(s)",r.value,s.value)},{immediate:!0});var c=B(function(){return l.value?Tt(l.value.abstract[0],{},n):null});return function(){return c.value}}});var Oo={prefix:"fas",iconName:"right-long",icon:[576,512,["long-arrow-alt-right"],"f30b","M566.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-128 128c-9.2 9.2-22.9 11.9-34.9 6.9S384 396.9 384 384l0-64-336 0c-26.5 0-48-21.5-48-48l0-32c0-26.5 21.5-48 48-48l336 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l128 128z"]},Eo={prefix:"fas",iconName:"calculator",icon:[384,512,[128425],"f1ec","M64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-384c0-35.3-28.7-64-64-64L64 0zM96 64l192 0c17.7 0 32 14.3 32 32l0 32c0 17.7-14.3 32-32 32L96 160c-17.7 0-32-14.3-32-32l0-32c0-17.7 14.3-32 32-32zm16 168a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zM88 352a24 24 0 1 1 0-48 24 24 0 1 1 0 48zm128-24a24 24 0 1 1 -48 0 24 24 0 1 1 48 0zm80 24a24 24 0 1 1 0-48 24 24 0 1 1 0 48zM64 424c0-13.3 10.7-24 24-24l112 0c13.3 0 24 10.7 24 24s-10.7 24-24 24L88 448c-13.3 0-24-10.7-24-24zm232-24c13.3 0 24 10.7 24 24s-10.7 24-24 24-24-10.7-24-24 10.7-24 24-24z"]},No={prefix:"fas",iconName:"car",icon:[512,512,[128664,"automobile"],"f1b9","M135.2 117.4l-26.1 74.6 293.8 0-26.1-74.6C372.3 104.6 360.2 96 346.6 96L165.4 96c-13.6 0-25.7 8.6-30.2 21.4zM39.6 196.8L74.8 96.3C88.3 57.8 124.6 32 165.4 32l181.2 0c40.8 0 77.1 25.8 90.6 64.3l35.2 100.5c23.2 9.6 39.6 32.5 39.6 59.2l0 192c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-32-320 0 0 32c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32L0 256c0-26.7 16.4-49.6 39.6-59.2zM128 304a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm288 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"]},bo={prefix:"fas",iconName:"calendar-days",icon:[448,512,["calendar-alt"],"f073","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zM64 240l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm128 0l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zM64 368l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16zm144-16c-8.8 0-16 7.2-16 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0zm112 16l0 32c0 8.8 7.2 16 16 16l32 0c8.8 0 16-7.2 16-16l0-32c0-8.8-7.2-16-16-16l-32 0c-8.8 0-16 7.2-16 16z"]},Fo=bo,Mo={prefix:"fas",iconName:"power-off",icon:[512,512,[9211],"f011","M288 0c0-17.7-14.3-32-32-32S224-17.7 224 0l0 256c0 17.7 14.3 32 32 32s32-14.3 32-32L288 0zM146.3 98.4c14.5-10.1 18-30.1 7.9-44.6s-30.1-18-44.6-7.9C43.4 92.1 0 169 0 256 0 397.4 114.6 512 256 512S512 397.4 512 256c0-87-43.4-163.9-109.7-210.1-14.5-10.1-34.4-6.6-44.6 7.9s-6.6 34.4 7.9 44.6c49.8 34.8 82.3 92.4 82.3 157.6 0 106-86 192-192 192S64 362 64 256c0-65.2 32.5-122.9 82.3-157.6z"]},Lo={prefix:"fas",iconName:"eye",icon:[576,512,[128065],"f06e","M288 32c-80.8 0-145.5 36.8-192.6 80.6-46.8 43.5-78.1 95.4-93 131.1-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6s145.5-36.8 192.6-80.6c46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6zM144 256a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm144-64c0 35.3-28.7 64-64 64-11.5 0-22.3-3-31.7-8.4-1 10.9-.1 22.1 2.9 33.2 13.7 51.2 66.4 81.6 117.6 67.9s81.6-66.4 67.9-117.6c-12.2-45.7-55.5-74.8-101.1-70.8 5.3 9.3 8.4 20.1 8.4 31.7z"]},jo={prefix:"fas",iconName:"delete-left",icon:[640,512,[9003,"backspace"],"f55a","M576 128c0-35.3-28.7-64-64-64L205.3 64c-17 0-33.3 6.7-45.3 18.7L9.4 233.4c-6 6-9.4 14.1-9.4 22.6s3.4 16.6 9.4 22.6L160 429.3c12 12 28.3 18.7 45.3 18.7L512 448c35.3 0 64-28.7 64-64l0-256zM284.1 188.1c9.4-9.4 24.6-9.4 33.9 0l33.9 33.9 33.9-33.9c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-33.9 33.9 33.9 33.9c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-33.9-33.9-33.9 33.9c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l33.9-33.9-33.9-33.9c-9.4-9.4-9.4-24.6 0-33.9z"]},xo={prefix:"fas",iconName:"pen-to-square",icon:[512,512,["edit"],"f044","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L368 46.1 465.9 144 490.3 119.6c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L432 177.9 334.1 80 172.4 241.7zM96 64C43 64 0 107 0 160L0 416c0 53 43 96 96 96l256 0c53 0 96-43 96-96l0-96c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 96c0 17.7-14.3 32-32 32L96 448c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l96 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 64z"]},To=xo,_o={prefix:"fas",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M256 0a256 256 0 1 1 0 512 256 256 0 1 1 0-512zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},$o={prefix:"fas",iconName:"arrow-right-to-bracket",icon:[512,512,["sign-in"],"f090","M352 96l64 0c17.7 0 32 14.3 32 32l0 256c0 17.7-14.3 32-32 32l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l64 0c53 0 96-43 96-96l0-256c0-53-43-96-96-96l-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32zm-9.4 182.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L242.7 224 32 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},So={prefix:"fas",iconName:"circle-xmark",icon:[512,512,[61532,"times-circle","xmark-circle"],"f057","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM167 167c9.4-9.4 24.6-9.4 33.9 0l55 55 55-55c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-55 55 55 55c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-55-55-55 55c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l55-55-55-55c-9.4-9.4-9.4-24.6 0-33.9z"]},Do=So,Ro={prefix:"fas",iconName:"plug-circle-bolt",icon:[640,512,[],"e55b","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm177.4-77c-5.8-4.2-13.8-4-19.4 .5l-80 64c-5.3 4.2-7.4 11.4-5.1 17.8S433.2 416 440 416l32.9 0-15.9 42.4c-2.5 6.7-.2 14.3 5.6 18.6s13.8 4 19.4-.5l80-64c5.3-4.2 7.4-11.4 5.1-17.8S558.8 384 552 384l-32.9 0 15.9-42.4c2.5-6.7 .2-14.3-5.6-18.6z"]},Wo={prefix:"fas",iconName:"calendar-day",icon:[448,512,[],"f783","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l64 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-64 0z"]},Uo={prefix:"fas",iconName:"circle-user",icon:[512,512,[62142,"user-circle"],"f2bd","M399 384.2C376.9 345.8 335.4 320 288 320l-64 0c-47.4 0-88.9 25.8-111 64.2 35.2 39.2 86.2 63.8 143 63.8s107.8-24.7 143-63.8zM0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zm256 16a72 72 0 1 0 0-144 72 72 0 1 0 0 144z"]},Bo={prefix:"fas",iconName:"car-battery",icon:[512,512,["battery-car"],"f5df","M80 64c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l96 0c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l16 0c35.3 0 64 28.7 64 64l0 256c0 35.3-28.7 64-64 64L64 448c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l16 0zM392 184c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 32-32 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l32 0 0 32c0 13.3 10.7 24 24 24s24-10.7 24-24l0-32 32 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-32 0 0-32zM64 240c0 13.3 10.7 24 24 24l112 0c13.3 0 24-10.7 24-24s-10.7-24-24-24L88 216c-13.3 0-24 10.7-24 24z"]},Yo={prefix:"fas",iconName:"wrench",icon:[576,512,[128295],"f0ad","M509.4 98.6c7.6-7.6 20.3-5.7 24.1 4.3 6.8 17.7 10.5 37 10.5 57.1 0 88.4-71.6 160-160 160-17.5 0-34.4-2.8-50.2-8L146.9 498.9c-28.1 28.1-73.7 28.1-101.8 0s-28.1-73.7 0-101.8L232 210.2c-5.2-15.8-8-32.6-8-50.2 0-88.4 71.6-160 160-160 20.1 0 39.4 3.7 57.1 10.5 10 3.8 11.8 16.5 4.3 24.1l-88.7 88.7c-3 3-4.7 7.1-4.7 11.3l0 41.4c0 8.8 7.2 16 16 16l41.4 0c4.2 0 8.3-1.7 11.3-4.7l88.7-88.7z"]},Ho={prefix:"fas",iconName:"eraser",icon:[576,512,[],"f12d","M178.5 416l123 0 65.3-65.3-173.5-173.5-126.7 126.7 112 112zM224 480l-45.5 0c-17 0-33.3-6.7-45.3-18.7L17 345C6.1 334.1 0 319.4 0 304s6.1-30.1 17-41L263 17C273.9 6.1 288.6 0 304 0s30.1 6.1 41 17L527 199c10.9 10.9 17 25.6 17 41s-6.1 30.1-17 41l-135 135 120 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-288 0z"]},Go={prefix:"fas",iconName:"charging-station",icon:[576,512,[],"f5e7","M64 64C64 28.7 92.7 0 128 0L288 0c35.3 0 64 28.7 64 64l0 224c44.2 0 80 35.8 80 80l0 12c0 11 9 20 20 20s20-9 20-20l0-127.7c-32.5-10.2-56-40.5-56-76.3l0-32c0-8.8 7.2-16 16-16l16 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 32 0 0-48c0-8.8 7.2-16 16-16s16 7.2 16 16l0 48 16 0c8.8 0 16 7.2 16 16l0 32c0 35.8-23.5 66.1-56 76.3L520 380c0 37.6-30.4 68-68 68s-68-30.4-68-68l0-12c0-17.7-14.3-32-32-32l0 129.4c9.3 3.3 16 12.2 16 22.6 0 13.3-10.7 24-24 24L72 512c-13.3 0-24-10.7-24-24 0-10.5 6.7-19.3 16-22.6L64 64zm82.7 125.7l39 0-20.9 66.9c-2.4 7.6 3.3 15.4 11.3 15.4 2.9 0 5.6-1 7.8-2.9l94.6-82c3.1-2.7 4.9-6.6 4.9-10.7 0-7.8-6.3-14.1-14.1-14.1l-39 0 20.9-66.9c2.4-7.6-3.3-15.4-11.3-15.4-2.9 0-5.6 1-7.8 2.9l-94.6 82c-3.1 2.7-4.9 6.6-4.9 10.7 0 7.8 6.3 14.1 14.1 14.1z"]},wo={prefix:"fas",iconName:"house",icon:[512,512,[127968,63498,63500,"home","home-alt","home-lg-alt"],"f015","M277.8 8.6c-12.3-11.4-31.3-11.4-43.5 0l-224 208c-9.6 9-12.8 22.9-8 35.1S18.8 272 32 272l16 0 0 176c0 35.3 28.7 64 64 64l288 0c35.3 0 64-28.7 64-64l0-176 16 0c13.2 0 25-8.1 29.8-20.3s1.6-26.2-8-35.1l-224-208zM240 320l32 0c26.5 0 48 21.5 48 48l0 96-128 0 0-96c0-26.5 21.5-48 48-48z"]},Xo=wo,Ko={prefix:"fas",iconName:"gauge-high",icon:[512,512,[62461,"tachometer-alt","tachometer-alt-fast"],"f625","M0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64 0-16.2-6-31.1-16-42.3l69.5-138.9c5.9-11.9 1.1-26.3-10.7-32.2s-26.3-1.1-32.2 10.7L261.1 288.2c-1.7-.1-3.4-.2-5.1-.2-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z"]},Vo={prefix:"fas",iconName:"right-left",icon:[512,512,["exchange-alt"],"f362","M502.6 150.6l-96 96c-9.2 9.2-22.9 11.9-34.9 6.9S352 236.9 352 224l0-64-320 0c-17.7 0-32-14.3-32-32S14.3 96 32 96l320 0 0-64c0-12.9 7.8-24.6 19.8-29.6s25.7-2.2 34.9 6.9l96 96c12.5 12.5 12.5 32.8 0 45.3zm-397.3 352l-96-96c-12.5-12.5-12.5-32.8 0-45.3l96-96c9.2-9.2 22.9-11.9 34.9-6.9S160 275.1 160 288l0 64 320 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-320 0 0 64c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9z"]},Jo={prefix:"fas",iconName:"lock-open",icon:[576,512,[],"f3c1","M384 96c0-35.3 28.7-64 64-64s64 28.7 64 64l0 32c0 17.7 14.3 32 32 32s32-14.3 32-32l0-32c0-70.7-57.3-128-128-128S320 25.3 320 96l0 64-160 0c-35.3 0-64 28.7-64 64l0 224c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-224c0-35.3-28.7-64-64-64l-32 0 0-64z"]},qo={prefix:"fas",iconName:"plug-circle-xmark",icon:[640,512,[],"e560","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM496 256a144 144 0 1 1 0 288 144 144 0 1 1 0-288zm59.3 107.3c6.2-6.2 6.2-16.4 0-22.6s-16.4-6.2-22.6 0l-36.7 36.7-36.7-36.7c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l36.7 36.7-36.7 36.7c-6.2 6.2-6.2 16.4 0 22.6s16.4 6.2 22.6 0l36.7-36.7 36.7 36.7c6.2 6.2 16.4 6.2 22.6 0s6.2-16.4 0-22.6l-36.7-36.7 36.7-36.7z"]},Qo={prefix:"fas",iconName:"solar-panel",icon:[576,512,[],"f5ba","M121.8 32c-30 0-56 20.8-62.5 50.1L9.6 306.1C.7 346.1 31.1 384 72 384l184.1 0 0 64-64 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l192 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0 0-64 184.1 0c40.9 0 71.4-37.9 62.5-77.9l-49.8-224C510.4 52.8 484.5 32 454.5 32L121.8 32zM245.6 96l85.2 0 7.3 88-99.8 0 7.3-88zm-55.5 88l-87.8 0 19.6-88 75.6 0-7.3 88zM91.6 232l94.5 0-7.3 88-106.7 0 19.6-88zm142.6 0l107.8 0 7.3 88-122.5 0 7.3-88zm156 0l94.5 0 19.6 88-106.7 0-7.3-88zM474 184l-87.8 0-7.3-88 75.6 0 19.6 88z"]},Zo={prefix:"fas",iconName:"plug-circle-check",icon:[640,512,[],"e55c","M192-32c17.7 0 32 14.3 32 32l0 96 128 0 0-96c0-17.7 14.3-32 32-32s32 14.3 32 32l0 96 64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 48.7c-98.6 8.1-176 90.7-176 191.3 0 27.3 5.7 53.3 16 76.9l0 3.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-66.7C165.2 398.1 96 319.1 96 224l0-64c-17.7 0-32-14.3-32-32S78.3 96 96 96l64 0 0-96c0-17.7 14.3-32 32-32zM352 400a144 144 0 1 1 288 0 144 144 0 1 1 -288 0zm201.4-60.9c-7.1-5.2-17.2-3.6-22.4 3.5l-53 72.9-26.8-26.8c-6.2-6.2-16.4-6.2-22.6 0s-6.2 16.4 0 22.6l40 40c3.3 3.3 7.9 5 12.6 4.6s8.9-2.8 11.7-6.5l64-88c5.2-7.1 3.6-17.2-3.5-22.3z"]},es={prefix:"fas",iconName:"star",icon:[576,512,[11088,61446],"f005","M309.5-18.9c-4.1-8-12.4-13.1-21.4-13.1s-17.3 5.1-21.4 13.1L193.1 125.3 33.2 150.7c-8.9 1.4-16.3 7.7-19.1 16.3s-.5 18 5.8 24.4l114.4 114.5-25.2 159.9c-1.4 8.9 2.3 17.9 9.6 23.2s16.9 6.1 25 2L288.1 417.6 432.4 491c8 4.1 17.7 3.3 25-2s11-14.2 9.6-23.2L441.7 305.9 556.1 191.4c6.4-6.4 8.6-15.8 5.8-24.4s-10.1-14.9-19.1-16.3L383 125.3 309.5-18.9z"]},Ao={prefix:"fas",iconName:"triangle-exclamation",icon:[512,512,[9888,"exclamation-triangle","warning"],"f071","M256 0c14.7 0 28.2 8.1 35.2 21l216 400c6.7 12.4 6.4 27.4-.8 39.5S486.1 480 472 480L40 480c-14.1 0-27.2-7.4-34.4-19.5s-7.5-27.1-.8-39.5l216-400c7-12.9 20.5-21 35.2-21zm0 352a32 32 0 1 0 0 64 32 32 0 1 0 0-64zm0-192c-18.2 0-32.7 15.5-31.4 33.7l7.4 104c.9 12.5 11.4 22.3 23.9 22.3 12.6 0 23-9.7 23.9-22.3l7.4-104c1.3-18.2-13.1-33.7-31.4-33.7z"]},as=Ao,ts={prefix:"fas",iconName:"lock",icon:[384,512,[128274],"f023","M128 96l0 64 128 0 0-64c0-35.3-28.7-64-64-64s-64 28.7-64 64zM64 160l0-64C64 25.3 121.3-32 192-32S320 25.3 320 96l0 64c35.3 0 64 28.7 64 64l0 224c0 35.3-28.7 64-64 64L64 512c-35.3 0-64-28.7-64-64L0 224c0-35.3 28.7-64 64-64z"]},ns={prefix:"fas",iconName:"arrow-right-from-bracket",icon:[512,512,["sign-out"],"f08b","M160 96c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 32C43 32 0 75 0 128L0 384c0 53 43 96 96 96l64 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l64 0zM502.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L402.7 224 192 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128z"]},rs={prefix:"fas",iconName:"eye-slash",icon:[576,512,[],"f070","M41-24.9c-9.4-9.4-24.6-9.4-33.9 0S-2.3-.3 7 9.1l528 528c9.4 9.4 24.6 9.4 33.9 0s9.4-24.6 0-33.9l-96.4-96.4c2.7-2.4 5.4-4.8 8-7.2 46.8-43.5 78.1-95.4 93-131.1 3.3-7.9 3.3-16.7 0-24.6-14.9-35.7-46.2-87.7-93-131.1-47.1-43.7-111.8-80.6-192.6-80.6-56.8 0-105.6 18.2-146 44.2L41-24.9zM204.5 138.7c23.5-16.8 52.4-26.7 83.5-26.7 79.5 0 144 64.5 144 144 0 31.1-9.9 59.9-26.7 83.5l-34.7-34.7c12.7-21.4 17-47.7 10.1-73.7-13.7-51.2-66.4-81.6-117.6-67.9-8.6 2.3-16.7 5.7-24 10l-34.7-34.7zM325.3 395.1c-11.9 3.2-24.4 4.9-37.3 4.9-79.5 0-144-64.5-144-144 0-12.9 1.7-25.4 4.9-37.3L69.4 139.2c-32.6 36.8-55 75.8-66.9 104.5-3.3 7.9-3.3 16.7 0 24.6 14.9 35.7 46.2 87.7 93 131.1 47.1 43.7 111.8 80.6 192.6 80.6 37.3 0 71.2-7.9 101.5-20.6l-64.2-64.2z"]},is={prefix:"fas",iconName:"bolt",icon:[448,512,[9889,"zap"],"f0e7","M338.8-9.9c11.9 8.6 16.3 24.2 10.9 37.8L271.3 224 416 224c13.5 0 25.5 8.4 30.1 21.1s.7 26.9-9.6 35.5l-288 240c-11.3 9.4-27.4 9.9-39.3 1.3s-16.3-24.2-10.9-37.8L176.7 288 32 288c-13.5 0-25.5-8.4-30.1-21.1s-.7-26.9 9.6-35.5l288-240c11.3-9.4 27.4-9.9 39.3-1.3z"]},ko={prefix:"fas",iconName:"arrow-rotate-left",icon:[512,512,[8634,"arrow-left-rotate","arrow-rotate-back","arrow-rotate-backward","undo"],"f0e2","M256 64c-56.8 0-107.9 24.7-143.1 64l47.1 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 192c-17.7 0-32-14.3-32-32L0 32C0 14.3 14.3 0 32 0S64 14.3 64 32l0 54.7C110.9 33.6 179.5 0 256 0 397.4 0 512 114.6 512 256S397.4 512 256 512c-87 0-163.9-43.4-210.1-109.7-10.1-14.5-6.6-34.4 7.9-44.6s34.4-6.6 44.6 7.9c34.8 49.8 92.4 82.3 157.6 82.3 106 0 192-86 192-192S362 64 256 64z"]},os=ko,ss={prefix:"fas",iconName:"coins",icon:[512,512,[],"f51e","M128 96l0-16c0-44.2 86-80 192-80S512 35.8 512 80l0 16c0 30.6-41.3 57.2-102 70.7-2.4-2.8-4.9-5.5-7.4-8-15.5-15.3-35.5-26.9-56.4-35.5-41.9-17.5-96.5-27.1-154.2-27.1-21.9 0-43.3 1.4-63.8 4.1-.2-1.3-.2-2.7-.2-4.1zM432 353l0-46.2c15.1-3.9 29.3-8.5 42.2-13.9 13.2-5.5 26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zm0-96l0-33c0-4.5-.4-8.8-1-13 15.5-3.9 30-8.6 43.2-14.2s26.1-12.2 37.8-20.3l0 15.4c0 26.8-31.5 50.5-80 65zM0 240l0-16c0-44.2 86-80 192-80s192 35.8 192 80l0 16c0 44.2-86 80-192 80S0 284.2 0 240zm384 96c0 44.2-86 80-192 80S0 380.2 0 336l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3l0 15.4zm0 80.6l0 15.4c0 44.2-86 80-192 80S0 476.2 0 432l0-15.4c11.6 8.1 24.5 14.7 37.8 20.3 41.9 17.5 96.5 27.1 154.2 27.1s112.3-9.7 154.2-27.1c13.2-5.5 26.1-12.2 37.8-20.3z"]},ls={prefix:"fas",iconName:"calendar-week",icon:[448,512,[],"f784","M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-192 0z"]},Po={prefix:"fas",iconName:"circle-info",icon:[512,512,["info-circle"],"f05a","M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM224 160a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm-8 64l48 0c13.3 0 24 10.7 24 24l0 88 8 0c13.3 0 24 10.7 24 24s-10.7 24-24 24l-80 0c-13.3 0-24-10.7-24-24s10.7-24 24-24l24 0 0-64-24 0c-13.3 0-24-10.7-24-24s10.7-24 24-24z"]},fs=Po;var cs={prefix:"far",iconName:"clock",icon:[512,512,[128339,"clock-four"],"f017","M464 256a208 208 0 1 1 -416 0 208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0 256 256 0 1 0 -512 0zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"]},us={prefix:"far",iconName:"star",icon:[576,512,[11088,61446],"f005","M288.1-32c9 0 17.3 5.1 21.4 13.1L383 125.3 542.9 150.7c8.9 1.4 16.3 7.7 19.1 16.3s.5 18-5.8 24.4L441.7 305.9 467 465.8c1.4 8.9-2.3 17.9-9.6 23.2s-17 6.1-25 2L288.1 417.6 143.8 491c-8 4.1-17.7 3.3-25-2s-11-14.2-9.6-23.2L134.4 305.9 20 191.4c-6.4-6.4-8.6-15.8-5.8-24.4s10.1-14.9 19.1-16.3l159.9-25.4 73.6-144.2c4.1-8 12.4-13.1 21.4-13.1zm0 76.8L230.3 158c-3.5 6.8-10 11.6-17.6 12.8l-125.5 20 89.8 89.9c5.4 5.4 7.9 13.1 6.7 20.7l-19.8 125.5 113.3-57.6c6.8-3.5 14.9-3.5 21.8 0l113.3 57.6-19.8-125.5c-1.2-7.6 1.3-15.3 6.7-20.7l89.8-89.9-125.5-20c-7.6-1.2-14.1-6-17.6-12.8L288.1 44.8z"]};export{is as A,Wo as B,ls as C,Fo as D,Vo as E,Co as F,Oo as G,ss as H,qo as I,Zo as J,Ro as K,os as L,Mo as M,Ho as a,ts as b,Jo as c,Uo as d,$o as e,jo as f,ns as g,Lo as h,rs as i,Ko as j,Bo as k,zo as l,Qo as m,Xo as n,Go as o,Eo as p,Yo as q,No as r,To as s,Do as t,as as u,fs as v,es as w,us as x,_o as y,cs as z};
