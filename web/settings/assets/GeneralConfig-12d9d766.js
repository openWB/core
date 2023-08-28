import{C as h}from"./index-4a8bd4a5.js";import{_ as v,p as u,k as r,l as d,q as s,A as a,L as i,z as p,u as o,y as m}from"./vendor-6e5b23b4.js";import"./vendor-fortawesome-396ff0d4.js";import"./vendor-bootstrap-6c75b4fa.js";import"./vendor-jquery-921f231b.js";import"./vendor-axios-86f7a224.js";import"./vendor-sortablejs-b3476726.js";const B={name:"OpenwbGeneralConfig",mixins:[h],data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/general/extern_display_mode","openWB/general/control_interval","openWB/general/grid_protection_configured","openWB/general/external_buttons_hw","openWB/general/modbus_control","openWB/general/notifications/selected","openWB/general/notifications/configuration","openWB/general/notifications/start_charging","openWB/general/notifications/stop_charging","openWB/general/notifications/plug","openWB/general/notifications/smart_home","openWB/general/price_kwh","openWB/general/range_unit"]}}},W={class:"generalConfig"},_={name:"generalConfigForm"},w=s("br",null,null,-1),k=s("br",null,null,-1),z=s("br",null,null,-1),S=s("a",{href:"https://openwb.de/main/?page_id=1025",target:"_blank",rel:"noopener noreferrer"}," Homepage ",-1),$=s("a",{href:"https://openwb.de/main/?page_id=628",target:"_blank",rel:"noopener noreferrer"},"hier ",-1),y={key:0},V={key:1},x=s("br",null,null,-1),q=s("span",{class:"text-danger"},' Nicht nur die Regelung der PV geführten Ladung, sondern auch die Ladestromänderung, beispielsweise “Stop“ etc., werden dann nur noch in diesem Intervall ausgeführt. Die Regelung wird insgesamt träger. Solange es keinen triftigen Grund gibt, sollte "Normal" gewählt werden. ',-1),P=s("br",null,null,-1),L=s("span",{class:"text-danger"}," Die Option ist nur aktiv, wenn der EVU-Zähler die Frequenz übermittelt. ",-1),A={key:0},D={key:1},N=s("br",null,null,-1);function E(t,e,T,I,C,G){const g=u("openwb-base-alert"),l=u("openwb-base-button-group-input"),b=u("openwb-base-card"),c=u("openwb-base-number-input"),f=u("openwb-base-submit-buttons");return r(),d("div",W,[s("form",_,[a(b,{title:"Steuerungsmodus"},{default:i(()=>[a(g,{subtype:"info"},{default:i(()=>[o(' Wird für den Steuerungsmodus "primary" gewählt, übernimmt diese openWB die alleinige Regelung und steuert ggf. vorhandene weitere openWB (z.B. externe openWB im Steuermodus secondary, openWB Pro, Satellit u.a.) fern. Sie werden in den Ladepunkt-Einstellungen der primary-openWB hinzugefügt. '),w,k,o(' Wird für den Steuerungsmodus "secondary" gewählt, übernimmt diese openWB keine Regelung und muss von einer anderen primary openWB ferngesteuert werden. Wichtig ist, dass in der secondary-openWB eine "interne openWB" mit der korrekten Bauart (= openWB-Hardwarevariante z.B. "Custom, Standard, Standard+, Duo, Buchse") konfiguriert ist. Bei einer Duo sind zwei "interne openWB" zu konfigurieren. Im "secondary"-Modus bleiben alle ausgeblendeten Einstellungen unbeachtet.'),z,o(" Eine bebilderte Anleitung zur Konfiguration der Ladepunkte findest Du auf der "),S,o(". ")]),_:1}),a(l,{title:"Steuerungsmodus",buttons:[{buttonValue:!1,text:"primary",class:"btn-outline-danger"},{buttonValue:!0,text:"secondary",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/extern"],"onUpdate:modelValue":e[0]||(e[0]=n=>t.updateState("openWB/general/extern",n))},null,8,["model-value"]),t.$store.state.mqtt["openWB/general/extern"]===!0?(r(),m(l,{key:0,title:"Steuerung über Modbus",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/modbus_control"],"onUpdate:modelValue":e[1]||(e[1]=n=>t.updateState("openWB/general/modbus_control",n))},{help:i(()=>[o(" Im secondary-Modus kann die openWB über die Modbus-Schnittstelle gesteuert werden. Die Register sind "),$,o(" dokumentiert. Die aktivierter Modbus-Schnittstelle darf die openWB nicht von einer primary-openWB gesteuert werden. ")]),_:1},8,["model-value"])):p("v-if",!0),t.$store.state.mqtt["openWB/general/modbus_control"]===!0?(r(),m(g,{key:1,subtype:"info"},{default:i(()=>[o(' Wenn die Steuerung über Modbus auf "aus" geändert wird, muss danach ein Neustart durchgeführt werden! ')]),_:1})):p("v-if",!0),p(` <openwb-base-select-input
					v-if="$store.state.mqtt['openWB/general/extern'] === true"
					title="Display-Theme"
					:options="[
						{
							value: 'local',
							text: 'Normal',
						},
						{
							value: 'main',
							text: 'Anzeige der übergeordneten openWB',
						},
					]"
					:model-value="
						$store.state.mqtt['openWB/general/extern_display_mode']
					"
					@update:model-value="
						updateState(
							'openWB/general/extern_display_mode',
							$event
						)
					"
				>
					<template #help>
						Das Theme "Normal" zeigt lediglich die Ladeleistung des
						Ladepunktes an. Änderungen sind nicht möglich.<br />
						Wird hier "Anzeige der übergeordneten openWB"
						ausgewählt, dann ist die Darstellung identisch zum
						Display der regelnden openWB. Alle Anzeigen und
						Änderungen sind möglich.
					</template>
				</openwb-base-select-input> `)]),_:1}),a(b,{title:"Hardware"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(r(),d("div",y,[a(g,{subtype:"info"},{default:i(()=>[o(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(r(),d("div",V,[a(l,{title:"Geschwindigkeit Regelintervall",buttons:[{buttonValue:10,text:"Normal",class:"btn-outline-success"},{buttonValue:20,text:"Langsam",class:"btn-outline-warning"},{buttonValue:60,text:"Sehr Langsam",class:"btn-outline-danger"}],"model-value":t.$store.state.mqtt["openWB/general/control_interval"],"onUpdate:modelValue":e[2]||(e[2]=n=>t.updateState("openWB/general/control_interval",n))},{help:i(()=>[o(' Sollten Probleme oder Fehlermeldungen auftauchen, stelle bitte zunächst das Regelintervall auf "Normal". Werden Module genutzt, welche z.B. eine Online-API zur Abfrage nutzen (höhere Latenzzeiten) oder möchte man weniger Regeleingriffe, so kann man das Regelintervall auf "Langsam" (20 Sekunden) herabsetzen. Die Einstellung „Sehr Langsam“ führt zu einer Regelzeit von 60 Sekunden.'),x,q]),_:1},8,["model-value"]),a(l,{title:"Netzschutz",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":t.$store.state.mqtt["openWB/general/grid_protection_configured"],"onUpdate:modelValue":e[3]||(e[3]=n=>t.updateState("openWB/general/grid_protection_configured",n))},{help:i(()=>[o(' Diese Option ist standardmäßig aktiviert und sollte so belassen werden. Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert. Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert. Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generator-Betrieb umschaltet. Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.'),P,L]),_:1},8,["model-value"]),p(` <openwb-base-button-group-input
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
					</openwb-base-button-group-input> `)]))]),_:1}),p(` <openwb-base-card title="Benachrichtigungen">
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
			</openwb-base-card> `),a(b,{title:"Lade-Log"},{default:i(()=>[t.$store.state.mqtt["openWB/general/extern"]===!0?(r(),d("div",A,[a(g,{subtype:"info"},{default:i(()=>[o(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(r(),d("div",D,[a(c,{title:"Preis je kWh",min:0,step:1e-4,unit:"€","model-value":t.$store.state.mqtt["openWB/general/price_kwh"],"onUpdate:modelValue":e[4]||(e[4]=n=>t.updateState("openWB/general/price_kwh",n))},{help:i(()=>[o(" Dient zur Berechnung der Ladekosten im Lade-Log."),N,o(" Es können bis zu 4 Nachkommastellen genutzt werden. ")]),_:1},8,["model-value"]),a(l,{title:"Einheit für Entfernungen","model-value":t.$store.state.mqtt["openWB/general/range_unit"],"onUpdate:modelValue":e[5]||(e[5]=n=>t.updateState("openWB/general/range_unit",n)),buttons:[{buttonValue:"km",text:"Kilometer"},{buttonValue:"mi",text:"Meilen"}]},null,8,["model-value"])]))]),_:1}),a(f,{formName:"generalConfigForm",onSave:e[6]||(e[6]=n=>t.$emit("save")),onReset:e[7]||(e[7]=n=>t.$emit("reset")),onDefaults:e[8]||(e[8]=n=>t.$emit("defaults"))})])])}const H=v(B,[["render",E],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/GeneralConfig.vue"]]);export{H as default};
