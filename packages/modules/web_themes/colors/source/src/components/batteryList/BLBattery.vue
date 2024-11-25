/* * BLBattery.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="battery-title">{{ bat.name }}</span>
		</template>
		<template #buttons>
			<WbBadge :bgcolor="statusbg">{{ batteryState }}</WbBadge>
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Ladestand:" :small="true" class="grid-left grid-col-4">
				<BatterySymbol :soc="props.bat.soc"></BatterySymbol>
			</InfoItem>

			<InfoItem heading="Geladen:" :small="true" class="grid-col-4">
				<FormatWattH :watt-h="props.bat.dailyYieldImport"></FormatWattH>
			</InfoItem>
			<InfoItem
				heading="Geliefert:"
				:small="true"
				class="grid-right grid-col-4"
			>
				<FormatWattH :watt-h="props.bat.dailyYieldExport"></FormatWattH>
			</InfoItem>
		</div>
	</WbSubwidget>
</template>

<script setup lang="ts">
import WbSubwidget from '../shared/WbSubwidget.vue'
import type { Battery } from './model'
import BatterySymbol from '../shared/BatterySymbol.vue'
import InfoItem from '../shared/InfoItem.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import WbBadge from '../shared/WbBadge.vue'
import { computed } from 'vue'
import { formatWatt } from '@/assets/js/helpers'
// props
const props = defineProps<{
	bat: Battery
}>()
const batteryState = computed(() => {
	if (props.bat.power < 0) {
		return `Liefert (${formatWatt(-props.bat.power)})`
	} else if (props.bat.power > 0) {
		return `Lädt (${formatWatt(props.bat.power)})`
	} else {
		return `Bereit`
	}
})
const statusbg = computed(() => {
	return props.bat.power < 0
		? 'var(--color-pv)'
		: props.bat.power > 0
			? 'var(--color-battery)'
			: 'var(--color-menu)'
})
</script>

<style scoped>
.battery-title {
	color: var(--color-battery);
	font-size: var(--font-medium);
}
</style>
