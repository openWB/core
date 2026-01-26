<template>
	<ConfigItem
		title="Status"
		icon="fa-info-circle"
		:fullwidth="true"
		class="item"
	>
		<span class="status-string shadow m-0 mb-1 p-3">{{ cp.stateStr }}</span>
	</ConfigItem>

	<ConfigItem
		v-if="cp.faultState != 0"
		title="Fehler"
		class="grid-col-12"
		icon="fa-triangle-exclamation"
	>
		<span style="color: red"> {{ cp.faultStr }} </span>
	</ConfigItem>

	<div :id="`cptabarea-${cpid}`" class="m-0 mt-4 p-0 grid-col-12 tabarea">
		<nav class="nav nav-tabs nav-justified mx-1 mt-1" role="tablist">
			<a
				:id="`chSettings${cpid}`"
				class="nav-link active"
				data-bs-toggle="tab"
				:data-bs-target="'#chargeSettings' + cpid"
			>
				<i class="fa-solid fa-charging-station" />
			</a>
			<a
				:id="`inSettings${cpid}`"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#instantSettings' + cpid"
			>
				<i class="fa-solid fa-lg fa-bolt" />
			</a>
			<a
				:id="`pvhSettings${cpid}`"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#pvSettings' + cpid"
			>
				<i class="fa-solid fa-solar-panel me-1" />
			</a>
			<a
				:id="`scSettings${cpid}`"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#scheduledSettings' + cpid"
			>
				<i class="fa-solid fa-bullseye me-1" />
			</a>
			<a
				:id="`ecSettings${cpid}`"
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#ecoSettings' + cpid"
			>
				<i class="fa-solid fa-coins" />
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#timedSettings' + cpid"
			>
				<i class="fa-solid fa-clock" />
			</a>
		</nav>

		<!-- Tab panes -->
		<div :id="`cpsettingsPanes-${cpid}`" class="tab-content mx-1 p-1 pb-3">
			<div
				:id="'chargeSettings' + cpid"
				class="tab-pane active"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<ConfigGeneral :chargepoint="chargepoint" />
			</div>
			<div
				:id="'instantSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<ConfigInstant
					:chargepoint="cp as ChargePoint"
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
				<ConfigPv
					:chargepoint="cp as ChargePoint"
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
				<ConfigScheduled
					v-if="chargeTemplate != undefined"
					:charge-point="cp as ChargePoint"
				/>
			</div>
			<div
				:id="'ecoSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="eco-tab"
			>
				<ConfigEco v-if="chargeTemplate != undefined" :chargepoint="cp as ChargePoint" />
			</div>
			<div
				:id="'timedSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="scheduled-tab"
			>
				<ConfigTimed v-if="chargeTemplate != undefined" :charge-point="cp as ChargePoint" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Tab } from 'bootstrap'
import { ChargePoint, vehicles, chargeTemplates } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import ConfigInstant from './ConfigInstant.vue'
import ConfigPv from './ConfigPv.vue'
import ConfigScheduled from './ConfigScheduled.vue'
import ConfigTimed from './ConfigTimed.vue'
import ConfigEco from './ConfigEco.vue'
import ConfigGeneral from './ConfigGeneral.vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
defineEmits(['closeConfig'])
//state
const cp = ref(props.chargepoint)

// computed
const chargeTemplate = computed(() => {
	return cp.value.chargeTemplate?.id ?? 0
})
const cpid = computed(() => {
	return cp.value.id
})
// methods
function selectStartTab() {
	let chargePanelName = ''
	switch (props.chargepoint.chargeMode) {
		case 'instant_charging':
			chargePanelName = '#inSettings' + props.chargepoint.id
			break
		case 'pv_charging':
			chargePanelName = '#pvhSettings' + props.chargepoint.id
			break
		case 'scheduled_charging':
			chargePanelName = '#scSettings' + props.chargepoint.id
			break
		case 'eco_charging':
			chargePanelName = '#ecSettings' + props.chargepoint.id
			break
		default:
			chargePanelName = '#chSettings' + props.chargepoint.id
	}
	const tabToActivate = document.querySelector(chargePanelName)
	if (tabToActivate) {
		var tab = new Tab(tabToActivate)
		tab.show()
	} else {
		console.error('Could not find the Tab element to activate')
	}
}
// lifecycle
onMounted(() => {
	selectStartTab()
})
</script>

<style scoped>
.status-string {
	font-size: var(--font-settings);
	font-style: italic;
	color: var(--color-charging);
	border-radius: 12px;
	background: var(--color-input);
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
.item {
	grid-column: span 12;
}
.tabarea {
	justify-self: stretch;
}
</style>
