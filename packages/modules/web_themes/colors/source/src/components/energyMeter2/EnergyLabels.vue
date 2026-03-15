<template>
	<g id="emBarLabels">
		<!-- Bars -->
		<g v-for="(item, i) in props.plotdata" :key="i">
			<EnergyLabel
				:id="i.toString()"
				:item="item"
				:yscale="props.yscale"
				:margin="props.margin"
				:width="props.width"
				:item-height="itemHeight"
				:aut-text="autTxt(item)"
				:autarchy="autPct(item)"
			/>
		</g>
	</g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import EnergyLabel from './EnergyLabel.vue'
import type { MarginType, PowerItem } from '@/assets/js/types'
import { autPct } from '../energyMeter/model'
const props = defineProps<{
	plotdata: PowerItem[]
	yscale: d3.ScaleBand<string>
	width: number
	itemHeight: number
	margin: MarginType
}>()
// computed
// methods

function autTxt(item: PowerItem) {
	if (item.name == 'PV') {
		return 'Eigen'
	} else {
		return 'Aut'
	}
}
</script>

<style></style>
