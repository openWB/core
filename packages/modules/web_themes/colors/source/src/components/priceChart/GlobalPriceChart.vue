<template>
	<WbWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-coins me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span>Strompreis</span>
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span
					v-if="etData.active"
					class="badge rounded-pill pricebadge mb-1 me-1"
					>{{ etData.etCurrentPriceString }}</span
				>
				<span
					v-if="etData.active"
					class="badge rounded-pill providerbadge mb-1 m-0"
					>{{ etData.etProvider }}</span
				>
			</div>
		</template>
		<div class="grapharea">
			<figure id="pricechart" class="p-0 m-0 pricefigure">
				<svg viewBox="0 0 400 280">
					<g
						:id="chartId"
						:origin="draw"
						:transform="'translate(' + margin.top + ',' + margin.right + ')'"
					/>
				</svg>
			</figure>
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { etData } from './model'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import {
	extent,
	scaleTime,
	scaleLinear,
	axisBottom,
	timeFormat,
	axisLeft,
	select,
	line,
} from 'd3'

const props = defineProps<{
	id: string
}>()

const needsUpdate = ref(false)
let dummy = false
const width = 400
const height = 250
const margin = { top: 0, bottom: 15, left: 20, right: 5 }
const axisfontsize = 12
const plotdata = computed(() => {
	let valueArray: [Date, number][] = []
	if (etData.etPriceList.size > 0) {
		etData.etPriceList.forEach((value, date) => {
			valueArray.push([date, value])
		})
	}
	return valueArray
})
const barwidth = computed(() => {
	if (plotdata.value.length > 1) {
		return (width - margin.left - margin.right) / plotdata.value.length - 1
	} else {
		return 0
	}
})
const xScale = computed(() => {
	let xdomain = extent(plotdata.value, (d) => d[0]) as [Date, Date]

	return scaleTime()
		.range([margin.left, width - margin.left - margin.right])
		.domain(xdomain)
})
const yDomain = computed(() => {
	let yd = extent(plotdata.value, (d) => d[1]) as [number, number]
	yd[0] = Math.floor(yd[0]) - 1
	yd[1] = Math.floor(yd[1]) + 1
	return yd
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom, 0])
		.domain(yDomain.value)
})
const zeroPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(0)],
		[width - margin.right, yScale.value(0)],
	]
	return generator(points as [number, number][])
})
const xAxisGenerator = computed(() => {
	return axisBottom<Date>(xScale.value)
		.ticks(6)
		.tickSize(5)
		.tickFormat(timeFormat('%H:%M'))
})
const yAxisGenerator = computed(() => {
	return axisLeft<number>(yScale.value)
		.ticks(6)
		.tickSizeInner(-(width - margin.right))
		.tickFormat((d) => d.toString())
})
const draw = computed(() => {
	if (needsUpdate.value == true) {
		dummy = !dummy
	}

	const svg = select('g#' + chartId.value)
	svg.selectAll('*').remove()
	const bargroups = svg
		.selectAll('bar')
		.data(plotdata.value)
		.enter()
		.append('g')
	bargroups
		.append('rect')
		.attr('class', 'bar')
		.attr('x', (d) => xScale.value(d[0]))
		.attr('y', (d) => yScale.value(d[1]))
		.attr('width', barwidth.value)
		.attr('height', (d) => yScale.value(yDomain.value[0]) - yScale.value(d[1]))
		.attr('fill', 'var(--color-charging)')
	// X Axis
	const xAxis = svg.append('g').attr('class', 'axis').call(xAxisGenerator.value)
	xAxis.attr('transform', 'translate(0,' + (height - margin.bottom) + ')')
	xAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')
	xAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-fg)')
		.attr('stroke-width', '0.5')
	xAxis.select('.domain').attr('stroke', 'var(--color-bg')
	// Y Axis
	const yAxis = svg.append('g').attr('class', 'axis').call(yAxisGenerator.value)
	yAxis.attr('transform', 'translate(' + margin.left + ',' + 0 + ')')
	yAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')

	yAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', '0.5')

	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')

	// zero line
	if (yDomain.value[0] < 0) {
		svg
			.append('path')
			.attr('d', zeroPath.value)
			.attr('stroke', 'var(--color-fg)')
	}
	return 'PriceChart.vue'
})
const chartId = computed(() => {
	return 'priceChartCanvas' + props.id
})
onMounted(() => {
	needsUpdate.value = !needsUpdate.value
})
</script>

<style scoped>
.pricebadge {
	background-color: var(--color-charging);
	font-weight: normal;
}
.providerbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}
.grapharea {
	grid-column-start: 1;
	grid-column-end: 13;
	width: 100%;
	object-fit: cover;
	max-height: 100%;

	justify-items: stretch;
}
.pricefigure {
	justify-self: stretch;
}
</style>
