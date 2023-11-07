import{C as T}from"./index-02c2fcbd.js";import{_ as $}from"./dynamic-import-helper-be004503.js";import{_ as h,p as d,k as r,l as p,y as w,L as i,u as a,x as f,A as n,q as s,a0 as z,a1 as V,z as c}from"./vendor-94ac8c48.js";import"./vendor-fortawesome-0f5e79b9.js";import"./vendor-bootstrap-9f620114.js";import"./vendor-jquery-f7104ff8.js";import"./vendor-axios-dc63434e.js";import"./vendor-sortablejs-dbc23470.js";const q={name:"WebThemeFallback",emits:["update:configuration"],props:{configuration:{type:Object,required:!0},webThemeType:{type:String}},methods:{updateConfiguration(t,e=void 0){this.$emit("update:configuration",{value:t,object:e})}}},P={class:"web-theme-fallback"},x={key:1};function C(t,e,u,_,v,b){const l=d("openwb-base-alert"),g=d("openwb-base-textarea");return r(),p("div",P,[Object.keys(u.configuration).length==0?(r(),w(l,{key:0,subtype:"info"},{default:i(()=>[a(' Das Web Theme "'+f(u.webThemeType)+'" bietet keine Einstellungen. ',1)]),_:1})):(r(),p("div",x,[n(l,{subtype:"warning"},{default:i(()=>[a(' Es wurde keine Konfigurationsseite für das Web Theme "'+f(u.webThemeType)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),n(g,{title:"Theme Konfiguration",subtype:"json","model-value":u.configuration,"onUpdate:modelValue":e[0]||(e[0]=m=>b.updateConfiguration(m,"configuration"))},{help:i(()=>[a(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),n(l,{subtype:"info"},{default:i(()=>[s("pre",null,f(JSON.stringify(u.configuration,void 0,2)),1)]),_:1})]))])}const O=h(q,[["render",C],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeFallback.vue"]]),D={name:"OpenwbWebThemeProxy",emits:["update:configuration"],props:{webThemeType:{type:String,required:!0},configuration:{type:Object,required:!0}},computed:{myComponent(){return console.debug(`loading web theme: ${this.webThemeType}`),z({loader:()=>$(Object.assign({}),`./${this.webThemeType}/webTheme.vue`),errorComponent:O})}},methods:{updateConfiguration(t){this.$emit("update:configuration",t)}}};function L(t,e,u,_,v,b){return r(),w(V(b.myComponent),{configuration:u.configuration,webThemeType:u.webThemeType,"onUpdate:configuration":e[0]||(e[0]=l=>b.updateConfiguration(l))},null,40,["configuration","webThemeType"])}const N=h(D,[["render",L],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeProxy.vue"]]),E={name:"OpenwbGeneralConfig",mixins:[T],components:{OpenwbWebThemeProxy:N},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/general/control_interval","openWB/general/grid_protection_configured","openWB/general/external_buttons_hw","openWB/general/modbus_control","openWB/general/notifications/selected","openWB/general/notifications/configuration","openWB/general/notifications/start_charging","openWB/general/notifications/stop_charging","openWB/general/notifications/plug","openWB/general/notifications/smart_home","openWB/general/price_kwh","openWB/general/range_unit","openWB/general/web_theme","openWB/system/configurable/web_themes"]}},computed:{webThemeList:{get(){return this.$store.state.mqtt["openWB/system/configurable/web_themes"]}}},methods:{getWebThemeDefaultConfiguration(t){const e=this.webThemeList.find(u=>u.value==t);return Object.prototype.hasOwnProperty.call(e,"defaults")?{...JSON.parse(JSON.stringify(e.defaults.configuration))}:(console.warn("no default configuration found for web theme type!",t),{})},updateSelectedWebTheme(t){this.updateState("openWB/general/web_theme",t,"type"),this.updateState("openWB/general/web_theme",this.getWebThemeDefaultConfiguration(t),"configuration")},updateConfiguration(t,e){console.debug("updateConfiguration",t,e),this.updateState(t,e.value,e.object)}}},A={class:"generalConfig"},I={name:"generalConfigForm"},U=s("br",null,null,-1),F=s("br",null,null,-1),G=s("br",null,null,-1),R=s("a",{href:"https://openwb.de/main/?page_id=1025",target:"_blank",rel:"noopener noreferrer"}," Homepage ",-1),M=s("a",{href:"https://openwb.de/main/wp-content/uploads/2023/10/ModbusTCP-openWB-series2-Pro-1.pdf",target:"_blank",rel:"noopener noreferrer"}," hier",-1),j={key:0},K={key:0},J={key:1},H=s("br",null,null,-1),Z=s("span",{class:"text-danger"},' Nicht nur die Regelung der PV geführten Ladung, sondern auch die Ladestromänderung, beispielsweise “Stop“ etc., werden dann nur noch in diesem Intervall ausgeführt. Die Regelung wird insgesamt träger. Solange es keinen triftigen Grund gibt, sollte "Normal" gewählt werden. ',-1),Q=s("br",null,null,-1),X=s("span",{class:"text-danger"}," Die Option ist nur aktiv, wenn der EVU-Zähler die Frequenz übermittelt. ",-1),Y={key:0},tt={key:1},et={key:0},nt=s("hr",null,null,-1),ot=s("br",null,null,-1);function at(t,e,u,_,v,b){const l=d("openwb-base-alert"),g=d("openwb-base-button-group-input"),m=d("openwb-base-card"),B=d("openwb-base-heading"),W=d("openwb-base-select-input"),y=d("openwb-web-theme-proxy"),k=d("openwb-base-number-input"),S=d("openwb-base-submit-buttons");return r(),p("div",A,[s("form",I,[n(m,{title:"Steuerungsmodus"},{default:i(()=>[n(l,{subtype:"info"},{default:i(()=>[a(' Wird für den Steuerungsmodus "primary" gewählt, übernimmt diese openWB die alleinige Regelung und steuert ggf. vorhandene weitere openWB (z.B. externe openWB im Steuermodus secondary, openWB Pro, Satellit u.a.) fern. Sie werden in den Ladepunkt-Einstellungen der primary-openWB hinzugefügt. '),U,F,a(' Wird für den Steuerungsmodus "secondary" gewählt, übernimmt diese openWB keine Regelung und muss von einer anderen primary openWB ferngesteuert werden. Wichtig ist, dass in der secondary-openWB eine "interne openWB" mit der korrekten Bauart (= openWB-Hardwarevariante z.B. "Custom, Standard, Standard+, Duo, Buchse") konfiguriert ist. Bei einer Duo sind zwei "interne openWB" zu konfigurieren. Im "secondary"-Modus bleiben alle ausgeblendeten Einstellungen unbeachtet.'),G,a(" Eine bebilderte Anleitung zur Konfiguration der Ladepunkte findest Du auf der "),R,a(". ")]),_:1}),n(g,{title:"Steuerungsmodus",buttons:[{buttonValue:!1,text:"primary",class:"btn-outline-danger"},{buttonValue:!0,text:"secondary",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/extern"],"onUpdate:modelValue":e[0]||(e[0]=o=>t.updateState("openWB/general/extern",o))},null,8,["model-value"]),n(g,{title:"Steuerung über Modbus als secondary",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/modbus_control"],"onUpdate:modelValue":e[1]||(e[1]=o=>t.updateState("openWB/general/modbus_control",o))},{help:i(()=>[a(" Im secondary-Modus kann die openWB über die Modbus-Schnittstelle gesteuert werden. Die Register sind "),M,a("dokumentiert. Bei aktivierter Modbus-Schnittstelle darf die openWB nicht von einer primary-openWB gesteuert werden. ")]),_:1},8,["model-value"]),t.$store.state.mqtt["openWB/general/modbus_control"]===!0?(r(),p("div",j,[n(l,{subtype:"info"},{default:i(()=>[a(' Wenn die Steuerung über Modbus auf "aus" geändert wird, muss danach ein Neustart durchgeführt werden! ')]),_:1})])):c("v-if",!0)]),_:1}),n(m,{title:"Hardware"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(r(),p("div",K,[n(l,{subtype:"info"},{default:i(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(r(),p("div",J,[n(g,{title:"Geschwindigkeit Regelintervall",buttons:[{buttonValue:10,text:"Normal",class:"btn-outline-success"},{buttonValue:20,text:"Langsam",class:"btn-outline-warning"},{buttonValue:60,text:"Sehr Langsam",class:"btn-outline-danger"}],"model-value":t.$store.state.mqtt["openWB/general/control_interval"],"onUpdate:modelValue":e[2]||(e[2]=o=>t.updateState("openWB/general/control_interval",o))},{help:i(()=>[a(' Sollten Probleme oder Fehlermeldungen auftauchen, stelle bitte zunächst das Regelintervall auf "Normal". Werden Module genutzt, welche z.B. eine Online-API zur Abfrage nutzen (höhere Latenzzeiten) oder möchte man weniger Regeleingriffe, so kann man das Regelintervall auf "Langsam" (20 Sekunden) herabsetzen. Die Einstellung „Sehr Langsam“ führt zu einer Regelzeit von 60 Sekunden.'),H,Z]),_:1},8,["model-value"]),n(g,{title:"Netzschutz",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/grid_protection_configured"],"onUpdate:modelValue":e[3]||(e[3]=o=>t.updateState("openWB/general/grid_protection_configured",o))},{help:i(()=>[a(' Diese Option ist standardmäßig aktiviert und sollte so belassen werden. Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert. Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert. Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generator-Betrieb umschaltet. Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.'),Q,X]),_:1},8,["model-value"]),c(` <openwb-base-button-group-input
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
			</openwb-base-card> `),n(m,{title:"Darstellung"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(r(),p("div",Y,[n(l,{subtype:"info"},{default:i(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(r(),p("div",tt,[n(B,{class:"mt-0"},{default:i(()=>[a(" Hauptseite ")]),_:1}),t.$store.state.mqtt["openWB/general/web_theme"]!==void 0?(r(),p("div",et,[n(W,{class:"mb-2",title:"Theme",options:b.webThemeList,"model-value":t.$store.state.mqtt["openWB/general/web_theme"].type,"onUpdate:modelValue":e[4]||(e[4]=o=>b.updateSelectedWebTheme(o))},null,8,["options","model-value"]),t.$store.state.mqtt["openWB/general/web_theme"].type?(r(),w(y,{key:0,webThemeType:t.$store.state.mqtt["openWB/general/web_theme"].type,configuration:t.$store.state.mqtt["openWB/general/web_theme"].configuration,"onUpdate:configuration":e[5]||(e[5]=o=>b.updateConfiguration("openWB/general/web_theme",o))},null,8,["webThemeType","configuration"])):c("v-if",!0)])):c("v-if",!0),nt,n(B,null,{default:i(()=>[a(" Lade-Log ")]),_:1}),n(k,{title:"Preis je kWh",min:0,step:1e-4,unit:"€","model-value":t.$store.state.mqtt["openWB/general/price_kwh"],"onUpdate:modelValue":e[6]||(e[6]=o=>t.updateState("openWB/general/price_kwh",o))},{help:i(()=>[a(" Dient zur Berechnung der Ladekosten im Lade-Log."),ot,a(" Es können bis zu 4 Nachkommastellen genutzt werden. ")]),_:1},8,["model-value"]),n(g,{title:"Einheit für Entfernungen","model-value":t.$store.state.mqtt["openWB/general/range_unit"],"onUpdate:modelValue":e[7]||(e[7]=o=>t.updateState("openWB/general/range_unit",o)),buttons:[{buttonValue:"km",text:"Kilometer"},{buttonValue:"mi",text:"Meilen"}]},null,8,["model-value"])]))]),_:1}),n(S,{formName:"generalConfigForm",onSave:e[8]||(e[8]=o=>t.$emit("save")),onReset:e[9]||(e[9]=o=>t.$emit("reset")),onDefaults:e[10]||(e[10]=o=>t.$emit("defaults"))})])])}const gt=h(E,[["render",at],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/GeneralConfig.vue"]]);export{gt as default};
