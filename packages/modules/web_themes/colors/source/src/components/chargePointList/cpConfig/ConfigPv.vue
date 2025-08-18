<template>
	<div class="pt-2 d-flex flex-column">
		<div class="heading ms-1">PV-Laden:</div>
		<!-- Min+PV-Laden -->
		<ConfigItem
			title="Minimaler Ladestrom"
			icon="fa-bolt"
			:infotext="infotext['minpv']"
			:fullwidth="true"
		>
			<template #inline-item>
				<SwitchInput v-model="useMinPv" />
			</template>
			<div class="subconfigstack grid-col-12">
				<div v-if="useMinPv" class="subconfig subgrid">
					<span class="subconfigtitle grid-col-1">Stärke:</span>
					<RangeInput
						id="minCurrent"
						v-model="cp.pvMinCurrent"
						:min="6"
						:max="32"
						:step="1"
						unit="A"
					/>
				</div>
			</div>
		</ConfigItem>

		<ConfigItem title="Anzahl Phasen" icon="fa-plug" :fullwidth="true">
			<RadioInput2
				v-model="cp.pvTargetPhases"
				:options="[
					['1', 1],
					['Maximum', 3],
					['Auto', 0],
				]"
			/>
		</ConfigItem>
		<!-- Min-PV-Laden -->
		<ConfigItem
			title="Mindest-Ladestand"
			icon="fa-battery-half"
			:infotext="infotext['minsoc']"
			:fullwidth="true"
		>
			<template #inline-item>
				<SwitchInput v-model="useMinSoc" class="grid-col-3" />
			</template>
			<div v-if="useMinSoc" class="subconfigstack">
				<div class="subconfig subgrid">
					<span class="subconfigtitle grid-col-1">SoC:</span>
					<RangeInput
						id="minSoc"
						v-model="cp.pvMinSoc"
						class="grid-col-2"
						:min="0"
						:max="100"
						:step="1"
						unit="%"
					/>
				</div>
				<div class="subconfig subgrid">
					<span class="subconfigtitle grid-col-1">Ladestrom:</span>
					<RangeInput
						id="minSocCurrent"
						v-model="cp.pvMinSocCurrent"
						class="grid-col-2"
						:min="6"
						:max="32"
						:step="1"
						unit="A"
					/>
				</div>
				<div class="subconfig subgrid">
					<span class="subconfigtitle grid-col-1">Phasen:</span>
					<RadioInput2
						v-model="cp.pvMinSocPhases"
						class="grid-col-1"
						:columns="2"
						:options="[
							['1', 1],
							['Maximum', 3],
						]"
					/>
				</div>
				<hr class="grid-col-3" />
			</div>
		</ConfigItem>

		<!-- <hr v-if="useMinPv || useMinSoc" />

		<hr v-if="cp.pvChargeLimitMode != 'none'" />
		 --><!-- Limit Mode -->
		<ConfigItem title="Begrenzung" icon="fa-hand" :fullwidth="true">
			<RadioInput2
				v-model="cp.pvChargeLimitMode"
				:options="chargeLimitModes.map((e) => [e.name, e.id])"
			/>
		</ConfigItem>
		<!-- Max SoC -->
		<ConfigItem
			v-if="cp.pvChargeLimitMode == 'soc'"
			title="Maximaler Ladestand"
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
			<template #inline-item>
				<SwitchInput v-model="cp.pvFeedInLimit" />
			</template>
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { type ChargePoint, chargeLimitModes } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'
import { infotext } from '@/assets/js/themeConfig'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
const energyLimit = computed({
	get() {
		return cp.value.pvMaxEnergy / 1000
	},
	set(limit: number) {
		cp.value.pvMaxEnergy = limit * 1000
	},
})
// methods:

// computed
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
.chargeConfigSelect {
	background: var(--color-bg);
	color: var(--color-fg);
}

.heading {
	color: var(--color-pv);
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
