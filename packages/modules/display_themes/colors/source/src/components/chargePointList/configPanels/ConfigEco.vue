<template>
	<div class="ecosettings">
		<PriceChart
			v-if="etData.active"
			:charge-point-id="props.chargepoint.id"
			class="fullwidth"
		/>
		<span class="fullwidth mb-4">
			<button type="button" class="btn btn-secondary" @click="pageDown">
				<i class="fa-solid fa-circle-down me-2"></i>
				Abwärts
			</button>
		</span>

		<!-- Minimal ampere -->
		<ConfigItem
			title="Minimaler Ladestrom unter der Preisgrenze"
			icon="fa-bolt"
			:fullwidth="true"
		>
			<RangeInput
				id="minCurrent"
				v-model="cp.ecoMinCurrent"
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
				v-model="cp.ecoTargetPhases"
				:options="[
					['Eine', 1],
					['Alle', 2],
					['Auto', 3],
				]"
			/>
		</ConfigItem>
		<hr v-if="cp.ecoChargeLimitMode != 'none'" class="fullwidth" />
		<!-- Limit Mode -->
		<ConfigItem title="Begrenzung" icon="fa-hand" :fullwidth="true">
			<RadioInput
				v-model="cp.ecoChargeLimitMode"
				:options="ecoChargeLimitModes.map((e) => [e.name, e.id])"
			/>
		</ConfigItem>
		<!-- Max SoC -->
		<ConfigItem
			v-if="cp.ecoChargeLimitMode == 'soc'"
			title="Maximaler SoC"
			icon="fa-sliders"
			:fullwidth="true"
		>
			<RangeInput
				id="maxSoc"
				v-model="cp.ecoTargetSoc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>

		<!-- Max Energy -->
		<ConfigItem
			v-if="cp.ecoChargeLimitMode == 'amount'"
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
		<span class="fullwidth">
			<button type="button" class="btn btn-secondary" @click="pageUp">
				<i class="fa-solid fa-circle-up me-2"></i>
				Aufwärts
			</button>
		</span>
	</div>
</template>

<script setup lang="ts">
// import { eventBus } from '@/main.js'
import { computed } from 'vue'
import { ChargePoint, chargePoints } from '../model'
import { etData } from '@/components/priceChart/model'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import PriceChart from '@/components/priceChart/PriceChart.vue'

const props = defineProps<{
	chargepoint: ChargePoint
}>()

const cp = computed(() => {
	return chargePoints[props.chargepoint.id]
})

const ecoChargeLimitModes = [
	{ name: 'keine', id: 'none' },
	{ name: 'EV-SoC', id: 'soc' },
	{ name: 'Energiemenge', id: 'amount' },
]
const energyLimit = computed({
	get() {
		return cp.value.ecoMaxEnergy / 1000
	},
	set(limit: number) {
		cp.value.ecoMaxEnergy = limit * 1000
	},
})
// methods
function pageDown() {
	const modalbody = document.getElementById('modal-body-settingspage')
	if (modalbody) {
		modalbody.scrollTo({ top: modalbody.scrollHeight, behavior: 'smooth' })
	} else {
		console.warn('modalbody not found')
	}
}
function pageUp() {
	const modalbody = document.getElementById('modal-body-settingspage')
	window.scrollTo(0, 0)
	if (modalbody) {
		modalbody.scrollTo({ top: 0, behavior: 'smooth' })
	} else {
		console.warn('modalbody not found')
	}
}
</script>

<style scoped>
.ecosettings {
	display: grid;
	justify-content: space-between;
	align-items: top;
	grid-template-columns: auto auto;
	grid-gap: 0px;
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
.fullwidth {
	grid-column: 1 / -1;
}
</style>
