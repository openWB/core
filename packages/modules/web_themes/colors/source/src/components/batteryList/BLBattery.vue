/* * BLBattery.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="battery-title">{{ bat.name }}</span>
		</template>
		<template #buttons>
			<BatterySymbol :soc="bat.soc" />
		</template>
		<div class="subgrid pt-1">
			<InfoItem heading="Geliefert:" :small="true" class="grid-left grid-col-4">
				<FormatWattH :watt-h="props.bat.dailyYieldExport"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Geladen:" :small="true" class="grid-col-4">
				<FormatWattH :watt-h="props.bat.dailyYieldImport"></FormatWattH>
			</InfoItem>
			<InfoItem
				heading="Ladestand:"
				:small="true"
				class="grid-right grid-col-4"
			>
				<BatterySymbol :soc="props.bat.soc"></BatterySymbol>
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
// props
const props = defineProps<{
	bat: Battery
}>()
</script>

<style scoped>
.battery-title {
	color: var(--color-battery);
	font-size: var(--font-medium);
}

.battery-color {
	color: var(--color-battery);
}

.fg-color {
	color: var(--color-fg);
}

.menu-color {
	color: var(--color-menu);
}
</style>
