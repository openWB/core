<template>
	<svg x="0" :width="props.width" class="Prices">
		<g>
			<path
				id="price"
				.origin="autozoom"
				class="price-baseline"
				:d="myline"
				stroke="var(--color-bg)"
				stroke-width="1"
				fill="none"
			/>
			<path
				id="pricedashes"
				class="price-dashes"
				:d="myline"
				stroke="crimson"
				stroke-width="1"
				:style="{ strokeDasharray: '3,1' }"
				fill="none"
			/>
			<text
				class="pricename"
				:x="props.width / 2"
				:y="nameY"
				:style="{ fill: 'crimson', fontSize: 10 }"
				text-anchor="middle"
			>
				Strompreis
			</text>
		</g>
	</svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
	extent,
	scaleLinear,
	scaleTime,
	line,
	type Selection,
	select,
} from 'd3'
import { graphData, type GraphDataItem, zoomedRange } from './model'

const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
}>()
const xScale = computed(() => {
	let e = extent(graphData.data, (d) => d.date)
	if (e[0] && e[1]) {
		return scaleTime<number>().domain(e).range([0, props.width])
	} else {
		return scaleTime().range([0, 0])
	}
})
const yScale = computed(() => {
	let e = extent(graphData.data, (d) => d.price)
	if (e[0] && e[1]) {
		return scaleLinear()
			.range([props.height - 10, 5])
			.domain(e)
	} else {
		return scaleLinear()
			.range([props.height - 10, 0])
			.domain([0, 0])
	}
})
const myline = computed(() => {
	const path = line<GraphDataItem>()
		.x((d) => xScale.value(d.date))
		.y((d) => yScale.value(d.price) ?? yScale.value(0))
	let p = path(graphData.data)
	return p ? p : ''
})

const nameY = computed(() => {
	if (graphData.data.length > 0) {
		let index: number
		index = Math.round(graphData.data.length / 2)
		return yScale.value(graphData.data[index].price) + 2
	} else {
		return 0
	}
})

const autozoom = computed(() => {
	if (graphData.graphMode != 'month' && graphData.graphMode != 'year') {
		const path1: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#price')
		const path2: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#pricedashes')
		xScale.value.range(zoomedRange.value)
		const path = line<GraphDataItem>()
			.x((d) => xScale.value(d.date))
			.y((d) => yScale.value(d.price) ?? yScale.value(0))
		path1.attr('d', path(graphData.data))
		path2.attr('d', path(graphData.data))
	}
	return 'zoomed'
})
</script>
<style scoped></style>
