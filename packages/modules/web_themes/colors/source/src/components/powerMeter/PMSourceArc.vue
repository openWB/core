<template>
	<PMArc
		:upper-arc="true"
		:plotdata="plotdata"
		:radius="props.radius"
		:categories-to-show="categoriesToShow"
	/>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import { PowerItemType } from '@/assets/js/types'
import { pvSystems, registry } from '@/assets/js/model'
import { computed, watchEffect } from 'vue'
import { batteries } from '../batteryList/model'
import PMArc from './PMArc.vue'

// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
}>()
const categoriesToShow = [PowerItemType.inverter, PowerItemType.battery]

//  computed:
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
	return [registry.getItem('evuIn')].concat(
		invertersToShow.value,
		batteriesToShow.value,
		emptyPowerItem.value,
	)
})
const invertersToShow = computed(() =>
	pvSystems.value.size > 1
		? [...pvSystems.value.values()]
				.filter((a) => a.power < 0)
				.sort((a, b) => {
					return a.power - b.power
				})
		: registry.getItem('pv').power > 0
			? [registry.getItem('pv')]
			: [],
)
const batteriesToShow = computed(() => {
	return batteries.value.size > 1
		? [...batteries.value.values()]
				.filter((b) => b.power < 0)
				.sort((a, b) => {
					return a.power - b.power
				})
		: [registry.getItem('batOut')]
})

watchEffect(() => {
	let currentMax =
		registry.getPower('pv') +
		registry.getPower('evuIn') +
		registry.getPower('batOut')
	if (currentMax > globalConfig.maxPower) {
		globalConfig.maxPower = currentMax
	}
})
</script>

<style></style>
