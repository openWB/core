<template>
	<g id="emBargraph">
		<!-- Bars -->
		<g v-for="(item, i) in props.plotdata" :key="i">
			<EnergyBar
				:item="item"
				:x-scale="props.yscale"
				:y-scale="props.xscale"
				:margin="props.margin"
				:height="props.height"
				:width="props.width"
				:barcount="props.plotdata.length"
				:aut-text="autTxt(item)"
				:autarchy="autPct(item)"
			/>
		</g>
		<animateTransform
			attribute-name="transform"
			type="scale"
			from="1 0"
			to="1 1"
			begin="0s"
			dur="2s"
		/>
	</g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import EnergyBar from './EnergyBar.vue'
import { sourceSummary, historicSummary, usageSummary } from '@/assets/js/model'
import { graphData } from '../powerGraph/model'

const props = defineProps<{
	plotdata: PowerItem[]
	yscale: d3.ScaleBand<string>
	xscale: d3.ScaleLinear<number, number, never>
	margin: MarginType
	height: number
	width: number
}>()

// computed: {
function autPct(item: PowerItem) {
	if (item.name == 'PV') {
		const src =
			graphData.graphMode == 'live' || graphData.graphMode == 'day'
				? sourceSummary
				: historicSummary.items
		const usg =
			graphData.graphMode == 'live' || graphData.graphMode == 'day'
				? usageSummary
				: historicSummary.items
		const exportedEnergy = usg.evuOut.energy
		const generatedEnergy = src.pv.energy
		return Math.round(
			((generatedEnergy - exportedEnergy) / generatedEnergy) * 100,
		)
	} else if (item.name == 'Netz') {
		const src =
			graphData.graphMode == 'live' || graphData.graphMode == 'day'
				? sourceSummary
				: historicSummary.items
		const usg =
			graphData.graphMode == 'live' || graphData.graphMode == 'day'
				? usageSummary
				: historicSummary.items
		const exportedEnergy = usg.evuOut.energy
		const importedEnergy = src.evuIn.energy
		const generatedEnergy = src.pv.energy
		const batEnergy = src.batOut.energy
		const storedEnergy = usg.batIn.energy
		return Math.round(
			((generatedEnergy + batEnergy - exportedEnergy - storedEnergy) /
				(generatedEnergy +
					batEnergy +
					importedEnergy -
					exportedEnergy -
					storedEnergy)) *
				100,
		)
	} else {
		return item.pvPercentage
	}
}

function autTxt(item: PowerItem) {
	if (item.name == 'PV') {
		return 'Eigen'
	} else {
		return 'Aut'
	}
}
</script>

<style></style>
