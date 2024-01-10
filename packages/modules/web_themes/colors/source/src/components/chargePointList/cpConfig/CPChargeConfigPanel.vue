<template>
	<ConfigItem title="Status" icon="fa-info-circle" :fullwidth="true">
		<span class="status-string">{{ cp.stateStr }}</span>
	</ConfigItem>

	<ConfigItem v-if="cp.faultState != 0" title="Fehler">
		<span style="color: red"> {{ cp.faultStr }} </span>
	</ConfigItem>

	<div class="m-0 mt-4 p-0">
		<nav class="nav nav-tabs nav-justified mx-1 mt-1" role="tablist">
			<a
				class="nav-link active"
				data-bs-toggle="tab"
				:data-bs-target="'#chargeSettings' + cpid"
			>
				<i class="fa-solid fa-charging-station" />
			</a>
			<a
				v-if="chargepoint.chargeMode == 'instant_charging'"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#instantSettings' + cpid"
			>
				<i class="fa-solid fa-lg fa-bolt" />
			</a>
			<a
				v-if="chargepoint.chargeMode == 'pv_charging'"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#pvSettings' + cpid"
			>
				<i class="fa-solid fa-solar-panel me-1" />
			</a>
			<a
				v-if="chargepoint.chargeMode == 'scheduled_charging'"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#scheduledSettings' + cpid"
			>
				<i class="fa-solid fa-bullseye me-1" />
			</a>
			<a
				v-if="chargepoint.timedCharging"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#timeSettings' + cpid"
			>
				<i class="fa-solid fa-clock" />
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#carSettings' + cpid"
			>
				<i class="fa-solid fa-rectangle-list" />
			</a>
			<a
				v-if="cp.etActive"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#priceChart' + cpid"
			>
				<i class="fa-solid fa-chart-line" />
			</a>
		</nav>

		<!-- Tab panes -->
		<div id="settingsPanes" class="tab-content mx-1 p-1 pb-3">
			<div
				:id="'chargeSettings' + cpid"
				class="tab-pane active"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<CPChargeConfig :chargepoint="chargepoint" />
			</div>
			<div
				:id="'instantSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<CPConfigInstant
					:chargepoint="cp"
					:vehicles="vehicles"
					:charge-templates="chargeTemplates"
				/>
			</div>

			<div
				:id="'pvSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="pv-tab"
			>
				<CPConfigPv
					:chargepoint="cp"
					:vehicles="vehicles"
					:charge-templates="chargeTemplates"
				/>
			</div>
			<div
				:id="'scheduledSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="scheduled-tab"
			>
				<CPConfigScheduled
					v-if="chargeTemplate != undefined"
					:charge-template-id="cp.chargeTemplate"
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
					:charge-template-id="cp.chargeTemplate"
				/>
			</div>

			<div
				:id="'carSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="car-tab"
			>
				<CPConfigVehicle
					v-if="vehicles[cp.connectedVehicle] != undefined"
					:vehicle-id="cp.connectedVehicle"
				/>
			</div>
			<div
				:id="'priceChart' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="price-tab"
			>
				<PriceChart
					v-if="vehicles[cp.connectedVehicle] != undefined"
					:chargepoint="cp"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { ChargePoint, vehicles, chargeTemplates } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import CPConfigInstant from './CPConfigInstant.vue'
import CPConfigPv from './CPConfigPv.vue'
import CPConfigScheduled from './CPConfigScheduled.vue'
import CPConfigTimed from './CPConfigTimed.vue'
import CPConfigVehicle from './CPConfigVehicle.vue'
import CPChargeConfig from './CPChargeConfig.vue'
import PriceChart from '@/components/priceChart/PriceChart.vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
defineEmits(['closeConfig'])
//state
const cp = props.chargepoint

// computed
const chargeTemplate = computed(() => {
	return chargeTemplates[cp.chargeTemplate]
})
const cpid = computed(() => {
	return cp.id
})
// methods
// lifecycle
onMounted(() => {})
</script>

<style scoped>
.status-string {
	font-size: var(--font-settings);
	font-style: italic;
	color: var(--color-battery);
}

.nav-tabs .nav-link {
	color: var(--color-menu);
	opacity: 0.5;
}
.nav-tabs .nav-link.disabled {
	color: var(--color-axis);
	border: 0.5px solid var(--color-axis);
}

.nav-tabs .nav-link.active {
	color: var(--color-fg);
	background-color: var(--color-bg);
	opacity: 1;
	border: 1px solid var(--color-menu);
	border-bottom: 0px solid var(--color-menu);
}
.heading {
	color: var(--color-menu);
}
</style>
