<template>
	<g
		id="pgUsageGraph"
		:origin="draw"
		:origin2="autozoom"
		:transform="'translate(' + margin.left + ',' + margin.top + ')'"
	/>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Selection, BaseType } from 'd3'
import {
	select,
	stack,
	scaleLinear,
	extent,
	axisLeft,
	area,
	easeLinear,
	curveBumpX,
} from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import {
	graphData,
	animateUsageGraph,
	usageGraphIsInitialized,
	xScaleMonth,
	xScale,
	zoomedRange,
} from './model'
import { chargePoints } from '../chargePointList/model'
const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
	stackOrder: number
}>()

//state
const keys = computed(() => {
	if (globalConfig.showInverters) {
		return [
			['house', 'charging', 'devices', 'batIn'],
			['charging', 'devices', 'batIn', 'house'],
			['devices', 'batIn', 'charging', 'house'],
			['batIn', 'charging', 'house', 'devices'],
		]
	} else {
		return [
			['house', 'charging', 'devices', 'batIn', 'evuOut'],
			['charging', 'devices', 'batIn', 'house', 'evuOut'],
			['devices', 'batIn', 'charging', 'house', 'evuOut'],
			['batIn', 'charging', 'house', 'devices', 'evuOut'],
		]
	}
})
const colors: { [key: string]: string } = {
	house: 'var(--color-house)',
	charging: 'var(--color-charging)',
	batIn: 'var(--color-battery)',
	batOut: 'var(--color-battery)',
	selfUsage: 'var(--color-pv)',
	evuOut: 'var(--color-export)',
	evuIn: 'var(--color-evu)',
	cp0: 'var(--color-cp0)',
	cp1: 'var(--color-cp1)',
	cp2: 'var(--color-cp2)',
	cp3: 'var(--color-cp3)',
	sh1: 'var(--color-sh1)',
	sh2: 'var(--color-sh2)',
	sh3: 'var(--color-sh3)',
	sh4: 'var(--color-sh4)',
	devices: 'var(--color-devices)',
}
var paths: Selection<SVGPathElement, [number, number][], BaseType, never>
var rects: Selection<SVGRectElement, [number, number], BaseType, never>
const duration = globalConfig.showAnimations
	? globalConfig.animationDuration
	: 0
const delay = globalConfig.showAnimations ? globalConfig.animationDelay : 0

// computed:
const draw = computed(() => {
	const graph = select('g#pgUsageGraph')
	if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
		drawBarGraph(graph)
	} else {
		drawGraph(graph)
	}
	graph.selectAll('.axis').remove()
	const yAxis = graph.append('g').attr('class', 'axis')
	yAxis.call(yAxisGenerator.value)
	yAxis
		.selectAll('.tick')
		.attr('font-size', 12)
		.attr('color', 'var(--color-axis)')
	if (globalConfig.showGrid) {
		yAxis
			.selectAll('.tick line')
			.attr('stroke', 'var(--color-grid)')
			.attr('stroke-width', '0.5')
	} else {
		yAxis.selectAll('.tick line').attr('stroke', 'var(--color-bg)')
	}
	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')

	return 'pgUsageGraph.vue'
})
//const stackGen = computed(() => stack().keys(keys[props.stackOrder].concat(['cp3'])))
const stackGen = computed(() => {
	return stack()
		.value((d, key) => d[key] ?? 0)
		.keys(keysToUse.value)
})
const stackedSeries = computed(() => stackGen.value(graphData.data))

const yScale = computed(() => {
	return scaleLinear()
		.range([props.height + 10, 2 * props.height])
		.domain(
			graphData.graphMode == 'year'
				? [0, Math.ceil(vrange.value[1] * 10) / 10]
				: [0, Math.ceil(vrange.value[1])],
		)
})

const keysToUse = computed(() => {
	if (
		graphData.graphMode != 'today' &&
		graphData.graphMode != 'day' &&
		graphData.graphMode != 'live'
	) {
		return keys.value[props.stackOrder]
	} else {
		const k = keys.value[props.stackOrder].slice()
		const idx = k.indexOf('charging')
		k.splice(idx, 1)
		const pattern = /cp\d+/
		let additionalKeys: string[] = []
		if (graphData.data.length > 0) {
			additionalKeys = Object.keys(graphData.data[0]).reduce(
				(list: string[], element: string) => {
					if (element.match(pattern)) {
						list.push(element)
					}
					return list
				},
				[],
			)
		}
		additionalKeys.forEach((key, i) => {
			k.splice(idx + i, 0, key)
			colors[key] = chargePoints[+key.slice(2)]?.color ?? 'black'
		})
		if (globalConfig.showInverters) {
			k.push('evuOut')
		}
		return k
	}
})

