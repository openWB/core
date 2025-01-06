<template>
	<WbWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-coins me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span>Strompreis</span>
		</template>
		<template #buttons>
			<WbBadge v-if="etData.active" bgcolor="var(--color-charging)">{{
				etData.etCurrentPriceString
			}}</WbBadge>
			<WbBadge v-if="etData.active" bgcolor="var(--color-menu)">{{
				etData.etProvider
			}}</WbBadge>
		</template>
		<div class="grapharea">
			<figure id="pricechart" class="p-1 m-0 pricefigure">
				<svg viewBox="0 0 400 280">
					<g
						:id="chartId"
						:origin="draw"
						:transform="'translate(' + margin.top + ',' + margin.left + ') '"
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
import WbBadge from '../shared/WbBadge.vue'
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
import { globalConfig } from '@/assets/js/themeConfig'

const props = defineProps<{
	id: string
}>()

const needsUpdate = ref(false)
let dummy = false
const width = 380
const height = 250
const margin = { top: 0, bottom: 15, left: 20, right: 0 }
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
		return (width - margin.left - margin.right) / plotdata.value.length
	} else {
		return 0
	}
})
const xScale = computed(() => {
	let xdomain = extent(plotdata.value, (d) => d[0]) as [Date, Date]
	if (xdomain[1]) {
		xdomain[1] = new Date(xdomain[1])
		xdomain[1].setTime(xdomain[1].getTime() + 3600000)
	}
	return scaleTime()
		.range([margin.left, width - margin.right])
		.domain(xdomain)
})
const yDomain = computed(() => {
	let yd = [0, 0]
	if (plotdata.value.length > 0) {
		yd = extent(plotdata.value, (d) => d[1]) as [number, number]
		yd[0] = Math.floor(yd[0]) - 1
		yd[1] = Math.floor(yd[1]) + 1
	}
	return yd
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom, 0])
		.domain(yDomain.value)
})
const lowerPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(globalConfig.lowerPriceBound)],
		[width - margin.right, yScale.value(globalConfig.lowerPriceBound)],
	]
	return generator(points as [number, number][])
})
const upperPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(globalConfig.upperPriceBound)],
		[width - margin.right, yScale.value(globalConfig.upperPriceBound)],
	]
	return generator(points as [number, number][])
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
		.ticks(plotdata.value.length)
		.tickSize(5)
		.tickSizeInner(-height)
		.tickFormat((d) => (d.getHours() % 6 == 0 ? timeFormat('%H:%M')(d) : ''))
})
const yAxisGenerator = computed(() => {
	return (
		axisLeft<number>(yScale.value)
			//.ticks(yDomain.value[1] - yDomain.value[0])
			.ticks(yDomain.value[1] - yDomain.value[0])
			.tickSize(0)
			.tickSizeInner(-(width - margin.right - margin.left))
			.tickFormat((d) => d.toString())
	)
})
// Draw the diagram
const draw = computed(() => {
	if (needsUpdate.value == true) {
		dummy = !dummy
	}
	const svg = select('g#' + chartId.value)
	svg.selectAll('*').remove()
	// Bars
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
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) =>
			(d as Date).getHours() % 6 == 0 ? '2' : '0.5',
		)
	xAxis.select('.domain').attr('stroke', 'var(--color-bg')
	// Y Axis
	const yAxis = svg.append('g').attr('class', 'axis').call(yAxisGenerator.value)
	yAxis.attr('transform', 'translate(' + margin.left + ',0)')
	yAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')
	yAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) => ((d as number) % 5 == 0 ? '2' : '0.5'))

	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
	if (yDomain.value[0] < 0) {
		svg
			.append('path')
			.attr('d', zeroPath.value)
			.attr('stroke', 'var(--color-fg)')
	}
	// Line for lower bound
	svg.append('path').attr('d', lowerPath.value).attr('stroke', 'green')
	// Line for upper bound
	svg.append('path').attr('d', upperPath.value).attr('stroke', 'red')

	// Tooltips
	const ttips = svg
		.selectAll('ttip')
		.data(plotdata.value)
		.enter()
		.append('g')
		.attr('class', 'ttarea')
	ttips
		.append('rect')
		.attr('x', (d) => xScale.value(d[0]))
		.attr('y', (d) => yScale.value(d[1]))
		.attr('height', (d) => yScale.value(yDomain.value[0]) - yScale.value(d[1]))
		.attr('class', 'ttrect')
		.attr('width', barwidth.value)
		.attr('opacity', '1%')
		.attr('fill', 'var(--color-charging)')
	const tt = ttips
		.append('g')
		.attr('class', 'ttmessage')
		.attr(
			'transform',
			(d) =>
				'translate(' +
				(xScale.value(d[0]) - 30 + barwidth.value / 2) +
				',' +
				(yScale.value(d[1]) - 16) +
				')',
		)
	tt.append('rect')
		.attr('rx', 5)
		.attr('width', '60')
		.attr('height', '30')
		.attr('fill', 'var(--color-menu)')
	const texts = tt
		.append('text')
		.attr('text-anchor', 'middle')
		.attr('x', 30)
		.attr('y', 12)
		.attr('font-size', axisfontsize)
		.attr('fill', 'var(--color-bg)')
	texts
		.append('tspan')
		.attr('x', 30)
		.attr('dy', '0em')
		.text((d) => timeFormat('%H:%M')(d[0]))
	texts
		.append('tspan')
		.attr('x', 30)
		.attr('dy', '1.1em')
		.text((d) => Math.round(d[1] * 10) / 10 + ' ct')
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
.priceWbBadge {
	background-color: var(--color-charging);
	font-weight: normal;
}

.providerWbBadge {
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
