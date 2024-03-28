<template>
	<div class="pt-2">
		<p class="heading ms-1">PV-Laden:</p>

		<!-- Maximum SoC -->
		<ConfigItem
			title="Maximaler Ladestand"
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
			<div class="form-check form-switch">
				<input
					id="feedInLimitSwitch"
					v-model="cp.pvFeedInLimit"
					class="form-check-input"
					type="checkbox"
					role="switch"
				/>
			</div>
		</ConfigItem>
		<hr />
		<!-- Min-PV-Laden -->
		<ConfigItem
			title="Minimaler Ladestand"
			icon="fa-battery-half"
			:infotext="infotext['minsoc']"
			:fullwidth="true"
		>
			<SwitchInput v-model="useMinSoc" />
		</ConfigItem>

		<!-- Minimum SoC -->
		<ConfigItem v-if="useMinSoc" title="...bis SoC" :fullwidth="true">
			<template #info>
				{{ infotext['minsoc'] }}
			</template>
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
		<hr v-if="useMinPv || useMinSoc" />

		<!-- Min+PV-Laden -->
		<ConfigItem
			title="Minimaler Ladestrom"
			icon="fa-bolt"
			:infotext="infotext['minpv']"
			:fullwidth="true"
		>
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
import { ref, computed } from 'vue'
import type { ChargePoint } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import { infotext } from '@/assets/js/themeConfig'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)

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
}
</style>
