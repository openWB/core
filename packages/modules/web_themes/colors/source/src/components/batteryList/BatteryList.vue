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
		<div class="subgrid grid-12">
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
					{{ formatWattH(registry.getEnergy('batOut')!) }}
				</span>
			</InfoItem>
		</div>
		<div v-if="batteries.size > 1" class="subgrid">
			<BLBattery
				v-for="[key, battery] in batteries"
				:key="key"
				:bat="battery"
				class="px-0"
			/>
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import InfoItem from '../shared/InfoItem.vue'
import BatterySymbol from '../shared/BatterySymbol.vue'
import { registry, globalData } from '@/assets/js/model'
import { computed } from 'vue'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import { batteries } from './model'
import BLBattery from './BLBattery.vue'
import WbBadge from '../shared/WbBadge.vue'

const batteryState = computed(() => {
	if (registry.getPower('batOut') > 0) {
		return `Liefert (${formatWatt(registry.getPower('batOut'))})`
	} else if (registry.getPower('batIn') > 0) {
		return `Lädt (${formatWatt(registry.getPower('batIn'))})`
	} else {
		return `Bereit:`
	}
})

const statusbg = computed(() => {
	return registry.getPower('batOut') > 0
		? 'var(--color-pv)'
		: registry.getPower('batIn') > 0
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
