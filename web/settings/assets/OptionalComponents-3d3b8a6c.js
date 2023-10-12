import{_ as w,C as B}from"./index-bbe99d07.js";import{_ as T}from"./dynamic-import-helper-be004503.js";import{_ as c,p,k as s,l as b,y as g,L as l,u as a,x as D,A as o,q as f,a0 as W,a1 as $,z as d}from"./vendor-20bb207d.js";import"./vendor-fortawesome-838df0c9.js";import"./vendor-bootstrap-d275de6c.js";import"./vendor-jquery-89b63fca.js";import"./vendor-axios-13ef03ae.js";import"./vendor-sortablejs-ad1d2cc8.js";const S={name:"DisplayThemeFallback",emits:["update:configuration"],props:{configuration:{type:Object,required:!0},displayThemeType:{type:String}},methods:{updateConfiguration(t,n=void 0){this.$emit("update:configuration",{value:t,object:n})}}},q={class:"display-theme-fallback"},A={key:1};function V(t,n,i,k,x,r){const u=p("openwb-base-alert"),v=p("openwb-base-textarea");return s(),b("div",q,[Object.keys(i.configuration).length==0?(s(),g(u,{key:0,subtype:"info"},{default:l(()=>[a(' Das Display-Theme "'+D(i.displayThemeType)+'" bietet keine Einstellungen. ',1)]),_:1})):(s(),b("div",A,[o(u,{subtype:"warning"},{default:l(()=>[a(' Es wurde keine Konfigurationsseite für das Display-Theme "'+D(i.displayThemeType)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),o(v,{title:"Konfiguration",subtype:"json","model-value":i.configuration,"onUpdate:modelValue":n[0]||(n[0]=m=>r.updateConfiguration(m,"configuration"))},{help:l(()=>[a(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),o(u,{subtype:"info"},{default:l(()=>[f("pre",null,D(JSON.stringify(i.configuration,void 0,2)),1)]),_:1})]))])}const z=c(S,[["render",V],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeFallback.vue"]]),C={name:"OpenwbDisplayThemeProxy",emits:["update:configuration"],props:{displayThemeType:{type:String,required:!0},configuration:{type:Object,required:!0}},computed:{myComponent(){return console.debug(`loading display theme: ${this.displayThemeType}`),W({loader:()=>T(Object.assign({"./cards/displayTheme.vue":()=>w(()=>import("./displayTheme-35595a93.js"),["assets/displayTheme-35595a93.js","assets/vendor-20bb207d.js","assets/vendor-sortablejs-ad1d2cc8.js","assets/vendor-7b9e30aa.css"])}),`./${this.displayThemeType}/displayTheme.vue`),errorComponent:z})}},methods:{updateConfiguration(t){this.$emit("update:configuration",t)}}};function O(t,n,i,k,x,r){return s(),g($(r.myComponent),{configuration:i.configuration,displayThemeType:i.displayThemeType,"onUpdate:configuration":n[0]||(n[0]=u=>r.updateConfiguration(u))},null,40,["configuration","displayThemeType"])}const I=c(C,[["render",O],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/display_themes/OpenwbDisplayThemeProxy.vue"]]),N={name:"OpenwbOptionalComponents",mixins:[B],components:{OpenwbDisplayThemeProxy:I},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/optional/rfid/active","openWB/optional/led/active","ToDo/optional/led/instant_blocked","ToDo/optional/led/pv_blocked","ToDo/optional/led/scheduled_blocked","ToDo/optional/led/standby_blocked","ToDo/optional/led/stop_blocked","ToDo/optional/led/instant","ToDo/optional/led/pv","ToDo/optional/led/scheduled","ToDo/optional/led/standby","ToDo/optional/led/stop","openWB/optional/int_display/active","openWB/optional/int_display/standby","openWB/optional/int_display/rotation","openWB/optional/int_display/on_if_plugged_in","openWB/optional/int_display/pin_active","openWB/optional/int_display/pin_code","openWB/optional/int_display/theme","openWB/optional/int_display/only_local_charge_points","openWB/system/configurable/display_themes","openWB/optional/et/active","openWB/optional/et/config/provider","openWB/optional/et/config/max_price"]}},computed:{displayThemeList:{get(){return this.$store.state.mqtt["openWB/system/configurable/display_themes"]}}},methods:{getDisplayThemeDefaultConfiguration(t){const n=this.displayThemeList.find(i=>i.value==t);return Object.prototype.hasOwnProperty.call(n,"defaults")?{...JSON.parse(JSON.stringify(n.defaults.configuration))}:(console.warn("no default configuration found for display theme type!",t),{})},updateSelectedDisplayTheme(t){this.updateState("openWB/optional/int_display/theme",t,"type"),this.updateState("openWB/optional/int_display/theme",this.getDisplayThemeDefaultConfiguration(t),"configuration")},updateConfiguration(t,n){console.debug("updateConfiguration",t,n),this.updateState(t,n.value,n.object)}}},P={class:"optionalComponents"},F={name:"optionalComponentsForm"},R={key:0},M=f("br",null,null,-1),j=f("br",null,null,-1),U=["innerHTML"],H={key:0},J=f("br",null,null,-1),Z=f("hr",null,null,-1),K={key:1},G=f("hr",null,null,-1),Q={key:2},X=f("hr",null,null,-1),Y=f("hr",null,null,-1),tt={key:0};function nt(t,n,i,k,x,r){const u=p("openwb-base-button-group-input"),v=p("openwb-base-alert"),m=p("openwb-base-card"),_=p("openwb-base-heading"),y=p("openwb-base-range-input"),h=p("openwb-base-select-input"),L=p("openwb-display-theme-proxy"),E=p("openwb-base-submit-buttons");return s(),b("div",P,[f("form",F,[o(m,{title:"RFID"},{default:l(()=>[o(u,{title:"RFID aktivieren","model-value":t.$store.state.mqtt["openWB/optional/rfid/active"],"onUpdate:modelValue":n[0]||(n[0]=e=>t.updateState("openWB/optional/rfid/active",e)),buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}]},{help:l(()=>[a(" Dies bedingt das Vorhandensein eines RFID-Readers in deiner openWB. Bitte prüfe zuerst die Hardwareausstattung deiner openWB (z.B. Lieferschein). ")]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/rfid/active"]===!0?(s(),b("div",R,[o(v,{subtype:"info"},{default:l(()=>[a(" Die RFID-Tags, die an dem jeweiligen Ladepunkt gültig sind, müssen in dem Ladepunkt-Profil hinterlegt werden. Der RFID-Tag muss in den Einstellungen des Fahrzeugs diesem zugeordnet werden."),M,a(" Es kann zuerst angesteckt und dann der RFID-Tag gescannt werden oder zuerst der RFID-Tag gescannt werden. Dann muss innerhalb von 5 Minuten ein Auto angesteckt werden, sonst wird der RFID-Tag verworfen. Das Auto wird erst nach dem Anstecken zugeordnet."),j,f("span",{innerHTML:t.$store.state.text.rfidWiki},null,8,U)]),_:1})])):d("v-if",!0)]),_:1}),d(` <openwb-base-card title="LED-Ausgänge">
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
			</openwb-base-card> `),o(m,{title:"Display (intern oder extern)"},{default:l(()=>[o(u,{title:"Integriertes Display","model-value":t.$store.state.mqtt["openWB/optional/int_display/active"],"onUpdate:modelValue":n[1]||(n[1]=e=>t.updateState("openWB/optional/int_display/active",e)),buttons:[{buttonValue:!1,text:"Nein",class:"btn-outline-danger"},{buttonValue:!0,text:"Ja",class:"btn-outline-success"}]},{help:l(()=>[a(' Je nach Bestellung kann die openWB mit oder ohne Display geliefert worden sein. Auch die Variante "Standalone" bietet beide Optionen. Bitte prüfe zuerst die Hardwareausstattung deiner openWB (z.B. Lieferschein). ')]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/optional/int_display/active"]==!0?(s(),b("div",H,[o(u,{title:"Orientierung","model-value":t.$store.state.mqtt["openWB/optional/int_display/rotation"],"onUpdate:modelValue":n[2]||(n[2]=e=>t.updateState("openWB/optional/int_display/rotation",e)),buttons:[{buttonValue:0,text:"0°"},{buttonValue:90,text:"90°"},{buttonValue:180,text:"180°"},{buttonValue:270,text:"270°"}]},{help:l(()=>[a(" Mit dieser Einstellung kann das Display im Uhrzeigersinn gedreht werden, falls erforderlich. Nach einer Änderung ist ein Neustart erforderlich!"),J,a(" Diese Einstellung erfordert ein Raspberry Pi Display. Anzeigen, welche über HDMI angeschlossen sind, werden nicht unterstützt. ")]),_:1},8,["model-value"]),Z,o(_,null,{default:l(()=>[a(" Display Standby ")]),_:1}),o(y,{title:"Ausschaltzeit",min:0,max:12,step:1,"model-value":t.$store.state.mqtt["openWB/optional/int_display/standby"],"onUpdate:modelValue":n[3]||(n[3]=e=>t.updateState("openWB/optional/int_display/standby",e)),unit:"Sek",labels:[{label:"Immer an",value:0},{label:5,value:5},{label:10,value:10},{label:15,value:15},{label:30,value:30},{label:45,value:45},{label:"1 Min",value:60},{label:"1,5 Min",value:90},{label:"2 Min",value:120},{label:"3 Min",value:180},{label:"4 Min",value:240},{label:"5 Min",value:300},{label:"10 Min",value:600}]},{help:l(()=>[a(" Hier kann eine Zeitspanne angegeben werden, nach der das Display ausgeschaltet wird. ")]),_:1},8,["model-value"]),d(` <openwb-base-button-group-input
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
					</openwb-base-button-group-input> `)])):d("v-if",!0),t.$store.state.mqtt["openWB/general/extern"]===!0?(s(),b("div",K,[d(` <hr />
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
					</openwb-base-select-input> `),G,o(v,{subtype:"info"},{default:l(()=>[a(' Weitere Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(s(),b("div",Q,[d(` <hr />
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
					</div> `),X,o(u,{title:"Ladepunkte auf externen openWB","model-value":t.$store.state.mqtt["openWB/optional/int_display/only_local_charge_points"],"onUpdate:modelValue":n[4]||(n[4]=e=>t.updateState("openWB/optional/int_display/only_local_charge_points",e)),buttons:[{buttonValue:!1,text:"Alle",class:"btn-outline-danger"},{buttonValue:!0,text:"Nur Lokale",class:"btn-outline-success"}]},{help:l(()=>[a(" Hiermit kann festgelegt werden, ob an angebundenen externen openWB alle oder nur die jeweils lokalen Ladepunkte angezeigt werden sollen. ")]),_:1},8,["model-value"]),Y,t.$store.state.mqtt["openWB/optional/int_display/theme"]!==void 0?(s(),b("div",tt,[o(h,{class:"mb-2",title:"Theme des Displays",options:r.displayThemeList,"model-value":t.$store.state.mqtt["openWB/optional/int_display/theme"].type,"onUpdate:modelValue":n[5]||(n[5]=e=>r.updateSelectedDisplayTheme(e))},{help:l(()=>[a(" Hier können unterschiedliche Display-Anzeigen, s.g. Themes, ausgewählt werden. Die Anzahl der Themes wird sich mit zukünftigen Releases erhöhen. ")]),_:1},8,["options","model-value"]),t.$store.state.mqtt["openWB/optional/int_display/theme"].type?(s(),g(L,{key:0,displayThemeType:t.$store.state.mqtt["openWB/optional/int_display/theme"].type,configuration:t.$store.state.mqtt["openWB/optional/int_display/theme"].configuration,"onUpdate:configuration":n[6]||(n[6]=e=>r.updateConfiguration("openWB/optional/int_display/theme",e))},null,8,["displayThemeType","configuration"])):d("v-if",!0)])):d("v-if",!0)]))]),_:1}),d(` <openwb-base-card title="Variable Stromtarife">
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
			</openwb-base-card> `),o(E,{formName:"optionalComponentsForm",onSave:n[7]||(n[7]=e=>t.$emit("save")),onReset:n[8]||(n[8]=e=>t.$emit("reset")),onDefaults:n[9]||(n[9]=e=>t.$emit("defaults"))})])])}const ft=c(N,[["render",nt],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/OptionalComponents.vue"]]);export{ft as default};
