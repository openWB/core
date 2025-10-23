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
import { registry, energyMeterNeedsRedraw } from '@/assets/js/model'
import EMBarGraph from './EMBarGraph.vue'
import EMYAxis from './EMYAxis.vue'
import EMLabels from './EMLabels.vue'
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
import { counters } from '../counterList/model'

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
	let result: PowerItem[] = []
	if (globalConfig.debug) {
		printDebugOutput()
	}
	if (energyMeterNeedsRedraw.value == true) {
		energyMeterNeedsRedraw.value = false
	}
	if (registry.items.size == 0) {
		noData.value = true
	} else {
		noData.value = false
		result = [
			registry.getItem('evuIn'),
			registry.getItem('pv'),
			registry.getItem('evuOut'),
			registry.getItem('batOut'),
			registry.getItem('charging'),
		]
		Object.values(chargePoints).forEach((cp) => {
			result.push(cp)
		})
	}
	result.push(registry.getItem('devices')!)
	shDevices.forEach((dev) => {
		if (dev.showInGraph) {
			result.push(dev)
		}
	})
	result.push(registry.getItem('counters'))
	counters.forEach((ctr) => {
		if (ctr.showInGraph) {
			result.push(ctr)
		}
	})
	result = result.concat([registry.getItem('batIn'), registry.getItem('house')])
	return result.filter(
		(row) => row[graphScope.value].energy && row[graphScope.value].energy > 0,
	)
})
const xScale = computed(() => {
	return scaleBand()
		.range([0, width - margin.left - margin.right])
		.domain(plotdata.value.map((d, index) => index.toString()))
		.padding(0.4)
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom - margin.top, 15])
		.domain([
			0,
			max(
				plotdata.value,
				(d: PowerItem) => d![graphScope.value]!.energy! as number,
			) ?? 0,
		])
})
const graphScope = computed(() => (graphData.usePastData ? 'past' : 'now'))
const heading = 'Energie'
function printDebugOutput() {
	console.debug(['all items:', registry])
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
