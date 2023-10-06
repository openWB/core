import{C as T}from"./index-bbf2ec18.js";import{_ as $}from"./dynamic-import-helper-be004503.js";import{_ as h,p as l,k as u,l as g,y as w,L as i,u as a,x as f,A as n,q as s,a0 as z,a1 as q,z as c}from"./vendor-94ac8c48.js";import"./vendor-fortawesome-ad83e535.js";import"./vendor-bootstrap-9f620114.js";import"./vendor-jquery-f7104ff8.js";import"./vendor-axios-dc63434e.js";import"./vendor-sortablejs-dbc23470.js";const V={name:"WebThemeFallback",emits:["update:configuration"],props:{configuration:{type:Object,required:!0},webThemeType:{type:String}},methods:{updateConfiguration(t,e=void 0){this.$emit("update:configuration",{value:t,object:e})}}},x={class:"web-theme-fallback"},P={key:1};function C(t,e,r,_,v,p){const d=l("openwb-base-alert"),b=l("openwb-base-textarea");return u(),g("div",x,[Object.keys(r.configuration).length==0?(u(),w(d,{key:0,subtype:"info"},{default:i(()=>[a(' Das Web Theme "'+f(r.webThemeType)+'" bietet keine Einstellungen. ',1)]),_:1})):(u(),g("div",P,[n(d,{subtype:"warning"},{default:i(()=>[a(' Es wurde keine Konfigurationsseite für das Web Theme "'+f(r.webThemeType)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),n(b,{title:"Theme Konfiguration",subtype:"json","model-value":r.configuration,"onUpdate:modelValue":e[0]||(e[0]=m=>p.updateConfiguration(m,"configuration"))},{help:i(()=>[a(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),n(d,{subtype:"info"},{default:i(()=>[s("pre",null,f(JSON.stringify(r.configuration,void 0,2)),1)]),_:1})]))])}const D=h(V,[["render",C],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeFallback.vue"]]),L={name:"OpenwbWebThemeProxy",emits:["update:configuration"],props:{webThemeType:{type:String,required:!0},configuration:{type:Object,required:!0}},computed:{myComponent(){return console.debug(`loading web theme: ${this.webThemeType}`),z({loader:()=>$(Object.assign({}),`./${this.webThemeType}/webTheme.vue`),errorComponent:D})}},methods:{updateConfiguration(t){this.$emit("update:configuration",t)}}};function O(t,e,r,_,v,p){return u(),w(q(p.myComponent),{configuration:r.configuration,webThemeType:r.webThemeType,"onUpdate:configuration":e[0]||(e[0]=d=>p.updateConfiguration(d))},null,40,["configuration","webThemeType"])}const E=h(L,[["render",O],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeProxy.vue"]]),N={name:"OpenwbGeneralConfig",mixins:[T],components:{OpenwbWebThemeProxy:E},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/general/control_interval","openWB/general/grid_protection_configured","openWB/general/external_buttons_hw","openWB/general/notifications/selected","openWB/general/notifications/configuration","openWB/general/notifications/start_charging","openWB/general/notifications/stop_charging","openWB/general/notifications/plug","openWB/general/notifications/smart_home","openWB/general/price_kwh","openWB/general/range_unit","openWB/general/web_theme","openWB/system/configurable/web_themes"]}},computed:{webThemeList:{get(){return this.$store.state.mqtt["openWB/system/configurable/web_themes"]}}},methods:{getWebThemeDefaultConfiguration(t){const e=this.webThemeList.find(r=>r.value==t);return Object.prototype.hasOwnProperty.call(e,"defaults")?{...e.defaults.configuration}:(console.warn("no default configuration found for web theme type!",t),{})},updateSelectedWebTheme(t){this.updateState("openWB/general/web_theme",t,"type"),this.updateState("openWB/general/web_theme",this.getWebThemeDefaultConfiguration(t),"configuration")},updateConfiguration(t,e){console.debug("updateConfiguration",t,e),this.updateState(t,e.value,e.object)}}},A={class:"generalConfig"},I={name:"generalConfigForm"},F=s("br",null,null,-1),G=s("br",null,null,-1),U=s("br",null,null,-1),R=s("a",{href:"https://openwb.de/main/?page_id=1025",target:"_blank",rel:"noopener noreferrer"}," Homepage ",-1),j={key:0},K={key:1},H=s("br",null,null,-1),J=s("span",{class:"text-danger"},' Nicht nur die Regelung der PV geführten Ladung, sondern auch die Ladestromänderung, beispielsweise “Stop“ etc., werden dann nur noch in diesem Intervall ausgeführt. Die Regelung wird insgesamt träger. Solange es keinen triftigen Grund gibt, sollte "Normal" gewählt werden. ',-1),Z=s("br",null,null,-1),M=s("span",{class:"text-danger"}," Die Option ist nur aktiv, wenn der EVU-Zähler die Frequenz übermittelt. ",-1),Q={key:0},X={key:1},Y={key:0},tt=s("hr",null,null,-1),et=s("br",null,null,-1);function nt(t,e,r,_,v,p){const d=l("openwb-base-alert"),b=l("openwb-base-button-group-input"),m=l("openwb-base-card"),B=l("openwb-base-heading"),W=l("openwb-base-select-input"),y=l("openwb-web-theme-proxy"),k=l("openwb-base-number-input"),S=l("openwb-base-submit-buttons");return u(),g("div",A,[s("form",I,[n(m,{title:"Steuerungsmodus"},{default:i(()=>[n(d,{subtype:"info"},{default:i(()=>[a(' Wird für den Steuerungsmodus "primary" gewählt, übernimmt diese openWB die alleinige Regelung und steuert ggf. vorhandene weitere openWB (z.B. externe openWB im Steuermodus secondary, openWB Pro, Satellit u.a.) fern. Sie werden in den Ladepunkt-Einstellungen der primary-openWB hinzugefügt. '),F,G,a(' Wird für den Steuerungsmodus "secondary" gewählt, übernimmt diese openWB keine Regelung und muss von einer anderen primary openWB ferngesteuert werden. Wichtig ist, dass in der secondary-openWB eine "interne openWB" mit der korrekten Bauart (= openWB-Hardwarevariante z.B. "Custom, Standard, Standard+, Duo, Buchse") konfiguriert ist. Bei einer Duo sind zwei "interne openWB" zu konfigurieren. Im "secondary"-Modus bleiben alle ausgeblendeten Einstellungen unbeachtet.'),U,a(" Eine bebilderte Anleitung zur Konfiguration der Ladepunkte findest Du auf der "),R,a(". ")]),_:1}),n(b,{title:"Steuerungsmodus",buttons:[{buttonValue:!1,text:"primary",class:"btn-outline-danger"},{buttonValue:!0,text:"secondary",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/extern"],"onUpdate:modelValue":e[0]||(e[0]=o=>t.updateState("openWB/general/extern",o))},null,8,["model-value"])]),_:1}),n(m,{title:"Hardware"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(u(),g("div",j,[n(d,{subtype:"info"},{default:i(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(u(),g("div",K,[n(b,{title:"Geschwindigkeit Regelintervall",buttons:[{buttonValue:10,text:"Normal",class:"btn-outline-success"},{buttonValue:20,text:"Langsam",class:"btn-outline-warning"},{buttonValue:60,text:"Sehr Langsam",class:"btn-outline-danger"}],"model-value":t.$store.state.mqtt["openWB/general/control_interval"],"onUpdate:modelValue":e[1]||(e[1]=o=>t.updateState("openWB/general/control_interval",o))},{help:i(()=>[a(' Sollten Probleme oder Fehlermeldungen auftauchen, stelle bitte zunächst das Regelintervall auf "Normal". Werden Module genutzt, welche z.B. eine Online-API zur Abfrage nutzen (höhere Latenzzeiten) oder möchte man weniger Regeleingriffe, so kann man das Regelintervall auf "Langsam" (20 Sekunden) herabsetzen. Die Einstellung „Sehr Langsam“ führt zu einer Regelzeit von 60 Sekunden.'),H,J]),_:1},8,["model-value"]),n(b,{title:"Netzschutz",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/grid_protection_configured"],"onUpdate:modelValue":e[2]||(e[2]=o=>t.updateState("openWB/general/grid_protection_configured",o))},{help:i(()=>[a(' Diese Option ist standardmäßig aktiviert und sollte so belassen werden. Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert. Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert. Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generator-Betrieb umschaltet. Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.'),Z,M]),_:1},8,["model-value"]),c(` <openwb-base-button-group-input
						title="Taster-Eingänge"
						:model-value="
							$store.state.mqtt[
								'openWB/general/external_buttons_hw'
							]
						"
						@update:model-value="
							updateState(
								'openWB/general/external_buttons_hw',
								$event
							)
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
					>
						<template #help>
							Wenn diese Option aktiviert ist, können bis zu fünf
							Taster an die openWB angeschlossen werden. Die
							entsprechenden Kontakte sind auf der Add-On-Platine
							beschriftet.<br />
							Bei Installationen ohne die Zusatzplatine können
							folgende GPIOs benutzt werden, die durch die Taster
							auf Masse zu schalten sind:
							<ul>
								<li>Taster 1: Pin 32 / GPIO 12</li>
								<li>Taster 2: Pin 36 / GPIO 16</li>
								<li>Taster 3: Pin 31 / GPIO 6</li>
								<li>Taster 4: Pin 33 / GPIO 13</li>
								<li>Taster 5: Pin 40 / GPIO 21</li>
							</ul>
						</template>
					</openwb-base-button-group-input> `)]))]),_:1}),c(` <openwb-base-card title="Benachrichtigungen">
				<div v-if="$store.state.mqtt['openWB/general/extern'] === true">
					<openwb-base-alert subtype="info">
						Diese Einstellungen sind nicht verfügbar, solange sich
						diese openWB im Steuerungsmodus "secondary" befindet.
					</openwb-base-alert>
				</div>
				<div v-else>
					<openwb-base-select-input
						title="Anbieter"
						:model-value="
							$store.state.mqtt[
								'openWB/general/notifications/selected'
							]
						"
						@update:model-value="
							updateState(
								'openWB/general/notifications/selected',
								$event
							)
						"
						:options="[
							{ value: 'none', text: 'Kein Anbieter' },
							{ value: 'pushover', text: 'Pushover' },
						]"
					/>
					<div
						v-if="
							$store.state.mqtt[
								'openWB/general/notifications/selected'
							] == 'pushover'
						"
					>
						<openwb-base-alert subtype="info">
							Zur Nutzung von Pushover muss ein Konto auf
							Pushover.net bestehen. Zudem muss im
							Pushover-Nutzerkonto eine Applikation openWB
							eingerichtet werden, um den benötigten API-Token/Key
							zu erhalten.<br />
							Wenn Pushover eingeschaltet ist, werden die
							Zählerstände aller konfigurierten Ladepunkte immer
							zum 1. des Monats gepusht.
						</openwb-base-alert>
						<openwb-base-text-input
							title="Einstellungen"
							subtype="json"
							disabled="disabled"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/configuration'
								]
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/configuration',
									$event
								)
							"
						>
							<template #help>Nur zur Info!</template>
						</openwb-base-text-input>
						<openwb-base-text-input
							title="Pushover User Key"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/configuration'
								].user
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/configuration',
									$event,
									'user'
								)
							"
							subtype="user"
						/>
						<openwb-base-text-input
							title="Pushover API-Token/Key"
							subtype="password"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/configuration'
								].key
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/configuration',
									$event,
									'key'
								)
							"
						/>
					</div>
					<div
						v-if="
							$store.state.mqtt[
								'openWB/general/notifications/selected'
							] != 'none'
						"
					>
						<hr />
						<openwb-base-heading>
							Benachrichtigungen
						</openwb-base-heading>
						<openwb-base-button-group-input
							title="Beim Starten der Ladung"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/start_charging'
								]
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/start_charging',
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
						<openwb-base-button-group-input
							title="Beim Stoppen der Ladung"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/stop_charging'
								]
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/stop_charging',
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
						<openwb-base-button-group-input
							title="Beim Einstecken eines Fahrzeugs"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/plug'
								]
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/plug',
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
						<openwb-base-button-group-input
							title="Bei Triggern von Smart Home Aktionen"
							:model-value="
								$store.state.mqtt[
									'openWB/general/notifications/smart_home'
								]
							"
							@update:model-value="
								updateState(
									'openWB/general/notifications/smart_home',
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
					</div>
				</div>
			</openwb-base-card> `),n(m,{title:"Darstellung"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(u(),g("div",Q,[n(d,{subtype:"info"},{default:i(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(u(),g("div",X,[n(B,{class:"mt-0"},{default:i(()=>[a(" Hauptseite ")]),_:1}),t.$store.state.mqtt["openWB/general/web_theme"]!==void 0?(u(),g("div",Y,[n(W,{class:"mb-2",title:"Theme",options:p.webThemeList,"model-value":t.$store.state.mqtt["openWB/general/web_theme"].type,"onUpdate:modelValue":e[3]||(e[3]=o=>p.updateSelectedWebTheme(o))},null,8,["options","model-value"]),t.$store.state.mqtt["openWB/general/web_theme"].type?(u(),w(y,{key:0,webThemeType:t.$store.state.mqtt["openWB/general/web_theme"].type,configuration:t.$store.state.mqtt["openWB/general/web_theme"].configuration,"onUpdate:configuration":e[4]||(e[4]=o=>p.updateConfiguration("openWB/general/web_theme",o))},null,8,["webThemeType","configuration"])):c("v-if",!0)])):c("v-if",!0),tt,n(B,null,{default:i(()=>[a(" Lade-Log ")]),_:1}),n(k,{title:"Preis je kWh",min:0,step:1e-4,unit:"€","model-value":t.$store.state.mqtt["openWB/general/price_kwh"],"onUpdate:modelValue":e[5]||(e[5]=o=>t.updateState("openWB/general/price_kwh",o))},{help:i(()=>[a(" Dient zur Berechnung der Ladekosten im Lade-Log."),et,a(" Es können bis zu 4 Nachkommastellen genutzt werden. ")]),_:1},8,["model-value"]),n(b,{title:"Einheit für Entfernungen","model-value":t.$store.state.mqtt["openWB/general/range_unit"],"onUpdate:modelValue":e[6]||(e[6]=o=>t.updateState("openWB/general/range_unit",o)),buttons:[{buttonValue:"km",text:"Kilometer"},{buttonValue:"mi",text:"Meilen"}]},null,8,["model-value"])]))]),_:1}),n(S,{formName:"generalConfigForm",onSave:e[7]||(e[7]=o=>t.$emit("save")),onReset:e[8]||(e[8]=o=>t.$emit("reset")),onDefaults:e[9]||(e[9]=o=>t.$emit("defaults"))})])])}const pt=h(N,[["render",nt],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/GeneralConfig.vue"]]);export{pt as default};
