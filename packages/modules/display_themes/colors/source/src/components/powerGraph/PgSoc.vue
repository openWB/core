<template>
	<path
		class="soc-baseline"
		:d="myline"
		stroke="var(--color-bg)"
		stroke-width="1"
		fill="none"
	/>
	<path
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
import { extent, scaleLinear, scaleTime, line } from 'd3'
import { chargePoints } from '../chargePointList/model'
import { graphData, type GraphDataItem } from './model'

const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
	order: number // 0, 1 or 2 (2 == battery)
}>()
// const evs = computed(() => Object.values(vehicles))
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
					props.order == 2 ? d.batSoc : d['soc' + cp.value.connectedVehicle],
				) ?? yScale.value(0),
		)

	let p = path(graphData.data)
	return p ?? ''
})
const vID = computed(() => {
	if (props.order == 2) {
		return 'Speicher'
	} else {
		return cp.value.connectedVehicle
	}
})
const vName = computed(() => {
	if (props.order == 2) {
		return 'Speicher'
	} else {
		return cp.value.vehicleName
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
			return props.width - 3
		case 1:
			return 3
		case 2:
			return props.width / 2
		default:
			return 0 // error
	}
})
const cp = computed(() => {
	const idx = props.order == 2 ? 0 : props.order
	return Object.values(chargePoints)[idx]
})
const nameY = computed(() => {
	if (graphData.data.length > 0) {
		let index: number
		switch (props.order) {
			case 0:
				index = graphData.data.length - 1
				return yScale.value(graphData.data[index]['soc' + vID.value] + 2)
			case 1:
				index = 0
				return yScale.value(graphData.data[index]['soc' + vID.value] + 2)
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
			return 'end'
		case 1:
			return 'start'
		case 2:
			return 'middle'
		default:
			return 'middle'
	}
})
</script>
<style scoped></style>
