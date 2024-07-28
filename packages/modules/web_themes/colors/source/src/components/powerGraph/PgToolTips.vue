<template>
	<g
		id="pgToolTips"
		:origin="autozoom"
		:transform="'translate(' + margin.left + ',' + margin.top + ')'"
	>
		<g v-for="d in data" :key="d.date" class="ttarea">
			<rect
				:x="xScale(d.date)"
				y="0"
				:height="height"
				class="ttrect"
				:width="graphData.data.length > 0 ? width / graphData.data.length : 0"
				opacity="1%"
				fill="var(--color-charging)"
			></rect>
			<PgToolTipItem
				:entry="d"
				:boxwidth="boxwidth"
				:x-scale="xScale2"
			></PgToolTipItem>
		</g>
	</g>
</template>
<script setup lang="ts">
import { extent, scaleTime, scaleUtc, select } from 'd3'
import { computed } from 'vue'
import { graphData, zoomedRange, type GraphDataItem } from './model'
import PgToolTipItem from './PgToolTipItem.vue'

const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
	data: GraphDataItem[]
}>()
const boxwidth = 140
const xScale = computed(() => {
	const e = extent(props.data, (d) => new Date(d.date))
	if (e[0] && e[1]) {
		return scaleUtc<number>()
			.domain(e)
			.range([0, props.width - props.margin.right])
	} else {
		return scaleTime().range([0, 0])
	}
})
const xScale2 = computed(() => {
	const e = extent(props.data, (d) => new Date(d.date))
	if (e[0] && e[1]) {
		return scaleUtc<number>()
			.domain(e)
			.range([0, props.width - props.margin.right - boxwidth])
	} else {
		return scaleTime().range([0, 0])
	}
})
const autozoom = computed(() => {
	if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
		xScale.value.range(zoomedRange.value)
		select('g#pgToolTips')
			.selectAll('g.ttarea')
			.select('rect')
			.attr('x', (d, i) =>
				props.data.length > i ? xScale.value(props.data[i].date) : 0,
			)
			.attr(
				'width',
				props.data.length > 0
					? (zoomedRange.value[1] - zoomedRange.value[0]) / props.data.length
					: 0,
			)
	}
	return 'PgToolTips.vue:autozoom'
})
</script>
<style scoped></style>
