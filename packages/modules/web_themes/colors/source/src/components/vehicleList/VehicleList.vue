<template>
	<WBWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-car me-2" style="color: var(--color-charging)"
				>&nbsp;</span
			>
			<span>Fahrzeuge</span>
		</template>
		<div
			v-for="(vehicle, index) in Object.values(vehicles).slice().reverse()"
			:key="index"
			class="subgrid"
		>
			<VlVehicle :vehicle="vehicle" />
		</div>
	</WBWidgetFlex>
</template>

<script setup lang="ts">
//import { computed } from 'vue'
import WBWidgetFlex from '../shared/WbWidgetFlex.vue'
import VlVehicle from './VlVehicle.vue'
import { vehicles } from '@/components/chargePointList/model'
</script>

<style scoped>
.statusbutton {
	font-size: var(--font-large);
}

.modebutton {
	background-color: var(--color-menu);
	font-size: var(--font-verysmall);
	font-weight: normal;
}

.tempbadge {
	background-color: var(--color-battery);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
</style>
