<template>
	<g :id="`bar-${props.item.name}`">
		<!-- Main bar -->
		<rect
			class="bar"
			:y="props.yScale(props.id)! + props.itemHeight / 2 - 4"
			x="0"
			rx="6"
			ry="6"
			height="12"
			:width="barlength"
			:fill="item.color"
		/>
		<!-- Pv fraction bar -->
		<rect
			class="bar"
			:y="(props.yScale(props.id) as number) + props.itemHeight / 2 + 10"
			x="0"
			rx="3"
			ry="3"
			height="7"
			:width="pvBarheight"
			fill="var(--color-pv)"
			fill-opacity="100%"
		/>
		<!-- Battery fraction bar  -->
		<rect
			class="bar"
			:y="(props.yScale(props.id) as number) + props.itemHeight / 2 + 10"
			:x="pvBarheight"
			rx="3"
			ry="3"
			height="7"
			:width="batBarheight"
			fill="var(--color-battery)"
			fill-opacity="100%"
		/>
	</g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { PowerItem } from '@/assets/js/types'

const props = defineProps<{
	id: string
	item: PowerItem
	yScale: d3.ScaleBand<string>
	xScale: d3.ScaleLinear<number, number, never>
	itemHeight: number
}>()
const barlength = computed(() => props.xScale(props.item.energy))

const pvBarheight = computed(() => {
	let result = 0
	if (props.item.energyPv > 0) {
		result = props.xScale(props.item.energyPv)
	}
	if (result > barlength.value) {
		result = barlength.value
	}
	return result
})
const batBarheight = computed(() => {
	let result = 0
	if (props.item.energyBat > 0) {
		result = props.xScale(props.item.energyBat)
	}
	if (result > barlength.value) {
		result = barlength.value
	}
	return result
})
</script>

<style scoped></style>
