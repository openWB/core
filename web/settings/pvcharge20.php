<?php include_once __DIR__ . '/includes/header.inc.php'; ?>
<div id="app">
	<content title="Einstellungen PV-Laden" footer="PV-Laden" nav="navPVCharge">

		<card title="Regelparameter">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Regelmodus"
					v-model="componentData['ToDo/pv_charge/control_mode']"
					linked-component="openWB/general/chargemode_config/pv_charging/control_range"
					:buttons="[
						{buttonValue: 'export', text: 'Einspeisung', linkedComponentValue: [-230,0]},
						{buttonValue: 'import', text: 'Bezug', linkedComponentValue: [0,230]},
						{buttonValue: 'individual', text: 'Individuell'}
					]">
					<template #help>
						ToDo: Werte Setzen
					</template>
				</buttongroup-input>
				<text-input
					title="Regelbereich"
					subtype="json"
					disabled="disabled"
					v-model="componentData['openWB/general/chargemode_config/pv_charging/control_range']">
					<template #help>
						Nur zur Info
					</template>
				</text-input>
				<div v-if="componentData['ToDo/pv_charge/control_mode'] == 'individual'">
					<number-input
						title="Minimum"
						:min=-10000 :max=10000
						v-model="componentData['openWB/general/chargemode_config/pv_charging/control_range'][0]"
						unit="W">
					</number-input>
					<number-input
						title="Maximum"
						:min=-10000 :max=10000
						v-model="componentData['openWB/general/chargemode_config/pv_charging/control_range'][1]"
						unit="W">
					</number-input>
				</div>
				<number-input
					title="Regelpunkt Einspeisegrenze"
					:min=0 :step=50
					v-model="componentData['openWB/general/chargemode_config/pv_charging/feed_in_yield']"
					unit="W">
					<template #help>
						Parameter für den 70%-Regelpunkt im Modus PV-Laden. Dieser Parameter ist nur wirksam bei der Einstellung "70%-Regelung eingeschaltet". Der hier eingetragene Wert sollte zur optimalen Eigenverbrauchssteuerung 70% der installierten Generatorleistung betragen.<br>
						Die Nutzung dieser Option ergibt nur Sinn wenn ein Wechselrichter und Smartmeter verbaut ist welches eine dynamische Begrenzung der Einspeiseleistung bietet.
					</template>
				</number-input>
				<hr>
				<number-input
					title="Einschaltschwelle"
					:min=0 :step=1
					v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_on_threshold']"
					unit="W">
				</number-input>
				<number-input
					title="Einschaltverzögerung"
					:min=0 :step=1
					v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_on_delay']"
					unit="Sek.">
				</number-input>
				<hr>
				<number-input
					title="Abschaltschwelle"
					:min=0 :step=1
					v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_off_threshold']"
					unit="W">
				</number-input>
				<number-input
					title="Abschaltverzögerung"
					:min=0 :step=1
					v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_off_delay']"
					unit="Sek.">
				</number-input>
			</div>
		</card>

		<card title="Phasenumschaltung">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Anzahl Phasen"
					v-model="componentData['openWB/general/chargemode_config/pv_charging/phases_to_use']"
					:buttons="[
						{buttonValue: 1, text: '1'},
						{buttonValue: 3, text: 'Maximum'},
						{buttonValue: 0, text: 'Automatisch'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<div v-if="componentData['openWB/general/chargemode_config/pv_charging/phases_to_use'] == 0">
					<range-input
						title="Schaltzeiten Automatikmodus"
						:min=1 :max=15 :step=1
						v-model="componentData['openWB/general/chargemode_config/pv_charging/phase_switch_delay']"
						unit="Min.">
						<template #help>
							Um zu viele Schaltungen im Automatikmodus zu vermeiden, wird hier definiert, wann die Umschaltung erfolgen soll. Ist bei einphasigen Laden für durchgehend x Minuten die Maximalstromstärke erreicht, wird auf dreiphasige Ladung umgestellt. Ist die Ladung nur für ein Intervall unterhalb der Maximalstromstärke, beginnt der Counter für die Umschaltung erneut. Ist die Ladung im dreiphasigen Modus für 16 - x Minuten bei der Minimalstromstärke, wird wieder auf einphasige Ladung gewechselt.<br>
							Standardmäßig ist dieser Wert bei 8 Minuten, sprich nach 8 Minuten Maximalstromstärke wird auf 3 Phasige Ladung umgestellt und nach 16 - 8 = 8 Minuten bei Minimalstromstärke wird wieder auf einphasige Ladung gewechselt.
						</template>
					</range-input>
				</div>
			</div>
		</card>

		<card title="Speicher-Beachtung" subtype="warning">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<div v-if="componentData['openWB/bat/config/configured'] == false">
					<alert
						subtype="info">
						Diese Einstellungen sind nur verfügbar, wenn ein Speicher konfiguriert wurde.
					</alert>
				</div>
				<div v-if="componentData['openWB/bat/config/configured'] == true">
					<buttongroup-input
						title="Priorisierung"
						v-model="componentData['openWB/general/chargemode_config/pv_charging/bat_prio']"
						:buttons="[
							{buttonValue: false, text: 'Fahrzeuge'},
							{buttonValue: true, text: 'Speicher'}
						]">
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<range-input
						title="Einschalt-SoC"
						:min=0 :max=19 :step=1
						v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_on_soc']"
						unit="%"
						:labels='[{"label":"Aus","value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
					<range-input
						title="Ausschalt-SoC"
						:min=0 :max=19 :step=1
						v-model="componentData['openWB/general/chargemode_config/pv_charging/switch_off_soc']"
						unit="%"
						:labels='[{"label":"Aus","value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
					<number-input
						v-if="componentData['openWB/general/chargemode_config/pv_charging/bat_prio'] == false"
						title="Reservierte Ladeleistung"
						:min=0 :step=100
						v-model="componentData['openWB/general/chargemode_config/pv_charging/charging_power_reserve']"
						unit="W">
						<template #help>
							ToDo
						</template>
					</number-input>
					<number-input
						v-if="componentData['openWB/general/chargemode_config/pv_charging/bat_prio'] == true"
						title="Erlaubte Entladeleistung"
						:min=0 :step=100
						v-model="componentData['openWB/general/chargemode_config/pv_charging/rundown_power']"
						unit="W">
						<template #help>
							ToDo
						</template>
					</number-input>
					<range-input
						v-if="componentData['openWB/general/chargemode_config/pv_charging/bat_prio'] == true"
						title="Minimaler Entlade-SoC"
						:min=0 :max=20 :step=1
						v-model="componentData['openWB/general/chargemode_config/pv_charging/rundown_soc']"
						unit="%"
						:labels='[{"label":0,"value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95},{"label":"Aus","value":100}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
				</div>
			</div>
		</card>

	</content>
