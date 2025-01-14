<template>
	<g
		id="pgSourceGraph"
		:origin="draw"
		:transform="'translate(' + margin.left + ',' + margin.top + ')'"
	/>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Selection, BaseType } from 'd3'
import {
	select,
	scaleLinear,
	stack,
	extent,
	axisLeft,
	area,
	easeLinear,
} from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import {
	graphData,
	animateSourceGraph,
	sourceGraphIsInitialized,
	xScaleMonth,
} from './model'
const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
}>()

//state
const colors: { [key: string]: string } = {
	house: 'var(--color-house)',
	batIn: 'var(--color-battery)',
	inverter: 'var(--color-pv)',
	batOut: 'var(--color-battery)',
	selfUsage: 'var(--color-pv)',
	evuOut: 'var(--color-export)',
	evuIn: 'var(--color-evu)',
}
var paths: Selection<SVGPathElement, [number, number][], BaseType, never>
var rects: Selection<SVGRectElement, [number, number], BaseType, never>
const duration = globalConfig.showAnimations
	? globalConfig.animationDuration
	: 0
const delay = globalConfig.showAnimations ? globalConfig.animationDelay : 0

// computed:
const draw = computed(() => {
	const graph = select('g#pgSourceGraph')
	if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
		drawBarGraph(graph)
	} else {
		drawGraph(graph)
	}
	graph.selectAll('.axis').remove()
	const yAxis = graph.append('g').attr('class', 'axis')
	yAxis.call(yAxisGenerator.value)
	yAxis.selectAll('.tick').attr('font-size', 12)
	yAxis
		.selectAll('.tick line')
		.attr('stroke', ticklineColor.value)
		.attr('stroke-width', ticklineWidth.value)
	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
	return 'pgSourceGraph.vue'
})
const keys = computed(() => {
	return graphData.graphMode == 'month' || graphData.graphMode == 'year'
		? ['evuIn', 'batOut', 'selfUsage', 'evuOut']
		: ['selfUsage', 'evuOut', 'batOut', 'evuIn']
})
const iScale = computed(() => {
	return scaleLinear()
		.domain([0, graphData.data.length - 1])
		.range([0, props.width])
})

const stackGen = computed(() => stack().keys(keys.value))
const stackedSeries = computed(() => stackGen.value(graphData.data))

const yScale = computed(() => {
	return scaleLinear()
		.range([props.height - 10, 0])
		.domain(
			graphData.graphMode == 'year'
				? [0, Math.ceil(vrange.value[1] * 10) / 10]
				: [0, Math.ceil(vrange.value[1])],
		)
})

const vrange = computed(() => {
	let result = extent(graphData.data, (d) =>
		Math.max(d.pv + d.evuIn + d.batOut, d.selfUsage + d.evuOut),
	)
	if (result[0] != undefined && result[1] != undefined) {
		if (graphData.graphMode == 'year') {
			result[0] = result[0] / 1000
			result[1] = result[1] / 1000
		}
		return result
	} else {
		return [0, 0]
	}
})
const ticklength = computed(() => {
	return graphData.graphMode == 'month' || graphData.graphMode == 'year'
		? -props.width - props.margin.right - 22
		: -props.width
})

const yAxisGenerator = computed(() => {
	return axisLeft<number>(yScale.value)
		.tickSizeInner(ticklength.value)
		.ticks(4)
		.tickFormat((d: number) =>
			(d == 0 ? '' : Math.round(d * 10) / 10).toLocaleString(undefined),
		)
})
const ticklineWidth = computed(() => {
	if (globalConfig.showGrid) {
		return '0.5'
	} else {
		return '1'
	}
})
const ticklineColor = computed(() => {
	return globalConfig.showGrid ? 'var(--color-grid)' : 'var(--color-bg)'
})

function drawGraph(graph: Selection<BaseType, unknown, HTMLElement, never>) {
	const area0 = area()
		.x((d, i) => iScale.value(i))
		.y(yScale.value(0))
	const area1 = area()
		.x((d, i) => iScale.value(i))
		.y0((d) => yScale.value(graphData.graphMode == 'year' ? d[0] / 1000 : d[0]))
		.y1((d) => yScale.value(graphData.graphMode == 'year' ? d[1] / 1000 : d[1]))
	if (animateSourceGraph) {
		graph.selectAll('*').remove()
		paths = graph
			.selectAll('.sourceareas')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('path')
			.attr('fill', (d, i) => colors[keys.value[i]])
			.attr('d', (series) => area0(series))
		paths
			.transition()
			.duration(duration)
			.delay(delay)
			.ease(easeLinear)
			.attr('d', (series) => area1(series))
		sourceGraphIsInitialized()
	} else {
		paths
			.data(stackedSeries.value as [number, number][][])
			.transition()
			.duration(0)
			.ease(easeLinear)
			.attr('d', (series) => area1(series))
	}
}
function drawBarGraph(graph: Selection<BaseType, unknown, HTMLElement, never>) {
	if (animateSourceGraph) {
		graph.selectAll('*').remove()
		rects = graph
			.selectAll('.sourcebar')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('g')
			.attr('fill', (d, i) => colors[keys.value[i]])
			.selectAll('rect')
			.data((d) => d)
			.enter()
			.append('rect')
			.attr('x', (d, i) => {
				return xScaleMonth.value(graphData.data[i].date) ?? 0
			})
			.attr('y', () => yScale.value(0))
			.attr('height', 0)
			.attr('width', xScaleMonth.value.bandwidth())
		rects
			.transition()
			.duration(duration)
			.delay(delay)
			.ease(easeLinear)
			.attr('height', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[0] / 1000) - yScale.value(d[1] / 1000)
					: yScale.value(d[0]) - yScale.value(d[1]),
			)
			.attr('y', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[1] / 1000)
					: yScale.value(d[1]),
			)
		sourceGraphIsInitialized()
	} else {
		graph.selectAll('*').remove()
		rects = graph
			.selectAll('.sourcebar')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('g')
			.attr('fill', (d, i) => colors[keys.value[i]])
			.selectAll('rect')
			.data((d) => d)
			.enter()
			.append('rect')
			.attr('x', (d, i) => {
				return xScaleMonth.value(graphData.data[i].date) ?? 0
			})
			.attr('y', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[1] / 1000)
					: yScale.value(d[1]),
			)
			.attr('width', xScaleMonth.value.bandwidth())
			.attr('height', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[0] / 1000) - yScale.value(d[1] / 1000)
					: yScale.value(d[0]) - yScale.value(d[1]),
			)
	}
}
</script>

<style></style>
