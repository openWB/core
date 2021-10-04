<?php include_once __DIR__ . '/includes/header.inc.php'; ?>
<div id="app">
	<content title="Einstellungen Diagramm" footer="Diagramm" nav="navGraphSettings">

		<card title="Allgemein">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Diagramm anzeigen"
					v-model="componentData['ToDo/graph/display']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<div v-if="componentData['ToDo/graph/display']">
					<buttongroup-input
						title="Legende"
						v-model="componentData['ToDo/graph/legend']"
						:buttons="[
							{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
							{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
						]">
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
				</div>
			</div>
		</card>

		<card title="EVU" subtype="danger" v-if="componentData['ToDo/graph/display']">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Gesamtleistung"
					v-model="componentData['ToDo/graph/grid']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<buttongroup-input
					title="Hausverbrauch"
					v-model="componentData['ToDo/graph/homeconsumption']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
			</div>
		</card>

		<card title="Ladepunkte" subtype="primary" v-if="componentData['ToDo/graph/display']">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Summe Ladepunktleistungen"
					v-model="componentData['ToDo/graph/chargepointsum']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<hr>
				<heading>
					Ladepunktleistungen
				</heading>
				<buttongroup-input
					title="Ladepunkt 1"
					v-model="componentData['ToDo/graph/chargepoints/1']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo: für alle Ladepunkte
					</template>
				</buttongroup-input>
			</div>
		</card>

		<card title="PV-Anlagen" subtype="success" v-if="componentData['ToDo/graph/display']">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Summe PV-Leistungen"
					v-model="componentData['ToDo/graph/pvsum']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<hr>
				<heading>
					Einzelleistungen
				</heading>
				<buttongroup-input
					title="PV 1"
					v-model="componentData['ToDo/graph/pv/1']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo: für alle PV-Anlagen
					</template>
				</buttongroup-input>
			</div>
		</card>

		<card title="Batteriespeicher" subtype="warning" v-if="componentData['ToDo/graph/display']">
			<div v-if="componentData['openWB/general/extern'] === true">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-if="componentData['openWB/general/extern'] === false">
				<buttongroup-input
					title="Summe Speichereistungen"
					v-model="componentData['ToDo/graph/batsum']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo
					</template>
				</buttongroup-input>
				<hr>
				<heading>
					Einzelleistungen
				</heading>
				<buttongroup-input
					title="Speicher 1"
					v-model="componentData['ToDo/graph/bat/1']"
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]">
					<template #help>
						ToDo: für alle Batteriespeicher
					</template>
				</buttongroup-input>
			</div>
		</card>

	</content>
</div><!-- app -->

<script>
	// define topics and default values here
	const componentDefaultData = {
		'openWB/general/extern': false,
		'ToDo/graph/display': true,
		'ToDo/graph/legend': true,
		'ToDo/graph/grid': true,
		'ToDo/graph/homeconsumption': true,
		'ToDo/graph/chargepointsum': true,
		'ToDo/graph/chargepoints/1': true,
		'ToDo/graph/pvsum': true,
		'ToDo/graph/pv/1': true,
		'ToDo/graph/batsum': true,
		'ToDo/graph/bat/1': true
	}
</script>
<?php include_once __DIR__ . '/includes/footer.inc.php'; ?>
