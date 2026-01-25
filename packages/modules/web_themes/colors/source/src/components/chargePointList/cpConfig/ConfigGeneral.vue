<template>
	<p class="settingsheader mt-2 ms-1">
		Ladeeinstellungen für {{ cp.vehicleName }}:
	</p>
	<!-- Select the charge mode -->
	<ConfigItem
		title="Lademodus"
		icon="fa-charging-station"
		:infotext="infotext['chargemode']"
		:fullwidth="true"
	>
		<RadioInput2
			v-model="cp.chargeMode"
			:columns="3"
			:options="
				Object.keys(chargemodes).map((v) => [
					chargemodes[v].name,
					v,
					chargemodes[v].color,
					chargemodes[v].icon,
				])
			"
		/>
	</ConfigItem>
	<!-- Select the vehicle -->
	<ConfigItem
		v-if="Object.values(vehicles).filter((v) => v.visible).length > 1"
		title="Fahrzeug wechseln"
		icon="fa-car"
		:infotext="infotext['vehicle']"
		:fullwidth="true"
	>
		<RadioInput2
			v-model.number="cp.connectedVehicle"
			:options="
				Object.values(vehicles)
					.filter((v) => v.visible)
					.map((v) => [v.name, v.id])
			"
		/>
	</ConfigItem>
	<!-- Select the charge template -->
	<ConfigItem
		title="Ladeprofil"
		icon="fa-settings"
		:infotext="infotext['chargeTemplate']"
		:fullwidth="true"
	>
		<RadioInput2
			v-model="templateId"
			:options="
				Object.values(chargeTemplates).map((template) => [
					template.name,
					template.id,
				])
			"
		/>
	</ConfigItem>
	<ConfigItem
		title="Sperren"
		icon="fa-lock"
		:infotext="infotext['locked']"
		:fullwidth="true"
	>
		<template #inline-item>
			<SwitchInput v-model="cp.isLocked" />
		</template>
	</ConfigItem>
	<!-- Priority -->
	<ConfigItem
		title="Priorität"
		icon="fa-star"
		:infotext="infotext['priority']"
		:fullwidth="true"
	>
		<template #inline-item>
			<SwitchInput v-model="cp.hasPriority" />
		</template>
	</ConfigItem>
	<!-- Scheduled Charging -->
	<ConfigItem
		title="Zeitplan"
		icon="fa-clock"
		:infotext="infotext['timeplan']"
		:fullwidth="true"
	>
		<template #inline-item>
			<SwitchInput v-model="cp.timedCharging" />
		</template>
	</ConfigItem>
	<!-- Priority mode if battery exists -->
	<ConfigItem
		v-if="globalData.isBatteryConfigured"
		title="PV-Priorität"
		icon="fa-car-battery"
		:infotext="infotext['pvpriority']"
		:fullwidth="true"
	>
		<RadioInput2
			v-model="globalData.pvBatteryPriority"
			:options="evPriorityModes"
		>
		</RadioInput2
	></ConfigItem>

	<!-- Price based Charging -->
	<!-- <ConfigItem
		v-if="etData.active"
		title="Strompreisbasiert laden"
		icon="fa-money-bill"
		:infotext="infotext['pricebased']"
		:fullwidth="true"
	>
		<SwitchInput v-model="cp.etActive" />
	</ConfigItem>
 -->
</template>

<script setup lang="ts">
import { chargemodes } from '@/assets/js/themeConfig'
import { ChargePoint, vehicles, chargeTemplates } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import { infotext } from '@/assets/js/themeConfig'
import SwitchInput from '../../shared/SwitchInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'
//import { etData } from '@/components/priceChart/model'
import { globalData } from '@/assets/js/model'
import { evPriorityModes } from '@/assets/js/types'
import { computed } from 'vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
defineEmits(['closeConfig'])
//state
const cp = props.chargepoint
const vehicle = vehicles[cp.connectedVehicle]
const templateId = computed ( {
	get() {
		return vehicle.chargeTemplateId
	},
	set(value: number) {
		vehicle.chargeTemplateId = value
		cp.chargeTemplate = chargeTemplates[value]
	},
} )
</script>

<style scoped>
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
