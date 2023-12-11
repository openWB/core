import{_ as B,C as T}from"./index-f6fb85ca.js";import{_ as W}from"./dynamic-import-helper-be004503.js";import{l as $,V as S,W as q,F as V}from"./vendor-fortawesome-773fe9b8.js";import{_ as k,p as s,k as u,l as b,y as g,L as o,u as l,x as m,A as e,q as p,a0 as A,a1 as z,G as C,z as r}from"./vendor-20bb207d.js";import"./vendor-bootstrap-d275de6c.js";import"./vendor-jquery-89b63fca.js";import"./vendor-axios-13ef03ae.js";import"./vendor-sortablejs-ad1d2cc8.js";const I={name:"DisplayThemeFallback",emits:["update:configuration"],props:{displayTheme:{type:Object,required:!0}},methods:{updateConfiguration(t,n=void 0){this.$emit("update:configuration",{value:t,object:n})}}},O={class:"display-theme-fallback"},N={key:1};function F(t,n,i,h,_,d){const f=s("openwb-base-alert"),v=s("openwb-base-textarea");return u(),b("div",O,[Object.keys(i.displayTheme.configuration).length==0?(u(),g(f,{key:0,subtype:"info"},{default:o(()=>[l(' Das Display-Theme "'+m(i.displayTheme.name)+'" bietet keine Einstellungen. ',1)]),_:1})):(u(),b("div",N,[e(f,{subtype:"warning"},{default:o(()=>[l(' Es wurde keine Konfigurationsseite für das Display-Theme "'+m(i.displayTheme.name)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),e(v,{title:"Konfiguration",subtype:"json","model-value":i.displayTheme.configuration,"onUpdate:modelValue":n[0]||(n[0]=c=>d.updateConfiguration(c,"configuration"))},{help:o(()=>[l(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),e(f,{subtype:"info"},{default:o(()=>[p("pre",null,m(JSON.stringify(i.displayTheme.configuration,void 0,2)),1)]),_:1})]))])}const P=k(I,[["render",F],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeFallback.vue"]]);$.add(S,q);const j={name:"OpenwbDisplayThemeProxy",emits:["update:configuration"],props:{displayTheme:{type:Object,required:!0}},components:{FontAwesomeIcon:V},computed:{myComponent(){return console.debug(`loading display theme: ${this.displayTheme.type}`),A({loader:()=>W(Object.assign({"./cards/displayTheme.vue":()=>B(()=>import("./displayTheme-399029a5.js"),["assets/displayTheme-399029a5.js","assets/vendor-20bb207d.js","assets/vendor-sortablejs-ad1d2cc8.js","assets/vendor-7b9e30aa.css"])}),`./${this.displayTheme.type}/displayTheme.vue`),errorComponent:P})}},methods:{updateConfiguration(t){this.$emit("update:configuration",t)}}};function M(t,n,i,h,_,d){const f=s("font-awesome-icon"),v=s("openwb-base-alert"),c=s("openwb-base-heading");return u(),b(C,null,[i.displayTheme.official?(u(),g(v,{key:0,subtype:"success"},{default:o(()=>[e(f,{"fixed-width":"",icon:["fas","certificate"]}),l(' Das ausgewählte Display Theme "'+m(i.displayTheme.name)+'" wird von openWB gepflegt. ',1)]),_:1})):(u(),g(v,{key:1,subtype:"info"},{default:o(()=>[e(f,{"fixed-width":"",icon:["fas","people-group"]}),l(' Das ausgewählte Display Theme "'+m(i.displayTheme.name)+'" wird in unserer Community gepflegt. Rückfragen oder Probleme bitte im Forum diskutieren. ',1)]),_:1})),e(c,null,{default:o(()=>[l(' Einstellungen für Display Theme "'+m(i.displayTheme.name)+'" ',1)]),_:1}),(u(),g(z(d.myComponent),{displayTheme:i.displayTheme,"onUpdate:configuration":n[0]||(n[0]=D=>d.updateConfiguration(D))},null,40,["displayTheme"]))],64)}const U=k(j,[["render",M],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeProxy.vue"]]),J={name:"OpenwbOptionalComponents",mixins:[T],components:{OpenwbDisplayThemeProxy:U},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/chargepoint/+/config","openWB/chargepoint/+/get/rfid","openWB/chargepoint/+/get/rfid_timestamp","openWB/chargepoint/+/set/rfid","openWB/optional/rfid/active","openWB/optional/led/active","ToDo/optional/led/instant_blocked","ToDo/optional/led/pv_blocked","ToDo/optional/led/scheduled_blocked","ToDo/optional/led/standby_blocked","ToDo/optional/led/stop_blocked","ToDo/optional/led/instant","ToDo/optional/led/pv","ToDo/optional/led/scheduled","ToDo/optional/led/standby","ToDo/optional/led/stop","openWB/optional/int_display/active","openWB/optional/int_display/standby","openWB/optional/int_display/rotation","openWB/optional/int_display/on_if_plugged_in","openWB/optional/int_display/pin_active","openWB/optional/int_display/pin_code","openWB/optional/int_display/theme","openWB/optional/int_display/only_local_charge_points","openWB/system/configurable/display_themes","openWB/optional/et/active","openWB/optional/et/config/provider","openWB/optional/et/config/max_price"],tempIdTagList:{}}},computed:{idTagList(){return Object.values(this.updateIdTagList())},displayThemeList(){return this.$store.state.mqtt["openWB/system/configurable/display_themes"]},displayThemeGroupList(){let t=[{label:"openWB",options:[]},{label:"Community",options:[]}];return this.displayThemeList.forEach(n=>{n.official===!0?t[0].options.push(n):t[1].options.push(n)}),t}},methods:{getIdFromTopic(t){return t.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g,"")},updateIdTagList(){return Object.entries(this.getWildcardTopics("^openWB/chargepoint/[^+/]+/[gs]et/rfid$",!0)).forEach(t=>{t[1]!==null&&(this.tempIdTagList[t[1]]=`${t[1]} (${t[0].includes("/set/")?"zugewiesen":"erfasst"} an ${this.getChargePointName(this.getIdFromTopic(t[0]))})`)}),this.tempIdTagList},getChargePointName(t){return this.$store.state.mqtt["openWB/chargepoint/"+t+"/config"]?this.$store.state.mqtt["openWB/chargepoint/"+t+"/config"].name:"Ladepunkt "+t},getDisplayThemeDefaults(t){const n=this.displayThemeList.find(i=>i.value==t);return Object.prototype.hasOwnProperty.call(n,"defaults")?{...JSON.parse(JSON.stringify(n.defaults))}:(console.warn("no default configuration found for display theme type!",t),{})},updateSelectedDisplayTheme(t){this.updateState("openWB/optional/int_display/theme",this.getDisplayThemeDefaults(t))},updateConfiguration(t,n){console.debug("updateConfiguration",t,n),this.updateState(t,n.value,n.object)}}},H={class:"optionalComponents"},R={name:"optionalComponentsForm"},G=p("ul",null,[p("li",null," Über einen in der openWB verbauten RFID-Reader (optional, z.B. anhand des Lieferscheins prüfen). "),p("li",null," Durch die automatische Erkennung an einer openWB Pro (muss in den Einstellungen aktiviert werden). "),p("li",null," Durch manuelle Eingabe einer ID am Display einer openWB. ")],-1),Z={key:0},K=p("br",null,null,-1),Q=p("br",null,null,-1),X=["innerHTML"],Y={key:0},tt=p("br",null,null,-1),nt=p("hr",null,null,-1),et={key:1},ot=p("hr",null,null,-1),lt={key:2},at=p("hr",null,null,-1),it=p("hr",null,null,-1),st={key:0};function ut(t,n,i,h,_,d){const f=s("openwb-base-button-group-input"),v=s("openwb-base-alert"),c=s("openwb-base-textarea"),D=s("openwb-base-card"),x=s("openwb-base-heading"),y=s("openwb-base-range-input"),L=s("openwb-base-select-input"),E=s("openwb-display-theme-proxy"),w=s("openwb-base-submit-buttons");return u(),b("div",H,[p("form",R,[e(D,{title:"Identifikation von Fahrzeugen"},{default:o(()=>[e(f,{title:"Identifikation aktivieren","model-value":t.$store.state.mqtt["openWB/optional/rfid/active"],"onUpdate:modelValue":n[0]||(n[0]=a=>t.updateState("openWB/optional/rfid/active",a)),buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}]},{help:o(()=>[l(" Die Identifikation von Fahrzeugen kann auf mehreren Wegen erfolgen: "),G]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/rfid/active"]===!0?(u(),b("div",Z,[e(v,{subtype:"info",class:"mb-1"},{default:o(()=>[l(" Die ID-Tags, die an dem jeweiligen Ladepunkt gültig sind, müssen in dem Ladepunkt-Profil hinterlegt werden. Die ID-Tags müssen auch in den Einstellungen der Fahrzeuge diesen zugeordnet werden."),K,l(" Es kann zuerst das Fahrzeug angesteckt und dann der ID-Tag erfasst werden oder anders herum. Im letzten Fall muss innerhalb von 5 Minuten ein Fahrzeug angesteckt werden, sonst wird der ID-Tag verworfen. Das Fahrzeug wird erst nach dem Anstecken zugeordnet."),Q,p("span",{innerHTML:t.$store.state.text.rfidWiki},null,8,X)]),_:1}),e(c,{title:"Erkannte ID-Tags",readonly:"",disabled:"","model-value":d.idTagList.join(`
`)},{help:o(()=>[l(" Solange diese Seite geöffnet ist, werden alle erfassten ID-Tags in dieser Liste aufgeführt. ")]),_:1},8,["model-value"])])):r("v-if",!0)]),_:1}),r(` <openwb-base-card title="LED-Ausgänge">
				<openwb-base-button-group-input
					title="LED-Ausgänge aktivieren"
					:model-value="
						$store.state.mqtt['openWB/optional/led/active']
					"
					@update:model-value="
						updateState('openWB/optional/led/active', $event)
					"
					:buttons="[
						{
							buttonValue: false,
							text: 'Aus',
							class: 'btn-outline-danger',
						},
						{
							buttonValue: true,
							text: 'An',
							class: 'btn-outline-success',
						},
					]"
				/>
				<div
					v-if="
						$store.state.mqtt['openWB/optional/led/active'] === true
					"
				>
					<openwb-base-alert subtype="info">
						ToDo: Informationen zu den verwendeten GPOIs ergänzen!
					</openwb-base-alert>
					<hr />
					<div
						v-if="
							$store.state.mqtt['openWB/general/extern'] === true
						"
					>
						<openwb-base-alert subtype="info">
							Diese Einstellungen sind nicht verfügbar, solange
							sich diese openWB im Steuerungsmodus "secondary"
							befindet.<br />
							Das Verhalten der LEDs wird durch die übergeordnete
							openWB festgelegt.
						</openwb-base-alert>
					</div>
					<div
						v-if="
							$store.state.mqtt['openWB/general/extern'] === false
						"
					>
						<openwb-base-heading>
							Ladung nicht freigegeben
						</openwb-base-heading>
						<openwb-base-select-input
							title="Sofortladen"
							:model-value="
								$store.state.mqtt[
									'ToDo/optional/led/instant_blocked'
								]
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/instant_blocked',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="PV-Laden"
							:model-value="
								$store.state.mqtt[
									'ToDo/optional/led/pv_blocked'
								]
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/pv_blocked',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Zielladen"
							:model-value="
								$store.state.mqtt[
									'ToDo/optional/led/scheduled_blocked'
								]
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/scheduled_blocked',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Standby"
							:model-value="
								$store.state.mqtt[
									'ToDo/optional/led/standby_blocked'
								]
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/standby_blocked',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Stop"
							:model-value="
								$store.state.mqtt[
									'ToDo/optional/led/stop_blocked'
								]
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/stop_blocked',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<hr />
						<openwb-base-heading>
							Ladung freigegeben
						</openwb-base-heading>
						<openwb-base-select-input
							title="Sofortladen"
							:model-value="
								$store.state.mqtt['ToDo/optional/led/instant']
							"
							@update:model-value="
								updateState('ToDo/optional/led/instant', $event)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="PV-Laden"
							:model-value="
								$store.state.mqtt['ToDo/optional/led/pv']
							"
							@update:model-value="
								updateState('ToDo/optional/led/pv', $event)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Zielladen"
							:model-value="
								$store.state.mqtt['ToDo/optional/led/scheduled']
							"
							@update:model-value="
								updateState(
									'ToDo/optional/led/scheduled',
									$event
								)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Standby"
							:model-value="
								$store.state.mqtt['ToDo/optional/led/standby']
							"
							@update:model-value="
								updateState('ToDo/optional/led/standby', $event)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
						<openwb-base-select-input
							title="Stop"
							:model-value="
								$store.state.mqtt['ToDo/optional/led/stop']
							"
							@update:model-value="
								updateState('ToDo/optional/led/stop', $event)
							"
							:options="[
								{
									value: ['off', 'off', 'off'],
									text: 'Alle aus',
								},
							]"
							:groups="[
								{
									label: 'Dauernd an',
									options: [
										{
											value: ['on', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'on', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'on'],
											text: 'LED 3',
										},
										{
											value: ['on', 'on', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['on', 'off', 'on'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'on', 'on'],
											text: 'LEDs 2+3',
										},
										{
											value: ['on', 'on', 'on'],
											text: 'alle',
										},
									],
								},
								{
									label: 'Blinkend',
									options: [
										{
											value: ['blink', 'off', 'off'],
											text: 'LED 1',
										},
										{
											value: ['off', 'blink', 'off'],
											text: 'LED 2',
										},
										{
											value: ['off', 'off', 'blink'],
											text: 'LED 3',
										},
										{
											value: ['blink', 'blink', 'off'],
											text: 'LEDs 1+2',
										},
										{
											value: ['blink', 'off', 'blink'],
											text: 'LEDs 1+3',
										},
										{
											value: ['off', 'blink', 'blink'],
											text: 'LEDs 2+3',
										},
										{
											value: ['blink', 'blink', 'blink'],
											text: 'alle',
										},
									],
								},
							]"
						/>
					</div>
				</div>
			</openwb-base-card> `),e(D,{title:"Display (intern oder extern)"},{default:o(()=>[e(f,{title:"Integriertes Display","model-value":t.$store.state.mqtt["openWB/optional/int_display/active"],"onUpdate:modelValue":n[1]||(n[1]=a=>t.updateState("openWB/optional/int_display/active",a)),buttons:[{buttonValue:!1,text:"Nein",class:"btn-outline-danger"},{buttonValue:!0,text:"Ja",class:"btn-outline-success"}]},{help:o(()=>[l(' Je nach Bestellung kann die openWB mit oder ohne Display geliefert worden sein. Auch die Variante "Standalone" bietet beide Optionen. Bitte prüfe zuerst die Hardwareausstattung deiner openWB (z.B. Lieferschein). ')]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/int_display/active"]==!0?(u(),b("div",Y,[e(f,{title:"Orientierung","model-value":t.$store.state.mqtt["openWB/optional/int_display/rotation"],"onUpdate:modelValue":n[2]||(n[2]=a=>t.updateState("openWB/optional/int_display/rotation",a)),buttons:[{buttonValue:0,text:"0°"},{buttonValue:90,text:"90°"},{buttonValue:180,text:"180°"},{buttonValue:270,text:"270°"}]},{help:o(()=>[l(" Mit dieser Einstellung kann das Display im Uhrzeigersinn gedreht werden, falls erforderlich. Nach einer Änderung ist ein Neustart erforderlich!"),tt,l(" Diese Einstellung erfordert ein Raspberry Pi Display. Anzeigen, welche über HDMI angeschlossen sind, werden nicht unterstützt. ")]),_:1},8,["model-value"]),nt,e(x,null,{default:o(()=>[l(" Display Standby ")]),_:1}),e(y,{title:"Ausschaltzeit",min:0,max:12,step:1,"model-value":t.$store.state.mqtt["openWB/optional/int_display/standby"],"onUpdate:modelValue":n[3]||(n[3]=a=>t.updateState("openWB/optional/int_display/standby",a)),unit:"Sek",labels:[{label:"Immer an",value:0},{label:5,value:5},{label:10,value:10},{label:15,value:15},{label:30,value:30},{label:45,value:45},{label:"1 Min",value:60},{label:"1,5 Min",value:90},{label:"2 Min",value:120},{label:"3 Min",value:180},{label:"4 Min",value:240},{label:"5 Min",value:300},{label:"10 Min",value:600}]},{help:o(()=>[l(" Hier kann eine Zeitspanne angegeben werden, nach der das Display ausgeschaltet wird. ")]),_:1},8,["model-value"]),r(` <openwb-base-button-group-input
						v-if="
							$store.state.mqtt[
								'openWB/optional/int_display/standby'
							] != 0
						"
						title="Automatisch einschalten"
						:model-value="
							$store.state.mqtt[
								'openWB/optional/int_display/on_if_plugged_in'
							]
						"
						@update:model-value="
							updateState(
								'openWB/optional/int_display/on_if_plugged_in',
								$event
							)
						"
						:buttons="[
							{
								buttonValue: false,
								text: 'Nein',
								class: 'btn-outline-danger',
							},
							{
								buttonValue: true,
								text: 'Ja',
								class: 'btn-outline-success',
							},
						]"
					>
						<template #help>
							Wird diese Funktion aktiviert, dann schaltet
							sich das Display automatisch ein, wenn ein
							Fahrzeug angesteckt wird.
						</template>
					</openwb-base-button-group-input> `)])):r("v-if",!0),t.$store.state.mqtt["openWB/general/extern"]===!0?(u(),b("div",et,[r(` <hr />
					<openwb-base-select-input
						title="Art der Anzeige"
						:options="[
							{
								value: 'primary',
								text: 'Primary openWB',
							},
							{
								value: 'local',
								text: 'diese(r) Ladepunkt(e)',
							},
						]"
						:model-value="
							$store.state.mqtt[
								'openWB/general/extern_display_mode'
							]
						"
						@update:model-value="
							updateState(
								'openWB/general/extern_display_mode',
								$event
							)
						"
					>
						<template #help>
							Wird hier "Primary openWB" ausgewählt, dann ist die
							Darstellung identisch zum Display der regelnden
							openWB. Alle Anzeigen und Änderungen sind möglich.
							Je nach Einstellung in der primary openWB werden die
							angezeigten Ladepunkte auf den/die an dieser openWB
							vorhandenen Ladepunkte beschränkt.<br />
							Die Option "diese(r) Ladepunkt(e)" ermöglicht eine
							minimale Anzeige und Bedienung der an dieser openWB
							verfügbaren Ladepunkte.
						</template>
					</openwb-base-select-input> `),ot,e(v,{subtype:"info"},{default:o(()=>[l(' Weitere Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(u(),b("div",lt,[r(` <hr />
					<openwb-base-heading>PIN-Sperre</openwb-base-heading>
					<openwb-base-button-group-input
						title="Display mit PIN schützen"
						:model-value="
							$store.state.mqtt[
								'openWB/optional/int_display/pin_active'
							]
						"
						@update:model-value="
							updateState(
								'openWB/optional/int_display/pin_active',
								$event
							)
						"
						:buttons="[
							{
								buttonValue: false,
								text: 'Nein',
								class: 'btn-outline-danger',
							},
							{
								buttonValue: true,
								text: 'Ja',
								class: 'btn-outline-success',
							},
						]"
					/>
					<div
						v-if="
							$store.state.mqtt[
								'openWB/optional/int_display/pin_active'
							] == true
						"
					>
						<openwb-base-text-input
							title="PIN-Code"
							:model-value="
								$store.state.mqtt[
									'openWB/optional/int_display/pin_code'
								]
							"
							@update:model-value="
								updateState(
									'openWB/optional/int_display/pin_code',
									$event
								)
							"
							subtype="password"
							pattern="[0-9]{4}"
						>
							<template #help>
								Der PIN-Code muss vierstellig sein und darf nur
								Zahlen enthalten.
							</template>
						</openwb-base-text-input>
					</div> `),at,e(f,{title:"Ladepunkte auf externen openWB","model-value":t.$store.state.mqtt["openWB/optional/int_display/only_local_charge_points"],"onUpdate:modelValue":n[4]||(n[4]=a=>t.updateState("openWB/optional/int_display/only_local_charge_points",a)),buttons:[{buttonValue:!1,text:"Alle",class:"btn-outline-danger"},{buttonValue:!0,text:"Nur Lokale",class:"btn-outline-success"}]},{help:o(()=>[l(" Hiermit kann festgelegt werden, ob an angebundenen externen openWB alle oder nur die jeweils lokalen Ladepunkte angezeigt werden sollen. ")]),_:1},8,["model-value"]),it,t.$store.state.mqtt["openWB/optional/int_display/theme"]!==void 0?(u(),b("div",st,[e(L,{class:"mb-2",title:"Theme des Displays",groups:d.displayThemeGroupList,"model-value":t.$store.state.mqtt["openWB/optional/int_display/theme"].type,"onUpdate:modelValue":n[5]||(n[5]=a=>d.updateSelectedDisplayTheme(a))},{help:o(()=>[l(" Hier können unterschiedliche Display-Anzeigen, s.g. Themes, ausgewählt werden. Die Anzahl der Themes wird sich mit zukünftigen Releases erhöhen. ")]),_:1},8,["groups","model-value"]),t.$store.state.mqtt["openWB/optional/int_display/theme"].type?(u(),g(E,{key:0,displayTheme:t.$store.state.mqtt["openWB/optional/int_display/theme"],"onUpdate:configuration":n[6]||(n[6]=a=>d.updateConfiguration("openWB/optional/int_display/theme",a))},null,8,["displayTheme"])):r("v-if",!0)])):r("v-if",!0)]))]),_:1}),r(` <openwb-base-card title="Variable Stromtarife">
				<div v-if="$store.state.mqtt['openWB/general/extern'] === true">
					<openwb-base-alert subtype="info">
						Diese Einstellungen sind nicht verfügbar, solange sich
						diese openWB im Steuerungsmodus "secondary" befindet.
					</openwb-base-alert>
				</div>
				<div v-else>
					<openwb-base-button-group-input
						title="Stromtarife aktivieren"
						:model-value="
							$store.state.mqtt['openWB/optional/et/active']
						"
						@update:model-value="
							updateState('openWB/optional/et/active', $event)
						"
						:buttons="[
							{
								buttonValue: false,
								text: 'Aus',
								class: 'btn-outline-danger',
							},
							{
								buttonValue: true,
								text: 'An',
								class: 'btn-outline-success',
							},
						]"
					/>
					<div
						v-if="
							$store.state.mqtt['openWB/optional/et/active'] ==
							true
						"
					>
						<openwb-base-text-input
							title="Anbieter"
							subtype="json"
							disabled="disabled"
							:model-value="
								$store.state.mqtt[
									'openWB/optional/et/config/provider'
								]
							"
							@update:model-value="
								updateState(
									'openWB/optional/et/config/provider',
									$event
								)
							"
						>
							<template #help>Nur zur Info.</template>
						</openwb-base-text-input>
						<openwb-base-range-input
							title="Maximaler Strompreis"
							:min="-30"
							:max="30"
							:step="0.1"
							:model-value="
								$store.state.mqtt[
									'openWB/optional/et/config/max_price'
								]
							"
							@update:model-value="
								updateState(
									'openWB/optional/et/config/max_price',
									$event
								)
							"
							unit="ct"
						/>
					</div>
				</div>
			</openwb-base-card> `),e(w,{formName:"optionalComponentsForm",onSave:n[7]||(n[7]=a=>t.$emit("save")),onReset:n[8]||(n[8]=a=>t.$emit("reset")),onDefaults:n[9]||(n[9]=a=>t.$emit("defaults"))})])])}const gt=k(J,[["render",ut],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/OptionalComponents.vue"]]);export{gt as default};
