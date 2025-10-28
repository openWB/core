<template>
	<g :id="'bar-' + props.id" transform="scale(1,-1) translate (0,-445)">
		<!-- Main bar -->
		<rect
			class="bar"
			:x="props.xScale(props.id)"
			y="0"
			:width="props.xScale.bandwidth()"
			:height="barheight"
			:fill="item.color"
		/>
		<!-- Pv fraction inner bar -->
		<rect
			class="bar"
			:x="(props.xScale(props.id) as number) + props.xScale.bandwidth() / 6"
			y="0"
			:width="(props.xScale.bandwidth() * 2) / 3"
			:height="pvBarheight"
			fill="var(--color-pv)"
			fill-opacity="66%"
		/>
		<!-- Battery fraction inner bar  -->
		<rect
			class="bar"
			:x="(props.xScale(props.id) as number) + props.xScale.bandwidth() / 6"
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
import { graphData } from '../powerGraph/model'

const props = defineProps<{
	item: PowerItem
	id: string
	xScale: d3.ScaleBand<string>
	yScale: d3.ScaleLinear<number, number, never>
	margin: MarginType
	height: number
}>()
const barheight = computed(
	() =>
		props.height -
		props.yScale(props.item[graphScope.value].energy) -
		props.margin.top -
		props.margin.bottom,
)
const pvBarheight = computed(() => {
	let result = 0
	if (props.item[graphScope.value].energyPv > 0) {
		result =
			props.height -
			props.yScale(props.item[graphScope.value].energyPv) -
			props.margin.top -
			props.margin.bottom
	}
	if (result > barheight.value) {
		result = barheight.value
	}
	return result
})
const batBarheight = computed(() => {
	let result = 0
	if (props.item[graphScope.value].energyBat > 0) {
		result =
			props.height -
			props.yScale(props.item[graphScope.value].energyBat) -
			props.margin.top -
			props.margin.bottom
	}
	if (result > barheight.value) {
		result = barheight.value
	}
	return result
})
const graphScope = computed(() => (graphData.usePastData ? 'past' : 'now'))
</script>

<style scoped></style>
