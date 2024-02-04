<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="countername">{{ counter.name }} </span>
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span
					v-if="props.counter.power != 0"
					class="badge rounded-pill modebadge mx-2"
					:style="modestyle"
					>{{ modestring }}</span
				>
				<span class="badge rounded-pill idbadge mx-2"
					>ID: {{ props.counter.id }}</span
				>
			</div>
		</template>
		<div class="d-flex justify-content-between pb-2">
			<InfoItem heading="Leistung:" :small="true">
				<FormatWatt :watt="Math.abs(props.counter.power)"></FormatWatt>
			</InfoItem>
			<InfoItem heading="Bezogen:" :small="true">
				<FormatWattH :watt-h="props.counter.energy_imported"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Exportiert:" :small="true">
				<FormatWattH :watt-h="props.counter.energy_exported"></FormatWattH>
			</InfoItem>
		</div>
	</WbSubwidget>
</template>
<script setup lang="ts">
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
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

const modestyle = computed(() => {
	let col = ''
	if (props.counter.power > 0) {
		col = 'var(--color-evu)'
	} else {
		col = 'var(--color-pv)'
	}
	return { 'background-color': col, 'font-weight': 'normal' }
})
</script>
<style scoped>
.idbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}

.countername {
	font-size: var(--font-medium);
}
</style>
