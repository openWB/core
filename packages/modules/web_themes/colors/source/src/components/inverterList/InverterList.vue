<template>
	<WBWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-solar-panel me-2" style="color: var(--color-pv)"
				>&nbsp;</span
			>
			<span>Wechselrichter</span>
		</template>
		<template #buttons>
			<WbBadge v-if="sourceSummary.pv.power > 0" bgcolor="var(--color-pv)">
				{{ formatWatt(sourceSummary.pv.power) }}
			</WbBadge>
		</template>
		<div v-for="[key, pvsystem] in pvSystems" :key="key" class="subgrid pb-2">
			<IlInverter :inverter="pvsystem" />
		</div>
	</WBWidgetFlex>
</template>

<script setup lang="ts">
import WBWidgetFlex from '../shared/WbWidgetFlex.vue'
import IlInverter from './IlInverter.vue'
import WbBadge from '../shared/WbBadge.vue'
import { pvSystems, sourceSummary } from '@/assets/js/model'
import { formatWatt } from '@/assets/js/helpers'
</script>

<style scoped>
.powerWbBadge {
	background-color: var(--color-pv);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
</style>
