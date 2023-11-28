import{_ as w,C as B}from"./index-a961d15f.js";import{_ as W}from"./dynamic-import-helper-be004503.js";import{l as T,R as $,S,F as q}from"./vendor-fortawesome-8ba39b16.js";import{_ as k,p as s,k as i,l as r,y as c,L as o,u as a,x as D,A as e,q as f,a0 as A,a1 as V,G as z,z as d}from"./vendor-20bb207d.js";import"./vendor-bootstrap-d275de6c.js";import"./vendor-jquery-89b63fca.js";import"./vendor-axios-13ef03ae.js";import"./vendor-sortablejs-ad1d2cc8.js";const C={name:"DisplayThemeFallback",emits:["update:configuration"],props:{displayTheme:{type:Object,required:!0}},methods:{updateConfiguration(t,n=void 0){this.$emit("update:configuration",{value:t,object:n})}}},O={class:"display-theme-fallback"},I={key:1};function F(t,n,u,g,x,b){const p=s("openwb-base-alert"),v=s("openwb-base-textarea");return i(),r("div",O,[Object.keys(u.displayTheme.configuration).length==0?(i(),c(p,{key:0,subtype:"info"},{default:o(()=>[a(' Das Display-Theme "'+D(u.displayTheme.name)+'" bietet keine Einstellungen. ',1)]),_:1})):(i(),r("div",I,[e(p,{subtype:"warning"},{default:o(()=>[a(' Es wurde keine Konfigurationsseite für das Display-Theme "'+D(u.displayTheme.name)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),e(v,{title:"Konfiguration",subtype:"json","model-value":u.displayTheme.configuration,"onUpdate:modelValue":n[0]||(n[0]=m=>b.updateConfiguration(m,"configuration"))},{help:o(()=>[a(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),e(p,{subtype:"info"},{default:o(()=>[f("pre",null,D(JSON.stringify(u.displayTheme.configuration,void 0,2)),1)]),_:1})]))])}const N=k(C,[["render",F],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeFallback.vue"]]);T.add($,S);const P={name:"OpenwbDisplayThemeProxy",emits:["update:configuration"],props:{displayTheme:{type:Object,required:!0}},components:{FontAwesomeIcon:q},computed:{myComponent(){return console.debug(`loading display theme: ${this.displayTheme.type}`),A({loader:()=>W(Object.assign({"./cards/displayTheme.vue":()=>w(()=>import("./displayTheme-6f1283bf.js"),["assets/displayTheme-6f1283bf.js","assets/vendor-20bb207d.js","assets/vendor-sortablejs-ad1d2cc8.js","assets/vendor-7b9e30aa.css"])}),`./${this.displayTheme.type}/displayTheme.vue`),errorComponent:N})}},methods:{updateConfiguration(t){this.$emit("update:configuration",t)}}};function R(t,n,u,g,x,b){const p=s("font-awesome-icon"),v=s("openwb-base-alert");return i(),r(z,null,[u.displayTheme.official?(i(),c(v,{key:0,subtype:"success"},{default:o(()=>[e(p,{"fixed-width":"",icon:["fas","certificate"]}),a(" Das ausgewählte Theme wird von openWB gepflegt. ")]),_:1})):(i(),c(v,{key:1,subtype:"info"},{default:o(()=>[e(p,{"fixed-width":"",icon:["fas","people-group"]}),a(" Das ausgewählte Theme wird in unserer Community gepflegt. Rückfragen oder Probleme bitte im Forum diskutieren. ")]),_:1})),(i(),c(V(b.myComponent),{displayTheme:u.displayTheme,"onUpdate:configuration":n[0]||(n[0]=m=>b.updateConfiguration(m))},null,40,["displayTheme"]))],64)}const M=k(P,[["render",R],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeProxy.vue"]]),j={name:"OpenwbOptionalComponents",mixins:[B],components:{OpenwbDisplayThemeProxy:M},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/optional/rfid/active","openWB/optional/led/active","ToDo/optional/led/instant_blocked","ToDo/optional/led/pv_blocked","ToDo/optional/led/scheduled_blocked","ToDo/optional/led/standby_blocked","ToDo/optional/led/stop_blocked","ToDo/optional/led/instant","ToDo/optional/led/pv","ToDo/optional/led/scheduled","ToDo/optional/led/standby","ToDo/optional/led/stop","openWB/optional/int_display/active","openWB/optional/int_display/standby","openWB/optional/int_display/rotation","openWB/optional/int_display/on_if_plugged_in","openWB/optional/int_display/pin_active","openWB/optional/int_display/pin_code","openWB/optional/int_display/theme","openWB/optional/int_display/only_local_charge_points","openWB/system/configurable/display_themes","openWB/optional/et/active","openWB/optional/et/config/provider","openWB/optional/et/config/max_price"]}},computed:{displayThemeList:{get(){return this.$store.state.mqtt["openWB/system/configurable/display_themes"]}},displayThemeGroupList:{get(){let t=[{label:"openWB",options:[]},{label:"Community",options:[]}];return this.displayThemeList.forEach(n=>{n.official===!0?t[0].options.push(n):t[1].options.push(n)}),t}}},methods:{getDisplayThemeDefaults(t){const n=this.displayThemeList.find(u=>u.value==t);return Object.prototype.hasOwnProperty.call(n,"defaults")?{...JSON.parse(JSON.stringify(n.defaults))}:(console.warn("no default configuration found for display theme type!",t),{})},updateSelectedDisplayTheme(t){this.updateState("openWB/optional/int_display/theme",this.getDisplayThemeDefaults(t))},updateConfiguration(t,n){console.debug("updateConfiguration",t,n),this.updateState(t,n.value,n.object)}}},U={class:"optionalComponents"},H={name:"optionalComponentsForm"},J={key:0},G=f("br",null,null,-1),Z=f("br",null,null,-1),K=["innerHTML"],Q={key:0},X=f("br",null,null,-1),Y=f("hr",null,null,-1),tt={key:1},nt=f("hr",null,null,-1),et={key:2},ot=f("hr",null,null,-1),lt=f("hr",null,null,-1),at={key:0};function it(t,n,u,g,x,b){const p=s("openwb-base-button-group-input"),v=s("openwb-base-alert"),m=s("openwb-base-card"),_=s("openwb-base-heading"),h=s("openwb-base-range-input"),y=s("openwb-base-select-input"),L=s("openwb-display-theme-proxy"),E=s("openwb-base-submit-buttons");return i(),r("div",U,[f("form",H,[e(m,{title:"RFID"},{default:o(()=>[e(p,{title:"RFID aktivieren","model-value":t.$store.state.mqtt["openWB/optional/rfid/active"],"onUpdate:modelValue":n[0]||(n[0]=l=>t.updateState("openWB/optional/rfid/active",l)),buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}]},{help:o(()=>[a(" Dies bedingt das Vorhandensein eines RFID-Readers in deiner openWB. Bitte prüfe zuerst die Hardwareausstattung deiner openWB (z.B. Lieferschein). ")]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/rfid/active"]===!0?(i(),r("div",J,[e(v,{subtype:"info"},{default:o(()=>[a(" Die RFID-Tags, die an dem jeweiligen Ladepunkt gültig sind, müssen in dem Ladepunkt-Profil hinterlegt werden. Der RFID-Tag muss in den Einstellungen des Fahrzeugs diesem zugeordnet werden."),G,a(" Es kann zuerst angesteckt und dann der RFID-Tag gescannt werden oder zuerst der RFID-Tag gescannt werden. Dann muss innerhalb von 5 Minuten ein Auto angesteckt werden, sonst wird der RFID-Tag verworfen. Das Auto wird erst nach dem Anstecken zugeordnet."),Z,f("span",{innerHTML:t.$store.state.text.rfidWiki},null,8,K)]),_:1})])):d("v-if",!0)]),_:1}),d(` <openwb-base-card title="LED-Ausgänge">
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
			</openwb-base-card> `),e(m,{title:"Display (intern oder extern)"},{default:o(()=>[e(p,{title:"Integriertes Display","model-value":t.$store.state.mqtt["openWB/optional/int_display/active"],"onUpdate:modelValue":n[1]||(n[1]=l=>t.updateState("openWB/optional/int_display/active",l)),buttons:[{buttonValue:!1,text:"Nein",class:"btn-outline-danger"},{buttonValue:!0,text:"Ja",class:"btn-outline-success"}]},{help:o(()=>[a(' Je nach Bestellung kann die openWB mit oder ohne Display geliefert worden sein. Auch die Variante "Standalone" bietet beide Optionen. Bitte prüfe zuerst die Hardwareausstattung deiner openWB (z.B. Lieferschein). ')]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/int_display/active"]==!0?(i(),r("div",Q,[e(p,{title:"Orientierung","model-value":t.$store.state.mqtt["openWB/optional/int_display/rotation"],"onUpdate:modelValue":n[2]||(n[2]=l=>t.updateState("openWB/optional/int_display/rotation",l)),buttons:[{buttonValue:0,text:"0°"},{buttonValue:90,text:"90°"},{buttonValue:180,text:"180°"},{buttonValue:270,text:"270°"}]},{help:o(()=>[a(" Mit dieser Einstellung kann das Display im Uhrzeigersinn gedreht werden, falls erforderlich. Nach einer Änderung ist ein Neustart erforderlich!"),X,a(" Diese Einstellung erfordert ein Raspberry Pi Display. Anzeigen, welche über HDMI angeschlossen sind, werden nicht unterstützt. ")]),_:1},8,["model-value"]),Y,e(_,null,{default:o(()=>[a(" Display Standby ")]),_:1}),e(h,{title:"Ausschaltzeit",min:0,max:12,step:1,"model-value":t.$store.state.mqtt["openWB/optional/int_display/standby"],"onUpdate:modelValue":n[3]||(n[3]=l=>t.updateState("openWB/optional/int_display/standby",l)),unit:"Sek",labels:[{label:"Immer an",value:0},{label:5,value:5},{label:10,value:10},{label:15,value:15},{label:30,value:30},{label:45,value:45},{label:"1 Min",value:60},{label:"1,5 Min",value:90},{label:"2 Min",value:120},{label:"3 Min",value:180},{label:"4 Min",value:240},{label:"5 Min",value:300},{label:"10 Min",value:600}]},{help:o(()=>[a(" Hier kann eine Zeitspanne angegeben werden, nach der das Display ausgeschaltet wird. ")]),_:1},8,["model-value"]),d(` <openwb-base-button-group-input
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
					</openwb-base-button-group-input> `)])):d("v-if",!0),t.$store.state.mqtt["openWB/general/extern"]===!0?(i(),r("div",tt,[d(` <hr />
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
					</openwb-base-select-input> `),nt,e(v,{subtype:"info"},{default:o(()=>[a(' Weitere Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(i(),r("div",et,[d(` <hr />
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
					</div> `),ot,e(p,{title:"Ladepunkte auf externen openWB","model-value":t.$store.state.mqtt["openWB/optional/int_display/only_local_charge_points"],"onUpdate:modelValue":n[4]||(n[4]=l=>t.updateState("openWB/optional/int_display/only_local_charge_points",l)),buttons:[{buttonValue:!1,text:"Alle",class:"btn-outline-danger"},{buttonValue:!0,text:"Nur Lokale",class:"btn-outline-success"}]},{help:o(()=>[a(" Hiermit kann festgelegt werden, ob an angebundenen externen openWB alle oder nur die jeweils lokalen Ladepunkte angezeigt werden sollen. ")]),_:1},8,["model-value"]),lt,t.$store.state.mqtt["openWB/optional/int_display/theme"]!==void 0?(i(),r("div",at,[e(y,{class:"mb-2",title:"Theme des Displays",groups:b.displayThemeGroupList,"model-value":t.$store.state.mqtt["openWB/optional/int_display/theme"].type,"onUpdate:modelValue":n[5]||(n[5]=l=>b.updateSelectedDisplayTheme(l))},{help:o(()=>[a(" Hier können unterschiedliche Display-Anzeigen, s.g. Themes, ausgewählt werden. Die Anzahl der Themes wird sich mit zukünftigen Releases erhöhen. ")]),_:1},8,["groups","model-value"]),t.$store.state.mqtt["openWB/optional/int_display/theme"].type?(i(),c(L,{key:0,displayTheme:t.$store.state.mqtt["openWB/optional/int_display/theme"],"onUpdate:configuration":n[6]||(n[6]=l=>b.updateConfiguration("openWB/optional/int_display/theme",l))},null,8,["displayTheme"])):d("v-if",!0)])):d("v-if",!0)]))]),_:1}),d(` <openwb-base-card title="Variable Stromtarife">
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
			</openwb-base-card> `),e(E,{formName:"optionalComponentsForm",onSave:n[7]||(n[7]=l=>t.$emit("save")),onReset:n[8]||(n[8]=l=>t.$emit("reset")),onDefaults:n[9]||(n[9]=l=>t.$emit("defaults"))})])])}const mt=k(j,[["render",it],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/OptionalComponents.vue"]]);export{mt as default};
