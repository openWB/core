<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="countername">{{ counter.name }} </span>
		</template>
		<template #buttons>
			<WbBadge v-if="props.counter.power != 0" :bgcolor="modebg">
				{{ modestring }}
			</WbBadge>
			<WbBadge color="var(--color-bg)"> ID: {{ props.counter.id }} </WbBadge>
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Leistung:" :small="true" class="grid-left grid-col-4">
				<FormatWatt :watt="Math.abs(props.counter.power)"></FormatWatt>
			</InfoItem>
			<InfoItem heading="Bezogen:" :small="true" class="grid-col-4">
				<FormatWattH :watt-h="props.counter.energy_imported"></FormatWattH>
			</InfoItem>
			<InfoItem
				heading="Exportiert:"
				:small="true"
				class="grid-right grid-col-4"
			>
				<FormatWattH :watt-h="props.counter.energy_exported"></FormatWattH>
			</InfoItem>
		</div>
	</WbSubwidget>
</template>
<script setup lang="ts">
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
import WbBadge from '../shared/WbBadge.vue'
import type { Counter } from './model'
import FormatWattH from '../shared/FormatWattH.vue'
import FormatWatt from '../shared/FormatWatt.vue'
import { computed } from 'vue'
const props = defineProps<{
	counter: Counter
}>()

const modestring = computed(() => {
	if (props.counter.power > 0) {
		return 'Bezug'
	} else {
		return 'Export'
	}
})

const modebg = computed(() => {
	if (props.counter.power > 0) {
		return 'var(--color-evu)'
	} else {
		return 'var(--color-pv)'
	}
})
</script>
<style scoped>
.idWbBadge {
	background-color: var(--color-menu);
	font-weight: normal;
}

.countername {
	font-size: var(--font-medium);
}
</style>
