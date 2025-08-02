<template>
	<g>
		<defs>
			<filter id="f1">
				<feDropShadow
					dx="2"
					dy="2"
					rx="10"
					ry="10"
					stdDeviation="1"
					flood-opacity="0.7"
				/>
			</filter>
		</defs>
		<g id="pmSourceArc" :origin="draw" />
	</g>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import { fgColor, formatWatt } from '@/assets/js/helpers'
import { pvSystems, sourceSummary } from '@/assets/js/model'
import {
	pie,
	arc,
	select,
	type PieArcDatum,
	type EnterElement,
	type BaseType,
	type Selection,
	type Arc,
} from 'd3'
import { computed, watchEffect } from 'vue'
import { batteries } from '../batteryList/model'

// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
	showLabels: boolean
}>()

//  computed:
const draw = computed(() => {
	// Draw the arc using d3
	let emptyPowerItem: PowerItem = {
		name: '',
		type: PowerItemType.counter,
		power: props.emptyPower,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: 'var(--color-bg)',
		icon: '',
		showInGraph: true,
	}
	let plotdata = [sourceSummary.evuIn]
	if (pvSystems.value.size > 1) {
		plotdata = plotdata.concat(
			[...pvSystems.value.values()].sort((a, b) => {
				return a.power - b.power
			}) as PowerItem[],
		)
	} else {
		plotdata.push(sourceSummary.pv)
	}
	if (batteries.value.size > 1) {
		plotdata = plotdata.concat(
			[...batteries.value.values()]
				.filter((b) => b.power < 0)
				.sort((a, b) => {
					return a.power - b.power
				}) as PowerItem[],
		)
	} else {
		plotdata.push(sourceSummary.batOut)
	}
	plotdata = plotdata.concat(emptyPowerItem)
	const arcCount = Object.values(sourceSummary).length - 1
	const pieGenerator = pie<PowerItem>()
		.value((record: PowerItem) => Math.abs(record.power))
		.startAngle(-Math.PI / 2 + props.circleGapSize)
		.endAngle(Math.PI / 2 - props.circleGapSize)
		.sort(null)
	const path = arc<PieArcDatum<PowerItem>>()
		//.innerRadius((props.radius / 6) * 5.5)
		.innerRadius(props.radius * 0.88)
		.outerRadius(props.radius)
		.cornerRadius(props.cornerRadius)
		.padAngle(0)
	const graph = select('g#pmSourceArc')
	graph.selectAll('*').remove()
	const sources = graph
		.selectAll('sources')
		.data(pieGenerator(Object.values(plotdata).filter((v) => v.power != 0)))
		.enter()

	sources
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
	addLabels(path, sources)
	return 'pmSourceArc.vue'
})
function addLabels(
	path: Arc<unknown, PieArcDatum<PowerItem>>,
	consumers: Selection<EnterElement, PieArcDatum<PowerItem>, BaseType, unknown>,
) {
	const categoriesToShow = [PowerItemType.inverter, PowerItemType.battery]
	const totalProduction =
		sourceSummary.pv.power +
		sourceSummary.evuIn.power +
		sourceSummary.batOut.power
	consumers = consumers.filter(
		(d) =>
			categoriesToShow.includes(d.data.type) &&
			Math.abs(d.data.power) / totalProduction > 0.05,
	)
	if (props.showLabels) {
		const popups = consumers.append('g')
		popups
			.append('rect')
			.attr('transform', (d) => 'translate(' + path.centroid(d) + ')')
			.attr('x', -40)
			.attr('y', -17)
			.attr('rx', 10)
			.attr('ry', 10)
			.attr('width', 80)
			.attr('height', 40)
			.attr('corner-radius', 20)
			.attr('filter', 'url(#f1)')
			.style('fill', (d) => d.data.color)
			.style('stroke', 'var(--color-axis)')
			.style('stroke-width', 0.4)
			.style('opacity', 1)
		const labels = popups
			.append('text')
			.attr('transform', (d) => 'translate(' + path.centroid(d) + ')')
			.attr('dy', 0)
			.attr('x', 0)
			.attr('y', 0)
			.style('text-anchor', 'middle')
			.style('font-size', 17)
			.style('fill', (d) => fgColor(d.data.color))
		labels
			.append('tspan')
			.attr('y', '0')
			.style('font-size', 14)
			.text((d) => trimLabel(d.data.name))
		labels
			.append('tspan')
			.attr('dy', '1em')
			.attr('x', '0')
			.text((d) => formatWatt(Math.abs(d.data.power)))
	}
}

function trimLabel(txt: string): string {
	const MAXLENGTH = 8
	if (txt.length > MAXLENGTH) {
		return txt.substring(0, MAXLENGTH) + '.'
	}
	return txt
}

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
