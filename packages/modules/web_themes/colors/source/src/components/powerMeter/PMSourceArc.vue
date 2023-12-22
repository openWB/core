<template>
	<g id="pmSourceArc" :origin="draw" />
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import type { PowerItem } from '@/assets/js/types'
import { sourceSummary } from '@/assets/js/model'
import { pie, arc, select, type PieArcDatum } from 'd3'
import { computed, watchEffect } from 'vue'
// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
}>()
//  computed:
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
	let plotdata = sourceSummary
	plotdata['zz-empty'] = emptyPowerItem
	const arcCount = Object.values(sourceSummary).length - 1

	const pieGenerator = pie<PowerItem>()
		.value((record: PowerItem) => record.power)
		.startAngle(-Math.PI / 2 + props.circleGapSize)
		.endAngle(Math.PI / 2 - props.circleGapSize)
		.sort(null)
	const path = arc<PieArcDatum<PowerItem>>()
		.innerRadius((props.radius / 6) * 5)
		.outerRadius(props.radius)
		.cornerRadius(props.cornerRadius)
		.padAngle(0)
	const graph = select('g#pmSourceArc')
	graph.selectAll('*').remove()
	graph
		.selectAll('sources')
		.data(pieGenerator(Object.values(plotdata)))
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
	return 'pmSourceArc.vue'
})

watchEffect(() => {
	let currentMax =
		sourceSummary.pv.power +
		sourceSummary.evuIn.power +
		sourceSummary.batOut.power
	if (currentMax > globalConfig.maxPower) {
		globalConfig.maxPower = currentMax
	}
})
</script>

<style></style>
