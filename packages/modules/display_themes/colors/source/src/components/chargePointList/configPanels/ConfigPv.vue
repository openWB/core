<template>
	<div class="pvsettings pt-2">
		<!-- Min+PV-Laden -->
		<ConfigItem title="Minimaler Ladestrom" icon="fa-bolt" :fullwidth="true">
			<SwitchInput v-model="useMinPv" />
		</ConfigItem>
		<!-- Minimum Current -->
		<ConfigItem
			v-if="useMinPv"
			title="...bei Ladestrom (minimal)"
			:fullwidth="true"
		>
			<RangeInput
				id="minCurrent"
				v-model="cp.pvMinCurrent"
				:min="6"
				:max="32"
				:step="1"
				unit="A"
			/>
		</ConfigItem>

		<!-- Phases -->
		<ConfigItem title="Anzahl Phasen" icon="fa-plug" :fullwidth="true">
			<RadioInput
				id="targetPhases"
				v-model="cp.pvTargetPhases"
				:options="[
					['Eine', 1],
					['Max', 3],
					['Auto', 0],
				]"
			/>
		</ConfigItem>

		<!-- Min-PV-Laden -->
		<ConfigItem
			title="Mindest-Ladestand"
			icon="fa-battery-half"
			:fullwidth="true"
		>
			<SwitchInput v-model="useMinSoc" />
		</ConfigItem>

		<!-- Minimum SoC -->
		<ConfigItem v-if="useMinSoc" title="...bis SoC" :fullwidth="true">
			<RangeInput
				id="minSoc"
				v-model="cp.pvMinSoc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>
		<!-- Minimum Soc Current -->
		<ConfigItem v-if="useMinSoc" title="...mit Ladestrom" :fullwidth="true">
			<RangeInput
				id="minSocCurrent"
				v-model="cp.pvMinSocCurrent"
				:min="6"
				:max="32"
				:step="1"
				unit="A"
			/>
		</ConfigItem>

		<hr v-if="cp.pvChargeLimitMode != 'none'" class="fullwidth" />

		<!-- Limit Mode -->
		<ConfigItem title="Begrenzung" icon="fa-hand" :fullwidth="true">
			<RadioInput
				v-model="cp.pvChargeLimitMode"
				:options="pvChargeLimitModes.map((e) => [e.name, e.id])"
			/>
		</ConfigItem>
		<!-- Max SoC -->
		<ConfigItem
			v-if="cp.pvChargeLimitMode == 'soc'"
			title="Maximaler SoC"
			icon="fa-sliders"
			:fullwidth="true"
		>
			<RangeInput
				id="maxSoc"
				v-model="cp.pvTargetSoc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>

		<!-- Max Energy -->
		<ConfigItem
			v-if="cp.pvChargeLimitMode == 'amount'"
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
		<ConfigItem
			title="Einspeisegrenze beachten"
			icon="fa-hand"
			:fullwidth="true"
		>
			<SwitchInput v-model="cp.pvFeedInLimit" />
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargePoints } from '../model'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
const props = defineProps<{
	chargepointId: number
}>()
const cp = computed(() => {
	return chargePoints[props.chargepointId]
})

// computed

const pvChargeLimitModes = [
	{ name: 'keine', id: 'none' },
	{ name: 'EV-SoC', id: 'soc' },
	{ name: 'Energiemenge', id: 'amount' },
]
const energyLimit = computed({
	get() {
		return cp.value.pvMaxEnergy / 1000
	},
	set(limit: number) {
		cp.value.pvMaxEnergy = limit * 1000
	},
})
const useMinPv = computed({
	get() {
		return cp.value.pvMinCurrent > 5
	},
	set(v: boolean) {
		if (!v) {
			cp.value.pvMinCurrent = 0
		} else {
			cp.value.pvMinCurrent = 6
		}
	},
})
const useMinSoc = computed({
	get() {
		return cp.value.pvMinSoc > 0
	},
	set(v: boolean) {
		if (v) {
			cp.value.pvMinSoc = 50
		} else {
			cp.value.pvMinSoc = 0
		}
	},
})
</script>

<style scoped>
.pvsettings {
	display: grid;
	justify-content: center;
	align-items: center;
	grid-gap: 20px;
	grid-template-columns: auto auto;
}
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}

.heading {
	color: var(--color-pv);
}
.fullwidth {
	grid-column: 1 / -1;
}
</style>
