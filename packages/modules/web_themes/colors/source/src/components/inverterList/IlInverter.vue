<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="invertername" :style="invertercolor"
				>{{ inverter.name }}
			</span>
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span
					v-if="props.inverter.power > 0"
					class="badge rounded-pill modebadge mx-2"
					:style="modestyle"
					>{{ modestring }}</span
				>
			</div>
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Leistung:" :small="true" class="grid-left grid-col-3">
				<FormatWatt :watt="Math.abs(props.inverter.power)"></FormatWatt>
			</InfoItem>
			<InfoItem heading="Heute:" :small="true" class="grid-col-3">
				<FormatWattH :watt-h="props.inverter.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Monat:" :small="true" class="grid-right grid-col-3">
				<FormatWattH :watt-h="props.inverter.energy_month"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Jahr:" :small="true" class="grid-right grid-col-3">
				<FormatWattH :watt-h="props.inverter.energy_year"></FormatWattH>
			</InfoItem>
		</div>
	</WbSubwidget>
</template>
<script setup lang="ts">
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
import type { PvSystem } from '@/assets/js/types'
import FormatWattH from '../shared/FormatWattH.vue'
import FormatWatt from '../shared/FormatWatt.vue'
import { computed } from 'vue'
const props = defineProps<{
	inverter: PvSystem
}>()

const modestring = computed(() => {
	if (props.inverter.power > 0) {
		return 'Altiv'
	} else {
		return ''
	}
})
const invertercolor = computed(() => {
	return { color: props.inverter.color }
})
const modestyle = computed(() => {
	let col = ''
	if (props.inverter.power > 0) {
		col = 'var(--color-pv)'
	} else {
		col = 'var(--color-evu)'
	}
	return { 'background-color': col, 'font-weight': 'normal' }
})
</script>
<style scoped>
.idbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}

.invertername {
	font-size: var(--font-normal);
}
</style>
