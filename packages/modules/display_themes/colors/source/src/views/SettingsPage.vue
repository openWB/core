<template>
	<div class="m-0 mt-1 p-0 grid-col-12 tabarea">
		<nav class="nav nav-tabs nav-justified mx-1 mt-1" role="tablist">
			<a
				class="nav-link active"
				data-bs-toggle="tab"
				:data-bs-target="'#chargeSettings' + cpid"
			>
				<i class="fa-solid fa-charging-station" />
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#instantSettings' + cpid"
			>
				<i class="fa-solid fa-lg fa-bolt" /> Sofort
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#pvSettings' + cpid"
			>
				<i class="fa-solid fa-solar-panel me-1" /> PV
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#scheduledSettings' + cpid"
			>
				<i class="fa-solid fa-bullseye me-1" /> Zielladen
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#timeSettings' + cpid"
			>
				<i class="fa-solid fa-clock" /> Zeitladen
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				:data-bs-target="'#carSettings' + cpid"
			>
				<i class="fa-solid fa-rectangle-list" />
			</a>
			<a
				v-if="etData.active && cp.etActive"
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
				<div class="settingslist">
					<ConfigItem
						v-if="globalData.isBatteryConfigured"
						title="PV-Priorität (global)"
						icon="fa-car-battery"
						iconcolor="var(--color-battery)"
						infotext="Priority during PV production"
						:fullwidth="true"
					>
						<RadioInput
							v-model="globalData.pvBatteryPriority"
							:options="evPriorityModes"
						>
						</RadioInput>
					</ConfigItem>
					<hr class="grid-col-12" />
					<ConfigItem title="Fahrzeug wechseln" icon="fa-car" :fullwidth="true">
						<RadioInput
							v-model.number="connectedVehicle"
							:options="Object.values(vehicles).map((v) => [v.name, v.id])"
						/>
					</ConfigItem>
					<hr class="grid-col-12" />
					<ConfigItem
						title="Strompreisbasiert laden"
						icon="fa-coins"
						iconcolor="var(--color-battery)"
						infotext="Settings"
					>
						<SwitchInput v-model="etActive"></SwitchInput>
					</ConfigItem>
					<ConfigItem
						title="Zeitplan aktivieren"
						icon="fa-clock"
						iconcolor="var(--color-battery)"
					>
						<SwitchInput v-model="timedCharging"></SwitchInput>
					</ConfigItem>
					<ConfigItem
						title="Ladeprofil"
						icon="fa-sliders"
						iconcolor="var(--color-pv)"
					>
						<RadioInput
							v-if="vehicles[connectedVehicle]"
							v-model.number="vehicles[connectedVehicle].chargeTemplateId"
							:options="
								Object.keys(chargeTemplates).map((v) => [
									chargeTemplates[+v].name,
									v,
								])
							"
						/>
					</ConfigItem>
				</div>
			</div>
			<div
				:id="'instantSettings' + cpid"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="instant-tab"
			>
				<CPConfigInstant
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
import { computed, ref } from 'vue'
import { globalData } from '@/assets/js/model'
import {
	chargePoints,
	type ChargePoint,
	vehicles,
	chargeTemplates,
} from '@/components/chargePointList/model'
import { etData } from '@/components/priceChart/model'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import CPConfigInstant from '@/components/chargePointList/CPConfigInstant.vue'
import CPConfigPv from '@/components/chargePointList/CPConfigPv.vue'
import { evPriorityModes } from '@/assets/js/types'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
const chargeTemplate = computed(() => {
	return chargeTemplates[props.chargepoint.chargeTemplate]
})
const cpid = computed(() => {
	return props.chargepoint.id
})
const etActive = computed({
	get: () => props.chargepoint.etActive,
	set: (value: boolean) => {
		chargePoints[props.chargepoint.id].etActive = value
	},
})
const timedCharging = computed({
	get: () => props.chargepoint.timedCharging,
	set: (value: boolean) => {
		chargePoints[props.chargepoint.id].timedCharging = value
	},
})
const connectedVehicle = computed({
	get: () => props.chargepoint.connectedVehicle,
	set: (value: number) => {
		chargePoints[props.chargepoint.id].connectedVehicle = value
	},
})
</script>

<style scoped>
.settingslist {
	display: grid;
	grid-template-columns: repeat(12, 1fr);
	font-size: 16px;
	color: var(--color-fg);
	background-color: var(--color-bg);
}
.nav-link {
	font-size: var(--font-settings);
	color: var(--color-fg);
}
.fa-bolt {
	color: var(--color-charging);
}
.fa-charging-station {
	color: var(--color-fg);
}
.fa-solar-panel {
	color: var(--color-pv);
}
</style>
