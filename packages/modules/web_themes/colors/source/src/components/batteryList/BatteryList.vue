/* * BatteryList.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WbWidget v-if="globalData.isBatteryConfigured" :variable-width="true">
		<template #title>
			<span class="fas fa-car-battery me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span class="sh-title py-4">Speicher</span>
		</template>
		<div class="col m-0 mb-1 p-0 d-flex justify-content-between">
			<!-- Soc information -->
			<InfoItem heading="Ladestand:">
				<BatterySymbol :soc="globalData.batterySoc" class="me-2" />
			</InfoItem>
			<!-- Status information -->
			<InfoItem heading="Status:">
				<span>
					{{ batteryState }}
				</span>
			</InfoItem>

			<!-- Status information -->
			<InfoItem heading="Leistung:">
				<span>
					{{ powerstring }}
				</span>
			</InfoItem>
		</div>
		<div class="col m-0 mt-3 mb-1 p-0 d-flex justify-content-between">
			<InfoItem heading="">
				<span class="todaystring mt-4 float-right"> Heute:</span>
			</InfoItem>
			<InfoItem heading="Geladen:">
				<span>
					{{ formatWattH(usageSummary.batIn.energy) }}
				</span>
			</InfoItem>
			<InfoItem heading="Geliefert">
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
