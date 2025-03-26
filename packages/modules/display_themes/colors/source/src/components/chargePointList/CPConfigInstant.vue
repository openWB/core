<template>
	<div class="instantsettings">
		<!-- Ampere -->
		<ConfigItem title="Stromstärke" icon="fa-bolt" :fullwidth="true">
			<RangeInput
				id="targetCurrent"
				v-model="cp.instantTargetCurrent"
				:min="6"
				:max="32"
				:step="1"
				unit="A"
			/>
		</ConfigItem>
		<hr v-if="cp.instantChargeLimitMode != 'none'" />
		<!-- Limit Mode -->
		<ConfigItem title="Begrenzung" icon="fa-hand" :fullwidth="true">
			<RadioInput
				v-model="cp.instantChargeLimitMode"
				:options="instantChargeLimitModes.map((e) => [e.name, e.id])"
			/>
		</ConfigItem>
		<!-- Max SoC -->
		<ConfigItem
			v-if="cp.instantChargeLimitMode == 'soc'"
			title="Maximaler SoC"
			icon="fa-sliders"
			:fullwidth="true"
		>
			<RangeInput
				id="maxSoc"
				v-model="cp.instantTargetSoc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>

		<!-- Max Energy -->
		<ConfigItem
			v-if="cp.instantChargeLimitMode == 'amount'"
			title="Zu ladende Energie"
			icon="fa-sliders"
			:fullwidth="true"
		>
			<RangeInput
				id="maxEnergy"
				v-model="energyLimit"
				:min="0"
				:max="100"
				:step="1"
				unit="kWh"
			/>
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
// import { eventBus } from '@/main.js'
import { computed } from 'vue'
import { chargePoints } from './model'
import ConfigItem from '../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'

const props = defineProps<{
	chargepointId: number
}>()

const cp = computed(() => {
	return chargePoints[props.chargepointId]
})

const instantChargeLimitModes = [
	{ name: 'keine', id: 'none' },
	{ name: 'EV-SoC', id: 'soc' },
	{ name: 'Energiemenge', id: 'amount' },
]
const energyLimit = computed({
	get() {
		return cp.value.instantMaxEnergy / 1000
	},
	set(limit: number) {
		cp.value.instantMaxEnergy = limit * 1000
	},
})
// methods
</script>

<style scoped>
.instantsettings {
	display: grid;
	justify-content: center;
	align-items: center;
	grid-template-columns: auto auto;
	grid-gap: 20px;
}
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}
.heading {
	color: var(--color-fg);
	font-size: var(--font-settings);
	font-weight: bold;
}
</style>
