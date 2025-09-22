<template>
	<PMArc
		:upper-arc="false"
		:plotdata="plotdata"
		:radius="props.radius"
		:show-labels="props.showLabels"
		:categories-to-show="categoriesToShow"
	/>
</template>

<script setup lang="ts">
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import { usageSummary } from '@/assets/js/model'
import { batteries } from '../batteryList/model'
import { shDevices } from '../smartHome/model'
import { computed } from 'vue'
import { chargePoints } from '../chargePointList/model'
import PMArc from './PMArc.vue'
// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
	showLabels: boolean
}>()

const categoriesToShow = [
	PowerItemType.chargepoint,
	PowerItemType.battery,
	PowerItemType.device,
]
const emptyPowerItem = computed(() => {
	return {
		name: '',
		type: PowerItemType.counter,
		power: props.emptyPower,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: 'var(--color-bg)',
		icon: '',
		showInGraph: true,
	}
})
const plotdata = computed(() => {
	return [usageSummary.evuOut].concat(
		chargePointsToShow.value,
		devicesToShow.value,
		batteriesToShow.value,
		usageSummary.house,
		emptyPowerItem.value,
	)
})
const chargePointsToShow = computed(() => {
	return Object.values(chargePoints).length > 1
		? Object.values(chargePoints).sort((a, b) => {
				return b.power - a.power
			})
		: [usageSummary.charging]
})
const devicesToShow = computed(() => {
	let summarizedPower = 0
	for (const d of shDevices.values()) {
		if (d.configured && !d.countAsHouse && !d.showInGraph) {
			summarizedPower += d.power
		}
	}
	const deviceSummary: PowerItem = {
		name: 'Geräte',
		type: PowerItemType.device,
		power: summarizedPower,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: 'var(--color-devices)',
		icon: '',
		showInGraph: true,
	}
	let activeDevices = [...shDevices.values()].filter((row) => row.configured)
	return activeDevices.length > 1
		? [deviceSummary].concat(
				activeDevices
					.filter((row) => !row.countAsHouse && row.showInGraph)
					.sort((a, b) => {
						return b.power - a.power
					}),
			)
		: [usageSummary.devices]
})
const batteriesToShow = computed(() => {
	return batteries.value.size > 1
		? [...batteries.value.values()]
				.filter((b) => b.power > 0)
				.sort((a, b) => {
					return b.power - a.power
				})
		: [usageSummary.batIn]
})
</script>

<style scoped></style>
