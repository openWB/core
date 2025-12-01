<template>
	<WBWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-solar-panel me-2" style="color: var(--color-pv)"
				>&nbsp;</span
			>
			<span>Wechselrichter</span>
		</template>
		<template #buttons>
			<WbBadge v-if="registry.getPower('pv') > 0" bgcolor="var(--color-pv)">
				{{ formatWatt(registry.getPower('pv')) }}
			</WbBadge>
		</template>
		<div
			v-for="inverter in sortedInverters"
			:key="inverter.id"
			class="subgrid pb-2"
		>
			<IlInverter :inverter="inverter" />
		</div>
	</WBWidgetFlex>
</template>

<script setup lang="ts">
import WBWidgetFlex from '../shared/WbWidgetFlex.vue'
import IlInverter from './IlInverter.vue'
import WbBadge from '../shared/WbBadge.vue'
import { pvSystems, registry } from '@/assets/js/model'
import { formatWatt } from '@/assets/js/helpers'
import { computed } from 'vue'

const sortedInverters = computed(() => {
	return [...pvSystems.value.values()].sort((a, b) => a.id - b.id)
})
</script>

<style scoped>
.powerWbBadge {
	background-color: var(--color-pv);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
</style>
