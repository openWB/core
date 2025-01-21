<template>
	<g id="pmUsageArc" :origin="draw" />
</template>

<script setup lang="ts">
import type { PowerItem } from '@/assets/js/types'
import { usageSummary } from '@/assets/js/model'
import { shDevices } from '../smartHome/model'
import { type PieArcDatum, select, arc, pie } from 'd3'
import { computed } from 'vue'
// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
}>()
//  computed: {
const draw = computed(() => {
	// Draw the arc using d3
	let emptyPowerItem: PowerItem = {
		name: '',
		power: props.emptyPower,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: 'var(--color-bg)',
		icon: '',
	}
	const plotdata = [usageSummary.evuOut, usageSummary.charging]
		.concat(
			[...shDevices.values()]
				.filter((row) => row.configured && !row.countAsHouse)
				.sort((a, b) => {
					return b.power - a.power
				}) as PowerItem[],
		)
		.concat([usageSummary.batIn, usageSummary.house])
		.concat(emptyPowerItem)
	const arcCount = plotdata.length - 1
	const pieGenerator = pie<PowerItem>()
		.value((record: PowerItem) => record.power)
		.startAngle(Math.PI * 1.5 - props.circleGapSize)
		.endAngle(Math.PI / 2 + props.circleGapSize)
		.sort(null)
	const path = arc<PieArcDatum<PowerItem>>()
		.innerRadius((props.radius / 6) * 5)
		.outerRadius(props.radius)
		.cornerRadius(props.cornerRadius)
	const graph = select('g#pmUsageArc')
	graph.selectAll('*').remove()
	graph
		.selectAll('consumers')
		.data(pieGenerator(plotdata))
		.enter()
		.append('path')
		.attr('d', path)
		.attr('fill', (d) => d.data.color)
		.attr('stroke', (d, i) =>
			i == arcCount
				? d.data.power > 0
					? 'var(--color-scale)'
					: 'null'
				: d.data.color,
		)
	return 'pmUsageArc.vue'
})
</script>

<style></style>
