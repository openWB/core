<template>
	<div class="m-0 mt-1 p-0 grid-col-12 tabarea">
		<nav class="nav nav-tabs nav-justified mx-1 mt-1" role="tablist">
			<a
				:id="'chSettings' + cpid"
				class="nav-link active"
				data-bs-toggle="tab"
				:data-bs-target="'#chargeSettings' + cpid"
			>
				<i class="fa-solid fa-charging-station" /> Allgemein
			</a>
			<a
				:id="'inSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#instantSettings' + cpid"
			>
				<i class="fa-solid fa-lg fa-bolt" /> Sofort
			</a>
			<a
				:id="'phvSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#pvSettings' + cpid"
			>
				<i class="fa-solid fa-solar-panel me-1" /> PV
			</a>
			<a
				:id="'scSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#scheduledSettings' + cpid"
			>
				<i class="fa-solid fa-bullseye me-1" /> Zielladen
			</a>
			<a
				:id="'tmSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#timeSettings' + cpid"
			>
				<i class="fa-solid fa-clock" /> Zeitpläne
			</a>
			<a
				:id="'prSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#priceSettings' + cpid"
			>
				<i class="fa-solid fa-coins" /> Strompreis
			</a>
		</nav>

		<!-- Tab panes -->
		<div id="settingsPanes" class="tab-content mt-2">
			<div
				:id="'chargeSettings' + cpid"
				class="tab-pane active"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<CPChargeConfig :chargepoint-id="cpid" />
			</div>
			<div
				:id="'instantSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<CPConfigInstant :chargepoint-id="cpid" />
			</div>

			<div
				:id="'pvSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="pv-tab"
			>
				<CPConfigPv :chargepoint-id="cpid" />
			</div>
			<div
				:id="'scheduledSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="scheduled-tab"
			>
				<CPConfigScheduled
					v-if="chargeTemplate != undefined"
					:charge-template-id="props.chargepoint.chargeTemplate"
				/>
			</div>
			<div
				:id="'timeSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="time-tab"
			>
				<CPConfigTimed
					v-if="chargeTemplate != undefined"
					:charge-template-id="props.chargepoint.chargeTemplate"
				/>
			</div>
			<div
				:id="'priceSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="price-tab"
			>
				<PriceChart
					v-if="etData.active"
					:charge-point-id="props.chargepoint.id"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
	type ChargePoint,
	chargeTemplates,
} from '@/components/chargePointList/model'
import CPConfigInstant from '@/components/chargePointList/CPConfigInstant.vue'
import CPConfigPv from '@/components/chargePointList/CPConfigPv.vue'
import CPConfigScheduled from '@/components/chargePointList/CPConfigScheduled.vue'
import CPConfigTimed from '@/components/chargePointList/CPConfigTimed.vue'
import CPChargeConfig from '@/components/chargePointList/CPChargeConfig.vue'
import PriceChart from '@/components/priceChart/PriceChart.vue'
import { etData } from '@/components/priceChart/model'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const chargeTemplate = computed(() => {
	return chargeTemplates[props.chargepoint.chargeTemplate]
})
const cpid = computed(() => {
	return props.chargepoint.id
})
</script>

<style scoped>
.tab-pane {
	font-size: 16px;
	color: var(--color-fg);
	background-color: var(--color-bg);
	align-items: center;
}

.nav-link {
	font-size: 14px;
	color: var(--color-fg);
}

.nav-tabs .nav-link.active {
	background-color: var(--color-fg);
}

.fa-bolt {
	color: var(--color-charging);
}

.fa-charging-station {
	color: var(--color-charging);
}

.fa-bullseye {
	color: var(--color-battery);
}

.fa-solar-panel {
	color: var(--color-pv);
}

.fa-lock {
	color: var(--color-evu);
}

.fa-coins {
	color: var(--color-charging);
}
</style>