const vrange = computed(() => {
	let result = extent(
		graphData.data,
		(d) => d.house + d.charging + d.batIn + d.devices + d.evuOut,
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
function drawGraph(graph: Selection<BaseType, unknown, HTMLElement, never>) {
	const area0 = area()
		.x((d, i) => xScale.value(graphData.data[i].date))
		.y(yScale.value(0))
		.curve(curveBumpX)
	const area1 = area()
		.x((d, i) => xScale.value(graphData.data[i].date))
		.y0((d) => yScale.value(d[0]))
		.y1((d) => yScale.value(d[1]))
		.curve(curveBumpX)
	if (globalConfig.showAnimations) {
		if (animateUsageGraph) {
			graph.selectAll('*').remove()
			paths = graph
				.selectAll('.usageareas')
				.data(stackedSeries.value as [number, number][][])
				.enter()
				.append('path')
				.attr('d', (series) => area0(series))
				.attr('fill', (d, i: number) => colors[keysToUse.value[i]])
			paths
				.transition()
				.duration(300)
				.delay(100)
				.ease(easeLinear)
				.attr('d', (series) => area1(series))
			usageGraphIsInitialized()
		} else {
			graph.selectAll('*').remove()
			graph
				.selectAll('.usageareas')

				.data(stackedSeries.value as [number, number][][])
				.enter()
				.append('path')
				.attr('d', (series) => area1(series))
				.attr('fill', (d, i: number) => colors[keysToUse.value[i]])
		}
	} else {
		graph.selectAll('*').remove()
		graph
			.selectAll('.usageareas')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('path')
			.attr('d', (series) => area1(series))
			.attr('fill', (d, i: number) => colors[keysToUse.value[i]])
	}
}
function drawBarGraph(graph: Selection<BaseType, unknown, HTMLElement, never>) {
	if (animateUsageGraph) {
		graph.selectAll('*').remove()
		rects = graph
			.selectAll('.usagebar')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('g')
			.attr('fill', (d, i) => colors[keys.value[props.stackOrder][i]])
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
			.attr('y', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[0] / 1000)
					: yScale.value(d[0]),
			)
			.attr('height', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[1] / 1000) - yScale.value(d[0] / 1000)
					: yScale.value(d[1]) - yScale.value(d[0]),
			)
		usageGraphIsInitialized()
	} else {
		graph.selectAll('*').remove()
		rects = graph
			.selectAll('.usagebar')
			.data(stackedSeries.value as [number, number][][])
			.enter()
			.append('g')
			.attr('fill', (d, i) => colors[keys.value[props.stackOrder][i]])
			.selectAll('rect')
			.data((d) => d)
			.enter()
			.append('rect')
			.attr('x', (d, i) => {
				return xScaleMonth.value(graphData.data[i].date) ?? 0
			})
			.attr('y', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[0] / 1000)
					: yScale.value(d[0]),
			)
			.attr('height', (d) =>
				graphData.graphMode == 'year'
					? yScale.value(d[1] / 1000) - yScale.value(d[0] / 1000)
					: yScale.value(d[1]) - yScale.value(d[0]),
			)
			.attr('width', xScaleMonth.value.bandwidth())
	}
}

const autozoom = computed(() => {
	const graph: Selection<SVGGElement, unknown, HTMLElement, unknown> =
		select('g#pgUsageGraph')
	if (graphData.graphMode != 'month' && graphData.graphMode != 'year') {
		xScale.value.range(zoomedRange.value)
		const areaz = area()
			.x((d, i) => xScale.value(graphData.data[i].date))
			.y0((d) => yScale.value(d[0]))
			.y1((d) => yScale.value(d[1]))
			.curve(curveBumpX)
		graph
			.selectAll('path')
			.attr('d', (series) =>
				series ? areaz(series as [number, number][]) : '',
			)
	}
	return 'zoomed'
})
</script>

<style></style>
