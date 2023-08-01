import{C as f}from"./index-e3aeceea.js";import{_ as h,p as r,k as l,l as u,q as i,A as o,L as s,z as b,u as a}from"./vendor-20bb207d.js";import"./vendor-fortawesome-63a0ad05.js";import"./vendor-bootstrap-d275de6c.js";import"./vendor-jquery-89b63fca.js";import"./vendor-axios-13ef03ae.js";import"./vendor-sortablejs-ad1d2cc8.js";const v={name:"OpenwbGeneralConfig",mixins:[f],data(){return{mqttTopicsToSubscribe:["openWB/general/extern","openWB/general/extern_display_mode","openWB/general/control_interval","openWB/general/grid_protection_configured","openWB/general/external_buttons_hw","openWB/general/notifications/selected","openWB/general/notifications/configuration","openWB/general/notifications/start_charging","openWB/general/notifications/stop_charging","openWB/general/notifications/plug","openWB/general/notifications/smart_home","openWB/general/price_kwh","openWB/general/range_unit"]}}},B={class:"generalConfig"},_={name:"generalConfigForm"},w=i("br",null,null,-1),W=i("br",null,null,-1),z=i("br",null,null,-1),k=i("a",{href:"https://openwb.de/main/?page_id=1025",target:"_blank",rel:"noopener noreferrer"}," Homepage ",-1),S={key:0},$={key:1},x=i("br",null,null,-1),y=i("span",{class:"text-danger"},' Nicht nur die Regelung der PV geführten Ladung, sondern auch die Ladestromänderung, beispielsweise “Stop“ etc., werden dann nur noch in diesem Intervall ausgeführt. Die Regelung wird insgesamt träger. Solange es keinen triftigen Grund gibt, sollte "Normal" gewählt werden. ',-1),V=i("br",null,null,-1),q=i("span",{class:"text-danger"}," Die Option ist nur aktiv, wenn der EVU-Zähler die Frequenz übermittelt. ",-1),P={key:0},L={key:1},N=i("br",null,null,-1);function A(e,t,D,E,T,I){const p=r("openwb-base-alert"),d=r("openwb-base-button-group-input"),g=r("openwb-base-card"),m=r("openwb-base-number-input"),c=r("openwb-base-submit-buttons");return l(),u("div",B,[i("form",_,[o(g,{title:"Steuerungsmodus"},{default:s(()=>[o(p,{subtype:"info"},{default:s(()=>[a(' Wird für den Steuerungsmodus "primary" gewählt, übernimmt diese openWB die alleinige Regelung und steuert ggf. vorhandene weitere openWB (z.B. externe openWB im Steuermodus secondary, openWB Pro, Satellit u.a.) fern. Sie werden in den Ladepunkt-Einstellungen der primary-openWB hinzugefügt. '),w,W,a(' Wird für den Steuerungsmodus "secondary" gewählt, übernimmt diese openWB keine Regelung und muss von einer anderen primary openWB ferngesteuert werden. Wichtig ist, dass in der secondary-openWB eine "interne openWB" mit der korrekten Bauart (= openWB-Hardwarevariante z.B. "Custom, Standard, Standard+, Duo, Buchse") konfiguriert ist. Bei einer Duo sind zwei "interne openWB" zu konfigurieren. Im "secondary"-Modus bleiben alle ausgeblendeten Einstellungen unbeachtet.'),z,a(" Eine bebilderte Anleitung zur Konfiguration der Ladepunkte findest Du auf der "),k,a(". ")]),_:1}),o(d,{title:"Steuerungsmodus",buttons:[{buttonValue:!1,text:"primary",class:"btn-outline-danger"},{buttonValue:!0,text:"secondary",class:"btn-outline-success"}],"model-value":e.$store.state.mqtt["openWB/general/extern"],"onUpdate:modelValue":t[0]||(t[0]=n=>e.updateState("openWB/general/extern",n))},null,8,["model-value"]),b(` <openwb-base-select-input
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
				</openwb-base-select-input> `)]),_:1}),o(g,{title:"Hardware"},{default:s(()=>[e.$store.state.mqtt["openWB/general/extern"]===!0?(l(),u("div",S,[o(p,{subtype:"info"},{default:s(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(l(),u("div",$,[o(d,{title:"Geschwindigkeit Regelintervall",buttons:[{buttonValue:10,text:"Normal",class:"btn-outline-success"},{buttonValue:20,text:"Langsam",class:"btn-outline-warning"},{buttonValue:60,text:"Sehr Langsam",class:"btn-outline-danger"}],"model-value":e.$store.state.mqtt["openWB/general/control_interval"],"onUpdate:modelValue":t[1]||(t[1]=n=>e.updateState("openWB/general/control_interval",n))},{help:s(()=>[a(' Sollten Probleme oder Fehlermeldungen auftauchen, stelle bitte zunächst das Regelintervall auf "Normal". Werden Module genutzt, welche z.B. eine Online-API zur Abfrage nutzen (höhere Latenzzeiten) oder möchte man weniger Regeleingriffe, so kann man das Regelintervall auf "Langsam" (20 Sekunden) herabsetzen. Die Einstellung „Sehr Langsam“ führt zu einer Regelzeit von 60 Sekunden.'),x,y]),_:1},8,["model-value"]),o(d,{title:"Netzschutz",buttons:[{buttonValue:!1,text:"Aus",class:"btn-outline-danger"},{buttonValue:!0,text:"An",class:"btn-outline-success"}],"model-value":e.$store.state.mqtt["openWB/general/grid_protection_configured"],"onUpdate:modelValue":t[2]||(t[2]=n=>e.updateState("openWB/general/grid_protection_configured",n))},{help:s(()=>[a(' Diese Option ist standardmäßig aktiviert und sollte so belassen werden. Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert. Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert. Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generator-Betrieb umschaltet. Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.'),V,q]),_:1},8,["model-value"]),b(` <openwb-base-button-group-input
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
					</openwb-base-button-group-input> `)]))]),_:1}),b(` <openwb-base-card title="Benachrichtigungen">
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
			</openwb-base-card> `),o(g,{title:"Lade-Log"},{default:s(()=>[e.$store.state.mqtt["openWB/general/extern"]===!0?(l(),u("div",P,[o(p,{subtype:"info"},{default:s(()=>[a(' Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Steuerungsmodus "secondary" befindet. ')]),_:1})])):(l(),u("div",L,[o(m,{title:"Preis je kWh",min:0,step:1e-4,unit:"€","model-value":e.$store.state.mqtt["openWB/general/price_kwh"],"onUpdate:modelValue":t[3]||(t[3]=n=>e.updateState("openWB/general/price_kwh",n))},{help:s(()=>[a(" Dient zur Berechnung der Ladekosten im Lade-Log."),N,a(" Es können bis zu 4 Nachkommastellen genutzt werden. ")]),_:1},8,["model-value"]),o(d,{title:"Einheit für Entfernungen","model-value":e.$store.state.mqtt["openWB/general/range_unit"],"onUpdate:modelValue":t[4]||(t[4]=n=>e.updateState("openWB/general/range_unit",n)),buttons:[{buttonValue:"km",text:"Kilometer"},{buttonValue:"mi",text:"Meilen"}]},null,8,["model-value"])]))]),_:1}),o(c,{formName:"generalConfigForm",onSave:t[5]||(t[5]=n=>e.$emit("save")),onReset:t[6]||(t[6]=n=>e.$emit("reset")),onDefaults:t[7]||(t[7]=n=>e.$emit("defaults"))})])])}const Z=h(v,[["render",A],["__file","/opt/openWB-dev/openwb-ui-settings/src/views/GeneralConfig.vue"]]);export{Z as default};
