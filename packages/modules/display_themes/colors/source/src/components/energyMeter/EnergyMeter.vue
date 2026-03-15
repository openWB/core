<template>
	<WBWidget>
		<template #title>
			{{ heading }}
		</template>
		<template #buttons>
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
		</template>
		<div class="grid-col-12">
			<figure id="energymeter" class="energymeter p-0 m-0 align-self-stretch">
				<svg viewBox="0 0 500 500">
					<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
						<!--  Bar Graph -->
						<EMBarGraph
							:plotdata="plotdata"
							:x-scale="xScale"
							:y-scale="yScale"
							:height="height"
							:margin="margin"
						/>
						<!-- Y Axis -->
						<EMYAxis
							:y-scale="yScale"
							:width="width"
							:fontsize="axisFontsize"
							:config="globalConfig"
						/>
						<text
							:x="-margin.left"
							y="-15"
							fill="var(--color-axis)"
							:font-size="axisFontsize"
						>
							{{ graphData.graphMode == 'year' ? 'MWh' : 'kWh' }}
						</text>
						<EMLabels
							:plotdata="plotdata"
							:x-scale="xScale"
							:y-scale="yScale"
							:height="height"
							:margin="margin"
							:config="globalConfig"
						/>
					</g>
				</svg>
			</figure>
		</div>
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
} from '@/assets/js/model'
import EMBarGraph from './EMBarGraph.vue'
import EMYAxis from './EMYAxis.vue'
import EMLabels from './EMLabels.vue'
import WBWidget from '../shared/WBWidget.vue'
import PgSelector from '../powerGraph/PgSelector.vue'
import { globalConfig } from '@/assets/js/themeConfig'
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

//state
const width = 500
const height = 500
const margin = {
	top: 25,
	bottom: 30,
	left: 25,
	right: 0,
}
const axisFontsize = 12
// computed
const plotdata = computed(() => {
	let sources = Object.values(sourceSummary)
	let usage = usageDetails.value
	let historic = historicSummary.values()
	let result: PowerItem[] = []

	if (globalConfig.debug) {
		console.debug('----------------------- source summary -----------------')
		console.debug(sourceSummary)
		console.debug('----------------------- usage details ------------------')
		console.debug(usageDetails.value)
		console.debug('----------------------- historic summary ---------------')
		console.debug(historicSummary)
		console.debug('--------------------------------------------------------')
	}
	if (energyMeterNeedsRedraw.value == true) {
		energyMeterNeedsRedraw.value = false
	}
	switch (graphData.graphMode) {
		default:
		case 'live':
		case 'today':
			result = sources.concat(usage).filter((row) => row.energy > 0)
			break
		case 'day':
		case 'month':
		case 'year':
			if (historic.length == 0) {
				noData.value = true
			} else {
				noData.value = false
				result = historic.filter((row) => row.energy > 0)
			}
	}
	return result
})
const xScale = computed(() => {
	return scaleBand()
		.range([0, width - margin.left - margin.right])
		.domain(plotdata.value.map((d) => d.name))
		.padding(0.4)
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom - margin.top, 15])
		.domain([0, max(plotdata.value, (d: PowerItem) => d.energy) as number])
})
const heading = 'Energie'

const usageDetails = computed(() => {
	const cpcount = Object.values(chargePoints).length
	const shcount = [...shDevices.values()].filter((dev) => dev.configured).length
	return [usageSummary.evuOut, usageSummary.devices, usageSummary.charging]
		.concat(
			cpcount > 1
				? Object.values(chargePoints).map((cp) => cp.toPowerItem())
				: [],
		)
		.concat(
			shcount > 1
				? [...shDevices.values()].filter(
						(row) => row.configured && row.showInGraph,
					)
				: [],
		)
		.concat([usageSummary.batIn, usageSummary.house])
})
</script>

<style scoped>
.energymeter {
	width: 100%;
}
</style>
