import{C as y}from"./index-e2dbf7bf.js";import{l as W,K as L,F as x,L as k,M as C,c as q,N as E,O as S,P as A,Q as z,R as M,S as V}from"./vendor-fortawesome-3d19d475.js";import{_ as w,u as o,k as r,z as l,E as p,G as n,y as c,F as b,x as g,B as T,l as I,N as P,M as $}from"./vendor-06e11d0e.js";import{C as H,p as Z,a as F,L as K,b as G,P as J,c as Q,T as U,i as X,d as Y,e as ee}from"./vendor-chartjs-888a84c2.js";import"./vendor-bootstrap-4263d7eb.js";import"./vendor-jquery-9fc083b4.js";import"./vendor-axios-22b906fb.js";import"./vendor-sortablejs-0bb60e5b.js";import"./vendor-luxon-8ddd27a0.js";W.add(L);const te={name:"ChargePointSumCard",components:{FontAwesomeIcon:x},mixins:[y]};function ne(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-text-input"),d=o("openwb-base-heading"),u=o("openwb-base-card");return r(),l(u,{subtype:"primary",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","charging-station"]}),t[0]||(t[0]=c(" Alle Ladepunkte "))]),default:p(()=>[n(m,{title:"Leistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/chargepoint/get/power",3,3,.001)},null,8,["model-value"]),n(m,{title:"Zählerstand laden",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/get/imported",3,3,.001)},null,8,["model-value"]),n(m,{title:"Zählerstand entladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/get/exported",3,3,.001)},null,8,["model-value"]),n(d,null,{default:p(()=>t[1]||(t[1]=[c("Historie")])),_:1}),n(m,{title:"Heute geladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/get/daily_imported",3,3,.001)},null,8,["model-value"]),n(m,{title:"Heute entladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/get/daily_exported",3,3,.001)},null,8,["model-value"])]),_:1})}const oe=w(te,[["render",ne],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/ChargePointSumCard.vue"]]);W.add(k,C,q,L);const ae={name:"ChargePointCard",components:{FontAwesomeIcon:x},mixins:[y],props:{installedChargePointKey:{type:String,required:!0},installedChargePoint:{type:Object,required:!0}},data(){return{statusLevel:["success","warning","danger"]}},computed:{chargePointIndex:{get(){return parseInt(this.installedChargePointKey.match(/(?:\/)(\d+)(?=\/)/)[1])}}}},re={style:{"white-space":"pre-wrap"}},se={style:{"white-space":"pre-wrap"}};function le(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-checkbox-input"),u=o("openwb-base-text-input"),h=o("openwb-base-heading"),B=o("openwb-base-card");return r(),l(B,{subtype:"primary",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","charging-station"]}),c(" "+b(a.installedChargePoint.name)+" (ID: "+b(s.chargePointIndex)+") ",1)]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[0]||(t[0]=c(" Modulmeldung:")),t[1]||(t[1]=g("br",null,null,-1)),g("span",re,b(e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/fault_str"]),1)]),_:1},8,["subtype"]),n(m,{subtype:"info"},{default:p(()=>[t[2]||(t[2]=c(" Statusmeldung:")),t[3]||(t[3]=g("br",null,null,-1)),g("span",se,b(e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/state_str"]),1)]),_:1}),n(d,{title:"Fahrzeug angesteckt",disabled:"","model-value":e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/plug_state"]==1},null,8,["model-value"]),n(d,{title:"Ladevorgang aktiv",disabled:"","model-value":e.$store.state.mqtt["openWB/chargepoint/"+s.chargePointIndex+"/get/charge_state"]==1},null,8,["model-value"]),n(u,{title:"Zählerstand laden",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/imported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Zählerstand entladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/exported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Heute geladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/daily_imported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Heute entladen",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/daily_exported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Wirkleistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/power",3,3,.001)},null,8,["model-value"]),n(u,{title:"Ladestromvorgabe",readonly:"",class:"text-right text-monospace",step:"0.01",unit:"A","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/set/current",2)},null,8,["model-value"]),n(u,{title:"Netzfrequenz",readonly:"",class:"text-right text-monospace",step:"0.01",unit:"Hz","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/frequency",2)},null,8,["model-value"]),n(h,null,{default:p(()=>t[4]||(t[4]=[c("Werte pro Phase")])),_:1}),n(u,{title:"Spannung",readonly:"",class:"text-right text-monospace",unit:"V","model-value":e.formatPhaseArrayNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/voltages",1)},null,8,["model-value"]),n(u,{title:"Strom",readonly:"",class:"text-right text-monospace",unit:"A","model-value":e.formatPhaseArrayNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/currents",2)},null,8,["model-value"]),n(u,{title:"Wirkleistung",readonly:"",class:"text-right text-monospace",unit:"kW","model-value":e.formatPhaseArrayNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/powers",3,3,.001)},null,8,["model-value"]),n(u,{title:"Leistungsfaktor",readonly:"",class:"text-right text-monospace","model-value":e.formatPhaseArrayNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/power_factors",2)},null,8,["model-value"]),n(h,null,{default:p(()=>t[5]||(t[5]=[c("Phasen")])),_:1}),e.$store.state.mqtt["openWB/general/extern"]===!0?(r(),l(u,{key:0,title:"Vorgabe",readonly:"",class:"text-right text-monospace","model-value":e.formatNumberTopic("openWB/internal_chargepoint/"+s.chargePointIndex+"/data/phases_to_use")},null,8,["model-value"])):(r(),l(u,{key:1,title:"Vorgabe",readonly:"",class:"text-right text-monospace","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/set/phases_to_use")},null,8,["model-value"])),n(u,{title:"Aktuell",readonly:"",class:"text-right text-monospace","model-value":e.formatNumberTopic("openWB/chargepoint/"+s.chargePointIndex+"/get/phases_in_use")},null,8,["model-value"])]),_:1})}const ie=w(ae,[["render",le],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/ChargePointCard.vue"]]);W.add(k,C,q,E);const ue={name:"CounterCard",components:{FontAwesomeIcon:x},mixins:[y],props:{counter:{type:Object,required:!0}},data(){return{statusLevel:["success","warning","danger"]}}},pe={style:{"white-space":"pre-wrap"}},de={style:{"white-space":"pre-wrap"}};function ce(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-heading"),u=o("openwb-base-text-input"),h=o("openwb-base-card");return r(),l(h,{subtype:"danger",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","gauge-high"]}),c(" "+b(a.counter.name)+" (ID: "+b(a.counter.id)+") ",1)]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[0]||(t[0]=c(" Modulmeldung:")),t[1]||(t[1]=g("br",null,null,-1)),g("span",pe,b(e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/fault_str"]),1)]),_:1},8,["subtype"]),e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/state_str"]!=null?(r(),l(m,{key:0,subtype:"info"},{default:p(()=>[t[2]||(t[2]=c(" Statusmeldung:")),t[3]||(t[3]=g("br",null,null,-1)),g("span",de,b(e.$store.state.mqtt["openWB/counter/"+a.counter.id+"/get/state_str"]),1)]),_:1})):T("",!0),n(d,null,{default:p(()=>t[4]||(t[4]=[c("Zählerstände")])),_:1}),n(u,{title:"Export",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/counter/"+a.counter.id+"/get/exported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Import",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/counter/"+a.counter.id+"/get/imported",3,3,.001)},null,8,["model-value"]),n(d,null,{default:p(()=>t[5]||(t[5]=[c("Saldierte Werte")])),_:1}),n(u,{title:"Wirkleistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/counter/"+a.counter.id+"/get/power",3,3,.001)},null,8,["model-value"]),n(u,{title:"Netzfrequenz",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"Hz","model-value":e.formatNumberTopic("openWB/counter/"+a.counter.id+"/get/frequency",3)},null,8,["model-value"]),n(d,null,{default:p(()=>t[6]||(t[6]=[c("Werte pro Phase")])),_:1}),n(u,{title:"Spannung",readonly:"",class:"text-right text-monospace",unit:"V","model-value":e.formatPhaseArrayNumberTopic("openWB/counter/"+a.counter.id+"/get/voltages",1)},null,8,["model-value"]),n(u,{title:"Strom",readonly:"",class:"text-right text-monospace",unit:"A","model-value":e.formatPhaseArrayNumberTopic("openWB/counter/"+a.counter.id+"/get/currents",2)},null,8,["model-value"]),n(u,{title:"Wirkleistung",readonly:"",class:"text-right text-monospace",unit:"kW","model-value":e.formatPhaseArrayNumberTopic("openWB/counter/"+a.counter.id+"/get/powers",3,3,.001)},null,8,["model-value"]),n(u,{title:"Leistungsfaktor",readonly:"",class:"text-right text-monospace","model-value":e.formatPhaseArrayNumberTopic("openWB/counter/"+a.counter.id+"/get/power_factors",2)},null,8,["model-value"])]),_:1})}const me=w(ue,[["render",ce],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/CounterCard.vue"]]);W.add(k,C,q,S);const ge={name:"InverterSumCard",components:{FontAwesomeIcon:x},mixins:[y],data(){return{statusLevel:["success","warning","danger"]}}},fe={style:{"white-space":"pre-wrap"}};function be(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-text-input"),u=o("openwb-base-heading"),h=o("openwb-base-card");return r(),l(h,{subtype:"success",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","solar-panel"]}),t[0]||(t[0]=c(" Alle Wechselrichter "))]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/pv/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/pv/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/pv/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[1]||(t[1]=c(" Modulmeldung:")),t[2]||(t[2]=g("br",null,null,-1)),g("span",fe,b(e.$store.state.mqtt["openWB/pv/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,{title:"Zählerstand",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/get/exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Leistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/pv/get/power",3,3,.001)},null,8,["model-value"]),n(u,null,{default:p(()=>t[3]||(t[3]=[c("Erträge")])),_:1}),n(d,{title:"Heute",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/get/daily_exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Dieser Monat",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/get/monthly_exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Dieses Jahr",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/get/yearly_exported",3,3,.001)},null,8,["model-value"])]),_:1})}const _e=w(ge,[["render",be],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/InverterSumCard.vue"]]);W.add(k,C,q,S);const he={name:"InverterCard",components:{FontAwesomeIcon:x},mixins:[y],props:{inverter:{type:Object,required:!0}},data(){return{statusLevel:["success","warning","danger"]}}},ve={style:{"white-space":"pre-wrap"}};function ye(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-text-input"),u=o("openwb-base-heading"),h=o("openwb-base-card");return r(),l(h,{subtype:"success",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","solar-panel"]}),c(" "+b(a.inverter.name)+" (ID: "+b(a.inverter.id)+") ",1)]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/pv/"+a.inverter.id+"/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/pv/"+a.inverter.id+"/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/pv/"+a.inverter.id+"/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[0]||(t[0]=c(" Modulmeldung:")),t[1]||(t[1]=g("br",null,null,-1)),g("span",ve,b(e.$store.state.mqtt["openWB/pv/"+a.inverter.id+"/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,{title:"Zählerstand",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/"+a.inverter.id+"/get/exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Leistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/pv/"+a.inverter.id+"/get/power",3,3,.001)},null,8,["model-value"]),n(u,null,{default:p(()=>t[2]||(t[2]=[c("Erträge")])),_:1}),n(d,{title:"Heute",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/"+a.inverter.id+"/get/daily_exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Dieser Monat",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/"+a.inverter.id+"/get/monthly_exported",3,3,.001)},null,8,["model-value"]),n(d,{title:"Dieses Jahr",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/pv/"+a.inverter.id+"/get/yearly_exported",3,3,.001)},null,8,["model-value"])]),_:1})}const we=w(he,[["render",ye],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/InverterCard.vue"]]);W.add(k,C,q,A);const We={name:"BatterySumCard",components:{FontAwesomeIcon:x},mixins:[y],data(){return{statusLevel:["success","warning","danger"]}}},xe={style:{"white-space":"pre-wrap"}};function Be(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-heading"),u=o("openwb-base-text-input"),h=o("openwb-base-number-input"),B=o("openwb-base-card");return r(),l(B,{subtype:"warning",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","car-battery"]}),t[0]||(t[0]=c(" Alle Speicher "))]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/bat/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/bat/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/bat/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[1]||(t[1]=c(" Modulmeldung:")),t[2]||(t[2]=g("br",null,null,-1)),g("span",xe,b(e.$store.state.mqtt["openWB/bat/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,null,{default:p(()=>t[3]||(t[3]=[c("Zählerstände")])),_:1}),n(u,{title:"Ladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/get/imported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Entladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/get/exported",3,3,.001)},null,8,["model-value"]),n(d,null,{default:p(()=>t[4]||(t[4]=[c("Tageswerte")])),_:1}),n(u,{title:"Ladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/get/daily_imported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Entladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/get/daily_exported",3,3,.001)},null,8,["model-value"]),n(d,null,{default:p(()=>t[5]||(t[5]=[c("Saldierte Werte")])),_:1}),n(u,{title:"Leistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/bat/get/power",3,3,.001)},null,8,["model-value"]),n(h,{title:"Ladestand",readonly:"",class:"text-right text-monospace",unit:"%","model-value":e.$store.state.mqtt["openWB/bat/get/soc"]},null,8,["model-value"])]),_:1})}const ke=w(We,[["render",Be],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/BatterySumCard.vue"]]);W.add(k,C,q,A);const Ce={name:"BatteryCard",components:{FontAwesomeIcon:x},mixins:[y],props:{battery:{type:Object,required:!0}},data(){return{statusLevel:["success","warning","danger"]}}},qe={style:{"white-space":"pre-wrap"}};function Te(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-heading"),u=o("openwb-base-text-input"),h=o("openwb-base-number-input"),B=o("openwb-base-card");return r(),l(B,{subtype:"warning",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","car-battery"]}),c(" "+b(a.battery.name)+" (ID: "+b(a.battery.id)+") ",1)]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/bat/"+a.battery.id+"/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/bat/"+a.battery.id+"/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/bat/"+a.battery.id+"/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[0]||(t[0]=c(" Modulmeldung:")),t[1]||(t[1]=g("br",null,null,-1)),g("span",qe,b(e.$store.state.mqtt["openWB/bat/"+a.battery.id+"/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,null,{default:p(()=>t[2]||(t[2]=[c("Aktuelle Werte")])),_:1}),n(u,{title:"Leistung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kW","model-value":e.formatNumberTopic("openWB/bat/"+a.battery.id+"/get/power",3,3,.001)},null,8,["model-value"]),n(h,{title:"Ladestand",readonly:"",class:"text-right text-monospace",unit:"%","model-value":e.$store.state.mqtt["openWB/bat/"+a.battery.id+"/get/soc"]},null,8,["model-value"]),n(d,null,{default:p(()=>t[3]||(t[3]=[c("Zählerstände")])),_:1}),n(u,{title:"Ladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/"+a.battery.id+"/get/imported",3,3,.001)},null,8,["model-value"]),n(u,{title:"Entladung",readonly:"",class:"text-right text-monospace",step:"0.001",unit:"kWh","model-value":e.formatNumberTopic("openWB/bat/"+a.battery.id+"/get/exported",3,3,.001)},null,8,["model-value"])]),_:1})}const Ie=w(Ce,[["render",Te],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/BatteryCard.vue"]]);W.add(k,C,q,z);const Ne={name:"RippleControlReceiverCard",components:{FontAwesomeIcon:x},mixins:[y],data(){return{mqttTopicsToSubscribe:["openWB/general/ripple_control_receiver/get/fault_state","openWB/general/ripple_control_receiver/get/fault_str","openWB/general/ripple_control_receiver/get/override_value","openWB/general/ripple_control_receiver/module"],statusLevel:["success","warning","danger"]}}},Pe={style:{"white-space":"pre-wrap"}};function $e(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-text-input"),u=o("openwb-base-card");return e.$store.state.mqtt["openWB/general/ripple_control_receiver/module"]&&e.$store.state.mqtt["openWB/general/ripple_control_receiver/module"].type?(r(),l(u,{key:0,subtype:"secondary",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{icon:["fas","tower-broadcast"]}),t[0]||(t[0]=c(" Steuerbare Verbrauchseinrichtung (RSE) "))]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[1]||(t[1]=c(" Modulmeldung:")),t[2]||(t[2]=g("br",null,null,-1)),g("span",Pe,b(e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,{title:"Status",readonly:"","model-value":e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/override_value"]==0?"Laden gesperrt":"Laden erlaubt ("+e.$store.state.mqtt["openWB/general/ripple_control_receiver/get/override_value"]+"%)"},null,8,["model-value"])]),_:1})):T("",!0)}const Le=w(Ne,[["render",$e],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/RippleControlReceiver.vue"]]);W.add(k,C,q,M);const Se={name:"VehicleCard",components:{FontAwesomeIcon:x},mixins:[y],props:{vehicle:{type:Object,required:!1,default:void 0},vehicleKey:{type:String,required:!0},vehicleName:{type:String,default:""}},data(){return{statusLevel:["success","warning","danger"]}},computed:{vehicleIndex:{get(){return parseInt(this.vehicleKey.match(/(?:\/)(\d+)(?=\/)/)[1])}},socTimestamp:{get(){return this.$store.state.mqtt["openWB/vehicle/"+this.vehicleIndex+"/get/soc_timestamp"]!==void 0?new Date(this.$store.state.mqtt["openWB/vehicle/"+this.vehicleIndex+"/get/soc_timestamp"]*1e3).toLocaleString():"-"}},socRange:{get(){return this.$store.state.mqtt["openWB/vehicle/"+this.vehicleIndex+"/get/range"]!==void 0?Math.round(this.$store.state.mqtt["openWB/vehicle/"+this.vehicleIndex+"/get/range"]):0}}}},Ae={style:{"white-space":"pre-wrap"}};function Oe(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-heading"),u=o("openwb-base-number-input"),h=o("openwb-base-text-input"),B=o("openwb-base-card");return r(),l(B,{subtype:"info",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","car"]}),c(" "+b(a.vehicleName)+" (ID: "+b(s.vehicleIndex)+") ",1)]),default:p(()=>[e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/fault_state"]!==void 0?(r(),l(m,{key:0,subtype:f.statusLevel[e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[0]||(t[0]=c(" Modulmeldung:")),t[1]||(t[1]=g("br",null,null,-1)),g("span",Ae,b(e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/fault_str"]),1)]),_:1},8,["subtype"])):T("",!0),n(d,null,{default:p(()=>t[2]||(t[2]=[c("Fahrzeugdaten")])),_:1}),n(u,{title:"Ladestand",readonly:"",class:"text-right text-monospace",unit:"%","model-value":e.$store.state.mqtt["openWB/vehicle/"+s.vehicleIndex+"/get/soc"]},null,8,["model-value"]),n(u,{title:"Reichweite",readonly:"",class:"text-right text-monospace",unit:"km","model-value":s.socRange},null,8,["model-value"]),n(h,{title:"Letzter Zeitstempel",readonly:"",class:"text-right text-monospace","model-value":s.socTimestamp},null,8,["model-value"])]),_:1})}const je=w(Se,[["render",Oe],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/VehicleCard.vue"]]);W.add(k,C,q,V);H.register(Z,F,K,G,J,Q,U,X,Y);const De={name:"ElectricityTariffCard",components:{ChartjsLine:ee,FontAwesomeIcon:x},mixins:[y],data(){return{mqttTopicsToSubscribe:["openWB/optional/et/provider","openWB/optional/et/get/fault_state","openWB/optional/et/get/fault_str","openWB/optional/et/get/prices"],statusLevel:["success","warning","danger"],chartDatasets:{datasets:[{label:"Stromtarif",unit:"ct/kWh",type:"line",stepped:!0,borderColor:"rgba(255, 0, 0, 0.7)",backgroundColor:"rgba(255, 10, 13, 0.3)",fill:!1,pointStyle:"circle",pointRadius:0,pointHoverRadius:4,cubicInterpolationMode:"monotone",hidden:!1,borderWidth:1,data:void 0,yAxisID:"y",parsing:{xAxisKey:"timestamp",yAxisKey:"price"}}]},chartOptions:{plugins:{title:{display:!1},tooltip:{enabled:!0},legend:{display:!1}},elements:{point:{radius:2}},responsive:!0,maintainAspectRatio:!1,interaction:{mode:"index",intersect:!1},scales:{x:{type:"time",time:{unit:"hour",text:"Zeit",maxTicksLimit:24},display:!0,title:{display:!0,text:"Uhrzeit"},ticks:{font:{size:12},maxTicksLimit:0},grid:{}},y:{position:"left",type:"linear",display:"auto",title:{font:{size:12},display:!0,text:"Preis [ct/kWh]"},grid:{},ticks:{font:{size:12},stepSize:.01,maxTicksLimit:11}}}}}},computed:{electricityTariffConfigured(){const e=this.$store.state.mqtt["openWB/optional/et/provider"];return e!==void 0?e.type!==null:!1},chartDataRead(){return this.chartDataObject.datasets[0].data!=null},chartDataObject(){if(this.$store.state.mqtt["openWB/optional/et/get/prices"]){var e=this.$store.state.mqtt["openWB/optional/et/get/prices"],t=[];for(const[f,s]of Object.entries(e))t.push({timestamp:f*1e3,price:s*1e5});const _=t.slice(-1)[0];t.push({timestamp:_.timestamp+(60*60-1)*1e3,price:_.price})}const a=this.chartDatasets;return a.datasets[0].data=t,a}}},Re={style:{"white-space":"pre-wrap"}},Ee={class:"openwb-chart"};function ze(e,t,a,_,f,s){const i=o("font-awesome-icon"),m=o("openwb-base-alert"),d=o("openwb-base-text-input"),u=o("chartjs-line"),h=o("openwb-base-card");return s.electricityTariffConfigured?(r(),l(h,{key:0,subtype:"secondary",collapsible:!0,collapsed:!0},{header:p(()=>[n(i,{"fixed-width":"",icon:["fas","ranking-star"]}),t[0]||(t[0]=c(" Variabler Stromtarif "))]),default:p(()=>[n(m,{subtype:f.statusLevel[e.$store.state.mqtt["openWB/optional/et/get/fault_state"]]},{default:p(()=>[e.$store.state.mqtt["openWB/optional/et/get/fault_state"]==1?(r(),l(i,{key:0,"fixed-width":"",icon:["fas","exclamation-triangle"]})):e.$store.state.mqtt["openWB/optional/et/get/fault_state"]==2?(r(),l(i,{key:1,"fixed-width":"",icon:["fas","times-circle"]})):(r(),l(i,{key:2,"fixed-width":"",icon:["fas","check-circle"]})),t[1]||(t[1]=c(" Modulmeldung:")),t[2]||(t[2]=g("br",null,null,-1)),g("span",Re,b(e.$store.state.mqtt["openWB/optional/et/get/fault_str"]),1)]),_:1},8,["subtype"]),n(d,{title:"Anbieter",readonly:"","model-value":e.$store.state.mqtt["openWB/optional/et/provider"].name},null,8,["model-value"]),g("div",Ee,[s.chartDataRead?(r(),l(u,{key:0,ref:"myChart",data:s.chartDataObject,options:f.chartOptions},null,8,["data","options"])):T("",!0)])]),_:1})):T("",!0)}const Me=w(De,[["render",ze],["__scopeId","data-v-f4769d2f"],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/status/ElectricityTariffCard.vue"]]);const Ve={name:"OpenwbStatusView",components:{ChargePointSumCard:oe,ChargePointCard:ie,CounterCard:me,InverterSumCard:_e,InverterCard:we,BatterySumCard:ke,BatteryCard:Ie,RippleControlReceiverCard:Le,VehicleCard:je,ElectricityTariffCard:Me},mixins:[y],data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/chargepoint/get/power","openWB/chargepoint/get/imported","openWB/chargepoint/get/exported","openWB/chargepoint/get/daily_imported","openWB/chargepoint/get/daily_exported","openWB/chargepoint/+/config","openWB/chargepoint/+/get/+","openWB/chargepoint/+/get/connected_vehicle/info","openWB/chargepoint/+/set/+","openWB/internal_chargepoint/+/data/phases_to_use","openWB/system/device/+/component/+/config","openWB/counter/+/get/+","openWB/pv/get/+","openWB/pv/+/get/+","openWB/bat/get/+","openWB/bat/+/get/+","openWB/vehicle/+/name","openWB/vehicle/+/get/+"]}},computed:{installedChargePoints:{get(){let e=this.getWildcardTopics("openWB/chargepoint/+/config"),t={};for(const[a,_]of Object.entries(e))(_.type==="internal_openwb"||this.$store.state.mqtt["openWB/general/extern"]===!1)&&(t[a]=_);return t}},numChargePointsInstalled:{get(){return Object.keys(this.installedChargePoints).length}},counterConfigs:{get(){return this.$store.state.mqtt["openWB/general/extern"]===!0?{}:this.filterComponentsByType(this.getWildcardTopics("openWB/system/device/+/component/+/config"),"counter")}},numInvertersInstalled:{get(){return Object.keys(this.inverterConfigs).length}},inverterConfigs:{get(){return this.$store.state.mqtt["openWB/general/extern"]===!0?{}:this.filterComponentsByType(this.getWildcardTopics("openWB/system/device/+/component/+/config"),"inverter")}},numBatteriesInstalled:{get(){return Object.keys(this.batteryConfigs).length}},batteryConfigs:{get(){return this.$store.state.mqtt["openWB/general/extern"]===!0?{}:this.filterComponentsByType(this.getWildcardTopics("openWB/system/device/+/component/+/config"),"bat")}},vehicleNames:{get(){return this.$store.state.mqtt["openWB/general/extern"]===!0?{}:this.getWildcardTopics("openWB/vehicle/+/name")}}},methods:{filterComponentsByType(e,t){return Object.keys(e).filter(a=>e[a].type.includes(t)).reduce((a,_)=>({...a,[_]:e[_]}),{})}}},He={class:"status"};function Ze(e,t,a,_,f,s){const i=o("charge-point-sum-card"),m=o("charge-point-card"),d=o("counter-card"),u=o("inverter-sum-card"),h=o("inverter-card"),B=o("battery-sum-card"),O=o("battery-card"),j=o("vehicle-card"),D=o("electricity-tariff-card"),R=o("ripple-control-receiver-card");return r(),I("div",He,[s.numChargePointsInstalled>1&&e.$store.state.mqtt["openWB/general/extern"]===!1?(r(),l(i,{key:0})):T("",!0),(r(!0),I(P,null,$(s.installedChargePoints,(v,N)=>(r(),l(m,{key:N,"installed-charge-point":v,"installed-charge-point-key":N},null,8,["installed-charge-point","installed-charge-point-key"]))),128)),(r(!0),I(P,null,$(s.counterConfigs,v=>(r(),l(d,{key:v.id,counter:v},null,8,["counter"]))),128)),s.numInvertersInstalled>1&&e.$store.state.mqtt["openWB/general/extern"]===!1?(r(),l(u,{key:1})):T("",!0),(r(!0),I(P,null,$(s.inverterConfigs,v=>(r(),l(h,{key:v.id,inverter:v},null,8,["inverter"]))),128)),s.numBatteriesInstalled>1&&e.$store.state.mqtt["openWB/general/extern"]===!1?(r(),l(B,{key:2})):T("",!0),(r(!0),I(P,null,$(s.batteryConfigs,v=>(r(),l(O,{key:v.id,battery:v},null,8,["battery"]))),128)),(r(!0),I(P,null,$(s.vehicleNames,(v,N)=>(r(),l(j,{key:N,"vehicle-key":N,"vehicle-name":v},null,8,["vehicle-key","vehicle-name"]))),128)),n(D),n(R)])}const tt=w(Ve,[["render",Ze],["__scopeId","data-v-051028a3"],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/Status.vue"]]);export{tt as default};