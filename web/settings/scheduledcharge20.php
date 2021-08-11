<?php include_once __DIR__ . '/includes/header.inc.php'; ?>
<div id="app">
	<content title="Einstellungen Zielladen" footer="Zielladen" nav="navScheduledCharge">

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
					v-model="componentData['openWB/general/chargemode_config/scheduled_charging/phases_to_use']"
					:buttons="[
						{buttonValue: 1, text: '1'},
						{buttonValue: 3, text: 'Maximum'},
						{buttonValue: 0, text: 'Automatisch'}
					]">
					<template #help>
						ToDo
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
		'openWB/general/chargemode_config/scheduled_charging/phases_to_use': 0
	}
</script>
<?php include_once __DIR__ . '/includes/footer.inc.php'; ?>
