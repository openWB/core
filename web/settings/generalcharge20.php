<?php include_once __DIR__ . '/includes/header.inc.php'; ?>
	<div id="app">
		<content title="Allgemeine Einstellungen der Lademodi" footer="Lademodi" nav="navGeneralCharge">

			<card title="Allgemein">
				<div v-if="componentData['openWB/general/extern'] == true">
					<alert
						subtype="info">
						Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
					</alert>
				</div>
				<div v-if="componentData['openWB/general/extern'] == false">
					<buttongroup-input
						title="Lademodus"
						v-model="componentData['openWB/general/chargemode_config/individual_mode']"
						:buttons="[
							{buttonValue: false, text: 'Einheitlich'},
							{buttonValue: true, text: 'Individuell'}
						]">
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<hr>
					<buttongroup-input
						title="Begrenzung der Schieflast"
						v-model="componentData['openWB/general/chargemode_config/unbalanced_load']"
						toggle-selector='unbalancedOn'
						:buttons="[
							{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
							{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
						]">
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<div v-if="componentData['openWB/general/chargemode_config/unbalanced_load'] == true">
						<range-input
							title="Erlaubte Schieflast"
							:min=10 :max=32 :step=1
							v-model="componentData['openWB/general/chargemode_config/unbalanced_load_limit']"
							unit="A">
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
			'openWB/general/chargemode_config/individual_mode': false,
			'openWB/general/chargemode_config/unbalanced_load': false,
			'openWB/general/chargemode_config/unbalanced_load_limit': 20
		}
	</script>
<?php include_once __DIR__ . '/includes/footer.inc.php'; ?>
