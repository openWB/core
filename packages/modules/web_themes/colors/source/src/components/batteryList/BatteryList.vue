/* * BatteryList.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WbWidgetFlex
		v-if="globalData.isBatteryConfigured"
		:variable-width="true"
		:full-width="false"
	>
		<template #title>
			<span class="fas fa-car-battery me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span>Speicher</span>
		</template>
		<template #buttons>
			<WbBadge :bgcolor="statusbg">
				{{ batteryState }}
			</WbBadge>
		</template>
		<div class="px-3 subgrid grid-12">
			<InfoItem heading="Ladestand:" class="grid-left grid-col-4">
				<BatterySymbol
					color="var(--color-battery)"
					:soc="globalData.batterySoc"
				></BatterySymbol>
			</InfoItem>
			<InfoItem heading="Geladen:" class="grid-col-4">
				<span>
					{{ formatWattH(importedSum) }}
				</span>
			</InfoItem>
			<InfoItem heading="Geliefert" class="grid-right grid-col-4">
				<span>
					{{ formatWattH(sourceSummary.batOut.energy) }}
				</span>
			</InfoItem>
		</div>
		<BLBattery v-for="[key, battery] in batteries" :key="key" :bat="battery" />
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import InfoItem from '../shared/InfoItem.vue'
import BatterySymbol from '../shared/BatterySymbol.vue'
import { globalData, sourceSummary, usageSummary } from '@/assets/js/model'
import { computed } from 'vue'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import { batteries } from './model'
import BLBattery from './BLBattery.vue'
import WbBadge from '../shared/WbBadge.vue'

const batteryState = computed(() => {
	if (sourceSummary.batOut.power > 0) {
		return `Liefert (${formatWatt(sourceSummary.batOut.power)})`
	} else if (usageSummary.batIn.power > 0) {
		return `Lädt (${formatWatt(usageSummary.batIn.power)})`
	} else {
		return `Bereit:`
	}
})

const statusbg = computed(() => {
	return sourceSummary.batOut.power > 0
		? 'var(--color-pv)'
		: usageSummary.batIn.power > 0
			? 'var(--color-battery)'
			: 'var(--color-menu)'
})
const importedSum = computed(() => {
	let sum = 0
	batteries.value.forEach((bat) => {
		sum += bat.dailyYieldImport
	})
	return sum
})
</script>

<style scoped>
.battery-color {
	color: var(--color-battery);
}

.fg-color {
	color: var(--color-fg);
}

.menu-color {
	color: var(--color-menu);
}

.todaystring {
	color: var(--color-menu);
}
</style>
