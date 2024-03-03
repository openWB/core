/* * BatteryList.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WbWidget
		v-if="globalData.isBatteryConfigured"
		:variable-width="true"
		:full-width="false"
	>
		<template #title>
			<span class="fas fa-car-battery me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span class="sh-title py-4">Speicher</span>
		</template>
		<div class="m-1 mt-0 p-0 grid12">
			<!-- Soc information -->
			<InfoItem heading="Ladestand:" class="grid-left grid-col-4">
				<BatterySymbol :soc="globalData.batterySoc" class="me-2" />
			</InfoItem>
			<!-- Status information -->
			<InfoItem heading="Status:" class="grid-col-4">
				<span>
					{{ batteryState }}
				</span>
			</InfoItem>

			<!-- Status information -->
			<InfoItem heading="Leistung:" class="grid-right grid-col-4">
				<span>
					{{ powerstring }}
				</span>
			</InfoItem>

			<InfoItem heading="" class="grid-left grid-col-4">
				<span class="todaystring mt-4 float-right"> Heute:</span>
			</InfoItem>
			<InfoItem heading="Geladen:" class="grid-col-4">
				<span>
					{{ formatWattH(usageSummary.batIn.energy) }}
				</span>
			</InfoItem>
			<InfoItem heading="Geliefert" class="grid-right grid-col-4">
				<span>
					{{ formatWattH(sourceSummary.batOut.energy) }}
				</span>
			</InfoItem>
		</div>
	</WbWidget>
</template>

<script setup lang="ts">
import WbWidget from '../shared/WBWidget.vue'
import InfoItem from '../shared/InfoItem.vue'
import BatterySymbol from '../shared/BatterySymbol.vue'
import { globalData, sourceSummary, usageSummary } from '@/assets/js/model'
import { computed } from 'vue'
import { formatWatt, formatWattH } from '@/assets/js/helpers'

const batteryState = computed(() => {
	if (sourceSummary.batOut.power > 0) {
		return 'Liefert'
	} else if (usageSummary.batIn.power > 0) {
		return 'Lädt'
	} else {
		return 'Bereit'
	}
})
const powerstring = computed(() => {
	return formatWatt(sourceSummary.batOut.power + usageSummary.batIn.power)
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
