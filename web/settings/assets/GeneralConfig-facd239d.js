import{C as T}from"./index-a961d15f.js";import{_ as $}from"./dynamic-import-helper-be004503.js";import{l as z,R as V,S as x,F as P}from"./vendor-fortawesome-8ba39b16.js";import{_ as w,p as u,k as s,l as b,y as f,L as a,u as o,x as h,A as n,q as r,a0 as q,a1 as C,G as D,z as c}from"./vendor-20bb207d.js";import"./vendor-bootstrap-d275de6c.js";import"./vendor-jquery-89b63fca.js";import"./vendor-axios-13ef03ae.js";import"./vendor-sortablejs-ad1d2cc8.js";const L={name:"WebThemeFallback",emits:["update:configuration"],props:{webTheme:{type:Object,required:!0}},methods:{updateConfiguration(e,t=void 0){this.$emit("update:configuration",{value:e,object:t})}}},O={class:"web-theme-fallback"},N={key:1};function E(e,t,l,_,v,m){const d=u("openwb-base-alert"),p=u("openwb-base-textarea");return s(),b("div",O,[Object.keys(l.webTheme.configuration).length==0?(s(),f(d,{key:0,subtype:"info"},{default:a(()=>[o(' Das Web Theme "'+h(l.webTheme.name)+'" bietet keine Einstellungen. ',1)]),_:1})):(s(),b("div",N,[n(d,{subtype:"warning"},{default:a(()=>[o(' Es wurde keine Konfigurationsseite für das Web Theme "'+h(l.webTheme.name)+'" gefunden. Die Einstellungen können als JSON direkt bearbeitet werden. ',1)]),_:1}),n(p,{title:"Theme Konfiguration",subtype:"json","model-value":l.webTheme.configuration,"onUpdate:modelValue":t[0]||(t[0]=g=>m.updateConfiguration(g,"configuration"))},{help:a(()=>[o(" Bitte prüfen Sie, ob die Eingaben richtig interpretiert werden. ")]),_:1},8,["model-value"]),n(d,{subtype:"info"},{default:a(()=>[r("pre",null,h(JSON.stringify(l.webTheme.configuration,void 0,2)),1)]),_:1})]))])}const A=w(L,[["render",E],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeFallback.vue"]]);z.add(V,x);const F={name:"OpenwbWebThemeProxy",emits:["update:configuration"],props:{webTheme:{type:Object,required:!0}},components:{FontAwesomeIcon:P},computed:{myComponent(){return console.debug(`loading web theme: ${this.webTheme.name}`),q({loader:()=>$(Object.assign({}),`./${this.webTheme.type}/webTheme.vue`),errorComponent:A})}},methods:{updateConfiguration(e){this.$emit("update:configuration",e)}}};function G(e,t,l,_,v,m){const d=u("font-awesome-icon"),p=u("openwb-base-alert");return s(),b(D,null,[l.webTheme.official?(s(),f(p,{key:0,subtype:"success"},{default:a(()=>[n(d,{"fixed-width":"",icon:["fas","certificate"]}),o(" Das ausgewählte Theme wird von openWB gepflegt. ")]),_:1})):(s(),f(p,{key:1,subtype:"info"},{default:a(()=>[n(d,{"fixed-width":"",icon:["fas","people-group"]}),o(" Das ausgewählte Theme wird in unserer Community gepflegt. Rückfragen oder Probleme bitte im Forum diskutieren. ")]),_:1})),(s(),f(C(m.myComponent),{webTheme:l.webTheme,"onUpdate:configuration":t[0]||(t[0]=g=>m.updateConfiguration(g))},null,40,["webTheme"]))],64)}const I=w(F,[["render",G],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/web_themes/OpenwbWebThemeProxy.vue"]]),R={name:"OpenwbGeneralConfig",mixins:[T],components:{OpenwbWebThemeProxy:I},data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/general/control_interval","openWB/general/grid_protection_configured","openWB/general/external_buttons_hw","openWB/general/modbus_control","openWB/general/notifications/selected","openWB/general/notifications/configuration","openWB/general/notifications/start_charging","openWB/general/notifications/stop_charging","openWB/general/notifications/plug","openWB/general/notifications/smart_home","openWB/general/price_kwh","openWB/general/range_unit","openWB/general/web_theme","openWB/system/configurable/web_themes"]}},computed:{webThemeList:{get(){return this.$store.state.mqtt["openWB/system/configurable/web_themes"]}},webThemeGroupList:{get(){let e=[{label:"openWB",options:[]},{label:"Community",options:[]}];return this.webThemeList.forEach(t=>{t.official===!0?e[0].options.push(t):e[1].options.push(t)}),e}}},methods:{getWebThemeDefaults(e){const t=this.webThemeList.find(l=>l.value==e);return Object.prototype.hasOwnProperty.call(t,"defaults")?{...JSON.parse(JSON.stringify(t.defaults))}:(console.warn("no default configuration found for web theme type!",e),{})},updateSelectedWebTheme(e){this.updateState("openWB/general/web_theme",this.getWebThemeDefaults(e))},updateConfiguration(e,t){console.debug("updateConfiguration",e,t),this.updateState(e,t.value,t.object)}}},U={class:"generalConfig"},M={name:"generalConfigForm"},j=r("br",null,null,-1),K=r("br",null,null,-1),J=r("br",null,null,-1),H=r("a",{href:"https://openwb.de/main/?page_id=1025",target:"_blank",rel:"noopener noreferrer"}," Homepage ",-1),Z=r("a",{href:"https://openwb.de/main/wp-content/uploads/2023/10/ModbusTCP-openWB-series2-Pro-1.pdf",target:"_blank",rel:"noopener noreferrer"}," hier",-1),Q={key:0},X={key:0},Y={key:1},tt=r("br",null,null,-1),et=r("span",{class:"text-danger"},' Nicht nur die Regelung der PV geführten Ladung, sondern auch die Ladestromänderung, beispielsweise “Stop“ etc., werden dann nur noch in diesem Intervall ausgeführt. Die Regelung wird insgesamt träger. Solange es keinen triftigen Grund gibt, sollte "Normal" gewählt werden. ',-1),nt=r("br",null,null,-1),ot=r("span",{class:"text-danger"}," Die Option ist nur aktiv, wenn der EVU-Zähler die Frequenz übermittelt. ",-1),at={key:0},it={key:1},st={key:0},rt=r("hr",null,null,-1),ut=r("br",null,null,-1);function lt(e,t,l,_,v,m){const d=u("openwb-base-alert"),p=u("openwb-base-button-group-input"),g=u("openwb-base-card"),B=u("openwb-base-heading"),W=u("openwb-base-select-input"),y=u("openwb-web-theme-proxy"),k=u("openwb-base-number-input"),S=u("openwb-base-submit-buttons");return s(),b("div",U,[r("form",M,[n(g,{title:"Steuerungsmodus"},{default:a(()=>[n(d,{subtype:"info"},{default:a(()=>[o(' Wird für den Steuerungsmodus "primary" gewählt, übernimmt diese openWB die alleinige Regelung und steuert ggf. vorhandene weitere openWB (z.B. externe openWB im Steuermodus secondary, openWB Pro, Satellit u.a.) fern. Sie werden in den Ladepunkt-Einstellungen der primary-openWB hinzugefügt. '),j,K,o(' Wird für den Steuerungsmodus "secondary" gewählt, übernimmt diese openWB keine Regelung und muss von einer anderen primary openWB ferngesteuert werden. Wichtig ist, dass in der secondary-openWB eine "interne openWB" mit der korrekten Bauart (= openWB-Hardwarevariante z.B. "Custom, Standard, Standard+, Duo, Buchse") konfiguriert ist. Bei einer Duo sind zwei "interne openWB" zu konfigurieren. Im "secondary"-Modus bleiben alle ausgeblendeten Einstellungen unbeachtet.'),J,o(" Eine bebilderte Anleitung zur Konfiguration der Ladepunkte findest Du auf der "),H,o(". ")]),_:1}),n(p,{title:"Steuerungsmodus",buttons:[{buttonValue:!1,text:"primary",class:"btn-outline-danger"},{buttonValue:!0,text:"secondary",class:"btn-outline-success"}],"model-value":e.$store.state.mqtt["openWB/general/extern"],"onUpdate:modelValue":t[0]||(t[0]=i=>e.updateState("openWB/general/extern",i))},null,8,["model-value"]),n(p,{title:"Steuerung über Modbus als secondary",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":e.$store.state.mqtt["openWB/general/modbus_control"],"onUpdate:modelValue":t[1]||(t[1]=i=>e.updateState("openWB/general/modbus_control",i))},{help:a(()=>[o(" Im secondary-Modus kann die openWB über die Modbus-Schnittstelle gesteuert werden. Die Register sind "),Z,o("dokumentiert. Bei aktivierter Modbus-Schnittstelle darf die openWB nicht von einer primary-openWB gesteuert werden. ")]),_:1},8,["model-value"]),e.$store.state.mqtt["openWB/general/modbus_control"]===!0?(s(),b("div",Q,[n(d,{subtype:"info"},{default:a(()=>[o(' Wenn die Steuerung über Modbus auf "aus" geändert wird, muss danach ein Neustart durchgeführt werden! ')]),_:1})])):c("v-if",!0)]),_:1}),n(g,{title:"Hardware"},{default:a(()=>[e.$store.state.mqtt["openWB/general/extern"]===!0?(s(),b("div",X,[n(d,{subtype:"info"},{default:a(()=>[o(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(s(),b("div",Y,[n(p,{title:"Geschwindigkeit Regelintervall",buttons:[{buttonValue:10,text:"Normal",class:"btn-outline-success"},{buttonValue:20,text:"Langsam",class:"btn-outline-warning"},{buttonValue:60,text:"Sehr Langsam",class:"btn-outline-danger"}],"model-value":e.$store.state.mqtt["openWB/general/control_interval"],"onUpdate:modelValue":t[2]||(t[2]=i=>e.updateState("openWB/general/control_interval",i))},{help:a(()=>[o(' Sollten Probleme oder Fehlermeldungen auftauchen, stelle bitte zunächst das Regelintervall auf "Normal". Werden Module genutzt, welche z.B. eine Online-API zur Abfrage nutzen (höhere Latenzzeiten) oder möchte man weniger Regeleingriffe, so kann man das Regelintervall auf "Langsam" (20 Sekunden) herabsetzen. Die Einstellung „Sehr Langsam“ führt zu einer Regelzeit von 60 Sekunden.'),tt,et]),_:1},8,["model-value"]),n(p,{title:"Netzschutz",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":e.$store.state.mqtt["openWB/general/grid_protection_configured"],"onUpdate:modelValue":t[3]||(t[3]=i=>e.updateState("openWB/general/grid_protection_configured",i))},{help:a(()=>[o(' Diese Option ist standardmäßig aktiviert und sollte so belassen werden. Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert. Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert. Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generator-Betrieb umschaltet. Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.'),nt,ot]),_:1},8,["model-value"]),c(` <openwb-base-button-group-input
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
			</openwb-base-card> `),n(g,{title:"Darstellung"},{default:a(()=>[e.$store.state.mqtt["openWB/general/extern"]===!0?(s(),b("div",at,[n(d,{subtype:"info"},{default:a(()=>[o(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(s(),b("div",it,[n(B,{class:"mt-0"},{default:a(()=>[o(" Hauptseite ")]),_:1}),e.$store.state.mqtt["openWB/general/web_theme"]!==void 0?(s(),b("div",st,[n(W,{class:"mb-2",title:"Theme",groups:m.webThemeGroupList,"model-value":e.$store.state.mqtt["openWB/general/web_theme"].type,"onUpdate:modelValue":t[4]||(t[4]=i=>m.updateSelectedWebTheme(i))},null,8,["groups","model-value"]),e.$store.state.mqtt["openWB/general/web_theme"].type?(s(),f(y,{key:0,webTheme:e.$store.state.mqtt["openWB/general/web_theme"],"onUpdate:configuration":t[5]||(t[5]=i=>m.updateConfiguration("openWB/general/web_theme",i))},null,8,["webTheme"])):c("v-if",!0)])):c("v-if",!0),rt,n(B,null,{default:a(()=>[o(" Lade-Log ")]),_:1}),n(k,{title:"Preis je kWh",min:0,step:1e-4,unit:"€","model-value":e.$store.state.mqtt["openWB/general/price_kwh"],"onUpdate:modelValue":t[6]||(t[6]=i=>e.updateState("openWB/general/price_kwh",i))},{help:a(()=>[o(" Dient zur Berechnung der Ladekosten im Lade-Log."),ut,o(" Es können bis zu 4 Nachkommastellen genutzt werden. ")]),_:1},8,["model-value"]),n(p,{title:"Einheit für Entfernungen","model-value":e.$store.state.mqtt["openWB/general/range_unit"],"onUpdate:modelValue":t[7]||(t[7]=i=>e.updateState("openWB/general/range_unit",i)),buttons:[{buttonValue:"km",text:"Kilometer"},{buttonValue:"mi",text:"Meilen"}]},null,8,["model-value"])]))]),_:1}),n(S,{formName:"generalConfigForm",onSave:t[8]||(t[8]=i=>e.$emit("save")),onReset:t[9]||(t[9]=i=>e.$emit("reset")),onDefaults:t[10]||(t[10]=i=>e.$emit("defaults"))})])])}const wt=w(R,[["render",lt],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/GeneralConfig.vue"]]);export{wt as default};
