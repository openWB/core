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
		{{ cpName }}
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
	order: number // 0 or 1
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
				yScale.value(d['soc' + cp.value.connectedVehicle]) ?? yScale.value(0),
		)
	let p = path(graphData.data)
	return p ? p : ''
})
const cpName = computed(() => {
	return cp.value.vehicleName
})
const cpColor = computed(() => {
	return props.order == 0 ? 'var(--color-cp1)' : 'var(--color-cp2)'
})
const nameX = computed(() => {
	if (props.order == 0) {
		return props.width - 3
	} else {
		return 3
	}
})
const cp = computed(() => {
	return Object.values(chargePoints)[props.order]
})

const nameY = computed(() => {
	if (graphData.data.length > 0) {
		const index = props.order == 0 ? graphData.data.length - 1 : 0
		return yScale.value(
			graphData.data[index]['soc' + cp.value.connectedVehicle] + 2,
		)
	} else {
		return 0
	}
})
const textPosition = computed(() => {
	if (props.order == 0) {
		return 'end'
	} else {
		return 'start'
	}
})
</script>
<style scoped></style>
