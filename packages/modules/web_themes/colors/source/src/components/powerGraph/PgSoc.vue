<template>
	<path
		:id="'soc-' + vID"
		.origin="autozoom"
		class="soc-baseline"
		:d="myline"
		stroke="var(--color-bg)"
		stroke-width="1"
		fill="none"
	/>
	<path
		:id="'socdashes-' + vID"
		class="soc-dashes"
		:d="myline"
		:stroke="cpColor"
		stroke-width="1"
		:style="{ strokeDasharray: '3,3' }"
		fill="none"
	/>
	<text
		class="cpname"
		:x="nameX"
		:y="nameY"
		:style="{ fill: cpColor, fontSize: 10 }"
		:text-anchor="textPosition"
	>
		{{ vName }}
	</text>
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
import { topVehicles, vehicles } from '../chargePointList/model'
import { graphData, type GraphDataItem, zoomedRange } from './model'

const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
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
		.y(
			(d) =>
				yScale.value(
					props.order == 2
						? d.batSoc
						: props.order == 0
							? d['soc' + topVehicles.value[0]]
							: d['soc' + topVehicles.value[1]!],
				) ?? yScale.value(0),
		)

	let p = path(graphData.data)
	return p ? p : ''
})
const vID = computed(() => {
	return props.order
})
const vName = computed(() => {
	switch (props.order) {
		case 2:
			return 'Speicher'
		case 1:
			if (vehicles[topVehicles.value[1]] != undefined) {
				return vehicles[topVehicles.value[1]].name
			} else {
				return '???'
			}
		default:
			if (vehicles[topVehicles.value[0]] != undefined) {
				return vehicles[topVehicles.value[0]].name
			} else {
				return '???'
			}
	}
})

const cpColor = computed(() => {
	switch (props.order) {
		case 0:
			return 'var(--color-cp1)'
		case 1:
			return 'var(--color-cp2)'
		case 2:
			return 'var(--color-battery)'
		default:
			return 'red' // error
	}
})
const nameX = computed(() => {
	switch (props.order) {
		case 0:
			return 3
		case 1:
			return props.width - 3
		case 2:
			return props.width / 2
		default:
			return 0 // error
	}
})

const nameY = computed(() => {
	if (graphData.data.length > 0) {
		let index: number
		switch (props.order) {
			case 0:
				index = graphData.data.length - 1
				return yScale.value(
					graphData.data[index]['soc' + topVehicles.value[0]] + 2,
				)
			case 1:
				index = 0
				return yScale.value(
					graphData.data[index]['soc' + topVehicles.value[1]] + 2,
				)
			case 2:
				index = Math.round(graphData.data.length / 2)
				return yScale.value(graphData.data[index].batSoc + 2)
			default:
				return 0
		}
	} else {
		return 0
	}
})
const textPosition = computed(() => {
	switch (props.order) {
		case 0:
			return 'start'
		case 1:
			return 'end'
		case 2:
			return 'middle'
		default:
			return 'middle'
	}
})

const autozoom = computed(() => {
	if (graphData.graphMode != 'month' && graphData.graphMode != 'year') {
		const path1: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#soc-' + vID.value)
		const path2: Selection<SVGPathElement, unknown, HTMLElement, unknown> =
			select('path#socdashes-' + vID.value)
		xScale.value.range(zoomedRange.value)
		const path = line<GraphDataItem>()
			.x((d) => xScale.value(d.date))
			.y(
				(d) =>
					yScale.value(
						props.order == 2
							? d.batSoc
							: props.order == 1
								? d['soc' + topVehicles.value[0]]
								: d['soc' + topVehicles.value[1]!],
					) ?? yScale.value(0),
			)
		path1.attr('d', path(graphData.data))
		path2.attr('d', path(graphData.data))
	}
	return 'zoomed'
})
</script>
<style scoped></style>
