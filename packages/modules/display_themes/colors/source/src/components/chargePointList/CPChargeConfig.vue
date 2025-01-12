<template>
	<div class="chargesettings pt-2">
		<ConfigItem
			v-if="Object.keys(vehicles).length > 1"
			title="Fahrzeug wechseln"
			icon="fa-car"
			:fullwidth="true"
		>
			<RadioInput
				v-model.number="connectedVehicle"
				:options="Object.values(vehicles).map((v) => [v.name, v.id])"
			/>
		</ConfigItem>
		<ConfigItem
			v-if="Object.keys(chargeTemplates).length > 1"
			title="Ladeprofil"
			icon="fa-sliders"
			iconcolor="var(--color-pv)"
		>
			<RadioInput
				v-if="vehicles[connectedVehicle]"
				v-model.number="vehicles[connectedVehicle].chargeTemplateId"
				:options="
					Object.keys(chargeTemplates).map((v) => [chargeTemplates[+v].name, v])
				"
			/>
		</ConfigItem>
		<hr class="grid-col-2 my-2" />
		<ConfigItem
			title="Priorität"
			icon="fa-star"
			iconcolor="var(--color-evu)"
			:fullwidth="true"
		>
			<SwitchInput v-model="cp.hasPriority" />
		</ConfigItem>
		<ConfigItem
			title="Zeitplan aktivieren"
			icon="fa-clock"
			iconcolor="var(--color-battery)"
		>
			<SwitchInput v-model="timedCharging"></SwitchInput>
		</ConfigItem>
		<ConfigItem
			title="Sperren"
			icon="fa-lock"
			iconcolor="var(--color-evu)"
			:fullwidth="true"
		>
			<SwitchInput v-model="cp.isLocked" />
		</ConfigItem>
		<!-- Priority -->

		<ConfigItem
			title="Strompreisbasiert laden"
			icon="fa-coins"
			iconcolor="var(--color-battery)"
		>
			<SwitchInput v-model="etActive"></SwitchInput>
		</ConfigItem>
		<hr v-if="globalData.isBatteryConfigured" class="grid-col-2 my-2" />
		<ConfigItem
			v-if="globalData.isBatteryConfigured"
			title="PV-Priorität (global)"
			icon="fa-car-battery"
			iconcolor="var(--color-battery)"
			:fullwidth="true"
		>
			<RadioInput
				v-model="globalData.pvBatteryPriority"
				:options="evPriorityModes"
			>
			</RadioInput>
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
import { vehicles, chargePoints, chargeTemplates } from './model'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import { globalData } from '@/assets/js/model'
import { evPriorityModes } from '@/assets/js/types'
import { computed } from 'vue'

const props = defineProps<{
	chargepointId: number
}>()

//state
const cp = computed(() => {
	return chargePoints[props.chargepointId]
})

const connectedVehicle = computed({
	get: () => cp.value.connectedVehicle,
	set: (value: number) => {
		chargePoints[cp.value.id].connectedVehicle = value
	},
})
const etActive = computed({
	get: () => cp.value.etActive,
	set: (value: boolean) => {
		chargePoints[cp.value.id].etActive = value
	},
})
const timedCharging = computed({
	get: () => cp.value.timedCharging,
	set: (value: boolean) => {
		chargePoints[cp.value.id].timedCharging = value
	},
})
</script>

<style scoped>
.chargesettings {
	display: grid;
	grid-template-columns: auto, auto;
	justify-content: center;
	align-items: center;
	grid-gap: 1px;
}
.status-string {
	font-size: var(--font-normal);
	font-style: italic;
	color: var(--color-battery);
}

.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}

.chargeModeOption {
	background: green;
	color: blue;
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
	border-bottom: 1px solid var(--color-menu);
}

.settingsheader {
	color: var(--color-charging);
	font-size: 16px;
	font-weight: bold;
}

hr {
	color: var(--color-menu);
}
</style>
