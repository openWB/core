<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="invertername" :style="invertercolor"
				>{{ inverter.name }}
			</span>
		</template>
		<template #buttons>
			<WbBadge v-if="props.inverter.power < 0" bgcolor="var(--color-pv)"
				>{{ formatWatt(-props.inverter.power) }}
			</WbBadge>
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Heute:" :small="true" class="grid-col-4 grid-left">
				<FormatWattH :watt-h="props.inverter.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Monat:" :small="true" class="grid-col-4">
				<FormatWattH :watt-h="props.inverter.energy_month"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Jahr:" :small="true" class="grid-right grid-col-4">
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
import WbBadge from '../shared/WbBadge.vue'
import { computed } from 'vue'
import { formatWatt } from '@/assets/js/helpers'
const props = defineProps<{
	inverter: PvSystem
}>()

const invertercolor = computed(() => {
	return { color: props.inverter.color }
})
</script>
<style scoped>
.modeWbBadge {
	background-color: var(--color-pv);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
.invertername {
	font-size: var(--font-medium);
}
</style>
