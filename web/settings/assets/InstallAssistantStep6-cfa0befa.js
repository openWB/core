import{C as d}from"./index-e2dbf7bf.js";import u from"./InstallAssistantStepTemplate-c95c4891.js";import{b as p}from"./ChargePointInstallation-1b33cf58.js";import{_ as m,u as a,k as g,z as h,E as r,x as n,G as w}from"./vendor-06e11d0e.js";import"./vendor-fortawesome-3d19d475.js";import"./vendor-bootstrap-4263d7eb.js";import"./vendor-jquery-9fc083b4.js";import"./vendor-axios-22b906fb.js";import"./vendor-sortablejs-0bb60e5b.js";import"./dynamic-import-helper-be004503.js";const P={name:"InstallAssistantStep6",components:{InstallAssistantStepTemplate:u,ChargePointInstallationView:p},mixins:[d],emits:["save","reset","defaults","sendCommand","switchPage","endAssistant"],data:()=>({mqttTopicsToSubscribe:[]}),methods:{nextPage(){this.$emit("switchPage",7)},previousPage(){this.$emit("switchPage",5)},endAssistant(){this.$emit("endAssistant")}}};function f(t,e,c,k,b,i){const o=a("ChargePointInstallationView"),l=a("InstallAssistantStepTemplate");return g(),h(l,{title:"5. Einrichten der Ladepunkte (openWB als primary)",onNextPage:i.nextPage,onPreviousPage:i.previousPage,onEndAssistant:i.endAssistant},{help:r(()=>e[4]||(e[4]=[n("p",null,' Enthält die steuernde openWB (primary) Ladetechnik, wird bei "Verfügbare Ladepunkte" Interne openWB ausgewählt. Weitere LP werden im primary als Externe openWB (als secondary konfigurierte openWB) oder andere WB-Typen wie Pro, Satellit eingebunden. ',-1),n("p",null,"Bei openWBs ab Werk kann hier bereits ein Ladepunkt eingetragen sein.",-1),n("p",null," Nachfolgend werden die Eigenschaften des Ladepunktes wie IP-Adresse und elektrischer Anschluss definiert. Die meisten openWB werden 3-phasig angeschlossen! Bei mehreren Ladepunkten ist auf phasenrotierten Anschluss der openWB-Zuleitung zu achten! Abschließend wird die korrekte Zuordnung der Phase 1 des Ladekabels zur zugehörigen EVU-Zählerphase konfiguriert. Dies ist sehr wichtig, um optimales Lastmanagement sicherzustellen! ",-1),n("p",null," Tipp zur Zuordnung: Verwende ein nur 1-phasig ladendes Auto (z.B. Hybrid) oder stelle bei openWB mit 1p3p-Phasenumschaltung temporär unter Sofortladen (s. Einstellungen -> Ladeeinstellungen) auf einphasig, um eine 1-phasige Ladung zu erzwingen. Gehe unter Status und vergleiche die Leistungen bzw. Ströme der 3 Phasen am EVU-Zähler (rot) beim und nach dem Autoladen (Sofortladen mit 16A/ Stop). Diejenige EVU-Phase, die deutlich erhöhte Werte anzeigt, ist die auszuwählende EVU-Phase. ",-1),n("p",null," Im grauen Menü Ladepunkt-Profile können neben dem Standard-Ladepunkt-Profil auch weitere Ladepunkt-Profile, die andere WB-Typen abbilden, erstellt werden. Dort sind Eintragungen bzgl. des Ladepunkt-Maximalstroms bei einer Phase bzw. mehreren Phasen vorzunehmen. Die Profile werden abschließend im jeweiligen blauen Ladepunkt mittels Auswahlmenü zugeordnet. ",-1),n("p",{class:"font-weight-bold"},"Änderungen werden nur durch Klicken auf Speichern wirksam!",-1)])),content:r(()=>[w(o,{"install-assistant-active":!0,onSendCommand:e[0]||(e[0]=s=>t.$emit("sendCommand",s)),onSave:e[1]||(e[1]=s=>t.$emit("save")),onReset:e[2]||(e[2]=s=>t.$emit("reset")),onDefaults:e[3]||(e[3]=s=>t.$emit("defaults"))})]),_:1},8,["onNextPage","onPreviousPage","onEndAssistant"])}const $=m(P,[["render",f],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/install_assistant/InstallAssistantStep6.vue"]]);export{$ as default};