<template>
	<g
		:id="'bar-' + props.item.name"
		:transform="'scale(1,-1) translate (0,-' + (props.height - 72) + ')'"
	>
		<!-- Main bar -->
		<rect
			class="bar"
			:y="props.xScale(item.name)"
			x="0"
			rx="5"
			ry="5"
			:height="props.xScale.bandwidth() / 3"
			:width="barlength"
			:fill="item.color"
		/>
		<!-- Pv fraction bar -->
		<rect
			class="bar"
			:y="
				(props.xScale(item.name) as number) - props.xScale.bandwidth() / 3 + 3
			"
			x="0"
			rx="3"
			ry="3"
			:height="props.xScale.bandwidth() / 5"
			:width="pvBarheight"
			fill="var(--color-pv)"
			fill-opacity="100%"
		/>
		<!-- Battery fraction bar  -->
		<rect
			class="bar"
			:y="
				(props.xScale(item.name) as number) - props.xScale.bandwidth() / 3 + 3
			"
			:x="pvBarheight"
			rx="3"
			ry="3"
			:height="props.xScale.bandwidth() / 5"
			:width="batBarheight"
			fill="var(--color-battery)"
			fill-opacity="100%"
		/>
	</g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'

const props = defineProps<{
	item: PowerItem
	xScale: d3.ScaleBand<string>
	yScale: d3.ScaleLinear<number, number, never>
	margin: MarginType
	height: number
	width: number
	barcount: number
	autarchy?: number
	autText?: string
}>()
const barlength = computed(() => props.yScale(props.item.energy))

const pvBarheight = computed(() => {
	let result = 0
	if (props.item.energyPv > 0) {
		result = props.yScale(props.item.energyPv)
	}
	if (result > barlength.value) {
		result = barlength.value
	}
	return result
})
const batBarheight = computed(() => {
	let result = 0
	if (props.item.energyBat > 0) {
		result = props.yScale(props.item.energyBat)
	}
	if (result > barlength.value) {
		result = barlength.value
	}
	return result
})
</script>

<style scoped></style>
