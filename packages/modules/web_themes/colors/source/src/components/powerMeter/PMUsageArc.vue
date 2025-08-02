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
		<g id="pmUsageArc" :origin="draw" />
	</g>
</template>

<script setup lang="ts">
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import { usageSummary } from '@/assets/js/model'
import { batteries } from '../batteryList/model'
import { shDevices } from '../smartHome/model'
import {
	type PieArcDatum,
	select,
	arc,
	pie,
	type Arc,
	type EnterElement,
	type Selection,
	type BaseType,
} from 'd3'
import { computed } from 'vue'
import { chargePoints } from '../chargePointList/model'
import { formatWatt, fgColor } from '@/assets/js/helpers'
// props
const props = defineProps<{
	radius: number
	cornerRadius: number
	circleGapSize: number
	emptyPower: number
	showLabels: boolean
}>()

//  computed: {
const draw = computed(() => {
	// Draw the arc using d3
	const arcCount = plotdata.value.length - 1
	const pieGenerator = pie<PowerItem>()
		.value((record: PowerItem) => record.power)
		.startAngle(Math.PI * 1.5 - props.circleGapSize)
		.endAngle(Math.PI / 2 + props.circleGapSize)
		.sort(null)
	const path = arc<PieArcDatum<PowerItem>>()
		//.innerRadius((props.radius / 6) * 5)
		.innerRadius(props.radius * 0.88)
		.outerRadius(props.radius)
		.cornerRadius(props.cornerRadius)
	const graph = select('g#pmUsageArc')
	graph.selectAll('*').remove()
	const consumers = graph
		.selectAll('consumers')
		.data(pieGenerator(plotdata.value.filter((v) => v.power != 0)))
		.enter()
	consumers
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
	//graph.selectAll('consumers')
	//	.data(pieGenerator(plotdata.filter((v) => v.power != 0)))
	//	.enter()

	addLabels(path, consumers)

	return 'pmUsageArc.vue'
})
const emptyPowerItem = computed(() => {
	return {
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
})
const plotdata = computed(() => {
	return [usageSummary.evuOut].concat(
		chargePointsToShow.value,
		devicesToShow.value,
		batteriesToShow.value,
		usageSummary.house,
		emptyPowerItem.value,
	)
})
const chargePointsToShow = computed(() => {
	return Object.values(chargePoints).length > 1
		? Object.values(chargePoints).sort((a, b) => {
				return b.power - a.power
			})
		: [usageSummary.charging]
})
const devicesToShow = computed(() => {
	let summarizedPower = 0
	for (const d of shDevices.values()) {
		if (d.configured && !d.countAsHouse && !d.showInGraph) {
			summarizedPower += d.power
		}
	}
	const deviceSummary: PowerItem = {
		name: 'Geräte',
		type: PowerItemType.device,
		power: summarizedPower,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: 'var(--color-devices)',
		icon: '',
		showInGraph: true,
	}
	let activeDevices = [...shDevices.values()].filter((row) => row.configured)
	return activeDevices.length > 1
		? [deviceSummary].concat(
				activeDevices
					.filter((row) => !row.countAsHouse && row.showInGraph)
					.sort((a, b) => {
						return b.power - a.power
					}),
			)
		: [usageSummary.devices]
})
const batteriesToShow = computed(() => {
	return batteries.value.size > 1
		? [...batteries.value.values()]
				.filter((b) => b.power > 0)
				.sort((a, b) => {
					return b.power - a.power
				})
		: [usageSummary.batIn]
})

function addLabels(
	path: Arc<unknown, PieArcDatum<PowerItem>>,
	consumers: Selection<EnterElement, PieArcDatum<PowerItem>, BaseType, unknown>,
) {
	const categoriesToShow = [
		PowerItemType.chargepoint,
		PowerItemType.battery,
		PowerItemType.device,
	]
	consumers = consumers.filter((d) => categoriesToShow.includes(d.data.type))
	if (props.showLabels) {
		consumers
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
			//.style('fill', 'var(--color-input)')
			.style('fill', (d) => d.data.color)
			.style('stroke', 'var(--color-axis)')
			.style('stroke-width', 0.4)
			.style('opacity', 1)
		const labels = consumers
			.append('text')
			.attr('transform', (d) => 'translate(' + path.centroid(d) + ')')
			.attr('dy', 0)
			.attr('x', 0)
			.attr('y', 0)
			.style('text-anchor', 'middle')
			.style('font-size', 17)
			//.style('stroke', (d) => fgColor(d.data.color))
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
			.text((d) => formatWatt(d.data.power))
	}
}

function trimLabel(txt: string): string {
	const MAXLENGTH = 8
	if (txt.length > MAXLENGTH) {
		return txt.substring(0, MAXLENGTH) + '.'
	}
	return txt
}
</script>

<style></style>
