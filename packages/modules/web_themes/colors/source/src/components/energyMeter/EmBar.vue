<template>
	<g :id="'bar-' + props.item.name" transform="scale(1,-1) translate (0,-445)">
		<!-- Main bar -->
		<rect
			class="bar"
			:x="props.xScale(item.name)"
			y="0"
			:width="props.xScale.bandwidth()"
			:height="barheight"
			:fill="item.color"
		/>
		<!-- Pv fraction inner bar -->
		<rect
			class="bar"
			:x="(props.xScale(item.name) as number) + props.xScale.bandwidth() / 6"
			y="0"
			:width="(props.xScale.bandwidth() * 2) / 3"
			:height="pvBarheight"
			fill="var(--color-pv)"
			fill-opacity="66%"
		/>
		<!-- Battery fraction inner bar  -->
		<rect
			class="bar"
			:x="(props.xScale(item.name) as number) + props.xScale.bandwidth() / 6"
			:y="pvBarheight"
			:width="(props.xScale.bandwidth() * 2) / 3"
			:height="batBarheight"
			fill="var(--color-battery)"
			fill-opacity="66%"
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
	barcount: number
	autarchy?: number
	autText?: string
}>()
const barheight = computed(
	() =>
		props.height -
		props.yScale(props.item.energy) -
		props.margin.top -
		props.margin.bottom,
)

const pvBarheight = computed(() => {
	return props.item.energyPv > 0
		? props.height -
				props.yScale(props.item.energyPv) -
				props.margin.top -
				props.margin.bottom
		: 0
})
const batBarheight = computed(() => {
	return props.item.energyPv > 0
		? props.height -
				props.yScale(props.item.energyBat) -
				props.margin.top -
				props.margin.bottom
		: 0
})
</script>

<style scoped></style>
