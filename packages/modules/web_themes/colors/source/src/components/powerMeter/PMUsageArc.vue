<template>
	<PMArc
		:upper-arc="false"
		:plotdata="plotdata"
		:radius="props.radius"
		:categories-to-show="categoriesToShow"
	/>
</template>

<script setup lang="ts">
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import { pvSystems, registry } from '@/assets/js/model'
import { batteries } from '../batteryList/model'
import { shDevices } from '../smartHome/model'
import { counters } from '../counterList/model'
import { computed } from 'vue'
import { chargePoints } from '../chargePointList/model'
import PMArc from './PMArc.vue'
// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
}>()

const categoriesToShow = [
	PowerItemType.chargepoint,
	PowerItemType.battery,
	PowerItemType.device,
	PowerItemType.counter,
]
const emptyPowerItem = computed(() => {
	return {
		name: 'empty',
		type: PowerItemType.counter,
		power: props.emptyPower,
		now: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
		past: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
		color: 'var(--color-bg)',
		icon: '',
		showInGraph: true,
	}
})
const plotdata = computed(() =>
	[registry.getItem('evuOut')].concat(
		chargePointsToShow.value,
		devicesToShow.value,
		countersToShow.value,
		batteriesToShow.value,
		invertersToShow.value,
		registry.getItem('house'),
		emptyPowerItem.value,
	),
)

const chargePointsToShow = computed(() => {
	return Object.values(chargePoints).length > 1
		? Object.values(chargePoints).sort((a, b) => {
				return b.power - a.power
			})
		: [registry.getItem('charging')]
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
		now: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
		past: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
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
		: [registry.getItem('devices')]
})

const batteriesToShow = computed(() =>
	batteries.value.size > 1
		? [...batteries.value.values()]
				.filter((b) => b.power > 0)
				.sort((a, b) => {
					return b.power - a.power
				})
		: batteries.value.size > 0
			? [registry.getItem('batIn')!]
			: [],
)
const countersToShow = computed(() =>
	counters.size > 0
		? [...counters.values()]
				.filter((ctr) => ctr.showInGraph && ctr.power > 0)
				.sort((a, b) => {
					return b.power - a.power
				})
		: [],
)
const invertersToShow = computed(() =>
	pvSystems.value.size > 1
		? [...pvSystems.value.values()]
				.filter((a) => a.power > 0)
				.sort((a, b) => {
					return a.power - b.power
				})
		: registry.getItem('pv').power < 0
			? [registry.getItem('pv')]
			: [],
)
</script>

<style scoped></style>
