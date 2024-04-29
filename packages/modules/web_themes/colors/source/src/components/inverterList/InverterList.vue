<template>
	<WBWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-solar-panel me-2" style="color: var(--color-pv)"
				>&nbsp;</span
			>
			<span>Wechselrichter</span>
		</template>
		<div
			v-for="(pvsystem, index) in inverters"
			:key="index"
			class="subgrid pb-2"
		>
			<IlInverter :inverter="pvsystem" />
		</div>
	</WBWidgetFlex>
</template>

<script setup lang="ts">
//import { computed } from 'vue'
import { computed } from 'vue'
import WBWidgetFlex from '../shared/WbWidgetFlex.vue'
import IlInverter from './IlInverter.vue'
import { pvSystems } from '@/assets/js/model'

const inverters = computed(() => {
	return pvSystems.value.values()
})
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
