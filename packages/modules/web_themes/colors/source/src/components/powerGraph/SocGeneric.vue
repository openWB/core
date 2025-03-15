<template>
	<svg x="0" :width="props.width">
		<g>
			<path
				:id="'soc-' + props.id"
				.origin="autozoom"
				class="soc-baseline"
				:d="myline"
				stroke="var(--color-bg)"
				stroke-width="1"
				fill="none"
			/>
			<path
				:id="'socdashes-' + props.id"
				class="soc-dashes"
				:d="myline"
				:stroke="props.color"
				stroke-width="1"
				:style="{ strokeDasharray: '3,3' }"
				fill="none"
			/>
			<text
				class="cpname"
				:x="props.textX"
				:y="props.textY"
				:style="{ fill: props.color, fontSize: 10 }"
				:text-anchor="props.textAnchor"
			>
				{{ props.name }}
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
	id: string
	name: string
	color: string
	tag: string
	textX: number
	textY: number
	textAnchor: string
	order: number // 0, 1 or 2 (2 == battery)
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
	return scaleLinear()
		.range([props.height - 10, 0])
		.domain([0, 100])
})
const myline = computed(() => {
	const path = line<GraphDataItem>()
		.x((d) => xScale.value(d.date))
		.y((d) => yScale.value(d[props.tag]))
	let p = path(graphData.data)
	return p ? p : ''
})

const autozoom = computed(() => {
	if (graphData.graphMode != 'month' && graphData.graphMode != 'year') {
		const path1: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#soc-' + props.id)
		const path2: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#socdashes-' + props.id)
		xScale.value.range(zoomedRange.value)
		const path = line<GraphDataItem>()
			.x((d) => xScale.value(d.date))
			.y((d) => yScale.value(d[props.tag]))
		path1.attr('d', path(graphData.data))
		path2.attr('d', path(graphData.data))
	}
	return 'zoomed'
})
</script>
<style scoped></style>