</div><!-- app -->

<script>
	// define topics and default values here
	const componentDefaultData = {
		'openWB/general/extern': false,
		'openWB/bat/config/configured': false,
		'ToDo/pv_charge/control_mode': "export",
		'openWB/general/chargemode_config/pv_charging/control_range': [-230,0],
		'openWB/general/chargemode_config/pv_charging/feed_in_yield': 0,
		'openWB/general/chargemode_config/pv_charging/switch_on_threshold': 1320,
		'openWB/general/chargemode_config/pv_charging/switch_on_delay': 20,
		'openWB/general/chargemode_config/pv_charging/switch_off_threshold': 0,
		'openWB/general/chargemode_config/pv_charging/switch_off_delay': 60,
		'openWB/general/chargemode_config/pv_charging/phases_to_use': 0,
		'openWB/general/chargemode_config/pv_charging/phase_switch_delay': 8,
		'openWB/general/chargemode_config/pv_charging/bat_prio': true,
		'openWB/general/chargemode_config/pv_charging/switch_on_soc': 0,
		'openWB/general/chargemode_config/pv_charging/switch_off_soc': 0,
		'openWB/general/chargemode_config/pv_charging/charging_power_reserve': 0,
		'openWB/general/chargemode_config/pv_charging/rundown_power': 0,
		'openWB/general/chargemode_config/pv_charging/rundown_soc': 0
	}
</script>
<?php include_once __DIR__ . '/includes/footer.inc.php'; ?>
