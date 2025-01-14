<template>
	<div class="pvsettings pt-2">
		<!-- Maximum SoC -->
		<ConfigItem
			title="Ladestand begrenzen"
			icon="fa-battery-three-quarters"
			:fullwidth="true"
		>
			<SwitchInput id="limitSoc" v-model="limitSoc" />
		</ConfigItem>
		<ConfigItem
			v-if="limitSoc"
			title="...auf maximal..."
			icon="fa-battery-three-quarters"
			:fullwidth="true"
		>
			<RangeInput
				id="maxSoc"
				v-model="cp.pvMaxSoc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>
		<ConfigItem
			title="Einspeisegrenze beachten"
			icon="fa-hand"
			:fullwidth="true"
		>
			<SwitchInput v-model="cp.pvFeedInLimit" />
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
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargePoints } from './model'
import ConfigItem from '../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
const props = defineProps<{
	chargepointId: number
}>()
const cp = computed(() => {
	return chargePoints[props.chargepointId]
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
const limitSoc = computed({
	get() {
		return cp.value.pvMaxSoc <= 100
	},
	set(v: boolean) {
		if (v) {
			cp.value.pvMaxSoc = 100
		} else {
			cp.value.pvMaxSoc = 101
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
</style>
