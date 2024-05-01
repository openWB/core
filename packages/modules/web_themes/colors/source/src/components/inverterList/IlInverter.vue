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
					v-if="props.inverter.power < 0"
					class="my-0 badge rounded-pill modebadge mx-1"
					>{{ formatWatt(-props.inverter.power) }}
				</span>
			</div>
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Heute:" :small="false" class="grid-col-4">
				<FormatWattH :watt-h="props.inverter.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Monat:" :small="false" class="grid-right grid-col-4">
				<FormatWattH :watt-h="props.inverter.energy_month"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Jahr:" :small="false" class="grid-right grid-col-4">
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
.modebadge {
	background-color: var(--color-pv);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
.invertername {
	font-size: var(--font-normal);
}
</style>
