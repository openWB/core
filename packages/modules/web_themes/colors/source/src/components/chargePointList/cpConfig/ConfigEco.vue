<template>
	<div class="pt-2 d-flex flex-column">
		<div class="heading ms-1">Eco-Laden:</div>
		<PriceChart v-if="etData.active" :chargepoint="cp as ChargePoint" />
		<!-- Minimal current -->
		<ConfigItem
			v-if="etData.active"
			title="Minimaler Ladestrom unter der Preisgrenze:"
			icon="fa-bolt"
			:fullwidth="true"
		>
			<div class="subconfigstack grid-col-12">
				<div class="subconfig subgrid">
					<span class="subconfigtitle grid-col-1">Stärke:</span>
					<RangeInput
						id="minCurrent"
						v-model="cp.ecoMinCurrent"
						:min="6"
						:max="32"
						:step="1"
						unit="A"
					/>
				</div>
			</div>
		</ConfigItem>

		<!-- Number of phases -->
		<ConfigItem title="Anzahl Phasen" icon="fa-plug" :fullwidth="true">
			<RadioInput2
				v-model="cp.ecoTargetPhases"
				:options="[
					['1', 1],
					['Maximum', 3],
					['Auto', 0],
				]"
			/>
		</ConfigItem>

		<!-- Limit Mode -->
		<ConfigItem title="Begrenzung" icon="fa-hand" :fullwidth="true">
			<RadioInput2
				v-model="cp.ecoChargeLimitMode"
				:options="chargeLimitModes.map((e) => [e.name, e.id])"
			/>
		</ConfigItem>

		<!-- Max SoC -->
		<ConfigItem
			v-if="cp.ecoChargeLimitMode == 'soc'"
			title="Maximaler Ladestand"
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
	</div>
	<PriceCalculator
		:model-value="price"
		:cp-id="chargepoint.id"
	></PriceCalculator>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { type ChargePoint, chargeLimitModes } from '../model'
import { etData } from '@/components/priceChart/model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
//import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'
import PriceChart from '@/components/priceChart/PriceChart.vue'
import PriceCalculator from './PriceCalculator.vue'
//import { infotext } from '@/assets/js/themeConfig'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
var price = 0
const energyLimit = computed({
	get() {
		return cp.value.ecoMaxEnergy / 1000
	},
	set(limit: number) {
		cp.value.ecoMaxEnergy = limit * 1000
	},
})
</script>

<style scoped>
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}

.heading {
	color: var(--color-eco);
	font-size: var(--font-settings);
	font-weight: bold;
}
.subconfigstack {
	display: grid;
	grid-template-columns: repeat(2, auto);
	width: 100%;
}
.subconfig {
	justify-content: end;
	align-items: baseline;
	margin-left: 1em;
	width: 100%;
}
.subconfigtitle {
	margin-right: 5px;
}
</style>
