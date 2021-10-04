<?php include_once __DIR__ . '/includes/header.inc.php'; ?>
<div id="app">
	<content title="Einstellungen Standby" footer="Standby" nav="navStandby">

		<card title="Phasenumschaltung">
			<div v-show="visibility.extOpenWBOn">
				<alert
					subtype="info">
					Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
				</alert>
			</div>
			<div v-show="!visibility.extOpenWBOn">
				<buttongroup-input
					title="Anzahl Phasen"
					v-model="componentData['openWB/general/chargemode_config/standby/phases_to_use']"
					:buttons="[
						{buttonValue: 1, text: '1'},
						{buttonValue: 3, text: 'Maximum'}
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
		'openWB/general/chargemode_config/standby/phases_to_use': 1
	}
</script>
<?php include_once __DIR__ . '/includes/footer.inc.php'; ?>
