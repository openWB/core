/* * BLBattery.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<WBWidget>
		<template #title>
			<span class="battery-title">Speicher</span>
		</template>
		<template #buttons>
			<BatterySymbol :soc="bat.soc" />
		</template>
		<div class="container-fluid p-0 m-0">
			<div class="row ps-1 pt-1 m-0">
				<div class="col p-0 m-0">
					<i class="fa battery-color" :class="powerSymbol" />
					<span class="battery-color ms-1 me-3"> {{ powerTag }} </span>
					<span class="fg-color"> {{ powerValue }} </span>
				</div>
			</div>
			<hr />
			<div class="row pb-2 ps-1 mt-2">
				<div class="col-2 m-0 menu-color">Heute:</div>
				<div class="col d-flex justify-content-center">
					<span class="menu-color me-2">Geladen </span>
					<span> {{ importString }} </span>
				</div>
				<div class="col d-flex justify-content-end">
					<span class="menu-color me-2">Geliefert </span>
					<span class="me-1"> {{ exportString }} </span>
				</div>
			</div>
		</div>
	</WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import WBWidget from '../shared/WBWidget.vue'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import type { Battery } from './model'
import BatterySymbol from '../shared/BatterySymbol.vue'
// props
const props = defineProps<{
	bat: Battery
}>()
// computed
const powerTag = computed(() => {
	let result = ''
	if (props.bat.power > 0) {
		result = 'Lädt '
	} else if (props.bat.power < 0) {
		result = 'Liefert '
	} else {
		result = 'Inaktiv '
	}
	return result
})
const powerValue = computed(() => {
	if (props.bat.power > 0) {
		return formatWatt(props.bat.power)
	} else if (props.bat.power < 0) {
		return formatWatt(-props.bat.power)
	} else {
		return '0 W'
	}
})
const importString = computed(() => {
	return formatWattH(props.bat.dailyYieldImport)
})
const exportString = computed(() => {
	return formatWattH(props.bat.dailyYieldExport)
})
const powerSymbol = computed(() => {
	if (props.bat.power > 0) {
		return 'fa-car-battery'
	} else if (props.bat.power < 0) {
		return 'fa-bolt'
	} else {
		return ''
	}
})
</script>

<style scoped>
.battery-title {
	color: var(--color-battery);
}
.battery-color {
	color: var(--color-battery);
}
.fg-color {
	color: var(--color-fg);
}
.menu-color {
	color: var(--color-menu);
}
</style>
