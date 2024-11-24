<template>
	<WBWidget :full-width="true">
		<template #title>
			{{ heading }}
		</template>
		<template #buttons>
			<div class="d-flex justify-content-end">
				<PgSelector
					widgetid="graphsettings"
					:show-left-button="true"
					:show-right-button="true"
					:ignore-live="true"
					@shift-left="shiftLeft"
					@shift-right="shiftRight"
					@shift-up="shiftUp"
					@shift-down="shiftDown"
				/>
				<span
					v-if="widescreen"
					type="button"
					class="ms-1 p-0 pt-1"
					@click="zoomGraph"
				>
					<span class="fa-solid fa-lg ps-1 fa-magnifying-glass" />
				</span>
			</div>
		</template>
		<figure id="energymeter" class="p-0 m-0">
			<svg :viewBox="'0 0 500 ' + height">
				<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
					<!--  Bar Graph -->
					<BarGraph
						:plotdata="plotdata"
						:xscale="xScale"
						:yscale="yScale"
						:item-height="itemHeight"
					/>
					<!-- Y Axis -->
					<!-- 		<EMYAxis
						:y-scale="yScale"
						:width="width"
						:fontsize="axisFontsize"
						:config="globalConfig"
					/> -->
					<text
						:x="-margin.left"
						y="-15"
						fill="var(--color-axis)"
						:font-size="axisFontsize"
					>
						{{ graphData.graphMode == 'year' ? 'MWh' : 'kWh' }}
					</text>
					<EnergyLabels
						:plotdata="plotdata"
						:yscale="yScale"
						:width="width"
						:item-height="itemHeight"
						:margin="margin"
					/>
				</g>
			</svg>
		</figure>
		<p v-if="noData">No data</p>
	</WBWidget>
</template>
<script setup lang="ts">
import { scaleBand, scaleLinear } from 'd3'
import { max } from 'd3'
import type { PowerItem } from '@/assets/js/types'
import {
	sourceSummary,
	historicSummary,
	energyMeterNeedsRedraw,
	usageSummary,
	pvSystems,
} from '@/assets/js/model'
import BarGraph from './BarGraph.vue'
//import EMYAxis from './EMYAxis.vue'
import EnergyLabels from './EnergyLabels.vue'
import WBWidget from '../shared/WBWidget.vue'
import PgSelector from '../powerGraph/PgSelector.vue'
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import {
	shiftLeft,
	shiftRight,
	shiftUp,
	shiftDown,
} from '@/components/powerGraph/model'
import { graphData, noData } from '@/components/powerGraph/model'
import { computed } from 'vue'
import { chargePoints } from '../chargePointList/model'
import { shDevices } from '../smartHome/model'
import { batteries } from '../batteryList/model'

//state
const width = 500
const itemHeight = 60
const margin = {
	top: 0,
	bottom: 30,
	left: 0,
	right: 0,
}
const height = computed(() => {
	return plotdata.value.length * itemHeight + margin.top + margin.bottom
	//return 600
})
const axisFontsize = 12
// computed
const plotdata = computed(() => {
	let sources = Object.values(sourceSummary)
	let usage = usageDetails.value
	const historic = historicSummary.items
	let result: PowerItem[] = []

	if (globalConfig.debug) {
		printDebugOutput()
	}
	if (energyMeterNeedsRedraw.value == true) {
		energyMeterNeedsRedraw.value = false
	}
	switch (graphData.graphMode) {
		default:
		case 'live':
		case 'today':
			result = addSourceDetails(sources).concat(usage)
			break
		case 'day':
		case 'month':
		case 'year':
			if (Object.values(historic).length == 0) {
				noData.value = true
			} else {
				noData.value = false
				result = [
					historic.evuIn,
					historic.pv,
					historic.evuOut,
					historic.batOut,
					historic.charging,
				]
				if (Object.values(chargePoints).length > 1) {
					Object.keys(chargePoints).forEach((id) => {
						if (historic['cp' + id]) {
							result.push(historic['cp' + id])
						}
					})
				}

				result.push(historic.devices)
				shDevices.forEach((dev, id) => {
					if (dev.showInGraph && historic['sh' + id]) {
						result.push(historic['sh' + id])
					}
				})
				result = result.concat([historic.batIn, historic.house])
			}
	}
	return result.filter((row) => row.energy && row.energy > 0)
})
const xScale = computed(() => {
	return scaleLinear()
		.range([0, width - margin.left - margin.right])
		.domain([0, max(plotdata.value, (d: PowerItem) => d.energy) as number])
})
const yScale = computed(() => {
	return scaleBand()
		.range([margin.top, height.value - margin.bottom])
		.domain(plotdata.value.map((d, i) => i.toString()))
		.padding(0.1)
})
const heading = 'Energie'

const usageDetails = computed(
	() => {
		const cpcount = Object.values(chargePoints).length
		const shcount = [...shDevices.values()].filter(
			(dev) => dev.configured,
		).length
		let usg = usageSummary
		return [
			...[usg.evuOut, usg.charging].concat(
				cpcount > 1
					? Object.values(chargePoints).map((cp) => cp.toPowerItem())
					: [],
			),
			...[usg.devices]
				.concat(
					shcount > 1
						? [...shDevices.values()].filter(
								(row) => row.configured && row.showInGraph,
							)
						: [],
				)
				.concat([usageSummary.batIn, usageSummary.house]),
		]
	},
	//}
)
function addSourceDetails(sources: PowerItem[]): PowerItem[] {
	let idx = 0
	if (pvSystems.value.size > 1) {
		pvSystems.value.forEach((inv) => {
			sources.splice(2 + idx++, 0, {
				name: inv.name,
				power: inv.power,
				energy: inv.energy,
				energyPv: 0,
				energyBat: 0,
				pvPercentage: 0,
				color: inv.color,
				icon: inv.name,
				showInGraph: true,
			})
		})
	}
	if (batteries.value.size > 1) {
		batteries.value.forEach((bat) => {
			sources.splice(3 + idx++, 0, {
				name: bat.name,
				power: bat.power,
				energy: bat.dailyYieldExport,
				energyPv: 0,
				energyBat: 0,
				pvPercentage: 0,
				color: bat.color,
				icon: bat.name,
				showInGraph: true,
			})
		})
	}
	return sources
}
function printDebugOutput() {
	console.debug(['source summary:', sourceSummary])
	console.debug(['usage details:', usageDetails.value])
	console.debug(['historic summary:', historicSummary])
}
function zoomGraph() {
	globalConfig.zoomedWidget = 2
	globalConfig.zoomGraph = !globalConfig.zoomGraph
}
</script>

<style scoped>
.fa-magnifying-glass {
	color: var(--color-menu);
}
</style>
