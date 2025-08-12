<template>
	<PMArc
		:upper-arc="true"
		:plotdata="plotdata"
		:radius="props.radius"
		:show-labels="props.showLabels"
		:categories-to-show="categoriesToShow"
	/>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import { PowerItemType } from '@/assets/js/types'
import { pvSystems, sourceSummary } from '@/assets/js/model'
import { computed, watchEffect } from 'vue'
import { batteries } from '../batteryList/model'
import PMArc from './PMArc.vue'

// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
	showLabels: boolean
}>()
const categoriesToShow = [PowerItemType.inverter, PowerItemType.battery]

//  computed:
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
	return [sourceSummary.evuIn].concat(
		invertersToShow.value,
		batteriesToShow.value,
		emptyPowerItem.value,
	)
})
const invertersToShow = computed(() =>
	pvSystems.value.size > 1
		? [...pvSystems.value.values()].sort((a, b) => {
				return a.power - b.power
			})
		: [sourceSummary.pv],
)
const batteriesToShow = computed(() => {
	return batteries.value.size > 1
		? [...batteries.value.values()]
				.filter((b) => b.power < 0)
				.sort((a, b) => {
					return a.power - b.power
				})
		: [sourceSummary.batOut]
})

watchEffect(() => {
	let currentMax =
		sourceSummary.pv.power +
		sourceSummary.evuIn.power +
		sourceSummary.batOut.power
	if (currentMax > globalConfig.maxPower) {
		globalConfig.maxPower = currentMax
	}
})
</script>

<style></style>
