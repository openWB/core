<template>
	<figure id="pricechart" class="p-0 m-0">
		<svg viewBox="0 0 400 260">
			<g :transform="'translate(' + margin.top + ',' + margin.right + ')'">
				<g :id="'pricechart-' + id" :origin="draw" />
				<g
					:id="'xaxis-' + id"
					class="axis"
					:transform="`translate(0,${height - margin.bottom})`"
				/>
				<g
					:id="'yaxis-' + id"
					class="axis"
					:transform="`translate(${margin.left},0)`"
				/>
				<path
					v-if="yDomain[0] < 0"
					:d="zeroPath!"
					stroke="var(--color-fg)"
					stroke-width="1"
				/>
				<path :d="lowerPath!" stroke="green" />
				<path :d="upperPath!" stroke="red" />
				<path :d="maxPricePath!" stroke="yellow" />
			</g>
			<g id="tooltips" />
		</svg>
	</figure>
</template>
<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import {
	select,
	extent,
	scaleTime,
	scaleLinear,
	axisBottom,
	axisLeft,
	timeFormat,
	line,
	type AxisContainerElement,
} from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import { etData } from './model'
const props = defineProps<{
	id: string
	maxPrice?: number
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
		return (width - margin.left - margin.right) / plotdata.value.length
	} else {
		return 0
	}
})
const xScale = computed(() => {
	let xdomain = extent(plotdata.value, (d) => d[0]) as [Date, Date]
	if (xdomain[1]) {
		xdomain[1] = new Date(xdomain[1])
		xdomain[1].setTime(xdomain[1].getTime() + 900000)
	}
	return scaleTime()
		.range([margin.left, width - margin.left - margin.right])
		.domain(xdomain)
})
const yDomain = computed(() => {
	let yd = [0, 0]
	if (plotdata.value.length > 0) {
		yd = extent(plotdata.value, (d) => d[1]) as [number, number]
		yd[0] = Math.floor(yd[0] - 1)
		yd[1] = Math.floor(yd[1] + 1)
	} else {
		yd = [0, 0]
	}
	return yd
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom, 0])
		.domain(yDomain.value)
})
const maxPricePath = computed(() => {
	if (props.maxPrice != undefined) {
		const generator = line()

		const points = [
			[margin.left, yScale.value(props.maxPrice)],
			[width - margin.left - margin.right, yScale.value(props.maxPrice)],
		]
		return generator(points as [number, number][])
	} else {
		return ''
	}
})
const lowerPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(globalConfig.lowerPriceBound)],
		[
			width - margin.left - margin.right,
			yScale.value(globalConfig.lowerPriceBound),
		],
	]
	return generator(points as [number, number][])
})
const upperPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(globalConfig.upperPriceBound)],
		[
			width - margin.left - margin.right,
			yScale.value(globalConfig.upperPriceBound),
		],
	]
	return generator(points as [number, number][])
})

const zeroPath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(0)],
		[width - margin.left - margin.right, yScale.value(0)],
	]
	return generator(points as [number, number][])
})

const xAxisGenerator = computed(() => {
	return axisBottom<Date>(xScale.value)
		.ticks(plotdata.value.length)
		.tickSize(5)
		.tickSizeInner(-height)
		.tickFormat((d) =>
			d.getHours() % 6 == 0 && d.getMinutes() == 0
				? timeFormat('%H:%M')(d)
				: '',
		)
})
const yAxisGenerator = computed(() => {
	return axisLeft<number>(yScale.value)
		.ticks(yDomain.value[1] - yDomain.value[0])
		.tickSizeInner(-(width - margin.right - margin.left))
		.tickFormat((d: number) => (d % 5 != 0 ? '' : d.toString()))
})

const draw = computed(() => {
	if (needsUpdate.value == true) {
		dummy = !dummy
	}
	const svg = select('g#' + 'pricechart-' + props.id)
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
		.attr('fill', (d) =>
			props.maxPrice != undefined
				? d[1] <= props.maxPrice
					? 'var(--color-charging)'
					: 'var(--color-axis)'
				: 'var(--color-charging)',
		)
	// X Axis
	const xAxis = select<AxisContainerElement, number>(
		'g#xaxis-' + props.id,
	).call(xAxisGenerator.value)
	xAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')
	xAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) =>
			(d as Date).getMinutes() == 0
				? (d as Date).getHours() % 6 == 0
					? '2'
					: '0.5'
				: '0',
		)
	xAxis.select('.domain').attr('stroke', 'var(--color-bg')
	// Y Axis
	const yAxis = select<AxisContainerElement, number>(
		'g#yaxis-' + props.id,
	).call(yAxisGenerator.value)
	yAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')
	yAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) => ((d as number) % 5 == 0 ? '2' : '0.5'))
	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
	// Tooltips
	const ttips = select('g#tooltips')
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

onMounted(() => {
	needsUpdate.value = !needsUpdate.value
})
</script>
<style scoped></style>
