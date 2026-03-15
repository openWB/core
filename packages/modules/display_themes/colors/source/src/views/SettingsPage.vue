<template>
	<div :id="`tabarea-${cpid}`" class="m-0 mt-1 p-0 grid-col-12 tabarea">
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
				:id="'ecSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#ecoSettings' + cpid"
			>
				<i class="fa-solid fa-coins me-1" /> Eco
			</a>

			<a
				:id="'tmSettings' + cpid"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#timeSettings' + cpid"
			>
				<i class="fa-solid fa-clock" /> Zeitpläne
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
				<ChargeConfig :chargepoint-id="cpid" />
			</div>
			<div
				:id="'instantSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<ConfigInstant :chargepoint-id="cpid" />
			</div>

			<div
				:id="'pvSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="pv-tab"
			>
				<ConfigPv :chargepoint-id="cpid" />
			</div>
			<div
				:id="'scheduledSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="scheduled-tab"
			>
				<ConfigScheduled
					v-if="chargeTemplate != undefined"
					:charge-point="props.chargepoint"
				/>
			</div>
			<div
				:id="'ecoSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="eco-tab"
			>
				<ConfigEco
					v-if="chargeTemplate != undefined"
					:chargepoint="props.chargepoint"
				/>
			</div>
			<div
				:id="'timeSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="time-tab"
			>
				<ConfigTimed
					v-if="chargeTemplate != undefined"
					:charge-point="props.chargepoint"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
	type ChargePoint,
	//	chargeTemplates,
} from '@/components/chargePointList/model'
import ConfigInstant from '@/components/chargePointList/configPanels/ConfigInstant.vue'
import ConfigPv from '@/components/chargePointList/configPanels/ConfigPv.vue'
import ConfigScheduled from '@/components/chargePointList/configPanels/ConfigScheduled.vue'
import ConfigEco from '@/components/chargePointList/configPanels/ConfigEco.vue'
import ConfigTimed from '@/components/chargePointList/configPanels/ConfigTimed.vue'
import ChargeConfig from '@/components/chargePointList/configPanels/ChargeConfig.vue'
//import PriceChart from '@/components/priceChart/PriceChart.vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const chargeTemplate = computed(() => {
	return props.chargepoint.chargeTemplate
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
	color: var(--color-menu);
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
	color: var(--color-devices);
}

.fa-clock {
	color: var(--color-menu);
}
</style>
